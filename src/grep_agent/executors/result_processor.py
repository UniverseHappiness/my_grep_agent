"""
结果处理器
"""
from typing import List
from cachetools import TTLCache

from ..core.models import SearchRecord
from ..utils.logger import get_logger


class ResultProcessor:
    """搜索结果处理器"""
    
    def __init__(
        self,
        enable_cache: bool = True,
        cache_ttl: int = 3600,
        preview_lines: int = 100,
    ):
        """
        初始化结果处理器
        
        Args:
            enable_cache: 是否启用缓存
            cache_ttl: 缓存过期时间（秒）
            preview_lines: 结果预览行数
        """
        self.logger = get_logger()
        self.enable_cache = enable_cache
        self.preview_lines = preview_lines
        
        # 初始化缓存
        if enable_cache:
            self.cache = TTLCache(maxsize=100, ttl=cache_ttl)
        else:
            self.cache = None
    
    def generate_cache_key(self, pattern: str, search_path: str) -> str:
        """
        生成缓存键
        
        Args:
            pattern: 搜索模式
            search_path: 搜索路径
            
        Returns:
            str: 缓存键
        """
        return f"{search_path}:{pattern}"
    
    def get_cached_result(self, pattern: str, search_path: str) -> str:
        """
        获取缓存的搜索结果
        
        Args:
            pattern: 搜索模式
            search_path: 搜索路径
            
        Returns:
            str: 缓存的结果，如果不存在则返回None
        """
        if not self.enable_cache or self.cache is None:
            return None
        
        cache_key = self.generate_cache_key(pattern, search_path)
        return self.cache.get(cache_key)
    
    def cache_result(self, pattern: str, search_path: str, result: str):
        """
        缓存搜索结果
        
        Args:
            pattern: 搜索模式
            search_path: 搜索路径
            result: 搜索结果
        """
        if not self.enable_cache or self.cache is None:
            return
        
        cache_key = self.generate_cache_key(pattern, search_path)
        self.cache[cache_key] = result
        self.logger.debug(f"缓存搜索结果: {cache_key}")
    
    def create_preview(self, full_result: str) -> str:
        """
        创建结果预览
        
        Args:
            full_result: 完整结果
            
        Returns:
            str: 结果预览
        """
        if not full_result:
            return ""
        
        lines = full_result.splitlines()
        
        if len(lines) <= self.preview_lines:
            return full_result
        
        preview_lines = lines[:self.preview_lines]
        preview = '\n'.join(preview_lines)
        preview += f"\n\n... (还有{len(lines) - self.preview_lines}行未显示)"
        
        return preview
    
    def deduplicate_results(self, results: List[str]) -> List[str]:
        """
        去重搜索结果
        
        Args:
            results: 结果列表
            
        Returns:
            List[str]: 去重后的结果列表
        """
        # 保持顺序的去重
        seen = set()
        deduplicated = []
        
        for result in results:
            if result not in seen:
                seen.add(result)
                deduplicated.append(result)
        
        return deduplicated
    
    def aggregate_search_history(
        self,
        search_history: List[SearchRecord],
    ) -> str:
        """
        聚合搜索历史
        
        Args:
            search_history: 搜索历史记录列表
            
        Returns:
            str: 聚合后的摘要
        """
        if not search_history:
            return "暂无搜索历史"
        
        summary_parts = []
        
        for record in search_history:
            part = (
                f"第{record.iteration_num}次搜索 [{record.strategy_type.value}]:\n"
                f"  模式: {record.search_pattern}\n"
                f"  结果: {record.result_count}行匹配\n"
                f"  耗时: {record.execution_time:.2f}秒"
            )
            summary_parts.append(part)
        
        return "\n\n".join(summary_parts)
    
    def format_result_for_llm(
        self,
        result: str,
        max_length: int = 5000,
    ) -> str:
        """
        格式化结果用于发送给LLM
        
        Args:
            result: 原始结果
            max_length: 最大长度
            
        Returns:
            str: 格式化后的结果
        """
        if not result:
            return "未找到匹配结果"
        
        # 如果结果太长，进行截断
        if len(result) > max_length:
            lines = result.splitlines()
            truncated_lines = []
            current_length = 0
            
            for line in lines:
                if current_length + len(line) > max_length:
                    break
                truncated_lines.append(line)
                current_length += len(line) + 1  # +1 for newline
            
            truncated = '\n'.join(truncated_lines)
            truncated += f"\n\n... (结果已截断，共{len(lines)}行)"
            return truncated
        
        return result
