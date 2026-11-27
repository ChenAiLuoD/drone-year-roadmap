import pytest
from std_msgs.msg import Header

from detector.detection_messages import build_detection_array


def make_header():
    header = Header()
    header.stamp.sec = 12
    header.stamp.nanosec = 345_000_000
    header.frame_id = 'source_video_frame'
    return header


def test_header_is_preserved():
    header = make_header()

    message = build_detection_array(
        header=header,
        image_width=3840,
        image_height=2160,
        candidates=[
            {
                'class_id': 'vehicle',
                'score': 0.236412,
                'xyxy': (
                    823.3346,
                    1061.9789,
                    1024.4427,
                    1138.6003,
                ),
            }
        ],
    )

    assert message.header.stamp.sec == 12
    assert message.header.stamp.nanosec == 345_000_000
    assert message.header.frame_id == 'source_video_frame'
    assert message.detections[0].header.frame_id == 'source_video_frame'


def test_empty_candidates_publish_empty_array():
    header = make_header()

    message = build_detection_array(
        header=header,
        image_width=3840,
        image_height=2160,
        candidates=[],
    )

    assert message.header.frame_id == 'source_video_frame'
    assert message.detections == []


@pytest.mark.parametrize(
    'xyxy',
    [
        (-1.0, 10.0, 100.0, 100.0),
        (10.0, -1.0, 100.0, 100.0),
        (10.0, 10.0, 4000.0, 100.0),
        (10.0, 10.0, 100.0, 2200.0),
        (100.0, 100.0, 100.0, 200.0),
    ],
)
def test_out_of_range_box_is_rejected(xyxy):
    with pytest.raises(ValueError, match='检测框'):
        build_detection_array(
            header=make_header(),
            image_width=3840,
            image_height=2160,
            candidates=[
                {
                    'class_id': 'vehicle',
                    'score': 0.9,
                    'xyxy': xyxy,
                }
            ],
        )
