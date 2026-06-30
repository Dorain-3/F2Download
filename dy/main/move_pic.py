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
import sys
from pathlib import Path

import yaml


def move_image_files_with_suffix(source_dir, target_dir, config_path):
    """
    移动指定扩展名的图片文件
    
    Args:
        source_dir: 源目录路径
        target_dir: 目标目录路径
        config_path: 配置文件路径（包含image_extensions配置）
    """
    # 初始化图片扩展名变量
    image_extensions = None

    try:
        # 读取配置文件
        with open(config_path, 'r', encoding='utf-8') as file:
            config = yaml.safe_load(file)

        # 提取图片扩展名列表并转换为元组
        image_extensions = tuple(config['image_extensions'])

    except Exception as e:
        print(e)

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
    # 获取Python可执行文件所在目录的父目录作为源目录
    script_dir = Path(sys.executable).parent.resolve()
    source_directory = script_dir.parent

    # 构建目标目录路径（源目录的父目录下的pic文件夹）
    target_directory = source_directory.parent / "pic"

    # 构建配置文件路径
    config_path = source_directory / "config.yaml"

    # 调用函数执行移动操作
    move_image_files_with_suffix(source_directory, target_directory, config_path)

    # 等待用户输入后退出
    input('已完成')