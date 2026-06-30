import os
import argparse
from pathlib import Path
from PIL import Image
from concurrent.futures import ProcessPoolExecutor, as_completed
import time
import sys


def compress_image(input_path, quality_strategy=None):
    """
    压缩单张图片并覆盖原文件

    参数:
        input_path: 输入图片路径
        quality_strategy: 压缩策略字典
    """
    # 检查文件是否存在
    if not os.path.exists(input_path):
        return False, input_path, "文件不存在", None

    # 检查压缩策略
    if quality_strategy is None:
        quality_strategy = {
            'level_breaks': [1000 * 1024, 2000 * 1024, 5000 * 1024, 10000 * 1024],  # 500KB, 2MB, 5MB , 10MB
            'level_quality': [None, 95, 90, 80, 65]  # None表示不压缩
        }

    # 根据原图大小确定本次压缩使用的质量（quality）
    try:
        file_size = os.path.getsize(input_path)

        # 修复逻辑错误：为大于等于最大分界点的文件设置最后一个质量等级
        chosen_quality = quality_strategy['level_quality'][-1]  # 默认取最后一个等级

        for i, break_point in enumerate(quality_strategy['level_breaks']):
            if file_size < break_point:
                chosen_quality = quality_strategy['level_quality'][i]
                break

    except Exception as e:
        print(f"警告: 无法获取文件大小 {input_path}，使用默认质量85。错误: {e}")
        chosen_quality = 85
        file_size = 0  # 设置默认值

    # 如果质量参数为None，表示不压缩
    if chosen_quality is None:
        return True, input_path, input_path, "未压缩（文件较小）"

    try:
        # 打开图片
        with Image.open(input_path) as img:
            # 转换为RGB模式（处理RGBA等模式）
            if img.mode in ('RGBA', 'LA', 'P'):
                # 如果有alpha通道，先创建一个白色背景
                background = Image.new('RGB', img.size, (255, 255, 255))
                if img.mode == 'P':
                    img = img.convert('RGBA')
                background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                img = background
            elif img.mode != 'RGB':
                img = img.convert('RGB')

            # 获取原文件信息
            original_size = file_size
            original_format = img.format

            # 创建临时文件路径
            temp_path = input_path + ".tmp"

            # 保存压缩后的图片到临时文件
            # 统一保存为JPEG格式
            img.save(temp_path, 'JPEG', quality=chosen_quality, optimize=True)

            # 获取压缩后文件大小
            compressed_size = os.path.getsize(temp_path)

            # 压缩率计算
            compression_ratio = 0
            if original_size > 0:
                compression_ratio = (1 - compressed_size / original_size) * 100

            # 用临时文件替换原文件
            os.replace(temp_path, input_path)

            detail = (f"原始大小: {original_size // 1024}KB, "
                      f"压缩后: {compressed_size // 1024}KB, "
                      f"压缩率: {compression_ratio:.1f}%, "
                      f"质量: {chosen_quality}")

            return True, input_path, input_path, detail

    except Exception as e:
        return False, input_path, str(e), None
    finally:
        # 清理临时文件（如果存在）
        temp_path = input_path + ".tmp"
        if os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except:
                pass


def process_images_parallel(input_dir, quality_strategy=None, max_workers=None):
    """
    并行处理图片压缩并覆盖原文件

    参数:
        input_dir: 输入目录
        quality_strategy: 压缩策略字典
        max_workers: 最大工作进程数
    """
    # 支持的图片格式
    supported_formats = ('.jpg', '.jpeg', '.png', '.JPG', '.JPEG', '.PNG')

    # 收集所有图片文件
    input_dir_path = Path(input_dir)
    image_files = []

    for file_path in input_dir_path.rglob('*'):
        if file_path.suffix.lower() in supported_formats and file_path.is_file():
            image_files.append(str(file_path))

    if not image_files:
        print(f"在目录 {input_dir} 中未找到支持的图片文件")
        return

    print(f"找到 {len(image_files)} 张待处理的图片")

    # 显示当前压缩策略
    if quality_strategy:
        print("当前压缩策略:")
        print("  文件大小范围         -> 压缩质量")

        breaks = quality_strategy['level_breaks']
        qualities = quality_strategy['level_quality']

        # 显示每个等级的范围
        for i in range(len(breaks)):
            if i == 0:
                range_str = f"< {breaks[0] // 1024}KB"
            else:
                range_str = f"{breaks[i - 1] // 1024}KB - {breaks[i] // 1024}KB"

            quality_str = "不压缩" if qualities[i] is None else f"{qualities[i]}"
            print(f"  {range_str:15} -> {quality_str}")

        # 最后一个等级
        last_range = f">= {breaks[-1] // 1024}KB"
        last_quality = "不压缩" if qualities[-1] is None else f"{qualities[-1]}"
        print(f"  {last_range:15} -> {last_quality}")
    print("-" * 50)

    # 使用ProcessPoolExecutor进行并行处理
    start_time = time.time()
    success_count = 0
    fail_count = 0
    total_original_size = 0
    total_compressed_size = 0

    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        # 提交所有任务
        future_to_path = {}
        for img_path in image_files:
            future = executor.submit(compress_image, img_path, quality_strategy)
            future_to_path[future] = img_path

        # 处理结果
        try:
            # 尝试导入tqdm显示进度条（可选）
            try:
                from tqdm import tqdm
                progress_bar = tqdm(total=len(image_files), desc="压缩进度")
                use_tqdm = True
            except ImportError:
                print("提示: 安装 'tqdm' 包可以显示进度条: pip install tqdm")
                progress_bar = None
                use_tqdm = False

            for future in as_completed(future_to_path):
                success, input_path, result, detail = future.result()

                if success:
                    success_count += 1
                    # 从详情信息中提取大小信息
                    if detail and "原始大小:" in detail and "压缩后:" in detail:
                        try:
                            # 解析详情字符串中的大小信息
                            parts = detail.split(",")
                            for part in parts:
                                if "原始大小:" in part:
                                    original_kb = int(part.split(":")[1].replace("KB", "").strip())
                                    total_original_size += original_kb * 1024
                                elif "压缩后:" in part:
                                    compressed_kb = int(part.split(":")[1].replace("KB", "").strip())
                                    total_compressed_size += compressed_kb * 1024
                        except:
                            pass

                    if use_tqdm:
                        progress_bar.set_postfix_str(f"成功: {success_count}")
                    if detail:
                        print(f"处理成功: {os.path.basename(input_path)} -> {detail}")
                else:
                    fail_count += 1
                    print(f"处理失败: {input_path}")
                    print(f"错误: {result}")

                if use_tqdm:
                    progress_bar.update(1)

            if use_tqdm:
                progress_bar.close()

        except KeyboardInterrupt:
            print("\n用户中断，正在停止...")
            executor.shutdown(wait=False, cancel_futures=True)
            raise

    elapsed_time = time.time() - start_time

    print(f"\n处理完成!")
    print(f"成功: {success_count} 张")
    print(f"失败: {fail_count} 张")

    # 计算总体压缩效果
    if total_original_size > 0 and total_compressed_size > 0:
        total_saved = total_original_size - total_compressed_size
        total_ratio = (total_saved / total_original_size) * 100 if total_original_size > 0 else 0
        print(f"原始总大小: {total_original_size // 1024}KB")
        print(f"压缩后总大小: {total_compressed_size // 1024}KB")
        print(f"节省空间: {total_saved // 1024}KB ({total_ratio:.1f}%)")

    print(f"总耗时: {elapsed_time:.2f} 秒")
    if success_count > 0:
        print(f"平均每张: {elapsed_time / success_count:.2f} 秒")


def main():
    """主函数，处理命令行参数"""
    parser = argparse.ArgumentParser(description='批量并行图片压缩工具（覆盖原文件）')
    parser.add_argument('input_dir', help='输入图片目录（将直接压缩并覆盖原文件）')
    parser.add_argument('-w', '--workers', type=int, default=8,
                        help='工作进程数 (默认使用CPU核心数，推荐设置)')

    args = parser.parse_args()

    # 验证输入目录是否存在
    if not os.path.exists(args.input_dir):
        print(f"错误: 输入目录 '{args.input_dir}' 不存在")
        return

    quality_strategy = {
        'level_breaks': [5000 * 1024, 10000 * 1024, 20000 * 1024, 40000 * 1024],  # 500KB, 2MB, 5MB , 10MB
        'level_quality': [None, 60, 50, 40, 30]  # None表示不压缩
    }

    print(f"输入目录: {args.input_dir}")
    print(f"工作进程: {args.workers or '自动（CPU核心数）'}")

    print("-" * 50)
    print("警告: 此操作将直接覆盖原文件！请确保已备份重要文件。")
    print("-" * 50)

    # 确认操作
    confirm = input("确定要继续吗？(y/N): ")
    if confirm.lower() != 'y':
        print("操作已取消")
        return

    process_images_parallel(args.input_dir, quality_strategy, args.workers)


if __name__ == "__main__":
    main()
