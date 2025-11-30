"""
自定义异常类
"""


class GrepAgentException(Exception):
    """基础异常类"""
    pass


class ConfigurationError(GrepAgentException):
    """配置错误"""
    pass


class SearchExecutionError(GrepAgentException):
    """搜索执行错误"""
    pass


class LLMConnectionError(GrepAgentException):
    """LLM连接错误"""
    pass


class ValidationError(GrepAgentException):
    """验证错误"""
    pass


class PathValidationError(ValidationError):
    """路径验证错误"""
    pass


class SessionNotFoundError(GrepAgentException):
    """会话不存在错误"""
    pass


class SessionExpiredError(GrepAgentException):
    """会话过期错误"""
    pass
