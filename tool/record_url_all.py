from datetime import datetime
import json
import os
from add_url2file import *


def record_urls():
    root_path = r"D:\Settings\TikTok\video\post"
    json_path = r"D:\Settings\TikTok\video\right_urls.json"
    error_json_path = r"D:\Settings\TikTok\video\error_urls.json"

    json_list2w = []
    error_json_list = []
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    json_list = data["json_list"]

    for root, dirs, files in os.walk(root_path):
        for file in files:
            if file.endswith(".json"):
                url_path = os.path.join(root, file)
                folder_path = root
                with open(url_path, "r", encoding="utf-8") as f__:
                    data = json.load(f__)
                    url = data["url"]
                    old_date = data["old_date"]

                    if not url:

                        json_data = {
                            "url": url,
                            "local_path": os.path.join(root, file),
                            "folder_path": folder_path,
                            "old_date": old_date,
                            "is_update": "1"
                        }

                        error_json_list.append(json_data)

                    else:

                        json_data = {
                            "url": url,
                            "local_path": os.path.join(root, file),
                            "folder_path": folder_path,
                            "old_date": next(
                                (item.get("old_date", old_date) for item in json_list if item.get("url") == url),
                                old_date),
                            "is_update": next(
                                (item.get("is_update", "1") for item in json_list if item.get("url") == url), "1")
                        }

                        json_list2w.append(json_data)

    with open(json_path, "w", encoding="utf-8") as json_file:
        print(f"right json files has {json_list2w.__len__()}")
        json_string = {
            "json_list_len": json_list2w.__len__(),
            "json_list": sorted(json_list2w,
                                key=lambda x: (-int(x['is_update']), datetime.strptime(x['old_date'], '%Y-%m-%d'))),
        }
        json.dump(json_string, json_file, indent=4, ensure_ascii=False)

    with open(error_json_path, "w", encoding="utf-8") as error_json_file:
        print(f"error json files has {error_json_list.__len__()}")
        json_string = {
            "json_list_len": error_json_list.__len__(),
            "json_list": error_json_list,
        }
        json.dump(json_string, error_json_file, indent=4, ensure_ascii=False)


if __name__ == "__main__":
    record_urls()
    # main()
