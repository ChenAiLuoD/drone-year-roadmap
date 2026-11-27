import time

import rclpy
from cv_bridge import CvBridge
from rclpy.node import Node
from rclpy.qos import (
    DurabilityPolicy,
    HistoryPolicy,
    QoSProfile,
    ReliabilityPolicy,
)
from sensor_msgs.msg import Image
from vision_msgs.msg import Detection2DArray

from visualizer.overlay import draw_tracks
from visualizer.pair_cache import TimestampPairCache

from pathlib import Path

PERCEPTION_QOS = QoSProfile(
    history=HistoryPolicy.KEEP_LAST,
    depth=10,
    reliability=ReliabilityPolicy.RELIABLE,
    durability=DurabilityPolicy.VOLATILE,
)


class VisualizerNode(Node):
    def __init__(self):
        super().__init__('visualizer_node')

        self.declare_parameter(
            'image_topic',
            '/camera/image_raw',
        )
        self.declare_parameter(
            'tracks_topic',
            '/perception/tracks',
        )
        self.declare_parameter(
            'output_topic',
            '/perception/annotated_image',
        )
        self.declare_parameter('max_cache_size', 30)
        self.declare_parameter('cache_timeout_seconds', 2.0)
        self.declare_parameter('output_dir', 'outputs/pipeline')

        self.output_dir = self.get_parameter('output_dir').value

        if not self.output_dir:
            self.get_logger().error('参数无效：output_dir 不能为空')
            raise ValueError('output_dir 不能为空')

        Path(self.output_dir).mkdir(parents=True, exist_ok=True)

        self.image_topic = self.get_parameter('image_topic').value
        self.tracks_topic = self.get_parameter(
            'tracks_topic'
        ).value
        self.output_topic = self.get_parameter(
            'output_topic'
        ).value
        self.max_cache_size = self.get_parameter(
            'max_cache_size'
        ).value
        self.cache_timeout_seconds = self.get_parameter(
            'cache_timeout_seconds'
        ).value

        if self.max_cache_size <= 0:
            self.get_logger().error(
                '参数无效：max_cache_size 必须大于 0'
            )
            raise ValueError('max_cache_size 无效')

        if self.cache_timeout_seconds <= 0.0:
            self.get_logger().error(
                '参数无效：cache_timeout_seconds 必须大于 0'
            )
            raise ValueError('cache_timeout_seconds 无效')

        self.bridge = CvBridge()
        self.cache = TimestampPairCache(
            max_cache_size=self.max_cache_size,
            timeout_seconds=self.cache_timeout_seconds,
        )

        self.image_subscription = self.create_subscription(
            Image,
            self.image_topic,
            self.image_callback,
            PERCEPTION_QOS,
        )

        self.tracks_subscription = self.create_subscription(
            Detection2DArray,
            self.tracks_topic,
            self.tracks_callback,
            PERCEPTION_QOS,
        )

        self.publisher = self.create_publisher(
            Image,
            self.output_topic,
            PERCEPTION_QOS,
        )

        self.cache_timer = self.create_timer(
            0.2,
            self.expire_cache,
        )

        self.get_logger().info(
            '可视化节点已启动：'
            f'image_topic={self.image_topic}, '
            f'tracks_topic={self.tracks_topic}, '
            f'output_topic={self.output_topic}, '
            f'max_cache_size={self.max_cache_size}, '
            f'cache_timeout_seconds={self.cache_timeout_seconds}, '
            f'output_dir={self.output_dir}'
        )

    def image_callback(self, msg):
        stamp = self.stamp_key(msg)
        pair, dropped = self.cache.add_image(
            stamp=stamp,
            image=msg,
            now=time.monotonic(),
        )

        self.log_dropped(dropped)
        self.publish_pair(pair)

    def tracks_callback(self, msg):
        stamp = self.stamp_key(msg)
        pair, dropped = self.cache.add_tracks(
            stamp=stamp,
            tracks=msg,
            now=time.monotonic(),
        )

        self.log_dropped(dropped)
        self.publish_pair(pair)

    def expire_cache(self):
        expired = self.cache.expire(time.monotonic())

        for kind, stamp in expired:
            label = '图像' if kind == 'image' else '轨迹结果'

            self.get_logger().warning(
                f'{label}缓存超时，丢弃：stamp={stamp}'
            )

    def log_dropped(self, dropped):
        for kind, stamp in dropped:
            label = '图像' if kind == 'image' else '轨迹结果'

            self.get_logger().warning(
                f'缓存超过上限，丢弃最早的{label}：'
                f'stamp={stamp}'
            )

    def publish_pair(self, pair):
        if pair is None:
            return

        image_msg = pair['image']
        tracks_msg = pair['tracks']

        if self.stamp_key(image_msg) != self.stamp_key(tracks_msg):
            self.get_logger().error(
                '内部配对错误：图像与轨迹时间戳不一致'
            )
            return

        if image_msg.encoding.lower() != 'bgr8':
            self.get_logger().error(
                f'不支持的图像编码：encoding={image_msg.encoding}'
            )
            return

        try:
            image = self.bridge.imgmsg_to_cv2(
                image_msg,
                desired_encoding='bgr8',
            )
            annotated = draw_tracks(image, tracks_msg)
            output = self.bridge.cv2_to_imgmsg(
                annotated,
                encoding='bgr8',
            )
        except Exception as error:
            self.get_logger().error(
                f'绘制或图像转换失败：error={error}'
            )
            return

        output.header = image_msg.header
        self.publisher.publish(output)

        self.get_logger().info(
            f'发布 {self.output_topic}：'
            f'stamp={pair["stamp"]}, '
            f'count={len(tracks_msg.detections)}'
        )

    @staticmethod
    def stamp_key(msg):
        return (
            msg.header.stamp.sec,
            msg.header.stamp.nanosec,
        )


def main(args=None):
    rclpy.init(args=args)
    node = None

    try:
        node = VisualizerNode()
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
