import cv2


def draw_tracks(image, tracks):
    if image is None or image.ndim != 3 or image.shape[2] != 3:
        raise ValueError('图像必须是三通道 BGR 数组')

    output = image.copy()

    for detection in tracks.detections:
        center_x = detection.bbox.center.position.x
        center_y = detection.bbox.center.position.y
        width = detection.bbox.size_x
        height = detection.bbox.size_y

        if width <= 0.0 or height <= 0.0:
            continue

        x1 = round(center_x - width / 2)
        y1 = round(center_y - height / 2)
        x2 = round(center_x + width / 2)
        y2 = round(center_y + height / 2)

        x1 = max(0, min(image.shape[1] - 1, x1))
        y1 = max(0, min(image.shape[0] - 1, y1))
        x2 = max(0, min(image.shape[1] - 1, x2))
        y2 = max(0, min(image.shape[0] - 1, y2))

        cv2.rectangle(
            output,
            (x1, y1),
            (x2, y2),
            (0, 255, 0),
            2,
        )

        class_id = 'unknown'
        score = 0.0

        if detection.results:
            hypothesis = detection.results[0].hypothesis
            class_id = hypothesis.class_id
            score = hypothesis.score

        track_id = detection.id or '-'
        label = f'ID:{track_id} {class_id} {score:.2f}'

        cv2.putText(
            output,
            label,
            (x1, max(15, y1 - 5)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (0, 255, 0),
            1,
            cv2.LINE_AA,
        )

    return output
