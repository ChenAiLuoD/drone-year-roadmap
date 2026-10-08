"""处理过程中的速度和统计报告计算。"""


def calculate_processing_fps(processed_frame_count, total_processing_time):
    """计算整个处理过程的平均处理 FPS。"""
    if total_processing_time <= 0:
        return 0.0
    return processed_frame_count / total_processing_time


def calculate_average_motion_area(total_motion_area, processed_frame_count):
    """计算每个已处理帧的平均运动区域面积。"""
    if processed_frame_count <= 0:
        return 0.0
    return total_motion_area / processed_frame_count


def build_report(
    input_path,
    input_info,
    output_path,
    output_fps,
    output_width,
    output_height,
    processed_frame_count,
    parameters,
    total_processing_time,
    total_motion_area,
):
    """把输入、输出、参数和统计信息组织成可写入 JSON 的字典。"""
    return {
        "input": {"path": str(input_path), **input_info},
        "output": {
            "path": str(output_path),
            "fps": output_fps,
            "width": output_width,
            "height": output_height,
            "processed_frame_count": processed_frame_count,
        },
        "parameters": parameters,
        "statistics": {
            "total_processing_seconds": total_processing_time,
            "average_processing_fps": calculate_processing_fps(
                processed_frame_count, total_processing_time
            ),
            "average_motion_area": calculate_average_motion_area(
                total_motion_area, processed_frame_count
            ),
        },
    }
