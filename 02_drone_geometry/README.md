# 02_drone_geometry

无人机坐标变换与轨迹可视化工具。项目用 C++17、CMake 和 Eigen 完成三维轨迹的 CSV 读写与刚体变换，用 GoogleTest/CTest 验证核心数学关系，再用 Python/Matplotlib 生成 3D 图。

本项目使用合成数据和固定变换验证程序结构，不代表真实传感器标定、PX4 飞控或真实飞行结果。

## 项目目标

- 用明确的 `T_target_source` 表达源坐标系到目标坐标系的变换；
- 读取 `timestamp,x,y,z` 轨迹 CSV 并输出转换后的 CSV；
- 用测试验证旋转、平移、距离、方向和异常输入；
- 用 Python 读取导出的 CSV，生成单轨迹图和变换前后对比图；
- 保留可复现的 CMake、CTest、命令行和文档流程。

## 坐标系约定

```text
# p_source 是源坐标系中的点，p_target 是目标坐标系中的点。
p_target = R_target_source * p_source + t_target_source
```

当前示例约定：

| 名称 | 轴方向 |
|---|---|
| `body_flu` | X=Forward，Y=Left，Z=Up |
| `world_enu` | X=East，Y=North，Z=Up |

示例变换为绕 Z 轴正方向旋转 90°，再平移 `(10,-2,1)`。四元数参数顺序固定为 `qw,qx,qy,qz`，程序会在使用前归一化。详细说明见 [`docs/frames.md`](docs/frames.md)。

## 目录结构

```text
02_drone_geometry/
├── CMakeLists.txt
├── include/                    # C++ 接口声明
├── src/                        # C++ 实现和命令行入口
├── tests/                      # GoogleTest 测试
├── apps/                       # 只负责读取 CSV 和绘图的 Python 脚本
├── data/                       # 输入样例和实验轨迹
├── docs/                       # 坐标系说明和实验记录
└── README.md
```

## 依赖

C++：

- GCC/G++，支持 C++17；
- CMake 3.22 或更高版本；
- Eigen3 3.3 或更高版本；
- GoogleTest（当前 WSL 环境检测到 1.11.0）。

Python：

- Python 3；
- Matplotlib（当前 WSL 环境检测到 3.5.1）。

## 构建和测试

在项目根目录执行：

```bash
# 进入最终作品仓库。
cd /home/chald/project/drone-geometry

# 使用独立 build/ 目录生成构建文件。
cmake -S . -B build

# 编译核心库、命令行程序和测试。
cmake --build build

# 运行全部 C++ 测试。
ctest --test-dir build --output-on-failure
```

如果要验证不依赖旧缓存，可以只删除这个项目自己的构建目录：

```bash
# 只删除 drone-geometry/build，不要删除用户主目录。
rm -rf build
cmake -S . -B build
cmake --build build
ctest --test-dir build --output-on-failure
```

## 运行 C++ 坐标变换

```bash
# 把 body_flu 中的样例轨迹转换到 world_enu。
./build/transform_trajectory \
    --input data/sample.csv \
    --output data/sample_world.csv \
    --source body_flu \
    --target world_enu \
    --tx 10 --ty 0 --tz 0 \
    --qw 0.7071067811865476 --qx 0 \
    --qy 0 --qz 0.7071067811865476
```

命令行参数：

| 参数 | 作用 |
|---|---|
| `--input` | 输入 CSV 路径 |
| `--output` | 输出 CSV 路径 |
| `--source` | 源坐标系名称 |
| `--target` | 目标坐标系名称 |
| `--tx --ty --tz` | 平移向量 |
| `--qw --qx --qy --qz` | 四元数，顺序为 w,x,y,z |

## 生成和查看轨迹图

先用相同变换生成两条实验轨迹的输出：

```bash
# 转换直线样例。
./build/transform_trajectory \
    --input data/line_source.csv \
    --output data/line_transformed.csv \
    --source body_flu --target world_enu \
    --tx 10 --ty -2 --tz 1 \
    --qw 0.7071067811865476 --qx 0 \
    --qy 0 --qz 0.7071067811865476

# 转换矩形样例。
./build/transform_trajectory \
    --input data/rectangle_source.csv \
    --output data/rectangle_transformed.csv \
    --source body_flu --target world_enu \
    --tx 10 --ty -2 --tz 1 \
    --qw 0.7071067811865476 --qx 0 \
    --qy 0 --qz 0.7071067811865476
```

生成单条 3D 图：

```bash
# Python 只负责读取 CSV 和绘图，不重新计算坐标变换。
python3 apps/plot_trajectory.py \
    --input data/line_transformed.csv \
    --output outputs/line_transformed.png \
    --source body_flu --target world_enu
```

生成变换前后对比图：

```bash
# 左图是源坐标系轨迹，右图是目标坐标系轨迹。
python3 apps/compare_trajectories.py \
    --before data/line_source.csv \
    --after data/line_transformed.csv \
    --output outputs/line_comparison.png \
    --source body_flu --target world_enu
```

## CSV 格式

第一行必须严格为：

```text
timestamp,x,y,z
```

| 列 | 含义 | 单位 |
|---|---|---|
| `timestamp` | 时间戳，输出时原样保留 | 秒 |
| `x`、`y`、`z` | 三维位置 | 米 |

当前只支持不带引号、单元格中不含逗号的简单 CSV。

## 示例结果

一次正常运行的日志：

```text
转换完成: body_flu -> world_enu
点数: 3
输出: data/sample_world.csv
```

直线样例的预期结果：原始轨迹沿 X 正方向，旋转后沿 Y 正方向；首点为 `(10,-2,1)`，尾点为 `(10,2,1)`，长度仍为 4 米。完整实验记录见 [`docs/experiments.md`](docs/experiments.md)。

## 已知限制

- 不处理完整 CSV 方言中的引号字段和单元格内逗号；
- 当前变换参数由命令行直接提供，没有坐标系配置文件；
- `body_flu`、`world_enu` 和外参是练习约定，不是真实标定结果；
- 不处理时间戳插值、丢点、重复点或多轨迹同步；
- Python 只生成静态 PNG；
- 当前没有接入 ROS 2、TF2、PX4 或真实传感器。

## 未来 ROS 2 对接点

以下内容尚未实现，只是后续接口方向：

1. 用 ROS 2 节点订阅 `nav_msgs/msg/Path` 或 `geometry_msgs/msg/PoseStamped`；
2. 用 `tf2` 查询坐标系之间的实时变换，替代命令行固定外参；
3. 将帧名映射到真实 TF tree，并明确记录 ROS、PX4 和相机各自的轴约定；
4. 保留 CSV/PNG 作为离线回归测试，实时节点负责消息接收、变换和发布；
5. 用实测标定结果替换当前合成旋转和平移。

## 相关文档

- [`docs/frames.md`](docs/frames.md)：坐标系、轴方向和符号约定；
- [`docs/experiments.md`](docs/experiments.md)：变换前后轨迹的预期与观察结果。
