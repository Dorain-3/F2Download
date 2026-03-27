import os
from collections import defaultdict


def get_file_type_stats(directory_path, human_readable=True, sort_by='size', top_n=None):
    """
    统计目录下的文件类型分布和大小

    Args:
        directory_path: 要统计的目录路径
        human_readable: 是否以人类可读格式显示大小
        sort_by: 排序方式 ('size', 'count', 'type')
        top_n: 只显示前N种文件类型，None表示显示全部
    """
    if not os.path.exists(directory_path):
        print(f"错误: 路径 '{directory_path}' 不存在")
        return None, None  # 修改返回值以包含分布信息

    if not os.path.isdir(directory_path):
        print(f"错误: '{directory_path}' 不是目录")
        return None, None

    # 初始化统计字典
    type_stats = defaultdict(lambda: {'count': 0, 'total_size': 0, 'files': []})
    # 初始化大小分布统计字典
    size_dist_stats = defaultdict(lambda: {'count': 0, 'total_size': 0})

    # 遍历目录
    print(f"正在扫描: {directory_path}")

    for root, dirs, files in os.walk(directory_path):
        for file in files:
            file_path = os.path.join(root, file)

            try:
                # 获取文件大小
                file_size = os.path.getsize(file_path)

                # 获取文件扩展名
                _, ext = os.path.splitext(file)
                ext = ext.lower()

                # 处理无扩展名文件
                if not ext:
                    file_type = '无扩展名'
                else:
                    file_type = ext

                # 更新文件类型统计信息
                type_stats[file_type]['count'] += 1
                type_stats[file_type]['total_size'] += file_size
                type_stats[file_type]['files'].append({
                    'path': file_path,
                    'size': file_size,
                    'name': file
                })

                # 更新文件大小分布统计信息
                size_range = _categorize_file_size(file_size)
                size_dist_stats[size_range]['count'] += 1
                size_dist_stats[size_range]['total_size'] += file_size

            except (OSError, PermissionError) as e:
                print(f"警告: 无法访问文件 {file_path}: {e}")

    return type_stats, size_dist_stats


def _categorize_file_size(size_in_bytes):
    """
    根据文件大小（字节）将其归类到预定义的区间。
    这是一个辅助函数，不直接对外暴露。
    """
    if size_in_bytes < 1024:  # 小于1KB
        return "0-1KB"
    elif size_in_bytes < 1024 * 1024:  # 小于1MB
        return "1KB-1MB"
    elif size_in_bytes < 100 * 1024 * 1024:  # 小于100MB
        return "1MB-100MB"
    elif size_in_bytes < 1024 * 1024 * 1024:  # 小于1GB
        return "100MB-1GB"
    else:  # 大于等于1GB
        return ">=1GB"


def format_size(bytes_size, human_readable=True):
    """格式化文件大小"""
    if not human_readable:
        return f"{bytes_size} B"

    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_size < 1024.0 or unit == 'TB':
            break
        bytes_size /= 1024.0

    return f"{bytes_size:.2f} {unit}"


def display_stats(type_stats, human_readable=True, sort_by='size', top_n=None):
    """显示文件类型统计结果"""
    if not type_stats:
        print("未找到任何文件")
        return

    # 计算总数
    total_files = sum(stats['count'] for stats in type_stats.values())
    total_size = sum(stats['total_size'] for stats in type_stats.values())

    # 打印汇总信息
    print("\n" + "=" * 80)
    print(f"文件类型统计汇总:")
    print(f"文件总数: {total_files:,} 个")
    print(f"总大小: {format_size(total_size, human_readable)}")
    print("=" * 80)

    # 按指定方式排序
    if sort_by == 'size':
        sorted_items = sorted(type_stats.items(), key=lambda x: x[1]['total_size'], reverse=True)
    elif sort_by == 'count':
        sorted_items = sorted(type_stats.items(), key=lambda x: x[1]['count'], reverse=True)
    elif sort_by == 'type':
        sorted_items = sorted(type_stats.items(), key=lambda x: x[0])
    else:
        sorted_items = list(type_stats.items())

    # 限制显示数量
    if top_n is not None and top_n > 0:
        sorted_items = sorted_items[:top_n]

    # 打印详细统计表
    print("\n文件类型详细统计:")
    print("-" * 60)
    print(f"{'文件类型':<15} {'数量':<10} {'总大小':<15} {'平均大小':<15} {'占比':<10}")
    print("-" * 60)

    for file_type, stats in sorted_items:
        count = stats['count']
        total = stats['total_size']
        avg_size = total / count if count > 0 else 0
        percentage = (total / total_size * 100) if total_size > 0 else 0

        print(f"{file_type:<15} {count:<10,} {format_size(total, human_readable):<15} "
              f"{format_size(avg_size, human_readable):<15} {percentage:.1f}%")


def display_size_distribution(size_dist_stats, human_readable=True):
    """
    显示文件大小分布统计结果
    """
    if not size_dist_stats:
        print("无文件大小分布数据")
        return

    # 计算总数以便计算百分比
    total_count = sum(stats['count'] for stats in size_dist_stats.values())
    total_size = sum(stats['total_size'] for stats in size_dist_stats.values())

    # 按区间名称排序（确保顺序符合直观认知）
    range_order = ["0-1KB", "1KB-1MB", "1MB-100MB", "100MB-1GB", ">=1GB"]
    sorted_items = []
    for r in range_order:
        if r in size_dist_stats:
            sorted_items.append((r, size_dist_stats[r]))
    # 添加任何未在预定义顺序中的区间（理论上不会发生）
    for r, stats in size_dist_stats.items():
        if r not in range_order:
            sorted_items.append((r, stats))

    print("\n" + "=" * 80)
    print("文件大小分布统计:")
    print("=" * 80)
    print(f"{'大小区间':<15} {'文件数量':<12} {'数量占比':<10} {'区间总大小':<15} {'大小占比':<10}")
    print("-" * 70)

    for size_range, stats in sorted_items:
        count = stats['count']
        range_total_size = stats['total_size']
        count_percentage = (count / total_count * 100) if total_count > 0 else 0
        size_percentage = (range_total_size / total_size * 100) if total_size > 0 else 0

        print(f"{size_range:<15} {count:<12,} {count_percentage:>8.1f}%  "
              f"{format_size(range_total_size, human_readable):<15} {size_percentage:>8.1f}%")


def export_to_csv(type_stats, filename, human_readable=True):
    """导出文件类型统计结果到CSV文件"""
    import csv

    with open(filename, 'w', newline='', encoding='utf-8-sig') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['文件类型', '数量', '总大小', '平均大小', '占比(%)'])

        for file_type, stats in sorted(type_stats.items(),
                                       key=lambda x: x[1]['total_size'],
                                       reverse=True):
            count = stats['count']
            total = stats['total_size']
            avg_size = total / count if count > 0 else 0
            total_all = sum(s['total_size'] for s in type_stats.values())
            percentage = (total / total_all * 100) if total_all > 0 else 0

            if human_readable:
                total_str = format_size(total, human_readable)
                avg_str = format_size(avg_size, human_readable)
            else:
                total_str = str(total)
                avg_str = str(avg_size)

            writer.writerow([file_type, count, total_str, avg_str, f"{percentage:.1f}%"])

    print(f"\n文件类型统计结果已导出到: {filename}")


def export_size_distribution_to_csv(size_dist_stats, filename, human_readable=True):
    """导出文件大小分布统计结果到CSV文件"""
    import csv

    with open(filename, 'w', newline='', encoding='utf-8-sig') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['大小区间', '文件数量', '数量占比(%)', '区间总大小', '大小占比(%)'])

        total_count = sum(stats['count'] for stats in size_dist_stats.values())
        total_size = sum(stats['total_size'] for stats in size_dist_stats.values())

        for size_range, stats in sorted(size_dist_stats.items()):
            count = stats['count']
            range_total_size = stats['total_size']
            count_percentage = (count / total_count * 100) if total_count > 0 else 0
            size_percentage = (range_total_size / total_size * 100) if total_size > 0 else 0

            if human_readable:
                size_str = format_size(range_total_size, human_readable)
            else:
                size_str = str(range_total_size)

            writer.writerow([size_range, count, f"{count_percentage:.1f}%", size_str, f"{size_percentage:.1f}%"])

    print(f"\n文件大小分布统计结果已导出到: {filename}")


def main():
    # 测试路径
    directory = r"C:\Users\31749\Dorain_file\cos"  # 用于测试的目录，请根据实际情况修改

    # 获取统计信息
    type_stats, size_dist_stats = get_file_type_stats(
        directory_path=directory,
        human_readable=True,
        sort_by='type'
    )

    if type_stats is None:
        return

    # 显示文件类型统计结果
    display_stats(
        type_stats=type_stats,
        human_readable=True,
        sort_by='type'
    )

    # 显示文件大小分布统计结果
    display_size_distribution(
        size_dist_stats=size_dist_stats,
        human_readable=True
    )

    # 可选：导出结果到CSV
    # export_to_csv(type_stats, "file_type_stats.csv")
    # export_size_distribution_to_csv(size_dist_stats, "file_size_distribution.csv")


if __name__ == "__main__":
    main()
