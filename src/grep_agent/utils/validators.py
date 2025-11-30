"""
输入验证模块
"""
import os
import re
from pathlib import Path
from typing import List, Optional

from ..core.exceptions import PathValidationError, ValidationError


class PathValidator:
    """路径验证器"""
    
    @staticmethod
    def validate_search_path(
        path: str,
        allowed_paths: Optional[List[str]] = None,
    ) -> str:
        """
        验证搜索路径
        
        Args:
            path: 要验证的路径
            allowed_paths: 允许的路径列表（白名单）
            
        Returns:
            str: 规范化后的绝对路径
            
        Raises:
            PathValidationError: 路径验证失败
        """
        # 检查路径是否为空
        if not path or not path.strip():
            raise PathValidationError("搜索路径不能为空")
        
        # 检查危险字符
        dangerous_patterns = ['..', '~', '$']
        for pattern in dangerous_patterns:
            if pattern in path:
                raise PathValidationError(f"路径包含危险字符: {pattern}")
        
        # 转换为绝对路径
        try:
            abs_path = os.path.abspath(path)
        except Exception as e:
            raise PathValidationError(f"路径格式无效: {e}")
        
        # 检查路径是否存在
        if not os.path.exists(abs_path):
            raise PathValidationError(f"路径不存在: {abs_path}")
        
        # 检查是否为目录
        if not os.path.isdir(abs_path):
            raise PathValidationError(f"路径不是目录: {abs_path}")
        
        # 检查是否可读
        if not os.access(abs_path, os.R_OK):
            raise PathValidationError(f"路径不可读: {abs_path}")
        
        # 白名单验证
        if allowed_paths:
            allowed = False
            for allowed_path in allowed_paths:
                allowed_abs = os.path.abspath(allowed_path)
                if abs_path.startswith(allowed_abs):
                    allowed = True
                    break
            
            if not allowed:
                raise PathValidationError(f"路径不在允许的范围内: {abs_path}")
        
        return abs_path
    
    @staticmethod
    def is_safe_path(path: str) -> bool:
        """
        检查路径是否安全
        
        Args:
            path: 要检查的路径
            
        Returns:
            bool: 是否安全
        """
        try:
            PathValidator.validate_search_path(path)
            return True
        except PathValidationError:
            return False


class InputValidator:
    """输入验证器"""
    
    @staticmethod
    def validate_query(query: str, max_length: int = 1000) -> str:
        """
        验证用户查询
        
        Args:
            query: 用户查询内容
            max_length: 最大长度
            
        Returns:
            str: 验证后的查询
            
        Raises:
            ValidationError: 验证失败
        """
        # 检查是否为空
        if not query or not query.strip():
            raise ValidationError("查询内容不能为空")
        
        query = query.strip()
        
        # 检查长度
        if len(query) > max_length:
            raise ValidationError(f"查询内容过长，最多{max_length}字符")
        
        return query
    
    @staticmethod
    def validate_max_iterations(max_iterations: int) -> int:
        """
        验证最大搜索次数
        
        Args:
            max_iterations: 最大搜索次数
            
        Returns:
            int: 验证后的值
            
        Raises:
            ValidationError: 验证失败
        """
        if not isinstance(max_iterations, int):
            raise ValidationError("最大搜索次数必须是整数")
        
        if max_iterations < 1:
            return 1
        elif max_iterations > 20:
            return 20
        
        return max_iterations
    
    @staticmethod
    def sanitize_grep_pattern(pattern: str) -> str:
        """
        清理grep搜索模式，防止命令注入
        
        Args:
            pattern: 搜索模式
            
        Returns:
            str: 清理后的模式
        """
        # 移除危险字符
        dangerous_chars = [';', '&', '|', '`', '$', '(', ')', '<', '>']
        sanitized = pattern
        for char in dangerous_chars:
            sanitized = sanitized.replace(char, '')
        
        return sanitized
    
    @staticmethod
    def validate_file_pattern(pattern: str) -> bool:
        """
        验证文件模式是否为有效的glob模式
        
        Args:
            pattern: 文件模式
            
        Returns:
            bool: 是否有效
        """
        # 简单验证：检查是否包含基本的glob字符
        if not pattern:
            return False
        
        # 检查危险字符
        dangerous_chars = [';', '&', '|', '`', '$', '(', ')']
        for char in dangerous_chars:
            if char in pattern:
                return False
        
        return True
