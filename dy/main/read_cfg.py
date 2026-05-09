import os
from pathlib import Path
from typing import Optional

import yaml


class Config:
    _instance: Optional['Config'] = None
    _loaded: bool = False

    def __init__(self):
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
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def load(self, config_path: Optional[Path] = None) -> 'Config':
        if self._loaded and config_path is None:
            return self

        if config_path is None:
            config_path = Path(r'C:\Users\31749\Dorain_file\TikTok\video\config.yaml')

        self.config_path = config_path

        try:
            with open(config_path, 'r', encoding='utf-8') as file:
                app_config = yaml.safe_load(file)

            PATHS = app_config.get('paths', {})
            SETTINGS = app_config.get('settings', {})

            self.root_path = Path(PATHS.get('root_path'))
            self.download_path = Path(PATHS.get('download_path'))
            self.update_path = Path(PATHS.get('update_path'))
            self.backup_path = Path(PATHS.get('backup_path'))
            self.log_path = Path(PATHS.get('log_path'))
            self.download_dir = Path(PATHS.get('download'))
            self.update_max_index = SETTINGS.get('update_max_index', 20)
            self.image_extensions = app_config.get('image_extensions', [])

            self._loaded = True

        except yaml.YAMLError as e:
            raise ValueError(f"解析配置文件时出错: {e}")
        except FileNotFoundError:
            raise FileNotFoundError(f"配置文件未找到: {config_path}")

        return self

    def validate(self) -> bool:
        if not os.path.exists(self.update_path):
            print(f"错误：源文件 '{self.update_path}' 不存在")
            return False

        if not os.path.exists(self.backup_path):
            os.makedirs(self.backup_path)
            print(f"创建目标目录: {self.backup_path}")

        return True


_config: Optional[Config] = None


def load_config(config_path: Optional[Path] = None) -> Config:
    global _config
    _config = Config.get_instance().load(config_path)
    return _config


def get_config() -> Config:
    global _config
    if _config is None:
        _config = load_config()
    return _config
