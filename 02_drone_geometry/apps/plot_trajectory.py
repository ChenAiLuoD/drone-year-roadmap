#!/usr/bin/env python3
"""读取轨迹 CSV，并把它绘制成带坐标系说明的 3D PNG。"""

import argparse  # 解析命令行参数。
import csv  # 读取简单的 timestamp,x,y,z CSV。
from pathlib import Path  # 以跨平台方式处理输入输出路径。

import matplotlib.pyplot as plt  # 创建图形和保存 PNG。


# 固定 CSV 表头，避免把列顺序或列名读错。
EXPECTED_COLUMNS = ["timestamp", "x", "y", "z"]


def read_trajectory_csv(input_path: Path) -> tuple[list[float], list[float], list[float], list[float]]:
    """读取 CSV，返回时间戳以及 x、y、z 四列数值。"""

    timestamps: list[float] = []  # 保存时间戳，当前绘图暂不使用但保留读取结果。
    x_values: list[float] = []  # 保存 x 坐标。
    y_values: list[float] = []  # 保存 y 坐标。
    z_values: list[float] = []  # 保存 z 坐标。

    # newline="" 是 csv 模块推荐的打开方式，可避免不同系统换行符干扰解析。
    with input_path.open("r", encoding="utf-8", newline="") as input_file:
        reader = csv.DictReader(input_file)

        # 表头必须完整匹配 C++ 程序导出的固定格式。
        if reader.fieldnames != EXPECTED_COLUMNS:
            raise ValueError(
                f"CSV 表头必须是 {','.join(EXPECTED_COLUMNS)}，"
                f"实际为 {reader.fieldnames}"
            )

        # 逐行读取；这里仅做字符串到浮点数的转换，不改变坐标值。
        for line_number, row in enumerate(reader, start=2):
            try:
                timestamps.append(float(row["timestamp"]))
                x_values.append(float(row["x"]))
                y_values.append(float(row["y"]))
                z_values.append(float(row["z"]))
            except (TypeError, ValueError) as error:
                raise ValueError(f"第 {line_number} 行包含非法数字") from error

    # 没有数据点时无法绘图，提前给出清晰错误。
    if not x_values:
        raise ValueError("CSV 中没有有效轨迹点")

    return timestamps, x_values, y_values, z_values


def plot_trajectory(
    x_values: list[float],
    y_values: list[float],
    z_values: list[float],
    input_path: Path,
    output_path: Path,
    source_frame: str,
    target_frame: str,
) -> None:
    """把已读取的坐标绘制成 3D 折线并保存为 PNG。"""

    # 创建 3D 坐标轴；脚本只绘图，不在这里计算坐标变换。
    figure = plt.figure(figsize=(9, 7))
    axes = figure.add_subplot(111, projection="3d")

    # 用点和折线同时表示轨迹，便于看出采样点顺序。
    axes.plot(
        x_values,
        y_values,
        z_values,
        marker="o",
        linewidth=1.8,
        markersize=4,
        label=f"trajectory ({len(x_values)} points)",
    )

    # 坐标轴标签明确说明当前图中展示的是目标坐标系中的位置。
    axes.set_xlabel(f"x [{target_frame}]")
    axes.set_ylabel(f"y [{target_frame}]")
    axes.set_zlabel(f"z [{target_frame}]")

    # 标题记录输入文件、源坐标系和目标坐标系，方便复盘。
    axes.set_title(
        f"Trajectory: {source_frame} -> {target_frame}\n"
        f"Input: {input_path.name}"
    )
    axes.legend()
    axes.grid(True)

    # 自动创建输出目录，避免用户必须提前手动 mkdir。
    output_path.parent.mkdir(parents=True, exist_ok=True)
    figure.tight_layout()
    figure.savefig(output_path, dpi=160)
    plt.close(figure)


def parse_arguments() -> argparse.Namespace:
    """定义并解析命令行参数。"""

    parser = argparse.ArgumentParser(
        description="读取 timestamp,x,y,z CSV 并输出 3D PNG。"
    )
    parser.add_argument("--input", required=True, type=Path, help="输入 CSV 路径")
    parser.add_argument("--output", required=True, type=Path, help="输出 PNG 路径")
    parser.add_argument("--source", required=True, help="源坐标系名称")
    parser.add_argument("--target", required=True, help="目标坐标系名称")
    return parser.parse_args()


def main() -> int:
    """程序入口：解析参数、读取 CSV、绘图并报告结果。"""

    arguments = parse_arguments()

    try:
        # 读取阶段只负责解析文件，不承担坐标变换。
        _, x_values, y_values, z_values = read_trajectory_csv(arguments.input)
        plot_trajectory(
            x_values,
            y_values,
            z_values,
            arguments.input,
            arguments.output,
            arguments.source,
            arguments.target,
        )
    except (OSError, ValueError) as error:
        print(f"绘图失败: {error}")
        return 1

    print(f"绘图完成: {arguments.output}（{len(x_values)} 个点）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
