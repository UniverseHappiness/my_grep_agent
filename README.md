# Grep搜索Agent系统

一个智能化的grep搜索Agent系统，能够通过grep命令在指定目录中搜索内容，将搜索结果提交给大语言模型进行分析，并根据LLM的反馈智能调整搜索策略。

## 核心特性

- 🔍 基于grep命令的文件内容搜索
- 🤖 与大语言模型集成，智能分析搜索结果
- 🎯 自适应搜索策略调整机制
- ⚙️ 可配置的搜索次数限制
- 💻 支持命令行交互和API服务双模式
- 📂 搜索范围可配置（指定目录或全局）

### ✨ 增强版特性（新！）

- 🚀 **LLM自动生成Linux命令**：不仅限于grep，支持find、cat、ls、wc等20+种命令
- 🧠 **更好的上下文管理**：保留完整的命令执行历史，LLM可以看到所有尝试
- 🔒 **强大的安全机制**：命令白名单、危险命令拦截、可选的用户确认
- 🌐 **智能命令生成**：根据问题自动选择最合适的命令和参数

### ⌨️ 高级CLI特性（最新！）

- ⬆️⬇️ **方向键支持**：浏览历史命令，移动光标编辑
- 🎯 **Tab自动补全**：快速补全命令
- 🧠 **智能建议**：根据历史自动推荐
- ✂️ **完整编辑**：删除、剪切、粘贴等所有标准操作
- 🎨 **美观界面**：彩色输出和格式化显示

## 快速开始

### 安装

```bash
# 安装所有依赖（包括高级CLI所需的prompt_toolkit）
pip install -r requirements.txt
```

> 💡 **提示**：如果只想使用高级CLI模式，也可以单独安装：
> ```bash
> pip install prompt_toolkit>=3.0.0
> ```
> 详细安装指南请查看：[INSTALL_ADVANCED.md](INSTALL_ADVANCED.md)

### 配置

复制配置模板并修改：

```bash
cp config/config.example.yaml config/config.yaml
```

配置LLM API密钥（通过环境变量）：

```bash
export OPENAI_API_KEY="your-api-key-here"
```

### 使用

#### 🌟 高级CLI模式（推荐！最佳体验）

```bash
# 默认启动高级模式
python run.py

# 或明确指定
python -m grep_agent --mode advanced
```

**高级CLI特性：**
- ⬆️⬇️ 方向键浏览历史命令
- ⬅️➡️ 光标移动编辑
- Tab 自动补全命令
- Ctrl+A/E/K/U/W 快捷编辑
- 🎨 彩色界面和格式化输出

📚 **完整使用指南**：[ADVANCED_CLI.md](ADVANCED_CLI.md)

#### 增强版模式

```bash
python -m grep_agent --mode enhanced
```

**增强版特性：**
- LLM自动生成Linux命令（grep、find、cat等）
- 更智能的上下文管理
- 强大的安全机制

📚 详细介绍请查看：[ENHANCED_FEATURES.md](ENHANCED_FEATURES.md)

#### 原始命令行模式

```bash
python -m grep_agent --mode cli
```

#### API服务模式

```bash
python -m grep_agent --mode api
```

## 项目结构

```
my_grep_agent/
├── src/grep_agent/          # 源代码目录
│   ├── core/                # 核心模块
│   ├── executors/           # 执行器模块
│   ├── llm/                 # LLM集成模块
│   ├── strategies/          # 策略管理模块
│   ├── api/                 # API服务模块
│   ├── cli/                 # CLI接口模块
│   └── utils/               # 工具函数模块
├── tests/                   # 测试目录
├── config/                  # 配置文件目录
├── logs/                    # 日志文件目录
└── README.md               # 项目说明
```

## 开发

### 运行测试

```bash
pytest tests/
```

### 代码规范

项目遵循PEP 8代码规范。

## 许可证

MIT License
