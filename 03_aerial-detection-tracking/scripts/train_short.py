#!/usr/bin/env python3
"""按固定 YAML 配置执行一次短跑训练，用于验证训练链路。"""

from pathlib import Path

import yaml  # 读取训练配置文件。
from ultralytics import YOLO  # 调用 Ultralytics 的训练接口。


# 配置文件相对于项目根目录固定，避免从其他工作目录运行时找错文件。
PROJECT_ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = PROJECT_ROOT / "configs" / "train_baseline.yaml"


def load_config(path: Path) -> dict:
    """读取 YAML，并检查训练必需字段是否存在。"""

    with path.open("r", encoding="utf-8") as config_file:
        config = yaml.safe_load(config_file) or {}

    # 这些字段决定实验是否可复现，缺少任意一个都直接停止。
    required_fields = {
        "model",
        "data",
        "imgsz",
        "epochs",
        "batch",
        "seed",
        "device",
        "data_version",
    }
    missing = sorted(required_fields - config.keys())
    if missing:
        raise ValueError(f"配置缺少字段: {', '.join(missing)}")

    return config


def resolve_path(value: str) -> Path:
    """把模型或数据路径解析成绝对路径，并检查文件存在。"""

    path = Path(value)
    if not path.is_absolute():
        path = PROJECT_ROOT / path
    return path.resolve()


def main() -> int:
    """加载固定配置，打印实验条件，然后启动一次短跑训练。"""

    config = load_config(CONFIG_PATH)
    model_path = resolve_path(config["model"])
    data_path = resolve_path(config["data"])

    # 在调用训练前先检查模型和数据入口，避免训练中途才发现路径错误。
    if not model_path.is_file():
        raise FileNotFoundError(f"找不到模型文件: {model_path}")
    if not data_path.is_file():
        raise FileNotFoundError(f"找不到数据配置: {data_path}")

    print("=== short training configuration ===")
    print(f"model: {config['model_version']} ({model_path})")
    print(f"data: {config['data_version']} ({data_path})")
    print(f"imgsz: {config['imgsz']}")
    print(f"epochs: {config['epochs']}")
    print(f"batch: {config['batch']}")
    print(f"seed: {config['seed']}")
    print(f"device: {config['device']}")

    # 以模型文件初始化训练器；数据、尺寸、轮数等全部来自固定配置。
    model = YOLO(str(model_path))
    train_arguments = {
        "data": str(data_path),
        "imgsz": config["imgsz"],
        "epochs": config["epochs"],
        "batch": config["batch"],
        "seed": config["seed"],
        "device": config["device"],
        "deterministic": config["deterministic"],
        "workers": config["workers"],
        "project": str(PROJECT_ROOT / config["project"]),
        "name": config["name"],
        "exist_ok": config["exist_ok"],
        "cache": config["cache"],
        "verbose": True,
    }

    # 训练结束后 Ultralytics 会在 runs/ 下保存 results.csv、日志和权重。
    results = model.train(**train_arguments)
    print(f"short training finished: {results.save_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
