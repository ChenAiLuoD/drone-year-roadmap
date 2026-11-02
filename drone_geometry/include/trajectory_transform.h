#pragma once

#include <string>  // std::string：文件路径和错误信息。
#include <vector>  // std::vector：保存行数未知的轨迹点。

#include <Eigen/Core>      // Eigen::Vector3d：三维位置。
#include <Eigen/Geometry>  // Eigen::Isometry3d：旋转加平移。

// 一行轨迹数据：时间戳和三维位置。
// 位置单位由项目约定为米，时间戳原样保留。
struct TrajectoryPoint {
    double timestamp{};  // CSV 第一列 timestamp。
    Eigen::Vector3d position{Eigen::Vector3d::Zero()}; // CSV 的 x,y,z。
};

// 用 T_target_source 把 source 坐标中的点转换到 target 坐标。
// 数学形式：p_target = R_target_source * p_source + t_target_source。
Eigen::Vector3d transformPoint(
    const Eigen::Isometry3d& T_target_source,
    const Eigen::Vector3d& point_source);

// 读取固定格式 timestamp,x,y,z 的简单 CSV。
// 只处理不带引号、单元格中不含逗号的简单 CSV。
bool readTrajectoryCsv(
    const std::string& input_path,
    std::vector<TrajectoryPoint>& points,
    std::string& error_message);

// 将轨迹写回相同的 CSV 格式，并保留时间戳。
bool writeTrajectoryCsv(
    const std::string& output_path,
    const std::vector<TrajectoryPoint>& points,
    std::string& error_message);
