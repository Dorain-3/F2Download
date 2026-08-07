"""
URL下载工具 - 根据URL列表批量下载抖音视频

功能说明:
    本脚本从new_url.json文件中读取URL列表，调用f2命令行工具批量下载抖音视频。
    下载完成后，自动在下载目录中创建url.json文件记录下载信息。

工作流程:
    1. 加载配置文件获取路径信息
    2. 读取new_url.json中的URL列表
    3. 逐个调用f2命令下载视频
    4. 获取下载目录中最新的文件夹
    5. 提取最新日期并创建url.json文件

使用方式:
    直接运行本脚本即可开始下载
"""

from dy.main.get_time_by_name import get_latest_date
from dy.main.read_cfg import get_config
import json
import logging
import os
from pathlib import Path
import shutil
import subprocess


def get_unique_folder_path(target_root, folder_name):
    """生成不重复的目标文件夹路径，重名时依次添加（2）、（3）等后缀。"""
    target_root = Path(target_root)
    target_path = target_root / folder_name
    index = 2

    while target_path.exists():
        target_path = target_root / f"{folder_name}（{index}）"
        index += 1

    return target_path


def move_download_folder_to_post(downloaded_folder, post_path):
    """将下载完成的整个文件夹移动到post目录，并自动处理重名。"""
    downloaded_folder = Path(downloaded_folder)
    post_path = Path(post_path)

    post_path.mkdir(parents=True, exist_ok=True)
    target_path = get_unique_folder_path(post_path, downloaded_folder.name)
    shutil.move(str(downloaded_folder), str(target_path))
    logging.info("文件夹移动完成: %s -> %s", downloaded_folder, target_path)
    return target_path


def save_remaining_urls(url_path, data, processed_count):
    """移除已经处理的URL，并通过临时文件原子写回待处理列表。"""
    url_path = Path(url_path)
    remaining_urls = data['url'][processed_count:]
    data['url'] = remaining_urls
    temp_path = url_path.with_name(f"{url_path.name}.tmp")

    with open(temp_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

    os.replace(temp_path, url_path)
    logging.info(
        "中断前已处理%s个URL，剩余%s个URL已写回: %s",
        processed_count,
        len(remaining_urls),
        url_path,
    )
    return remaining_urls


def main(url_path):
    """
    主函数 - 读取URL列表并批量下载
    
    Args:
        url_path: URL列表文件路径（new_url.json）
    """
    try:
        # 读取URL列表文件
        with open(url_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            url_list = data['url']

        # 记录日志：开始下载
        logging.info(f"开始下载#{url_list.__len__()}个url\n")

        # 逐个处理URL，并记录已经完成处理的数量
        processed_count = 0
        try:
            for i, url in enumerate(url_list):
                logging.info(f"开始下载第{i + 1}个url")
                # 调用下载函数
                download_url(url)
                processed_count += 1
                logging.info(f"第{i + 1}个url下载完成\n")
        except KeyboardInterrupt:
            remaining_urls = save_remaining_urls(url_path, data, processed_count)
            print(
                f"\n程序已中断，已移除{processed_count}个已处理URL，"
                f"剩余{len(remaining_urls)}个URL。"
            )
            raise SystemExit(130)

    except Exception as e:
        print(e)


def download_url(url):
    """
    下载单个URL的视频
    
    Args:
        url: 抖音视频URL
    """
    try:
        # 记录日志：开始处理URL
        logging.info(f"开始处理URL: {url}")

        # 构建f2命令（使用powershell执行）
        ps_command = f"f2 -d DEBUG dy -p {download} -u {url}"
        logging.info(ps_command)

        # 执行命令
        process = subprocess.run(
            ["powershell", "-ExecutionPolicy", "Bypass", "-Command", ps_command],
            capture_output=True,
            text=True,
            encoding='gbk',
            errors='ignore'
        )

        # 检查命令执行结果
        if process.returncode == 0:
            logging.info(f"url处理成功: {url}")

        # 获取下载目录中最新创建的文件夹
        dirs = os.listdir(DOWNLOAD_PATH)
        latest_folder = max(dirs, key=lambda f: os.path.getctime(os.path.join(DOWNLOAD_PATH, f)))
        latest_folder_path = os.path.join(DOWNLOAD_PATH, latest_folder)

        # 构建url.json文件路径
        json_path = os.path.join(latest_folder_path, "url.json")

        # 获取该目录下最新的日期
        old_date = get_latest_date(latest_folder_path)

        # 构建要写入的JSON数据
        json_data = {
            "url": [url],
            "old_date": old_date.strftime('%Y-%m-%d')
        }

        # 记录日志：日期信息
        logging.info(f"old_date: {old_date.strftime('%Y-%m-%d')}")

        # 写入url.json文件
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, ensure_ascii=False, indent=4)

        # 将下载完成的整个文件夹移动到post目录，重名时自动添加序号
        moved_folder_path = move_download_folder_to_post(latest_folder_path, POST_PATH)
        logging.info("URL对应文件夹已归档: %s", moved_folder_path)

    except Exception as e:
        print(e)


if __name__ == "__main__":
    # 加载配置
    cfg = get_config()

    # 获取路径配置
    download = cfg.download_dir  # 下载临时目录
    url_path = cfg.new_url_path  # URL列表文件
    DOWNLOAD_PATH = cfg.download_path  # 下载文件存放路径
    POST_PATH = cfg.post_path  # 下载完成后的归档目录
    LOG_PATH = cfg.log_path  # 日志文件路径

    # 配置日志（同时输出到文件和控制台）
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(LOG_PATH),
            logging.StreamHandler()
        ],
        encoding='utf-8'
    )

    # 调用主函数开始下载
    main(url_path)

    # 等待用户输入后退出
    input("下载完成")
