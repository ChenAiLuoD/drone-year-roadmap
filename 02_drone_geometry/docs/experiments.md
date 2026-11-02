# 轨迹变换实验记录

## 实验 1：直线轨迹

| 项目 | 记录 |
|---|---|
| 原始坐标系 | `body_flu` |
| 目标坐标系 | `world_enu` |
| 输入文件 | `data/line_source.csv` |
| 输出文件 | `data/line_transformed.csv` |
| 变换 | 绕 Z 轴正方向旋转 90°，再平移 `(10,-2,1)` |
| 数学形式 | `p_target = R_z(90°) p_source + (10,-2,1)` |
| 预期 | 原来沿 X 轴的直线应转到 Y 轴正方向；长度仍为 4 米；首点变为 `(10,-2,1)`，尾点变为 `(10,2,1)`。 |
| 观察结果 | 对比图中轨迹由 X 方向变为 Y 方向，长度没有改变；CSV 首点为 `(10,-2,1)`，尾点为 `(10,2,1)`，与预期一致。 |

## 实验 2：矩形轨迹

| 项目 | 记录 |
|---|---|
| 原始坐标系 | `body_flu` |
| 目标坐标系 | `world_enu` |
| 输入文件 | `data/rectangle_source.csv` |
| 输出文件 | `data/rectangle_transformed.csv` |
| 变换 | 绕 Z 轴正方向旋转 90°，再平移 `(10,-2,1)` |
| 数学形式 | `p_target = R_z(90°) p_source + (10,-2,1)` |
| 预期 | 矩形的宽高和周长保持；起点和终点都应变为 `(10,-2,1)`；第一条边由 X 方向变为 Y 正方向。 |
| 观察结果 | 对比图中矩形只是旋转和平移，没有缩放或变形；首尾仍重合，第一条边指向 Y 正方向，与预期一致。 |

## 复现命令

在 `drone-geometry` 项目根目录执行：

```bash
# 先生成直线和矩形的变换结果。
./build/transform_trajectory \
    --input data/line_source.csv \
    --output data/line_transformed.csv \
    --source body_flu --target world_enu \
    --tx 10 --ty -2 --tz 1 \
    --qw 0.7071067811865476 --qx 0 \
    --qy 0 --qz 0.7071067811865476

./build/transform_trajectory \
    --input data/rectangle_source.csv \
    --output data/rectangle_transformed.csv \
    --source body_flu --target world_enu \
    --tx 10 --ty -2 --tz 1 \
    --qw 0.7071067811865476 --qx 0 \
    --qy 0 --qz 0.7071067811865476

# 再生成变换前后对比图。
python3 apps/compare_trajectories.py \
    --before data/line_source.csv \
    --after data/line_transformed.csv \
    --output outputs/line_comparison.png \
    --source body_flu --target world_enu

python3 apps/compare_trajectories.py \
    --before data/rectangle_source.csv \
    --after data/rectangle_transformed.csv \
    --output outputs/rectangle_comparison.png \
    --source body_flu --target world_enu
```
