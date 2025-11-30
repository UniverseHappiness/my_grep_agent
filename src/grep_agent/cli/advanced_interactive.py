"""
高级CLI交互模块 - 使用prompt_toolkit提供专业的命令行体验
"""
from typing import Optional, List
from datetime import datetime

from prompt_toolkit import PromptSession
from prompt_toolkit.history import InMemoryHistory
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.formatted_text import HTML
from prompt_toolkit.styles import Style
from prompt_toolkit.key_binding import KeyBindings

from ..core.config import ConfigManager
from ..core.models import AppConfig, SessionStatus
from ..core.enhanced_agent import EnhancedSearchAgent, EnhancedSearchSession
from ..utils.logger import get_logger


# 自定义样式
cli_style = Style.from_dict({
    'prompt': '#00aa00 bold',
    'path': '#884444 italic',
    'command': '#0066ff',
    'success': '#00aa00',
    'error': '#aa0000',
    'warning': '#aa5500',
    'info': '#0088aa',
    'header': '#aa00aa bold',
    'subtitle': '#888888 italic',
})


class AdvancedCLI:
    """高级命令行交互界面"""
    
    def __init__(self, config: AppConfig):
        """
        初始化高级CLI
        
        Args:
            config: 应用配置
        """
        self.config = config
        self.agent = EnhancedSearchAgent(config)
        self.logger = get_logger()
        
        # 创建历史记录
        self.history = InMemoryHistory()
        
        # 创建命令补全
        self.command_completer = WordCompleter(
            ['help', 'exit', 'quit', 'examples', 'config list', 'history', 'clear'],
            ignore_case=True,
        )
        
        # 创建会话
        self.session = PromptSession(
            history=self.history,
            auto_suggest=AutoSuggestFromHistory(),
            completer=self.command_completer,
            style=cli_style,
        )
        
        # 搜索历史
        self.search_history: List[dict] = []
    
    def run(self):
        """运行CLI主循环"""
        self.logger.info("启动高级CLI交互模式")
        
        # 显示欢迎信息
        self._show_welcome()
        
        # 主循环
        while True:
            try:
                # 获取用户输入（支持历史、自动补全、方向键等）
                query = self.session.prompt(
                    HTML('<prompt>📝 搜索查询</prompt> <subtitle>(输入help查看帮助)</subtitle>: '),
                    style=cli_style,
                ).strip()
                
                if not query:
                    continue
                
                # 处理命令
                if query.lower() in ['exit', 'quit']:
                    if self._confirm_exit():
                        break
                    continue
                
                elif query.lower() == 'help':
                    self._show_help()
                    continue
                
                elif query.lower() == 'examples':
                    self._show_examples()
                    continue
                
                elif query.lower().startswith('config'):
                    self._handle_config(query)
                    continue
                
                elif query.lower() == 'history':
                    self._show_search_history()
                    continue
                
                elif query.lower() == 'clear':
                    self._clear_screen()
                    continue
                
                # 执行搜索
                self._execute_search(query)
                
            except KeyboardInterrupt:
                print("\n")
                if self._confirm_exit():
                    break
            
            except EOFError:
                break
            
            except Exception as e:
                self._print_error(f"错误: {e}")
                self.logger.error(f"CLI异常: {e}", exc_info=True)
    
    def _show_welcome(self):
        """显示欢迎信息"""
        print("\n" + "=" * 70)
        print("🔍 Grep搜索Agent - 高级交互模式")
        print("=" * 70)
        print("\n✨ 功能特性：")
        print("  ✅ 支持方向键：⬆️⬇️ 浏览历史命令，⬅️➡️ 移动光标编辑")
        print("  ✅ 自动补全：按Tab键补全命令")
        print("  ✅ 智能建议：根据历史自动推荐")
        print("  ✅ LLM自动生成Linux命令")
        print("  ✅ 完整的命令执行历史")
        print("\n💡 提示：输入 'help' 查看帮助，'examples' 查看示例\n")
    
    def _show_help(self):
        """显示帮助信息"""
        help_text = """
╔══════════════════════════════════════════════════════════════╗
║                    命令和功能说明                              ║
╚══════════════════════════════════════════════════════════════╝

📌 基本命令：
    help         - 显示此帮助信息
    examples     - 查看命令示例和用法
    config list  - 查看当前配置
    history      - 查看搜索历史
    clear        - 清屏
    exit / quit  - 退出程序

⌨️  键盘快捷键：
    ⬆️ / ⬇️      - 浏览历史命令
    ⬅️ / ➡️      - 移动光标编辑
    Ctrl+A      - 移到行首
    Ctrl+E      - 移到行尾
    Ctrl+K      - 删除到行尾
    Ctrl+U      - 删除到行首
    Ctrl+W      - 删除前一个单词
    Tab         - 自动补全
    Ctrl+C      - 取消当前操作
    Ctrl+D      - 退出（EOF）

🤖 智能搜索：
    • 直接输入你的问题，LLM会自动生成合适的Linux命令
    • 支持grep、find、cat、ls、wc等20+种安全命令
    • 自动组合命令和管道
    • 智能上下文管理，避免重复搜索

🛡️  安全保障：
    • 命令白名单机制
    • 危险命令自动拦截
    • 路径访问控制
    • 可选的命令确认模式

📝 搜索示例：
    • "查找所有Python文件"
    • "统计代码总行数"
    • "查找包含TODO的代码"
    • "查看README文件内容"
    • "列出所有配置文件"
        """
        print(help_text)
    
    def _show_examples(self):
        """显示命令示例"""
        examples_text = """
╔══════════════════════════════════════════════════════════════╗
║                    搜索示例和说明                              ║
╚══════════════════════════════════════════════════════════════╝

1️⃣  文件查找类：
   
   查询: "查找所有Python文件"
   → LLM生成: find . -name '*.py' -type f
   
   查询: "找出大于1MB的日志文件"
   → LLM生成: find . -name '*.log' -size +1M -type f
   
   查询: "列出最近修改的文件"
   → LLM生成: ls -lt | head -10

2️⃣  内容搜索类：
   
   查询: "查找包含TODO的代码"
   → LLM生成: grep -rn 'TODO' . --include='*.py'
   
   查询: "搜索包含error或warning的日志"
   → LLM生成: grep -rn 'error\|warning' . --include='*.log'
   
   查询: "查找函数定义"
   → LLM生成: grep -rn 'def function_name' . --include='*.py'

3️⃣  统计分析类：
   
   查询: "统计代码总行数"
   → LLM生成: find . -name '*.py' | xargs wc -l
   
   查询: "统计每个文件的行数"
   → LLM生成: wc -l *.py
   
   查询: "统计TODO的数量"
   → LLM生成: grep -rn 'TODO' . | wc -l

4️⃣  文件查看类：
   
   查询: "查看README文件内容"
   → LLM生成: cat README.md
   
   查询: "查看配置文件的前20行"
   → LLM生成: head -20 config.yaml
   
   查询: "查看日志文件的最后100行"
   → LLM生成: tail -100 app.log

5️⃣  组合查询类：
   
   查询: "找出包含class定义的Python文件"
   → LLM生成: find . -name '*.py' | xargs grep -l 'class '
   
   查询: "统计每个目录的文件数"
   → LLM生成: find . -type f | awk -F/ '{print $2}' | sort | uniq -c
   
   查询: "查找并显示所有TODO注释"
   → LLM生成: grep -rn 'TODO' . --include='*.py' | sort

💡 提示：
   - 使用自然语言描述你的需求即可
   - LLM会根据上下文选择最合适的命令
   - 如果第一次搜索结果不够，LLM会自动调整策略
        """
        print(examples_text)
    
    def _handle_config(self, command: str):
        """处理config命令"""
        parts = command.split()
        
        if len(parts) < 2 or parts[1].lower() != 'list':
            self._print_info("用法: config list")
            return
        
        print("\n⚙️  当前配置：")
        print(f"  📁 默认搜索范围: {self.config.system.default_search_scope}")
        print(f"  🔢 默认最大次数: {self.config.system.default_max_iterations}")
        print(f"  📊 日志级别: {self.config.system.log_level}")
        print(f"  🤖 LLM模型: {self.config.llm.model_name}")
        print(f"  🌐 LLM端点: {self.config.llm.api_endpoint}")
        print()
    
    def _show_search_history(self):
        """显示搜索历史"""
        if not self.search_history:
            self._print_info("暂无搜索历史")
            return
        
        print("\n📚 搜索历史：\n")
        for i, record in enumerate(self.search_history[-10:], 1):  # 只显示最近10条
            print(f"{i}. [{record['time']}] {record['query']}")
            print(f"   状态: {record['status']} | 执行次数: {record['iterations']}")
            if record.get('answer'):
                answer_preview = record['answer'][:80] + '...' if len(record['answer']) > 80 else record['answer']
                print(f"   结果: {answer_preview}")
            print()
    
    def _clear_screen(self):
        """清屏"""
        import os
        os.system('clear' if os.name != 'nt' else 'cls')
        self._show_welcome()
    
    def _execute_search(self, query: str):
        """
        执行搜索
        
        Args:
            query: 用户查询
        """
        # 获取搜索参数（使用新的提示方式）
        search_scope = self.session.prompt(
            HTML('<info>🔍 搜索范围</info>: '),
            default=self.config.system.default_search_scope,
            style=cli_style,
        ).strip()
        
        max_iterations_str = self.session.prompt(
            HTML('<info>🔢 最大命令执行次数</info>: '),
            default=str(self.config.system.default_max_iterations),
            style=cli_style,
        ).strip()
        
        try:
            max_iterations = int(max_iterations_str)
        except ValueError:
            max_iterations = self.config.system.default_max_iterations
        
        require_confirmation_str = self.session.prompt(
            HTML('<warning>⚠️  是否需要确认每个命令（y/n）</warning>: '),
            default='n',
            style=cli_style,
        ).strip().lower()
        
        require_confirmation = require_confirmation_str in ['y', 'yes', '是']
        
        # 显示搜索信息
        print(f"\n{'='*70}")
        print(f"🚀 开始智能搜索")
        print(f"{'='*70}")
        print(f"📝 查询: {query}")
        print(f"📁 范围: {search_scope}")
        print(f"🔢 最大次数: {max_iterations}")
        print(f"⚠️  确认模式: {'是' if require_confirmation else '否'}")
        print(f"{'='*70}\n")
        
        # 执行搜索
        start_time = datetime.now()
        
        try:
            session = self.agent.search(
                user_query=query,
                search_scope=search_scope,
                max_iterations=max_iterations,
                require_confirmation=require_confirmation,
            )
            
            # 记录历史
            self.search_history.append({
                'time': start_time.strftime('%Y-%m-%d %H:%M:%S'),
                'query': query,
                'status': session.status.value,
                'iterations': session.current_iteration,
                'answer': session.final_answer,
            })
            
            # 显示结果
            self._display_result(session)
            
        except Exception as e:
            self._print_error(f"搜索失败: {e}")
            self.logger.error(f"搜索异常: {e}", exc_info=True)
    
    def _display_result(self, session: EnhancedSearchSession):
        """
        显示搜索结果
        
        Args:
            session: 搜索会话
        """
        print(f"\n{'='*70}")
        print(f"📊 搜索完成")
        print(f"{'='*70}")
        print(f"🏷️  会话ID: {session.session_id}")
        print(f"📍 状态: {self._format_status(session.status)}")
        print(f"🔄 执行轮次: {session.current_iteration}/{session.max_iterations}")
        print(f"⏱️  总耗时: {session.total_execution_time:.2f}秒")
        print(f"{'='*70}\n")
        
        # 显示命令历史
        if session.search_history:
            print("📜 命令执行历史：\n")
            for i, record in enumerate(session.search_history, 1):
                print(f"  {i}. 命令: {record.command}")
                print(f"     目的: {record.purpose}")
                print(f"     结果: {record.result_count}行，耗时{record.execution_time:.2f}秒")
                if record.error:
                    print(f"     ⚠️  错误: {record.error}")
                print()
        
        # 显示最终答案
        if session.final_answer:
            print(f"{'='*70}")
            print("✅ 最终答案：\n")
            print(session.final_answer)
            print(f"\n{'='*70}\n")
        else:
            self._print_warning("未能获得最终答案，请查看命令执行历史")
    
    def _format_status(self, status: SessionStatus) -> str:
        """格式化状态显示"""
        status_map = {
            SessionStatus.COMPLETED: "✅ 已完成",
            SessionStatus.RUNNING: "🔄 运行中",
            SessionStatus.FAILED: "❌ 失败",
            SessionStatus.INIT: "🆕 初始化",
        }
        return status_map.get(status, str(status.value))
    
    def _confirm_exit(self) -> bool:
        """确认退出"""
        try:
            response = self.session.prompt(
                HTML('<warning>❓ 确定要退出吗？(y/n)</warning>: '),
                default='n',
                style=cli_style,
            ).strip().lower()
            return response in ['y', 'yes', '是']
        except:
            return True
    
    def _print_success(self, message: str):
        """打印成功消息"""
        print(f"\n✅ {message}\n")
    
    def _print_error(self, message: str):
        """打印错误消息"""
        print(f"\n❌ {message}\n")
    
    def _print_warning(self, message: str):
        """打印警告消息"""
        print(f"\n⚠️  {message}\n")
    
    def _print_info(self, message: str):
        """打印信息消息"""
        print(f"\n💡 {message}\n")


def run_advanced_cli(config: AppConfig):
    """
    运行高级CLI交互模式
    
    Args:
        config: 应用配置
    """
    cli = AdvancedCLI(config)
    cli.run()
