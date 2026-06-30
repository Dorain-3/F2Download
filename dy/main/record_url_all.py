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
from get_time_by_name import get_latest_date

# 项目根目录路径
parent_dir = Path(r"C:\Users\31749\Dorain_file\TikTok\video")


def record_urls():
    """
    扫描目录并记录所有URL配置信息
    
    遍历post目录，读取每个子目录中的url.json文件，生成汇总的配置文件。
    """
    # 定义文件路径
    root_path = parent_dir / "post"           # 视频目录
    json_path = parent_dir / "right_urls.json"  # 有效URL配置文件
    error_json_path = parent_dir / "error_urls.json"  # 无效URL配置文件

    # 初始化结果列表
    json_list2w = []      # 有效URL列表
    error_json_list = []  # 无效URL列表
    
    # 读取现有的right_urls.json文件（用于保留历史更新时间）
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    json_list = data["json_list"]

    # 遍历post目录下的所有子目录和文件
    for root, dirs, files in os.walk(root_path):
        for file in files:
            # 只处理json文件
            if file.endswith(".json"):
                url_path = os.path.join(root, file)
                folder_path = root

                # 获取该目录下的最新日期
                latest_date = get_latest_date(folder_path)

                # 如果没有找到日期，使用当前日期
                if not latest_date:
                    print(folder_path)
                    latest_date = datetime.now()

                # 读取url.json文件内容
                with open(url_path, "r", encoding="utf-8") as f__:
                    data = json.load(f__)
                    url = data["url"]
                    # 计算下次更新的起始日期（最新日期+1天）
                    old_date = (latest_date + timedelta(days=1)).strftime('%Y-%m-%d')
                    datetime_now = datetime.now().strftime('%Y-%m-%d')

                    # 如果URL列表为空，归类到错误列表
                    if not url:
                        json_data = {
                            "url": url,
                            "local_path": os.path.join(root, file),
                            "folder_path": folder_path,
                            "old_date": old_date,
                            "update_time": next(
                                (item.get("update_time", old_date) for item in json_list if item.get("url") == url),
                                old_date),
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
                            "update_time": next(
                                (item.get("update_time", old_date) for item in json_list if item.get("url") == url),
                                old_date),
                            "is_update": next(
                                (item.get("is_update", "1") for item in json_list if item.get("url") == url), "1")
                        }
                        json_list2w.append(json_data)

    # 写入right_urls.json文件（按更新状态、更新时间、旧日期排序）
    with open(json_path, "w", encoding="utf-8") as json_file:
        print(f"right json files has {json_list2w.__len__()}")
        json_string = {
            "json_list_len": json_list2w.__len__(),
            "json_list": sorted(json_list2w,
                                key=lambda x: (-int(x['is_update']), datetime.strptime(x['update_time'], '%Y-%m-%d'),
                                               datetime.strptime(x['old_date'], '%Y-%m-%d'))),
        }
        json.dump(json_string, json_file, indent=4, ensure_ascii=False)

    # 写入error_urls.json文件
    with open(error_json_path, "w", encoding="utf-8") as error_json_file:
        print(f"error json files has {error_json_list.__len__()}")
        json_string = {
            "json_list_len": error_json_list.__len__(),
            "json_list": error_json_list,
        }
        json.dump(json_string, error_json_file, indent=4, ensure_ascii=False)


if __name__ == "__main__":
    # 调用主函数
    record_urls()
    # 等待用户输入后退出
    input("ok")