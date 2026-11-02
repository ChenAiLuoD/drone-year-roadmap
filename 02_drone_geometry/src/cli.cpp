#include "cli.h"

#include <cmath>
#include <cstdlib>
#include <iostream>
#include <limits>

namespace {

// 从命令行中读取一个 double 参数。
// index 会前进到参数值所在的位置，调用方的 for 循环随后继续处理下一个选项。
bool readDoubleArgument(
    int& index,
    int argc,
    char* argv[],
    const char* option_name,
    double& value,
    std::string& error_message) {
    if (index + 1 >= argc) {
        error_message = std::string(option_name) + " 缺少数值";
        return false;
    }

    // strtod 会把文本转换成 double，并通过 end 告诉我们读到了哪里。
    char* end = nullptr;
    const std::string text = argv[++index];
    value = std::strtod(text.c_str(), &end);

    // 既要检查“读到了数字”，也要拒绝尾随文字、NaN 和无穷大。
    if (end == text.c_str() || *end != '\0' || !std::isfinite(value)) {
        error_message = std::string(option_name) + " 不是合法数字: " + text;
        return false;
    }

    return true;
}

// 从命令行中读取一个字符串参数，例如文件路径或坐标系名称。
bool readStringArgument(
    int& index,
    int argc,
    char* argv[],
    const char* option_name,
    std::string& value,
    std::string& error_message) {
    if (index + 1 >= argc) {
        error_message = std::string(option_name) + " 缺少值";
        return false;
    }

    // 参数值紧跟在选项后面，例如 --input data/sample.csv。
    value = argv[++index];
    if (value.empty()) {
        error_message = std::string(option_name) + " 不能是空字符串";
        return false;
    }

    return true;
}

}  // namespace

bool parseCommandLine(
    int argc,
    char* argv[],
    CommandLineOptions& options,
    std::string& error_message) {
    // 这四个参数决定输入输出的基本语义，因此必须显式提供。
    bool has_input = false;
    bool has_output = false;
    bool has_source = false;
    bool has_target = false;
    // 四元数默认是单位旋转；如果用户提供部分数值，下面会用默认值补齐。
    double qw = 1.0;
    double qx = 0.0;
    double qy = 0.0;
    double qz = 0.0;
    double tx = 0.0;
    double ty = 0.0;
    double tz = 0.0;

    // argv[0] 是程序名，所以从 argv[1] 开始读取选项。
    for (int index = 1; index < argc; ++index) {
        const std::string option = argv[index];

        // 帮助不是错误：打印用法后让 main() 以成功状态结束。
        if (option == "--help" || option == "-h") {
            printUsage(argv[0]);
            return false;
        }
        // 字符串参数：文件路径和坐标系名称。
        if (option == "--input") {
            has_input = readStringArgument(index, argc, argv, "--input", options.input_path, error_message);
        } else if (option == "--output") {
            has_output = readStringArgument(index, argc, argv, "--output", options.output_path, error_message);
        } else if (option == "--source") {
            has_source = readStringArgument(index, argc, argv, "--source", options.source_frame, error_message);
        } else if (option == "--target") {
            has_target = readStringArgument(index, argc, argv, "--target", options.target_frame, error_message);
        // 平移参数：构成 t_target_source。
        } else if (option == "--tx") {
            if (!readDoubleArgument(index, argc, argv, "--tx", tx, error_message)) return false;
        } else if (option == "--ty") {
            if (!readDoubleArgument(index, argc, argv, "--ty", ty, error_message)) return false;
        } else if (option == "--tz") {
            if (!readDoubleArgument(index, argc, argv, "--tz", tz, error_message)) return false;
        // 四元数参数：构成 q_target_source，顺序固定为 w,x,y,z。
        } else if (option == "--qw") {
            if (!readDoubleArgument(index, argc, argv, "--qw", qw, error_message)) return false;
        } else if (option == "--qx") {
            if (!readDoubleArgument(index, argc, argv, "--qx", qx, error_message)) return false;
        } else if (option == "--qy") {
            if (!readDoubleArgument(index, argc, argv, "--qy", qy, error_message)) return false;
        } else if (option == "--qz") {
            if (!readDoubleArgument(index, argc, argv, "--qz", qz, error_message)) return false;
        } else {
            // 不接受拼写错误或未定义参数，避免静默使用错误配置。
            error_message = "未知参数: " + option;
            return false;
        }

        if ((option == "--input" || option == "--output" || option == "--source" || option == "--target") && !error_message.empty()) {
            return false;
        }
    }

    // 缺少任意必需参数时，不进入文件处理阶段。
    if (!has_input || !has_output || !has_source || !has_target) {
        error_message = "必须提供 --input、--output、--source 和 --target";
        return false;
    }

    // 把零散的命令行数值组装成 Eigen 类型。
    options.translation = Eigen::Vector3d(tx, ty, tz);
    options.rotation = Eigen::Quaterniond(qw, qx, qy, qz);

    // 零四元数无法表示旋转，必须拒绝。
    if (options.rotation.norm() < std::numeric_limits<double>::epsilon()) {
        error_message = "四元数长度不能接近 0";
        return false;
    }

    // 归一化后才把四元数当作纯旋转使用，避免浮点误差破坏旋转性质。
    options.rotation.normalize();
    return true;
}

void printUsage(const char* program_name) {
    std::cout
        << "用法:\n"
        << "  " << program_name << " --input input.csv --output output.csv\n"
        << "      --source body_flu --target world_enu\n"
        << "      --tx 0 --ty 0 --tz 0\n"
        << "      --qw 1 --qx 0 --qy 0 --qz 0\n";
}
