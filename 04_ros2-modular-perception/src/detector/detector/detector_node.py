from pathlib import Path

import numpy as np
import rclpy
from rclpy.node import Node
from rclpy.qos import (
    DurabilityPolicy,
    HistoryPolicy,
    QoSProfile,
    ReliabilityPolicy,
)
from sensor_msgs.msg import Image
from ultralytics import YOLO
from vision_msgs.msg import Detection2DArray
from detector.detection_messages import build_detection_array


DEFAULT_MODEL_PATH = ''

PERCEPTION_QOS = QoSProfile(
    history=HistoryPolicy.KEEP_LAST,
    depth=10,
    reliability=ReliabilityPolicy.RELIABLE,
    durability=DurabilityPolicy.VOLATILE,
)


class DetectorNode(Node):
    def __init__(self):
        super().__init__('detector_node')

        self.declare_parameter('model_path', DEFAULT_MODEL_PATH)
        self.declare_parameter('device', '0')
        self.declare_parameter('conf_threshold', 0.20)
        self.declare_parameter('input_size', 640)

        self.model_path = self.get_parameter('model_path').value
        self.device = self.get_parameter('device').value
        self.conf_threshold = self.get_parameter('conf_threshold').value
        self.input_size = self.get_parameter('input_size').value

        if not self.model_path:
            self.get_logger().error('参数无效：model_path 不能为空')
            raise ValueError('model_path 不能为空')

        if not Path(self.model_path).is_file():
            self.get_logger().error(
                f'模型文件不存在：model_path={self.model_path}'
            )
            raise FileNotFoundError('模型文件不存在')

        if not 0.0 <= self.conf_threshold <= 1.0:
            self.get_logger().error(
                f'参数无效：conf_threshold={self.conf_threshold}，'
                '必须在 0 到 1 之间'
            )
            raise ValueError('conf_threshold 无效')

        if self.input_size <= 0:
            self.get_logger().error(
                f'参数无效：input_size={self.input_size}，必须大于 0'
            )
            raise ValueError('input_size 无效')

        try:
            self.model = YOLO(self.model_path)
        except Exception as error:
            self.get_logger().error(
                f'模型加载失败：model_path={self.model_path}, error={error}'
            )
            raise RuntimeError('模型加载失败') from error

        self.subscription = self.create_subscription(
            Image,
            '/camera/image_raw',
            self.image_callback,
            PERCEPTION_QOS,
        )

        self.detection_publisher = self.create_publisher(
            Detection2DArray,
            '/perception/detections',
            PERCEPTION_QOS,
        )

        self.get_logger().info(
            f'模型已加载：model_path={self.model_path}, '
            f'device={self.device}, '
            f'conf_threshold={self.conf_threshold}, '
            f'input_size={self.input_size}'
        )

    def image_callback(self, msg):
        if msg.encoding.lower() != 'bgr8':
            self.get_logger().error(
                f'跳过图像：不支持 encoding={msg.encoding}，'
                '当前只支持 bgr8'
            )
            return

        if msg.height <= 0 or msg.width <= 0:
            self.get_logger().error(
                f'跳过空图像：height={msg.height}, width={msg.width}'
            )
            return

        expected_step = msg.width * 3

        if msg.step < expected_step:
            self.get_logger().error(
                f'跳过图像：step={msg.step} 小于 '
                f'bgr8 所需的 {expected_step}'
            )
            return

        image_data = np.frombuffer(msg.data, dtype=np.uint8)
        expected_size = msg.height * msg.step

        if image_data.size != expected_size:
            self.get_logger().error(
                f'跳过图像：字节数实际={image_data.size}，'
                f'预期={expected_size}'
            )
            return

        try:
            rows = image_data.reshape(msg.height, msg.step)
            frame = rows[:, :expected_step].reshape(
                msg.height,
                msg.width,
                3
            )
        except ValueError as error:
            self.get_logger().error(
                f'跳过图像：无法恢复 bgr8 图像，error={error}'
            )
            return

        try:
            results = self.model.predict(
                source=frame,
                imgsz=self.input_size,
                conf=self.conf_threshold,
                device=self.device,
                verbose=False,
            )
        except Exception as error:
            self.get_logger().error(
                f'模型推理失败：source_frame={msg.header.frame_id}, '
                f'error={error}'
            )
            return

        result = results[0]
        candidates = []

        if result.boxes is not None:
            for box in result.boxes:
                class_index = int(box.cls[0].item())

                candidates.append(
                    {
                        'class_id': str(result.names[class_index]),
                        'score': float(box.conf[0].item()),
                        'xyxy': tuple(
                            float(value)
                            for value in box.xyxy[0].tolist()
                        ),
                    }
                )

        try:
            detections_msg = build_detection_array(
                header=msg.header,
                image_width=msg.width,
                image_height=msg.height,
                candidates=candidates,
            )
        except ValueError as error:
            self.get_logger().error(
                f'检测框无效，跳过当前图像：{error}'
            )
            return

        self.detection_publisher.publish(detections_msg)

        source_time = (
            msg.header.stamp.sec
            + msg.header.stamp.nanosec / 1_000_000_000
        )

        self.get_logger().info(
            f'发布 /perception/detections：source_time={source_time:.3f}s, '
            f'count={len(detections_msg.detections)}'
        )


def main(args=None):
    rclpy.init(args=args)
    node = None

    try:
        node = DetectorNode()
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
