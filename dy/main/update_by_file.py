"""
批量更新下载工具 - 根据right_urls.json批量更新抖音视频

功能说明:
    本脚本从right_urls.json文件中读取URL配置列表，按配置的最大更新数量批量下载视频。
    支持自动备份配置文件、更新日期信息、排序和保存结果。

工作流程:
    1. 加载配置文件获取路径信息
    2. 备份right_urls.json文件
    3. 读取right_urls.json中的URL配置列表
    4. 按最大更新数量循环下载视频
    5. 更新每个配置项的日期信息
    6. 按更新状态和日期排序并保存结果

使用方式:
    直接运行本脚本即可开始批量更新下载
"""

import os
import json
import shutil
import subprocess
import logging
import sys
from datetime import datetime, timedelta
from pathlib import Path
from dy.main.get_time_by_name import get_latest_date
from dy.main.read_cfg import get_config


def main(update_path_to_download: Path):
    """
    主函数：遍历文件并处理所有JSON块
    
    Args:
        update_path_to_download: right_urls.json文件路径
    """
    try:
        # 读取right_urls.json文件
        with open(update_path_to_download, "r", encoding="utf-8") as f:
            jsons_data = json.load(f)

        # 提取json_list列表
        json_list = jsons_data["json_list"]

        # 初始化索引和计数器
        index = 0
        count = 0

        # 循环处理，直到达到最大更新数量
        while count < UPDATE_MAX_INDEX:
            # 获取当前JSON块
            json_data = json_list[index]
            index += 1

            # 记录日志：开始下载
            logging.info(f"开始下载第{index}个json,剩余{UPDATE_MAX_INDEX - count}个")
            
            # 调用下载函数
            count_, latest_date = download_by_json(json_data)

            # 记录日志：最新日期
            logging.info(f"latest_date:{(latest_date + timedelta(days=1))}\n")

            # 如果下载成功且获取到了日期
            if count_ > 0 and latest_date is not None:
                # 更新旧日期（最新日期+1天）
                json_data["old_date"] = (latest_date + timedelta(days=1)).strftime('%Y-%m-%d')
                # 更新更新时间为当前日期
                json_data["update_time"] = datetime.now().strftime('%Y-%m-%d')
                count += 1
            else:
                # 下载失败，标记为不需要更新
                json_data["is_update"] = "0"

        # 按更新状态、更新时间、旧日期排序
        json_list = sorted(json_list,
                           key=lambda x: (-int(x['is_update']), datetime.strptime(x['update_time'], '%Y-%m-%d'),
                                          datetime.strptime(x['old_date'], '%Y-%m-%d')))

        # 构建要写入的数据结构
        json_data_to_write = {
            "json_list_len": len(json_list),
            "json_list": json_list,
        }

        # 写回right_urls.json文件
        with open(UPDATE_PATH, "w+", encoding="utf-8") as f:
            json.dump(json_data_to_write, f, ensure_ascii=False, indent=4)

        # 记录日志：更新完成
        logging.info(f"successfully updated {UPDATE_MAX_INDEX} urls")

    except Exception as e:
        print(e)


def download_by_json(json_data: dict):
    """
    根据JSON配置下载视频并复制到目标目录
    
    Args:
        json_data: 单个URL配置字典
        
    Returns:
        file_count: 复制的文件数量
        latest_date: 目标目录中的最新日期
    """
    try:
        # 提取配置信息
        urls = json_data['url']
        old_date = json_data['old_date']
        folder_path = json_data['folder_path']

        # 记录日志：URL数量
        logging.info(f"#{folder_path} has {urls.__len__()} urls!")

        # 逐个下载URL
        for index, url in enumerate(urls, 1):
            # 记录日志：开始下载
            logging.info(f"开始下载第{index + 1}个URL: {url}")
            # 调用下载函数
            download_single_url(url, old_date)

        # 复制下载的文件到目标目录
        file_count = 0

        # 遍历下载目录中的所有文件
        for root, _, files in os.walk(DOWNLOAD_PATH):
            for filename in files:
                source_path = os.path.join(root, filename)
                target_path = os.path.join(folder_path, filename)

                try:
                    # 使用copy2保留文件元数据
                    shutil.copy2(source_path, target_path)
                    file_count += 1
                except Exception as e:
                    print(f"复制失败 {filename}: {str(e)}")

        # 记录日志：复制完成
        logging.info(f"复制完成! 共复制 {file_count} 个文件到 {folder_path}")

        # 获取目标目录中的最新日期
        latest_date = get_latest_date(folder_path)
        
        # 清空下载目录（为下次下载做准备）
        shutil.rmtree(DOWNLOAD_PATH)
        os.makedirs(DOWNLOAD_PATH)

        return file_count, latest_date

    except Exception as e:
        print(e)


def download_single_url(url: str, old_date: str):
    """
    下载单个URL的视频
    
    Args:
        url: 抖音视频URL
        old_date: 起始日期（格式：YYYY-MM-DD）
    """
    try:
        # 构建f2命令（使用powershell执行）
        ps_command = f"f2 -d DEBUG dy -p {Download_path} -i {old_date}'|'2030-12-01 -u {url}"

        # 记录日志：命令内容
        logging.info(ps_command)

        # 执行命令
        process = subprocess.run(
            ["powershell", "-ExecutionPolicy", "Bypass", "-Command", ps_command],
            capture_output=True,
            text=True,
            encoding='UTF-8',
            errors='ignore'
        )

        # 检查命令执行结果
        if process.returncode == 0:
            logging.info(f"url处理成功: {url}")

    except Exception as e:
        logging.error(e)
        print(e)


if __name__ == "__main__":
    # 加载配置
    cfg = get_config()

    # 获取路径配置
    Download_path = cfg.download_dir              # 下载临时目录
    DOWNLOAD_PATH = cfg.download_path            # 下载文件存放路径
    UPDATE_PATH = cfg.right_urls_path             # 更新数据文件路径
    BACKUP_PATH = cfg.backup_path                # 备份文件路径
    LOG_PATH = cfg.log_path                      # 日志文件路径
    UPDATE_MAX_INDEX = cfg.update_max_index      # 最大更新数量

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

    # 复制文件到目标位置（备份）
    shutil.copy2(UPDATE_PATH, target_file_path)
    print(f"文件备份成功: {file_name} -> {new_file_name}")
    print(f"备份位置: {target_file_path}")

    # 调用主函数开始更新下载
    main(UPDATE_PATH)

    # 等待用户输入后退出
    input("按回车键退出...")
