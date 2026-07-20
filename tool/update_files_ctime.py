import os
from datetime import datetime
from pathlib import Path
from win32_setctime import setctime


def batch_set_times_if_older(folder: str, target_str: str):
    """
    遍历 folder 下所有指定扩展名的文件，
    只有当文件的创建时间早于 target_str 时，才将其创建/修改/访问时间设为 target_str。
    """
    dt = datetime.strptime(target_str, "%Y-%m-%d %H:%M:%S")
    target_ts = dt.timestamp()

    count_modified = 0
    count_skipped = 0

    for f in Path(folder).rglob('*'):

        try:
            current_ctime = os.path.getctime(f)  # Windows 下返回创建时间（Unix 时间戳）
            update_time = os.path.getmtime(f)
        except OSError:
            print(f"⚠️ 无法读取创建时间，跳过: {f.name}")
            continue

        if current_ctime >= target_ts:
            # 创建时间不早于目标时间，跳过
            # setctime(str(f), update_time)
            count_skipped += 1
            continue

        # 执行修改
        setctime(str(f), target_ts)  # 改创建时间
        os.utime(f, (target_ts, target_ts))  # 改访问/修改时间
        count_modified += 1
        print(f"✅ 已修改: {f.name}")

    print(f"\n完成。共修改 {count_modified} 个文件，跳过 {count_skipped} 个（创建时间不早于目标时间）。")


if __name__ == "__main__":
    # 请修改这两个变量
    FOLDER = r"C:\Users\31749\Dorain_file\TikTok\Camera"
    TARGET_TIME = "2026-01-01 00:00:00"

    batch_set_times_if_older(FOLDER, TARGET_TIME)
