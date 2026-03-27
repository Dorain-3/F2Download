import sys
from datetime import datetime
import json
import logging
import os
import subprocess
from pathlib import Path

import yaml

script_dir = Path(sys.executable).parent.resolve()
parent_dir = script_dir.parent

url_path = parent_dir / "new_url.json"

download_post_path = parent_dir / "Download" / "douyin" / "post"

log_path = script_dir / "logs" / "download.log"

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_path),
        logging.StreamHandler()
    ]
)


def main(url_path):
    try:
        with open(url_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            url_list = data['url']
            logging.info(f"开始下载#{url_list.__len__()}个url")
            for i, url in enumerate(url_list):
                logging.info(f"开始下载第{i + 1}个url")
                download_url(url)

    except Exception as e:
        print(e)


def download_url(url):
    try:
        logging.info(f"开始处理URL: {url}")

        download_path = parent_dir / "Download"

        ps_command = f"f2 -d DEBUG dy -p {download_path} -u {url}"
        logging.info(ps_command)

        process = subprocess.run(
            ["powershell", "-ExecutionPolicy", "Bypass", "-Command", ps_command],
            capture_output=True,
            text=True,
            encoding='gbk',
            errors='ignore'
        )

        if process.returncode == 0:
            logging.info(f"url处理成功: {url}")

        dirs = os.listdir(download_post_path)
        latest_folder = max(dirs, key=lambda f: os.path.getctime(os.path.join(download_post_path, f)))
        latest_folder_path = os.path.join(download_post_path, latest_folder)
        json_path = os.path.join(latest_folder_path, "url.json")

        json_data = {
            "url": [url],
            "old_date": datetime.now().strftime('%Y-%m-%d')
        }
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, ensure_ascii=False, indent=4)

    except Exception as e:
        print(e)


if __name__ == "__main__":

    # script_dir = Path(sys.executable).parent.resolve()
    script_dir = Path(r'C:\Users\31749\Dorain_file\TikTok\video\tool')
    parent_dir = script_dir.parent

    config_path = parent_dir / "config.yaml"
    Download_path = parent_dir / "Download"

    try:

        with open(config_path, 'r', encoding='utf-8') as file:
            app_config = yaml.safe_load(file)  # 使用 safe_load 避免安全风险[7,8](@ref)

        PATHS = app_config.get('paths', {})
        SETTINGS = app_config.get('settings', {})

        DOWNLOAD_PATH = Path(PATHS.get('download_path'))
        UPDATE_PATH = Path(PATHS.get('update_path'))
        BACKUP_PATH = Path(PATHS.get('backup_path'))
        LOG_PATH = Path(PATHS.get('log_path'))
        UPDATE_MAX_INDEX = SETTINGS.get('update_max_index', 20)  # 提供默认值

        # 配置日志
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(LOG_PATH),
                logging.StreamHandler()
            ],
            encoding='utf-8'
        )

        # 检查源文件是否存在
        if not os.path.exists(UPDATE_PATH):
            print(f"错误：源文件 '{UPDATE_PATH}' 不存在")
            sys.exit()

        # 检查目标目录是否存在，如果不存在则创建
        if not os.path.exists(BACKUP_PATH):
            os.makedirs(BACKUP_PATH)
            print(f"创建目标目录: {BACKUP_PATH}")

        # 获取文件名和扩展名
        file_name = os.path.basename(UPDATE_PATH)
        name_without_ext, file_extension = os.path.splitext(file_name)

        # 获取当前日期并格式化为字符串
        current_date = datetime.now().strftime("%Y-%m-%d")

        # 构建新文件名（原文件名_当前日期.扩展名）
        new_file_name = f"{name_without_ext}_{current_date}{file_extension}"
        target_file_path = os.path.join(BACKUP_PATH, new_file_name)

        # 复制文件到目标位置
        shutil.copy2(UPDATE_PATH, target_file_path)
        print(f"文件备份成功: {file_name} -> {new_file_name}")
        print(f"备份位置: {target_file_path}")

        main(UPDATE_PATH)


    except yaml.YAMLError as e:
        raise ValueError(f"解析配置文件时出错: {e}")
    except Exception as e:
        print(f"备份过程中发生错误: {e}")
    except FileNotFoundError:
        raise FileNotFoundError(f"配置文件未找到")

    main(url_path)
    input("下载完成")
