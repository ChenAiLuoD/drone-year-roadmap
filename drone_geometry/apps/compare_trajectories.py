#!/usr/bin/env python3
"""读取变换前后的 CSV，并生成并排 3D 对比图。"""

import argparse  # 解析命令行参数。
import csv  # 读取简单的 timestamp,x,y,z CSV。
from pathlib import Path  # 跨平台处理文件路径。

import matplotlib.pyplot as plt  # 创建并保存图形。


# 统一要求输入文件使用 C++ 程序导出的固定表头。
EXPECTED_COLUMNS = ["timestamp", "x", "y", "z"]


def read_trajectory_csv(input_path: Path) -> dict[str, list[float]]:
    """读取一个轨迹 CSV，并返回四列浮点数据。"""

    values = {column: [] for column in EXPECTED_COLUMNS}

    # newline="" 可以避免 csv 模块受到平台换行符差异影响。
    with input_path.open("r", encoding="utf-8", newline="") as input_file:
        reader = csv.DictReader(input_file)

        # 先检查表头，防止前后文件列含义不一致。
        if reader.fieldnames != EXPECTED_COLUMNS:
            raise ValueError(
                f"{input_path} 的表头必须是 {','.join(EXPECTED_COLUMNS)}"
            )

        # 逐行把 CSV 字符串转换为浮点数；不在这里执行坐标变换。
        for line_number, row in enumerate(reader, start=2):
            try:
                for column in EXPECTED_COLUMNS:
                    values[column].append(float(row[column]))
            except (TypeError, ValueError) as error:
                raise ValueError(
                    f"{input_path} 第 {line_number} 行包含非法数字"
                ) from error

    # 空文件没有可供比较的轨迹。
    if not values["x"]:
        raise ValueError(f"{input_path} 没有有效轨迹点")

    return values


def check_matching_timestamps(
    before: dict[str, list[float]],
    after: dict[str, list[float]],
) -> None:
    """检查前后轨迹点数和时间戳是否一致。"""

    if len(before["timestamp"]) != len(after["timestamp"]):
        raise ValueError("变换前后点数不一致，无法逐点对比")

    for index, (before_time, after_time) in enumerate(
        zip(before["timestamp"], after["timestamp"])
    ):
        if before_time != after_time:
            raise ValueError(f"第 {index + 1} 个点的时间戳不一致")


def calculate_limits(
    before: dict[str, list[float]],
    after: dict[str, list[float]],
) -> dict[str, tuple[float, float]]:
    """为两个子图计算相同的坐标范围，避免视觉比例产生误导。"""

    limits: dict[str, tuple[float, float]] = {}
    for axis in ("x", "y", "z"):
        all_values = before[axis] + after[axis]
        minimum = min(all_values)
        maximum = max(all_values)

        # 如果某一轴所有数值相同，手动留出一点范围避免图形退化成平面线。
        span = maximum - minimum
        margin = 0.1 * span if span > 0.0 else 1.0
        limits[axis] = (minimum - margin, maximum + margin)

    return limits


def draw_trajectory(
    axes,
    trajectory: dict[str, list[float]],
    title: str,
    frame_name: str,
    limits: dict[str, tuple[float, float]],
    color: str,
) -> None:
    """在一个 3D 子图中绘制一条轨迹。"""

    # 用圆点显示采样点，用折线显示点的先后连接关系。
    axes.plot(
        trajectory["x"],
        trajectory["y"],
        trajectory["z"],
        color=color,
        marker="o",
        linewidth=1.8,
        markersize=4,
        label=f"{frame_name} ({len(trajectory['x'])} points)",
    )

    # 轴名和标题明确说明这个子图代表哪个坐标系。
    axes.set_xlabel(f"x [{frame_name}]")
    axes.set_ylabel(f"y [{frame_name}]")
    axes.set_zlabel(f"z [{frame_name}]")
    axes.set_title(title)
    axes.set_xlim(*limits["x"])
    axes.set_ylim(*limits["y"])
    axes.set_zlim(*limits["z"])
    axes.legend()
    axes.grid(True)


def parse_arguments() -> argparse.Namespace:
    """定义并解析命令行参数。"""

    parser = argparse.ArgumentParser(
        description="对比变换前后轨迹并输出 3D PNG。"
    )
    parser.add_argument("--before", required=True, type=Path, help="变换前 CSV")
    parser.add_argument("--after", required=True, type=Path, help="变换后 CSV")
    parser.add_argument("--output", required=True, type=Path, help="输出 PNG")
    parser.add_argument("--source", required=True, help="变换前坐标系名称")
    parser.add_argument("--target", required=True, help="变换后坐标系名称")
    return parser.parse_args()


def main() -> int:
    """程序入口：读取两份 CSV、检查时间戳、生成对比图。"""

    arguments = parse_arguments()

    try:
        # 读取前后轨迹；这里不重新计算变换，保持脚本职责单一。
        before = read_trajectory_csv(arguments.before)
        after = read_trajectory_csv(arguments.after)
        check_matching_timestamps(before, after)
        limits = calculate_limits(before, after)

        # 创建左右两个 3D 子图，便于直接比较形状和方向。
        figure = plt.figure(figsize=(14, 6))
        before_axes = figure.add_subplot(121, projection="3d")
        after_axes = figure.add_subplot(122, projection="3d")

        draw_trajectory(
            before_axes,
            before,
            f"Before transform: {arguments.source}",
            arguments.source,
            limits,
            "tab:blue",
        )
        draw_trajectory(
            after_axes,
            after,
            f"After transform: {arguments.target}",
            arguments.target,
            limits,
            "tab:orange",
        )

        # 总标题说明两幅图来自哪一组坐标系。
        figure.suptitle(
            f"Trajectory comparison: {arguments.source} -> {arguments.target}"
        )

        # 自动创建输出目录，并保存高分辨率 PNG。
        arguments.output.parent.mkdir(parents=True, exist_ok=True)
        figure.tight_layout()
        figure.savefig(arguments.output, dpi=160)
        plt.close(figure)
    except (OSError, ValueError) as error:
        print(f"对比失败: {error}")
        return 1

    print(f"对比图已保存: {arguments.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
