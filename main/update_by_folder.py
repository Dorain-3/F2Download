import glob
import os
import json
import shutil
import subprocess
import logging

download_path = r"D:\Settings\TikTok\video\Download\douyin\post"

update_path = ""

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(r'/logs/update.log'),
        logging.StreamHandler()
    ]
)


def main(root_directory: str):
    """主函数：遍历文件夹并处理所有JSON文件"""
    if not os.path.isdir(root_directory):
        logging.error(f"目录不存在: {root_directory}")
        return

    for dir_ in os.listdir(root_directory):
        if os.path.isdir(os.path.join(root_directory, dir_)):
            folder_path = os.path.join(root_directory, dir_)
            download_by_folder(folder_path)


def download_by_folder(folder_path: str):
    json_files = glob.glob("**/*.json", root_dir=folder_path, recursive=True)
    if len(json_files) == 1:
        json_path = os.path.join(folder_path, json_files[0])
    else:
        logging.error(f"find more than one json file in #{folder_path}")
        return

    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            urls = data['url']
            old_date = data['old_date']
            if urls.__len__() == 0:
                logging.error(f"#{folder_path} has no urls!")
                return
            elif urls.__len__() == 1:
                logging.info(f"#{folder_path} has only one urls!")
                download_single_url(urls[0], old_date)
                logging.info(f"url #{urls[0]} download success!")
                dirs = os.listdir(download_path)
                latest_folder = max(dirs, key=lambda f: os.path.getctime(os.path.join(download_path, f)))
                latest_folder_path = os.path.join(download_path, latest_folder)
            else:
                logging.info(f"#{folder_path} has {urls.__len__()} urls!")
                for index, url in enumerate(urls, 1):
                    download_single_url(url, old_date)
                    logging.info(f"url #{url} download success!")
                    if index == 1:
                        dirs = os.listdir(download_path)
                        latest_folder = max(dirs, key=lambda f: os.path.getctime(os.path.join(download_path, f)))
                        latest_folder_path = os.path.join(download_path, latest_folder)

        file_count = 0
        for root, _, files in os.walk(folder_path):
            for filename in files:
                source_path = os.path.join(root, filename)
                target_path = os.path.join(latest_folder_path, filename)

                try:
                    shutil.copy2(source_path, target_path)  # 使用copy2保留元数据
                    file_count += 1
                except Exception as e:
                    print(f"复制失败 {filename}: {str(e)}")

        print(f"\n复制完成! 共复制 {file_count} 个文件到 {latest_folder_path}")
        logging.info(f"\n复制完成! 共复制 {file_count} 个文件到 {latest_folder_path}")


    except Exception as e:
        print(e)


def download_single_url(url: str, old_date: str):
    try:
        logging.info(f"开始下载URL: {url}")

        ps_command = f"f2 dy -p D:/Settings/TikTok/video/Download -i {old_date}'|'2027-01-01 -u {url}"
        logging.info(ps_command)

        process = subprocess.run(
            ["powershell", "-ExecutionPolicy", "Bypass", "-Command", ps_command],
            capture_output=True,
            text=True,
            encoding='utf-8',
        )

        if process.returncode == 0:
            logging.info(f"url处理成功: {url}")
        else:
            logging.error(f"错误信息: {process.stderr.strip()}")

    except Exception as e:
        logging.error(e)
        print(e)


if __name__ == "__main__":
    main(update_path)
