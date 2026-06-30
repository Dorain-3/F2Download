"""
URL添加工具 - 用于向抖音视频项目添加新的URL链接

功能说明:
    本脚本提供一个交互式界面，用于将新的抖音视频URL添加到待处理列表中。
    支持去重检查，避免重复添加已存在的URL。

工作流程:
    1. 从配置文件获取项目根目录路径
    2. 加载new_url.json（待处理URL列表）和right_urls.json（已配置URL列表）
    3. 接收用户输入的URL，自动去除查询参数
    4. 检查URL是否已存在于两个列表中
    5. 如果不存在，添加到new_url.json并保存

文件结构:
    new_url.json:      {"url": ["url1", "url2", ...]}
    right_urls.json:   {"json_list": [{"url": [...], ...}, ...]}

使用方式:
    直接运行本脚本，按提示输入URL即可
"""

import json
from read_cfg import get_config


def url_in_list(url, json_list):
    """
    检查URL是否已存在于right_urls.json的json_list中
    
    Args:
        url: 要检查的URL字符串
        json_list: right_urls.json中的json_list列表
        
    Returns:
        bool: URL是否存在
    """
    # 遍历json_list中的每个字典项
    for item in json_list:
        # 从每个字典中获取'url'键对应的列表
        url_sublist = item.get("url", [])
        # 判断目标URL是否在当前项目的URL列表中
        if url in url_sublist:
            return True
    return False


if __name__ == "__main__":
    # 加载配置
    cfg = get_config()
    
    # 获取项目根目录路径
    root_dir = cfg.root_path
    
    # 构建文件路径
    new_url_file = root_dir / "new_url.json"      # 待处理URL文件
    right_url_file = root_dir / "right_urls.json"  # 已配置URL文件

    # 进入循环，持续接收用户输入
    while True:
        # 提示用户输入URL
        o_url = input("url:")
        
        # 去除URL中的查询参数（保留?之前的部分）
        url = o_url.split('?')[0]

        try:
            # 读取new_url.json文件
            with open(new_url_file, "r", encoding="utf-8") as f:
                data1 = json.load(f)
            urls = data1["url"]

            # 读取right_urls.json文件
            with open(right_url_file, "r", encoding="utf-8") as f:
                data2 = json.load(f)
            json_list = data2["json_list"]

            # 检查URL是否已存在
            if url in urls or url_in_list(url, json_list):
                print(f"url has already been added: {url}")
            else:
                # 将新URL添加到列表
                urls.append(url)
                
                # 构建要写入的数据结构
                data2w = {
                    "url": urls,
                }
                
                # 写回new_url.json文件
                with open(new_url_file, "w", encoding="utf-8") as f:
                    json.dump(data2w, f, ensure_ascii=False, indent=4)
                
                print(f"url has added: {url}")

        except FileNotFoundError as e:
            print(f"File not found: {e}")
        except json.decoder.JSONDecodeError as e:
            print(f"Decode error: {e}")
        except KeyError as e:
            print(f"Key error: {e}")
        except Exception as e:
            print(e.args, type(e))