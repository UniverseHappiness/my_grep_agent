"""
主入口文件
"""
import sys
import os
from pathlib import Path

# 添加src目录到Python路径
src_path = Path(__file__).parent
sys.path.insert(0, str(src_path))

import click
from grep_agent.core.config import config_manager
from grep_agent.utils.logger import logger_manager, get_logger


@click.command()
@click.option(
    '--mode', '-m',
    type=click.Choice(['cli', 'api', 'enhanced', 'advanced']),
    default='advanced',
    help='运行模式：cli（命令行）、api（API服务）、enhanced（增强版CLI）、advanced（高级CLI）'
)
@click.option(
    '--config', '-c',
    type=click.Path(exists=True),
    default='./config/config.yaml',
    help='配置文件路径'
)
@click.option(
    '--verbose', '-v',
    is_flag=True,
    help='详细输出模式'
)
@click.option(
    '--log-file', '-l',
    type=str,
    default='./logs/agent.log',
    help='日志文件路径'
)
def main(mode: str, config: str, verbose: bool, log_file: str):
    """
    Grep搜索Agent - 智能化的grep搜索助手
    
    支持命令行交互和API服务两种模式
    """
    try:
        # 加载配置
        app_config = config_manager.load_config(config)
        
        # 设置日志
        log_level = "DEBUG" if verbose else app_config.system.log_level
        logger_manager.setup_logger(
            log_level=log_level,
            log_file=log_file,
        )
        
        logger = get_logger()
        logger.info(f"Grep搜索Agent启动 - 模式: {mode}")
        logger.info(f"配置文件: {config}")
        
        if mode == 'advanced':
            # 高级CLI模式（支持方向键、自动补全等）
            from grep_agent.cli.advanced_interactive import run_advanced_cli
            run_advanced_cli(app_config)
        elif mode == 'enhanced':
            # 增强版CLI模式
            from grep_agent.cli.enhanced_interactive import run_enhanced_cli
            run_enhanced_cli(app_config)
        elif mode == 'cli':
            # 原始 CLI模式
            from grep_agent.cli.interactive import run_cli
            run_cli(app_config)
        else:
            # API模式
            from grep_agent.api.server import run_api_server
            run_api_server(app_config)
            
    except Exception as e:
        click.echo(f"错误: {e}", err=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
