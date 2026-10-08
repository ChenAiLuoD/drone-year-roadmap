"""视频输入、视频元信息读取和视频输出。"""

import logging
from pathlib import Path

import cv2


def setup_logging(log_path: Path) -> None:
    """同时把日志输出到终端和日志文件。"""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(log_path, encoding="utf-8"),
        ],
    )


def open_video(input_path: Path):
    """打开输入视频，并返回 VideoCapture 和基本元信息。"""
    capture = cv2.VideoCapture(str(input_path))
    if not capture.isOpened():
        raise RuntimeError(f"视频无法打开，可能是编码器不支持：{input_path}")

    fps = capture.get(cv2.CAP_PROP_FPS)
    width = int(capture.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT))
    frame_count = int(capture.get(cv2.CAP_PROP_FRAME_COUNT))

    if fps <= 0:
        logging.warning("读取到的 FPS 无效，将使用默认 FPS=25")
        fps = 25.0
    if width <= 0 or height <= 0:
        capture.release()
        raise RuntimeError("无法获取视频宽高")

    return capture, {
        "fps": fps,
        "width": width,
        "height": height,
        "frame_count": frame_count,
        "duration_seconds": frame_count / fps,
    }


def create_video_writer(output_path: Path, fps: float, width: int, height: int):
    """创建 MP4 输出对象，并检查编码器是否可用。"""
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    writer = cv2.VideoWriter(str(output_path), fourcc, fps, (width, height))
    if not writer.isOpened():
        raise RuntimeError("输出视频无法创建，请检查编码器或输出路径")
    return writer
