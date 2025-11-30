# 高级CLI安装指南

## 📦 安装步骤

### 步骤1：安装prompt_toolkit

高级CLI模式需要 `prompt_toolkit` 库。请运行以下命令安装：

```bash
# 方法1：单独安装prompt_toolkit
pip install prompt_toolkit>=3.0.0

# 方法2：安装所有依赖（推荐）
pip install -r requirements.txt
```

### 步骤2：验证安装

运行测试脚本验证安装是否成功：

```bash
python test_advanced_cli.py
```

成功的输出应该显示：
```
✅ prompt_toolkit 版本: 3.0.x
✅ 所有核心组件导入成功
✅ 高级CLI模块导入成功
🎉 所有测试通过！可以使用高级CLI模式了！
```

### 步骤3：启动高级CLI

```bash
# 直接启动（默认使用高级模式）
python run.py

# 或明确指定模式
python -m grep_agent --mode advanced
```

## 🆘 故障排除

### 问题1：pip install失败

**错误信息**：
```
ERROR: Could not find a version that satisfies the requirement prompt_toolkit
```

**解决方法**：
```bash
# 升级pip
pip install --upgrade pip

# 重试安装
pip install prompt_toolkit
```

### 问题2：虚拟环境问题

如果你使用虚拟环境，确保激活了正确的环境：

```bash
# 激活虚拟环境（如果有）
source grep_env/bin/activate  # Linux/Mac
# 或
grep_env\Scripts\activate  # Windows

# 然后安装
pip install prompt_toolkit
```

### 问题3：权限问题

如果遇到权限错误：

```bash
# 使用用户安装
pip install --user prompt_toolkit
```

### 问题4：依赖冲突

如果提示版本冲突：

```bash
# 查看当前安装的版本
pip list | grep prompt

# 卸载旧版本
pip uninstall prompt_toolkit

# 重新安装
pip install prompt_toolkit>=3.0.0
```

## ✅ 验证checklist

安装完成后，请确认以下几点：

- [ ] `pip list` 中能看到 `prompt_toolkit`
- [ ] 运行 `python test_advanced_cli.py` 全部通过
- [ ] 运行 `python run.py` 能正常启动
- [ ] 按⬆️⬇️键能浏览历史
- [ ] 按⬅️➡️键能移动光标
- [ ] 按Tab键能自动补全

## 🚀 快速开始

安装完成后，查看使用文档：

```bash
cat ADVANCED_CLI.md
```

或直接开始使用：

```bash
python run.py
```

## 📝 其他说明

### 为什么需要prompt_toolkit？

- ✅ 提供专业的命令行交互体验
- ✅ 支持方向键历史浏览
- ✅ 支持光标移动和编辑
- ✅ 支持Tab自动补全
- ✅ 支持智能建议
- ✅ 广泛使用于各种CLI工具（如ipython、mycli等）

### 如果不想安装怎么办？

可以使用其他模式：

```bash
# 增强模式（不需要prompt_toolkit）
python -m grep_agent --mode enhanced

# 基础CLI模式
python -m grep_agent --mode cli
```

但这些模式不支持方向键等高级功能。

## 📚 相关资源

- [prompt_toolkit官方文档](https://python-prompt-toolkit.readthedocs.io/)
- [ADVANCED_CLI.md](ADVANCED_CLI.md) - 高级CLI使用指南
- [README.md](README.md) - 项目概览

祝使用愉快！🎉
