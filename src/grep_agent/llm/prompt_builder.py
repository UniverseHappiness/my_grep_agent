"""
Prompt构建器
"""
from typing import List, Optional
import json

from ..core.models import SearchRecord, LLMMessage, MessageRole


class PromptBuilder:
    """Prompt工程构建器"""
    
    SYSTEM_PROMPT = """你是一个代码搜索助手，专注于分析grep搜索结果并判断是否足够回答用户的问题。

你的任务：
1. 分析当前的搜索结果是否包含足够的信息来回答用户的问题
2. 如果信息充足，提供答案
3. 如果信息不足，说明缺少什么信息，并建议下一步搜索策略

判断标准：
- 信息充足：搜索结果包含了回答问题所需的关键信息（如函数定义、配置值、文档说明等）
- 信息不足：搜索结果为空、不相关、或只包含部分信息

输出格式（JSON）：
{
    "is_sufficient": true/false,
    "confidence": 0.0-1.0,
    "answer": "如果信息充足，提供答案",
    "analysis": "对当前搜索结果的分析",
    "missing_info": ["如果不足，列出缺少的信息"],
    "next_strategy": {
        "search_type": "exact/fuzzy/context/broad",
        "keywords": ["建议搜索的关键词"],
        "file_patterns": ["*.py", "*.js"],
        "context_lines": 3,
        "case_sensitive": false,
        "explanation": "为什么建议这个策略"
    },
    "reason": "判断理由"
}

注意：
- 必须严格按照JSON格式输出
- 如果信息充足，next_strategy可以为null
- 如果信息不足，必须提供next_strategy
"""
    
    def __init__(self):
        """初始化Prompt构建器"""
        pass
    
    def build_system_message(self) -> LLMMessage:
        """
        构建系统提示消息
        
        Returns:
            LLMMessage: 系统消息
        """
        return LLMMessage(
            session_id="system",
            iteration_num=0,
            role=MessageRole.SYSTEM,
            content=self.SYSTEM_PROMPT,
        )
    
    def build_user_message(
        self,
        session_id: str,
        iteration_num: int,
        user_query: str,
        search_result: str,
        search_strategy: str,
        search_history: Optional[List[SearchRecord]] = None,
        remaining_iterations: int = 0,
    ) -> LLMMessage:
        """
        构建用户消息
        
        Args:
            session_id: 会话ID
            iteration_num: 当前搜索轮次
            user_query: 用户原始查询
            search_result: 当前搜索结果
            search_strategy: 使用的搜索策略
            search_history: 历史搜索记录
            remaining_iterations: 剩余搜索次数
            
        Returns:
            LLMMessage: 用户消息
        """
        content_parts = []
        
        # 原始查询
        content_parts.append(f"**用户问题：**\n{user_query}")
        
        # 当前搜索信息
        content_parts.append(
            f"\n**当前搜索（第{iteration_num}次）：**\n"
            f"策略：{search_strategy}\n"
            f"剩余搜索次数：{remaining_iterations}"
        )
        
        # 历史搜索摘要
        if search_history and len(search_history) > 0:
            history_summary = self._format_search_history(search_history)
            content_parts.append(f"\n**历史搜索：**\n{history_summary}")
        
        # 当前搜索结果
        content_parts.append(f"\n**搜索结果：**\n{search_result}")
        
        # 请求分析
        content_parts.append(
            "\n**请分析：**\n"
            "1. 这些搜索结果是否足以回答用户的问题？\n"
            "2. 如果足够，请提供答案\n"
            "3. 如果不够，请说明缺少什么信息，并建议下一步搜索策略"
        )
        
        content = "\n".join(content_parts)
        
        return LLMMessage(
            session_id=session_id,
            iteration_num=iteration_num,
            role=MessageRole.USER,
            content=content,
        )
    
    def _format_search_history(self, search_history: List[SearchRecord]) -> str:
        """
        格式化搜索历史
        
        Args:
            search_history: 搜索历史记录
            
        Returns:
            str: 格式化后的历史摘要
        """
        history_parts = []
        
        for record in search_history:
            part = (
                f"- 第{record.iteration_num}次 [{record.strategy_type.value}]: "
                f"搜索'{record.search_pattern}'，找到{record.result_count}行"
            )
            history_parts.append(part)
        
        return "\n".join(history_parts)
    
    def compress_context(
        self,
        messages: List[LLMMessage],
        max_tokens: int = 4000,
    ) -> List[LLMMessage]:
        """
        压缩上下文以适应Token限制
        
        Args:
            messages: 消息列表
            max_tokens: 最大Token数（粗略估计）
            
        Returns:
            List[LLMMessage]: 压缩后的消息列表
        """
        # 粗略估计：1个token约等于4个字符
        max_chars = max_tokens * 4
        
        # 始终保留系统消息和最新的用户消息
        if len(messages) <= 2:
            return messages
        
        system_msg = messages[0]
        latest_user_msg = messages[-1]
        
        # 计算当前长度
        current_length = len(system_msg.content) + len(latest_user_msg.content)
        
        if current_length >= max_chars:
            # 如果最新消息已经太长，只保留系统消息和截断的用户消息
            truncated_content = latest_user_msg.content[:max_chars - len(system_msg.content)]
            latest_user_msg.content = truncated_content + "\n\n... (内容已截断)"
            return [system_msg, latest_user_msg]
        
        # 尝试包含历史消息
        compressed = [system_msg]
        remaining_space = max_chars - current_length
        
        # 从倒数第二条消息开始向前添加
        for msg in reversed(messages[1:-1]):
            if len(msg.content) < remaining_space:
                compressed.insert(1, msg)
                remaining_space -= len(msg.content)
            else:
                break
        
        compressed.append(latest_user_msg)
        
        return compressed
