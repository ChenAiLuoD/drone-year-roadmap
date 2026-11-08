# 环境与基线记录

## 环境

- 日期：2026-11-08
- 项目路径：/home/chald/project/03_aerial-detection-tracking
- 系统：Ubuntu 22.04（WSL）
- Python：3.10.12
- 虚拟环境：.venv-project
- 数据源：UAVDT-Benchmark-M

## 安装记录

~~~bash
python3 -m venv .venv-project
source .venv-project/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pip freeze > requirements-lock.txt
yolo checks
~~~

## 基线记录

基线使用现成的 yolo26n.pt，不代表本项目训练结果。

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

输出目录、运行日志、输入视频哈希和硬件信息应保留在本地 outputs/，不提交原始视频或模型权重。

## 本次实际结果

- 安装结果：成功
- Ultralytics：8.4.207
- PyTorch：2.14.1+cu130
- GPU：NVIDIA GeForce RTX 4060 Laptop GPU，CUDA 13.0
- 模型：yolo26n.pt（Ultralytics 预训练权重）
- 输入：video_a.mp4，2,824 帧，3840×2160，约 94.14 秒
- 推理设置：imgsz=640、conf=0.25、device=0
- 速度记录：预处理 3.5 ms、推理 13.8 ms、后处理 2.0 ms／帧（Ultralytics 汇总）
- 输出视频：outputs/baseline/video_a_yolo26n/
- 输出标签：outputs/baseline/video_a_yolo26n/labels/，679 个标签文件
- 结论：这是通用预训练模型的原始基线，不是本项目训练成绩；后续训练模型必须单独记录。
