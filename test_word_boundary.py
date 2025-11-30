#!/usr/bin/env python3
"""
测试单词边界匹配 - 验证命令验证不会误判
"""
import re

def test_word_boundary():
    """测试单词边界匹配"""
    
    # 危险命令列表
    forbidden_commands = ['nc', 'rm', 'sudo', 'curl', 'wget', 'bash', 'sh']
    
    # 测试用例：(命令字符串, 是否应该被拦截, 说明)
    test_cases = [
        # 应该被拦截的
        ("nc localhost 8080", True, "真正的nc命令"),
        ("rm -rf /tmp/test", True, "真正的rm命令"),
        ("sudo apt install", True, "真正的sudo命令"),
        
        # 不应该被拦截的
        ("grep --include='*.py' pattern", False, "include参数不是nc命令"),
        ("find . -name 'include.txt'", False, "文件名包含include"),
        ("grep format file.txt", False, "format不是rm命令"),
        ("cat filename.txt", False, "filename不是rm命令"),
        ("ls -lah /home", False, "home不是rm命令"),
        ("grep performance log.txt", False, "performance包含rm但不是rm命令"),
    ]
    
    print("=" * 60)
    print("测试单词边界匹配")
    print("=" * 60)
    
    passed = 0
    failed = 0
    
    for command, should_block, description in test_cases:
        is_blocked = False
        blocked_by = None
        
        # 使用单词边界匹配
        for forbidden in forbidden_commands:
            pattern = r'\b' + re.escape(forbidden) + r'\b'
            if re.search(pattern, command.lower()):
                is_blocked = True
                blocked_by = forbidden
                break
        
        # 检查结果
        success = (is_blocked == should_block)
        
        if success:
            status = "✅ PASS"
            passed += 1
        else:
            status = "❌ FAIL"
            failed += 1
        
        print(f"\n{status} | {description}")
        print(f"  命令: {command}")
        print(f"  预期: {'拦截' if should_block else '放行'}")
        print(f"  实际: {'拦截' if is_blocked else '放行'}", end="")
        if is_blocked:
            print(f" (被 '{blocked_by}' 规则拦截)")
        else:
            print()
    
    print("\n" + "=" * 60)
    print(f"总计: {len(test_cases)} 个测试")
    print(f"通过: {passed} ✅")
    print(f"失败: {failed} ❌")
    print("=" * 60)
    
    if failed == 0:
        print("\n🎉 所有测试通过！单词边界匹配工作正常！")
    else:
        print(f"\n⚠️  有 {failed} 个测试失败")
    
    return failed == 0

if __name__ == "__main__":
    success = test_word_boundary()
    exit(0 if success else 1)
