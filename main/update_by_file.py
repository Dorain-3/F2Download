import os
import json
import shutil
import subprocess
import logging
import sys
from datetime import datetime
from pathlib import Path

import yaml


def main(update_path_to_download: Path):
    """主函数：遍历文件并处理所有JSON块"""
    try:
        with open(update_path_to_download, "r", encoding="utf-8") as f:
            jsons_data = json.load(f)

        json_list = jsons_data["json_list"]

        json_list = sorted(json_list,
                           key=lambda x: (-int(x['is_update']), datetime.strptime(x['old_date'], '%Y-%m-%d')))

        index = 0
        count = 0

        while count < UPDATE_MAX_INDEX:
            json_data = json_list[index]
            index += 1
            logging.info(f"开始下载第{index}个json,剩余{UPDATE_MAX_INDEX - count}个")
            count_ = download_by_json(json_data)

            if count_ > 0:
                json_data["old_date"] = datetime.now().strftime('%Y-%m-%d')
                count += 1
            else:
                json_data["is_update"] = "0"

        json_list = sorted(json_list,
                           key=lambda x: (-int(x['is_update']), datetime.strptime(x['old_date'], '%Y-%m-%d')))

        json_data_to_write = {
            "json_list_len": len(json_list),
            "json_list": json_list,
        }
        logging.info(f"successfully updated {UPDATE_MAX_INDEX} urls")
        with open(UPDATE_PATH, "w+", encoding="utf-8") as f:
            json.dump(json_data_to_write, f, ensure_ascii=False, indent=4)


    except Exception as e:
        print(e)


def download_by_json(json_data: dict):
    # json_data = json.loads(json_data)
    try:
        urls = json_data['url']
        old_date = json_data['old_date']
        folder_path = json_data['folder_path']

        logging.info(f"#{folder_path} has {urls.__len__()} urls!")
        for index, url in enumerate(urls, 1):
            download_single_url(url, old_date)

        file_count = 0

        for root, _, files in os.walk(DOWNLOAD_PATH):
            for filename in files:
                source_path = os.path.join(root, filename)
                target_path = os.path.join(folder_path, filename)

                try:
                    shutil.copy2(source_path, target_path)  # 使用copy2保留元数据
                    file_count += 1
                except Exception as e:
                    print(f"复制失败 {filename}: {str(e)}")

        logging.info(f"复制完成! 共复制 {file_count} 个文件到 {folder_path}\n")
        shutil.rmtree(DOWNLOAD_PATH)
        os.makedirs(DOWNLOAD_PATH)

        return file_count

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
            encoding='gbk',
            errors='ignore'
        )

        if process.returncode == 0:
            logging.info(f"url处理成功: {url}")


    except Exception as e:
        logging.error(e)
        print(e)


if __name__ == "__main__":

    config_path = r"D:\Settings\TikTok\video\config.yaml"

    try:

        with open(config_path, 'r', encoding='utf-8') as file:
            app_config = yaml.safe_load(file)  # 使用 safe_load 避免安全风险[7,8](@ref)

        PATHS = app_config.get('paths', {})
        SETTINGS = app_config.get('settings', {})

        DOWNLOAD_PATH = Path(PATHS.get('download_path'))
        UPDATE_PATH = Path(PATHS.get('update_path'))
        BACKUP_PATH = Path(PATHS.get('backup_path'))
        LOG_PATH = Path(PATHS.get('log_path'))
        UPDATE_MAX_INDEX = SETTINGS.get('update_max_index', 5)  # 提供默认值

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


    except yaml.YAMLError as e:
        raise ValueError(f"解析配置文件时出错: {e}")
    except Exception as e:
        print(f"备份过程中发生错误: {e}")
        sys.exit()
    except FileNotFoundError:
        raise FileNotFoundError(f"配置文件未找到")

    main(UPDATE_PATH)

    input("按回车键退出...")  # 程序会停在这里，等待用户按下回车键
