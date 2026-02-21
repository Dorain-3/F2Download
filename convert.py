import ffmpeg
from pathlib import Path
import os
from show_progress import show_progress

def rename_video_file(old_file_path):
    """
    生成重命名后的视频文件路径（返回字符串路径）
    """
    # 将输入转换为Path对象
    old_path = Path(old_file_path)

    # 构建新文件名：原主文件名_H265.原后缀，保持路径不变
    new_path = old_path.with_name(f"{old_path.stem}_H265{old_path.suffix}")

    # 返回新路径的字符串形式
    return str(new_path)

def convert_to_h265_gpu_with_progressbar(input_file):
    """
    使用NVIDIA GPU将视频转换为H.265编码，并显示进度条 (修复版)
    """
    # 确保输入路径为Path对象
    input_path = Path(input_file) if isinstance(input_file, str) else input_file

    # 生成输出文件路径（字符串）
    output_file = rename_video_file(input_path)

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
                preset='fast',  # 编码预设，平衡速度与质量
                cq=23,  # 恒定质量因子
                acodec='copy'  # 直接复制音频流，避免重新编码
            )
            # 使用返回的address而不是硬编码的地址
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
        convert_to_h265_gpu_with_progressbar(file_path)
        input("")
    else:
        print(f"❌ 文件不存在: {file_path}")