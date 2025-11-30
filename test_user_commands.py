#!/usr/bin/env python3
"""
测试用户报告的具体命令 - 独立测试，不依赖项目模块
"""
import re

# 复制验证逻辑
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
        
        parts = command.split('|')
        for part in parts:
            part = part.strip()
            if part:
                tokens = part.split()
                if tokens:
                    cmd_name = tokens[0]
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

def test_user_commands():
    """测试用户报告的两个命令"""
    
    # 用户报告的两个命令
    commands = [
        {
            'cmd': 'find /home/wu/myproject/my_grep_agent/docs -type f -name "*.md" -o -name "*.txt" -o -name "*.pdf" | xargs grep -l "单纯性甲状腺肿\\|simple goiter" 2>/dev/null',
            'desc': '使用xargs和错误重定向的find命令'
        },
        {
            'cmd': 'find /home/wu/myproject/my_grep_agent/docs -type f \\( -name "*.md" -o -name "*.txt" \\) -exec grep -l "单纯性甲状腺肿\\|simple goiter" {} \\;',
            'desc': '使用-exec的find命令'
        }
    ]
    
    print("=" * 70)
    print("测试用户报告的命令")
    print("=" * 70)
    
    all_passed = True
    
    for i, test in enumerate(commands, 1):
        cmd = test['cmd']
        desc = test['desc']
        
        print(f"\n测试 {i}: {desc}")
        print(f"命令: {cmd[:60]}...")
        
        # 验证命令
        is_safe, msg = validate_command(cmd)
        
        if is_safe:
            print(f"✅ 验证通过: {msg}")
        else:
            print(f"❌ 验证失败: {msg}")
            all_passed = False
    
    print("\n" + "=" * 70)
    if all_passed:
        print("🎉 所有命令验证通过！")
        print("\n现在这些命令都可以正常使用了：")
        print("  ✅ find ... | xargs ... 2>/dev/null")
        print("  ✅ find ... -exec ... {} \\;")
    else:
        print("⚠️  有命令验证失败")
    print("=" * 70)
    
    return all_passed

if __name__ == "__main__":
    success = test_user_commands()
    exit(0 if success else 1)
