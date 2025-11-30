"""
LLM客户端
"""
import json
import time
from typing import List, Dict, Any, Optional
import httpx

from ..core.models import (
    LLMConfig,
    LLMMessage,
    LLMFeedback,
    SearchStrategy,
    StrategyType,
    GrepOptions,
)
from ..core.exceptions import LLMConnectionError
from ..utils.logger import get_logger


class LLMClient:
    """LLM API客户端"""
    
    def __init__(self, config: LLMConfig):
        """
        初始化LLM客户端
        
        Args:
            config: LLM配置
        """
        self.config = config
        self.logger = get_logger()
        
        # 创建HTTP客户端
        self.client = httpx.Client(
            timeout=config.timeout,
            headers={
                "Authorization": f"Bearer {config.api_key}",
                "Content-Type": "application/json",
            }
        )
    
    def call_llm(
        self,
        messages: List[LLMMessage],
        max_retries: Optional[int] = None,
    ) -> str:
        """
        调用LLM API
        
        Args:
            messages: 消息列表
            max_retries: 最大重试次数
            
        Returns:
            str: LLM响应内容
            
        Raises:
            LLMConnectionError: LLM调用失败
        """
        if max_retries is None:
            max_retries = self.config.retry_times
        
        # 转换消息格式
        api_messages = self._convert_messages(messages)
        
        # 构建请求体
        request_data = {
            "model": self.config.model_name,
            "messages": api_messages,
            "max_tokens": self.config.max_tokens,
            "temperature": self.config.temperature,
        }
        
        last_error = None
        
        for attempt in range(max_retries):
            try:
                self.logger.info(f"调用LLM API (尝试 {attempt + 1}/{max_retries})")
                
                # 发送请求
                response = self.client.post(
                    f"{self.config.api_endpoint}/chat/completions",
                    json=request_data,
                )
                
                # 检查响应状态
                if response.status_code == 200:
                    result = response.json()
                    content = result["choices"][0]["message"]["content"]
                    
                    # 记录Token使用情况
                    if "usage" in result:
                        self.logger.info(
                            f"Token使用: {result['usage'].get('total_tokens', 'N/A')}"
                        )
                    
                    return content
                
                elif response.status_code == 429:
                    # API限流
                    retry_after = int(response.headers.get("Retry-After", 5))
                    self.logger.warning(f"API限流，{retry_after}秒后重试")
                    time.sleep(retry_after)
                    continue
                
                elif response.status_code == 401:
                    # 认证失败
                    raise LLMConnectionError("API认证失败，请检查API密钥")
                
                else:
                    # 其他错误
                    error_msg = f"API调用失败: {response.status_code} - {response.text}"
                    self.logger.error(error_msg)
                    last_error = LLMConnectionError(error_msg)
                    
                    # 指数退避
                    if attempt < max_retries - 1:
                        wait_time = 2 ** attempt
                        self.logger.info(f"等待{wait_time}秒后重试")
                        time.sleep(wait_time)
            
            except httpx.TimeoutException:
                error_msg = f"LLM API超时 ({self.config.timeout}秒)"
                self.logger.error(error_msg)
                last_error = LLMConnectionError(error_msg)
                
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt
                    time.sleep(wait_time)
            
            except Exception as e:
                error_msg = f"LLM API调用异常: {e}"
                self.logger.error(error_msg)
                last_error = LLMConnectionError(error_msg)
                
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt
                    time.sleep(wait_time)
        
        # 所有重试都失败
        if last_error:
            raise last_error
        else:
            raise LLMConnectionError("LLM调用失败，原因未知")
    
    def parse_llm_response(self, response: str) -> LLMFeedback:
        """
        解析LLM响应
        
        Args:
            response: LLM响应内容
            
        Returns:
            LLMFeedback: 解析后的反馈对象
            
        Raises:
            LLMConnectionError: 解析失败
        """
        try:
            # 尝试提取JSON内容
            json_str = self._extract_json(response)
            data = json.loads(json_str)
            
            # 解析next_strategy（如果存在）
            next_strategy = None
            if data.get("next_strategy") and data["next_strategy"] is not None:
                next_strategy = self._parse_strategy(data["next_strategy"])
            
            # 创建反馈对象
            feedback = LLMFeedback(
                is_sufficient=data.get("is_sufficient", False),
                confidence=float(data.get("confidence", 0.0)),
                answer=data.get("answer"),
                analysis=data.get("analysis", ""),
                missing_info=data.get("missing_info", []),
                next_strategy=next_strategy,
                reason=data.get("reason", ""),
            )
            
            return feedback
        
        except json.JSONDecodeError as e:
            self.logger.error(f"JSON解析失败: {e}")
            self.logger.debug(f"原始响应: {response}")
            
            # 尝试宽松解析
            return self._fallback_parse(response)
        
        except Exception as e:
            self.logger.error(f"响应解析失败: {e}")
            raise LLMConnectionError(f"无法解析LLM响应: {e}")
    
    def _convert_messages(self, messages: List[LLMMessage]) -> List[Dict[str, str]]:
        """
        转换消息格式为API格式
        
        Args:
            messages: 消息列表
            
        Returns:
            List[Dict]: API消息格式
        """
        return [
            {
                "role": msg.role.value,
                "content": msg.content,
            }
            for msg in messages
        ]
    
    def _extract_json(self, text: str) -> str:
        """
        从文本中提取JSON内容
        
        Args:
            text: 包含JSON的文本
            
        Returns:
            str: JSON字符串
        """
        # 尝试直接解析
        text = text.strip()
        if text.startswith('{') and text.endswith('}'):
            return text
        
        # 尝试查找JSON代码块
        if '```json' in text:
            start = text.find('```json') + 7
            end = text.find('```', start)
            if end != -1:
                return text[start:end].strip()
        
        # 尝试查找JSON对象
        start = text.find('{')
        end = text.rfind('}')
        if start != -1 and end != -1:
            return text[start:end + 1]
        
        # 无法提取，返回原始文本
        return text
    
    def _parse_strategy(self, strategy_data: Dict[str, Any]) -> SearchStrategy:
        """
        解析搜索策略
        
        Args:
            strategy_data: 策略数据
            
        Returns:
            SearchStrategy: 搜索策略对象
        """
        # 映射search_type到StrategyType
        search_type_map = {
            "exact": StrategyType.EXACT,
            "fuzzy": StrategyType.FUZZY,
            "context": StrategyType.CONTEXT,
            "broad": StrategyType.BROAD,
            "case_insensitive": StrategyType.CASE_INSENSITIVE,
        }
        
        search_type_str = strategy_data.get("search_type", "fuzzy")
        strategy_type = search_type_map.get(search_type_str, StrategyType.FUZZY)
        
        # 构建grep选项
        grep_options = GrepOptions(
            context_lines=strategy_data.get("context_lines", 0),
            case_sensitive=strategy_data.get("case_sensitive", True),
        )
        
        # 创建策略
        strategy = SearchStrategy(
            strategy_type=strategy_type,
            search_pattern=strategy_data.get("keywords", [""])[0] if strategy_data.get("keywords") else "",
            keywords=strategy_data.get("keywords", []),
            grep_options=grep_options,
            file_patterns=strategy_data.get("file_patterns", []),
            explanation=strategy_data.get("explanation", ""),
        )
        
        return strategy
    
    def _fallback_parse(self, response: str) -> LLMFeedback:
        """
        宽松解析响应（当JSON解析失败时）
        
        Args:
            response: 响应文本
            
        Returns:
            LLMFeedback: 反馈对象
        """
        self.logger.warning("使用宽松解析模式")
        
        # 简单判断：如果包含肯定词汇，认为信息充足
        positive_words = ['充足', '足够', '可以回答', '找到了', 'sufficient', 'enough']
        is_sufficient = any(word in response.lower() for word in positive_words)
        
        return LLMFeedback(
            is_sufficient=is_sufficient,
            confidence=0.5,
            answer=response if is_sufficient else None,
            analysis=response,
            missing_info=[] if is_sufficient else ["需要更多信息"],
            next_strategy=None,
            reason="宽松解析模式",
        )
    
    def close(self):
        """关闭客户端"""
        self.client.close()
    
    def __enter__(self):
        """上下文管理器入口"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器退出"""
        self.close()
