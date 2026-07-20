import os
import shutil
from datetime import datetime


def parse_date(date_str):
    """
    解析日期字符串，支持 YYYY-MM-DD 格式

    Args:
        date_str: 日期字符串

    Returns:
        datetime: 解析后的日期对象，失败返回 None
    """
    date_str = date_str.strip()
    for fmt in ('%Y-%m-%d', '%Y/%m/%d', '%Y.%m.%d'):
        try:
            dt = datetime.strptime(date_str, fmt)
            return dt
        except ValueError:
            continue
    return None


def prompt_date(prompt_text):
    """
    交互式提示用户输入日期，直到输入有效格式

    Args:
        prompt_text: 提示文本

    Returns:
        datetime: 解析后的日期对象
    """
    while True:
        input_str = input(prompt_text).strip()
        if not input_str:
            print("错误: 日期不能为空，请重新输入")
            continue
        dt = parse_date(input_str)
        if dt:
            return dt
        print("错误: 日期格式不正确，请使用 YYYY-MM-DD 格式（例如 2026-01-01）")


def get_mp4_files_in_date_range(source_dir, start_date, end_date):
    """
    递归扫描源目录，筛选创建日期在指定范围内的 mp4 文件

    Args:
        source_dir: 源目录路径
        start_date: 开始日期（包含）
        end_date: 结束日期（包含，当天结束时刻）

    Returns:
        list: 符合条件的文件列表，元素为 (绝对路径, 相对于源目录的路径)
    """
    if not os.path.exists(source_dir):
        print(f"错误: 源目录 '{source_dir}' 不存在")
        return None

    if not os.path.isdir(source_dir):
        print(f"错误: '{source_dir}' 不是目录")
        return None

    source_dir_abs = os.path.abspath(source_dir)
    end_date_end = end_date.replace(hour=23, minute=59, second=59, microsecond=999999)

    matched_files = []
    scanned_count = 0

    print(f"\n正在扫描目录: {source_dir_abs}")
    print(f"日期范围: {start_date.strftime('%Y-%m-%d')} ~ {end_date.strftime('%Y-%m-%d')}")
    print("请稍候...\n")

    for root, dirs, files in os.walk(source_dir_abs):
        for file in files:
            _, ext = os.path.splitext(file)
            if ext.lower() != '.mp4':
                continue

            scanned_count += 1
            file_path = os.path.join(root, file)

            try:
                stat = os.stat(file_path)
                created_at = datetime.fromtimestamp(stat.st_ctime)

                if start_date <= created_at <= end_date_end:
                    rel_path = os.path.relpath(file_path, source_dir_abs)
                    matched_files.append((file_path, rel_path))
            except (OSError, PermissionError) as e:
                print(f"警告: 无法访问文件 {file_path}: {e}")

    print(f"扫描完成：共检查 {scanned_count} 个 mp4 文件")
    print(f"符合日期范围的文件: {len(matched_files)} 个")
    return matched_files


def move_files_with_structure(matched_files, source_dir, output_dir):
    """
    按原目录结构移动文件到输出目录

    Args:
        matched_files: 匹配的文件列表 [(绝对路径, 相对路径), ...]
        source_dir: 源目录（用于显示）
        output_dir: 输出目录

    Returns:
        tuple: (成功数量, 失败数量, 跳过数量)
    """
    output_dir_abs = os.path.abspath(output_dir)
    source_dir_abs = os.path.abspath(source_dir)

    success = 0
    failed = 0
    skipped = 0
    errors = []

    print(f"\n源目录: {source_dir_abs}")
    print(f"输出目录: {output_dir_abs}")
    print(f"待移动文件数: {len(matched_files)}")
    print("\n开始移动文件...\n")

    for idx, (src_path, rel_path) in enumerate(matched_files, 1):
        dst_path = os.path.join(output_dir_abs, rel_path)
        dst_dir = os.path.dirname(dst_path)

        try:
            if not os.path.exists(dst_dir):
                os.makedirs(dst_dir, exist_ok=True)

            if os.path.exists(dst_path):
                print(f"[{idx}/{len(matched_files)}] 跳过(目标已存在): {rel_path}")
                skipped += 1
                continue

            shutil.move(src_path, dst_path)
            print(f"[{idx}/{len(matched_files)}] 移动成功: {rel_path}")
            success += 1

        except Exception as e:
            error_msg = f"{type(e).__name__}: {e}"
            print(f"[{idx}/{len(matched_files)}] 移动失败: {rel_path} -> {error_msg}")
            errors.append((rel_path, error_msg))
            failed += 1

    print("\n" + "=" * 60)
    print("移动完成")
    print("=" * 60)
    print(f"成功: {success} 个")
    print(f"跳过: {skipped} 个 (目标已存在)")
    print(f"失败: {failed} 个")

    if errors:
        print("\n失败详情:")
        for rel_path, err in errors:
            print(f"  - {rel_path}: {err}")

    print("=" * 60)
    return success, failed, skipped


def build_output_dir_name(start_date, end_date):
    """
    根据日期范围生成输出根目录名称

    Args:
        start_date: 开始日期
        end_date: 结束日期

    Returns:
        str: 目录名称，格式 YYYY-MM-DD-YYYY-MM-DD
    """
    return f"{start_date.strftime('%Y-%m-%d')}-{end_date.strftime('%Y-%m-%d')}"


def main():
    print("=" * 60)
    print("MP4 文件按日期范围移动工具")
    print("=" * 60)
    print("说明:")
    print("  筛选源目录下创建日期在指定范围内的 mp4 文件")
    print("  自动以日期范围命名输出根目录（源目录同级）")
    print("  保持原相对目录结构移动\n")

    source_dir = input("请输入源目录路径: ").strip().strip('"')
    if not source_dir:
        print("错误: 源目录不能为空")
        return

    source_dir_abs = os.path.abspath(source_dir)
    if not os.path.exists(source_dir_abs) or not os.path.isdir(source_dir_abs):
        print(f"错误: 源目录 '{source_dir_abs}' 不存在或不是目录")
        return

    print("\n--- 设置日期范围 ---")
    print("(格式: YYYY-MM-DD，例如 2026-01-01)")
    start_date = prompt_date("请输入开始日期: ")
    end_date = prompt_date("请输入结束日期: ")

    if start_date > end_date:
        print("错误: 开始日期不能晚于结束日期")
        return

    output_dir_name = build_output_dir_name(start_date, end_date)
    source_parent = os.path.dirname(source_dir_abs)
    output_dir = os.path.join(source_parent, output_dir_name)
    print(f"\n输出目录: {output_dir}")

    matched_files = get_mp4_files_in_date_range(source_dir_abs, start_date, end_date)

    if matched_files is None:
        return

    if len(matched_files) == 0:
        print("没有符合日期范围的 mp4 文件")
        return

    print("\n即将移动以下文件:")
    print("-" * 80)
    print(f"{'创建日期':<12} {'源相对路径':<35} {'目标路径'}")
    print("-" * 80)
    for src_path, rel_path in matched_files[:10]:
        stat = os.stat(src_path)
        created_at = datetime.fromtimestamp(stat.st_ctime)
        target_rel = f"{output_dir_name}{os.sep}{rel_path}"
        print(f"  {created_at.strftime('%Y-%m-%d'):<10} {rel_path:<35} -> {target_rel}")
    if len(matched_files) > 10:
        print(f"  ... 还有 {len(matched_files) - 10} 个文件未显示")
    print("-" * 80)

    while True:
        choice = input("\n确认开始移动？(y/n): ").strip().lower()
        if choice in ('y', 'yes'):
            break
        elif choice in ('n', 'no'):
            print("已取消操作")
            return
        else:
            print("请输入 y 或 n")

    move_files_with_structure(matched_files, source_dir_abs, output_dir)


if __name__ == "__main__":
    main()
