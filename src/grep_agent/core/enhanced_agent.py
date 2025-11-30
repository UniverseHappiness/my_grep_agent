"""
增强版Agent - 支持LLM自动生成Linux命令
"""
from typing import Optional, List, Dict, Any
import copy

from ..core.models import AppConfig, SessionStatus
from ..core.exceptions import SearchExecutionError, LLMConnectionError
from ..executors.command_executor import CommandExecutor
from ..llm.llm_client import LLMClient
from ..llm.enhanced_prompt_builder import EnhancedPromptBuilder
from ..llm.enhanced_response_parser import EnhancedResponseParser
from ..utils.logger import get_logger
from ..utils.validators import PathValidator, InputValidator


class EnhancedSearchSession:
    """增强版搜索会话"""
    
    def __init__(
        self,
        session_id: str,
        user_query: str,
        search_scope: str,
        max_iterations: int,
    ):
        """初始化会话"""
        self.session_id = session_id
        self.user_query = user_query
        self.search_scope = search_scope
        self.max_iterations = max_iterations
        self.current_iteration = 0
        self.status = SessionStatus.INIT
        self.command_history: List[Dict[str, Any]] = []
        self.final_answer: Optional[str] = None
        self.created_at = None
        self.updated_at = None
        self.total_execution_time: float = 0.0  # 总执行时间
    
    @property
    def search_history(self) -> List[Any]:
        """返回搜索历史（为了兼容）"""
        # 将command_history转换为具有属性访问的对象
        class Record:
            def __init__(self, data: dict):
                self.command = data.get('command', '')
                self.purpose = data.get('purpose', '')
                self.execution_time = data.get('execution_time', 0.0)
                self.result_count = data.get('result_lines', 0)
                self.error = data.get('error')
        
        return [Record(cmd) for cmd in self.command_history]
    
    def add_command_record(
        self,
        command: str,
        purpose: str,
        output: str,
        execution_time: float,
        result_lines: int,
        error: Optional[str] = None,
    ):
        """添加命令执行记录"""
        self.command_history.append({
            'iteration': self.current_iteration,
            'command': command,
            'purpose': purpose,
            'output': output,
            'execution_time': execution_time,
            'result_lines': result_lines,
            'error': error,
        })
        # 累加总执行时间
        self.total_execution_time += execution_time


class EnhancedSearchAgent:
    """增强版搜索Agent"""
    
    def __init__(self, config: AppConfig):
        """
        初始化增强版Agent
        
        Args:
            config: 应用配置
        """
        self.config = config
        self.logger = get_logger()
        
        # 初始化组件
        self.llm_client = LLMClient(config.llm)
        self.prompt_builder = EnhancedPromptBuilder()
        self.response_parser = EnhancedResponseParser()
        
        self.logger.info("增强版搜索Agent初始化完成")
    
    def search(
        self,
        user_query: str,
        search_scope: Optional[str] = None,
        max_iterations: Optional[int] = None,
        require_confirmation: bool = False,
    ) -> EnhancedSearchSession:
        """
        执行搜索任务
        
        Args:
            user_query: 用户查询
            search_scope: 搜索范围
            max_iterations: 最大迭代次数
            require_confirmation: 是否需要用户确认每个命令
            
        Returns:
            EnhancedSearchSession: 搜索会话
        """
        # 验证输入
        user_query = InputValidator.validate_query(user_query)
        
        if search_scope is None:
            search_scope = self.config.system.default_search_scope
        
        search_scope = PathValidator.validate_search_path(search_scope)
        
        if max_iterations is None:
            max_iterations = self.config.system.default_max_iterations
        
        max_iterations = InputValidator.validate_max_iterations(max_iterations)
        
        # 创建会话
        import uuid
        from datetime import datetime
        
        session = EnhancedSearchSession(
            session_id=str(uuid.uuid4()),
            user_query=user_query,
            search_scope=search_scope,
            max_iterations=max_iterations,
        )
        session.created_at = datetime.now()
        session.status = SessionStatus.RUNNING
        
        # 创建命令执行器
        executor = CommandExecutor(
            search_scope=search_scope,
            max_result_size=self.config.strategy.max_result_size,
            timeout=30,
            allow_pipes=True,
        )
        
        self.logger.info(
            f"开始增强搜索会话 {session.session_id}: "
            f"查询='{user_query}', 范围={search_scope}, 最大次数={max_iterations}"
        )
        
        try:
            # 执行搜索循环
            self._search_loop(session, executor, require_confirmation)
            
            # 标记为完成
            session.status = SessionStatus.COMPLETED if session.final_answer else SessionStatus.FAILED
            session.updated_at = datetime.now()
            
        except Exception as e:
            self.logger.error(f"搜索失败: {e}", exc_info=True)
            session.status = SessionStatus.FAILED
            session.updated_at = datetime.now()
            raise
        
        return session
    
    def _search_loop(
        self,
        session: EnhancedSearchSession,
        executor: CommandExecutor,
        require_confirmation: bool,
    ):
        """
        搜索主循环
        
        Args:
            session: 搜索会话
            executor: 命令执行器
            require_confirmation: 是否需要确认
        """
        # 构建系统消息
        messages = [self.prompt_builder.build_system_message()]
        
        # 构建初始消息
        initial_msg = self.prompt_builder.build_initial_message(
            session_id=session.session_id,
            user_query=session.user_query,
            search_scope=session.search_scope,
            max_iterations=session.max_iterations,
        )
        messages.append(initial_msg)
        
        while session.current_iteration < session.max_iterations:
            session.current_iteration += 1
            iteration = session.current_iteration
            
            self.logger.info(f"=== 第{iteration}次迭代 ===")
            
            try:
                # 调用LLM获取分析或下一个命令
                compressed_messages = self.prompt_builder.compress_context(messages)
                llm_response = self.llm_client.call_llm(compressed_messages)
                
                # 解析响应
                parsed = self.response_parser.parse_response(llm_response)
                
                self.logger.info(f"LLM分析: {parsed['analysis'][:300]}...")
                self.logger.info(f"信息充足: {parsed['is_sufficient']}, 置信度: {parsed['confidence']}")
                self.logger.info(f"llm_response: {llm_response}")
                self.logger.info(f"parsed:  {parsed}")
                
                # 检查是否已经足够
                if parsed['is_sufficient']:
                    self.logger.info("LLM判断信息已充足")
                    session.final_answer = parsed.get('answer') or parsed['analysis']
                    break
                
                # 获取下一个命令
                next_cmd_info = parsed.get('next_command')
                if not next_cmd_info:
                    self.logger.warning("LLM未提供下一个命令")
                    session.final_answer = (
                        f"经过{iteration}次尝试，未能获得足够信息。\n\n"
                        f"最后分析：{parsed['analysis']}"
                    )
                    break
                
                command = next_cmd_info['command']
                purpose = next_cmd_info.get('purpose', '探索信息')
                
                self.logger.info(f"准备执行命令: {command}")
                self.logger.info(f"命令目的: {purpose}")
                
                # 执行命令
                try:
                    output, line_count, exec_time, error = executor.execute(
                        command=command,
                        require_confirmation=require_confirmation,
                    )
                    
                    # 记录命令执行
                    session.add_command_record(
                        command=command,
                        purpose=purpose,
                        output=output,
                        execution_time=exec_time,
                        result_lines=line_count,
                        error=error,
                    )
                    
                    # 构建下一轮消息
                    next_msg = self.prompt_builder.build_iteration_message(
                        session_id=session.session_id,
                        iteration_num=iteration,
                        user_query=session.user_query,
                        command_history=session.command_history,
                        last_command=command,
                        last_output=output,
                        remaining_iterations=session.max_iterations - iteration,
                    )
                    messages.append(next_msg)
                    
                except SearchExecutionError as e:
                    self.logger.error(f"命令执行失败: {e}")
                    
                    # 记录失败
                    session.add_command_record(
                        command=command,
                        purpose=purpose,
                        output="",
                        execution_time=0.0,
                        result_lines=0,
                        error=str(e),
                    )
                    
                    # 告诉LLM命令失败了
                    error_msg = self.prompt_builder.build_iteration_message(
                        session_id=session.session_id,
                        iteration_num=iteration,
                        user_query=session.user_query,
                        command_history=session.command_history,
                        last_command=command,
                        last_output=f"错误: {str(e)}",
                        remaining_iterations=session.max_iterations - iteration,
                    )
                    messages.append(error_msg)
                
            except LLMConnectionError as e:
                self.logger.error(f"LLM调用失败: {e}")
                session.final_answer = f"LLM调用失败: {e}\n\n请检查API配置和网络连接。"
                break
            
            except Exception as e:
                self.logger.error(f"迭代异常: {e}", exc_info=True)
                continue
        
        # 如果达到最大次数仍未找到答案
        if not session.final_answer:
            self.logger.info("达到最大迭代次数")
            
            # 最后一次尝试获取总结
            summary_msg = self.prompt_builder.build_iteration_message(
                session_id=session.session_id,
                iteration_num=session.current_iteration,
                user_query=session.user_query,
                command_history=session.command_history,
                last_command="总结",
                last_output="已达到最大搜索次数，请基于现有信息给出最佳答案。",
                remaining_iterations=0,
            )
            messages.append(summary_msg)
            
            try:
                final_response = self.llm_client.call_llm(messages[-2:])  # 只用最后的消息
                final_parsed = self.response_parser.parse_response(final_response)
                session.final_answer = final_parsed.get('answer') or final_parsed['analysis']
            except Exception as e:
                self.logger.error(f"获取最终总结失败: {e}")
                session.final_answer = (
                    f"经过{session.max_iterations}次命令执行，收集了以下信息：\n\n"
                    + self._format_command_summary(session.command_history)
                )
    
    def _format_command_summary(self, history: List[Dict[str, Any]]) -> str:
        """
        格式化命令历史摘要
        
        Args:
            history: 命令历史
            
        Returns:
            str: 格式化的摘要
        """
        lines = []
        for i, record in enumerate(history, 1):
            lines.append(
                f"{i}. {record['command']}\n"
                f"   目的: {record['purpose']}\n"
                f"   结果: {record['result_lines']}行，耗时{record['execution_time']:.2f}秒"
            )
        return "\n\n".join(lines)
