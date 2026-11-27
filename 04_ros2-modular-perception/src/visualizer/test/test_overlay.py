import numpy as np
from vision_msgs.msg import (
    Detection2D,
    Detection2DArray,
    ObjectHypothesisWithPose,
)

from visualizer.overlay import draw_tracks


def make_tracks():
    tracks = Detection2DArray()

    detection = Detection2D()
    detection.bbox.center.position.x = 50.0
    detection.bbox.center.position.y = 50.0
    detection.bbox.size_x = 40.0
    detection.bbox.size_y = 20.0
    detection.id = '1'

    hypothesis = ObjectHypothesisWithPose()
    hypothesis.hypothesis.class_id = 'vehicle'
    hypothesis.hypothesis.score = 0.9
    detection.results.append(hypothesis)

    tracks.detections.append(detection)

    return tracks


def test_draw_tracks_returns_new_image_with_rectangle():
    image = np.zeros((100, 100, 3), dtype=np.uint8)

    output = draw_tracks(image, make_tracks())

    assert output.shape == image.shape
    assert np.array_equal(image, np.zeros((100, 100, 3), dtype=np.uint8))
    assert not np.array_equal(output, image)
    assert output[40, 30].tolist() == [0, 255, 0]
