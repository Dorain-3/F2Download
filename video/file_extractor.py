"""
视频提取工具 - 修改版

功能说明:
    本脚本用于遍历指定文件夹路径下的所有子文件夹，根据用户输入的文件后缀，
    提取所有匹配该后缀的文件到输入路径/output目录下。

使用方式:
    直接运行本脚本，按提示输入文件夹路径和文件后缀即可

注意事项:
    1. 输入后缀时不需加点，如输入 mp4 而非 .mp4
    2. 移动操作不可逆，请谨慎使用
    3. 如果目标文件已存在，会自动添加数字后缀（如 filename_1.mp4）
    4. 遇到权限问题时会自动跳过并提示
"""

import os
import shutil


def normalize_extension(ext):
    """
    标准化文件后缀，确保以.开头且为小写

    Args:
        ext: 用户输入的文件后缀

    Returns:
        str: 标准化后的文件后缀（如 ".mp4"）
    """
    ext = ext.strip().lower()
    if not ext.startswith('.'):
        ext = '.' + ext
    return ext


def get_target_files(folder_path, target_ext):
    """
    获取文件夹中所有指定后缀的文件

    Args:
        folder_path: 文件夹路径
        target_ext: 目标文件后缀（已标准化）

    Returns:
        list: 匹配的文件路径列表
    """
    matched_files = []

    try:
        for filename in os.listdir(folder_path):
            file_path = os.path.join(folder_path, filename)
            if os.path.isfile(file_path) and filename.lower().endswith(target_ext):
                matched_files.append(file_path)
    except PermissionError:
        print(f"[WARN] 权限不足，无法访问文件夹: {folder_path}")
    except OSError as e:
        print(f"[WARN] 访问文件夹失败 [{folder_path}]: {e}")

    return matched_files


def get_unique_filename(output_dir, filename):
    """
    获取唯一的文件名，避免重复

    如果目标文件已存在，自动添加数字后缀（如 filename_1.mp4）

    Args:
        output_dir: 输出目录路径
        filename: 原始文件名

    Returns:
        str: 唯一的文件名
    """
    base_name, ext = os.path.splitext(filename)
    counter = 1
    new_filename = filename

    while os.path.exists(os.path.join(output_dir, new_filename)):
        new_filename = f"{base_name}_{counter}{ext}"
        counter += 1

    return new_filename


def extract_files(base_path, target_ext):
    """
    遍历并提取指定后缀的文件

    遍历所有子文件夹：
    - 如果子文件夹中有匹配后缀的文件（一个或多个），全部移动到 output 目录

    Args:
        base_path: 要扫描的基础文件夹路径
        target_ext: 目标文件后缀（已标准化）

    Returns:
        int: 移动成功的文件数量
    """
    moved_count = 0

    # 修正：输出目录应在输入路径下，而非上级目录
    output_dir = os.path.join(base_path, 'output')

    try:
        os.makedirs(output_dir, exist_ok=True)
    except PermissionError:
        print(f"[ERR] 权限不足，无法创建输出目录: {output_dir}")
        return 0
    except OSError as e:
        print(f"[ERR] 创建输出目录失败: {e}")
        return 0

    for root, dirs, files in os.walk(base_path):
        # 跳过输出目录，避免循环移动
        if root == output_dir:
            continue

        target_files = get_target_files(root, target_ext)

        if target_files:
            for file_path in target_files:
                filename = os.path.basename(file_path)
                unique_filename = get_unique_filename(output_dir, filename)
                output_path = os.path.join(output_dir, unique_filename)

                try:
                    shutil.move(file_path, output_path)
                    print(f"[MOVED] 已移动: {filename} -> {unique_filename}")
                    moved_count += 1
                except PermissionError:
                    print(f"[WARN] 权限不足，无法移动文件: {filename}")
                except shutil.Error as e:
                    print(f"[WARN] 移动文件失败 [{filename}]: {e}")
                except OSError as e:
                    print(f"[WARN] 移动文件失败 [{filename}]: {e}")

    return moved_count


def validate_path(input_path):
    """
    验证输入路径是否有效

    Args:
        input_path: 用户输入的路径

    Returns:
        bool: True表示路径有效，False表示无效
    """
    input_path = input_path.strip('"')

    if not input_path:
        print("[ERR] 路径不能为空")
        return False

    if not os.path.exists(input_path):
        print(f"[ERR] 路径不存在: {input_path}")
        return False

    if not os.path.isdir(input_path):
        print(f"[ERR] 路径不是文件夹: {input_path}")
        return False

    return True


def validate_extension(ext):
    """
    验证文件后缀是否有效

    Args:
        ext: 用户输入的文件后缀

    Returns:
        bool: True表示后缀有效，False表示无效
    """
    ext = ext.strip()
    if not ext:
        print("[ERR] 文件后缀不能为空")
        return False

    # 只允许字母和数字的组合作为后缀
    if not ext.replace('.', '').isalnum():
        print("[ERR] 文件后缀只能包含字母和数字")
        return False

    return True


if __name__ == "__main__":
    print("=" * 50)
    print("    文件提取工具（按后缀筛选）")
    print("=" * 50)
    print("说明：本工具将遍历指定路径下的所有子文件夹")
    print("      并将所有匹配指定后缀的文件移动到 output 目录")
    print("=" * 50)

    # 获取并验证文件夹路径
    while True:
        path_input = input("\n请输入要扫描的文件夹路径: ").strip()
        if validate_path(path_input):
            path_input = path_input.strip('"')
            break

    # 获取并验证文件后缀
    while True:
        ext_input = input("请输入要提取的文件后缀（如 mp4）: ").strip()
        if validate_extension(ext_input):
            target_extension = normalize_extension(ext_input)
            break

    print(f"\n[SCAN] 正在扫描路径: {path_input}")
    print(f"[FILTER] 目标文件后缀: {target_extension}")
    print("=" * 50)

    moved = extract_files(path_input, target_extension)

    print("=" * 50)
    print("[DONE] 扫描完成！")
    print(f"   移动文件总数: {moved} 个")
    if moved > 0:
        output_path = os.path.join(path_input, 'output')
        print(f"   输出目录: {output_path}")