# ROS 2 航拍感知链路：接口约定 v0.2

更新日期：2026-11-26

## 1. 节点图

```text
video_source_node
  └─ /camera/image_raw                  sensor_msgs/msg/Image
          ↓
detector_node
  └─ /perception/detections             vision_msgs/msg/Detection2DArray
          ↓
tracker_node
  └─ /perception/tracks                 vision_msgs/msg/Detection2DArray
          ↓
visualizer_node
  └─ /perception/annotated_image        sensor_msgs/msg/Image
```

## 2. Topic 契约

| Topic | 发布者 → 订阅者 | 消息类型 | 最小内容 | 时间与错误约定 |
| :--- | :--- | :--- | :--- | :--- |
| `/camera/image_raw` | 视频源 → 检测、可视化 | `sensor_msgs/msg/Image` | `bgr8` 像素数据、宽高、`header` | `header.stamp` 为源视频帧时间，`frame_id=source_video_frame`。 |
| `/perception/detections` | 检测 → 跟踪 | `vision_msgs/msg/Detection2DArray` | 类别、置信度、二维框 | 数组与每个检测项复制输入图像的 `header`。空检测是合法的空数组。 |
| `/perception/tracks` | 跟踪 → 可视化 | `vision_msgs/msg/Detection2DArray` | 检测字段加当前视频内轨迹 ID | 复制检测消息的源图像时间；ID 仅在当前节点运行、当前视频内有效。 |
| `/perception/annotated_image` | 可视化 → 外部查看 | `sensor_msgs/msg/Image` | 原图叠加框、类别、置信度、ID | 仅在图像与轨迹 `stamp` 精确相同后发布。 |

## 3. 检测和跟踪字段

检测消息使用 ROS 已有的 `Detection2DArray`，不自定义二维检测消息：

- `header`：继承输入图像；
- `detections[].results[].hypothesis.class_id`：当前类别为 `vehicle`；
- `detections[].results[].hypothesis.score`：YOLO 置信度；
- `detections[].bbox.center.position.x/y`：二维框中心像素坐标；
- `detections[].bbox.size_x/size_y`：二维框宽、高；
- `detections[].id`：跟踪节点写入的轨迹 ID。

检测节点在消息构造时拒绝边界越界、左右颠倒或上下颠倒的框；没有候选框时发布合法空数组，而不是静默停止。

## 4. 时间、帧名和图像编码

- 源视频第 `i` 帧使用 `i / FPS` 作为 `header.stamp`；下游不改成推理完成的系统时间。
- `frame_id` 目前为 `source_video_frame`，只表示离线视频来源，不是已标定相机坐标系。
- OpenCV 图像使用 BGR 通道顺序，对应 `bgr8`。
- rosbag 回放时，下游结果继续保留保存于图像消息内的源时间。已验证的检测与跟踪时间范围为 `0.000–0.484s`。

完整说明见 [time-and-frames.md](time-and-frames.md)。

## 5. QoS

四个 Topic 当前都使用：

```text
KEEP_LAST(10) + RELIABLE + VOLATILE
```

`VOLATILE` 意味着晚启动订阅者不会补收旧帧。因此，测试时需要先启动下游，再启动视频源或播放 bag。理由、实验现象和 `ros2 topic info -v` 核验见 [../config/qos_profiles.md](../config/qos_profiles.md)。

## 6. 可视化配对与缓存行为

可视化不是把“最新图像”与“最新跟踪框”直接拼在一起，而是：

1. 缓存图像和轨迹消息；
2. 用完全相同的 `header.stamp` 配对；
3. 配对成功才绘制和发布；
4. 缓存过大、图像超时或轨迹超时时记录警告并丢弃过期项。

这保证标注图像对应同一来源视频帧。冷启动时，模型加载可能较慢；本项目用 `cache_timeout_seconds=10.0` 验证过完整配对。

## 7. 当前边界

- 不发布真实标定得到的 `CameraInfo`；
- 不把二维框或轨迹 ID 解释成三维位置、地理坐标或真实车辆身份；
- 当前 IoU 跟踪器在遮挡过长、目标重新出现位置变化大或车辆交叉时可能更换 ID；
- 未提供 rosbag 回放模式的一键 Launch；回放时需关闭视频源，只启动三个下游节点。
