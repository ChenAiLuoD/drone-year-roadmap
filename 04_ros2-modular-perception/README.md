# ROS 2 航拍感知链路

这是第 4 月的 ROS 2 模块化感知项目：把第 3 月已训练的二维车辆检测模型接入视频源、检测、跟踪与可视化流水线。公开仓库只保留源码、参数模板和文字证据；视频、权重、rosbag、构建产物与批量图片不提交。

## 节点与 Topic

~~~
video_source_node -> /camera/image_raw
detector_node -> /perception/detections
tracker_node -> /perception/tracks
visualizer_node -> /perception/annotated_image
~~~

- video_source_node：读取离线视频，发布 BGR 图像和来源时间戳。
- detector_node：对图像执行 YOLO 二维检测。
- tracker_node：以贪心 IoU 匹配为视频内目标分配轨迹 ID。
- visualizer_node：按相同时间戳配对图像和轨迹，绘制框、类别、置信度和 ID。

消息定义和时间约定见 [docs/interfaces.md](docs/interfaces.md) 与 [docs/time-and-frames.md](docs/time-and-frames.md)。

## 环境边界

项目运行于 Ubuntu 22.04 与 ROS 2 Humble。检测节点依赖第 3 月虚拟环境中的 Ultralytics、PyTorch 和模型权重。ROS 的 cv_bridge 使用系统 Python 二进制扩展，可能和该虚拟环境的 NumPy 2 冲突，所以 Launch 只将第 3 月 site-packages 传给 detector_node。

## 构建

在本目录运行：

~~~bash
source /opt/ros/humble/setup.bash
colcon build --packages-select video_source detector tracker visualizer perception_bringup
source install/setup.bash
~~~

## 参数与 Launch

先编辑 src/perception_bringup/config/pipeline.yaml 中的 input_path 和 model_path，填入你机器上的绝对路径。也可以复制该文件为 pipeline.local.yaml；它已被 Git 忽略，并可通过 params_file 传入。

~~~bash
source /opt/ros/humble/setup.bash
source install/setup.bash
export MONTH3_ROOT=/absolute/path/to/03_aerial-detection-tracking

ros2 launch perception_bringup perception_pipeline.launch.py   detector_pythonpath:="$MONTH3_ROOT/.venv-project/lib/python3.10/site-packages"   max_frames:=30
~~~

Launch 先启动检测、跟踪、可视化，默认等待 10 秒再启动视频源，减少模型冷启动造成的早期消息丢失。视频结束后下游节点仍会等待消息，按 Ctrl+C 关闭。

QoS 首版为 KEEP_LAST(10)、RELIABLE、VOLATILE；选择理由见 [config/qos_profiles.md](config/qos_profiles.md)。

## rosbag 重放

最小重放输入只录制 /camera/image_raw。重放时不要再启动 video_source_node，以免两个发布者同时发送该 Topic。

~~~bash
ros2 bag record -o outputs/input_image_bag /camera/image_raw
ros2 bag play outputs/input_image_bag --rate 1.0
~~~

样例 bag 的 30 条消息记录见 [docs/week4-day1-bag-record.md](docs/week4-day1-bag-record.md)。原始 bag 因为超过 700 MiB 不在仓库中。

## 测试与验收

~~~bash
source /opt/ros/humble/setup.bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 colcon test --event-handlers console_direct+
colcon test-result --all --verbose
~~~

干净构建验收记录为 27 tests、0 errors、0 failures、4 skipped。详细过程见 [docs/week4-day6-acceptance.md](docs/week4-day6-acceptance.md)。

## 当前已知问题

输入 rosbag 有 30 条图像；最近三次受控回放中，检测、跟踪和标注图像各得到 29 条，缺少末帧。降低回放速率和增加启动延迟后问题仍存在，尚未通过修改阈值、QoS 或模型逻辑掩盖。后续需要区分播放器末帧投递、订阅队列与节点收尾的原因。

性能记录见 [docs/week4-day4-performance.md](docs/week4-day4-performance.md)。第 5 月接入 PX4、MAVLink 与 Gazebo 前，需要替换输入端为仿真相机 Topic，并重新核验图像编码、时间基准、frame_id、QoS、CameraInfo 与标定信息。
