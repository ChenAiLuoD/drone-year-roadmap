# 第 4 周第 6 天：干净构建与端到端验收

日期：2026-11-26

## 1. 验收范围

本次从空的 `build/`、`install/`、`log/` 目录开始，构建 `video_source`、`detector`、`tracker`、`visualizer`、`perception_bringup` 五个包；随后执行完整测试、正常视频 Launch、关闭视频源后的 rosbag 回放和标注图保存。

## 2. 干净构建与测试

- 构建结果：5 个包全部完成。
- 测试环境：`PYTHONNOUSERSITE=1`，避免用户目录的 NumPy 2 覆盖 ROS 系统 OpenCV/cv_bridge；`PYTEST_DISABLE_PLUGIN_AUTOLOAD=1`，避开本机 `launch_testing` 与 Pytest 插件兼容问题。
- 汇总：27 tests，0 errors，0 failures，4 skipped（版权检查）。
- 日志：`clean_build.log`、`clean_test.log`、`clean_test_result.log`。

本次修正的源文件格式问题：`video_source/setup.py`、`detector/setup.py` 的 `entry_points` 缩进；三个 Python 文件缺少末尾换行；`visualizer_node.py` 有一行空白行包含空格。未改变节点运行逻辑。

## 3. 正常视频 Launch

- 启动方式：`perception_pipeline.launch.py`，`max_frames:=30`，仅向检测节点传入第 3 个月虚拟环境的 `detector_pythonpath`。
- 运行中节点：`/video_source_node`、`/detector_node`、`/tracker_node`、`/visualizer_node`、`/image_saver_node`。
- 运行中 Topic：`/camera/image_raw`、`/perception/detections`、`/perception/tracks`、`/perception/annotated_image`。
- 日志计数：检测 30、跟踪 30、标注图像 30。
- 样例：`normal_annotated0000.png`。
- 说明：Launch 在视频源结束后，下游节点仍常驻；本次由超时器发出 SIGINT 收尾。`normal_launch_status.txt` 的 124 表示受控超时结束，不表示节点错误。

## 4. rosbag 回放

- 输入 bag：`../week4_day1/input_image_bag_01`，`ros2 bag info` 为 30 条 `/camera/image_raw` 消息。
- 回放时只启动检测、跟踪、可视化；节点快照中没有 `video_source_node`。
- 回放 Topic：`/camera/image_raw`、`/perception/detections`、`/perception/tracks`、`/perception/annotated_image`。
- 回放标注结果：保存了 `replay_annotated0000.png` 等 PNG 文件。

## 5. 待核实项：末帧差异

两次独立回放（`--rate 1.0` 与 `--rate 0.6`）和一次带 `--delay 2` 的回放中，下游检测、跟踪、标注图像均新增 29 条；检测日志从源时间 `0.000s` 到 `0.467s`，缺少 bag 中应有的末帧 `0.484s`。

已排除的简单解释：三个下游节点在播放前已列出，检测模型已加载；降低播放速度和添加 2 秒播放器启动延迟仍未得到末帧。

当前结论：这是 rosbag 回放的待核实项，不能把 29 条写成完整 30 条，也不通过修改阈值、QoS 或模型逻辑掩盖。后续需要在交互式终端或以独立时间戳订阅器继续区分“播放器末帧投递”“订阅队列”“节点收尾”三类原因。

## 6. 输出文件

- 正常链路：`normal_launch.log`、`normal_topics_during.txt`、`normal_annotated0000.png`。
- 回放链路：`replay_final_detector.log`、`replay_final_tracker.log`、`replay_final_visualizer.log`、`replay_final_bag.log`、`replay_final_topics_ready.txt`。
- 首次回放的 29 条记录与保存图片保留在 `replay_*.log`、`replay_annotated*.png`，用于复查。
