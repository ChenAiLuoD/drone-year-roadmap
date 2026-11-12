# 第 3 周第 1 天：训练配置与短跑记录

## 目的

今天先不追求模型效果，而是确认“配置 → 数据 → 训练 → 日志 → 输出”的链路能跑通。短跑训练只使用 1 个 epoch，属于工程验收，不是最终基线结果。

## 固定配置

| 项目 | 值 | 作用 |
| --- | --- | --- |
| 模型规格 | `yolo26n.pt` | 轻量 YOLO 预训练模型 |
| 输入尺寸 | `640` | 训练时把图像缩放到 640 像素规格 |
| epoch | `1` | 只做一次短跑，检查链路 |
| batch | `4` | 每次同时处理 4 张图像 |
| 随机种子 | `20261112` | 尽量让同配置结果可复现 |
| 数据版本 | `uavdt-yolo-v0.2` | 第二周生成的单类 `vehicle` 数据 |
| 设备 | `CUDA:0` | 使用第 0 张 GPU（RTX 4060 Laptop GPU） |
| 类别 | `0: vehicle` | 车辆统一为一个类别 |

配置文件：`configs/train_baseline.yaml`。

数据入口文件：`configs/dataset_v0.2.yaml`。它只记录本机数据根目录和 `train/val/test` 子目录，不把数据集本身提交到 Git。

## 训练前检查

数据检查脚本通过：

| 划分 | 图像/标签 | 错误 |
| --- | ---: | ---: |
| train | 764 / 764 | 0 |
| val | 216 / 216 | 0 |
| test | 673 / 673 | 0 |

训练环境为 Ubuntu 22.04（WSL）、Python 3.10.12、Ultralytics 8.4.207、PyTorch 2.14.1+cu130；CUDA 可用。

## 运行命令

```bash
# 进入项目并启用项目虚拟环境。
cd ~/project/03_aerial-detection-tracking
source .venv-project/bin/activate

# 使用固定 YAML 配置执行短跑训练，同时把终端输出保存成日志。
python scripts/train_short.py 2>&1 | tee outputs/week3_day1_short_train.log
```

脚本 `scripts/train_short.py` 会先检查模型文件和数据配置是否存在，再打印本次实验条件，最后调用 Ultralytics 训练接口。代码中的关键步骤都保留了中文注释。

## 实际结果

输出目录：

`runs/week3_day1/baseline_short_seed20261112-2/`

训练完成并生成 `results.csv`、`results.png`、混淆矩阵、样例图和 `weights/best.pt`/`last.pt`。本次短跑的汇总指标为：

| 指标 | 值 |
| --- | ---: |
| Precision | 0.56371 |
| Recall | 0.56349 |
| mAP50 | 0.58546 |
| mAP50-95 | 0.28080 |

这些数值只用于确认训练和验证阶段都成功执行，不能当作最终模型性能结论。

## 问题与修正

1. 第一次运行提示缺少 `yaml` 模块，已在项目环境安装 `PyYAML==6.0.2`，并更新 `requirements.txt` 与 `requirements-lock.txt`。
2. 原始数据集配置中的相对路径会被训练进程按项目目录解释，导致找不到 `images/val`。未修改外部数据集文件，而是在项目内增加 `configs/dataset_v0.2.yaml`，用绝对路径明确指向数据版本。

## 下一步

第 2 天再把 epoch、batch 等调整为正式基线规模，比较合成轨迹或数据样例，并继续记录模型、数据版本、设备和日志路径。
