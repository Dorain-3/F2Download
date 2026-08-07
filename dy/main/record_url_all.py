"""
URL记录工具 - 扫描视频目录并生成URL配置文件

功能说明:
    本脚本扫描post目录下的所有子目录，读取每个目录中的url.json文件，
    提取URL和日期信息，生成right_urls.json和error_urls.json文件。

工作流程:
    1. 遍历post目录下的所有子目录
    2. 读取每个目录中的url.json文件
    3. 提取URL列表、文件夹路径和最新日期
    4. 根据URL是否有效分类到right_urls.json或error_urls.json
    5. 保存结果文件并按更新状态和日期排序

文件结构:
    right_urls.json: {"json_list_len": N, "json_list": [...]}
    error_urls.json: {"json_list_len": N, "json_list": [...]}

使用方式:
    直接运行本脚本即可生成配置文件
"""

from datetime import datetime, timedelta
import json
import os
from pathlib import Path
import shutil
from dy.main.get_time_by_name import get_latest_date
from dy.main.read_cfg import get_config


def write_json_atomic(file_path, data):
    """先写入临时文件，再原子替换目标JSON，避免中途失败损坏原文件。"""
    file_path = Path(file_path)
    temp_path = file_path.with_name(f"{file_path.name}.tmp")

    with open(temp_path, "w", encoding="utf-8") as json_file:
        json.dump(data, json_file, indent=4, ensure_ascii=False)

    os.replace(temp_path, file_path)


def record_urls():
    """
    扫描目录并记录所有URL配置信息
    
    遍历post目录，读取每个子目录中的url.json文件，生成汇总的配置文件。
    """
    cfg = get_config()

    # 从统一配置获取文件路径
    root_path = cfg.post_path  # 视频目录
    json_path = cfg.right_urls_path  # 有效URL配置文件
    error_json_path = cfg.error_urls_path  # 无效URL配置文件

    if not root_path.is_dir():
        raise FileNotFoundError(f"视频目录不存在: {root_path}")

    # 初始化结果列表
    json_list2w = []  # 有效URL列表
    error_json_list = []  # 无效URL列表
    processed_count = 0

    # 读取现有的right_urls.json文件（用于保留历史更新时间）
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    json_list = data["json_list"]

    # 遍历post目录下的所有子目录和文件
    for root, dirs, files in os.walk(root_path):
        for file in files:
            # 只处理每个视频目录中的url.json，忽略其他JSON文件
            if file.lower() == "url.json":
                url_path = os.path.join(root, file)
                folder_path = root

                # 获取该目录下的最新日期
                latest_date = get_latest_date(folder_path)

                # 如果没有找到日期，使用当前日期
                if not latest_date:
                    print("this folder is empty " + folder_path)
                    latest_date = next(
                        (item.get("old_date") for item in json_list if item.get("url") == url))

                # 读取url.json文件内容
                with open(url_path, "r", encoding="utf-8") as f__:
                    data = json.load(f__)
                    if "url" not in data:
                        raise KeyError(f"文件缺少url字段: {url_path}")

                    url = data["url"]
                    processed_count += 1
                    # 计算下次更新的起始日期（最新日期+1天）
                    old_date = latest_date.strftime('%Y-%m-%d')

                    update_time = next(
                        (item.get("update_time", old_date) for item in json_list if item.get("url") == url),
                        old_date)

                    if datetime.strptime(update_time, '%Y-%m-%d').date() < datetime.strptime(old_date,
                                                                                             '%Y-%m-%d').date():
                        update_time = old_date

                    # 如果URL列表为空，归类到错误列表
                    if not url:
                        json_data = {
                            "url": url,
                            "local_path": os.path.join(root, file),
                            "folder_path": folder_path,
                            "old_date": old_date,
                            "update_time": update_time,
                            "is_update": "1"
                        }
                        error_json_list.append(json_data)
                    else:
                        # URL列表不为空，归类到正常列表
                        json_data = {
                            "url": url,
                            "local_path": os.path.join(root, file),
                            "folder_path": folder_path,
                            "old_date": old_date,
                            "update_time": update_time,
                            "is_update": next(
                                (item.get("is_update", "1") for item in json_list if item.get("url") == url), "1")
                        }
                        json_list2w.append(json_data)

    # 扫描结果为空时禁止覆盖现有文件，避免路径配置错误造成数据清空
    if processed_count == 0:
        raise RuntimeError(f"在视频目录中没有找到url.json，已取消写入: {root_path}")

    right_json_data = {
        "json_list_len": len(json_list2w),
        "json_list": sorted(
            json_list2w,
            key=lambda x: (
                -int(x['is_update']),
                datetime.strptime(x['update_time'], '%Y-%m-%d'),
                datetime.strptime(x['old_date'], '%Y-%m-%d'),
            ),
        ),
    }
    error_json_data = {
        "json_list_len": len(error_json_list),
        "json_list": error_json_list,
    }

    # 每次覆盖前自动备份right_urls.json
    backup_dir = cfg.backup_path
    backup_dir.mkdir(parents=True, exist_ok=True)
    backup_file = backup_dir / f"right_urls_record_{datetime.now():%Y%m%d_%H%M%S}.json"
    shutil.copy2(json_path, backup_file)
    print(f"right_urls backup: {backup_file}")

    # 使用原子替换写入，避免程序中断留下半个JSON文件
    write_json_atomic(json_path, right_json_data)
    write_json_atomic(error_json_path, error_json_data)

    print(f"processed url.json files: {processed_count}")
    print(f"right json files has {len(json_list2w)}")
    print(f"error json files has {len(error_json_list)}")


if __name__ == "__main__":
    # 调用主函数
    record_urls()
    # 等待用户输入后退出
    input("ok")
