# Grep搜索Agent快速开始指南

## 安装依赖

```bash
cd /home/wu/myproject/my_grep_agent
pip install -r requirements.txt
```

## 配置

### 1. 设置环境变量

创建`.env`文件（从`.env.example`复制）：

```bash
cp .env.example .env
```

编辑`.env`文件，设置你的OpenAI API密钥：

```bash
OPENAI_API_KEY=sk-your-actual-api-key-here

# 可选：如果需要使用自定义的API端点（比如Azure OpenAI或其他兼容服务）
OPENAI_API_ENDPOINT=https://your-custom-endpoint.com/v1
```

### 2. 配置文件

配置文件已经准备好了：`config/config.yaml`

可以根据需要调整：
- 搜索范围
- 最大搜索次数
- LLM模型
- 策略模式等

## 使用方法

### ⭐ 方式1：增强版模式（推荐！）

**新特性：**
- 🚀 LLM自动生成Linux命令（不仅限于grep）
- 🧠 更好的上下文管理
- 🔒 强大的安全机制

```bash
# 默认就是增强版
python run.py

# 或明确指定
python run.py --mode enhanced
```

📖 **详细功能介绍**：[ENHANCED_FEATURES.md](ENHANCED_FEATURES.md)

---

### 方式2：原始模式

#### CLI模式（命令行交互）

```bash
python run.py --mode cli
```

或者简化：

```bash
python run.py
```

#### API模式（HTTP服务）

```bash
python run.py --mode api
```

然后访问：http://localhost:8000/api/v1/health

### 方式2：使用python模块

#### CLI模式

```bash
python -m grep_agent --mode cli
```

#### API模式

```bash
python -m grep_agent --mode api
```

### 方式3：运行示例

```bash
python example.py
```

## CLI使用示例

启动后，可以输入查询：

```
请输入搜索查询: find authentication function
搜索范围 [./src]: ./src
最大搜索次数 [5]: 3
```

系统会：
1. 在指定范围内使用grep搜索
2. 将结果发送给LLM分析
3. 根据LLM反馈调整搜索策略
4. 最多搜索3次，直到找到答案

## 命令

- `help` - 显示帮助
- `config list` - 查看配置
- `exit` - 退出

## 运行测试

```bash
pytest tests/ -v
```

## 注意事项

1. **OpenAI API密钥**：必须配置有效的API密钥才能使用LLM功能
2. **搜索范围**：确保指定的搜索路径存在且可读
3. **grep命令**：系统需要grep命令可用（Linux/macOS默认有，Windows需要安装）

## 项目结构

```
my_grep_agent/
├── src/grep_agent/          # 源代码
│   ├── core/                # 核心模块（模型、配置、Agent）
│   ├── executors/           # 执行器（grep、结果处理）
│   ├── llm/                 # LLM集成（客户端、Prompt）
│   ├── strategies/          # 策略管理
│   ├── cli/                 # CLI接口
│   ├── api/                 # API服务
│   └── utils/               # 工具函数
├── config/                  # 配置文件
├── tests/                   # 测试
├── logs/                    # 日志
├── run.py                   # 运行脚本
└── example.py              # 示例代码
```

## 故障排查

### 问题：找不到grep命令

**解决**：
- Linux/macOS：grep应该默认安装
- Windows：安装Git Bash或WSL

### 问题：LLM调用失败

**解决**：
1. 检查API密钥是否正确设置
2. 检查网络连接
3. 查看日志文件：`logs/agent.log`

### 问题：搜索路径错误

**解决**：
- 确保路径存在
- 使用绝对路径或相对路径
- 检查路径权限

## 下一步

- 查看设计文档：`.qoder/quests/grep-search-agent.md`
- 修改配置以适应你的需求
- 尝试不同的搜索策略
- 扩展API功能（见`src/grep_agent/api/server.py`）
