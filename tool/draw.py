import json
import matplotlib.pyplot as plt
from datetime import datetime
import matplotlib.font_manager as fm

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'Arial Unicode MS']
plt.rcParams['axes.unicode_minus'] = False

def analyze_date_distribution(json_data):
    """
    分析日期分布并区分is_update的值
    """
    # 提取数据
    update_1_dates = []
    update_0_dates = []

    for item in json_data["json_list"]:
        if item["is_update"] == "1":
            update_1_dates.append(item["old_date"])
        else:
            update_0_dates.append(item["old_date"])

    # 统计is_update=1的日期分布
    date_count_update_1 = {}
    for date in update_1_dates:
        date_count_update_1[date] = date_count_update_1.get(date, 0) + 1

    # 按日期排序
    sorted_dates_update_1 = sorted(date_count_update_1.items(), key=lambda x: datetime.strptime(x[0], "%Y-%m-%d"))

    # 分离日期和数量
    dates_update_1 = [item[0] for item in sorted_dates_update_1]
    counts_update_1 = [item[1] for item in sorted_dates_update_1]

    # 统计is_update=0的总数
    update_0_count = len(update_0_dates)

    return dates_update_1, counts_update_1, date_count_update_1, update_0_count

def plot_date_distribution(dates_update_1, counts_update_1, update_0_count, total_count):
    """
    绘制日期分布统计图（包含is_update统计维度）
    """
    fig, ax = plt.subplots(1, 1, figsize=(15, 8))

    # 柱状图 - 显示is_update=1的数据
    bars = ax.bar(dates_update_1, counts_update_1, color='skyblue', edgecolor='black', alpha=0.7, label='is_update=1')
    ax.set_title(f'抖音用户数据按日期分布统计 (总计: {total_count}个)', fontsize=16, fontweight='bold')
    ax.set_xlabel('日期', fontsize=12)
    ax.set_ylabel('数量', fontsize=12)
    ax.tick_params(axis='x', rotation=45)

    # 在柱子上显示数量
    for bar, count in zip(bars, counts_update_1):
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height + 0.1,
                 f'{count}', ha='center', va='bottom', fontsize=10)

    # 添加is_update=0的统计信息到图例
    if update_0_count > 0:
        ax.bar([0], [0], color='orange', alpha=0.7, label=f'is_update=0 ({update_0_count}个)')
    
    # 添加图例
    ax.legend(loc='upper right')

    # 添加统计信息文本框
    stats_text = f"总计: {total_count}个\nis_update=1: {sum(counts_update_1)}个\nis_update=0: {update_0_count}个"
    ax.text(0.02, 0.98, stats_text, transform=ax.transAxes, fontsize=12,
            verticalalignment='top', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))

    plt.tight_layout()
    plt.show()

    return fig

def print_statistics(date_count_update_1, update_0_count, total_count):
    """
    打印统计信息
    """
    print("=" * 60)
    print("日期分布统计结果:")
    print("=" * 60)

    # 按数量排序
    sorted_by_count = sorted(date_count_update_1.items(), key=lambda x: x[1], reverse=True)

    print("is_update=1的数据:")
    for date, count in sorted_by_count:
        percentage = (count / total_count) * 100
        print(f"  {date}: {count}个 ({percentage:.1f}%)")

    print(f"is_update=0的数据: {update_0_count}个 ({(update_0_count/total_count)*100:.1f}%)")

    print("=" * 60)
    print(f"总计: {total_count}个用户配置")
    print(f"is_update=1: {sum(date_count_update_1.values())}个")
    print(f"is_update=0: {update_0_count}个")

    # 统计信息
    if date_count_update_1:
        avg_per_day = sum(date_count_update_1.values()) / len(date_count_update_1)
        max_count = max(date_count_update_1.values())
        max_date = [date for date, count in date_count_update_1.items() if count == max_count][0]

        print(f"平均每天(is_update=1): {avg_per_day:.1f}个")
        print(f"最多配置的日期: {max_date} ({max_count}个)")

# 主程序
# 主程序 - 从文件读取版本
if __name__ == "__main__":
    # 从文件读取JSON数据
    file_path = r"D:\Settings\TikTok\video\right_urls.json"  # 请替换为实际文件路径

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            json_data = json.load(f)

        # 分析数据
        dates_update_1, counts_update_1, date_count_update_1, update_0_count = analyze_date_distribution(json_data)
        total_count = sum(counts_update_1) + update_0_count

        # 打印统计信息
        print_statistics(date_count_update_1, update_0_count, total_count)

        # 绘制图表
        plot_date_distribution(dates_update_1, counts_update_1, update_0_count, total_count)

    except FileNotFoundError:
        print(f"错误: 文件 {file_path} 未找到")
    except json.JSONDecodeError:
        print("错误: JSON文件格式不正确")
    except Exception as e:
        print(f"发生错误: {e}")