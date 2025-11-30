"""
日志管理模块
"""
import sys
import os
from pathlib import Path
from loguru import logger
from typing import Optional


class LoggerManager:
    """日志管理器"""
    
    _instance: Optional['LoggerManager'] = None
    _initialized: bool = False
    
    def __new__(cls):
        """单例模式"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def setup_logger(
        self,
        log_level: str = "INFO",
        log_file: Optional[str] = None,
        rotation: str = "100 MB",
        retention: str = "10 days",
    ):
        """
        配置日志系统
        
        Args:
            log_level: 日志级别
            log_file: 日志文件路径
            rotation: 日志轮转大小
            retention: 日志保留时间
        """
        if self._initialized:
            return
        
        # 移除默认处理器
        logger.remove()
        
        # 添加控制台处理器
        logger.add(
            sys.stderr,
            format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
            level=log_level,
            colorize=True,
        )
        
        # 添加文件处理器
        if log_file:
            # 确保日志目录存在
            log_path = Path(log_file)
            log_path.parent.mkdir(parents=True, exist_ok=True)
            
            logger.add(
                log_file,
                format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
                level=log_level,
                rotation=rotation,
                retention=retention,
                encoding="utf-8",
            )
        
        self._initialized = True
        logger.info("日志系统初始化完成")
    
    def get_logger(self):
        """获取日志对象"""
        return logger


# 全局日志管理器实例
logger_manager = LoggerManager()


def get_logger():
    """获取日志对象"""
    return logger_manager.get_logger()
