import os
import shutil

def copy_all_files_recursive(source_dir, target_dir):
    """
    递归地将源目录下的所有文件复制到目标目录（不保留目录结构）

    参数:
        source_dir (str): 源目录路径
        target_dir (str): 目标目录路径
    """

    # 确保目标目录存在，如果不存在则创建
    if not os.path.exists(target_dir):
        os.makedirs(target_dir)
        print(f"已创建目标目录: {target_dir}")

    # 计数器，用于统计复制的文件数量
    file_count = 0

    # 使用os.walk递归遍历所有目录和文件
    for root, _, files in os.walk(source_dir):
        for filename in files:
            source_path = os.path.join(root, filename)
            target_path = os.path.join(target_dir, filename)

            # 处理文件名冲突
            # if os.path.exists(target_path):
            #     base, ext = os.path.splitext(filename)
            #     counter = 1
            #     while os.path.exists(target_path):
            #         new_name = f"{base}_{counter}{ext}"
            #         target_path = os.path.join(target_dir, new_name)
            #         counter += 1

            try:
                shutil.move(source_path, target_path)  # 使用copy2保留元数据
                print(f"已复制: {filename} -> {os.path.basename(target_path)}")
                file_count += 1
            except Exception as e:
                print(f"复制失败 {filename}: {str(e)}")

    print(f"\n复制完成! 共复制 {file_count} 个文件到 {target_dir}")


if __name__ == "__main__":

    source_directory = r"D:\Settings\girls"
    target_directory = r"D:\Settings\sao_v"

    # 验证源目录是否存在
    if not os.path.isdir(source_directory):
        print(f"错误: 源目录 '{source_directory}' 不存在!")
    else:
        try:
            copy_all_files_recursive(source_directory, target_directory)
            print("\n文件复制完成!")
        except Exception as e:
            print(f"\n发生错误: {str(e)}")