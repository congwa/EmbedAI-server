import logging
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler
from typing import Optional
from app.core.config import settings

class Logger:
    _instance: Optional[logging.Logger] = None

    @classmethod
    def get_logger(cls) -> logging.Logger:
        if cls._instance is None:
            cls._instance = cls._setup_logger()
        return cls._instance

    @staticmethod
    def _setup_logger() -> logging.Logger:
        # 创建logger
        logger = logging.getLogger("fastapi")
        logger.setLevel(logging.INFO)

        # 创建格式化器
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )

        # 创建控制台处理器
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

        # 创建文件处理器
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        file_handler = RotatingFileHandler(
            log_dir / "app.log",
            maxBytes=10485760,  # 10MB
            backupCount=5,
            encoding="utf-8"
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

        return logger

    @staticmethod
    def info(message: str):
        Logger.get_logger().info(message)

    @staticmethod
    def error(message: str):
        Logger.get_logger().error(message)

    @staticmethod
    def warning(message: str):
        Logger.get_logger().warning(message)

    @staticmethod
    def debug(message: str):
        Logger.get_logger().debug(message) 