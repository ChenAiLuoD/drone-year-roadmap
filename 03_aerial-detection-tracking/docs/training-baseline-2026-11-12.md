# 第 3 周第 2 天：完整基线训练记录

## 目的

用第 2 周已经检查过的数据集，按照固定的模型、输入尺寸、训练轮数、随机种子和设备完成一次完整基线训练。这里得到的是后续比较模型改动的参照线，不是最终测试成绩。

## 实际使用的固定条件

| 项目 | 值 |
| --- | --- |
| 模型 | `yolo26n.pt` |
| 数据版本 | `uavdt-yolo-v0.2` |
| 类别 | `0: vehicle` |
| 输入尺寸 | `640` |
| epoch | `50` |
| batch | `4` |
| 随机种子 | `20261112` |
| 设备 | `CUDA:0`（RTX 4060 Laptop GPU） |
| 训练图像 | `764` |
| 验证图像 | `216` |
| 评估划分 | `val` |

配置文件：`configs/train_baseline_full.yaml`。

数据配置：`configs/dataset_v0.2.yaml`。

## 等价复现命令

下面的命令是根据训练生成的 `args.yaml` 还原的等价命令；它用于以后复现同一组条件，不声称是当时终端中逐字输入的原命令。

```bash
cd ~/project/03_aerial-detection-tracking
source .venv-project/bin/activate

PROJECT_ROOT=/path/to/03_aerial-detection-tracking

yolo detect train \
  model="$PROJECT_ROOT/yolo26n.pt" \
  data="$PROJECT_ROOT/configs/dataset_v0.2.yaml" \
  imgsz=640 epochs=50 batch=4 seed=20261112 \
  device=0 deterministic=True workers=2 \
  project="$PROJECT_ROOT/runs/week3_day2" \
  name=baseline_full_v0.2 exist_ok=False cache=False
```

如果要重新运行，建议另改 `name`，避免覆盖或混淆已有结果。

## 产物

训练输出目录：

`runs/week3_day2/baseline_full_v0.2/`

其中包括：

- `weights/best.pt`：训练过程中按验证指标保存的最优 checkpoint。
- `weights/last.pt`：第 50 个 epoch 结束时的 checkpoint。
- `args.yaml`：Ultralytics 实际生效的完整参数。
- `results.csv`：每个 epoch 的训练和验证指标。

日志文件：`outputs/week3_day2_baseline.log`。

耗时文件：`outputs/week3_day2_elapsed.txt`，记录为 `618.58` 秒，约 10 分 18 秒。

## 验证结果

训练日志确认：`50 epochs completed`，使用 `764` 张训练图像和 `216` 张验证图像。

`results.csv` 最后一轮（epoch 50）为：

| 指标 | 值 |
| --- | ---: |
| Precision | 0.82280 |
| Recall | 0.81178 |
| mAP50 | 0.83017 |
| mAP50-95 | 0.52222 |

这些是验证集指标。测试集没有参与本次训练、模型选择或阈值调整，最终测试应在后续冻结方案后单独进行。

## 环境

- Ubuntu 22.04（WSL）
- Python 3.10.12
- Ultralytics 8.4.207
- PyTorch 2.14.1+cu130
- NVIDIA GeForce RTX 4060 Laptop GPU

## 检查结论

训练过程、权重、日志、耗时和验证指标均已生成。配置文件中的阶段名称和输出目录已与本次 Day 2 实际运行结果保持一致。
