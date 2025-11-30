"""
Grep执行器
"""
import subprocess
import time
from typing import Tuple, List
from pathlib import Path

from ..core.models import GrepOptions, StrategyType
from ..core.exceptions import SearchExecutionError
from ..utils.logger import get_logger
from ..utils.validators import InputValidator


class GrepExecutor:
    """Grep命令执行器"""
    
    def __init__(self, max_result_size: int = 10485760):
        """
        初始化Grep执行器
        
        Args:
            max_result_size: 最大结果大小（字节）
        """
        self.logger = get_logger()
        self.max_result_size = max_result_size
    
    def build_grep_command(
        self,
        pattern: str,
        search_path: str,
        options: GrepOptions,
        strategy_type: StrategyType,
    ) -> List[str]:
        """
        构建grep命令
        
        Args:
            pattern: 搜索模式
            search_path: 搜索路径
            options: grep选项
            strategy_type: 策略类型
            
        Returns:
            List[str]: 命令列表
        """
        cmd = ['grep']
        
        # 根据策略类型设置参数
        if strategy_type == StrategyType.EXACT:
            # 精确匹配：固定字符串
            cmd.append('-F')
        elif strategy_type == StrategyType.CASE_INSENSITIVE:
            # 大小写不敏感
            cmd.append('-i')
        elif strategy_type == StrategyType.FUZZY:
            # 模糊匹配：扩展正则表达式
            cmd.append('-E')
        elif strategy_type == StrategyType.CONTEXT:
            # 上下文扩展
            if options.context_lines > 0:
                cmd.extend(['-C', str(options.context_lines)])
        
        # 递归搜索
        if options.recursive:
            cmd.append('-r')
        
        # 显示行号
        if options.line_number:
            cmd.append('-n')
        
        # 大小写敏感（默认）
        if not options.case_sensitive and strategy_type != StrategyType.CASE_INSENSITIVE:
            cmd.append('-i')
        
        # 最大匹配数
        if options.max_count:
            cmd.extend(['-m', str(options.max_count)])
        
        # 排除目录
        for exclude_dir in options.exclude_dirs:
            cmd.extend(['--exclude-dir', exclude_dir])
        
        # 包含文件模式
        for include_pattern in options.include_patterns:
            if InputValidator.validate_file_pattern(include_pattern):
                cmd.extend(['--include', include_pattern])
        
        # 排除文件模式
        for exclude_pattern in options.exclude_patterns:
            if InputValidator.validate_file_pattern(exclude_pattern):
                cmd.extend(['--exclude', exclude_pattern])
        
        # 清理搜索模式
        sanitized_pattern = InputValidator.sanitize_grep_pattern(pattern)
        cmd.append(sanitized_pattern)
        
        # 搜索路径
        cmd.append(search_path)
        
        return cmd
    
    def execute(
        self,
        pattern: str,
        search_path: str,
        options: GrepOptions,
        strategy_type: StrategyType,
        timeout: int = 60,
    ) -> Tuple[str, str, int, float]:
        """
        执行grep搜索
        
        Args:
            pattern: 搜索模式
            search_path: 搜索路径
            options: grep选项
            strategy_type: 策略类型
            timeout: 超时时间（秒）
            
        Returns:
            Tuple[str, str, int, float]: (命令字符串, 搜索结果, 结果数量, 执行时间)
            
        Raises:
            SearchExecutionError: 搜索执行失败
        """
        # 构建命令
        cmd = self.build_grep_command(pattern, search_path, options, strategy_type)
        cmd_str = ' '.join(cmd)
        
        self.logger.info(f"执行grep命令: {cmd_str}")
        
        start_time = time.time()
        
        try:
            # 执行命令
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
                encoding='utf-8',
                errors='replace',
            )
            
            execution_time = time.time() - start_time
            
            # grep返回码：0=找到匹配，1=未找到匹配，2=错误
            if result.returncode == 2:
                error_msg = result.stderr.strip()
                self.logger.error(f"Grep执行错误: {error_msg}")
                raise SearchExecutionError(f"Grep执行错误: {error_msg}")
            
            output = result.stdout
            
            # 检查结果大小
            if len(output.encode('utf-8')) > self.max_result_size:
                self.logger.warning(f"搜索结果过大，截断到{self.max_result_size}字节")
                # 截断结果
                output_bytes = output.encode('utf-8')[:self.max_result_size]
                output = output_bytes.decode('utf-8', errors='ignore')
            
            # 统计结果数量（行数）
            result_count = len(output.splitlines()) if output else 0
            
            self.logger.info(
                f"搜索完成: 找到{result_count}行匹配，耗时{execution_time:.2f}秒"
            )
            
            return cmd_str, output, result_count, execution_time
            
        except subprocess.TimeoutExpired:
            execution_time = time.time() - start_time
            self.logger.error(f"Grep执行超时（{timeout}秒）")
            raise SearchExecutionError(f"搜索超时（{timeout}秒）")
        
        except Exception as e:
            execution_time = time.time() - start_time
            self.logger.error(f"Grep执行异常: {e}")
            raise SearchExecutionError(f"搜索执行失败: {e}")
    
    def test_grep_available(self) -> bool:
        """
        测试grep命令是否可用
        
        Returns:
            bool: grep是否可用
        """
        try:
            result = subprocess.run(
                ['grep', '--version'],
                capture_output=True,
                timeout=5,
            )
            return result.returncode == 0
        except Exception:
            return False
