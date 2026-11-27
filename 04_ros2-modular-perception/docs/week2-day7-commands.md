# 第 2 周第 7 天：构建、运行与停止记录

## 构建

```bash
cd /path/to/04_ros2-modular-perception
source /opt/ros/humble/setup.bash
colcon build --packages-select video_source detector
source install/setup.bash