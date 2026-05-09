from dy.main.get_time_by_name import get_latest_date
from dy.main.read_cfg import get_config
import json
import logging
import os
import subprocess


def main(url_path):
    try:
        with open(url_path, 'r', encoding='utf-8') as f:
            #
            data = json.load(f)
            url_list = data['url']

            logging.info(f"开始下载#{url_list.__len__()}个url\n")

            for i, url in enumerate(url_list):
                #
                logging.info(f"开始下载第{i + 1}个url")

                download_url(url)

                logging.info(f"第{i + 1}个url下载完成\n")


    except Exception as e:
        print(e)


def download_url(url):
    try:
        logging.info(f"开始处理URL: {url}")

        ps_command = f"f2 -d DEBUG dy -p {download} -u {url}"

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

        old_date = get_latest_date(latest_folder_path)

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
    #
    cfg = get_config()

    root_path = cfg.root_path

    download = root_path / "Download"

    url_path = root_path / "new_url.json"

    DOWNLOAD_PATH = cfg.download_path

    LOG_PATH = cfg.log_path

    UPDATE_MAX_INDEX = cfg.update_max_index  # 提供默认值

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
