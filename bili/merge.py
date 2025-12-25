# 合并bilibili缓存文件


import subprocess
import os
import json


#
# 合并bili缓存视频
#
#

def merge(video_path, audio_path, output_path):
    # 手动指定ffmpeg.exe的路径（替换为你的实际路径）
    ffmpeg_path = r"C:\Users\31749\APP\ffmpeg-7.1.1-full_build\bin\ffmpeg.exe"  # 例如：C:\ffmpeg-6.0\bin\ffmpeg.exe

    # 检查ffmpeg是否存在
    if not os.path.exists(ffmpeg_path):
        print(f"错误：找不到ffmpeg.exe，路径：{ffmpeg_path}")
        return False

    # 构建FFmpeg命令
    cmd = [
        ffmpeg_path,  # 指定FFmpeg可执行文件
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
    result_list = []
    output = r"C:\Users\31749\Downloads\output"
    i = 0

    for dirs in [dir for dir in os.listdir(root_path) if os.path.isdir(os.path.join(root_path, dir))]:
        # dirs = "114986374399514"

        dirs_path = os.path.join(root_path, dirs)
        # dirs_path = "C:\Users\31749\Downloads\压缩文件\114986374399514

        for dir_path in [dir for dir in os.listdir(dirs_path) if os.path.isdir(os.path.join(dirs_path, dir))]:
            i += 1
            dir_path = os.path.join(dirs_path, dir_path)

            json_path = os.path.join(dir_path, "entry.json")
            # json_path = "C:\Users\31749\Downloads\压缩文件\114986374399514\c_31542021453\entry.json"
            json_data = json.load(open(json_path, 'r', encoding='utf-8'))
            title = sanitize_folder_title(json_data.get("title"), i)
            output_path = os.path.join(output, f"{title}.mp4")

            path_list = [dir for dir in os.listdir(dir_path) if os.path.isdir(os.path.join(dir_path, dir))]

            # print(path_list)
            # path_list = ["80"]

            folder_path = os.path.join(dir_path, path_list[0])
            # folder_path = "C:\Users\31749\Downloads\压缩文件\114986374399514\c_31542021453\80"

            m4s_path = os.listdir(folder_path)
            m4s_path = [path for path in m4s_path if ".json" not in path]
            # m4s_path = ["audio.m4s","video.m4s"]

            print(m4s_path)
            m4s_list = []
            for m4s in m4s_path:
                m4s_list.append(os.path.join(folder_path, m4s))
            m4s_list.append(output_path)
            result_list.append(m4s_list)
    print((result_list))
    return result_list


def sanitize_folder_title(title, i):
    if not title:
        return "未命名文件夹" + str(i)  # 处理空标题

    # 1. 替换Windows严格禁止的字符（必选）
    invalid_chars = r'\/:*?"<>|'
    replace_map = {char: '#' for char in invalid_chars}
    safe_title = ''.join([replace_map.get(char, char) for char in title])

    # 2. 处理可能引起问题的符号（可选但推荐）
    # 去除首尾空格（避免文件夹名首尾有空格导致识别困难）
    safe_title = safe_title.strip()

    # 多个连续空格合并为一个（避免路径中出现过多空格）
    safe_title = ' '.join(safe_title.split())

    # 处理点号问题（Windows不推荐文件夹名以点号开头/结尾）
    if safe_title.startswith('.'):
        safe_title = '#' + safe_title[1:]  # 点号开头替换为#
    if safe_title.endswith('.'):
        safe_title = safe_title[:-1] + '#'  # 点号结尾替换为#

    # 3. 处理长度限制（Windows文件夹名最长255个字符）
    max_length = 255
    if len(safe_title) > max_length:
        safe_title = safe_title[:max_length]  # 截断过长标题

    # 4. 处理特殊情况（标题全为特殊字符被替换后为空）
    if not safe_title:
        safe_title = "未命名文件夹" + str(i)

    return safe_title + str(i)


def main(list_):
    for item in list_:
        merge(item[1], item[0], item[2])


if __name__ == '__main__':
    root_path = r"C:\Users\31749\Downloads\download"
    main(iterate(root_path))
    # merge(video, audio, output_path)
