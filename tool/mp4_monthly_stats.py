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


def group_by_month(created_dates):
    """
    按月份对文件创建日期进行分组统计

    Args:
        created_dates: 创建日期列表

    Returns:
        dict: 按 'YYYY-MM' 格式分组的文件数量
    """
    monthly_count = defaultdict(int)
    for created_at in created_dates:
        month_key = created_at.strftime('%Y-%m')
        monthly_count[month_key] += 1
    return monthly_count


def display_monthly_count(monthly_count, total_files):
    """
    在控制台显示每个月份的 mp4 文件数量
    """
    if not monthly_count:
        print("未找到任何 mp4 文件")
        return

    sorted_months = sorted(monthly_count.keys())

    print("\n" + "=" * 40)
    print("MP4 文件按月统计")
    print("=" * 40)
    print(f"文件总数: {total_files:,} 个")
    print(f"涉及月份: {len(monthly_count)} 个月")
    print("=" * 40)
    print(f"{'月份':<12} {'文件数量':<10}")
    print("-" * 40)

    for month in sorted_months:
        print(f"{month:<12} {monthly_count[month]:<10,}")

    print("-" * 40)


def main():
    target_dir = input("请输入要统计的目标文件夹路径: ").strip().strip('"')

    if not target_dir:
        print("错误: 未输入路径")
        return

    created_dates = get_mp4_creation_dates(target_dir)

    if created_dates is None or len(created_dates) == 0:
        return

    monthly_count = group_by_month(created_dates)

    display_monthly_count(monthly_count, len(created_dates))

    print("\n✅ 统计完成！")


if __name__ == "__main__":
    main()
