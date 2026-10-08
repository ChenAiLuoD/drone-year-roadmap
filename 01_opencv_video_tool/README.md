# 航拍视频分析工具

## 1. 项目目标

这是一个基于 Python 和 OpenCV 的航拍视频分析工具，能够：

- 读取录制好的视频；
- 获取视频 FPS、分辨率、总帧数和时长；
- 按指定间隔抽帧；
- 缩放视频画面；
- 根据相邻帧差检测变化区域；
- 在画面中绘制运动区域框和统计文字；
- 输出处理后的视频、统计报告和运行日志。

当前版本主要用于学习完整的视频处理流程：

```text
输入视频 → 读取信息 → 逐帧处理 → 写出结果视频 → 生成报告和日志
```

## 2. 项目目录

```text
drone-video-tool/
├── src/
│   └── drone_video_tool/
│       ├── __init__.py
│       ├── cli.py          # 命令行参数和主流程
│       ├── video_io.py     # 视频读取、信息获取和视频写出
│       ├── processing.py   # 缩放、帧差、画框和文字叠加
│       └── metrics.py      # FPS、运动面积和 JSON 报告统计
├── tests/
│   ├── __init__.py
│   ├── test_cli.py
│   ├── test_processing.py
│   └── test_metrics.py
├── data/                   # 本地测试视频，不提交大文件
├── outputs/                # 处理结果，不提交到仓库
├── requirements.txt
├── .gitignore
└── README.md
```

## 3. 环境要求

- Linux、WSL 或其他能够运行 Python 的环境；
- Python 3.10 或更高版本；
- OpenCV 4.8 及以上、5 以下版本；
- 输入视频需要是当前 OpenCV 后端能够解码的格式；
- 本项目不要求摄像头，默认使用录制好的视频文件。

## 4. 创建环境和安装依赖

在项目根目录执行：

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install --upgrade pip
python3 -m pip install -r requirements.txt
```

确认 OpenCV 已安装：

```bash
python3 -c "import cv2; print(cv2.__version__)"
```

项目采用 `src` 目录布局。运行前设置源码路径：

```bash
export PYTHONPATH="$PWD/src"
```

## 5. 运行命令

先将测试视频放入 `data/`，例如：

```text
data/video_20261008_091640.mp4
```

运行程序：

```bash
python3 -m drone_video_tool.cli \
  --input data/video_20261008_091640.mp4 \
  --output-dir outputs \
  --scale 0.5
```

多行命令中的反斜杠必须是每行最后一个字符，后面不要再加空格。

## 6. 参数说明

| 参数 | 是否必需 | 默认值 | 作用 |
| :--- | :--- | :--- | :--- |
| `--input` | 是 | 无 | 输入视频路径 |
| `--output-dir` | 否 | `outputs` | 输出目录 |
| `--sample-every` | 否 | `1` | 每隔多少帧处理一次 |
| `--scale` | 否 | `1.0` | 输出画面的缩放比例 |
| `--motion-threshold` | 否 | `25` | 帧差二值化阈值 |
| `--min-area` | 否 | `500` | 忽略小于该面积的变化区域 |
| `--display` | 否 | 关闭 | 显示实时处理窗口；无图形界面时不要使用 |

例如，每 5 帧处理 1 帧，并缩放到原来的一半：

```bash
python3 -m drone_video_tool.cli \
  --input data/sample.mp4 \
  --output-dir outputs/sample_test \
  --sample-every 5 \
  --scale 0.5
```

## 7. 输出文件

例如输出目录是 `outputs/sample_test/`，程序会生成：

```text
outputs/sample_test/
├── result.mp4       # 处理后的视频画面
├── report.json      # 输入、输出、参数和统计数据
└── processing.log   # 运行过程和错误日志
```

`report.json` 中包括：

- 输入 FPS、宽度、高度、总帧数和时长；
- 输出 FPS、尺寸和处理帧数；
- 抽帧、缩放、阈值和最小面积参数；
- 总处理时间、平均处理 FPS 和平均运动区域面积。

## 8. 运行测试

在项目根目录执行：

```bash
source .venv/bin/activate
export PYTHONPATH="$PWD/src"
python3 -m unittest discover -s tests -p 'test_*.py' -v
```

当前最小测试覆盖：

- 输入文件和参数检查；
- 图像缩放尺寸；
- 运动区域检测；
- 平均处理 FPS 和运动面积计算。

## 9. 三种视频格式测试记录

建议至少测试以下三种编码组合：

| 输入文件 | 容器/编码器 | 能否读取 | 能否写出 | 结果能否播放 | 备注 |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `sample_h264.mp4` | MP4/H.264 | 待填写 | 待填写 | 待填写 |  |
| `sample_mp4v.mp4` | MP4/MPEG-4 | 待填写 | 待填写 | 待填写 |  |
| `sample_mjpg.avi` | AVI/MJPG | 待填写 | 待填写 | 待填写 |  |

每种格式使用单独的输出目录，避免 `result.mp4`、`report.json` 和日志互相覆盖：

```bash
python3 -m drone_video_tool.cli \
  --input data/sample_h264.mp4 \
  --output-dir outputs/test_h264 \
  --scale 0.5
```

## 10. 已知限制

- 当前 OpenCV 流程只处理视频画面，不会自动保留原视频音频；
- 运动框来自相邻帧差，不是真正的目标检测，不能直接说明识别出了人、车或无人机；
- 不保证所有视频容器和编码器都兼容，能否读取取决于本机 OpenCV 后端和系统编解码器；
- 当前主要使用录制好的视频文件，不要求摄像头输入；
- 实时处理时，如果实际处理 FPS 低于输入 FPS，程序可能跟不上实时画面；
- 抽帧后会同步降低输出 FPS 以尽量保持视频时长，但画面时间细节会减少；
- 当前版本输出固定名称为 `result.mp4`，重复运行到同一目录时可能覆盖结果视频和 JSON 报告；
- 运动检测适合学习和简单变化分析，不等同于目标检测、目标跟踪或无人机自主决策系统。
