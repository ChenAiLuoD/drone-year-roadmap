- 正常链路中，visualizer 发布
  `/perception/annotated_image`，时间戳为 `(0, 0)`，
  检测数量为 `1`。
- image_saver 保存
  `outputs/week3_day3/annotated_frame0000.png`。
- 以默认缓存等待 2 秒运行时，图像与轨迹结果曾分别触发超时日志；
  未发生静默丢弃。
- 使用 `cache_timeout_seconds:=10.0` 进行冷启动验证后，
  同时间戳的图像与轨迹结果成功配对并生成标注图。