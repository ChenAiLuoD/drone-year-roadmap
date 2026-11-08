#!/usr/bin/env python3

import argparse
import sys
from pathlib import Path

from PIL import Image, UnidentifiedImageError


IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}


def collect_images(directory):
    if not directory.exists():
        return {}
    result = {}
    for path in directory.rglob("*"):
        if path.is_file() and path.suffix.lower() in IMAGE_EXTENSIONS:
            key = path.relative_to(directory).with_suffix(".txt").as_posix()
            result[key] = path
    return result


def collect_labels(directory):
    if not directory.exists():
        return {}
    return {
        path.relative_to(directory).as_posix(): path
        for path in directory.rglob("*.txt")
    }


def check_label_file(path, class_count):
    errors = []
    for line_number, raw_line in enumerate(
        path.read_text(encoding="utf-8").splitlines(), start=1
    ):
        line = raw_line.strip()
        if not line:
            continue
        parts = line.split()
        if len(parts) != 5:
            errors.append(f"{path}:{line_number}: expected 5 columns, got {len(parts)}")
            continue
        try:
            class_id = int(parts[0])
            x_center, y_center, width, height = map(float, parts[1:])
        except ValueError:
            errors.append(f"{path}:{line_number}: non-numeric label value")
            continue
        if not 0 <= class_id < class_count:
            errors.append(f"{path}:{line_number}: class id {class_id} out of range")
        values = [x_center, y_center, width, height]
        if any(value < 0 or value > 1 for value in values):
            errors.append(f"{path}:{line_number}: coordinate outside [0, 1]")
        if width <= 0 or height <= 0:
            errors.append(f"{path}:{line_number}: width and height must be positive")
    return errors


def check_split(root, split, class_count):
    image_dir = root / "images" / split
    label_dir = root / "labels" / split
    images = collect_images(image_dir)
    labels = collect_labels(label_dir)
    errors = []
    if not image_dir.exists():
        errors.append(f"{split}: missing {image_dir}")
    if not label_dir.exists():
        errors.append(f"{split}: missing {label_dir}")
    for key in sorted(set(images) - set(labels)):
        errors.append(f"{split}: image without label {key}")
    for key in sorted(set(labels) - set(images)):
        errors.append(f"{split}: label without image {key}")
    for label_path in labels.values():
        errors.extend(check_label_file(label_path, class_count))
    for image_path in images.values():
        try:
            with Image.open(image_path) as image:
                image.verify()
        except (UnidentifiedImageError, OSError) as exc:
            errors.append(f"{split}: unreadable image {image_path}: {exc}")
    print(f"{split}: images={len(images)} labels={len(labels)} errors={len(errors)}")
    return errors


def main():
    parser = argparse.ArgumentParser(description="Check a YOLO detection dataset")
    parser.add_argument("--root", required=True, type=Path)
    parser.add_argument("--classes", required=True, type=int)
    parser.add_argument("--splits", nargs="+", default=["train", "val", "test"])
    args = parser.parse_args()
    if args.classes <= 0:
        print("--classes must be greater than zero")
        return 1
    errors = []
    for split in args.splits:
        errors.extend(check_split(args.root, split, args.classes))
    if errors:
        print("\nProblems found:")
        for error in errors:
            print(f"- {error}")
        return 1
    print("\nDataset check passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
