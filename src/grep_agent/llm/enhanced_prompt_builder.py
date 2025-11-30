"""
增强版Prompt构建器 - 支持LLM自动生成Linux命令
"""
from typing import List, Optional, Dict, Any
import json

from ..core.models import LLMMessage, MessageRole


class EnhancedPromptBuilder:
    """增强版Prompt工程构建器"""
    
    SYSTEM_PROMPT = """你是一个智能代码搜索助手，能够通过执行Linux命令来帮助用户查找和分析代码。

你的能力：
1. 根据用户的问题，自动生成合适的Linux命令来获取信息
2. 分析命令执行结果，判断是否足够回答用户问题
3. 如果信息不足，继续生成新的命令进行探索

可用的命令类型（安全白名单）：
- grep: 搜索文件内容（支持正则、递归、上下文等）
- find: 查找文件（按名称、类型、大小等）
- cat: 查看文件内容
- head/tail: 查看文件开头/结尾
- wc: 统计行数、字数
- ls: 列出目录内容
- tree: 显示目录树结构（如果可用）
- file: 识别文件类型
- stat: 查看文件详细信息
- du: 查看目录大小
- sort/uniq: 排序和去重
- awk/sed: 文本处理（基础用法）

安全限制：
- 只能使用只读命令
- 不能使用rm、mv、cp等修改文件的命令
- 不能使用sudo、su等权限提升命令
- 不能使用网络命令（wget、curl等）
- 不能使用管道中的危险命令

命令生成原则：
1. 优先使用简单、安全的命令
2. 合理使用管道组合多个命令
3. 添加必要的过滤和格式化
4. 考虑性能，避免搜索过大的范围
5. 使用grep命令时应该要搭配-n输出内容在的行号，方便定位

输出格式（必须是有效的JSON）：
{
    "analysis": "对当前情况的分析",
    "is_sufficient": true/false,
    "confidence": 0.0-1.0,
    "answer": "如果信息充足，提供答案",
    "next_command": {
        "command": "完整的Linux命令",
        "purpose": "这条命令的目的",
        "expected_output": "期望获得什么信息"
    },
    "reasoning": "为什么选择这个命令"
}

重要说明：
- 如果信息充足，设置is_sufficient=true，next_command可以为null
- 如果信息不足，设置is_sufficient=false，必须提供next_command
- 命令必须是安全的、只读的
- 命令路径必须在允许的搜索范围内
"""
    
    def __init__(self):
        """初始化增强版Prompt构建器"""
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
    
    def build_initial_message(
        self,
        session_id: str,
        user_query: str,
        search_scope: str,
        max_iterations: int,
    ) -> LLMMessage:
        """
        构建初始查询消息
        
        Args:
            session_id: 会话ID
            user_query: 用户查询
            search_scope: 搜索范围
            max_iterations: 最大迭代次数
            
        Returns:
            LLMMessage: 用户消息
        """
        content = f"""用户问题：{user_query}

搜索范围：{search_scope}
最大命令执行次数：{max_iterations}

请根据用户的问题，生成第一条Linux命令来获取相关信息。

注意：
1. 命令必须在搜索范围 {search_scope} 内执行
2. 优先使用grep、find等常用命令
3. 如果是查找代码，考虑文件类型过滤
4. 提供清晰的命令目的说明
"""
        
        return LLMMessage(
            session_id=session_id,
            iteration_num=0,
            role=MessageRole.USER,
            content=content,
        )
    
    def build_iteration_message(
        self,
        session_id: str,
        iteration_num: int,
        user_query: str,
        command_history: List[Dict[str, Any]],
        last_command: str,
        last_output: str,
        remaining_iterations: int,
    ) -> LLMMessage:
        """
        构建迭代消息
        
        Args:
            session_id: 会话ID
            iteration_num: 当前迭代次数
            user_query: 用户查询
            command_history: 命令历史
            last_command: 上一条命令
            last_output: 上一条命令的输出
            remaining_iterations: 剩余迭代次数
            
        Returns:
            LLMMessage: 用户消息
        """
        content_parts = []
        
        # 用户问题
        content_parts.append(f"**用户问题：**\n{user_query}")
        
        # 当前进度
        content_parts.append(
            f"\n**当前进度：**\n"
            f"- 已执行命令数：{iteration_num}\n"
            f"- 剩余可执行次数：{remaining_iterations}"
        )
        
        # 命令历史摘要
        if len(command_history) > 1:
            history_summary = self._format_command_history(command_history[:-1])
            content_parts.append(f"\n**历史命令：**\n{history_summary}")
        
        # 最近执行的命令和结果
        content_parts.append(
            f"\n**刚执行的命令：**\n```bash\n{last_command}\n```"
        )
        
        # 限制输出长度
        output_preview = self._truncate_output(last_output, max_lines=100)
        content_parts.append(
            f"\n**命令输出：**\n```\n{output_preview}\n```"
        )
        
        # 请求分析
        content_parts.append(
            f"\n**请分析：**\n"
            f"1. 这些信息是否足够回答用户的问题？\n"
            f"2. 如果足够，请提供答案,并在答案中包含文件名与行号作为参考文献\n"
            f"3. 如果不够，请生成下一条命令继续探索\n"
            f"4. 注意：还剩{remaining_iterations}次机会"
        )
        
        content = "\n".join(content_parts)
        
        return LLMMessage(
            session_id=session_id,
            iteration_num=iteration_num,
            role=MessageRole.USER,
            content=content,
        )
    
    def _format_command_history(self, history: List[Dict[str, Any]]) -> str:
        """
        格式化命令历史
        
        Args:
            history: 命令历史列表
            
        Returns:
            str: 格式化后的历史
        """
        lines = []
        for i, item in enumerate(history, 1):
            cmd = item.get('command', 'N/A')
            purpose = item.get('purpose', 'N/A')
            result_count = item.get('result_lines', 0)
            lines.append(
                f"{i}. 命令: {cmd}\n"
                f"   目的: {purpose}\n"
                f"   结果: {result_count}行"
            )
        return "\n\n".join(lines)
    
    def _truncate_output(self, output: str, max_lines: int = 100) -> str:
        """
        截断输出到指定行数
        
        Args:
            output: 原始输出
            max_lines: 最大行数
            
        Returns:
            str: 截断后的输出
        """
        if not output:
            return "（无输出）"
        
        lines = output.splitlines()
        
        if len(lines) <= max_lines:
            return output
        
        truncated = "\n".join(lines[:max_lines])
        truncated += f"\n\n... （还有{len(lines) - max_lines}行未显示）"
        
        return truncated
    
    def compress_context(
        self,
        messages: List[LLMMessage],
        max_tokens: int = 6000,
    ) -> List[LLMMessage]:
        """
        压缩上下文以适应Token限制
        
        Args:
            messages: 消息列表
            max_tokens: 最大Token数
            
        Returns:
            List[LLMMessage]: 压缩后的消息列表
        """
        # 粗略估计：1个token约等于4个字符（中文）或1个单词
        max_chars = max_tokens * 3
        
        if len(messages) <= 2:
            return messages
        
        # 始终保留系统消息和最新的用户消息
        system_msg = messages[0]
        latest_msg = messages[-1]
        
        current_length = len(system_msg.content) + len(latest_msg.content)
        
        if current_length >= max_chars:
            # 截断最新消息
            truncated_content = latest_msg.content[:max_chars - len(system_msg.content)]
            latest_msg.content = truncated_content + "\n\n... (内容已截断)"
            return [system_msg, latest_msg]
        
        # 尝试包含部分历史
        compressed = [system_msg]
        remaining_space = max_chars - current_length
        
        # 只保留最近的几条消息
        recent_messages = messages[1:-1][-3:]  # 最多保留最近3条
        
        for msg in recent_messages:
            # 压缩历史消息内容
            compressed_content = self._compress_message_content(msg.content, max_length=500)
            if len(compressed_content) < remaining_space:
                msg.content = compressed_content
                compressed.append(msg)
                remaining_space -= len(compressed_content)
        
        compressed.append(latest_msg)
        
        return compressed
    
    def _compress_message_content(self, content: str, max_length: int = 500) -> str:
        """
        压缩消息内容
        
        Args:
            content: 原始内容
            max_length: 最大长度
            
        Returns:
            str: 压缩后的内容
        """
        if len(content) <= max_length:
            return content
        
        # 保留开头和结尾
        half = max_length // 2
        return content[:half] + "\n...(省略)...\n" + content[-half:]
