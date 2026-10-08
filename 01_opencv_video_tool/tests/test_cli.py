"""命令行参数检查测试。"""

import argparse
import tempfile
import unittest
from pathlib import Path

from drone_video_tool.cli import validate_args


class ValidateArgsTests(unittest.TestCase):
    def make_args(self, input_path, sample_every=1, scale=1.0):
        return argparse.Namespace(
            input=str(input_path),
            sample_every=sample_every,
            scale=scale,
        )

    def test_rejects_missing_input_file(self):
        args = self.make_args("missing-video.mp4")
        with self.assertRaises(FileNotFoundError):
            validate_args(args)

    def test_rejects_non_positive_sample_interval(self):
        with tempfile.TemporaryDirectory() as directory:
            input_path = Path(directory) / "sample.mp4"
            input_path.touch()
            args = self.make_args(input_path, sample_every=0)
            with self.assertRaises(ValueError):
                validate_args(args)

    def test_accepts_existing_input_and_positive_parameters(self):
        with tempfile.TemporaryDirectory() as directory:
            input_path = Path(directory) / "sample.mp4"
            input_path.touch()
            args = self.make_args(input_path, sample_every=2, scale=0.5)
            self.assertEqual(validate_args(args), input_path)


if __name__ == "__main__":
    unittest.main()
