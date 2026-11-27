import cv2

import rclpy
from rclpy.node import Node
from rclpy.qos import (
    DurabilityPolicy,
    HistoryPolicy,
    QoSProfile,
    ReliabilityPolicy,
)
from cv_bridge import CvBridge
from sensor_msgs.msg import Image


DEFAULT_INPUT_PATH = ''

PERCEPTION_QOS = QoSProfile(
    history=HistoryPolicy.KEEP_LAST,
    depth=10,
    reliability=ReliabilityPolicy.RELIABLE,
    durability=DurabilityPolicy.VOLATILE,
)


class VideoSourceNode(Node):
    def __init__(self):
        super().__init__('video_source_node')

        self.cap = None
        self.timer = None

        self.declare_parameter('input_path', DEFAULT_INPUT_PATH)
        self.declare_parameter('publish_rate', 2.0)
        self.declare_parameter('loop', False)
        self.declare_parameter('max_frames', 10)

        self.input_path = self.get_parameter('input_path').value
        self.publish_rate = self.get_parameter('publish_rate').value
        self.loop = self.get_parameter('loop').value
        self.max_frames = self.get_parameter('max_frames').value

        if not self.input_path:
            self.get_logger().error('参数无效：input_path 不能为空')
            raise ValueError('input_path 不能为空')

        if self.publish_rate <= 0:
            self.get_logger().error(
                f'参数无效：publish_rate={self.publish_rate}，必须大于 0'
            )
            raise ValueError('publish_rate 必须大于 0')

        if self.max_frames < 0:
            self.get_logger().error(
                f'参数无效：max_frames={self.max_frames}，不能小于 0'
            )
            raise ValueError('max_frames 不能小于 0')

        self.bridge = CvBridge()
        self.publisher_ = self.create_publisher(
            Image,
            '/camera/image_raw',
            PERCEPTION_QOS,
        )

        self.cap = cv2.VideoCapture(self.input_path)

        if not self.cap.isOpened():
            self.get_logger().error(
                f'无法打开视频：input_path={self.input_path}'
            )
            raise RuntimeError('视频打开失败')

        self.source_fps = self.cap.get(cv2.CAP_PROP_FPS)

        if self.source_fps <= 0:
            self.get_logger().error(
                f'视频帧率异常：fps={self.source_fps}'
            )
            raise RuntimeError('视频帧率无效')

        self.frame_count = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
        self.width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

        self.source_frame_index = 0
        self.published_count = 0

        self.get_logger().info(
            f'实际参数：input_path={self.input_path}, '
            f'publish_rate={self.publish_rate}, '
            f'loop={self.loop}, max_frames={self.max_frames}'
        )
        self.get_logger().info(
            f'视频信息：frames={self.frame_count}, '
            f'fps={self.source_fps:.3f}, '
            f'size={self.width}x{self.height}, encoding=bgr8'
        )

        self.timer = self.create_timer(
            1.0 / self.publish_rate,
            self.publish_next_frame
        )

    def stop_publishing(self, reason, level='info'):
        if self.timer is not None:
            self.timer.cancel()

        if self.cap is not None and self.cap.isOpened():
            self.cap.release()

        message = f'{reason}；累计发布 {self.published_count} 帧'

        if level == 'error':
            self.get_logger().error(message)
        else:
            self.get_logger().info(message)

    def publish_next_frame(self):
        if (
            self.max_frames > 0
            and self.published_count >= self.max_frames
        ):
            self.stop_publishing(
                f'达到 max_frames={self.max_frames}'
            )
            return

        success, frame = self.cap.read()

        if not success:
            if self.loop:
                reset_ok = self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)

                if reset_ok:
                    self.source_frame_index = 0
                    self.get_logger().info(
                        '视频到达末尾，loop=True，重新从第 0 帧发布'
                    )
                else:
                    self.stop_publishing(
                        '视频到达末尾，但无法重新定位到第 0 帧',
                        level='error'
                    )
                return

            self.stop_publishing('视频结束')
            return

        if frame is None or frame.size == 0:
            self.stop_publishing(
                f'读取到空帧：source_frame={self.source_frame_index}',
                level='error'
            )
            return

        source_time = self.source_frame_index / self.source_fps

        try:
            msg = self.bridge.cv2_to_imgmsg(frame, encoding='bgr8')
        except Exception as error:
            self.stop_publishing(
                f'图像转换失败：{error}',
                level='error'
            )
            return

        msg.header.stamp.sec = int(source_time)
        msg.header.stamp.nanosec = int(
            (source_time - int(source_time)) * 1_000_000_000
        )
        msg.header.frame_id = 'source_video_frame'

        self.publisher_.publish(msg)

        self.get_logger().info(
            f'发布 source_frame={self.source_frame_index}, '
            f'source_time={source_time:.3f}s, '
            f'published_count={self.published_count + 1}'
        )

        self.source_frame_index += 1
        self.published_count += 1

    def destroy_node(self):
        if self.cap is not None and self.cap.isOpened():
            self.cap.release()
        super().destroy_node()


def main(args=None):
    rclpy.init(args=args)
    node = None

    try:
        node = VideoSourceNode()
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
