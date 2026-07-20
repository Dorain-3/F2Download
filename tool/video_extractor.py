"""
视频提取工具

功能说明:
    本脚本用于遍历指定文件夹路径下的所有子文件夹，自动提取所有视频文件。
    如果子文件夹中有视频文件（一个或多个），全部移动到输入路径/output目录下。

使用方式:
    直接运行本脚本，按提示输入文件夹路径即可

注意事项:
    1. 视频文件定义：后缀为 .mp4, .mkv, .avi, .mov, .wmv, .flv, .webm, .ts, .rmvb 的文件
    2. 移动操作不可逆，请谨慎使用
    3. 如果目标文件已存在，会自动添加数字后缀（如 filename_1.mp4）
    4. 遇到权限问题时会自动跳过并提示
"""

import os
import shutil


VIDEO_EXTENSIONS = ('.mp4', '.mkv', '.avi', '.mov', '.wmv', '.flv', '.webm', '.ts', '.rmvb')


def is_video_file(filename):
    """
    判断文件是否为视频文件
    
    Args:
        filename: 文件名
        
    Returns:
        bool: True表示是视频文件，False表示不是
    """
    return filename.lower().endswith(VIDEO_EXTENSIONS)


def get_video_files(folder_path):
    """
    获取文件夹中的所有视频文件
    
    Args:
        folder_path: 文件夹路径
        
    Returns:
        list: 视频文件路径列表
    """
    video_files = []
    
    try:
        for filename in os.listdir(folder_path):
            file_path = os.path.join(folder_path, filename)
            if os.path.isfile(file_path) and is_video_file(filename):
                video_files.append(file_path)
    except PermissionError:
        print(f"[WARN] 权限不足，无法访问文件夹: {folder_path}")
    except OSError as e:
        print(f"[WARN] 访问文件夹失败 [{folder_path}]: {e}")
    
    return video_files


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


def extract_videos(base_path):
    """
    遍历并提取视频文件
    
    遍历所有子文件夹：
    - 如果子文件夹中有视频文件（一个或多个），全部移动到 output 目录
    
    Args:
        base_path: 要扫描的基础文件夹路径
        
    Returns:
        int: 移动成功的视频文件数量
    """
    moved_count = 0
    
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
        if root == output_dir:
            continue
        
        video_files = get_video_files(root)
        
        if len(video_files) >= 1:
            for video_path in video_files:
                filename = os.path.basename(video_path)
                unique_filename = get_unique_filename(output_dir, filename)
                output_path = os.path.join(output_dir, unique_filename)
                
                try:
                    shutil.move(video_path, output_path)
                    print(f"[MOVED] 已移动: {video_path} -> {unique_filename}")
                    moved_count += 1
                except PermissionError:
                    print(f"[WARN] 权限不足，无法移动文件: {video_path}")
                except shutil.Error as e:
                    print(f"[WARN] 移动文件失败 [{video_path}]: {e}")
                except OSError as e:
                    print(f"[WARN] 移动文件失败 [{video_path}]: {e}")
    
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


if __name__ == "__main__":
    print("=" * 40)
    print("    视频提取工具")
    print("=" * 40)
    print("说明：本工具将遍历指定路径下的所有子文件夹")
    print("      如果子文件夹中有视频文件（一个或多个），全部移动到 output 目录")
    print("=" * 40)
    
    while True:
        user_input = input("\n请输入要扫描的文件夹路径: ").strip()
        
        if validate_path(user_input):
            user_input = user_input.strip('"')
            break
    
    print(f"\n[SCAN] 正在扫描路径: {user_input}")
    print("=" * 40)
    
    moved = extract_videos(user_input)
    
    print("=" * 40)
    print("[DONE] 扫描完成！")
    print(f"   自动移动视频文件: {moved} 个")
    if moved > 0:
        print(f"   输出目录: {os.path.join(user_input, 'output')}")