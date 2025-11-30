"""
增强版CLI交互模块 - 支持LLM自动生成命令
"""
import click
from typing import Optional

from ..core.config import ConfigManager
from ..core.models import AppConfig, SessionStatus
from ..core.enhanced_agent import EnhancedSearchAgent, EnhancedSearchSession
from ..utils.logger import get_logger


def run_enhanced_cli(config: AppConfig):
    """
    运行增强版CLI交互模式
    
    Args:
        config: 应用配置
    """
    logger = get_logger()
    logger.info("启动增强版CLI交互模式")
    
    # 创建增强版Agent
    agent = EnhancedSearchAgent(config)
    
    # 欢迎信息
    click.echo("=" * 70)
    click.echo("Grep搜索Agent - 增强版（支持LLM自动生成Linux命令）")
    click.echo("=" * 70)
    click.echo("\n✨ 新特性：")
    click.echo("  - LLM可以自动生成各种Linux命令（grep、find、cat等）")
    click.echo("  - 更智能的上下文管理")
    click.echo("  - 支持命令链和管道")
    click.echo("\n输入'help'查看帮助，输入'exit'退出\n")
    
    # 交互循环
    while True:
        try:
            # 获取用户输入
            query = click.prompt("\n📝 请输入搜索查询", type=str).strip()
            
            if not query:
                continue
            
            # 处理命令
            if query.lower() == 'exit':
                click.echo("再见！")
                break
            
            elif query.lower() == 'help':
                show_enhanced_help()
                continue
            
            elif query.lower().startswith('config'):
                handle_config_command(query, config)
                continue
            
            elif query.lower() == 'examples':
                show_command_examples()
                continue
            
            # 获取搜索参数
            search_scope = click.prompt(
                "🔍 搜索范围",
                default=config.system.default_search_scope,
                type=str,
            )
            
            max_iterations = click.prompt(
                "🔢 最大命令执行次数",
                default=config.system.default_max_iterations,
                type=int,
            )
            
            require_confirmation = click.confirm(
                "⚠️  是否需要确认每个命令（安全模式）",
                default=False,
            )
            
            # 执行搜索
            click.echo(f"\n🚀 开始智能搜索...")
            click.echo(f"   查询: {query}")
            click.echo(f"   范围: {search_scope}")
            click.echo(f"   最大次数: {max_iterations}\n")
            
            try:
                session = agent.search(
                    user_query=query,
                    search_scope=search_scope,
                    max_iterations=max_iterations,
                    require_confirmation=require_confirmation,
                )
                
                # 显示结果
                display_enhanced_result(session)
                
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


def show_enhanced_help():
    """显示增强版帮助信息"""
    help_text = """
╔══════════════════════════════════════════════════════════════╗
║                    增强版功能说明                              ║
╚══════════════════════════════════════════════════════════════╝

可用命令:
    help         - 显示此帮助信息
    examples     - 查看命令示例
    config list  - 查看当前配置
    exit         - 退出程序

增强特性:
    1. LLM自动生成Linux命令
       - 根据你的问题，自动选择合适的命令
       - 支持grep、find、cat、ls、wc等常用命令
       - 智能组合多个命令（管道）

    2. 更好的上下文管理
       - 保留完整的命令执行历史
       - LLM可以看到之前的所有尝试
       - 避免重复执行相同的命令

    3. 安全机制
       - 命令白名单（只允许安全的只读命令）
       - 危险命令自动拦截
       - 可选的用户确认模式

搜索示例:
    • "查找所有Python文件"
      → LLM可能生成: find . -name '*.py' -type f

    • "统计代码行数"
      → LLM可能生成: find . -name '*.py' | xargs wc -l

    • "查找包含TODO的代码"
      → LLM可能生成: grep -rn 'TODO' . --include='*.py'

    • "查看配置文件内容"
      → LLM可能生成: find . -name 'config.*' | xargs cat
    """
    click.echo(help_text)


def show_command_examples():
    """显示命令示例"""
    click.echo("\n📚 LLM可能生成的命令示例：\n")
    
    examples = [
        ("查找文件", "find /path -name '*.py' -type f"),
        ("搜索内容", "grep -rn 'pattern' /path --include='*.py'"),
        ("查看文件", "cat /path/file.txt | head -20"),
        ("统计行数", "wc -l /path/*.py"),
        ("列出目录", "ls -lah /path"),
        ("文件类型", "file /path/*"),
        ("目录大小", "du -sh /path/*"),
        ("排序去重", "grep -rn 'TODO' . | sort | uniq"),
    ]
    
    for i, (desc, cmd) in enumerate(examples, 1):
        click.echo(f"  {i}. {desc}")
        click.echo(f"     {cmd}\n")


def handle_config_command(command: str, config: AppConfig):
    """处理config命令"""
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
        click.echo(f"  LLM端点: {config.llm.api_endpoint}")


def display_enhanced_result(session: EnhancedSearchSession):
    """
    显示增强版搜索结果
    
    Args:
        session: 搜索会话
    """
    click.echo("\n" + "=" * 70)
    click.echo("搜索结果")
    click.echo("=" * 70)
    
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
    click.echo(f"执行命令数: {session.current_iteration}/{session.max_iterations}")
    
    # 命令历史
    if session.command_history:
        click.echo(f"\n📜 命令执行历史:")
        for i, record in enumerate(session.command_history, 1):
            click.echo(f"\n  {i}. 命令: {record['command']}")
            click.echo(f"     目的: {record['purpose']}")
            click.echo(f"     结果: {record['result_lines']}行，耗时{record['execution_time']:.2f}秒")
            if record.get('error'):
                click.echo(f"     ⚠️  错误: {record['error']}")
    
    # 最终答案
    if session.final_answer:
        click.echo(f"\n{'='*70}")
        click.echo("💡 答案:")
        click.echo("=" * 70)
        click.echo(f"\n{session.final_answer}\n")
    else:
        click.echo("\n未找到满意的答案")
    
    # 询问是否查看详细输出
    if session.command_history and click.confirm("\n🔍 是否查看详细命令输出？", default=False):
        for i, record in enumerate(session.command_history, 1):
            click.echo(f"\n{'='*70}")
            click.echo(f"命令 {i}: {record['command']}")
            click.echo("=" * 70)
            
            output = record['output']
            if len(output) > 1000:
                click.echo(output[:1000])
                if click.confirm(f"\n还有{len(output)-1000}字符，是否查看完整输出？", default=False):
                    click.echo(output[1000:])
            else:
                click.echo(output)
            
            if i < len(session.command_history):
                if not click.confirm("\n继续查看下一个？", default=True):
                    break
