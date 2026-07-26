"""
视频压缩工具 - 使用NVIDIA GPU加速压缩视频

功能说明:
    本脚本提供交互式界面，用于选择视频压缩方案（H.265或AV1）并使用NVIDIA GPU进行硬件加速压缩。
    支持使用hevc_nvenc（H.265）和av1_nvenc（AV1）编码器。
    根据输入视频码率动态调整压缩参数，确保输出码率接近目标码率。

压缩方案:
    1. H.265: 使用hevc_nvenc编码器，基于目标码率动态调整质量因子
    2. AV1: 使用av1_nvenc编码器，基于目标码率动态调整质量因子

使用方式:
    直接运行本脚本，按提示选择压缩方案并输入视频文件路径

CQ值计算公式说明:
    CQ (Constant Quality) 值是NVENC编码器的恒定质量参数，范围0-51，值越小质量越高。
    
    关键经验: CQ值与输出码率呈近似对数关系，CQ每增加1，码率大约下降12%。
    例如: CQ=26时约输出2Mbps，CQ=30时约输出1Mbps，CQ=34时约输出500kbps。
    
    计算公式:
        ratio = 源码率 / 目标码率
        cq = base_cq + int(log2(ratio) * 0.25)
        
        最终 cq 值限制在 0-51 范围内
        
    参数含义:
        - base_cq: 基础质量因子（H.265为26，AV1为36），对应目标码率下的标准质量
        - ratio: 源码率与目标码率的比值，反映压缩需求程度
        - log2(ratio): 以2为底的对数，ratio=4表示需要压缩4倍（log2=2）
        - 系数0.25: 经验系数，log2每增加4（压缩16倍），CQ增加1
        
    示例:
        场景1: 源码率8Mbps，目标码率2Mbps（ratio=4，log2=2）
            cq = 26 + int(2 * 0.25) = 26 + 0 = 26
        
        场景2: 源码率4Mbps，目标码率2Mbps（ratio=2，log2=1）
            cq = 26 + int(1 * 0.25) = 26 + 0 = 26
        
        场景3: 源码率1Mbps，目标码率2Mbps（ratio=0.5，log2=-1）
            cq = 26 + int(-1 * 0.25) = 26 + 0 = 26
"""

import ffmpeg
import os
import math


TARGET_BITRATE = '2M'

CODECS = {
    '1': {
        'name': 'H.265',
        'vcodec': 'hevc_nvenc',
        'rc': 'vbr',
        'base_cq': 26,
        'preset': 'p5',
        'acodec': 'copy',
        'suffix': '_H265'
    },
    '2': {
        'name': 'AV1',
        'vcodec': 'av1_nvenc',
        'rc': 'vbr',
        'base_cq': 36,
        'preset': 'p5',
        'acodec': 'copy',
        'suffix': '_av1'
    }
}


def parse_bitrate(bitrate_str):
    """
    解析码率字符串为整数（单位：bps）
    
    支持的格式:
        - '2M' 或 '2m' -> 2 * 1000000 = 2000000 bps
        - '1500k' 或 '1500K' -> 1500 * 1000 = 1500000 bps
        - '500000' -> 直接转换为整数 500000 bps
    
    Args:
        bitrate_str: 码率字符串，如 '2M', '1500k', '500000'
    
    Returns:
        int: 码率值（bps），解析失败返回0
    """
    if bitrate_str is None:
        return 0
    
    bitrate_str = bitrate_str.strip().upper()
    
    if bitrate_str.endswith('M'):
        return int(float(bitrate_str[:-1]) * 1000000)
    elif bitrate_str.endswith('K'):
        return int(float(bitrate_str[:-1]) * 1000)
    else:
        try:
            return int(bitrate_str)
        except ValueError:
            return 0


def get_video_bitrate(input_file):
    """
    获取视频文件的视频流码率
    
    使用ffmpeg.probe()获取视频文件的元数据，提取视频流的bit_rate字段。
    
    Args:
        input_file: 输入视频文件路径
    
    Returns:
        int: 视频码率（bps），获取失败返回0
    """
    try:
        probe = ffmpeg.probe(input_file)
        video_streams = [stream for stream in probe['streams'] if stream['codec_type'] == 'video']
        if video_streams:
            bitrate = video_streams[0].get('bit_rate')
            return parse_bitrate(bitrate)
    except Exception as e:
        print(f"⚠️ 获取视频码率失败: {e}")
    
    return 0


def calculate_cq(source_bitrate, target_bitrate, base_cq):
    """
    根据源码率和目标码率计算合适的CQ值
    
    CQ值计算逻辑:
        1. 计算源码率与目标码率的比值 ratio
        2. 使用log2对数变换将线性比例转换为非线性调整
        3. 根据经验公式调整基础CQ值
        4. 限制CQ值在0-51范围内（NVENC编码器的有效范围）
    
    关键原理:
        CQ值与输出码率呈近似对数关系，CQ每增加1，码率大约下降12%。
        使用log2变换更直观，因为log2(ratio)表示压缩的倍数等级。
    
    计算公式:
        ratio = source_bitrate / target_bitrate
        cq = base_cq + int(log2(ratio) * 0.25)
        
        最终: cq = max(0, min(51, cq))
    
    参数含义:
        - base_cq: 基础质量因子（H.265为26，AV1为36），对应目标码率下的标准质量
        - ratio: 源码率与目标码率的比值，反映压缩需求程度
        - log2(ratio): 以2为底的对数，ratio=4表示需要压缩4倍（log2=2）
        - 系数0.25: 经验系数，log2每增加4（压缩16倍），CQ增加1
    
    示例:
        场景1: 源码率8Mbps，目标码率2Mbps（ratio=4，log2=2）
            cq = 26 + int(2 * 0.25) = 26 + 0 = 26
        
        场景2: 源码率4Mbps，目标码率2Mbps（ratio=2，log2=1）
            cq = 26 + int(1 * 0.25) = 26 + 0 = 26
        
        场景3: 源码率1Mbps，目标码率2Mbps（ratio=0.5，log2=-1）
            cq = 26 + int(-1 * 0.25) = 26 + 0 = 26
    
    Args:
        source_bitrate: 源码率（bps）
        target_bitrate: 目标码率（bps）
        base_cq: 基础cq值（H.265为26，AV1为36）
    
    Returns:
        int: 计算后的cq值（0-51）
    """
    if source_bitrate == 0 or target_bitrate == 0:
        return base_cq
    
    ratio = source_bitrate / target_bitrate
    
    cq = base_cq + int(math.log2(ratio) * 0.25)
    
    cq = max(0, min(51, cq))
    
    return cq


def verify_video(file_path):
    """
    验证视频文件完整性
    
    使用ffmpeg.probe()检查视频文件是否可以正常读取，验证内容包括：
    1. 文件是否存在且大小大于0
    2. 是否包含至少一个视频流
    3. 是否可以正常读取视频元数据（时长、码率等）
    4. 视频时长是否大于0（排除损坏的空文件）
    
    Args:
        file_path: 视频文件路径
        
    Returns:
        bool: True表示视频完整可用，False表示视频损坏或不可用
    """
    # 检查文件是否存在
    if not os.path.exists(file_path):
        print(f"❌ 文件不存在: {file_path}")
        return False
    
    # 检查文件大小
    file_size = os.path.getsize(file_path)
    if file_size == 0:
        print(f"❌ 文件为空（大小为0）: {file_path}")
        return False
    
    try:
        # 使用ffmpeg.probe()获取视频元数据，这会解析文件并验证其完整性
        probe = ffmpeg.probe(file_path)
        
        # 检查是否包含视频流
        video_streams = [stream for stream in probe['streams'] if stream['codec_type'] == 'video']
        if not video_streams:
            print(f"❌ 文件不包含视频流: {file_path}")
            return False
        
        # 检查视频时长
        duration = float(probe.get('format', {}).get('duration', 0))
        if duration <= 0:
            print(f"❌ 视频时长无效（<=0）: {file_path}")
            return False
        
        # 获取视频信息用于显示
        video_info = video_streams[0]
        codec_name = video_info.get('codec_name', 'unknown')
        resolution = f"{video_info.get('width', '?')}x{video_info.get('height', '?')}"
        
        print(f"✅ 视频验证通过")
        print(f"   文件大小: {file_size // 1024 // 1024} MB")
        print(f"   时长: {int(duration // 60)}分{int(duration % 60)}秒")
        print(f"   编码: {codec_name}")
        print(f"   分辨率: {resolution}")
        
        return True
        
    except ffmpeg.Error as e:
        # FFmpeg无法解析文件，说明文件损坏
        error_msg = e.stderr.decode() if e.stderr else str(e)
        print(f"❌ FFmpeg解析失败，视频可能损坏: {error_msg}")
        return False
    except Exception as e:
        # 其他未知错误
        print(f"❌ 验证视频时发生错误: {e}")
        return False


def delete_original(input_file, output_file):
    """
    删除原始视频文件
    
    在删除前进行双重确认：
    1. 确认输入文件和输出文件不是同一个文件
    2. 再次确认输入文件存在
    
    Args:
        input_file: 原始视频文件路径
        output_file: 压缩后的视频文件路径
        
    Returns:
        bool: True表示删除成功，False表示删除失败或被取消
    """
    # 安全检查：确保输入和输出不是同一个文件
    if input_file == output_file:
        print("❌ 错误：输入文件和输出文件相同，无法删除")
        return False
    
    # 确认输入文件存在
    if not os.path.exists(input_file):
        print(f"❌ 原始文件不存在: {input_file}")
        return False
    
    try:
        # 删除原始文件
        os.remove(input_file)
        print(f"🗑️ 已删除原始文件: {os.path.basename(input_file)}")
        return True
    except Exception as e:
        print(f"❌ 删除原始文件失败: {e}")
        return False


def compress_video(input_file, codec_key, target_bitrate=TARGET_BITRATE, auto_delete=False):
    """
    压缩视频文件
    
    压缩流程:
        1. 检查输入文件是否存在
        2. 获取压缩方案配置
        3. 计算目标码率和源码率
        4. 根据码率比值动态计算CQ值
        5. 构建FFmpeg命令并执行
        6. 获取输出文件码率并显示结果
        7. 验证压缩后视频完整性
        8. 如果验证通过且auto_delete=True，删除原视频
        
    Args:
        input_file: 输入视频文件路径
        codec_key: 压缩方案键值（'1'表示H.265，'2'表示AV1）
        target_bitrate: 目标视频码率，如 '2M', '1500k'
        auto_delete: 是否自动删除原视频（默认False，需要用户确认）
    
    FFmpeg参数说明:
        - vcodec: 视频编码器（hevc_nvenc或av1_nvenc）
        - rc: 码率控制模式（vbr = Variable Bit Rate）
        - cq: 恒定质量因子（0-51，值越小质量越高）
        - b:v: 视频码率（设为0表示不限制最大码率）
        - preset: 编码预设（p5为平衡速度与质量）
        - acodec: 音频编码器（copy表示直接复制音频流）
    """
    if not os.path.exists(input_file):
        print(f"❌ 输入文件 {input_file} 不存在")
        return

    codec = CODECS[codec_key]
    base_name = os.path.splitext(input_file)[0]
    output_file = f"{base_name}{codec['suffix']}.mp4"

    target_bitrate_bps = parse_bitrate(target_bitrate)
    source_bitrate_bps = get_video_bitrate(input_file)
    
    cq = calculate_cq(source_bitrate_bps, target_bitrate_bps, codec['base_cq'])

    print(f"📥 输入文件: {input_file}")
    print(f"📤 输出文件: {output_file}")
    print(f"🎯 编码方案: {codec['name']}")
    print(f"📊 源码率: {source_bitrate_bps // 1000} kbps")
    print(f"🎯 目标码率: {target_bitrate}")
    print(f"⚙️ 计算CQ值: {cq}")
    print("🚀 开始压缩...")

    try:
        stream = ffmpeg.input(input_file)
        stream = ffmpeg.output(
            stream,
            output_file,
            vcodec=codec['vcodec'],
            rc=codec['rc'],
            cq=cq,
            **{'b:v': '0'},
            preset=codec['preset'],
            acodec=codec['acodec']
        )
        
        ffmpeg.run(stream, overwrite_output=True)
        
        output_bitrate_bps = get_video_bitrate(output_file)
        print("✅ 压缩成功！")
        print(f"输出文件: {output_file}")
        print(f"📊 输出码率: {output_bitrate_bps // 1000} kbps")
        
        # 验证压缩后视频的完整性
        print("\n🔍 正在验证压缩后视频完整性...")
        if verify_video(output_file):
            # 验证通过，询问是否删除原视频
            if auto_delete:
                # 自动删除模式，直接删除
                delete_original(input_file, output_file)
            else:
                # 交互式模式，询问用户
                while True:
                    choice = input("\n是否删除原始视频文件？(y/n): ").strip().lower()
                    if choice in ('y', 'yes'):
                        delete_original(input_file, output_file)
                        break
                    elif choice in ('n', 'no'):
                        print("✓ 保留原始视频文件")
                        break
                    else:
                        print("❌ 无效选项，请输入 y 或 n")
        else:
            # 验证失败，保留原视频
            print("❌ 压缩后视频验证失败，保留原始视频文件")
            
    except ffmpeg.Error as e:
        print(f"❌ 压缩失败 - FFmpeg错误:")
        error_msg = e.stderr.decode() if e.stderr else str(e)
        print(f"stderr: {error_msg}")
        
    except Exception as e:
        print(f"❌ 发生未知错误: {e}")


def select_codec():
    """
    交互式选择压缩方案
    
    显示压缩方案菜单，获取用户选择并验证输入有效性。
    
    Returns:
        str: 用户选择的压缩方案键值（'1'或'2'）
    """
    print("=" * 40)
    print("    视频压缩方案选择")
    print("=" * 40)
    
    for key, codec in CODECS.items():
        print(f"  {key}. {codec['name']}")
    
    print("=" * 40)

    while True:
        choice = input("请选择压缩方案 (1/2): ").strip()
        if choice in CODECS:
            return choice
        print("❌ 无效选项，请重新选择")


def set_target_bitrate():
    """
    设置目标码率
    
    交互式获取用户输入的目标码率，支持多种格式。
    
    Returns:
        str: 用户设置的目标码率，如 '2M', '1500k'，默认返回TARGET_BITRATE
    """
    while True:
        user_input = input(f"请输入目标视频码率（默认: {TARGET_BITRATE}）: ").strip()
        if not user_input:
            return TARGET_BITRATE
        
        try:
            if parse_bitrate(user_input) > 0:
                return user_input
            else:
                print("❌ 无效的码率格式，请使用如 '2M', '1500k', '500000' 等格式")
        except:
            print("❌ 无效的码率格式，请使用如 '2M', '1500k', '500000' 等格式")


if __name__ == "__main__":
    codec_key = select_codec()
    
    target_bitrate = set_target_bitrate()
    
    user_input = input("请输入需要压缩的视频文件路径: ").strip('"')
    
    compress_video(user_input, codec_key, target_bitrate)