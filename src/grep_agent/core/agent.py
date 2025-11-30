"""
Agent编排器 - 核心控制逻辑
"""
from typing import Optional
import copy

from ..core.models import (
    AppConfig,
    SearchSession,
    SessionStatus,
    SearchRecord,
    StrategyType,
)
from ..core.exceptions import SearchExecutionError, LLMConnectionError
from ..executors.grep_executor import GrepExecutor
from ..executors.result_processor import ResultProcessor
from ..strategies.strategy_manager import StrategyManager
from ..llm.llm_client import LLMClient
from ..llm.prompt_builder import PromptBuilder
from ..utils.logger import get_logger
from ..utils.validators import PathValidator, InputValidator


class SearchAgent:
    """搜索Agent编排器"""
    
    def __init__(self, config: AppConfig):
        """
        初始化搜索Agent
        
        Args:
            config: 应用配置
        """
        self.config = config
        self.logger = get_logger()
        
        # 初始化组件
        self.grep_executor = GrepExecutor(
            max_result_size=config.strategy.max_result_size
        )
        self.result_processor = ResultProcessor(
            enable_cache=config.system.enable_cache,
            cache_ttl=config.system.cache_ttl,
            preview_lines=config.system.result_preview_lines,
        )
        self.strategy_manager = StrategyManager(config.strategy)
        self.llm_client = LLMClient(config.llm)
        self.prompt_builder = PromptBuilder()
        
        # 检查grep是否可用
        if not self.grep_executor.test_grep_available():
            self.logger.warning("grep命令不可用，某些功能可能无法正常工作")
    
    def search(
        self,
        user_query: str,
        search_scope: Optional[str] = None,
        max_iterations: Optional[int] = None,
    ) -> SearchSession:
        """
        执行搜索任务
        
        Args:
            user_query: 用户查询
            search_scope: 搜索范围路径
            max_iterations: 最大搜索次数
            
        Returns:
            SearchSession: 搜索会话
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
        session = SearchSession(
            user_query=user_query,
            search_scope=search_scope,
            max_iterations=max_iterations,
            status=SessionStatus.RUNNING,
        )
        
        self.logger.info(
            f"开始搜索会话 {session.session_id}: "
            f"查询='{user_query}', 范围={search_scope}, 最大次数={max_iterations}"
        )
        
        try:
            # 执行搜索循环
            self._search_loop(session)
            
            # 标记为完成
            if session.final_answer:
                session.status = SessionStatus.COMPLETED
            else:
                session.status = SessionStatus.FAILED
            
            session.update_timestamp()
            
        except Exception as e:
            self.logger.error(f"搜索失败: {e}")
            session.status = SessionStatus.FAILED
            session.update_timestamp()
            raise
        
        return session
    
    def _search_loop(self, session: SearchSession):
        """
        搜索主循环
        
        Args:
            session: 搜索会话
        """
        # 获取初始策略
        strategy = self.strategy_manager.get_initial_strategy(session.user_query)
        
        while session.current_iteration < session.max_iterations:
            session.current_iteration += 1
            iteration_num = session.current_iteration
            
            self.logger.info(f"开始第{iteration_num}次搜索")
            
            # 执行搜索
            try:
                grep_cmd, search_result, result_count, execution_time = (
                    self.grep_executor.execute(
                        pattern=strategy.search_pattern,
                        search_path=session.search_scope,
                        options=strategy.grep_options,
                        strategy_type=strategy.strategy_type,
                    )
                )
            except SearchExecutionError as e:
                self.logger.error(f"搜索执行失败: {e}")
                # 记录失败的搜索
                failed_record = SearchRecord(
                    iteration_num=iteration_num,
                    strategy_type=strategy.strategy_type,
                    grep_command=str(e),
                    search_pattern=strategy.search_pattern,
                    search_options=strategy.grep_options,
                    execution_time=0.0,
                    result_count=0,
                    result_preview="搜索执行失败",
                )
                session.search_history.append(failed_record)
                
                # 尝试下一个策略
                strategy = self.strategy_manager.get_next_strategy(
                    current_iteration=iteration_num,
                    user_query=session.user_query,
                    previous_results_count=0,
                    llm_feedback=None,
                )
                continue
            
            # 处理结果
            result_preview = self.result_processor.create_preview(search_result)
            formatted_result = self.result_processor.format_result_for_llm(search_result)
            
            # 创建搜索记录
            search_record = SearchRecord(
                iteration_num=iteration_num,
                strategy_type=strategy.strategy_type,
                grep_command=grep_cmd,
                search_pattern=strategy.search_pattern,
                search_options=strategy.grep_options,
                execution_time=execution_time,
                result_count=result_count,
                result_preview=result_preview,
                full_result=search_result,
            )
            
            # 调用LLM分析结果
            llm_feedback = None
            try:
                llm_feedback = self._analyze_with_llm(
                    session=session,
                    iteration_num=iteration_num,
                    search_result=formatted_result,
                    strategy_type=strategy.strategy_type,
                )
                search_record.llm_feedback = llm_feedback
            except LLMConnectionError as e:
                self.logger.error(f"LLM调用失败: {e}")
                # LLM失败时继续使用预定义策略
            
            # 添加到历史
            session.search_history.append(search_record)
            session.update_timestamp()
            
            # 检查是否找到答案
            if llm_feedback and llm_feedback.is_sufficient:
                self.logger.info(f"LLM判断信息充足，置信度: {llm_feedback.confidence}")
                session.final_answer = llm_feedback.answer
                break
            
            # 检查是否达到最大次数
            if session.current_iteration >= session.max_iterations:
                self.logger.info("达到最大搜索次数")
                # 使用最后的分析作为答案
                if llm_feedback:
                    session.final_answer = (
                        f"经过{session.max_iterations}次搜索，未能找到完整答案。\n\n"
                        f"分析：{llm_feedback.analysis}\n\n"
                        f"建议：请尝试更精确的查询或扩大搜索范围。"
                    )
                else:
                    session.final_answer = (
                        f"经过{session.max_iterations}次搜索，共找到{result_count}行匹配。\n\n"
                        f"请查看搜索历史获取详细结果。"
                    )
                break
            
            # 获取下一个策略
            strategy = self.strategy_manager.get_next_strategy(
                current_iteration=iteration_num,
                user_query=session.user_query,
                previous_results_count=result_count,
                llm_feedback=llm_feedback,
            )
    
    def _analyze_with_llm(
        self,
        session: SearchSession,
        iteration_num: int,
        search_result: str,
        strategy_type: StrategyType,
    ):
        """
        使用LLM分析搜索结果
        
        Args:
            session: 搜索会话
            iteration_num: 当前迭代次数
            search_result: 搜索结果
            strategy_type: 策略类型
            
        Returns:
            LLMFeedback: LLM反馈
        """
        # 构建消息
        system_msg = self.prompt_builder.build_system_message()
        
        user_msg = self.prompt_builder.build_user_message(
            session_id=session.session_id,
            iteration_num=iteration_num,
            user_query=session.user_query,
            search_result=search_result,
            search_strategy=strategy_type.value,
            search_history=session.search_history[:-1] if len(session.search_history) > 0 else [],
            remaining_iterations=session.max_iterations - session.current_iteration,
        )
        
        messages = [system_msg, user_msg]
        
        # 压缩上下文（如果需要）
        messages = self.prompt_builder.compress_context(messages)
        
        # 调用LLM
        response = self.llm_client.call_llm(messages)
        
        # 解析响应
        feedback = self.llm_client.parse_llm_response(response)
        
        return feedback
