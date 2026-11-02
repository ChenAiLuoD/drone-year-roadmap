# 坐标系与变换约定

## 项目内部约定

本仓库只使用明确写出的项目约定，不把 ROS、PX4 和相机的轴定义混为一谈。

| 帧名 | X 轴 | Y 轴 | Z 轴 | 当前用途 |
|---|---|---|---|---|
| `body_flu` | Forward，前 | Left，左 | Up，上 | 项目示例机体系 |
| `world_enu` | East，东 | North，北 | Up，天 | 项目示例世界系 |

这里的 `body_flu` 是本项目内部教学约定；它不是在声明所有飞控或传感器都使用同一套机体系。

## 变换记号

`T_target_source` 的含义是：把一个点从 source 坐标表示转换成 target 坐标表示。

```text
# p_source 和 p_target 是同一个物理点在不同坐标系下的坐标。
p_target = R_target_source * p_source + t_target_source
```

- `R_target_source`：source 到 target 的旋转矩阵；
- `t_target_source`：平移向量，单位为米；
- `T_target_source`：旋转和平移组成的刚体变换。

## 本项目的合成示例

示例使用绕 Z 轴正方向旋转 90°，再平移 `(10,-2,1)`：

```text
p_target = R_z(90°) * p_source + (10,-2,1)
```

因此，source 中的单位 X 方向会变成 target 中的单位 Y 正方向；刚体变换不会改变点之间的距离。

## 与 ROS、PX4、相机约定的边界

| 来源 | 本项目处理方式 |
|---|---|
| ROS 2 | 未来可用 `tf2` 管理实际帧变换；当前没有接入 ROS 2。 |
| PX4 | 未来接入时必须单独核对飞控消息的坐标约定；不能直接假设等于 `body_flu`。 |
| 相机 | 光学坐标系常有自己的轴方向；未来加入相机外参时必须记录来源和标定结果。 |

当前仓库只验证合成的离线轨迹，不声称已经完成 ROS 2、PX4、相机标定或真实飞行验证。
