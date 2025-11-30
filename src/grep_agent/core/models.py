"""
数据模型定义
包含系统所有核心数据结构
"""
from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
import uuid


class SessionStatus(str, Enum):
    """会话状态枚举"""
    INIT = "INIT"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class StrategyType(str, Enum):
    """搜索策略类型枚举"""
    EXACT = "exact"  # 精确匹配
    CASE_INSENSITIVE = "case_insensitive"  # 大小写不敏感
    CONTEXT = "context"  # 上下文扩展
    FUZZY = "fuzzy"  # 模糊匹配
    BROAD = "broad"  # 全局广搜
    FILTERED = "filtered"  # 文件类型过滤
    CUSTOM = "custom"  # 自定义策略


class StrategyMode(str, Enum):
    """策略模式枚举"""
    LLM_DRIVEN = "llm_driven"  # LLM自主决策
    PREDEFINED = "predefined"  # 预定义序列
    HYBRID = "hybrid"  # 混合模式


class MessageRole(str, Enum):
    """消息角色枚举"""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class GrepOptions(BaseModel):
    """Grep搜索选项"""
    recursive: bool = True
    line_number: bool = True
    case_sensitive: bool = True
    context_lines: int = 0
    include_patterns: List[str] = Field(default_factory=list)
    exclude_patterns: List[str] = Field(default_factory=list)
    exclude_dirs: List[str] = Field(default_factory=list)
    max_count: Optional[int] = None


class SearchStrategy(BaseModel):
    """搜索策略"""
    strategy_type: StrategyType
    search_pattern: str
    keywords: List[str] = Field(default_factory=list)
    grep_options: GrepOptions = Field(default_factory=GrepOptions)
    file_patterns: List[str] = Field(default_factory=list)
    explanation: Optional[str] = None


class LLMMessage(BaseModel):
    """LLM交互消息"""
    message_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    session_id: str
    iteration_num: int
    role: MessageRole
    content: str
    timestamp: datetime = Field(default_factory=datetime.now)
    token_count: Optional[int] = None


class LLMFeedback(BaseModel):
    """LLM分析反馈"""
    is_sufficient: bool
    confidence: float = Field(ge=0.0, le=1.0)
    answer: Optional[str] = None
    analysis: str
    missing_info: List[str] = Field(default_factory=list)
    next_strategy: Optional[SearchStrategy] = None
    reason: str


class SearchRecord(BaseModel):
    """搜索记录"""
    iteration_num: int
    strategy_type: StrategyType
    grep_command: str
    search_pattern: str
    search_options: GrepOptions
    execution_time: float
    result_count: int
    result_preview: str
    full_result: Optional[str] = None
    llm_feedback: Optional[LLMFeedback] = None


class SearchSession(BaseModel):
    """搜索会话"""
    session_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_query: str = Field(max_length=1000)
    search_scope: str
    max_iterations: int = Field(default=5, ge=1, le=20)
    current_iteration: int = Field(default=0)
    status: SessionStatus = SessionStatus.INIT
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    final_answer: Optional[str] = None
    search_history: List[SearchRecord] = Field(default_factory=list)
    
    def update_timestamp(self):
        """更新时间戳"""
        self.updated_at = datetime.now()


class StrategyConfig(BaseModel):
    """搜索策略配置"""
    strategy_name: str
    strategy_mode: StrategyMode
    predefined_sequence: List[StrategyType] = Field(default_factory=list)
    hybrid_rules: Dict[str, Any] = Field(default_factory=dict)
    grep_base_options: GrepOptions = Field(default_factory=GrepOptions)
    file_include_patterns: List[str] = Field(default_factory=list)
    file_exclude_patterns: List[str] = Field(default_factory=list)
    max_result_size: int = Field(default=10485760)  # 10MB


class SystemConfig(BaseModel):
    """系统配置"""
    default_max_iterations: int = 5
    default_search_scope: str = "./src"
    enable_cache: bool = True
    cache_ttl: int = 3600
    log_level: str = "INFO"
    result_preview_lines: int = 100
    max_result_size_mb: int = 10


class LLMConfig(BaseModel):
    """LLM配置"""
    provider: str = "openai"
    api_endpoint: str
    api_key: Optional[str] = None
    model_name: str = "gpt-4"
    max_tokens: int = 2000
    temperature: float = 0.7
    timeout: int = 30
    retry_times: int = 3


class APIConfig(BaseModel):
    """API服务配置"""
    host: str = "0.0.0.0"
    port: int = 8000
    enable_cors: bool = True
    max_concurrent_sessions: int = 10
    session_timeout: int = 1800


class AppConfig(BaseModel):
    """应用总配置"""
    system: SystemConfig
    llm: LLMConfig
    api: APIConfig
    strategy: StrategyConfig
