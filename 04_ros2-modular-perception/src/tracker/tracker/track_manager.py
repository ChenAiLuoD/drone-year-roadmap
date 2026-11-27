class TrackManager:
    def __init__(self, iou_threshold, max_missed_frames):
        if not 0.0 < iou_threshold <= 1.0:
            raise ValueError('iou_threshold 必须大于 0 且不超过 1')

        if max_missed_frames < 0:
            raise ValueError('max_missed_frames 不能小于 0')

        self.iou_threshold = iou_threshold
        self.max_missed_frames = max_missed_frames
        self.active_tracks = {}
        self.next_track_id = 1

    def update(self, detections):
        assignments = {}
        available_track_ids = set(self.active_tracks)
        available_detection_indices = set(range(len(detections)))
        candidates = []

        for track_id, track in self.active_tracks.items():
            for detection_index, detection in enumerate(detections):
                iou = self._iou(track['bbox'], self._bbox(detection))

                if iou >= self.iou_threshold:
                    candidates.append((iou, track_id, detection_index))

        for _, track_id, detection_index in sorted(
            candidates,
            reverse=True,
        ):
            if (
                track_id not in available_track_ids
                or detection_index not in available_detection_indices
            ):
                continue

            assignments[detection_index] = track_id
            available_track_ids.remove(track_id)
            available_detection_indices.remove(detection_index)

        for detection_index in available_detection_indices:
            track_id = self.next_track_id
            self.next_track_id += 1

            assignments[detection_index] = track_id
            self.active_tracks[track_id] = {
                'bbox': self._bbox(detections[detection_index]),
                'missed_frames': 0,
            }

        matched_track_ids = set(assignments.values())

        for track_id in list(self.active_tracks):
            if track_id in matched_track_ids:
                detection_index = next(
                    index
                    for index, assigned_id in assignments.items()
                    if assigned_id == track_id
                )
                self.active_tracks[track_id]['bbox'] = self._bbox(
                    detections[detection_index]
                )
                self.active_tracks[track_id]['missed_frames'] = 0
                continue

            self.active_tracks[track_id]['missed_frames'] += 1

            if (
                self.active_tracks[track_id]['missed_frames']
                > self.max_missed_frames
            ):
                del self.active_tracks[track_id]

        tracks = []

        for detection_index, detection in enumerate(detections):
            track = dict(detection)
            track['track_id'] = assignments[detection_index]
            tracks.append(track)

        return tracks

    @staticmethod
    def _bbox(detection):
        width = float(detection['width'])
        height = float(detection['height'])

        if width <= 0.0 or height <= 0.0:
            raise ValueError('检测框宽高必须大于 0')

        center_x = float(detection['center_x'])
        center_y = float(detection['center_y'])

        return (
            center_x - width / 2,
            center_y - height / 2,
            center_x + width / 2,
            center_y + height / 2,
        )

    @staticmethod
    def _iou(box_a, box_b):
        left = max(box_a[0], box_b[0])
        top = max(box_a[1], box_b[1])
        right = min(box_a[2], box_b[2])
        bottom = min(box_a[3], box_b[3])

        intersection_width = max(0.0, right - left)
        intersection_height = max(0.0, bottom - top)
        intersection = intersection_width * intersection_height

        area_a = (box_a[2] - box_a[0]) * (box_a[3] - box_a[1])
        area_b = (box_b[2] - box_b[0]) * (box_b[3] - box_b[1])
        union = area_a + area_b - intersection

        if union <= 0.0:
            return 0.0

        return intersection / union
