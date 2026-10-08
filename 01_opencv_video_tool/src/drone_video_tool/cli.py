"""命令行入口和视频处理主流程。"""

import argparse
import json
import logging
import sys
import time
from pathlib import Path

import cv2

from .metrics import build_report
from .processing import detect_motion, draw_information, resize_frame
from .video_io import create_video_writer, open_video, setup_logging


def parse_args():
    """读取命令行参数。"""
    parser = argparse.ArgumentParser(description="航拍视频分析工具第一版")
    parser.add_argument("--input", required=True, help="输入视频路径，例如 data/sample.mp4")
    parser.add_argument("--output-dir", default="outputs", help="输出目录，默认是 outputs")
    parser.add_argument("--sample-every", type=int, default=1, help="每隔多少帧处理一次")
    parser.add_argument("--scale", type=float, default=1.0, help="缩放比例，例如 0.5")
    parser.add_argument("--motion-threshold", type=int, default=25, help="运动检测灰度差阈值")
    parser.add_argument("--min-area", type=float, default=500.0, help="运动区域最小面积")
    parser.add_argument("--display", action="store_true", help="显示处理窗口；无图形界面时不要使用")
    return parser.parse_args()


def validate_args(args):
    """检查输入路径和关键参数。"""
    input_path = Path(args.input)
    if not input_path.exists():
        raise FileNotFoundError(f"输入视频不存在：{input_path}")
    if args.sample_every <= 0:
        raise ValueError("--sample-every 必须大于 0")
    if args.scale <= 0:
        raise ValueError("--scale 必须大于 0")
    return input_path


def main():
    args = parse_args()
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    log_path = output_dir / "processing.log"
    report_path = output_dir / "report.json"
    output_video_path = output_dir / "result.mp4"
    setup_logging(log_path)
    logging.info("程序开始")

    try:
        input_path = validate_args(args)
    except Exception:
        logging.exception("输入参数或输入文件检查失败")
        raise

    logging.info("输入视频：%s", input_path)
    logging.info("输出目录：%s", output_dir)

    capture, input_info = open_video(input_path)
    input_fps = input_info["fps"]
    input_width = input_info["width"]
    input_height = input_info["height"]
    logging.info(
        "输入信息：FPS=%.2f，尺寸=%dx%d，总帧数=%d，时长=%.2f 秒",
        input_fps,
        input_width,
        input_height,
        input_info["frame_count"],
        input_info["duration_seconds"],
    )

    output_width = int(input_width * args.scale)
    output_height = int(input_height * args.scale)
    if output_width <= 0 or output_height <= 0:
        capture.release()
        raise RuntimeError("输出视频尺寸无效")

    output_fps = input_fps / args.sample_every
    try:
        writer = create_video_writer(
            output_video_path, output_fps, output_width, output_height
        )
    except Exception:
        capture.release()
        raise

    previous_gray = None
    frame_index = 0
    processed_frame_count = 0
    total_motion_area = 0.0
    total_processing_time = 0.0

    try:
        while True:
            read_success, frame = capture.read()
            if not read_success:
                break

            frame_index += 1
            resized_frame = resize_frame(frame, args.scale)
            current_gray = cv2.cvtColor(resized_frame, cv2.COLOR_BGR2GRAY)

            if frame_index % args.sample_every != 0:
                previous_gray = current_gray
                continue

            start_time = time.perf_counter()
            boxes, motion_area = detect_motion(
                previous_gray,
                current_gray,
                args.motion_threshold,
                args.min_area,
            )

            for x, y, width, height in boxes:
                cv2.rectangle(
                    resized_frame,
                    (x, y),
                    (x + width, y + height),
                    (0, 0, 255),
                    2,
                )

            current_processing_time = time.perf_counter() - start_time
            total_processing_time += current_processing_time
            processed_frame_count += 1
            processing_fps = (
                1 / current_processing_time
                if current_processing_time > 0
                else 0
            )
            video_time = frame_index / input_fps

            draw_information(
                resized_frame,
                frame_index,
                video_time,
                processing_fps,
                len(boxes),
                motion_area,
            )

            if resized_frame.shape[1] != output_width:
                raise RuntimeError("输出帧宽度不一致")
            if resized_frame.shape[0] != output_height:
                raise RuntimeError("输出帧高度不一致")

            writer.write(resized_frame)
            total_motion_area += motion_area

            if args.display:
                cv2.imshow("Drone Video Tool", resized_frame)
                key = cv2.waitKey(1) & 0xFF
                if key == ord("q"):
                    logging.info("用户按下 q，提前结束处理")
                    break

            previous_gray = current_gray
    finally:
        capture.release()
        writer.release()
        if args.display:
            cv2.destroyAllWindows()

    report = build_report(
        input_path=input_path,
        input_info=input_info,
        output_path=output_video_path,
        output_fps=output_fps,
        output_width=output_width,
        output_height=output_height,
        processed_frame_count=processed_frame_count,
        parameters={
            "sample_every": args.sample_every,
            "scale": args.scale,
            "motion_threshold": args.motion_threshold,
            "min_area": args.min_area,
        },
        total_processing_time=total_processing_time,
        total_motion_area=total_motion_area,
    )

    with report_path.open("w", encoding="utf-8") as file:
        json.dump(report, file, ensure_ascii=False, indent=4)

    logging.info("处理完成")
    logging.info("结果视频：%s", output_video_path)
    logging.info("统计报告：%s", report_path)
    logging.info("日志文件：%s", log_path)


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        logging.exception("程序运行失败")
        print(f"程序运行失败：{error}")
        sys.exit(1)
