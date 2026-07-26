"""
B站缓存视频合并工具 - 将B站下载的缓存视频合并为完整MP4文件

功能说明:
    本脚本用于合并B站缓存的视频文件。B站缓存视频通常分为视频流和音频流两个文件，
    需要使用ffmpeg将它们合并为一个完整的MP4文件。

工作流程:
    1. 遍历B站缓存目录结构
    2. 读取entry.json文件获取视频标题
    3. 找到视频流和音频流文件（.m4s格式）
    4. 使用ffmpeg合并视频和音频
    5. 将结果保存到指定输出目录

使用方式:
    直接运行本脚本，默认处理指定目录下的所有缓存视频
"""

import subprocess
import os
import json


def merge(video_path, audio_path, output_path):
    """
    合并视频和音频文件
    
    使用ffmpeg将视频流和音频流合并为一个完整的MP4文件。
    
    Args:
        video_path: 视频流文件路径
        audio_path: 音频流文件路径
        output_path: 输出文件路径
        
    Returns:
        bool: 是否合并成功
    """
    # 指定ffmpeg.exe的路径
    ffmpeg_path = r"C:\Users\31749\Applications\ffmpeg-8.0.1-essentials_build\bin\ffmpeg.exe"

    # 检查ffmpeg是否存在
    if not os.path.exists(ffmpeg_path):
        print(f"错误：找不到ffmpeg.exe，路径：{ffmpeg_path}")
        return False

    # 构建FFmpeg命令
    cmd = [
        "ffmpeg",  # 指定FFmpeg可执行文件
        "-i", video_path,  # 输入视频
        "-i", audio_path,  # 输入音频
        "-c:v", "copy",  # 视频流直接复制
        "-c:a", "copy",  # 音频流直接复制
        "-y",  # 覆盖输出文件
        output_path  # 输出文件
    ]

    try:
        # 执行命令
        result = subprocess.run(
            cmd,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding='utf-8'
        )
        print(f"合并成功！输出文件：{output_path}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"合并失败！错误信息：{e.stderr}")
        return False


def iterate(root_path):
    """
    遍历B站缓存目录结构，收集所有需要合并的视频信息
    
    Args:
        root_path: B站缓存目录根路径
        
    Returns:
        list: 包含视频信息的字典列表
    """
    result_list = []
    output = r"C:\Users\31749\Downloads\output"

    # 确保输出目录存在
    if not os.path.exists(output):
        os.makedirs(output)

    # 文件计数器
    i = 0

    # 遍历一级目录（通常是视频UP主ID）
    for dirs in [dir for dir in os.listdir(root_path) if os.path.isdir(os.path.join(root_path, dir))]:
        dirs_path = os.path.join(root_path, dirs)

        # 遍历二级目录（通常是视频ID）
        for dir_path in [dir for dir in os.listdir(dirs_path) if os.path.isdir(os.path.join(dirs_path, dir))]:
            i += 1
            dir_path_full = os.path.join(dirs_path, dir_path)

            # 读取entry.json文件获取视频标题
            json_path = os.path.join(dir_path_full, "entry.json")
            if os.path.exists(json_path):
                json_data = json.load(open(json_path, 'r', encoding='utf-8'))
                title = sanitize_folder_title(json_data.get("title"), i)
            else:
                # 如果没有entry.json，使用默认标题
                title = f"video-{i}"
            
            # 构建输出文件路径
            output_path = os.path.join(output, f"{title}.mp4")

            # 获取视频质量目录（通常是80、120等数字）
            path_list = [dir for dir in os.listdir(dir_path_full) if os.path.isdir(os.path.join(dir_path_full, dir))]

            # 进入质量目录
            folder_path = os.path.join(dir_path_full, path_list[0])

            # 获取.m4s文件列表（排除json文件）
            m4s_path = os.listdir(folder_path)
            m4s_path = [path for path in m4s_path if ".json" not in path]
            
            # 检查是否有至少2个.m4s文件（视频和音频）
            if len(m4s_path) < 2:
                print(dirs_path)
                continue

            # 构建视频信息字典
            result = {
                "m4s1": os.path.join(folder_path, m4s_path[0]),
                "m4s2": os.path.join(folder_path, m4s_path[1]),
                "output": output_path
            }
            result_list.append(result)
    
    return result_list


def sanitize_folder_title(title, i):
    """
    清理视频标题，使其可以作为合法的文件名
    
    处理Windows文件名限制：
    - 替换禁止字符：\\/:*?"<>|
    - 去除首尾空格
    - 合并连续空格
    - 处理点号开头/结尾
    - 限制长度为255个字符
    
    Args:
        title: 原始标题
        i: 序号（用于生成默认标题）
        
    Returns:
        str: 清理后的标题
    """
    if not title:
        return "未命名文件夹" + str(i)

    # 1. 替换Windows严格禁止的字符
    invalid_chars = r'\/:*?"<>|'
    replace_map = {char: '#' for char in invalid_chars}
    safe_title = ''.join([replace_map.get(char, char) for char in title])

    # 2. 处理可能引起问题的符号
    # 去除首尾空格
    safe_title = safe_title.strip()
    # 多个连续空格合并为一个
    safe_title = ' '.join(safe_title.split())

    # 3. 处理点号问题
    if safe_title.startswith('.'):
        safe_title = '#' + safe_title[1:]
    if safe_title.endswith('.'):
        safe_title = safe_title[:-1] + '#'

    # 4. 处理长度限制（Windows文件名最长255个字符）
    max_length = 255
    if len(safe_title) > max_length:
        safe_title = safe_title[:max_length]

    # 5. 处理特殊情况（标题全为特殊字符被替换后为空）
    if not safe_title:
        safe_title = "未命名文件夹" + str(i)

    return safe_title + str(i)


def main(list_):
    """
    主函数：批量合并视频
    
    Args:
        list_: 视频信息列表
    """
    for item in list_:
        print(item)
        merge(item.get('m4s1'), item.get('m4s2'), item.get('output'))


if __name__ == '__main__':
    # B站缓存目录根路径
    root_path = r"C:\Users\31749\Downloads\download"

    # 遍历目录收集视频信息
    list_ = iterate(root_path)
    # 批量合并视频
    main(list_)
