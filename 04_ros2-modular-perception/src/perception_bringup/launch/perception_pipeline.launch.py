import os

from launch import LaunchDescription
from launch.actions import (
    DeclareLaunchArgument,
    LogInfo,
    OpaqueFunction,
    RegisterEventHandler,
    TimerAction,
)
from launch.event_handlers import OnProcessExit
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def exit_log(node_name, node_action):
    return RegisterEventHandler(
        OnProcessExit(
            target_action=node_action,
            on_exit=[
                LogInfo(
                    msg=[
                        node_name,
                        ' 已退出；请查看该节点此前的日志判断是正常停止还是异常。',
                    ]
                )
            ],
        )
    )


def launch_nodes(context, *args, **kwargs):
    params_file = LaunchConfiguration('params_file').perform(context)
    max_frames_text = LaunchConfiguration('max_frames').perform(context)
    delay_text = LaunchConfiguration(
        'video_start_delay_sec'
    ).perform(context)
    detector_pythonpath = LaunchConfiguration(
        'detector_pythonpath'
    ).perform(context)

    if not detector_pythonpath:
        raise RuntimeError(
            'detector_pythonpath 不能为空；'
            '请传入第 3 月虚拟环境的 site-packages 路径。'
        )

    inherited_pythonpath = os.environ.get('PYTHONPATH', '')
    ros_pythonpath = os.pathsep.join(
        path
        for path in inherited_pythonpath.split(os.pathsep)
        if path and os.path.abspath(path) != os.path.abspath(detector_pythonpath)
    )

    cv_bridge_env = {
        'PYTHONNOUSERSITE': '1',
        'PYTHONPATH': ros_pythonpath,
    }

    detector_env = {
        'PYTHONNOUSERSITE': '1',
        'PYTHONPATH': os.pathsep.join(
            filter(None, [detector_pythonpath, ros_pythonpath])
        ),
    }

    video_parameters = [params_file]

    if max_frames_text:
        video_parameters.append(
            {'max_frames': int(max_frames_text)}
        )

    video_source = Node(
        package='video_source',
        executable='video_source_node',
        name='video_source_node',
        output='screen',
        parameters=video_parameters,
        additional_env=cv_bridge_env,
    )

    detector = Node(
        package='detector',
        executable='detector_node',
        name='detector_node',
        output='screen',
        parameters=[params_file],
        additional_env=detector_env,
    )

    tracker = Node(
        package='tracker',
        executable='tracker_node',
        name='tracker_node',
        output='screen',
        parameters=[params_file],
    )

    visualizer = Node(
        package='visualizer',
        executable='visualizer_node',
        name='visualizer_node',
        output='screen',
        parameters=[params_file],
        additional_env=cv_bridge_env,
    )

    return [
        detector,
        tracker,
        visualizer,

        TimerAction(
            period=float(delay_text),
            actions=[video_source],
        ),

        exit_log('detector_node', detector),
        exit_log('tracker_node', tracker),
        exit_log('visualizer_node', visualizer),
        exit_log('video_source_node', video_source),
    ]


def generate_launch_description():
    default_params_file = PathJoinSubstitution(
        [
            FindPackageShare('perception_bringup'),
            'config',
            'pipeline.yaml',
        ]
    )

    return LaunchDescription(
        [
            DeclareLaunchArgument(
                'params_file',
                default_value=default_params_file,
                description='ROS 2 参数文件路径。',
            ),
            DeclareLaunchArgument(
                'max_frames',
                default_value='',
                description=(
                    '可选。非空时覆盖 YAML 中的 max_frames。'
                ),
            ),
            DeclareLaunchArgument(
                'video_start_delay_sec',
                default_value='10.0',
                description=(
                    '等待检测、跟踪和可视化节点初始化后，再启动视频源的秒数。'
                ),
            ),
            DeclareLaunchArgument(
                'detector_pythonpath',
                default_value='',
                description=(
                    '第 3 月虚拟环境的 site-packages 路径，'
                    '只提供给 detector_node。'
                ),
            ),
            OpaqueFunction(function=launch_nodes),
        ]
    )