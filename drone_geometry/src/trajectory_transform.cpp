#include "trajectory_transform.h"

#include <cmath>
#include <fstream>
#include <iomanip>
#include <sstream>

namespace {

// 将一个 CSV 字段解析为 double，并拒绝空字段和尾随非法字符。
bool parseDouble(
    const std::string& text,
    double& value) {
    // used 表示 stod 实际消耗的字符数量。
    std::size_t used = 0;

    try {
        value = std::stod(text, &used);
    } catch (const std::exception&) {
        return false;
    }

    // used 必须等于完整字段长度，避免把 "1.2abc" 当成合法数字。
    return used == text.size() && std::isfinite(value);
}

}  // namespace

Eigen::Vector3d transformPoint(
    const Eigen::Isometry3d& T_target_source,
    const Eigen::Vector3d& point_source) {
    // Isometry3d 会执行 p_target = R * p_source + t。
    // 这里不改变变换方向，方向由变量名 T_target_source 表明。
    return T_target_source * point_source;
}

bool readTrajectoryCsv(
    const std::string& input_path,
    std::vector<TrajectoryPoint>& points,
    std::string& error_message) {
    // 打开输入文件；打开失败时立即返回，避免继续读取空流。
    std::ifstream input(input_path);
    if (!input) {
        error_message = "无法打开输入文件: " + input_path;
        return false;
    }

    // 第一行必须是固定表头，保证输入格式明确。
    std::string line;
    if (!std::getline(input, line) || line != "timestamp,x,y,z") {
        error_message = "CSV 表头必须是 timestamp,x,y,z";
        return false;
    }

    // 从第二行开始读取数据，并记录行号用于报错。
    std::size_t line_number = 1;
    while (std::getline(input, line)) {
        ++line_number;

        // 忽略空白行，便于手工编辑样例文件。
        if (line.empty()) {
            continue;
        }

        // 用逗号把一行拆成四个文字字段。
        std::stringstream row(line);
        std::string field;
        std::string fields[4];

        // 逐列读取 timestamp、x、y、z；不足四列时报告错误。
        for (int index = 0; index < 4; ++index) {
            if (!std::getline(row, fields[index], ',')) {
                error_message = "第 " + std::to_string(line_number) + " 行列数不足";
                return false;
            }
        }

        // 第四列之后仍能读到内容，说明列数超过了固定格式。
        if (std::getline(row, field, ',')) {
            error_message = "第 " + std::to_string(line_number) + " 行列数超过 4";
            return false;
        }

        // 先把字符串转换成真正可计算的 double。
        double timestamp = 0.0;
        double x = 0.0;
        double y = 0.0;
        double z = 0.0;
        if (!parseDouble(fields[0], timestamp) ||
            !parseDouble(fields[1], x) ||
            !parseDouble(fields[2], y) ||
            !parseDouble(fields[3], z)) {
            error_message = "第 " + std::to_string(line_number) + " 行包含非法数字";
            return false;
        }

        // 转换成功后，创建轨迹点并追加到 vector。
        points.push_back(TrajectoryPoint{
            timestamp,
            Eigen::Vector3d(x, y, z)
        });
    }

    // 空文件没有可供转换的轨迹，作为输入错误处理。
    if (points.empty()) {
        error_message = "输入 CSV 没有有效轨迹点";
        return false;
    }

    return true;
}

bool writeTrajectoryCsv(
    const std::string& output_path,
    const std::vector<TrajectoryPoint>& points,
    std::string& error_message) {
    // 打开输出文件；如果路径不可写，直接返回错误。
    std::ofstream output(output_path);
    if (!output) {
        error_message = "无法打开输出文件: " + output_path;
        return false;
    }

    // 输出固定表头，并提高精度，减少浮点转换造成的信息损失。
    output << "timestamp,x,y,z\n";
    output << std::setprecision(17);

    // 时间戳保持不变，只写出转换后的 x、y、z。
    for (const TrajectoryPoint& point : points) {
        output << point.timestamp << ','
               << point.position.x() << ','
               << point.position.y() << ','
               << point.position.z() << '\n';
    }

    // 检查写入过程中是否发生磁盘或流错误。
    if (!output) {
        error_message = "写入输出文件失败: " + output_path;
        return false;
    }

    return true;
}
