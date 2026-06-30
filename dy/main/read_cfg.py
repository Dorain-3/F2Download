"""
配置文件读取模块 - 为抖音视频下载项目提供统一的配置管理

功能说明:
    本模块使用单例模式实现配置文件的加载和管理，确保配置只加载一次。
    支持从YAML配置文件中读取路径和设置参数，供项目中其他模块调用。

主要组件:
    - Config类: 配置管理类，封装配置加载、验证和获取逻辑
    - load_config(): 加载配置文件的函数
    - get_config(): 获取已加载配置的便捷函数

配置项说明:
    paths.root_path:        项目根目录路径
    paths.download_path:    下载文件存放路径
    paths.update_path:      更新数据文件路径
    paths.backup_path:      备份文件路径
    paths.log_path:         日志文件路径
    paths.download:         下载临时目录路径
    settings.update_max_index: 最大更新数量
    image_extensions:       图片扩展名列表

使用方式:
    from dy.main.read_cfg import get_config
    
    cfg = get_config()
    print(cfg.root_path)
    print(cfg.update_max_index)
"""

import os
from pathlib import Path
from typing import Optional

import yaml


class Config:
    """
    配置管理类 - 使用单例模式确保全局唯一配置实例
    
    特性:
        - 单例模式，避免重复加载配置文件
        - 支持延迟加载，首次调用时自动加载
        - 提供配置验证方法
        - 所有配置项作为类属性暴露，方便访问
    """
    
    _instance: Optional['Config'] = None
    _loaded: bool = False

    def __init__(self):
        """
        初始化配置类实例
        
        属性说明:
            root_path: 项目根目录路径
            download_path: 下载文件存放路径
            update_path: 更新数据文件路径
            backup_path: 备份文件路径
            log_path: 日志文件路径
            update_max_index: 最大更新数量（默认20）
            config_path: 配置文件路径
            download_dir: 下载临时目录路径
            image_extensions: 图片扩展名列表
        """
        self.root_path: Optional[Path] = None
        self.download_path: Optional[Path] = None
        self.update_path: Optional[Path] = None
        self.backup_path: Optional[Path] = None
        self.log_path: Optional[Path] = None
        self.update_max_index: int = 20
        self.config_path: Optional[Path] = None
        self.download_dir: Optional[Path] = None
        self.image_extensions: list = []

    @classmethod
    def get_instance(cls) -> 'Config':
        """
        获取配置类的单例实例
        
        Returns:
            Config: 配置类的全局唯一实例
        """
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def load(self, config_path: Optional[Path] = None) -> 'Config':
        """
        加载配置文件
        
        Args:
            config_path: 配置文件路径，为None时使用默认路径
            
        Returns:
            Config: 加载完成的配置实例
            
        Raises:
            ValueError: 配置文件解析错误
            FileNotFoundError: 配置文件不存在
        """
        # 如果已经加载且未指定新路径，直接返回
        if self._loaded and config_path is None:
            return self

        # 使用默认配置文件路径（项目根目录下的config.yaml）
        if config_path is None:
            config_path = Path(__file__).parent.parent / "config.yaml"

        # 记录配置文件路径
        self.config_path = config_path

        try:
            # 读取并解析YAML配置文件
            with open(config_path, 'r', encoding='utf-8') as file:
                app_config = yaml.safe_load(file)

            # 提取paths和settings配置项
            PATHS = app_config.get('paths', {})
            SETTINGS = app_config.get('settings', {})

            # 赋值路径配置
            self.root_path = Path(PATHS.get('root_path'))
            self.download_path = Path(PATHS.get('download_path'))
            self.update_path = Path(PATHS.get('update_path'))
            self.backup_path = Path(PATHS.get('backup_path'))
            self.log_path = Path(PATHS.get('log_path'))
            self.download_dir = Path(PATHS.get('download'))
            
            # 赋值设置配置
            self.update_max_index = SETTINGS.get('update_max_index', 20)
            self.image_extensions = app_config.get('image_extensions', [])

            # 标记已加载
            self._loaded = True

        except yaml.YAMLError as e:
            raise ValueError(f"解析配置文件时出错: {e}")
        except FileNotFoundError:
            raise FileNotFoundError(f"配置文件未找到: {config_path}")

        return self

    def validate(self) -> bool:
        """
        验证配置的有效性
        
        检查项:
            - 更新数据文件是否存在
            - 备份目录是否存在，不存在则创建
            
        Returns:
            bool: 验证是否通过
        """
        # 检查更新数据文件是否存在
        if not os.path.exists(self.update_path):
            print(f"错误：源文件 '{self.update_path}' 不存在")
            return False

        # 检查备份目录是否存在，不存在则创建
        if not os.path.exists(self.backup_path):
            os.makedirs(self.backup_path)
            print(f"创建目标目录: {self.backup_path}")

        return True


# 全局配置实例
_config: Optional[Config] = None


def load_config(config_path: Optional[Path] = None) -> Config:
    """
    加载配置文件（便捷函数）
    
    Args:
        config_path: 配置文件路径，为None时使用默认路径
        
    Returns:
        Config: 加载完成的配置实例
    """
    global _config
    _config = Config.get_instance().load(config_path)
    return _config


def get_config() -> Config:
    """
    获取已加载的配置实例（便捷函数）
    
    如果配置尚未加载，会自动调用load_config()进行加载。
    
    Returns:
        Config: 配置实例
    """
    global _config
    if _config is None:
        _config = load_config()
    return _config