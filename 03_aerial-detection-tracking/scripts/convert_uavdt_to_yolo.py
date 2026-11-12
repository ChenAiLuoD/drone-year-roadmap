#!/usr/bin/env python3

import argparse
import csv
import json
import re
import shutil
from collections import Counter
from pathlib import Path

from PIL import Image


CATEGORY_MAP = {1: 0, 2: 0, 3: 0}
IMAGE_RE = re.compile(r"img(\d+)\.jpg$", re.IGNORECASE)


def read_split_manifest(path):
    groups = {"train": [], "val": [], "test": []}
    seen = {}

    with path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        required = {"sequence", "split"}
        if not required.issubset(reader.fieldnames or set()):
            raise ValueError(
                f"{path}: expected columns {sorted(required)}"
            )

        for line_number, row in enumerate(reader, start=2):
            sequence = row["sequence"].strip()
            split = row["split"].strip()

            if not sequence:
                raise ValueError(f"{path}:{line_number}: empty sequence")
            if split not in groups:
                raise ValueError(
                    f"{path}:{line_number}: invalid split {split!r}"
                )
            if sequence in seen:
                raise ValueError(
                    f"{path}:{line_number}: duplicate sequence {sequence}"
                )

            seen[sequence] = split
            groups[split].append(sequence)

    for split, sequences in groups.items():
        if not sequences:
            raise ValueError(f"{path}: split {split!r} is empty")

    return groups


def read_ground_truth(path):
    by_frame = {}
    for line_number, raw_line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not raw_line.strip():
            continue
        parts = raw_line.split(",")
        if len(parts) != 9:
            raise ValueError(f"{path}:{line_number}: expected 9 columns, got {len(parts)}")
        frame = int(parts[0])
        category = int(parts[8])
        if category not in CATEGORY_MAP:
            continue
        x, y, width, height = map(float, parts[2:6])
        by_frame.setdefault(frame, []).append((x, y, width, height, CATEGORY_MAP[category]))
    return by_frame



def frame_number(path):
    match = IMAGE_RE.search(path.name)
    if not match:
        raise ValueError(f"unexpected image name: {path}")
    return int(match.group(1))


def yolo_rows(boxes, image_width, image_height):
    rows = []
    clipped_count = 0
    for x, y, width, height, class_id in boxes:
        x1 = max(0.0, x)
        y1 = max(0.0, y)
        x2 = min(float(image_width), x + width)
        y2 = min(float(image_height), y + height)
        if x1 != x or y1 != y or x2 != x + width or y2 != y + height:
            clipped_count += 1
        if x2 <= x1 or y2 <= y1:
            continue
        cx = ((x1 + x2) / 2.0) / image_width
        cy = ((y1 + y2) / 2.0) / image_height
        w = (x2 - x1) / image_width
        h = (y2 - y1) / image_height
        rows.append(f"{class_id} {cx:.6f} {cy:.6f} {w:.6f} {h:.6f}")
    return rows, clipped_count


def write_yaml(path):
    path.write_text(
        "path: .\n"
        "train: images/train\n"
        "val: images/val\n"
        "test: images/test\n"
        "names:\n"
        "  0: vehicle\n",
        encoding="utf-8",
    )


def convert_sequence(source_root, gt_root, output_root, split, sequence, stride, writer, stats):
    image_paths = sorted((source_root / sequence).glob("*.jpg"), key=frame_number)
    if not image_paths:
        raise FileNotFoundError(f"no images for {sequence}")
    gt = read_ground_truth(gt_root / f"{sequence}_gt_whole.txt")
    selected = image_paths[::stride]
    image_dir = output_root / "images" / split
    label_dir = output_root / "labels" / split
    image_dir.mkdir(parents=True, exist_ok=True)
    label_dir.mkdir(parents=True, exist_ok=True)
    for image_path in selected:
        frame = frame_number(image_path)
        output_stem = f"{sequence}_{image_path.stem}"
        output_image = image_dir / f"{output_stem}.jpg"
        output_label = label_dir / f"{output_stem}.txt"
        with Image.open(image_path) as image:
            width, height = image.size
        rows, clipped_count = yolo_rows(gt.get(frame, []), width, height)
        shutil.copy2(image_path, output_image)
        output_label.write_text("\n".join(rows) + ("\n" if rows else ""), encoding="utf-8")
        writer.writerow(
            {
                "split": split,
                "sequence": sequence,
                "frame": frame,
                "image": output_image.relative_to(output_root).as_posix(),
                "label": output_label.relative_to(output_root).as_posix(),
                "objects": len(rows),
                "source_gt": (gt_root / f"{sequence}_gt_whole.txt").as_posix(),
            }
        )
        stats[split]["images"] += 1
        stats[split]["objects"] += len(rows)
        stats[split]["empty_labels"] += int(not rows)
        stats[split]["clipped_boxes"] += clipped_count
        stats[split]["sequences"].add(sequence)


def main():
    parser = argparse.ArgumentParser(description="Convert UAVDT gt_whole annotations to single-class YOLO")
    parser.add_argument("--images", type=Path, required=True, help="UAVDT-Benchmark-M directory")
    parser.add_argument("--gt", type=Path, required=True, help="UAVDT toolkit GT directory")
    parser.add_argument("--output", type=Path, required=True, help="output YOLO dataset directory")
    parser.add_argument("--split-manifest", type=Path, required=True, help="sequence split manifest CSV")
    parser.add_argument("--stride", type=int, default=25)
    args = parser.parse_args()
    if args.stride <= 0:
        raise SystemExit("--stride must be positive")
    split_sequences = read_split_manifest(args.split_manifest)
    args.output.mkdir(parents=True, exist_ok=True)
    write_yaml(args.output / "dataset.yaml")
    stats = {
        split: {
            "images": 0,
            "objects": 0,
            "empty_labels": 0,
            "clipped_boxes": 0,
            "sequences": set(),
        }
        for split in split_sequences
    }
    manifest_path = args.output / "manifest.csv"
    with manifest_path.open("w", newline="", encoding="utf-8") as manifest_file:
        fields = ["split", "sequence", "frame", "image", "label", "objects", "source_gt"]
        writer = csv.DictWriter(manifest_file, fieldnames=fields)
        writer.writeheader()
        for split, sequences in split_sequences.items():
            for sequence in sequences:
                convert_sequence(args.images, args.gt, args.output, split, sequence, args.stride, writer, stats)
    serializable = {
        "source": "UAVDT-Benchmark-M + UAVDT-DET-MOT-toolkit/GT/*_gt_whole.txt",
        "category_mapping": {"car": 0, "truck": 0, "bus": 0},
        "stride": args.stride,
        "split_manifest": args.split_manifest.as_posix(),
        "splits": {
            split: {**values, "sequences": sorted(values["sequences"])}
            for split, values in stats.items()
        },
    }
    (args.output / "stats.json").write_text(json.dumps(serializable, indent=2) + "\n", encoding="utf-8")
    for split, values in serializable["splits"].items():
        print(
            f"{split}: images={values['images']} objects={values['objects']} "
            f"empty_labels={values['empty_labels']} clipped_boxes={values['clipped_boxes']} "
            f"sequences={len(values['sequences'])}"
        )
    print(f"output: {args.output}")


if __name__ == "__main__":
    main()
