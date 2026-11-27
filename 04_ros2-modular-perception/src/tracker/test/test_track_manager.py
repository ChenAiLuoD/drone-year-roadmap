from tracker.track_manager import TrackManager


def make_detection(center_x=100.0, center_y=100.0,
                   width=40.0, height=20.0):
    return {
        'center_x': center_x,
        'center_y': center_y,
        'width': width,
        'height': height,
    }


def test_first_detection_gets_first_track_id():
    manager = TrackManager(iou_threshold=0.3, max_missed_frames=1)

    tracks = manager.update([make_detection()])

    assert [track['track_id'] for track in tracks] == [1]


def test_overlapping_detection_keeps_same_track_id():
    manager = TrackManager(iou_threshold=0.3, max_missed_frames=1)

    manager.update([make_detection(center_x=100.0)])
    tracks = manager.update([make_detection(center_x=102.0)])

    assert [track['track_id'] for track in tracks] == [1]


def test_expired_track_gets_new_id_when_target_returns():
    manager = TrackManager(iou_threshold=0.3, max_missed_frames=1)

    manager.update([make_detection()])
    manager.update([])
    manager.update([])

    tracks = manager.update([make_detection()])

    assert [track['track_id'] for track in tracks] == [2]
