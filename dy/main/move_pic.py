"""
图片移动工具 - 将图片文件从源目录移动到目标目录

功能说明:
    本脚本从配置文件中读取图片扩展名列表，递归遍历源目录，将所有匹配的图片文件
    移动到目标目录。支持处理重复文件名（自动添加序号）。

工作流程:
    1. 从配置文件读取图片扩展名列表
    2. 确保目标目录存在
    3. 递归遍历源目录查找图片文件
    4. 处理重复文件名（添加序号）
    5. 移动文件并统计数量

使用方式:
    直接运行本脚本即可开始移动
"""

import os
import shutil
from dy.main.read_cfg import get_config


def move_image_files_with_suffix(source_dir, target_dir, image_extensions):
    """
    移动指定扩展名的图片文件
    
    Args:
        source_dir: 源目录路径
        target_dir: 目标目录路径
        image_extensions: 需要移动的图片扩展名列表
    """
    # 转换为endswith支持的元组
    image_extensions = tuple(image_extensions)
    if not image_extensions:
        raise ValueError("配置项 image_extensions 不能为空")

    # 确保目标目录存在，如果不存在则创建
    os.makedirs(target_dir, exist_ok=True)

    # 用于记录已移动的文件数量
    moved_count = 0
    # 用于跟踪目标目录中已存在的文件名，处理重复
    file_counters = {}

    # 使用 os.walk 递归遍历源目录及其所有子目录
    for root, dirs, files in os.walk(source_dir):
        for filename in files:
            # 检查文件扩展名是否在配置的扩展名列表中（不区分大小写）
            if filename.lower().endswith(image_extensions):
                source_file_path = os.path.join(root, filename)

                # 生成目标文件名（处理重复情况）
                base_name = os.path.splitext(filename)[0]  # 主文件名（不含扩展名）
                extension = os.path.splitext(filename)[1].lower()  # 扩展名

                target_filename = filename  # 初始目标文件名
                counter = 1

                # 如果文件名已存在，则添加序号
                while os.path.exists(os.path.join(target_dir, target_filename)):
                    target_filename = f"{base_name}_{counter}{extension}"
                    counter += 1

                target_file_path = os.path.join(target_dir, target_filename)

                try:
                    # 移动文件到目标目录
                    shutil.move(source_file_path, target_file_path)
                    moved_count += 1
                    print(f"已移动: {source_file_path} -> {target_file_path}")
                except Exception as e:
                    print(f"移动文件失败 {source_file_path}: {str(e)}")

    print(f"\n操作完成！共移动了 {moved_count} 个图片文件。")


if __name__ == "__main__":
    cfg = get_config()

    # 调用函数执行移动操作
    move_image_files_with_suffix(
        cfg.image_source_path,
        cfg.image_target_path,
        cfg.image_extensions,
    )

    # 等待用户输入后退出
    input('已完成')
