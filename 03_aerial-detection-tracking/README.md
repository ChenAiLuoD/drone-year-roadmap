# Aerial Detection and Tracking

航拍车辆目标检测与多目标跟踪月度项目。

## 项目目标

使用公开航拍数据完成一条可复现的视觉数据闭环：读取数据、理解原始标注、按完整视频序列切分、转换为 YOLO 格式、训练轻量检测模型，再将检测结果接入多目标跟踪器，输出带类别、置信度和轨迹 ID 的结果视频。

本项目不接入 ROS 2、PX4、Gazebo 或真实飞控；本月只覆盖视觉检测、视频跟踪、指标和失败分析。

## 当前阶段

第 1 周：任务定义、数据来源、标注规则、序列切分、项目骨架和预训练基线。

## 数据源

主数据集：UAVDT-Benchmark-M。

相关官方资料：

- 数据集主页：https://sites.google.com/view/grli-uavdt
- DET/MOT toolkit：项目内的 data/UAVDT-DET-MOT-toolkit/
- Attributes：项目内的 data/UAVDT-Attributes/
- 访问日期：2026-11-08

原始类别：car、truck、bus。

第一版项目类别：单类 vehicle。

类别映射：

~~~text
car / truck / bus -> vehicle -> YOLO class 0
~~~

原始数据只用于本地研究和学习，不提交到 Git，也不公开上传可还原数据集的原始帧、标注、忽略区域或属性文件。

## 环境

- 系统：Ubuntu 22.04（WSL）
- Python：3.10.12
- 项目虚拟环境：.venv-project/
- 依赖文件：requirements.txt
- 精确环境记录：requirements-lock.txt

安装：

~~~bash
python3 -m venv .venv-project
source .venv-project/bin/activate
python -m pip install -r requirements.txt
~~~

## 数据和标注

原始图像按序列存放在 data/UAVDT-Benchmark-M/；完整检测标注在 data/UAVDT-DET-MOT-toolkit/GT/*_gt_whole.txt；跟踪真值在 *_gt.txt；忽略区域在 *_gt_ignore.txt。

详细规则见：

- data/README.md
- docs/annotation-guide.md
- docs/split-policy.md

转换后的 YOLO 数据仍放在 data/ 下但被 .gitignore 排除。原始目录不改写。

## 基线推理

预训练基线使用 Ultralytics 的轻量 YOLO 权重，仅用于观察通用模型在航拍画面上的表现，不代表本项目训练结果：

~~~bash
yolo predict \
  model=yolo26n.pt \
  source=/home/chald/project/study_3/01/day3/inputs/video_a.mp4 \
  imgsz=640 \
  conf=0.25 \
  device=0 \
  save=True \
  save_txt=True \
  save_conf=True \
  project="$(pwd)/outputs/baseline" \
  name=video_a_yolo26n \
  2>&1 | tee outputs/baseline/video_a.log
~~~

## 评估指标

训练完成后记录 Precision、Recall、mAP50、mAP50-95、混淆矩阵和端到端 FPS；每项结果同时记录模型、数据版本、输入尺寸、阈值、硬件和计时范围。跟踪阶段额外记录 ID 切换、轨迹中断和短暂丢失。

## Git 边界

不提交：原始数据、转换数据、视频、模型权重、缓存、运行输出和包含数据内容的截图。提交代码、配置、数据卡、标注规则、切分清单、命令和汇总指标。
