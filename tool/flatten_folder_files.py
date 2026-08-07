"""将所有子文件夹中的文件集中移动到指定目录的根层。

程序会先收集目标目录所有层级中的文件，再逐个移动到目标目录本身。
根目录中原有的文件不会被移动或覆盖；如果目标位置存在同名文件，程序会
在文件名后追加递增数字，例如 ``photo.jpg`` 会改名为 ``photo_1.jpg``。

使用方式：
    python flatten_folder_files.py "D:\\Files"

如果没有传入目录参数，程序会交互式提示输入路径。移动完成后不会自动
删除已变空的子文件夹。
"""

from __future__ import annotations

import argparse
import shutil
from pathlib import Path


def normalize_folder(raw_path: str) -> Path:
    """清理用户输入的空格和成对引号，并返回绝对目录路径。"""
    return Path(raw_path.strip().strip('"').strip("'")).expanduser().resolve()


def build_unique_destination(folder: Path, filename: str) -> Path:
    """生成不与现有文件重名的目标路径。

    文件名没有冲突时直接使用原名称；发生冲突时，在扩展名前依次追加
    ``_1``、``_2`` 等后缀，直到找到可用名称。
    """
    destination = folder / filename
    if not destination.exists():
        return destination

    source_name = Path(filename)
    stem = source_name.stem
    suffix = source_name.suffix
    counter = 1

    while True:
        destination = folder / f"{stem}_{counter}{suffix}"
        if not destination.exists():
            return destination
        counter += 1


def collect_nested_files(folder: Path) -> list[Path]:
    """收集目录所有子层级中的文件，不包含根目录已有文件。"""
    return sorted(
        (path for path in folder.rglob("*") if path.is_file() and path.parent != folder),
        key=lambda path: str(path).lower(),
    )


def flatten_folder(folder: Path) -> tuple[int, int, int]:
    """将子文件夹中的文件移动到根目录。

    Returns:
        tuple[int, int, int]: 成功移动数、因重名而改名数、移动失败数。
    """
    nested_files = collect_nested_files(folder)
    moved_count = 0
    renamed_count = 0
    failed_count = 0

    if not nested_files:
        print(f"[INFO] 未在子文件夹中找到文件：{folder}")
        return moved_count, renamed_count, failed_count

    print(f"[INFO] 共找到 {len(nested_files)} 个待移动文件")

    for index, source in enumerate(nested_files, start=1):
        destination = build_unique_destination(folder, source.name)
        was_renamed = destination.name != source.name

        try:
            shutil.move(str(source), str(destination))
            moved_count += 1
            if was_renamed:
                renamed_count += 1
                print(
                    f"[{index}/{len(nested_files)}] [MOVED] "
                    f"{source} -> {destination.name}（重名，已自动改名）"
                )
            else:
                print(f"[{index}/{len(nested_files)}] [MOVED] {source} -> {destination.name}")
        except (OSError, shutil.Error) as error:
            failed_count += 1
            print(f"[{index}/{len(nested_files)}] [ERROR] 移动失败：{source}：{error}")

    return moved_count, renamed_count, failed_count


def parse_args() -> argparse.Namespace:
    """解析可选的目标目录命令行参数。"""
    parser = argparse.ArgumentParser(
        description="将所有子文件夹中的文件移动到输入目录根层，并自动处理重名文件。"
    )
    parser.add_argument("folder", nargs="?", help="需要整理的文件夹路径")
    return parser.parse_args()


def main() -> int:
    """验证输入目录，执行文件移动并返回进程状态码。"""
    args = parse_args()
    raw_folder = args.folder or input("请输入需要整理的文件夹路径：")
    folder = normalize_folder(raw_folder)

    if not folder.exists():
        print(f"[ERROR] 路径不存在：{folder}")
        return 1
    if not folder.is_dir():
        print(f"[ERROR] 输入路径不是文件夹：{folder}")
        return 1

    print(f"[INFO] 目标目录：{folder}")
    moved, renamed, failed = flatten_folder(folder)

    print("\n[DONE] 处理完成")
    print(f"成功移动：{moved}，重名改名：{renamed}，失败：{failed}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
