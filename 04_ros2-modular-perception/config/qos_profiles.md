# 首版 QoS 配置（v0.1）

更新日期：2026-11-25

## 应用范围

- /camera/image_raw：源视频图像，sensor_msgs/Image
- /perception/detections：二维检测结果，vision_msgs/Detection2DArray
- /perception/tracks：带轨迹 ID 的二维检测结果，vision_msgs/Detection2DArray
- /perception/annotated_image：叠加轨迹后的图像，sensor_msgs/Image

## 固定配置

四个 Topic 均使用：

- History：KEEP_LAST
- Depth：10
- Reliability：RELIABLE
- Durability：VOLATILE

KEEP_LAST(10) 只保留最近十条消息，限制下游暂时变慢时的积压量。当前项目处理本地短视频，目标是可复现实验链路，因此使用 RELIABLE，不主动采用可能丢帧的 BEST_EFFORT。VOLATILE 使晚启动节点不接收历史帧，避免旧图像与新轨迹在可视化阶段错误配对。

## 实际问题与结论

第 3 天曾出现图像和轨迹缓存超时。排查后发现原因是上游节点未同时正常运行，或模型冷启动使同一时间戳的数据未在缓存期限内配对；这属于 pair_cache 的时间同步问题，而不是 QoS 不兼容。

完整启动视频源、检测、跟踪、可视化节点，并把可视化缓存临时设为十秒后，已生成 annotated_frame0000.png。因此首版保留 RELIABLE；不通过改为 BEST_EFFORT 掩盖启动顺序或缓存超时问题。

## 验证与观察

代码中的四份 PERCEPTION_QOS 均明确设置 History=KEEP_LAST、Depth=10、Reliability=RELIABLE、Durability=VOLATILE。

使用 ros2 topic info -v 检查 /perception/tracks 时，tracker_node 发布端和 visualizer_node 订阅端均显示 RELIABLE 和 VOLATILE，证明两端 QoS 兼容。

本机 ROS 中间件在该命令中将 History (Depth) 显示为 UNKNOWN；因此该项以源码中的显式 QoSProfile 定义为准，不能把 UNKNOWN 误解为没有设置队列深度。
