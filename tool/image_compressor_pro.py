import os
import argparse
from pathlib import Path
from PIL import Image, ImageFile
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

ImageFile.LOAD_TRUNCATED_IMAGES = True


def estimate_compression_quality(file_size):
    """根据文件大小智能估算压缩质量"""
    quality_strategy = {
        'level_breaks': [1000 * 1024, 3000 * 1024, 10000 * 1024, 20000 * 1024],
        'level_quality': [None, 75, 60, 50, 40]
    }

    chosen_quality = quality_strategy['level_quality'][-1]
    for i, break_point in enumerate(quality_strategy['level_breaks']):
        if file_size < break_point:
            chosen_quality = quality_strategy['level_quality'][i]
            break

    return chosen_quality


def compress_image(input_path, output_format='JPEG', max_retries=2):
    """压缩单张图片并覆盖原文件"""
    if not os.path.exists(input_path):
        return False, input_path, "文件不存在", None, None, None

    for attempt in range(max_retries + 1):
        try:
            with Image.open(input_path) as img:
                original_size = os.path.getsize(input_path)
                original_width, original_height = img.size

                if img.mode in ('RGBA', 'LA', 'P'):
                    background = Image.new('RGB', img.size, (255, 255, 255))
                    if img.mode == 'P':
                        img = img.convert('RGBA')
                    background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                    img = background
                elif img.mode != 'RGB':
                    img = img.convert('RGB')

                scale_ratio = 1.0
                if original_size > 20 * 1024 * 1024:
                    scale_ratio = 0.25
                elif original_size >= 10 * 1024 * 1024:
                    scale_ratio = 0.5

                if scale_ratio < 1.0:
                    new_width = int(original_width * scale_ratio)
                    new_height = int(original_height * scale_ratio)
                    img = img.resize((new_width, new_height), Image.LANCZOS)
                    width, height = new_width, new_height
                else:
                    width, height = original_width, original_height

                quality = estimate_compression_quality(original_size)

                if quality is None:
                    return True, input_path, input_path, "未压缩（文件较小）", original_size, original_size

                temp_path = input_path + ".tmp"
                img.save(temp_path, output_format, quality=quality, optimize=True)

                compressed_size = os.path.getsize(temp_path)

                os.replace(temp_path, input_path)

                compression_ratio = (1 - compressed_size / original_size) * 100 if original_size > 0 else 0

                resolution_info = f"{original_width}x{original_height}"
                if scale_ratio < 1.0:
                    resolution_info += f" -> {width}x{height}"

                detail = (f"原始: {original_size // 1024}KB, "
                          f"压缩后: {compressed_size // 1024}KB, "
                          f"压缩率: {compression_ratio:.1f}%, "
                          f"质量: {quality}, "
                          f"分辨率: {resolution_info}")

                return True, input_path, input_path, detail, original_size, compressed_size

        except Exception as e:
            temp_path = input_path + ".tmp"
            if os.path.exists(temp_path):
                os.remove(temp_path)

            if attempt < max_retries:
                continue
            else:
                return False, input_path, str(e), None, None, None


def process_images_parallel(input_dir, output_format='JPEG', max_workers=None, show_progress=True):
    """并行处理图片压缩并覆盖原文件"""
    supported_formats = ('.jpg', '.jpeg', '.png', '.JPG', '.JPEG', '.PNG')

    input_dir_path = Path(input_dir)
    image_files = []

    for file_path in input_dir_path.rglob('*'):
        if file_path.suffix.lower() in supported_formats and file_path.is_file():
            image_files.append(str(file_path))

    if not image_files:
        print(f"在目录 {input_dir} 中未找到支持的图片文件")
        return

    print(f"找到 {len(image_files)} 张待处理的图片")
    print(f"输出格式: {output_format}")
    print("-" * 60)

    start_time = time.time()
    success_count = 0
    fail_count = 0
    total_original_size = 0
    total_compressed_size = 0

    progress_bar = None
    use_tqdm = False

    if show_progress:
        try:
            from tqdm import tqdm
            progress_bar = tqdm(total=len(image_files), desc="压缩进度")
            use_tqdm = True
        except ImportError:
            pass

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_path = {}

        for img_path in image_files:
            future = executor.submit(compress_image, img_path, output_format)
            future_to_path[future] = img_path

        try:
            for future in as_completed(future_to_path):
                success, input_path, result, detail, orig_size, comp_size = future.result()

                if success:
                    success_count += 1
                    if orig_size:
                        total_original_size += orig_size
                    if comp_size:
                        total_compressed_size += comp_size

                    if use_tqdm:
                        progress_bar.set_postfix_str(f"成功: {success_count}")
                    if detail:
                        print(f"✓ {os.path.basename(input_path)} -> {detail}")
                else:
                    fail_count += 1
                    print(f"✗ 失败: {os.path.basename(input_path)}")
                    print(f"  错误: {result}")

                if use_tqdm:
                    progress_bar.update(1)

            if use_tqdm:
                progress_bar.close()

        except KeyboardInterrupt:
            print("\n用户中断，正在停止...")
            executor.shutdown(wait=False, cancel_futures=True)
            raise

    elapsed_time = time.time() - start_time

    print("\n" + "-" * 60)
    print(f"处理完成!")
    print(f"成功: {success_count} 张")
    print(f"失败: {fail_count} 张")

    if total_original_size > 0:
        total_saved = total_original_size - total_compressed_size
        total_ratio = (total_saved / total_original_size) * 100 if total_original_size > 0 else 0
        print(f"原始总大小: {total_original_size // 1024}KB ({total_original_size / (1024 * 1024):.2f}MB)")
        print(f"压缩后总大小: {total_compressed_size // 1024}KB ({total_compressed_size / (1024 * 1024):.2f}MB)")
        print(f"节省空间: {total_saved // 1024}KB ({total_ratio:.1f}%)")

    print(f"总耗时: {elapsed_time:.2f} 秒")
    if success_count > 0:
        print(f"平均每张: {elapsed_time / success_count:.2f} 秒")


def main():
    parser = argparse.ArgumentParser(description='批量并行图片压缩工具（增强版）')
    parser.add_argument('input_dir', help='输入图片目录（将直接压缩并覆盖原文件）')
    parser.add_argument('-f', '--format', choices=['JPEG', 'WEBP'],
                        default='JPEG', help='输出格式 (默认: JPEG)')
    parser.add_argument('-w', '--workers', type=int, default=None,
                        help='工作线程数 (默认: CPU核心数)')

    args = parser.parse_args()

    if not os.path.exists(args.input_dir):
        print(f"错误: 输入目录 '{args.input_dir}' 不存在")
        return

    print(f"输入目录: {args.input_dir}")
    print(f"输出格式: {args.format}")
    print(f"工作线程: {args.workers or '自动'}")
    print("-" * 60)
    print("警告: 此操作将直接覆盖原文件！请确保已备份重要文件。")
    print("-" * 60)

    confirm = input("确定要继续吗？(y/N): ")
    if confirm.lower() != 'y':
        print("操作已取消")
        return

    process_images_parallel(args.input_dir, args.format, args.workers)


if __name__ == "__main__":
    main()
