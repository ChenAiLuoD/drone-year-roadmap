#!/usr/bin/env python3

import argparse
import csv
import json
import time
from pathlib import Path

import cv2
from ultralytics import YOLO


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--video", required=True)
    parser.add_argument("--model", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--tracker", default="bytetrack.yaml")
    parser.add_argument("--imgsz", type=int, default=640)
    parser.add_argument("--conf", type=float, default=0.20)
    parser.add_argument("--iou", type=float, default=0.60)
    args = parser.parse_args()

    video_path = Path(args.video)
    model_path = Path(args.model)
    output_path = Path(args.output)

    if not video_path.is_file():
        raise FileNotFoundError(f"视频不存在: {video_path}")
    if not model_path.is_file():
        raise FileNotFoundError(f"模型不存在: {model_path}")

    output_path.parent.mkdir(parents=True, exist_ok=True)

    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        raise RuntimeError(f"无法打开视频: {video_path}")

    input_fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    writer = cv2.VideoWriter(
        str(output_path),
        cv2.VideoWriter_fourcc(*"XVID"),
        input_fps,
        (width, height),
    )

    model = YOLO(str(model_path))

    stage_seconds = {
        "decode": 0.0,
        "inference_tracking": 0.0,
        "draw": 0.0,
        "write": 0.0,
    }

    frame_rows = []
    input_frames = 0
    output_frames = 0

    total_start = time.perf_counter()

    while True:
        start = time.perf_counter()
        ok, frame = cap.read()
        stage_seconds["decode"] += time.perf_counter() - start

        if not ok:
            break

        input_frames += 1

        start = time.perf_counter()
        results = model.track(
            frame,
            persist=True,
            tracker=args.tracker,
            imgsz=args.imgsz,
            conf=args.conf,
            iou=args.iou,
            verbose=False,
        )
        stage_seconds["inference_tracking"] += time.perf_counter() - start

        start = time.perf_counter()
        annotated = results[0].plot()
        stage_seconds["draw"] += time.perf_counter() - start

        start = time.perf_counter()
        writer.write(annotated)
        stage_seconds["write"] += time.perf_counter() - start

        output_frames += 1

        frame_rows.append(
            {
                "frame": input_frames,
                "decode_ms": stage_seconds["decode"] * 1000 / input_frames,
                "inference_tracking_ms": (
                    stage_seconds["inference_tracking"] * 1000 / output_frames
                ),
                "draw_ms": stage_seconds["draw"] * 1000 / output_frames,
                "write_ms": stage_seconds["write"] * 1000 / output_frames,
            }
        )

    cap.release()
    writer.release()

    total_seconds = time.perf_counter() - total_start
    end_to_end_fps = output_frames / total_seconds if total_seconds else 0.0
    compute_fps = (
        output_frames
        / (stage_seconds["inference_tracking"] + stage_seconds["draw"])
        if output_frames
        else 0.0
    )

    summary = {
        "input_video": str(video_path),
        "output_video": str(output_path),
        "input_frames": input_frames,
        "output_frames": output_frames,
        "input_fps": input_fps,
        "stage_total_ms": {
            key: round(value * 1000, 2)
            for key, value in stage_seconds.items()
        },
        "average_fps_end_to_end": round(end_to_end_fps, 3),
        "average_fps_compute_only": round(compute_fps, 3),
        "fps_policy": {
            "end_to_end": [
                "decode",
                "inference_tracking",
                "draw",
                "write",
            ],
            "compute_only": [
                "inference_tracking",
                "draw",
            ],
            "inference_tracking_note": (
                "Ultralytics track() combines model inference and ByteTrack association."
            ),
        },
    }

    summary_path = output_path.with_name(output_path.stem + ".timing.json")
    frames_path = output_path.with_name(output_path.stem + ".timing.csv")

    summary_path.write_text(
        json.dumps(summary, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    with frames_path.open("w", newline="", encoding="utf-8") as f:
        writer_csv = csv.DictWriter(f, fieldnames=frame_rows[0].keys())
        writer_csv.writeheader()
        writer_csv.writerows(frame_rows)

    print(json.dumps(summary, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()