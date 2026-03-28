from datetime import datetime
from dy.tool.update_time_by_name import find_latest_date_from_files
import json
import logging
import os
import subprocess
from pathlib import Path
import yaml


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

        dirs = os.listdir(DOWNLOAD_PATH)
        latest_folder = max(dirs, key=lambda f: os.path.getctime(os.path.join(DOWNLOAD_PATH, f)))
        latest_folder_path = os.path.join(DOWNLOAD_PATH, latest_folder)
        json_path = os.path.join(latest_folder_path, "url.json")

        old_date = find_latest_date_from_files(latest_folder_path)

        json_data = {
            "url": [url],
            "old_date": old_date.strftime('%Y-%m-%d')
        }

        logging.info(f"old_date: {old_date.strftime('%Y-%m-%d')}")

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

    url_path = parent_dir / "new_url.json"

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

        main(url_path)
        input("下载完成")

    except yaml.YAMLError as e:
        raise ValueError(f"解析配置文件时出错: {e}")
    except Exception as e:
        print(f"备份过程中发生错误: {e}")
    except FileNotFoundError:
        raise FileNotFoundError(f"配置文件未找到")
