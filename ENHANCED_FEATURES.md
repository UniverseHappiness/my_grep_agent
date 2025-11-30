# 增强版功能说明

## 🎉 新功能概览

系统现在支持**增强版模式**，让LLM能够自动生成和执行各种Linux命令，而不仅仅局限于grep！

### 核心改进

1. **LLM自动生成Linux命令**
   - LLM根据用户问题智能选择合适的命令
   - 支持多种常用命令：grep、find、cat、ls、wc、head、tail等
   - 支持命令组合和管道

2. **更好的上下文管理**
   - 保留完整的命令执行历史
   - LLM可以看到所有之前的尝试
   - 智能避免重复执行

3. **强大的安全机制**
   - 命令白名单（只允许安全的只读命令）
   - 自动拦截危险命令（rm、sudo等）
   - 可选的用户确认模式

## 🚀 如何使用

### 启动增强版

```bash
# 方式1：直接运行（默认就是增强版）
python run.py

# 方式2：明确指定增强版模式
python run.py --mode enhanced

# 方式3：使用模块方式
python -m grep_agent --mode enhanced
```

### 使用示例

启动后，你可以问各种问题，LLM会自动生成合适的命令：

```
📝 请输入搜索查询: 查找所有Python文件
🔍 搜索范围 [./src]: ./
🔢 最大命令执行次数 [5]: 3
⚠️  是否需要确认每个命令（安全模式） [y/N]: n
```

**LLM可能生成的命令：**
```bash
find ./ -name '*.py' -type f
```

### 更多示例

| 你的问题 | LLM可能生成的命令 |
|---------|------------------|
| "查找包含TODO的代码" | `grep -rn 'TODO' ./ --include='*.py'` |
| "统计Python代码行数" | `find ./ -name '*.py' \| xargs wc -l` |
| "查看配置文件内容" | `find ./ -name 'config.*' -type f \| xargs cat` |
| "列出所有目录" | `find ./ -type d \| sort` |
| "查找最大的文件" | `du -ah ./ \| sort -rh \| head -10` |

## 🔒 安全机制

### 白名单命令

只允许以下安全的只读命令：

```
grep, find, cat, head, tail, wc, ls, tree,
file, stat, du, sort, uniq, awk, sed,
less, more, which, whereis, type, pwd,
echo, printf, basename, dirname, readlink
```

### 黑名单命令

以下危险命令会被自动拦截：

```
rm, rmdir, mv, cp, dd, mkfs, chmod, chown,
sudo, su, kill, wget, curl, ssh, scp,
bash, sh, python, eval, exec
```

### 安全验证

每个命令在执行前都会经过多重验证：
1. ✅ 命令是否在白名单中
2. ✅ 命令是否包含危险关键词
3. ✅ 路径是否在允许范围内
4. ✅ 是否包含危险符号（重定向、后台执行等）

## 📊 与原版对比

| 特性 | 原版 | 增强版 |
|-----|------|--------|
| 支持的命令 | 仅grep | grep、find、cat、ls等20+命令 |
| 命令生成 | 预定义策略 | LLM智能生成 |
| 上下文管理 | 基础 | 完整历史+智能压缩 |
| 安全机制 | 基础输入验证 | 多层安全检查+白名单 |
| 灵活性 | 中等 | 高 |

## 🎯 典型使用场景

### 场景1：代码分析

**问题**："这个项目使用了哪些第三方库？"

**LLM可能的策略：**
1. `find . -name 'requirements.txt' -o -name 'package.json'`
2. `cat ./requirements.txt`
3. 分析内容并给出答案

### 场景2：快速统计

**问题**："项目有多少行代码？"

**LLM可能的策略：**
1. `find . -name '*.py' -type f | xargs wc -l | tail -1`
2. 直接给出统计结果

### 场景3：配置查找

**问题**："数据库连接配置在哪里？"

**LLM可能的策略：**
1. `grep -rn 'database\|db_host\|DATABASE_URL' . --include='*.yaml' --include='*.json' --include='*.env'`
2. `cat <找到的配置文件>`
3. 提取并解释配置

## ⚙️ 配置选项

在 `config/config.yaml` 中可以调整：

```yaml
system:
  default_max_iterations: 5    # 默认最大命令执行次数
  default_search_scope: "./src" # 默认搜索范围
  
llm:
  model_name: "gpt-4"          # 使用的LLM模型
  max_tokens: 2000             # 最大Token数
  temperature: 0.7             # 生成温度
```

## 🐛 故障排查

### 问题1：命令被拒绝执行

**原因**：命令包含不安全的内容

**解决**：
- 检查命令是否在白名单中
- 检查是否包含危险字符
- 查看日志了解具体原因

### 问题2：LLM生成的命令不正确

**原因**：问题描述不够清晰或LLM理解偏差

**解决**：
- 更明确地描述你的需求
- 提供更多上下文信息
- 尝试换一种问法

### 问题3：执行时间过长

**原因**：搜索范围太大或命令复杂度高

**解决**：
- 缩小搜索范围
- 减少最大迭代次数
- 在配置中调整超时时间

## 📝 最佳实践

1. **明确问题**：越具体的问题，LLM生成的命令越精准
   - ❌ "查找文件"
   - ✅ "查找src目录下所有Python文件"

2. **合理设置迭代次数**：
   - 简单查询：2-3次
   - 复杂分析：5-7次
   - 深度探索：10次

3. **使用安全模式**：
   - 对不熟悉的查询，启用用户确认
   - 定期查看命令执行历史

4. **缩小搜索范围**：
   - 尽量指定具体的目录
   - 避免搜索整个文件系统

## 🔄 从原版迁移

如果你习惯了原版，也可以继续使用：

```bash
# 使用原版CLI
python run.py --mode cli

# 或直接使用增强版（推荐）
python run.py --mode enhanced
```

## 💡 高级用法

### 自定义命令白名单

编辑 `src/grep_agent/executors/command_executor.py`：

```python
ALLOWED_COMMANDS = {
    'grep', 'find', 'cat',
    # 添加你的命令
    'your_command',
}
```

### 调整LLM Prompt

编辑 `src/grep_agent/llm/enhanced_prompt_builder.py` 中的 `SYSTEM_PROMPT`

## 📚 相关文档

- [快速开始](QUICKSTART.md)
- [项目总结](PROJECT_SUMMARY.md)
- [设计文档](.qoder/quests/grep-search-agent.md)

## 🎓 学习资源

- 了解Linux命令：[Linux命令大全](https://man7.org/linux/man-pages/)
- 学习正则表达式：[RegexOne](https://regexone.com/)
- Prompt工程：[OpenAI Prompt Engineering](https://platform.openai.com/docs/guides/prompt-engineering)
