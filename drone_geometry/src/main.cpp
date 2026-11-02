#include "cli.h"
#include "trajectory_transform.h"

#include <iostream>

// 程序入口：读取参数、读取轨迹、执行变换并写出结果。
int main(int argc, char* argv[]) {
    // 保存命令行解析结果和可读的错误信息。
    CommandLineOptions options;
    std::string error_message;

    // 第一步：解析输入输出路径、坐标系名称、四元数和平移参数。
    if (!parseCommandLine(argc, argv, options, error_message)) {
        if (!error_message.empty()) {
            std::cerr << "参数错误: " << error_message << '\n';
            printUsage(argv[0]);
            return 2;
        }
        return 0;
    }

    // 用 vector 保存 CSV 中数量未知的所有轨迹点。
    std::vector<TrajectoryPoint> points;

    // 读取源坐标系中的轨迹点。
    if (!readTrajectoryCsv(options.input_path, points, error_message)) {
        std::cerr << "读取失败: " << error_message << '\n';
        return 1;
    }

    // 第三步：将四元数和平移组成 T_target_source。
    // 该变换会把 source 坐标表示转换为 target 坐标表示。
    Eigen::Isometry3d T_target_source = Eigen::Isometry3d::Identity();
    T_target_source.linear() = options.rotation.toRotationMatrix();
    T_target_source.translation() = options.translation;

    // 第四步：对每个轨迹点执行 p_target = R * p_source + t。
    for (TrajectoryPoint& point : points) {
        point.position = transformPoint(T_target_source, point.position);
    }

    // 第五步：输出目标坐标系中的轨迹，并保持原时间戳。
    if (!writeTrajectoryCsv(options.output_path, points, error_message)) {
        std::cerr << "写出失败: " << error_message << '\n';
        return 1;
    }

    std::cout << "转换完成: " << options.source_frame
              << " -> " << options.target_frame << '\n'
              << "点数: " << points.size() << '\n'
              << "输出: " << options.output_path << '\n';

    return 0;
}
