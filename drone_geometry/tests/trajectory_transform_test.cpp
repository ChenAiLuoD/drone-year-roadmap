#include "trajectory_transform.h"

#include <cmath>
#include <gtest/gtest.h>

namespace {

// 旋转和距离测试使用统一的浮点容差，而不是直接比较 ==。
constexpr double kTolerance = 1e-9;

}  // namespace

// 先验证最核心的“旋转 + 平移”公式。
TEST(TrajectoryTransformTest, AppliesRotationAndTranslation) {
    // 构造一个绕 Z 轴旋转 90 度、再沿 X 轴平移 10 米的变换。
    Eigen::Isometry3d T_target_source = Eigen::Isometry3d::Identity();
    T_target_source.rotate(Eigen::AngleAxisd(
        M_PI / 2.0,
        Eigen::Vector3d::UnitZ()));
    T_target_source.pretranslate(Eigen::Vector3d(10.0, 0.0, 0.0));

    // 输入点位于 source 坐标系的 X 轴正方向。
    const Eigen::Vector3d point_source(1.0, 0.0, 0.0);
    const Eigen::Vector3d point_target =
        transformPoint(T_target_source, point_source);

    // 旋转后 X 轴变成 Y 轴，再加上平移，预期为 (10,1,0)。
    EXPECT_TRUE(point_target.isApprox(
        Eigen::Vector3d(10.0, 1.0, 0.0),
        kTolerance));
}

// 验证旋转不会改变点之间的距离。
TEST(TrajectoryTransformTest, PreservesDistance) {
    // 刚体变换可以改变位置，但不应改变两个点之间的距离。
    Eigen::Isometry3d T_target_source = Eigen::Isometry3d::Identity();
    T_target_source.rotate(Eigen::AngleAxisd(
        M_PI / 3.0,
        Eigen::Vector3d::UnitZ()));
    T_target_source.pretranslate(Eigen::Vector3d(4.0, -2.0, 1.0));

    // 选择两个距离为 5 的测试点（3-4-5 三角形）。
    const Eigen::Vector3d first_source(0.0, 0.0, 0.0);
    const Eigen::Vector3d second_source(3.0, 4.0, 0.0);
    const Eigen::Vector3d first_target =
        transformPoint(T_target_source, first_source);
    const Eigen::Vector3d second_target =
        transformPoint(T_target_source, second_source);

    // 变换前后的距离应在容差范围内相等。
    EXPECT_NEAR(
        (second_target - first_target).norm(),
        (second_source - first_source).norm(),
        kTolerance);
}
