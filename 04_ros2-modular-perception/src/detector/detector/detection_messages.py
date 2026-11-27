from vision_msgs.msg import (
    Detection2D,
    Detection2DArray,
    ObjectHypothesisWithPose,
)


def build_detection_array(
    header,
    image_width,
    image_height,
    candidates,
):
    if image_width <= 0 or image_height <= 0:
        raise ValueError(
            f'图像尺寸无效：width={image_width}, height={image_height}'
        )

    message = Detection2DArray()
    message.header = header

    for candidate in candidates:
        x1, y1, x2, y2 = candidate['xyxy']
        score = float(candidate['score'])
        class_id = str(candidate['class_id'])

        in_bounds = (
            0.0 <= x1 < x2 <= image_width
            and 0.0 <= y1 < y2 <= image_height
        )

        if not in_bounds:
            raise ValueError(
                '检测框越界：'
                f'xyxy=({x1}, {y1}, {x2}, {y2}), '
                f'image={image_width}x{image_height}'
            )

        if not 0.0 <= score <= 1.0:
            raise ValueError(
                f'检测置信度无效：score={score}'
            )

        detection = Detection2D()
        detection.header = header

        detection.bbox.center.position.x = float((x1 + x2) / 2)
        detection.bbox.center.position.y = float((y1 + y2) / 2)
        detection.bbox.center.theta = 0.0
        detection.bbox.size_x = float(x2 - x1)
        detection.bbox.size_y = float(y2 - y1)

        hypothesis = ObjectHypothesisWithPose()
        hypothesis.hypothesis.class_id = class_id
        hypothesis.hypothesis.score = score

        detection.results.append(hypothesis)

        # 当前未接入跟踪器，因此没有稳定目标 ID。
        detection.id = ''

        message.detections.append(detection)

    return message
