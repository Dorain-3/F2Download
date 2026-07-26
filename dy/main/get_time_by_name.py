"""
日期提取工具 - 从文件名和文件属性中提取日期信息

功能说明:
    本模块提供多个函数用于从文件中提取日期信息，主要用于抖音视频项目中确定
    已下载视频的最新日期，以便后续更新时从该日期之后开始下载。

主要功能:
    - get_date_from_filename(): 从文件名中提取日期（匹配格式：YYYY-MM-DD）
    - get_latest_mp4_creation_time(): 查找目录中MP4文件的最晚创建时间
    - get_latest_date(): 综合方法，优先从文件名提取，其次使用文件创建时间

使用方式:
    from dy.main.get_time_by_name import get_latest_date
    
    latest_date = get_latest_date("/path/to/folder")
    print(latest_date.strftime('%Y-%m-%d'))
"""

import os
import re
from datetime import datetime
from pathlib import Path


def get_date_from_filename(filename) -> datetime | None:
    """
    从文件名中提取日期时间信息
    
    支持的文件名格式: "2025-12-23.mp4" 或包含类似日期格式的文件名
    
    Args:
        filename: 文件名
        
    Returns:
        如果匹配成功，返回datetime对象，否则返回None
    """
    # 正则表达式：匹配YYYY-MM-DD格式的日期
    pattern = r'(\d{4}-\d{2}-\d{2})'
    match = re.search(pattern, filename)

    if match:
        try:
            # 提取日期字符串并转换为datetime对象
            date_str = match.group(1)
            return datetime.strptime(date_str, '%Y-%m-%d')
        except ValueError:
            # 日期格式不正确
            return None
    return None


def get_latest_mp4_creation_time(folder_path: Path) -> datetime | None:
    """
    查找指定文件夹中所有MP4文件的最晚创建时间
    
    Args:
        folder_path: 要搜索的文件夹路径
        
    Returns:
        datetime: 最晚的创建时间，如果没有找到MP4文件则返回None
    """
    latest_time = None

    try:
        # 遍历文件夹及其所有子文件夹
        for root, dirs, files in os.walk(folder_path):
            for file in files:
                # 检查文件扩展名是否为.mp4（不区分大小写）
                if file.lower().endswith('.mp4'):
                    file_path = os.path.join(root, file)

                    try:
                        # 获取文件的创建时间
                        creation_time = os.path.getctime(file_path)

                        # 更新最晚创建时间
                        if latest_time is None or creation_time > latest_time:
                            latest_time = creation_time

                    except (OSError, PermissionError) as e:
                        # 处理无法访问的文件
                        print(f"警告：无法访问文件 '{file_path}': {e}")
                        continue

    except Exception as e:
        print(f"遍历文件夹时发生错误: {e}")
        return None

    if latest_time is not None:
        return datetime.fromtimestamp(latest_time)
    else:
        return None


def get_latest_date(directory) -> datetime | None:
    """
    从指定目录的文件中提取最晚的日期
    
    优先从文件名中提取日期，如果文件名中没有日期信息，则使用文件创建时间。
    
    Args:
        directory: 要扫描的目录路径
        
    Returns:
        datetime: 最晚的日期，如果目录为空或处理失败则返回None或默认日期
    """
    try:
        # 将目录路径转换为Path对象
        path = Path(directory)
        # 获取目录下所有非JSON文件
        files = [f for f in path.iterdir() if f.is_file() and f.suffix != '.json']

        # 如果目录中没有文件
        if not files:
            print(directory)
            print(f"目录中没有文件\n")
            return datetime(2021, 1, 1)

        latest_date = None

        # 遍历所有文件，从文件名中提取日期
        for file in files:
            filename = file.name
            date_obj = get_date_from_filename(filename)

            if date_obj:
                # 更新最晚日期
                if latest_date is None or date_obj > latest_date:
                    latest_date = date_obj

        # 如果从文件名中没有提取到日期，使用文件创建时间
        if latest_date is None:
            latest_date = get_latest_mp4_creation_time(directory)
            return latest_date

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
    from dy.main.read_cfg import get_config

    # 从统一配置获取测试目录
    path = get_config().post_path

    # 示例: 使用完整功能
    result = get_latest_date(path)
    if result:
        print(f"最晚日期: {result.strftime('%Y-%m-%d')}")
