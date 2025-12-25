import json

new_url_file = r"D:\Settings\TikTok\video\new_url.json"
right_url_file = r"D:\Settings\TikTok\video\right_urls.json"


def url_in_list(url, list):
    for item in list:
        # 从每个字典中获取`url`键对应的列表
        url_sublist = item.get("url", [])  # 使用.get()方法安全获取，如果键不存在则返回空列表
        # 判断目标URL是否在当前项目的URL列表中
        if url in url_sublist:
            return True
    return False


if __name__ == "__main__":
    while True:
        o_url = input("url:")

        url = o_url.split('?')[0]

        try:
            with open(new_url_file, "r", encoding="utf-8") as f:
                data1 = json.load(f)
            urls = data1["url"]

            with open(right_url_file, "r", encoding="utf-8") as f:
                data2 = json.load(f)

            json_list = data2["json_list"]

            if url in urls or url_in_list(url, json_list):
                print(f"url has already been added: {url}")

            else:
                urls.append(url)

                data2w = {
                    "url": urls,
                }

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
