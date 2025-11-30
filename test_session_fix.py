#!/usr/bin/env python3
"""
测试EnhancedSearchSession的属性修复
"""
import sys
sys.path.insert(0, '/home/wu/myproject/my_grep_agent/src')

from grep_agent.core.enhanced_agent import EnhancedSearchSession
from grep_agent.core.models import SessionStatus

def test_session_attributes():
    """测试会话属性"""
    print("="*60)
    print("测试EnhancedSearchSession属性修复")
    print("="*60)
    
    # 创建会话
    session = EnhancedSearchSession(
        session_id="test-123",
        user_query="测试查询",
        search_scope="./",
        max_iterations=5
    )
    
    print("\n测试1: 检查total_execution_time属性...")
    try:
        time = session.total_execution_time
        print(f"  ✅ total_execution_time存在，初始值: {time}")
        assert time == 0.0, "初始值应该是0.0"
    except AttributeError as e:
        print(f"  ❌ 缺少total_execution_time属性: {e}")
        return False
    
    print("\n测试2: 添加命令记录...")
    try:
        session.add_command_record(
            command="grep test",
            purpose="测试搜索",
            output="结果",
            execution_time=1.5,
            result_lines=10,
            error=None
        )
        print(f"  ✅ 添加成功")
        print(f"  ✅ 总执行时间更新为: {session.total_execution_time}秒")
        assert session.total_execution_time == 1.5, "应该累加执行时间"
    except Exception as e:
        print(f"  ❌ 添加失败: {e}")
        return False
    
    print("\n测试3: 检查search_history属性...")
    try:
        history = session.search_history
        print(f"  ✅ search_history存在，记录数: {len(history)}")
        assert len(history) == 1, "应该有1条记录"
        
        # 检查记录的属性
        record = history[0]
        print(f"  ✅ 记录属性访问:")
        print(f"     - command: {record.command}")
        print(f"     - purpose: {record.purpose}")
        print(f"     - execution_time: {record.execution_time}")
        print(f"     - result_count: {record.result_count}")
        print(f"     - error: {record.error}")
        
        assert record.command == "grep test", "命令应该匹配"
        assert record.purpose == "测试搜索", "目的应该匹配"
        assert record.execution_time == 1.5, "执行时间应该匹配"
        assert record.result_count == 10, "结果行数应该匹配"
        
    except AttributeError as e:
        print(f"  ❌ 缺少search_history属性: {e}")
        return False
    except Exception as e:
        print(f"  ❌ 测试失败: {e}")
        return False
    
    print("\n测试4: 测试多次添加记录...")
    try:
        session.add_command_record(
            command="find .",
            purpose="查找文件",
            output="文件列表",
            execution_time=0.8,
            result_lines=25,
            error=None
        )
        
        session.add_command_record(
            command="cat file.txt",
            purpose="查看文件",
            output="文件内容",
            execution_time=0.2,
            result_lines=50,
            error=None
        )
        
        print(f"  ✅ 添加了3条记录")
        print(f"  ✅ search_history长度: {len(session.search_history)}")
        print(f"  ✅ 总执行时间: {session.total_execution_time}秒")
        
        assert len(session.search_history) == 3, "应该有3条记录"
        assert session.total_execution_time == 2.5, "总时间应该是1.5+0.8+0.2=2.5"
        
    except Exception as e:
        print(f"  ❌ 测试失败: {e}")
        return False
    
    print("\n测试5: 检查其他基本属性...")
    try:
        assert session.session_id == "test-123"
        assert session.user_query == "测试查询"
        assert session.search_scope == "./"
        assert session.max_iterations == 5
        assert session.current_iteration == 0
        assert session.status == SessionStatus.INIT
        print(f"  ✅ 所有基本属性正常")
    except Exception as e:
        print(f"  ❌ 基本属性检查失败: {e}")
        return False
    
    return True

if __name__ == "__main__":
    print("\n" + "="*60)
    print("EnhancedSearchSession属性修复验证")
    print("="*60 + "\n")
    
    success = test_session_attributes()
    
    print("\n" + "="*60)
    if success:
        print("🎉 所有测试通过！Bug已修复！")
        print("\n修复内容:")
        print("  ✅ 添加了 total_execution_time 属性")
        print("  ✅ 添加了 search_history 属性（作为property）")
        print("  ✅ 自动累加命令执行时间")
        print("  ✅ search_history返回可访问属性的记录对象")
    else:
        print("❌ 部分测试失败")
    print("="*60 + "\n")
    
    sys.exit(0 if success else 1)
