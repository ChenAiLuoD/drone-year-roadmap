"""单帧图像处理和运动区域检测。"""

import cv2


def resize_frame(frame, scale):
    """按比例缩放图像。"""
    if scale == 1.0:
        return frame

    height, width = frame.shape[:2]
    new_width = int(width * scale)
    new_height = int(height * scale)
    if new_width <= 0 or new_height <= 0:
        raise ValueError("缩放后的宽高不能小于等于 0")

    return cv2.resize(frame, (new_width, new_height), interpolation=cv2.INTER_AREA)


def detect_motion(previous_gray, current_gray, threshold_value, min_area):
    """比较相邻灰度帧，返回运动框和运动区域总面积。"""
    if previous_gray is None:
        return [], 0.0

    difference = cv2.absdiff(previous_gray, current_gray)
    _, binary = cv2.threshold(
        difference, threshold_value, 255, cv2.THRESH_BINARY
    )
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
    binary = cv2.dilate(binary, kernel, iterations=2)
    contours, _ = cv2.findContours(
        binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
    )

    boxes = []
    total_area = 0.0
    for contour in contours:
        area = cv2.contourArea(contour)
        if area < min_area:
            continue
        x, y, width, height = cv2.boundingRect(contour)
        boxes.append((x, y, width, height))
        total_area += area
    return boxes, total_area


def draw_information(
    frame, frame_index, video_time, processing_fps, motion_count, motion_area
):
    """在图像上叠加帧号、时间、处理速度和运动区域信息。"""
    lines = [
        f"Frame: {frame_index}",
        f"Video time: {video_time:.2f}s",
        f"Processing FPS: {processing_fps:.2f}",
        f"Motion regions: {motion_count}",
        f"Motion area: {motion_area:.1f}",
    ]
    y = 30
    for line in lines:
        cv2.putText(
            frame, line, (20, y), cv2.FONT_HERSHEY_SIMPLEX,
            0.7, (0, 255, 0), 2, cv2.LINE_AA
        )
        y += 30
