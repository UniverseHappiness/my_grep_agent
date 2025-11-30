"""
测试命令验证 - 验证修复后的单词边界匹配
"""
import sys
from pathlib import Path

# 添加src目录到路径
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from grep_agent.executors.command_executor import CommandExecutor
from grep_agent.llm.enhanced_response_parser import EnhancedResponseParser


def test_command_validation():
    """测试命令验证功能"""
    
    print("=" * 70)
    print("测试命令验证 - 单词边界匹配")
    print("=" * 70)
    
    # 创建执行器
    executor = CommandExecutor(
        search_scope="./src",
        allow_pipes=True,
    )
    
    # 创建解析器
    parser = EnhancedResponseParser()
    
    # 测试用例
    test_cases = [
        # (命令, 应该通过, 描述)
        ("grep -rn 'test' . --include='*.py'", True, "合法的grep命令，include不应被识别为nc"),
        ("find . -name '*.py' -type f", True, "合法的find命令"),
        ("grep -rn 'function' . --include='*.js'", True, "include参数是合法的"),
        ("nc -l 1234", False, "危险命令nc应该被拦截"),
        ("rm -rf /", False, "危险命令rm应该被拦截"),
        ("sudo apt install", False, "危险命令sudo应该被拦截"),
        ("cat include.txt", True, "文件名包含include是合法的"),
        ("ls -lah ./include", True, "目录名include是合法的"),
        ("grep 'format' .", True, "format不应被识别为包含rm"),
        ("format disk", False, "format不在白名单中应该被拦截"),
    ]
    
    print("\n执行测试...\n")
    
    passed = 0
    failed = 0
    
    for command, should_pass, description in test_cases:
        print(f"测试: {description}")
        print(f"命令: {command}")
        
        # 测试执行器验证
        is_safe, msg = executor.validate_command(command)
        
        # 测试解析器验证（快速检查）
        parser_safe, parser_msg = parser.validate_command_safety(command)
        
        # 判断结果
        executor_result = "✅ 通过" if is_safe == should_pass else "❌ 失败"
        
        if is_safe == should_pass:
            passed += 1
            print(f"结果: {executor_result}")
            if not is_safe:
                print(f"拦截原因: {msg}")
        else:
            failed += 1
            print(f"结果: {executor_result}")
            print(f"期望: {'通过' if should_pass else '拦截'}")
            print(f"实际: {'通过' if is_safe else '拦截'}")
            print(f"消息: {msg}")
        
        print("-" * 70)
    
    # 总结
    print("\n" + "=" * 70)
    print("测试总结")
    print("=" * 70)
    print(f"通过: {passed}/{len(test_cases)}")
    print(f"失败: {failed}/{len(test_cases)}")
    
    if failed == 0:
        print("\n🎉 所有测试通过！单词边界匹配工作正常！")
    else:
        print(f"\n⚠️  有{failed}个测试失败")
    
    return failed == 0


if __name__ == "__main__":
    success = test_command_validation()
    sys.exit(0 if success else 1)
