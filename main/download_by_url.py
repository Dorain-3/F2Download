from datetime import datetime
import json
import logging
import os
import subprocess

url_path = r"D:\Settings\TikTok\video\new_url.json"

download_path = r"D:\Settings\TikTok\video\Download\douyin\post"

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(r'/logs/download.log'),
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
                logging.info(f"开始下载第{i+1}个url")
                download_url(url)

    except Exception as e:
        print(e)


def download_url(url):
    try:
        logging.info(f"开始处理URL: {url}")

        ps_command = f"f2 dy -p D:/Settings/TikTok/video/Download -u {url}"
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

        dirs = os.listdir(download_path)
        latest_folder = max(dirs, key=lambda f: os.path.getctime(os.path.join(download_path, f)))
        latest_folder_path = os.path.join(download_path, latest_folder)
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
    # 检查是否提供了命令行参数
    main(url_path)
    input()
