import ffmpeg
from pathlib import Path
from tool.show_progress import show_progress


def rename_video_file(old_file_path,convert_str:str):
    """
    生成重命名后的视频文件路径（返回字符串路径）
    """
    # 将输入转换为Path对象
    old_path = Path(old_file_path)

    # 构建新文件名：原主文件名_H265.原后缀，保持路径不变
    new_path = old_path.with_name(f"{old_path.stem}_{convert_str}{old_path.suffix}")

    # 返回新路径的字符串形式
    return str(new_path)


def convert_to_h265_nvidia_with_progressbar(input_file):
    """
    使用NVIDIA GPU将视频转换为H.265编码，并显示进度条 (修复版)
    """
    # 确保输入路径为Path对象
    input_path = Path(input_file) if isinstance(input_file, str) else input_file

    # 生成输出文件路径（字符串）
    output_file = rename_video_file(input_path,'h265_nvidia')

    try:
        probe = ffmpeg.probe(str(input_path))
        total_duration = float(probe['format']['duration'])
        print(f"🎬 视频总时长: {total_duration:.2f}秒")

        # 使用 show_progress 上下文管理器，获取地址信息
        with show_progress(total_duration) as address:
            # 构建FFmpeg处理流程
            stream = ffmpeg.input(input_path, hwaccel='cuda')
            stream = ffmpeg.output(
                stream,
                output_file,  # 这里已经是字符串路径
                vcodec='hevc_nvenc',  # 使用NVIDIA的H.265硬件编码器
                preset='p7',  # 编码预设，平衡速度与质量
                cq=28,  # 恒定质量因子
                acodec='copy'  # 直接复制音频流，避免重新编码
            )

            stream = stream.global_args('-progress', f'tcp://{address}')
            # 执行转换
            stream.run(overwrite_output=True)

        print(f"\n✅ 转换成功！输出文件: {output_file}")

    except ffmpeg.Error as e:
        # 安全的错误信息处理
        error_msg = e.stderr.decode() if e.stderr else str(e)
        print(f"❌ FFmpeg错误: {error_msg}")
    except Exception as e:
        print(f"❌ 发生未知错误: {e}")


def convert_to_av1_nvidia_with_progressbar(input_file):
    """
    使用NVIDIA GPU将视频转换为H.265编码，并显示进度条 (修复版)
    """
    # 确保输入路径为Path对象
    input_path = Path(input_file) if isinstance(input_file, str) else input_file

    # 生成输出文件路径（字符串）
    output_file = rename_video_file(input_path,'av1_nvidia')

    try:
        probe = ffmpeg.probe(str(input_path))
        total_duration = float(probe['format']['duration'])
        print(f"🎬 视频总时长: {total_duration:.2f}秒")

        # 使用 show_progress 上下文管理器，获取地址信息
        with show_progress(total_duration) as address:
            # 构建FFmpeg处理流程
            stream = ffmpeg.input(input_path, hwaccel='cuda')
            stream = ffmpeg.output(
                stream,
                output_file,  # 这里已经是字符串路径
                vcodec='av1_nvenc',  # 使用NVIDIA的H.265硬件编码器
                preset='p7',  # 编码预设，平衡速度与质量
                tune='hq',  # 调优为高质量模式
                cq=23,  # 恒定质量
                multipass='fullres',  # 两次编码分析（全分辨率）
                spatial_aq=1,  # 空间自适应量化
                temporal_aq=1,  # 时间自适应量化
                rc_lookahead=40,  # 前瞻帧数
                **{'b:v': '0'},  # 禁用最大码率限制（使用 0 表示无限制）
                acodec='copy'  # 复制音频
            )

            stream = stream.global_args('-progress', f'tcp://{address}')
            # 执行转换
            stream.run(overwrite_output=True)

        print(f"\n✅ 转换成功！输出文件: {output_file}")

    except ffmpeg.Error as e:
        # 安全的错误信息处理
        error_msg = e.stderr.decode() if e.stderr else str(e)
        print(f"❌ FFmpeg错误: {error_msg}")
    except Exception as e:
        print(f"❌ 发生未知错误: {e}")


def convert_to_av1_intel_with_progressbar(input_file):
    """
    使用NVIDIA GPU将视频转换为H.265编码，并显示进度条 (修复版)
    """
    # 确保输入路径为Path对象
    input_path = Path(input_file) if isinstance(input_file, str) else input_file

    # 生成输出文件路径（字符串）
    output_file = rename_video_file(input_path,'av1_intel')

    try:
        probe = ffmpeg.probe(str(input_path))
        total_duration = float(probe['format']['duration'])
        print(f"🎬 视频总时长: {total_duration:.2f}秒")

        # 使用 show_progress 上下文管理器，获取地址信息
        with show_progress(total_duration) as address:
            # 构建FFmpeg处理流程
            stream = ffmpeg.input(input_path, hwaccel='qsv')
            stream = ffmpeg.output(
                stream,
                output_file,  # 这里已经是字符串路径
                vcodec='veryslow',  # 使用NVIDIA的H.265硬件编码器
                preset='veryslow',  # 最慢预设，最佳压缩
                global_quality=23,  # 质量因子，例如 23
                extbrc=1,  # 启用外部码率控制
                look_ahead_depth=40,  # 前瞻深度
                adaptive_i=1,  # 自适应 I 帧
                adaptive_b=1,  # 自适应 B 帧
                b_strategy=1,  # B 帧策略
                bf=7,  # 最大 B 帧数
                acodec='copy'  # 复制音频
            )

            stream = stream.global_args('-progress', f'tcp://{address}')
            # 执行转换
            stream.run(overwrite_output=True)

        print(f"\n✅ 转换成功！输出文件: {output_file}")

    except ffmpeg.Error as e:
        # 安全的错误信息处理
        error_msg = e.stderr.decode() if e.stderr else str(e)
        print(f"❌ FFmpeg错误: {error_msg}")
    except Exception as e:
        print(f"❌ 发生未知错误: {e}")


if __name__ == "__main__":
    # 获取用户输入并去除可能存在的引号
    user_input = input("请输入视频文件路径: ").strip('"')
    file_path = Path(user_input)

    if file_path.exists():
        convert_to_h265_nvidia_with_progressbar(file_path)
        convert_to_av1_nvidia_with_progressbar(file_path)
        convert_to_av1_nvidia_with_progressbar(file_path)
        input("")

    else:
        print(f"❌ 文件不存在: {file_path}")
