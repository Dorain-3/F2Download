"""
批量视频压缩工具 - 使用NVIDIA GPU加速压缩

功能说明:
    本脚本提供批量视频压缩功能，输入视频文件夹路径，自动扫描并压缩码率大于指定阈值的视频文件。
    复用video_compressor模块的compress_video方法进行压缩处理。

过滤条件:
    - 视频码率 > 4Mbps（可配置）
    - 支持的视频格式: .mp4, .mkv, .avi, .mov, .flv, .wmv

使用方式:
    直接运行本脚本，按提示选择压缩方案、设置目标码率和码率阈值，然后输入视频文件夹路径。

处理流程:
    1. 选择压缩方案（H.265或AV1）
    2. 设置目标压缩码率（默认2Mbps）
    3. 设置码率过滤阈值（默认4Mbps）
    4. 输入视频文件夹路径
    5. 扫描文件夹，获取所有支持的视频文件
    6. 过滤码率大于阈值的文件
    7. 逐个调用compress_video方法进行压缩
    8. 输出批量处理统计报告

依赖模块:
    - video_compressor: 提供核心压缩功能和辅助函数
    - os: 文件系统操作
    - sys: 系统路径和退出操作
"""

# 导入标准库模块
import os
import sys

# 将当前脚本所在目录添加到模块搜索路径最前面
# 确保可以正确导入同一目录下的video_compressor模块
# 解析过程:
#   __file__           -> 当前脚本文件名，如 'batch_video_compressor.py'
#   os.path.abspath()  -> 转换为绝对路径，如 'C:\Users\...\tool\batch_video_compressor.py'
#   os.path.dirname()  -> 获取父目录，如 'C:\Users\...\tool\'
#   sys.path.insert(0) -> 插入到搜索路径列表最前面，优先搜索此目录
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 从video_compressor模块导入所需的功能
# - CODECS: 压缩方案配置字典（H.265和AV1）
# - TARGET_BITRATE: 默认目标码率（'2M'）
# - compress_video: 核心压缩函数
# - select_codec: 交互式选择压缩方案
# - set_target_bitrate: 交互式设置目标码率
# - get_video_bitrate: 获取视频文件码率
# - parse_bitrate: 解析码率字符串为数值
from video.video_compressor import (
    TARGET_BITRATE,
    compress_video, select_codec, get_video_bitrate, parse_bitrate
)

# 默认码率过滤阈值，码率大于此值的视频才会被压缩
MIN_BITRATE_THRESHOLD = '4M'

# 支持的视频文件扩展名列表
# 只有扩展名在列表中的文件才会被识别为视频文件
SUPPORTED_EXTENSIONS = ('.mp4', '.mkv', '.avi', '.mov', '.flv', '.wmv')


# 已压缩视频的后缀标记，包含这些标记的文件将被跳过
COMPRESSED_SUFFIXES = ('_H265', '_av1')


def get_video_files(folder_path):
    """
    获取文件夹中所有支持的视频文件
    
    遍历指定文件夹，筛选出扩展名在SUPPORTED_EXTENSIONS中的文件，
    并验证文件是否为普通文件（非目录）。同时过滤掉已压缩的视频文件
    （文件名中包含_H265或_av1的文件）。
    
    Args:
        folder_path: 文件夹路径（字符串）
        
    Returns:
        list: 视频文件路径列表，每个元素为文件的绝对路径或相对路径
    """
    video_files = []
    skipped_count = 0

    # 检查输入路径是否为有效目录
    if not os.path.isdir(folder_path):
        return video_files

    # 遍历文件夹中的所有文件和目录
    for filename in os.listdir(folder_path):
        # 获取文件扩展名并转换为小写
        ext = os.path.splitext(filename)[1].lower()
        # 判断扩展名是否在支持的列表中
        if ext in SUPPORTED_EXTENSIONS:
            # 检查文件名是否包含已压缩标记（_H265或_av1）
            if any(suffix in filename for suffix in COMPRESSED_SUFFIXES):
                # 跳过已压缩的文件，记录跳过数量
                skipped_count += 1
                continue
            # 拼接完整文件路径
            file_path = os.path.join(folder_path, filename)
            # 确保是普通文件而非目录
            if os.path.isfile(file_path):
                video_files.append(file_path)

    # 如果有被跳过的文件，打印提示信息
    if skipped_count > 0:
        print(f"ℹ️ 已跳过 {skipped_count} 个已压缩的视频文件（文件名包含_H265或_av1）")

    return video_files


def filter_by_bitrate(video_files, min_bitrate_bps):
    """
    过滤码率大于指定阈值的视频文件
    
    遍历视频文件列表，使用get_video_bitrate获取每个文件的视频流码率，
    只保留码率大于min_bitrate_bps的文件。同时打印每个文件的处理状态。
    
    Args:
        video_files: 视频文件路径列表
        min_bitrate_bps: 最小码率阈值（单位：bps，整数）
        
    Returns:
        list: 过滤后的视频文件列表，每个元素为字典，包含'path'和'bitrate'键
    """
    filtered = []

    # 打印扫描提示信息，显示当前的码率阈值
    print(f"\n🔍 正在扫描视频文件，过滤码率 > {min_bitrate_bps // 1000} kbps 的文件...\n")

    # 遍历所有视频文件
    for file_path in video_files:
        try:
            # 获取视频文件的码率（单位：bps）
            bitrate_bps = get_video_bitrate(file_path)

            # 判断码率是否大于阈值
            if bitrate_bps > min_bitrate_bps:
                # 将符合条件的文件添加到过滤列表中
                filtered.append({
                    'path': file_path,
                    'bitrate': bitrate_bps
                })
                # 打印符合条件的文件信息
                print(f"✅ {os.path.basename(file_path)} - {bitrate_bps // 1000} kbps")
            else:
                # 打印跳过的文件信息（码率低于阈值）
                print(f"⏭️ {os.path.basename(file_path)} - {bitrate_bps // 1000} kbps（码率低于阈值，跳过）")

        except Exception as e:
            # 处理获取码率失败的情况
            print(f"❌ {os.path.basename(file_path)} - 获取码率失败: {e}")

    return filtered


def set_bitrate_threshold():
    """
    设置码率过滤阈值
    
    提供交互式界面让用户输入码率阈值，支持多种格式（如 '2M', '1500k', '500000'）。
    如果用户输入为空，则返回默认值MIN_BITRATE_THRESHOLD。
    
    Returns:
        str: 用户设置的码率阈值字符串，如 '4M', '2000k'
    """
    while True:
        # 提示用户输入码率阈值，显示默认值
        user_input = input(f"请输入最小码率阈值（默认: {MIN_BITRATE_THRESHOLD}）: ").strip()
        # 如果用户输入为空，返回默认值
        if not user_input:
            return MIN_BITRATE_THRESHOLD

        try:
            # 尝试解析用户输入的码率字符串
            if parse_bitrate(user_input) > 0:
                # 解析成功，返回用户输入的值
                return user_input
            else:
                # 解析失败，提示用户输入有效的码率格式
                print("❌ 无效的码率格式，请使用如 '2M', '1500k', '500000' 等格式")
        except:
            # 捕获异常，提示用户输入有效的码率格式
            print("❌ 无效的码率格式，请使用如 '2M', '1500k', '500000' 等格式")


def set_auto_delete():
    """
    设置是否自动删除原始视频文件
    
    提供交互式界面让用户选择是否在压缩完成且验证通过后自动删除原视频。
    
    Returns:
        bool: True表示自动删除，False表示需要用户确认
    """
    while True:
        choice = input("压缩完成后是否自动删除原始视频文件？(y/n): ").strip().lower()
        if choice in ('y', 'yes'):
            print("⚠️ 已开启自动删除模式，压缩验证通过后将自动删除原视频")
            return True
        elif choice in ('n', 'no'):
            print("✓ 保留原始视频文件，需手动确认删除")
            return False
        else:
            print("❌ 无效选项，请输入 y 或 n")


def process_batch(batch_files, total_count, start_idx, codec_key, target_bitrate, auto_delete):
    """
    处理一批视频文件
    
    Args:
        batch_files: 当前批次的视频文件列表
        total_count: 总文件数量
        start_idx: 当前批次的起始索引（从1开始）
        codec_key: 压缩方案键值
        target_bitrate: 目标视频码率
        auto_delete: 是否自动删除原视频
        
    Returns:
        tuple: (success_count, fail_count) 成功和失败的数量
    """
    success_count = 0
    fail_count = 0

    for i, file_info in enumerate(batch_files, start_idx):
        # 获取文件路径和码率信息
        file_path = file_info['path']
        bitrate = file_info['bitrate']

        # 打印当前处理进度和文件信息
        print(f"\n📦 [{i}/{total_count}] 开始处理: {os.path.basename(file_path)}")
        print(f"   📊 源码率: {bitrate // 1000} kbps")

        try:
            # 调用compress_video函数进行压缩，传入auto_delete参数
            compress_video(file_path, codec_key, target_bitrate, auto_delete)
            # 压缩成功，增加成功计数
            success_count += 1
        except Exception as e:
            # 压缩失败，增加失败计数并打印错误信息
            print(f"❌ 处理失败: {e}")
            fail_count += 1

        # 打印分隔线，区分不同文件的处理信息
        print("-" * 80)

    return success_count, fail_count


def ask_continue(processed_count, total_count):
    """
    询问用户是否继续处理剩余文件
    
    Args:
        processed_count: 已处理的文件数量
        total_count: 总文件数量
        
    Returns:
        bool: True表示继续处理，False表示退出
    """
    remaining = total_count - processed_count

    if remaining <= 0:
        return False

    print(f"\n📊 当前已处理 {processed_count}/{total_count} 个文件，还剩 {remaining} 个文件")

    while True:
        choice = input("是否继续处理下一批？(y/n): ").strip().lower()
        if choice in ('y', 'yes'):
            return True
        elif choice in ('n', 'no'):
            return False
        else:
            print("❌ 无效选项，请输入 y 或 n")


def batch_compress(folder_path, codec_key, target_bitrate, bitrate_threshold, auto_delete=False):
    """
    批量压缩视频文件
    
    主函数，负责协调批量压缩的整个流程：
    1. 获取文件夹中的视频文件
    2. 根据码率阈值过滤文件
    3. 按码率从大到小排序并显示前20个
    4. 分批处理视频（每批20个），处理完一批后询问用户是否继续
    5. 统计并输出处理结果
    
    Args:
        folder_path: 视频文件夹路径（字符串）
        codec_key: 压缩方案键值（'1'表示H.265，'2'表示AV1）
        target_bitrate: 目标视频码率（字符串，如 '2M', '1500k'）
        bitrate_threshold: 码率过滤阈值（字符串，如 '4M', '2000k'）
        auto_delete: 是否自动删除原视频（默认False）
    """
    # 步骤1: 获取文件夹中的所有视频文件
    video_files = get_video_files(folder_path)

    # 如果没有找到任何视频文件，提示用户并返回
    if not video_files:
        print("❌ 未找到任何支持的视频文件")
        return

    # 步骤2: 解析码率阈值并过滤视频文件
    # 将码率阈值字符串转换为数值（单位：bps）
    min_bitrate_bps = parse_bitrate(bitrate_threshold)
    # 根据码率阈值过滤视频文件
    filtered_files = filter_by_bitrate(video_files, min_bitrate_bps)

    # 如果没有符合条件的视频文件，提示用户并返回
    if not filtered_files:
        print(f"\n❌ 没有码率大于 {min_bitrate_bps // 1000} kbps 的视频文件")
        return

    # 步骤3: 对过滤后的视频文件按码率从大到小排序
    # 使用sort方法，key参数指定按bitrate字段排序，reverse=True表示降序
    filtered_files.sort(key=lambda x: x['bitrate'], reverse=True)

    # 步骤4: 显示符合条件的文件数量和排序后的前20个结果
    total_count = len(filtered_files)


    print(f"\n📋 共找到 {total_count} 个符合条件的视频文件")
    print("=" * 80)

    # 打印排序后的前20个文件信息
    print("📊 按码率从大到小排序（前20个）:")
    print("-" * 80)
    print(f"{'序号':<6} {'文件名':<50} {'码率(kbps)':<12}")
    print("-" * 80)

    for i, file_info in enumerate(filtered_files[:20], 1):
        filename = os.path.basename(file_info['path'])
        # 文件名过长时进行截断，保持格式整齐
        if len(filename) > 48:
            filename = filename[:45] + "..."
        print(f"{i:<6} {filename:<50} {file_info['bitrate'] // 1000:<12}")

    print("=" * 80)

    # 步骤5: 分批处理视频文件（每批20个）
    BATCH_SIZE = 20
    current_idx = 0
    total_success = 0
    total_fail = 0

    while current_idx < total_count:
        # 计算当前批次的起止索引
        batch_start = current_idx
        batch_end = min(current_idx + BATCH_SIZE, total_count)
        batch_files = filtered_files[batch_start:batch_end]

        # 显示当前批次信息
        print(
            f"\n🎯 开始处理第 {batch_start // BATCH_SIZE + 1} 批（共 {(total_count + BATCH_SIZE - 1) // BATCH_SIZE} 批）")
        print(f"   文件范围: {batch_start + 1} - {batch_end}")
        print("-" * 80)

        # 处理当前批次
        success, fail = process_batch(
            batch_files,
            total_count,
            batch_start + 1,
            codec_key,
            target_bitrate,
            auto_delete
        )

        total_success += success
        total_fail += fail

        # 更新当前索引
        current_idx = batch_end

        # 询问用户是否继续处理下一批
        if not ask_continue(current_idx, total_count):
            print("\n⏹️ 用户选择退出，停止处理")
            break

    # 步骤6: 输出批量处理统计报告
    print("\n" + "=" * 80)
    print(f"📊 批量压缩完成！")
    print(f"✅ 成功: {total_success} 个")
    print(f"❌ 失败: {total_fail} 个")
    print(f"⏭️ 未处理: {total_count - total_success - total_fail} 个")
    print("=" * 80)


if __name__ == "__main__":
    """
    程序入口
    
    提供交互式界面，引导用户完成批量压缩的参数设置，
    然后调用batch_compress函数执行批量压缩任务。
    """
    # 打印程序标题
    print("=" * 60)
    print("      批量视频压缩工具")
    print("=" * 60)

    # 步骤1: 选择压缩方案（H.265或AV1）
    codec_key = select_codec()

    # 步骤2: 设置目标码率（默认2Mbps）
    target_bitrate = TARGET_BITRATE

    # 步骤3: 设置码率过滤阈值（默认4Mbps）
    bitrate_threshold = MIN_BITRATE_THRESHOLD

    # 步骤4: 设置是否自动删除原视频
    auto_delete = set_auto_delete()

    # 步骤5: 获取视频文件夹路径
    folder_path = input("请输入视频文件夹路径: ").strip('"')

    # 检查文件夹路径是否有效
    if not os.path.isdir(folder_path):
        print(f"❌ 文件夹路径不存在: {folder_path}")
        sys.exit(1)

    # 步骤6: 执行批量压缩任务
    batch_compress(folder_path, codec_key, target_bitrate, bitrate_threshold, auto_delete)
