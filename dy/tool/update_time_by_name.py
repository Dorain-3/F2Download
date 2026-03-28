import os
import re
from datetime import datetime
from pathlib import Path


def extract_date_from_filename(filename):
    """
    从文件名中提取日期时间信息

    Args:
        filename: 文件名

    Returns:
        如果匹配成功，返回datetime对象，否则返回None
    """
    # 匹配格式: "2025-12-23.mp4"
    # 日期时间部分格式: 年-月-日
    pattern = r'(\d{4}-\d{2}-\d{2})'
    match = re.search(pattern, filename)

    if match:
        try:
            # 提取日期时间字符串并转换为datetime对象
            date_str = match.group(1)
            return datetime.strptime(date_str, '%Y-%m-%d')
        except ValueError:
            # 日期格式不正确
            return None
    return None


def find_latest_date_from_files(directory='.'):
    """
    从指定目录的文件中提取最晚的日期

    Args:
        directory: 要扫描的目录，默认为当前目录

    Returns:
        包含最新日期和对应文件名的字典，如果没有找到则返回None
    """
    try:
        # 获取目录下所有文件
        path = Path(directory)
        files = [f for f in path.iterdir() if f.is_file() and f.suffix != '.json']

        if not files:
            print(f"目录 '{directory}' 中没有文件")
            return None

        latest_date = None

        for file in files:
            filename = file.name
            date_obj = extract_date_from_filename(filename)

            if date_obj:
                # 如果这是第一个找到的日期，或者比当前最晚的日期更晚
                if latest_date is None or date_obj > latest_date:
                    latest_date = date_obj

        if latest_date is None:
            print("未找到符合日期格式的文件")
            return None

        return latest_date

    except FileNotFoundError:
        print(f"错误: 目录 '{directory}' 不存在")
        return None
    except PermissionError:
        print(f"错误: 没有权限访问目录 '{directory}'")
        return None
    except Exception as e:
        print(f"处理过程中发生错误: {e}")
        return None


if __name__ == "__main__":

    path = Path(r"C:\Users\31749\Dorain_file\TikTok\video\post\_")

    # 示例1: 使用完整功能
    result = find_latest_date_from_files(path)
    if result:
        print(f"最晚日期: {result.strftime('%Y-%m-%d')}")
