# 测试

这里保存项目的最小自动化测试，当前覆盖：

- 命令行参数检查；
- 图像缩放尺寸；
- 运动区域检测；
- 处理 FPS 和平均运动面积计算。

在项目根目录运行：

```bash
export PYTHONPATH=src
python3 -m unittest discover -s tests -p 'test_*.py' -v
```
