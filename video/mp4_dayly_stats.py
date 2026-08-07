"""按创建日期统计目录树中的 MP4 文件数量。"""

import os
from collections import defaultdict
from datetime import datetime


def get_mp4_creation_dates(directory_path):
    """
    递归扫描目录下所有mp4文件，获取其创建日期

    Args:
        directory_path: 要扫描的目录路径

    Returns:
        list: 包含文件创建日期的列表
    """
    if not os.path.exists(directory_path):
        print(f"错误: 路径 '{directory_path}' 不存在")
        return None

    if not os.path.isdir(directory_path):
        print(f"错误: '{directory_path}' 不是目录")
        return None

    created_dates = []
    print(f"正在扫描目录: {directory_path}")
    print("请稍候，正在查找所有 .mp4 文件...\n")

    for root, dirs, files in os.walk(directory_path):
        for file in files:
            _, ext = os.path.splitext(file)
            if ext.lower() != '.mp4':
                continue

            file_path = os.path.join(root, file)
            try:
                stat = os.stat(file_path)
                created_at = datetime.fromtimestamp(stat.st_ctime)
                created_dates.append(created_at)
            except (OSError, PermissionError) as e:
                print(f"警告: 无法访问文件 {file_path}: {e}")

    print(f"扫描完成，共找到 {len(created_dates)} 个 mp4 文件")
    return created_dates


def group_by_day(created_dates):
    """
    按天对文件创建日期进行分组统计

    Args:
        created_dates: 创建日期列表

    Returns:
        dict: 按 'YYYY-MM-DD' 格式分组的文件数量
    """
    daily_count = defaultdict(int)
    for created_at in created_dates:
        day_key = created_at.strftime('%Y-%m-%d')
        daily_count[day_key] += 1
    return daily_count


def display_daily_count(daily_count, total_files):
    """
    在控制台显示每个日期的 mp4 文件数量
    """
    if not daily_count:
        print("未找到任何 mp4 文件")
        return

    sorted_days = sorted(daily_count.keys())

    print("\n" + "=" * 50)
    print("MP4 文件按日统计")
    print("=" * 50)
    print(f"文件总数: {total_files:,} 个")
    print(f"涉及天数: {len(daily_count)} 天")
    print("=" * 50)
    print(f"{'日期':<12} {'文件数量':<10}")
    print("-" * 50)

    for day in sorted_days:
        print(f"{day:<12} {daily_count[day]:<10,}")

    print("-" * 50)

    # 可选：显示统计摘要
    if len(sorted_days) > 1:
        first_day = sorted_days[0]
        last_day = sorted_days[-1]
        print(f"时间范围: {first_day} 至 {last_day}")

        # 计算日均文件数
        avg_per_day = total_files / len(sorted_days)
        print(f"日均文件数: {avg_per_day:.1f}")


def main():
    """读取目标目录，完成扫描、按日聚合并打印统计结果。"""
    target_dir = input("请输入要统计的目标文件夹路径: ").strip().strip('"')

    if not target_dir:
        print("错误: 未输入路径")
        return

    created_dates = get_mp4_creation_dates(target_dir)

    if created_dates is None or len(created_dates) == 0:
        return

    daily_count = group_by_day(created_dates)

    display_daily_count(daily_count, len(created_dates))

    print("\n✅ 统计完成！")


if __name__ == "__main__":
    main()