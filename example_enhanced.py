"""
增强版示例 - 演示LLM自动生成Linux命令的功能
"""
import sys
from pathlib import Path

# 添加src目录到路径
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from grep_agent.core.config import config_manager
from grep_agent.core.enhanced_agent import EnhancedSearchAgent
from grep_agent.utils.logger import logger_manager


def main():
    """主函数"""
    # 加载配置
    try:
        config = config_manager.load_config("./config/config.yaml")
    except Exception as e:
        print(f"配置加载失败: {e}")
        print("请确保config/config.yaml文件存在且OPENAI_API_KEY已配置")
        return
    
    # 设置日志
    logger_manager.setup_logger(
        log_level="INFO",
        log_file="./logs/example_enhanced.log",
    )
    
    # 创建增强版Agent
    agent = EnhancedSearchAgent(config)
    
    print("=" * 70)
    print("Grep搜索Agent - 增强版示例")
    print("=" * 70)
    print("\n✨ 增强版特性：")
    print("  - LLM可以自动生成各种Linux命令")
    print("  - 支持grep、find、cat、ls、wc等20+种命令")
    print("  - 智能组合多个命令")
    print("  - 强大的安全机制\n")
    
    # 示例查询
    examples = [
        {
            "query": "查找所有Python文件",
            "scope": "./src",
            "max_iter": 2,
            "description": "LLM可能会使用 find 命令"
        },
        {
            "query": "这个项目有多少行Python代码",
            "scope": "./src",
            "max_iter": 3,
            "description": "LLM可能会组合 find 和 wc 命令"
        },
        {
            "query": "查找包含TODO的代码",
            "scope": "./src",
            "max_iter": 2,
            "description": "LLM可能会使用 grep 命令搜索TODO"
        },
    ]
    
    # 选择一个示例运行
    print("可用示例：")
    for i, ex in enumerate(examples, 1):
        print(f"  {i}. {ex['query']}")
        print(f"     {ex['description']}")
    
    print(f"\n  0. 自定义查询")
    
    try:
        choice = int(input("\n请选择示例（0-{}）: ".format(len(examples))))
    except (ValueError, EOFError):
        choice = 1
    
    if choice == 0:
        # 自定义查询
        query = input("请输入查询: ").strip()
        if not query:
            query = "查找配置文件"
        scope = input("搜索范围 [./src]: ").strip() or "./src"
        try:
            max_iter = int(input("最大迭代次数 [3]: ").strip() or "3")
        except ValueError:
            max_iter = 3
    elif 1 <= choice <= len(examples):
        example = examples[choice - 1]
        query = example["query"]
        scope = example["scope"]
        max_iter = example["max_iter"]
    else:
        # 默认使用第一个示例
        example = examples[0]
        query = example["query"]
        scope = example["scope"]
        max_iter = example["max_iter"]
    
    print(f"\n{'='*70}")
    print(f"执行查询: {query}")
    print(f"范围: {scope}")
    print(f"最大迭代次数: {max_iter}")
    print("=" * 70)
    
    try:
        # 执行搜索
        print("\n🚀 开始搜索...\n")
        
        session = agent.search(
            user_query=query,
            search_scope=scope,
            max_iterations=max_iter,
            require_confirmation=False,  # 示例中不需要确认
        )
        
        # 显示结果
        print("\n" + "=" * 70)
        print("搜索结果")
        print("=" * 70)
        
        print(f"\n状态: {session.status.value}")
        print(f"执行命令数: {session.current_iteration}")
        
        if session.command_history:
            print(f"\n📜 命令执行历史：")
            for i, record in enumerate(session.command_history, 1):
                print(f"\n  {i}. 命令: {record['command']}")
                print(f"     目的: {record['purpose']}")
                print(f"     结果: {record['result_lines']}行")
                print(f"     耗时: {record['execution_time']:.2f}秒")
                if record.get('error'):
                    print(f"     错误: {record['error']}")
        
        if session.final_answer:
            print(f"\n{'='*70}")
            print("💡 答案:")
            print("=" * 70)
            print(f"\n{session.final_answer}\n")
        else:
            print("\n未找到答案")
        
        # 询问是否查看详细输出
        show_detail = input("\n是否查看命令详细输出？(y/N): ").strip().lower()
        if show_detail == 'y':
            for i, record in enumerate(session.command_history, 1):
                print(f"\n{'='*70}")
                print(f"命令 {i}: {record['command']}")
                print("=" * 70)
                print(record['output'][:500])  # 显示前500字符
                if len(record['output']) > 500:
                    print(f"\n... (还有{len(record['output'])-500}字符)")
    
    except Exception as e:
        print(f"\n❌ 搜索失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
