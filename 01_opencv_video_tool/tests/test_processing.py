"""图像处理函数测试。"""

import unittest

import cv2
import numpy as np

from drone_video_tool.processing import detect_motion, resize_frame


class ProcessingTests(unittest.TestCase):
    def test_resize_frame_halves_width_and_height(self):
        frame = np.zeros((100, 200, 3), dtype=np.uint8)
        resized = resize_frame(frame, 0.5)
        self.assertEqual(resized.shape, (50, 100, 3))

    def test_resize_frame_rejects_non_positive_result(self):
        frame = np.zeros((10, 10, 3), dtype=np.uint8)
        with self.assertRaises(ValueError):
            resize_frame(frame, 0)

    def test_detect_motion_finds_changed_region(self):
        previous = np.zeros((100, 100), dtype=np.uint8)
        current = previous.copy()
        current[30:60, 30:60] = 255

        boxes, total_area = detect_motion(
            previous,
            current,
            threshold_value=25,
            min_area=20,
        )

        self.assertGreaterEqual(len(boxes), 1)
        self.assertGreater(total_area, 0)


if __name__ == "__main__":
    unittest.main()
