"""
配置文件读取模块 - 为抖音视频下载项目提供统一的配置管理

功能说明:
    本模块使用单例模式实现配置文件的加载和管理，确保配置只加载一次。
    支持通过环境变量指定YAML配置文件，并从中读取路径和设置参数，
    供项目中其他模块统一调用。

主要组件:
    - Config类: 配置管理类，封装配置加载、验证和获取逻辑
    - load_config(): 加载配置文件的函数
    - get_config(): 获取已加载配置的便捷函数

配置项说明:
    paths.root_path:        项目根目录路径
    paths.download_path:    下载文件存放路径
    paths.update_path:      right_urls.json路径（兼容旧配置项）
    paths.backup_path:      备份文件路径
    paths.log_path:         日志文件路径
    paths.download:         下载临时目录路径
    paths.new_url_path:     new_url.json路径（可选）
    paths.right_urls_path:  right_urls.json路径（可选，优先于update_path）
    paths.error_urls_path:  error_urls.json路径（可选）
    paths.post_path:        视频归档目录（可选）
    paths.image_source_path: 图片整理源目录（可选）
    paths.image_target_path: 图片整理目标目录（可选）
    settings.update_max_index: 最大更新数量
    image_extensions:       图片扩展名列表

使用方式:
    先设置环境变量 DY_CONFIG_PATH，值为YAML配置文件路径，然后：

    from dy.main.read_cfg import get_config
    
    cfg = get_config()
    print(cfg.root_path)
    print(cfg.update_max_index)
"""

import os
from pathlib import Path
from typing import Optional
import yaml


CONFIG_PATH_ENV = "DY_CONFIG_PATH"


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
        self.new_url_path: Optional[Path] = None
        self.right_urls_path: Optional[Path] = None
        self.error_urls_path: Optional[Path] = None
        self.post_path: Optional[Path] = None
        self.image_source_path: Optional[Path] = None
        self.image_target_path: Optional[Path] = None
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
            config_path: 配置文件路径。为None时从DY_CONFIG_PATH环境变量读取
            
        Returns:
            Config: 加载完成的配置实例
            
        Raises:
            ValueError: 配置文件解析错误
            FileNotFoundError: 配置文件不存在
        """
        # 如果已经加载且未指定新路径，直接返回
        if self._loaded and config_path is None:
            return self

        # 未显式传入路径时，统一从环境变量读取配置文件位置
        if config_path is None:
            config_path_value = os.environ.get(CONFIG_PATH_ENV)
            if not config_path_value:
                raise EnvironmentError(
                    f"未设置环境变量 {CONFIG_PATH_ENV}，请将其设置为YAML配置文件路径"
                )
            config_path = Path(os.path.expandvars(config_path_value)).expanduser()
        else:
            config_path = Path(config_path).expanduser()

        if not config_path.is_absolute():
            config_path = config_path.resolve()

        # 记录配置文件路径
        self.config_path = config_path

        try:
            # 读取并解析YAML配置文件
            with open(config_path, 'r', encoding='utf-8') as file:
                app_config = yaml.safe_load(file) or {}

            if not isinstance(app_config, dict):
                raise ValueError(f"配置文件根节点必须是对象: {config_path}")

            # 提取paths和settings配置项
            paths = app_config.get('paths', {})
            settings = app_config.get('settings', {})

            if not isinstance(paths, dict):
                raise ValueError("配置项 paths 必须是对象")
            if not isinstance(settings, dict):
                raise ValueError("配置项 settings 必须是对象")

            # 赋值路径配置
            self.root_path = self._read_path(paths, 'root_path')
            self.download_path = self._read_path(paths, 'download_path')
            self.download_dir = self._read_path(paths, 'download')
            self.backup_path = self._read_path(paths, 'backup_path')
            self.log_path = self._read_path(paths, 'log_path')

            # update_path是旧字段；right_urls_path存在时优先使用新字段
            right_urls_value = paths.get('right_urls_path', paths.get('update_path'))
            self.right_urls_path = self._make_path(right_urls_value, 'right_urls_path')
            self.update_path = self.right_urls_path

            # 以下路径可在YAML中单独覆盖，否则由基础路径统一推导
            self.new_url_path = self._read_path(
                paths, 'new_url_path', self.root_path / 'new_url.json'
            )
            self.error_urls_path = self._read_path(
                paths, 'error_urls_path', self.root_path / 'error_urls.json'
            )
            self.post_path = self._read_path(
                paths, 'post_path', self.root_path / 'post'
            )
            self.image_source_path = self._read_path(
                paths, 'image_source_path', self.download_dir
            )
            self.image_target_path = self._read_path(
                paths, 'image_target_path', self.root_path / 'pic'
            )
            
            # 赋值设置配置
            self.update_max_index = settings.get('update_max_index', 20)
            self.image_extensions = app_config.get('image_extensions', [])

            # 标记已加载
            self._loaded = True

        except yaml.YAMLError as e:
            raise ValueError(f"解析配置文件时出错: {e}")
        except FileNotFoundError:
            raise FileNotFoundError(f"配置文件未找到: {config_path}")

        return self

    def _read_path(self, paths: dict, key: str, default=None) -> Path:
        """读取一个路径配置；可选配置缺失时使用给定默认值。"""
        return self._make_path(paths.get(key, default), key)

    def _make_path(self, value, key: str) -> Path:
        """展开路径中的环境变量，并让相对路径相对于YAML所在目录。"""
        if value is None or str(value).strip() == '':
            raise ValueError(f"缺少路径配置: paths.{key}")

        path = Path(os.path.expandvars(str(value))).expanduser()
        if not path.is_absolute():
            path = self.config_path.parent / path
        return path

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
        config_path: 配置文件路径，为None时从DY_CONFIG_PATH环境变量读取
        
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
