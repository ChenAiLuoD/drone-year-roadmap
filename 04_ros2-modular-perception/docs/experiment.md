# 实验记录索引

本文件汇总可复查的关键实验；每次实验的参数、输入和日志路径优先于单张终端截图。

## 1. 单帧 ROS 与离线检测对照

- 输入：源视频第 0 帧，保存为 `outputs/day5/ros_frame0000.png`。
- 参数：同一 `best.pt`、`imgsz=640`、`conf=0.20`、`device=0`。
- 结果：类别 `vehicle`；ROS 置信度 `0.2364118993`，离线结果 `0.236412`；中心与宽高一致。
- 结论：ROS 封装未改变该帧的模型输入、阈值或输出。

## 2. 跟踪检查

- 输入：`video_c_pixabay_327970.mp4`，318 源帧。
- 参数：`TrackManager v0.1`、贪心 IoU、`iou_threshold=0.3`、`max_missed_frames=5`。
- 结果：12 条空检测；两处单帧检测缺失后，恢复目标保留原轨迹 ID。
- 边界：未依据叠加图像确认真实物理遮挡；未确认明确 ID 切换。
- 证据：[week3-day2-tracking-check.md](week3-day2-tracking-check.md)。

## 3. 四节点正常视频链路

- 启动：`perception_pipeline.launch.py`，在检测、跟踪、可视化初始化后启动视频源。
- 参数覆盖：`max_frames:=1`、`max_frames:=3` 均成功覆盖 YAML。
- 结果：视频源、检测、跟踪、可视化按顺序产生日志和对应 Topic 输出。
- 异常模型：设置 `/tmp/not-a-model.pt` 时，检测节点明确记录“模型文件不存在”，Launch 记录异常退出。

## 4. 最小 rosbag 与回放

- bag：`outputs/week4_day1/input_image_bag_01`。
- 存储：`sqlite3` / `cdr`；仅包含 `/camera/image_raw`。
- 内容：30 条 3840×2160 `bgr8` 图像，时长 14.2225 秒，大小 712.6 MiB。
- 回放：关闭视频源，仅启动检测、跟踪、可视化后播放 bag。
- 结果：原始与回放中，检测、跟踪、标注图像均发布 30 条；检测与跟踪的 `source_time` 都是 `0.000–0.484s`。
- 证据：`outputs/week4_day1/`、`outputs/week4_day3/`。

## 5. 吞吐记录的边界

- 输入 bag 的录制跨度频率为 `30 / 14.2225 = 2.109 Hz`。
- 检测和跟踪的最后一次 `ros2 topic hz` 观察窗口为 `2.158 Hz`，不能解释为稳定 YOLO FPS。
- 高分辨率图像 Topic 未获得可靠的 `ros2 topic hz` 平均值；可视化节点日志仍证明完整回放发布了 30 条标注图像。
- 没有逐阶段计时，因此不报告视频解码、YOLO、跟踪、绘制、写盘或端到端延迟。
- 详细记录：[../outputs/week4_day4/performance.md](../outputs/week4_day4/performance.md)。

## 6. 已知失败案例

| 情况 | 处理与结论 |
| :--- | :--- |
| NumPy 2 与 `cv_bridge` 冲突 | 第 3 个月虚拟环境只传给检测节点；视频源和可视化使用 ROS Python 环境。 |
| 图像与轨迹缓存超时 | 记录警告，不静默拼接不同帧；冷启动验证时使用 10 秒缓存超时。 |
| 视频源自动停止后下游仍运行 | 这是常驻订阅节点的预期行为，实验结束后使用 `Ctrl+C`。 |
| SIGINT 关闭日志 | 跟踪、可视化可出现 `KeyboardInterrupt`、退出码 `-2`；结合此前日志判断为关闭过程，而非推理失败。 |
