"""批量提取文件夹中 MP4 的原始音频流，不进行重新编码。

依赖：
    pip install ffmpeg-python

此外，系统中需要已经安装 FFmpeg，并确保 ``ffmpeg`` 命令可用。

使用示例：
    python mp4_to_mp3.py "D:\\Videos"
    python mp4_to_mp3.py "D:\\Videos" --overwrite

如果不传入文件夹路径，程序会在启动后提示输入。

输出文件与视频同名，扩展名根据原音频编码决定。例如 AAC 音频保存为
``.m4a``，MP3 音频保存为 ``.mp3``。直接复制音频流不会改变码率和音质。
"""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

try:
    import ffmpeg
except ModuleNotFoundError:
    ffmpeg = None


AUDIO_EXTENSIONS = {
    "aac": ".m4a",
    "alac": ".m4a",
    "mp3": ".mp3",
    "opus": ".opus",
    "vorbis": ".ogg",
    "flac": ".flac",
    "ac3": ".ac3",
    "eac3": ".eac3",
    "truehd": ".thd",
    "dts": ".dts",
}


def find_mp4_files(folder: Path) -> list[Path]:
    """递归查找文件夹下所有扩展名为 .mp4 的文件。"""
    return sorted(
        (path for path in folder.rglob("*") if path.is_file() and path.suffix.lower() == ".mp4"),
        key=lambda path: str(path).lower(),
    )


def get_audio_codec(input_file: Path) -> str:
    """读取第一个音频流的编码名称。"""
    probe = ffmpeg.probe(str(input_file))
    audio_stream = next(
        (stream for stream in probe.get("streams", []) if stream.get("codec_type") == "audio"),
        None,
    )
    if audio_stream is None:
        raise ValueError("文件中不包含音频流")

    codec_name = audio_stream.get("codec_name")
    if not codec_name:
        raise ValueError("无法识别音频编码")
    return codec_name.lower()


def get_output_file(input_file: Path, codec_name: str) -> Path:
    """根据音频编码生成同名输出文件路径。"""
    extension = AUDIO_EXTENSIONS.get(codec_name, ".mka")
    return input_file.with_suffix(extension)


def extract_audio(input_file: Path, output_file: Path, overwrite: bool = False) -> None:
    """使用流复制提取音频，不重新编码。"""
    stream = ffmpeg.input(str(input_file)).audio
    command = ffmpeg.output(
        stream,
        str(output_file),
        acodec="copy",
    )

    if overwrite:
        command = command.overwrite_output()

    command.run(capture_stdout=True, capture_stderr=True)


def convert_folder(folder: Path, overwrite: bool = False) -> tuple[int, int, int]:
    """转换文件夹中的 MP4，返回成功、跳过和失败的数量。"""
    mp4_files = find_mp4_files(folder)
    success_count = 0
    skipped_count = 0
    failed_count = 0

    if not mp4_files:
        print(f"[INFO] 未找到 MP4 文件：{folder}")
        return success_count, skipped_count, failed_count

    print(f"[INFO] 共找到 {len(mp4_files)} 个 MP4 文件")

    for index, input_file in enumerate(mp4_files, start=1):
        print(f"[{index}/{len(mp4_files)}] {input_file}")

        try:
            codec_name = get_audio_codec(input_file)
            output_file = get_output_file(input_file, codec_name)

            if output_file.exists() and not overwrite:
                print(f"  [SKIP] 音频文件已存在：{output_file}")
                skipped_count += 1
                continue

            extract_audio(input_file, output_file, overwrite=overwrite)
            print(f"  [OK] 已保存：{output_file}（{codec_name}，未重新编码）")
            success_count += 1
        except ValueError as error:
            print(f"  [ERR] 提取失败：{error}")
            failed_count += 1
        except ffmpeg.Error as error:
            stderr = error.stderr.decode("utf-8", errors="replace").strip() if error.stderr else str(error)
            print(f"  [ERR] 提取失败：{stderr}")
            failed_count += 1
        except OSError as error:
            print(f"  [ERR] 无法运行 FFmpeg 或写入文件：{error}")
            failed_count += 1

    return success_count, skipped_count, failed_count


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="递归提取 MP4 的原始音频流；不重新编码，码率和音质保持不变。"
    )
    parser.add_argument("folder", nargs="?", help="要扫描的文件夹路径")
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="覆盖已经存在的同名音频文件（默认跳过）",
    )
    return parser.parse_args()


def normalize_folder(raw_path: str) -> Path:
    """清理用户输入中的首尾空格及成对引号。"""
    return Path(raw_path.strip().strip('"').strip("'")).expanduser()


def main() -> int:
    args = parse_args()

    if ffmpeg is None:
        print("[ERR] 未安装 ffmpeg-python，请先执行：pip install ffmpeg-python")
        return 1
    if shutil.which("ffmpeg") is None:
        print("[ERR] 未找到 FFmpeg，请先安装 FFmpeg 并将 ffmpeg 命令加入 PATH")
        return 1

    raw_folder = args.folder or input("请输入要处理的文件夹路径：")
    folder = normalize_folder(raw_folder)

    if not folder.exists():
        print(f"[ERR] 路径不存在：{folder}")
        return 1
    if not folder.is_dir():
        print(f"[ERR] 输入路径不是文件夹：{folder}")
        return 1

    success, skipped, failed = convert_folder(folder, overwrite=args.overwrite)
    print("\n[DONE] 处理完成")
    print(f"成功：{success}，跳过：{skipped}，失败：{failed}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
