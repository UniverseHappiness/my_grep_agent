"""
Grep搜索Agent包
"""
__version__ = "0.1.0"
__author__ = "Grep Agent Team"
__description__ = "智能化的grep搜索Agent系统"

from .core import (
    ConfigManager,
    SessionStatus,
    StrategyType,
    StrategyMode,
)

__all__ = [
    "__version__",
    "__author__",
    "__description__",
    "ConfigManager",
    "SessionStatus",
    "StrategyType",
    "StrategyMode",
]
