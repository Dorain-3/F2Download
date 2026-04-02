import os
import shutil
import sys
from pathlib import Path

import yaml


def move_image_files_with_suffix(source_dir, target_dir, config_path):
    image_extensions = None

    try:

        with open(config_path, 'r', encoding='utf-8') as file:
            config = yaml.safe_load(file)  # 使用 safe_load 避免安全风险[7,8](@ref)

        image_extensions = tuple(config['image_extensions'])

    except Exception as e:
        print(e)

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
    script_dir = Path(sys.executable).parent.resolve()
    source_directory = script_dir.parent

    target_directory = source_directory.parent / "pic"

    config_path = source_directory / "config.yaml"

    # 调用函数执行移动操作
    move_image_files_with_suffix(source_directory, target_directory, config_path)

    input('已完成')
