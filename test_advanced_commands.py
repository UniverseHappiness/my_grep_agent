#!/usr/bin/env python3
"""
测试高级命令验证 - 验证find -exec和管道与xargs的支持
"""
import re

# 模拟命令验证逻辑
ALLOWED_COMMANDS = {
    'grep', 'find', 'cat', 'head', 'tail', 'wc', 'ls', 'tree', 'exec',
    'file', 'stat', 'du', 'sort', 'uniq', 'awk', 'sed',
    'less', 'more', 'which', 'whereis', 'type', 'pwd',
    'echo', 'printf', 'basename', 'dirname', 'readlink',
    'xargs',
}

FORBIDDEN_COMMANDS = {
    'rm', 'rmdir', 'mv', 'cp', 'dd', 'mkfs', 'fdisk',
    'sudo', 'su', 'chmod', 'chown', 'chgrp',
    'kill', 'killall', 'pkill',
    'wget', 'curl', 'nc', 'netcat', 'ssh', 'scp', 'ftp',
    'mount', 'umount', 'format',
    'bash', 'sh', 'zsh', 'fish', 'python', 'perl', 'ruby',
    'eval', 'source',
}

DANGEROUS_PATTERNS = {
    '&&': '命令链接',
    '||': '条件执行',
    '`': '命令替换',
    '$(': '命令替换',
}

def validate_command(command: str, allow_pipes: bool = True) -> tuple:
    """验证命令是否安全"""
    if not command or not command.strip():
        return False, "命令为空"
    
    command = command.strip()
    
    # 检查危险命令 - 使用单词边界匹配
    for forbidden in FORBIDDEN_COMMANDS:
        pattern = r'\b' + re.escape(forbidden) + r'\b'
        if re.search(pattern, command.lower()):
            return False, f"包含禁止的命令: {forbidden}"
    
    # 解析命令（处理管道）
    if '|' in command:
        if not allow_pipes:
            return False, "不允许使用管道"
        
        # 检查管道中的每个命令（使用xargs是安全的）
        parts = command.split('|')
        for part in parts:
            part = part.strip()
            if part:
                tokens = part.split()
                if tokens:
                    cmd_name = tokens[0]
                    # xargs是安全的白名单命令
                    if cmd_name not in ALLOWED_COMMANDS and cmd_name != 'xargs':
                        if cmd_name in FORBIDDEN_COMMANDS:
                            return False, f"管道中包含禁止的命令: {cmd_name}"
    
    # 获取主命令
    main_cmd = command.split()[0] if command.split() else ""
    
    # 检查是否在白名单中
    if main_cmd not in ALLOWED_COMMANDS:
        return False, f"命令不在允许列表中: {main_cmd}"
    
    # 检查真正危险的模式
    for pattern, desc in DANGEROUS_PATTERNS.items():
        if pattern in command:
            return False, f"包含危险操作: {desc} ({pattern})"
    
    # 检查重定向（但允许错误重定向到/dev/null）
    if '>' in command or '<' in command:
        safe_redirects = ['2>/dev/null', '2>&1']
        temp_cmd = command
        for sr in safe_redirects:
            temp_cmd = temp_cmd.replace(sr, '')
        
        if '>' in temp_cmd or '<' in temp_cmd:
            return False, "包含不安全的文件重定向"
    
    # find命令的特殊检查：允许 -exec 和 \; 结尾
    if main_cmd == 'find':
        if '-exec' in command:
            if not (command.rstrip().endswith('\\;') or command.rstrip().endswith('+')):
                return False, "find -exec 必须以 \\; 或 + 结尾"
            exec_match = re.search(r'-exec\s+(\S+)', command)
            if exec_match:
                exec_cmd = exec_match.group(1)
                if exec_cmd in FORBIDDEN_COMMANDS:
                    return False, f"-exec 包含禁止的命令: {exec_cmd}"
    
    return True, "命令安全"


def test_advanced_commands():
    """测试高级命令场景"""
    
    # 测试用例：(命令, 是否应该通过, 说明)
    test_cases = [
        # 应该通过的命令
        (
            'find /path -type f \\( -name "*.md" -o -name "*.txt" \\) -exec grep -l "keyword" {} \\;',
            True,
            "find with -exec and escaped semicolon"
        ),
        (
            'find . -name "*.py" | xargs grep -l "function"',
            True,
            "find piped to xargs"
        ),
        (
            'find /path -type f -name "*.md" 2>/dev/null',
            True,
            "find with error redirect to /dev/null"
        ),
        (
            'find /path -name "*.log" | xargs grep -l "error" 2>/dev/null',
            True,
            "pipe with xargs and error redirect"
        ),
        (
            'grep --include="*.py" pattern .',
            True,
            "grep with include parameter"
        ),
        (
            'find . -type f -exec cat {} \\;',
            True,
            "find exec cat with semicolon"
        ),
        
        # 应该被拦截的命令
        (
            'find . -name "*.txt" -exec rm {} \\;',
            False,
            "find exec with dangerous rm command"
        ),
        (
            'grep pattern file.txt > output.txt',
            False,
            "command with output redirect"
        ),
        (
            'find . -name "*.py" && rm test.py',
            False,
            "command chaining with &&"
        ),
        (
            'find . -name "*.sh" | xargs bash',
            False,
            "xargs with dangerous bash command"
        ),
        (
            'grep pattern `cat file.txt`',
            False,
            "command substitution with backticks"
        ),
        (
            'find . -exec grep pattern {} \\; > output.txt',
            False,
            "find exec with output redirect"
        ),
    ]
    
    print("=" * 70)
    print("测试高级命令验证")
    print("=" * 70)
    
    passed = 0
    failed = 0
    
    for command, should_pass, description in test_cases:
        is_safe, msg = validate_command(command)
        success = (is_safe == should_pass)
        
        if success:
            status = "✅ PASS"
            passed += 1
        else:
            status = "❌ FAIL"
            failed += 1
        
        print(f"\n{status} | {description}")
        print(f"  命令: {command[:80]}{'...' if len(command) > 80 else ''}")
        print(f"  预期: {'通过' if should_pass else '拦截'}")
        print(f"  实际: {'通过' if is_safe else '拦截'}", end="")
        if not is_safe:
            print(f" - {msg}")
        else:
            print()
    
    print("\n" + "=" * 70)
    print(f"总计: {len(test_cases)} 个测试")
    print(f"通过: {passed} ✅")
    print(f"失败: {failed} ❌")
    print("=" * 70)
    
    if failed == 0:
        print("\n🎉 所有测试通过！")
        print("\n✅ 支持的功能：")
        print("   - find -exec ... \\; 语法")
        print("   - 管道 | xargs 组合")
        print("   - 错误重定向 2>/dev/null")
        print("   - grep --include 等参数")
        print("\n✅ 正确拦截：")
        print("   - 危险命令（rm、sudo等）")
        print("   - 文件输出重定向（> output.txt）")
        print("   - 命令链接（&&、||）")
        print("   - 命令替换（`、$()）")
    else:
        print(f"\n⚠️  有 {failed} 个测试失败")
    
    return failed == 0


if __name__ == "__main__":
    success = test_advanced_commands()
    exit(0 if success else 1)
