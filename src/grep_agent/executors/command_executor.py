"""
通用Linux命令执行器 - 支持多种只读命令
"""
import subprocess
import time
import shlex
from typing import Tuple, List, Optional
from pathlib import Path

from ..core.exceptions import SearchExecutionError
from ..utils.logger import get_logger


class CommandExecutor:
    """通用命令执行器"""
    
    # 允许的命令白名单
    ALLOWED_COMMANDS = {
        'grep', 'find', 'cat', 'head', 'tail', 'wc', 'ls', 'tree','exec',
        'file', 'stat', 'du', 'sort', 'uniq', 'awk', 'sed',
        'less', 'more', 'which', 'whereis', 'type', 'pwd',
        'echo', 'printf', 'basename', 'dirname', 'readlink',
        'xargs',  # xargs用于将管道输出转换为命令参数，是安全的
    }
    
    # 危险命令黑名单（绝对禁止）
    FORBIDDEN_COMMANDS = {
        'rm', 'rmdir', 'mv', 'cp', 'dd', 'mkfs', 'fdisk',
        'sudo', 'su', 'chmod', 'chown', 'chgrp',
        'kill', 'killall', 'pkill',
        'wget', 'curl', 'nc', 'netcat', 'ssh', 'scp', 'ftp',
        'mount', 'umount', 'format',
        'bash', 'sh', 'zsh', 'fish', 'python', 'perl', 'ruby',
        'eval', 'source',
    }
    
    # 危险字符/模式（需要特殊检查）
    # 注意：有些字符在特定上下文中是安全的
    DANGEROUS_PATTERNS = {
        '&&': '命令链接',
        '||': '条件执行', 
        '`': '命令替换',
        '$(': '命令替换',
    }
    
    def __init__(
        self,
        search_scope: str,
        max_result_size: int = 10485760,  # 10MB
        timeout: int = 30,
        allow_pipes: bool = True,  # 是否允许管道
    ):
        """
        初始化命令执行器
        
        Args:
            search_scope: 允许的搜索范围
            max_result_size: 最大结果大小（字节）
            timeout: 超时时间（秒）
            allow_pipes: 是否允许管道命令
        """
        self.logger = get_logger()
        self.search_scope = Path(search_scope).resolve()
        self.max_result_size = max_result_size
        self.timeout = timeout
        self.allow_pipes = allow_pipes
    
    def validate_command(self, command: str) -> Tuple[bool, str]:
        """
        验证命令是否安全
        
        Args:
            command: 要执行的命令
            
        Returns:
            Tuple[bool, str]: (是否安全, 错误信息)
        """
        if not command or not command.strip():
            return False, "命令为空"
        
        command = command.strip()
        
        # 检查危险命令 - 使用更精确的单词边界匹配
        import re
        for forbidden in self.FORBIDDEN_COMMANDS:
            # 使用单词边界\b来确保完整匹配命令，而不是子字符串
            # 例如：'nc' 不会匹配 'include'，'rm' 不会匹配 'format'
            pattern = r'\b' + re.escape(forbidden) + r'\b'
            if re.search(pattern, command.lower()):
                return False, f"包含禁止的命令: {forbidden}"
        
        # 解析命令（处理管道）
        if '|' in command:
            if not self.allow_pipes:
                return False, "不允许使用管道"
            
            # 检查管道中的每个命令（使用xargs是安全的）
            parts = command.split('|')
            for part in parts:
                part = part.strip()
                if part:
                    # 获取命令名（可能是xargs、grep等）
                    tokens = part.split()
                    if tokens:
                        cmd_name = tokens[0]
                        # xargs是安全的白名单命令
                        if cmd_name not in self.ALLOWED_COMMANDS and cmd_name != 'xargs':
                            # 检查是否是禁止命令
                            if cmd_name in self.FORBIDDEN_COMMANDS:
                                return False, f"管道中包含禁止的命令: {cmd_name}"
        
        # 获取主命令
        main_cmd = command.split()[0] if command.split() else ""
        
        # 检查是否在白名单中
        if main_cmd not in self.ALLOWED_COMMANDS:
            return False, f"命令不在允许列表中: {main_cmd}"
        
        # 检查真正危险的模式
        for pattern, desc in self.DANGEROUS_PATTERNS.items():
            if pattern in command:
                return False, f"包含危险操作: {desc} ({pattern})"
        
        # 检查重定向（但允许错误重定向到/dev/null）
        # 2>/dev/null 是安全的，用于抑制错误输出
        if '>' in command or '<' in command:
            # 允许 2>/dev/null 或 2>&1 这样的错误重定向
            safe_redirects = ['2>/dev/null', '2>&1']
            has_safe_redirect = any(sr in command for sr in safe_redirects)
            
            # 检查是否只有安全的重定向
            temp_cmd = command
            for sr in safe_redirects:
                temp_cmd = temp_cmd.replace(sr, '')
            
            if '>' in temp_cmd or '<' in temp_cmd:
                return False, "包含不安全的文件重定向"
        
        # find命令的特殊检查：允许 -exec 和 \; 结尾
        if main_cmd == 'find':
            # -exec ... \; 是find的标准语法
            if '-exec' in command:
                # 检查是否以 \; 或 + 结尾
                if not (command.rstrip().endswith('\;') or command.rstrip().endswith('+')):
                    return False, "find -exec 必须以 \\; 或 + 结尾"
                # exec后面的命令也需要检查
                exec_match = re.search(r'-exec\s+(\S+)', command)
                if exec_match:
                    exec_cmd = exec_match.group(1)
                    if exec_cmd in self.FORBIDDEN_COMMANDS:
                        return False, f"-exec 包含禁止的命令: {exec_cmd}"
        
        # 检查路径是否在允许范围内
        if not self._validate_paths_in_command(command):
            return False, f"命令路径超出允许范围: {self.search_scope}"
        
        return True, "命令安全"
    
    def _validate_paths_in_command(self, command: str) -> bool:
        """
        验证命令中的路径是否在允许范围内
        
        Args:
            command: 命令字符串
            
        Returns:
            bool: 是否合法
        """
        # 提取可能的路径参数
        parts = shlex.split(command)
        
        for part in parts:
            # 跳过选项参数
            if part.startswith('-'):
                continue
            
            # 检查是否看起来像路径
            if '/' in part or part.startswith('.'):
                try:
                    path = Path(part).resolve()
                    # 检查是否在允许范围内
                    if not str(path).startswith(str(self.search_scope)):
                        self.logger.warning(f"路径超出范围: {path}")
                        return False
                except Exception:
                    # 可能不是路径，继续
                    continue
        
        return True
    
    def execute(
        self,
        command: str,
        require_confirmation: bool = False,
    ) -> Tuple[str, int, float, str]:
        """
        执行命令
        
        Args:
            command: 要执行的命令
            require_confirmation: 是否需要用户确认
            
        Returns:
            Tuple[str, int, float, str]: (输出, 行数, 执行时间, 错误信息)
            
        Raises:
            SearchExecutionError: 执行失败
        """
        # 验证命令
        is_safe, error_msg = self.validate_command(command)
        if not is_safe:
            raise SearchExecutionError(f"命令不安全: {error_msg}")
        
        # 用户确认（如果需要）
        if require_confirmation:
            self.logger.info(f"需要确认执行: {command}")
            # 这里可以添加交互式确认逻辑
        
        self.logger.info(f"执行命令: {command}")
        
        start_time = time.time()
        
        try:
            # 执行命令
            result = subprocess.run(
                command,
                shell=True,  # 需要shell来支持管道
                capture_output=True,
                text=True,
                timeout=self.timeout,
                encoding='utf-8',
                errors='replace',
                cwd=str(self.search_scope),  # 在搜索范围内执行
            )
            
            execution_time = time.time() - start_time
            
            # 获取输出
            output = result.stdout
            error_output = result.stderr
            
            # 检查返回码
            if result.returncode != 0 and not output:
                # 某些命令（如grep）找不到匹配时返回非0
                if error_output:
                    self.logger.warning(f"命令执行警告: {error_output}")
            
            # 检查结果大小
            if len(output.encode('utf-8')) > self.max_result_size:
                self.logger.warning(f"结果过大，截断到{self.max_result_size}字节")
                output_bytes = output.encode('utf-8')[:self.max_result_size]
                output = output_bytes.decode('utf-8', errors='ignore')
                output += "\n\n... (输出已截断)"
            
            # 统计行数
            line_count = len(output.splitlines()) if output else 0
            
            self.logger.info(
                f"命令执行完成: {line_count}行输出，耗时{execution_time:.2f}秒"
            )
            
            return output, line_count, execution_time, error_output
            
        except subprocess.TimeoutExpired:
            execution_time = time.time() - start_time
            self.logger.error(f"命令执行超时（{self.timeout}秒）")
            raise SearchExecutionError(f"命令执行超时（{self.timeout}秒）")
        
        except Exception as e:
            execution_time = time.time() - start_time
            self.logger.error(f"命令执行异常: {e}")
            raise SearchExecutionError(f"命令执行失败: {e}")
    
    def suggest_command_improvements(self, command: str) -> List[str]:
        """
        建议命令改进
        
        Args:
            command: 原始命令
            
        Returns:
            List[str]: 改进建议
        """
        suggestions = []
        
        # 检查是否缺少常用选项
        if command.startswith('grep') and '-n' not in command:
            suggestions.append("建议添加 -n 选项显示行号")
        
        if command.startswith('find') and '-type' not in command:
            suggestions.append("建议添加 -type 选项指定文件类型")
        
        if 'grep' in command and '-r' not in command and self.search_scope.is_dir():
            suggestions.append("建议添加 -r 选项递归搜索")
        
        return suggestions
    
    def get_safe_command_examples(self) -> List[str]:
        """
        获取安全命令示例
        
        Returns:
            List[str]: 示例命令列表
        """
        scope = str(self.search_scope)
        
        return [
            f"grep -rn 'function' {scope}",
            f"find {scope} -name '*.py' -type f",
            f"grep -rn 'class.*User' {scope} --include='*.py'",
            f"find {scope} -name 'config.*' | head -10",
            f"grep -rn 'TODO' {scope} | wc -l",
            f"ls -lah {scope}",
            f"find {scope} -type f -name '*.py' | wc -l",
            f"cat {scope}/README.md | head -20",
        ]
