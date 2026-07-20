"""
空文件夹清理工具

功能说明:
    本脚本用于遍历指定文件夹路径下的所有子文件夹，自动删除所有空文件夹。
    采用自底向上遍历方式，确保删除子文件夹后，如果其父文件夹变为空，也会被删除。

使用方式:
    直接运行本脚本，按提示输入文件夹路径即可

注意事项:
    1. 空文件夹定义：不包含任何文件和子文件夹的文件夹
    2. 使用前请确认路径正确，删除操作不可恢复
    3. 遇到权限问题时会自动跳过并提示
"""

import os


def delete_empty_folders(base_path):
    """
    遍历并删除空文件夹
    
    采用自底向上遍历（topdown=False），确保子文件夹先被处理。
    如果删除子文件夹后父文件夹变为空，父文件夹也会被删除。
    
    Args:
        base_path: 要扫描的基础文件夹路径
        
    Returns:
        int: 删除的空文件夹数量
    """
    deleted_count = 0

    for root, dirs, files in os.walk(base_path, topdown=False):
        for dir_name in dirs:
            dir_path = os.path.join(root, dir_name)

            try:
                if not os.listdir(dir_path):
                    os.rmdir(dir_path)
                    print(f"🗑️ 已删除空文件夹: {dir_path}")
                    deleted_count += 1
            except PermissionError:
                print(f"⚠️ 权限不足，无法删除: {dir_path}")
            except OSError as e:
                print(f"⚠️ 删除失败 [{dir_path}]: {e}")

    return deleted_count


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
        print("❌ 路径不能为空")
        return False

    if not os.path.exists(input_path):
        print(f"❌ 路径不存在: {input_path}")
        return False

    if not os.path.isdir(input_path):
        print(f"❌ 路径不是文件夹: {input_path}")
        return False

    return True


if __name__ == "__main__":
    print("=" * 40)
    print("    空文件夹清理工具")
    print("=" * 40)
    print("说明：本工具将遍历指定路径下的所有子文件夹")
    print("      自动删除所有空文件夹（包含嵌套空文件夹）")
    print("=" * 40)

    while True:
        user_input = input("\n请输入要清理的文件夹路径: ").strip()

        if validate_path(user_input):
            user_input = user_input.strip('"')
            break

    print(f"\n🔍 正在扫描路径: {user_input}")
    print("=" * 40)

    deleted = delete_empty_folders(user_input)

    print("=" * 40)
    if deleted > 0:
        print(f"✅ 清理完成！共删除 {deleted} 个空文件夹")
    else:
        print("✅ 扫描完成，未发现空文件夹")
