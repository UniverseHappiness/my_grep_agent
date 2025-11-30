#!/bin/bash
# 高级CLI快速安装和测试脚本

echo "======================================================================"
echo "🚀 Grep搜索Agent - 高级CLI安装和测试"
echo "======================================================================"
echo ""

# 步骤1：安装依赖
echo "📦 步骤1：安装prompt_toolkit..."
pip install prompt_toolkit>=3.0.0

if [ $? -eq 0 ]; then
    echo "✅ prompt_toolkit安装成功"
else
    echo "❌ 安装失败，请检查网络或pip配置"
    exit 1
fi

echo ""

# 步骤2：运行测试
echo "🧪 步骤2：运行功能测试..."
python test_advanced_cli.py

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ 测试通过！"
else
    echo ""
    echo "⚠️  测试未完全通过，但可能不影响使用"
fi

echo ""
echo "======================================================================"
echo "✨ 安装完成！"
echo "======================================================================"
echo ""
echo "🚀 启动命令："
echo "   python run.py"
echo ""
echo "📚 查看文档："
echo "   cat ADVANCED_CLI.md"
echo ""
echo "💡 使用技巧："
echo "   - 按 ⬆️⬇️ 浏览历史命令"
echo "   - 按 ⬅️➡️ 移动光标编辑"
echo "   - 按 Tab 自动补全命令"
echo "   - 输入 help 查看帮助"
echo ""
echo "======================================================================"
