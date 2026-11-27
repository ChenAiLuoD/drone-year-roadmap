import copy

import rclpy
from rclpy.node import Node
from rclpy.qos import (
    DurabilityPolicy,
    HistoryPolicy,
    QoSProfile,
    ReliabilityPolicy,
)
from vision_msgs.msg import Detection2DArray

from tracker.track_manager import TrackManager

PERCEPTION_QOS = QoSProfile(
    history=HistoryPolicy.KEEP_LAST,
    depth=10,
    reliability=ReliabilityPolicy.RELIABLE,
    durability=DurabilityPolicy.VOLATILE,
)


class TrackerNode(Node):
    def __init__(self):
        super().__init__('tracker_node')

        self.declare_parameter(
            'input_topic',
            '/perception/detections',
        )
        self.declare_parameter(
            'output_topic',
            '/perception/tracks',
        )
        self.declare_parameter('iou_threshold', 0.3)
        self.declare_parameter('max_missed_frames', 5)

        self.input_topic = self.get_parameter('input_topic').value
        self.output_topic = self.get_parameter('output_topic').value
        self.iou_threshold = self.get_parameter(
            'iou_threshold'
        ).value
        self.max_missed_frames = self.get_parameter(
            'max_missed_frames'
        ).value

        if not 0.0 < self.iou_threshold <= 1.0:
            self.get_logger().error(
                '参数无效：iou_threshold 必须大于 0 且不超过 1'
            )
            raise ValueError('iou_threshold 无效')

        if self.max_missed_frames < 0:
            self.get_logger().error(
                '参数无效：max_missed_frames 不能小于 0'
            )
            raise ValueError('max_missed_frames 无效')

        self.track_manager = TrackManager(
            iou_threshold=self.iou_threshold,
            max_missed_frames=self.max_missed_frames,
        )

        self.subscription = self.create_subscription(
            Detection2DArray,
            self.input_topic,
            self.detections_callback,
            PERCEPTION_QOS,
        )

        self.publisher = self.create_publisher(
            Detection2DArray,
            self.output_topic,
            PERCEPTION_QOS,
        )

        self.get_logger().info(
            '跟踪节点已启动：'
            f'input_topic={self.input_topic}, '
            f'output_topic={self.output_topic}, '
            f'iou_threshold={self.iou_threshold}, '
            f'max_missed_frames={self.max_missed_frames}'
        )

    def detections_callback(self, msg):
        valid_detections = []

        for detection in msg.detections:
            width = detection.bbox.size_x
            height = detection.bbox.size_y

            if width <= 0.0 or height <= 0.0:
                self.get_logger().error(
                    '跳过无效检测框：'
                    f'width={width}, height={height}'
                )
                continue

            valid_detections.append(detection)

        tracker_inputs = [
            {
                'center_x': detection.bbox.center.position.x,
                'center_y': detection.bbox.center.position.y,
                'width': detection.bbox.size_x,
                'height': detection.bbox.size_y,
            }
            for detection in valid_detections
        ]

        try:
            tracks = self.track_manager.update(tracker_inputs)
        except ValueError as error:
            self.get_logger().error(
                f'跟踪更新失败，跳过当前帧：{error}'
            )
            return

        output = Detection2DArray()
        output.header = msg.header

        for detection, track in zip(valid_detections, tracks):
            tracked_detection = copy.deepcopy(detection)
            tracked_detection.id = str(track['track_id'])
            output.detections.append(tracked_detection)

        self.publisher.publish(output)

        source_time = (
            msg.header.stamp.sec
            + msg.header.stamp.nanosec / 1_000_000_000
        )

        self.get_logger().info(
            f'发布 {self.output_topic}：'
            f'source_time={source_time:.3f}s, '
            f'count={len(output.detections)}, '
            f'active_tracks={len(self.track_manager.active_tracks)}'
        )


def main(args=None):
    rclpy.init(args=args)
    node = None

    try:
        node = TrackerNode()
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        if node is not None:
            node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
