"""统计函数测试。"""

import unittest

from drone_video_tool.metrics import (
    calculate_average_motion_area,
    calculate_processing_fps,
)


class MetricsTests(unittest.TestCase):
    def test_calculates_average_processing_fps(self):
        self.assertEqual(calculate_processing_fps(120, 4), 30)

    def test_calculates_average_motion_area(self):
        self.assertEqual(calculate_average_motion_area(900, 3), 300)

    def test_returns_zero_when_no_frames_are_processed(self):
        self.assertEqual(calculate_processing_fps(0, 0), 0.0)
        self.assertEqual(calculate_average_motion_area(0, 0), 0.0)


if __name__ == "__main__":
    unittest.main()
