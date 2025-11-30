"""
基础单元测试
"""
import pytest
from grep_agent.core.models import GrepOptions, StrategyType, SearchStrategy
from grep_agent.utils.validators import PathValidator, InputValidator
from grep_agent.executors.grep_executor import GrepExecutor


def test_grep_options_creation():
    """测试GrepOptions创建"""
    options = GrepOptions(
        recursive=True,
        line_number=True,
        case_sensitive=False,
    )
    
    assert options.recursive is True
    assert options.line_number is True
    assert options.case_sensitive is False


def test_search_strategy_creation():
    """测试SearchStrategy创建"""
    strategy = SearchStrategy(
        strategy_type=StrategyType.EXACT,
        search_pattern="test",
        keywords=["test", "example"],
    )
    
    assert strategy.strategy_type == StrategyType.EXACT
    assert strategy.search_pattern == "test"
    assert len(strategy.keywords) == 2


def test_input_validator_query():
    """测试查询验证"""
    # 有效查询
    valid_query = InputValidator.validate_query("find user function")
    assert valid_query == "find user function"
    
    # 空查询
    with pytest.raises(Exception):
        InputValidator.validate_query("")
    
    # 过长查询
    with pytest.raises(Exception):
        InputValidator.validate_query("a" * 2000)


def test_input_validator_max_iterations():
    """测试最大迭代次数验证"""
    assert InputValidator.validate_max_iterations(5) == 5
    assert InputValidator.validate_max_iterations(0) == 1  # 最小值
    assert InputValidator.validate_max_iterations(100) == 20  # 最大值


def test_input_validator_sanitize():
    """测试输入清理"""
    dangerous = "test; rm -rf /"
    safe = InputValidator.sanitize_grep_pattern(dangerous)
    assert ";" not in safe
    assert "rm" in safe  # 保留有效部分


def test_grep_executor_command_building():
    """测试grep命令构建"""
    executor = GrepExecutor()
    
    options = GrepOptions(
        recursive=True,
        line_number=True,
    )
    
    cmd = executor.build_grep_command(
        pattern="test",
        search_path="/tmp",
        options=options,
        strategy_type=StrategyType.EXACT,
    )
    
    assert "grep" in cmd
    assert "-F" in cmd  # 精确匹配
    assert "-r" in cmd  # 递归
    assert "-n" in cmd  # 行号
    assert "test" in cmd
    assert "/tmp" in cmd


def test_grep_available():
    """测试grep是否可用"""
    executor = GrepExecutor()
    # 这个测试在大多数Linux系统上应该通过
    assert executor.test_grep_available() is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
