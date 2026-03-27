#!/usr/bin/env python
# show_progress.py - 无第三方依赖的稳定进度条
import sys
import time
import socket
import threading
import tempfile
import os
import contextlib
import errno

class StableProgressBar:
    """稳定、无闪烁的文本进度条"""

    def __init__(self, total_duration, desc="转换进度"):
        self.total_duration = total_duration
        self.desc = desc
        self.current_time = 0.0
        self.last_percentage = -1  # 记录上次显示的百分比，用于减少刷新
        self.start_time = time.time()
        self.last_update_time = self.start_time
        self.refresh_interval = 0.3  # 每0.3秒最多刷新一次进度条，大大减少闪烁
        self.completed = False

        # 打印初始状态
        self._print_progress(force=True)

    def _print_progress(self, force=False):
        """内部方法：打印或更新进度条。force=True 强制刷新。"""
        now = time.time()

        # 控制刷新频率
        if not force and (now - self.last_update_time) < self.refresh_interval:
            return

        self.last_update_time = now
        elapsed = now - self.start_time

        # 计算进度百分比
        if self.total_duration > 0:
            percentage = (self.current_time / self.total_duration) * 100
        else:
            percentage = 0

        # 只在进度有显著变化（>=0.1%）或强制刷新时才更新显示
        if not force and abs(percentage - self.last_percentage) < 0.1:
            return

        self.last_percentage = percentage

        # 计算编码速度和剩余时间
        if self.current_time > 0 and elapsed > 0:
            speed = self.current_time / elapsed  # 倍速
            if speed > 0:
                remaining = (self.total_duration - self.current_time) / speed
            else:
                remaining = 0
        else:
            speed = 0.0
            remaining = 0

        # 构建进度条和输出字符串（使用固定宽度避免抖动）
        bar_length = 30
        filled_length = int(bar_length * percentage / 100)
        bar = '█' * filled_length + '░' * (bar_length - filled_length)

        # 格式化输出，使用固定宽度字段
        status_line = (f"\r{self.desc}: [{bar}] {percentage:6.2f}% | "
                       f"时间: {self.current_time:6.1f}/{self.total_duration:6.1f}s | "
                       f"速度: {speed:4.2f}x | "
                       f"剩余: {remaining:5.0f}s")
        sys.stdout.write(status_line)
        sys.stdout.flush()

    def update(self, current_time):
        """更新当前时间并刷新显示"""
        self.current_time = min(current_time, self.total_duration)
        self._print_progress()

    def complete(self):
        """标记转换完成，显示最终状态"""
        if not self.completed:
            self.completed = True
            self.current_time = self.total_duration
            # 强制刷新一次完成状态
            self._print_progress(force=True)
            sys.stdout.write('\n')  # 完成后换行
            sys.stdout.flush()


def _do_watch_progress(sock, handler):
    """监听FFmpeg进度信息的工作线程"""
    sock.settimeout(5.0)  # 设置超时，防止线程永久阻塞
    try:
        conn, addr = sock.accept()
        conn.settimeout(2.0)
    except socket.timeout:
        # print("进度监听: 等待连接超时")
        return
    except OSError as e:
        # print(f"进度监听: 连接错误 {e}")
        return

    buffer = b''
    try:
        while True:
            try:
                # 接收数据
                chunk = conn.recv(512)
                if not chunk:
                    break  # 连接关闭

                buffer += chunk
                lines = buffer.split(b'\n')

                # 处理所有完整的行（最后一行可能不完整，放回buffer）
                for line in lines[:-1]:
                    if line.strip():  # 跳过空行
                        try:
                            line_str = line.decode('utf-8', errors='ignore').strip()
                            if '=' in line_str:
                                key, value = line_str.split('=', 1)
                                # 调用处理函数
                                handler(key, value)
                        except Exception:
                            # 忽略单行解析错误
                            pass

                buffer = lines[-1]  # 保存不完整的行供下次处理

            except socket.timeout:
                # 超时是正常的，继续循环
                continue
            except (ConnectionResetError, BrokenPipeError):
                break  # 连接异常中断
            except Exception:
                # 其他异常也退出循环
                break
    finally:
        conn.close()
        # print("进度监听: 连接已关闭")


@contextlib.contextmanager
def watch_progress(handler):
    """创建并管理进度监听服务器"""
    # 创建TCP socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    # 绑定到本地回环地址和随机可用端口
    sock.bind(('127.0.0.1', 0))
    sock.listen(1)
    host, port = sock.getsockname()

    # 启动监听线程
    listener_thread = threading.Thread(
        target=_do_watch_progress,
        args=(sock, handler),
        daemon=True  # 设置为守护线程，主程序退出时自动结束
    )
    listener_thread.start()

    try:
        # 返回给调用者的地址 (如 "127.0.0.1:12345")
        yield f"{host}:{port}"
    finally:
        # 清理：关闭socket会终止accept()阻塞，使线程自然结束
        sock.close()
        listener_thread.join(timeout=1.0)


def safe_float_convert(s, default=0.0):
    """安全地将字符串转换为浮点数，处理 'N/A' 等无效值"""
    if not s:
        return default
    try:
        return float(s)
    except (ValueError, TypeError):
        return default


@contextlib.contextmanager
def show_progress(total_duration, desc="转换进度"):
    """主进度条上下文管理器"""
    progress_bar = StableProgressBar(total_duration, desc)

    def handle_ffmpeg_update(key, value):
        """处理FFmpeg发来的进度更新"""
        if key == 'out_time_ms':
            # 将微秒转换为秒
            time_us = safe_float_convert(value)
            if time_us > 0:
                time_sec = time_us / 1_000_000.0
                progress_bar.update(time_sec)
        elif key == 'progress' and value == 'end':
            # FFmpeg处理结束
            progress_bar.complete()
        # 可以处理其他键，如frame、fps等，用于更详细的显示

    # 启动进度监听服务器
    with watch_progress(handle_ffmpeg_update) as socket_address:
        # 将地址（如"127.0.0.1:54321"）返回给调用者
        yield socket_address

    # 上下文退出后，确保进度条显示完成（如果还没完成的话）
    if not progress_bar.completed:
        progress_bar.complete()


