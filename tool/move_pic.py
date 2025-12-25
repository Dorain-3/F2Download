import os
import shutil
from pathlib import Path


def move_image_files_with_suffix(source_dir, target_dir):
    """
    将源目录及其所有子目录中的 jpg 和 png 文件移动到目标目录。
    如果目标目录中存在同名文件，则自动添加序号。

    Args:
        source_dir (str): 源目录（Windows路径）
        target_dir (str): 目标目录
    """
    # 定义要移动的图片扩展名（不区分大小写）
    image_extensions = ('.jpg', '.png')

    # 确保目标目录存在
    os.makedirs(target_dir, exist_ok=True)

    # 用于记录已移动的文件数量
    moved_count = 0
    # 用于跟踪目标目录中已存在的文件名，处理重复[1,9](@ref)
    file_counters = {}

    # 使用 os.walk 递归遍历源目录及其所有子目录[6,7](@ref)
    for root, dirs, files in os.walk(source_dir):
        for filename in files:
            # 检查文件扩展名是否为 jpg 或 png（不区分大小写）
            if filename.lower().endswith(image_extensions):
                source_file_path = os.path.join(root, filename)

                # 生成目标文件名（处理重复情况）
                base_name = os.path.splitext(filename)[0]  # 主文件名
                extension = os.path.splitext(filename)[1].lower()  # 扩展名

                target_filename = filename  # 初始目标文件名
                counter = 1

                # 如果文件名已存在，则添加序号[1,9](@ref)
                while os.path.exists(os.path.join(target_dir, target_filename)):
                    target_filename = f"{base_name}_{counter}{extension}"
                    counter += 1

                target_file_path = os.path.join(target_dir, target_filename)

                try:
                    # 移动文件[4,10](@ref)
                    shutil.move(source_file_path, target_file_path)
                    moved_count += 1
                    print(f"已移动: {source_file_path} -> {target_file_path}")
                except Exception as e:
                    print(f"移动文件失败 {source_file_path}: {str(e)}")

    print(f"\n操作完成！共移动了 {moved_count} 个图片文件。")


# 使用示例
if __name__ == "__main__":
    # 设置您的源目录路径（需要搜索的目录）
    source_directory = r"D:\Settings\TikTok\video"

    # 设置目标目录路径（文件将被移动到此）
    target_directory = r"D:\Settings\TikTok\pic"

    # 调用函数执行移动操作
    move_image_files_with_suffix(source_directory, target_directory)
