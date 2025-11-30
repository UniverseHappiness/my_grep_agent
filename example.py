"""
简单示例 - 演示如何使用Grep搜索Agent
"""
import sys
from pathlib import Path

# 添加src目录到路径
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

from grep_agent.core.config import config_manager
from grep_agent.core.agent import SearchAgent
from grep_agent.utils.logger import logger_manager


def main():
    """主函数"""
    # 加载配置
    try:
        config = config_manager.load_config("./config/config.yaml")
    except Exception as e:
        print(f"配置加载失败: {e}")
        print("请确保config/config.yaml文件存在")
        return
    
    # 设置日志
    logger_manager.setup_logger(
        log_level="INFO",
        log_file="./logs/example.log",
    )
    
    # 创建Agent
    agent = SearchAgent(config)
    
    print("=" * 60)
    print("Grep搜索Agent示例")
    print("=" * 60)
    
    # 示例查询
    query = "配置文件"
    search_scope = "./config"
    max_iterations = 3
    
    print(f"\n查询: {query}")
    print(f"范围: {search_scope}")
    print(f"最大次数: {max_iterations}\n")
    
    try:
        # 执行搜索
        session = agent.search(
            user_query=query,
            search_scope=search_scope,
            max_iterations=max_iterations,
        )
        
        # 显示结果
        print("\n搜索结果:")
        print(f"状态: {session.status.value}")
        print(f"搜索次数: {session.current_iteration}")
        
        if session.search_history:
            print("\n搜索历史:")
            for record in session.search_history:
                print(f"  - 第{record.iteration_num}次: {record.result_count}行匹配")
        
        if session.final_answer:
            print(f"\n答案:\n{session.final_answer}")
        else:
            print("\n未找到答案")
    
    except Exception as e:
        print(f"\n搜索失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
