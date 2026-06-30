"""
MP4文件检查工具 - 快速检测并自动删除无效的MP4文件

功能说明:
    本脚本用于快速检查MP4文件的有效性，自动识别并删除以下类型的无效文件：
    - HTML错误页面（以'<html'开头）
    - 文本内容文件（非MP4格式）
    - 损坏的MP4文件
    - 空文件
    - 读取错误或权限问题的文件
    
    使用多线程加速检查过程，支持将无效文件移至回收站或永久删除。

主要组件:
    - CheckResult: 检查结果数据类
    - FastMP4Checker: 快速MP4文件检测器类
    
使用方式:
    直接运行本脚本，默认检查指定目录下的所有MP4文件
"""

import os
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from typing import List, Dict
import time
import send2trash


@dataclass
class CheckResult:
    """检查结果数据类 - 存储单个文件的检查结果"""
    file_path: str        # 文件路径
    is_valid: bool        # 是否为有效MP4文件
    reason: str          # 检查结果原因
    file_size: int       # 文件大小（字节）
    check_time: float    # 检查耗时（秒）
    deleted: bool = False  # 是否已删除


class FastMP4Checker:
    """快速MP4文件检测器 - 自动删除无效文件"""

    def __init__(self, chunk_size: int = 20, max_workers: int = 20):
        """
        初始化检测器
        
        Args:
            chunk_size: 读取的文件头大小（字节），默认20字节
            max_workers: 最大线程数，默认20
        """
        self.chunk_size = chunk_size
        self.max_workers = max_workers
        # 默认开启自动删除，删除到回收站，删除所有无效类型
        self.auto_delete = True
        self.delete_to_recycle = True  # True=移到回收站, False=永久删除
        self.delete_types = ['html', 'other', 'error']  # 删除所有无效类型

        # 统计信息字典
        self.stats = {
            'total': 0,
            'valid': 0,
            'invalid_html': 0,
            'invalid_other': 0,
            'errors': 0,
            'deleted': 0,
            'delete_failed': 0
        }

    def quick_check_single(self, file_path: str) -> CheckResult:
        """
        快速检查单个文件
        
        通过读取文件头判断文件类型：
        - 空文件：文件大小为0
        - HTML内容：以'<'开头且包含<html/head/body标签
        - 正常MP4：包含'ftyp'标识
        
        Args:
            file_path: 文件路径
            
        Returns:
            CheckResult: 检查结果对象
        """
        start_time = time.time()

        try:
            # 获取文件大小
            file_size = os.path.getsize(file_path)

            # 空文件直接判定为无效
            if file_size == 0:
                return CheckResult(
                    file_path=file_path,
                    is_valid=False,
                    reason="空文件",
                    file_size=file_size,
                    check_time=time.time() - start_time
                )

            # 读取文件头
            with open(file_path, 'rb') as f:
                header = f.read(self.chunk_size)

                # 情况1: HTML内容（以'<'开头）
                if header.startswith(b'<'):
                    # 尝试读取更多内容确认
                    if len(header) < 100:
                        more = f.read(80)
                        header += more

                    # 检查是否包含HTML特征
                    header_lower = header.lower()
                    if b'<html' in header_lower or b'<head' in header_lower or b'<body' in header_lower:
                        return CheckResult(
                            file_path=file_path,
                            is_valid=False,
                            reason="HTML内容（可能是302错误页面）",
                            file_size=file_size,
                            check_time=time.time() - start_time
                        )

                # 情况2: 正常MP4文件（包含ftyp）
                if b'ftyp' in header:
                    # 进一步验证MP4类型
                    ftyp_pos = header.find(b'ftyp')
                    if ftyp_pos >= 0 and ftyp_pos + 8 <= len(header):
                        brand = header[ftyp_pos + 4:ftyp_pos + 8].decode('ascii', errors='ignore')
                        return CheckResult(
                            file_path=file_path,
                            is_valid=True,
                            reason=f"正常MP4 (品牌: {brand})",
                            file_size=file_size,
                            check_time=time.time() - start_time
                        )
                    else:
                        return CheckResult(
                            file_path=file_path,
                            is_valid=True,
                            reason="正常MP4",
                            file_size=file_size,
                            check_time=time.time() - start_time
                        )

                # 情况3: 可能是其他格式或损坏
                # 检查是否全为文本（可能是其他错误页面）
                if all(32 <= b <= 126 or b in (9, 10, 13) for b in header[:min(50, len(header))]):
                    return CheckResult(
                        file_path=file_path,
                        is_valid=False,
                        reason="文本内容（非MP4）",
                        file_size=file_size,
                        check_time=time.time() - start_time
                    )

                return CheckResult(
                    file_path=file_path,
                    is_valid=False,
                    reason="非MP4格式或损坏",
                    file_size=file_size,
                    check_time=time.time() - start_time
                )

        except PermissionError:
            return CheckResult(
                file_path=file_path,
                is_valid=False,
                reason="权限不足",
                file_size=0,
                check_time=time.time() - start_time
            )
        except Exception as e:
            return CheckResult(
                file_path=file_path,
                is_valid=False,
                reason=f"读取失败: {str(e)}",
                file_size=0,
                check_time=time.time() - start_time
            )

    def delete_file(self, result: CheckResult) -> bool:
        """
        删除文件
        
        Args:
            result: 检查结果对象
            
        Returns:
            bool: 是否删除成功
        """
        try:
            file_path = result.file_path

            # 检查文件是否存在
            if not os.path.exists(file_path):
                result.reason += " (文件已不存在)"
                return True

            # 根据设置选择删除方式
            if self.delete_to_recycle:
                # 尝试发送到回收站
                try:
                    # 使用send2trash库（需要安装）
                    send2trash.send2trash(file_path)
                    result.reason += " (已移至回收站)"
                except ImportError:
                    # 如果没有send2trash，则永久删除
                    os.remove(file_path)
                    result.reason += " (永久删除 - 未安装send2trash)"
                except Exception as e:
                    # 如果发送到回收站失败，尝试永久删除
                    os.remove(file_path)
                    result.reason += f" (永久删除 - 回收站失败: {str(e)})"
            else:
                # 直接永久删除
                os.remove(file_path)
                result.reason += " (已永久删除)"

            result.deleted = True
            self.stats['deleted'] += 1
            return True

        except PermissionError:
            result.reason += " (删除失败：权限不足)"
            self.stats['delete_failed'] += 1
            return False
        except Exception as e:
            result.reason += f" (删除失败：{str(e)})"
            self.stats['delete_failed'] += 1
            return False

    def should_delete(self, result: CheckResult) -> bool:
        """
        判断是否应该删除该文件
        
        Args:
            result: 检查结果
            
        Returns:
            bool: 是否应该删除
        """
        # 有效文件不删除
        if result.is_valid:
            return False

        # 根据删除类型配置判断
        if "HTML" in result.reason or "文本" in result.reason:
            return 'html' in self.delete_types
        elif "读取失败" in result.reason or "权限" in result.reason:
            return 'error' in self.delete_types
        else:
            return 'other' in self.delete_types

    def find_mp4_files(self, path: str, recursive: bool = True) -> List[str]:
        """
        查找所有MP4文件
        
        Args:
            path: 路径（文件或目录）
            recursive: 是否递归查找子目录
            
        Returns:
            List[str]: MP4文件路径列表
        """
        path_obj = Path(path)

        if path_obj.is_file():
            if path_obj.suffix.lower() == '.mp4':
                return [str(path_obj)]
            return []

        if recursive:
            # 递归查找所有.mp4文件
            return [str(p) for p in path_obj.rglob('*.mp4') if p.is_file()]
        else:
            # 只查找当前目录
            return [str(p) for p in path_obj.glob('*.mp4') if p.is_file()]

    def batch_check(self, paths: List[str], recursive: bool = True) -> Dict[str, List[CheckResult]]:
        """
        批量检查多个路径
        
        Args:
            paths: 路径列表（可以是文件或目录）
            recursive: 是否递归查找子目录
            
        Returns:
            Dict: 按状态分类的结果
        """
        all_files = []
        for path in paths:
            all_files.extend(self.find_mp4_files(path, recursive))

        # 去重
        all_files = list(set(all_files))
        self.stats['total'] = len(all_files)

        # 打印开始信息
        print(f"找到 {len(all_files)} 个MP4文件，开始检查...")
        print(f"⚠️ 自动删除模式已开启：将删除所有无效文件（移至回收站）")
        print(f"   - HTML错误文件 (🌐)")
        print(f"   - 其他异常文件 (⚠️)")
        print(f"   - 读取错误文件 (❌)")
        print("-" * 70)

        # 初始化结果字典
        results = {
            'valid': [],
            'invalid_html': [],
            'invalid_other': [],
            'errors': []
        }

        # 多线程检查
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_file = {executor.submit(self.quick_check_single, file_path): file_path
                              for file_path in all_files}

            for future in as_completed(future_to_file):
                result = future.result()

                # 分类统计
                if result.is_valid:
                    results['valid'].append(result)
                    self.stats['valid'] += 1
                    status = "✅"
                else:
                    if "HTML" in result.reason or "文本" in result.reason:
                        results['invalid_html'].append(result)
                        self.stats['invalid_html'] += 1
                        status = "🌐"
                    elif "读取失败" in result.reason or "权限" in result.reason:
                        results['errors'].append(result)
                        self.stats['errors'] += 1
                        status = "❌"
                    else:
                        results['invalid_other'].append(result)
                        self.stats['invalid_other'] += 1
                        status = "⚠️"

                    # 自动删除逻辑 - 所有无效文件都删除
                    delete_success = self.delete_file(result)
                    if delete_success:
                        status = "🗑️ " + status
                    else:
                        status = "🔒 " + status

                # 实时打印结果
                filename = os.path.basename(result.file_path)
                print(f"{status} {filename:<50} "
                      f"大小: {self._format_size(result.file_size):>8} "
                      f"耗时: {result.check_time * 1000:>6.1f}ms"
                      f"{' [已删除]' if result.deleted else ''}")

        return results

    def _format_size(self, size: int) -> str:
        """
        格式化文件大小
        
        Args:
            size: 文件大小（字节）
            
        Returns:
            str: 格式化后的大小字符串
        """
        if size < 1024:
            return f"{size}B"
        elif size < 1024 * 1024:
            return f"{size / 1024:.1f}KB"
        else:
            return f"{size / (1024 * 1024):.1f}MB"

    def print_summary(self, results: Dict[str, List[CheckResult]], elapsed_time: float):
        """
        打印统计摘要
        
        Args:
            results: 检查结果字典
            elapsed_time: 总耗时（秒）
        """
        print("\n" + "=" * 70)
        print("检查完成！统计结果：")
        print("=" * 70)
        print(f"总文件数:     {self.stats['total']}")
        print(f"正常MP4:      {self.stats['valid']} (✅) - 已保留")
        print(f"HTML错误:     {self.stats['invalid_html']} (🌐) - {'已删除' if self.stats['invalid_html'] > 0 else '-'}")
        print(f"其他异常:     {self.stats['invalid_other']} (⚠️) - {'已删除' if self.stats['invalid_other'] > 0 else '-'}")
        print(f"读取错误:     {self.stats['errors']} (❌) - {'已删除' if self.stats['errors'] > 0 else '-'}")

        print(f"\n删除统计:")
        print(f"  成功删除:   {self.stats['deleted']} 个文件 (🗑️)")
        if self.stats['delete_failed'] > 0:
            print(f"  删除失败:   {self.stats['delete_failed']} 个文件 (🔒)")

        # 计算释放空间
        deleted_size = sum(r.file_size for r in results['invalid_html'] + results['invalid_other'] + results['errors']
                           if r.deleted)
        if deleted_size > 0:
            print(f"  释放空间:   {self._format_size(deleted_size)}")

        print(f"\n处理耗时:     {elapsed_time:.2f} 秒")
        print(f"处理速度:     {self.stats['total'] / elapsed_time:.1f} 文件/秒")

        # 如果有删除失败的文件，列出它们
        if self.stats['delete_failed'] > 0:
            print("\n" + "=" * 70)
            print("删除失败的文件（可能需要手动处理）：")
            for category in ['invalid_html', 'invalid_other', 'errors']:
                for r in results[category]:
                    if not r.deleted and not r.is_valid:
                        print(f"  🔒 {r.file_path}")
                        print(f"     原因: {r.reason}")

    def export_results(self, results: Dict[str, List[CheckResult]], output_file: str = "check_results.txt"):
        """
        导出结果到文件
        
        Args:
            results: 检查结果字典
            output_file: 输出文件路径
        """
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("MP4文件检查结果报告\n")
            f.write("=" * 70 + "\n\n")

            f.write(f"正常文件 (已保留) - {len(results['valid'])}个:\n")
            for r in results['valid']:
                f.write(f"  ✅ {r.file_path} ({self._format_size(r.file_size)})\n")

            f.write(f"\nHTML错误文件 - {len(results['invalid_html'])}个:\n")
            for r in results['invalid_html']:
                delete_status = " [已删除]" if r.deleted else " [删除失败]"
                f.write(f"  🌐 {r.file_path} ({self._format_size(r.file_size)}) - {r.reason}{delete_status}\n")

            f.write(f"\n其他异常文件 - {len(results['invalid_other'])}个:\n")
            for r in results['invalid_other']:
                delete_status = " [已删除]" if r.deleted else " [删除失败]"
                f.write(f"  ⚠️ {r.file_path} ({self._format_size(r.file_size)}) - {r.reason}{delete_status}\n")

            f.write(f"\n读取错误文件 - {len(results['errors'])}个:\n")
            for r in results['errors']:
                delete_status = " [已删除]" if r.deleted else " [删除失败]"
                f.write(f"  ❌ {r.file_path} - {r.reason}{delete_status}\n")

            # 删除统计
            f.write(f"\n" + "=" * 70 + "\n")
            f.write("删除统计:\n")
            f.write(f"  成功删除: {self.stats['deleted']} 个文件\n")
            f.write(f"  删除失败: {self.stats['delete_failed']} 个文件\n")

            deleted_size = sum(
                r.file_size for r in results['invalid_html'] + results['invalid_other'] + results['errors']
                if r.deleted)
            if deleted_size > 0:
                f.write(f"  释放空间: {self._format_size(deleted_size)}\n")

        print(f"\n📄 详细报告已导出到: {output_file}")


def main():
    """主函数 - 默认自动删除所有无效文件"""

    # 要检查的路径（可以根据需要修改）
    target_paths = [
        r'C:\Users\31749\Dorain_file\TikTok\video'
    ]

    # 打印标题信息
    print("=" * 70)
    print("🚀 MP4文件自动检测删除工具")
    print("=" * 70)
    print(f"目标路径: {target_paths}")
    print("运行模式: 自动删除所有无效MP4文件（移至回收站）")
    print("=" * 70 + "\n")

    # 创建检测器
    checker = FastMP4Checker()

    # 记录开始时间
    start_time = time.time()

    # 执行检查
    results = checker.batch_check(
        paths=target_paths,
        recursive=True  # 递归查找子目录
    )

    # 计算耗时
    elapsed_time = time.time() - start_time

    # 打印统计摘要
    checker.print_summary(results, elapsed_time)

    # 导出结果到文件
    checker.export_results(results)


if __name__ == "__main__":
    # 如果需要修改目标路径，可以直接在这里修改
    # 例如: target_paths = ['D:/videos', 'E:/downloads']
    main()