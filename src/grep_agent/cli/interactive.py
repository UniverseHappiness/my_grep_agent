"""
CLI交互模块
"""
import click
from typing import Optional

from ..core.config import ConfigManager
from ..core.models import AppConfig, SessionStatus
from ..core.agent import SearchAgent
from ..utils.logger import get_logger


def run_cli(config: AppConfig):
    """
    运行CLI交互模式
    
    Args:
        config: 应用配置
    """
    logger = get_logger()
    logger.info("启动CLI交互模式")
    
    # 创建Agent
    agent = SearchAgent(config)
    
    # 欢迎信息
    click.echo("=" * 60)
    click.echo("Grep搜索Agent - 智能化代码搜索助手")
    click.echo("=" * 60)
    click.echo("\n输入'help'查看帮助，输入'exit'退出\n")
    
    # 交互循环
    while True:
        try:
            # 获取用户输入
            query = click.prompt("\n请输入搜索查询", type=str).strip()
            
            if not query:
                continue
            
            # 处理命令
            if query.lower() == 'exit':
                click.echo("再见！")
                break
            
            elif query.lower() == 'help':
                show_help()
                continue
            
            elif query.lower().startswith('config'):
                handle_config_command(query, config)
                continue
            
            # 获取搜索参数
            search_scope = click.prompt(
                "搜索范围",
                default=config.system.default_search_scope,
                type=str,
            )
            
            max_iterations = click.prompt(
                "最大搜索次数",
                default=config.system.default_max_iterations,
                type=int,
            )
            
            # 执行搜索
            click.echo(f"\n🔍 开始搜索: {query}")
            click.echo(f"   范围: {search_scope}")
            click.echo(f"   最大次数: {max_iterations}\n")
            
            try:
                session = agent.search(
                    user_query=query,
                    search_scope=search_scope,
                    max_iterations=max_iterations,
                )
                
                # 显示结果
                display_search_result(session)
                
            except Exception as e:
                click.echo(f"\n❌ 搜索失败: {e}", err=True)
                logger.error(f"搜索异常: {e}", exc_info=True)
        
        except KeyboardInterrupt:
            click.echo("\n\n操作已取消")
            if click.confirm("是否退出？"):
                break
        
        except Exception as e:
            click.echo(f"\n错误: {e}", err=True)
            logger.error(f"CLI异常: {e}", exc_info=True)


def show_help():
    """显示帮助信息"""
    help_text = """
可用命令:
    
    search <query>  - 执行搜索查询
    config list     - 查看当前配置
    config get <key>- 获取配置值
    help            - 显示此帮助信息
    exit            - 退出程序

搜索示例:
    - "find user authentication function"
    - "查找配置文件中的数据库连接"
    - "搜索错误处理相关代码"
    """
    click.echo(help_text)


def handle_config_command(command: str, config: AppConfig):
    """
    处理config命令
    
    Args:
        command: 命令字符串
        config: 配置对象
    """
    parts = command.split()
    
    if len(parts) < 2:
        click.echo("用法: config list | config get <key>")
        return
    
    action = parts[1].lower()
    
    if action == 'list':
        click.echo("\n当前配置:")
        click.echo(f"  默认搜索范围: {config.system.default_search_scope}")
        click.echo(f"  默认最大次数: {config.system.default_max_iterations}")
        click.echo(f"  日志级别: {config.system.log_level}")
        click.echo(f"  LLM模型: {config.llm.model_name}")
        click.echo(f"  策略模式: {config.strategy.strategy_mode.value}")
    
    elif action == 'get':
        if len(parts) < 3:
            click.echo("用法: config get <key>")
            return
        
        key = parts[2]
        # 简单实现
        click.echo(f"配置项 {key} 的值获取功能待实现")


def display_search_result(session):
    """
    显示搜索结果
    
    Args:
        session: 搜索会话
    """
    click.echo("\n" + "=" * 60)
    click.echo("搜索结果")
    click.echo("=" * 60)
    
    # 状态
    if session.status == SessionStatus.COMPLETED:
        status_icon = "✅"
        status_text = "完成"
    elif session.status == SessionStatus.FAILED:
        status_icon = "❌"
        status_text = "失败"
    else:
        status_icon = "⏳"
        status_text = session.status.value
    
    click.echo(f"\n状态: {status_icon} {status_text}")
    click.echo(f"搜索次数: {session.current_iteration}/{session.max_iterations}")
    
    # 搜索历史摘要
    if session.search_history:
        click.echo(f"\n搜索历史:")
        for record in session.search_history:
            click.echo(
                f"  {record.iteration_num}. [{record.strategy_type.value}] "
                f"'{record.search_pattern}' - {record.result_count}行, "
                f"{record.execution_time:.2f}秒"
            )
    
    # 最终答案
    if session.final_answer:
        click.echo(f"\n{'='*60}")
        click.echo("答案:")
        click.echo("=" * 60)
        click.echo(f"\n{session.final_answer}\n")
    else:
        click.echo("\n未找到满意的答案")
    
    # 询问是否查看详细结果
    if session.search_history and click.confirm("\n是否查看详细搜索结果？", default=False):
        for i, record in enumerate(session.search_history, 1):
            click.echo(f"\n--- 第{i}次搜索 ---")
            click.echo(f"策略: {record.strategy_type.value}")
            click.echo(f"命令: {record.grep_command}")
            click.echo(f"\n结果预览:\n{record.result_preview[:500]}")
            
            if i < len(session.search_history):
                if not click.confirm("继续查看下一个？", default=True):
                    break
