"""批量修正 Windows 文件的创建时间为其修改时间。

递归遍历指定文件夹及其所有子文件夹中的文件，
将每个文件的创建时间设置为该文件的修改时间。
脚本依赖 ``win32-setctime``，并使用 Windows 对 ``st_ctime`` 的“创建时间”语义。
"""

import os
from pathlib import Path
from win32_setctime import setctime


def batch_set_creation_to_modification(root_folder: str):
    """
    递归遍历 root_folder 及其所有子文件夹，
    将每个文件的创建时间设置为该文件的修改时间。
    """
    root_path = Path(root_folder)
    count_modified = 0
    count_skipped = 0
    count_errors = 0

    # 使用 rglob('*') 递归遍历所有文件和目录
    for file_path in root_path.rglob('*'):
        # 跳过目录，只处理文件
        if not file_path.is_file():
            continue

        try:
            # 获取文件的修改时间（作为时间戳）
            mtime = os.path.getmtime(file_path)
            # 获取当前创建时间
            ctime = os.path.getctime(file_path)
        except OSError as e:
            print(f"⚠️ 无法读取时间信息，跳过: {file_path.relative_to(root_path)} ({e})")
            count_errors += 1
            continue

        # 如果创建时间已经等于修改时间，跳过
        if abs(ctime - mtime) < 0.001:  # 允许微小的时间差
            count_skipped += 1
            continue

        try:
            # 将创建时间设置为修改时间
            setctime(str(file_path), mtime)
            # 同时更新访问时间为修改时间
            os.utime(file_path, (mtime, mtime))
            count_modified += 1
            # 显示相对路径，便于识别子文件夹中的文件
            rel_path = file_path.relative_to(root_path)
            print(f"✅ 已修改: {rel_path}")
        except OSError as e:
            print(f"❌ 修改失败: {file_path.relative_to(root_path)} ({e})")
            count_errors += 1

    print(f"\n完成。共修改 {count_modified} 个文件，跳过 {count_skipped} 个，错误 {count_errors} 个。")


if __name__ == "__main__":
    # 请修改这个路径
    FOLDER = input()

    print(f"开始处理文件夹: {FOLDER}")
    print("递归遍历所有子文件夹...")
    batch_set_creation_to_modification(FOLDER)
