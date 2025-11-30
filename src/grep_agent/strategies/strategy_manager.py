"""
策略管理器
"""
from typing import Optional, List
import copy

from ..core.models import (
    StrategyConfig,
    StrategyMode,
    StrategyType,
    SearchStrategy,
    GrepOptions,
    LLMFeedback,
)
from ..utils.logger import get_logger


class StrategyManager:
    """搜索策略管理器"""
    
    def __init__(self, config: StrategyConfig):
        """
        初始化策略管理器
        
        Args:
            config: 策略配置
        """
        self.config = config
        self.logger = get_logger()
        self.current_predefined_index = 0
    
    def get_initial_strategy(
        self,
        user_query: str,
        keywords: Optional[List[str]] = None,
    ) -> SearchStrategy:
        """
        获取初始搜索策略
        
        Args:
            user_query: 用户查询
            keywords: 提取的关键词
            
        Returns:
            SearchStrategy: 初始搜索策略
        """
        # 使用预定义序列的第一个策略
        if self.config.predefined_sequence:
            strategy_type = self.config.predefined_sequence[0]
            self.current_predefined_index = 0
        else:
            # 默认使用精确匹配
            strategy_type = StrategyType.EXACT
        
        # 提取关键词（如果未提供）
        if keywords is None:
            keywords = self._extract_keywords(user_query)
        
        # 构建grep选项
        grep_options = copy.deepcopy(self.config.grep_base_options)
        grep_options.include_patterns = self.config.file_include_patterns
        grep_options.exclude_patterns = self.config.file_exclude_patterns
        
        # 创建策略
        strategy = SearchStrategy(
            strategy_type=strategy_type,
            search_pattern=keywords[0] if keywords else user_query,
            keywords=keywords,
            grep_options=grep_options,
            explanation="初始搜索策略：精确匹配用户查询中的关键词",
        )
        
        self.logger.info(f"生成初始策略: {strategy_type.value}")
        return strategy
    
    def get_next_strategy(
        self,
        current_iteration: int,
        user_query: str,
        previous_results_count: int,
        llm_feedback: Optional[LLMFeedback] = None,
    ) -> SearchStrategy:
        """
        获取下一个搜索策略
        
        Args:
            current_iteration: 当前搜索轮次
            user_query: 用户查询
            previous_results_count: 前一次搜索的结果数量
            llm_feedback: LLM反馈（如果有）
            
        Returns:
            SearchStrategy: 下一个搜索策略
        """
        # 混合模式决策
        if self.config.strategy_mode == StrategyMode.HYBRID:
            return self._hybrid_strategy_decision(
                current_iteration,
                user_query,
                previous_results_count,
                llm_feedback,
            )
        # LLM驱动模式
        elif self.config.strategy_mode == StrategyMode.LLM_DRIVEN:
            return self._llm_driven_strategy(
                user_query,
                llm_feedback,
            )
        # 预定义模式
        else:
            return self._predefined_strategy(user_query)
    
    def _hybrid_strategy_decision(
        self,
        current_iteration: int,
        user_query: str,
        previous_results_count: int,
        llm_feedback: Optional[LLMFeedback],
    ) -> SearchStrategy:
        """
        混合模式策略决策
        
        根据设计文档6.3节的混合策略模式决策规则：
        - 第1-2次：使用预定义策略
        - 第3次及以后：如果LLM可用且有结果，使用LLM决策
        """
        llm_start_iteration = self.config.hybrid_rules.get('llm_start_iteration', 3)
        
        # 前几次使用预定义策略
        if current_iteration < llm_start_iteration:
            self.logger.info(f"混合模式：第{current_iteration}次，使用预定义策略")
            return self._predefined_strategy(user_query)
        
        # 之后检查LLM是否可用
        if llm_feedback and llm_feedback.next_strategy:
            # LLM提供了有效策略
            self.logger.info(f"混合模式：第{current_iteration}次，使用LLM策略")
            return llm_feedback.next_strategy
        
        # LLM不可用或未提供策略，回退到预定义
        self.logger.info(f"混合模式：第{current_iteration}次，LLM策略无效，回退到预定义")
        return self._predefined_strategy(user_query)
    
    def _llm_driven_strategy(
        self,
        user_query: str,
        llm_feedback: Optional[LLMFeedback],
    ) -> SearchStrategy:
        """
        LLM驱动的策略生成
        """
        if llm_feedback and llm_feedback.next_strategy:
            self.logger.info("使用LLM建议的策略")
            return llm_feedback.next_strategy
        
        # LLM未提供策略，使用默认策略
        self.logger.warning("LLM未提供策略，使用默认策略")
        return self._predefined_strategy(user_query)
    
    def _predefined_strategy(self, user_query: str) -> SearchStrategy:
        """
        获取预定义序列中的下一个策略
        """
        self.current_predefined_index += 1
        
        # 如果超出序列长度，循环回到开始或使用最后一个
        if self.current_predefined_index >= len(self.config.predefined_sequence):
            # 使用最后一个策略（通常是最宽松的）
            strategy_type = self.config.predefined_sequence[-1]
            self.logger.warning(f"预定义策略已用完，重复使用: {strategy_type.value}")
        else:
            strategy_type = self.config.predefined_sequence[self.current_predefined_index]
        
        # 构建grep选项
        grep_options = copy.deepcopy(self.config.grep_base_options)
        grep_options.include_patterns = self.config.file_include_patterns
        grep_options.exclude_patterns = self.config.file_exclude_patterns
        
        # 根据策略类型调整选项
        if strategy_type == StrategyType.CONTEXT:
            grep_options.context_lines = 3
        elif strategy_type == StrategyType.BROAD:
            # 全局广搜：移除文件类型限制
            grep_options.include_patterns = []
        
        # 提取关键词
        keywords = self._extract_keywords(user_query)
        
        strategy = SearchStrategy(
            strategy_type=strategy_type,
            search_pattern=keywords[0] if keywords else user_query,
            keywords=keywords,
            grep_options=grep_options,
            explanation=f"预定义策略序列第{self.current_predefined_index + 1}个: {strategy_type.value}",
        )
        
        self.logger.info(f"使用预定义策略: {strategy_type.value}")
        return strategy
    
    def _extract_keywords(self, query: str) -> List[str]:
        """
        从查询中提取关键词
        
        Args:
            query: 用户查询
            
        Returns:
            List[str]: 关键词列表
        """
        # 简单实现：按空格分割，过滤停用词
        stop_words = {'的', '是', '在', '和', '了', '有', '为', '与', '或', 'the', 'is', 'in', 'and', 'or', 'a', 'an'}
        
        words = query.split()
        keywords = [w for w in words if w.lower() not in stop_words and len(w) > 1]
        
        # 至少返回一个关键词
        if not keywords:
            keywords = [query]
        
        return keywords[:3]  # 最多返回3个关键词
