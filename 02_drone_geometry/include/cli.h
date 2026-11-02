#pragma once

#include <string>  // std::string：保存路径、坐标系名称和错误信息。

#include <Eigen/Core>      // Eigen::Vector3d：保存平移向量。
#include <Eigen/Geometry>  // Eigen::Quaterniond：保存旋转。

// 保存命令行解析后的配置。
struct CommandLineOptions {
    std::string input_path;   // --input：源轨迹 CSV 文件。
    std::string output_path;  // --output：转换后的 CSV 文件。
    std::string source_frame; // --source：输入点使用的坐标系。
    std::string target_frame; // --target：输出点使用的坐标系。

    // --qw/--qx/--qy/--qz：source -> target 的旋转四元数。
    Eigen::Quaterniond rotation{Eigen::Quaterniond::Identity()};

    // --tx/--ty/--tz：source 原点在 target 坐标系中的平移。
    Eigen::Vector3d translation{Eigen::Vector3d::Zero()};
};

// 解析命令行；成功返回 true，失败时把原因写入 error_message。
// --help 时打印帮助并返回 false，但不设置错误信息。
bool parseCommandLine(
    int argc,
    char* argv[],
    CommandLineOptions& options,
    std::string& error_message);

// 打印程序支持的参数格式和一个最小调用示例。
void printUsage(const char* program_name);
