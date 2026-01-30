# LightAgent 项目

## 项目概述

LightAgent 是一个轻量级、模块化的 Python AI Agent 框架，支持 async/await 异步编程。

**核心特性:**
- 多模型支持 (OpenAI, Anthropic, Ollama, 自定义适配器)
- 工具调用系统 (MCP, Function Call, RAG)
- 中间件管道，用于请求前/后处理
- A2A 协议，支持多 Agent 通信
- 内存存储系统 (内存、文件、SQLite、MySQL、PostgreSQL)
- 使用 Pydantic 保证类型安全

## 项目结构

```
lightagent/
├── core/           # 核心 Agent 逻辑 (Agent, 协议, 中间件)
├── models/         # 模型适配器 (OpenAI, Anthropic, Ollama, Mock)
├── tools/          # 工具实现 (MCP, Function, RAG, File)
├── memory/         # 内存存储和事件系统
├── workflow/       # 工作流引擎和规划系统
└── models/         # Pydantic 数据模型

examples/           # 使用示例和演示
tests/              # 测试套件 (使用 pytest 和 asyncio)
docs/               # 详细文档
```

## 开发命令

**运行测试:**
```bash
# 运行所有测试
pytest

# 运行特定测试文件
pytest tests/test_agent.py

# 运行测试并生成覆盖率报告
pytest --cov=lightagent --cov-report=html

# 只运行快速测试 (跳过 slow/integration 标记的测试)
pytest -m "not slow and not integration"
```

**代码质量检查:**
```bash
# 格式化代码
black lightagent tests examples

# 代码检查
flake8 lightagent tests examples

# 类型检查
mypy lightagent
```

**运行示例:**
```bash
# 基础 Agent 演示
python examples/simple_demo.py

# RAG Agent 示例
python examples/rag_agent.py

# 多 Agent 协作
python examples/multi_agent.py
```

## 核心概念

**Agent:** 具有推理循环和工具执行能力的主 Agent 类
- `lightagent/core/agent.py:Agent` - 核心 Agent 实现
- `lightagent/core/protocol.py:A2AMessage` - Agent 间通信

**模型适配器:** LLM 提供商的抽象接口
- `lightagent/models/providers/openai.py:OpenAIAdapter`
- `lightagent/models/providers/anthropic.py:AnthropicAdapter`
- `lightagent/models/providers/ollama.py:OllamaAdapter`
- `lightagent/models/providers/mock.py:MockAdapter` (用于测试)

**工具:**
- `lightagent/tools/mcp_tool.py:MCPTool` - 外部 MCP 服务器集成
- `lightagent/tools/function_tool.py:FunctionCallTool` - Python 函数封装
- `lightagent/tools/rag_tool.py:RAGTool` - 检索增强生成

**中间件:** 请求前/后处理管道
- `lightagent/core/middleware.py:MiddlewareManager` - 中间件编排
- 内置中间件: 日志、限流、缓存、验证、重试

**内存:** 事件存储和检索
- `lightagent/memory/stores/` - 各种存储后端
- `lightagent/memory/base.py:AgentEvent` - 事件数据模型

## 重要指南

**异步编程（优先原则）:**
- Agent 操作都是异步的 - 优先使用 `await agent.initialize()`, `await agent.run()`
- 模型调用建议异步 - 优先使用 `await model_adapter.generate()` 以提高性能
- 文件 I/O 推荐异步 - 优先使用 `aiofiles` 进行文件读写，避免阻塞事件循环
- 数据库操作建议异步 - 优先使用异步驱动 (aiosqlite, aiomysql, asyncpg)
- 网络 I/O 推荐异步 - 优先使用 `aiohttp` 而非 `requests`
- 测试使用 `pytest-asyncio` 的自动模式

**异步最佳实践:**
- 工具的 `execute()` 方法建议实现为异步函数
- 中间件的 `process_before()` 和 `process_after()` 建议实现为异步函数
- 避免 I/O 密集型操作阻塞事件循环
- 在性能敏感场景优先考虑异步方案

**类型安全:**
- 所有数据模型使用 Pydantic v2 进行验证
- 公共 API 建议添加类型提示

**配置管理:**
- 配置项通过 Pydantic 实现，支持多种解析方式
- 配置优先级: **参数 > 环境变量 > 配置文件**
- 推荐使用 `ModelConfig` 和 `AgentConfig` 进行配置
- 环境变量自动解析，使用大写字母和下划线（如 `OPENAI_API_KEY`）
- 配置文件支持 YAML、JSON 等格式
- Pydantic 自动进行类型验证和转换

**测试:**
- 推荐使用 `MockAdapter` 进行无 API 调用的测试
- 测试函数建议使用异步
- 使用标记: `@pytest.mark.asyncio`, `@pytest.mark.slow`, `@pytest.mark.integration`

**错误处理:**
- 模型适配器在 API 失败时抛出异常
- 工具返回带有成功/错误状态的 `ToolExecutionResult`
- 中间件可以拦截和处理错误

## 代码风格

- Python 3.12+ 兼容性
- 所有文件使用 UTF-8 编码
- 使用 `black` 格式化 (行长度 88)
- 使用 `flake8` 进行代码检查
- 使用 `mypy` 进行类型检查
- 代码文件中不要使用 emoji

## 文档

**核心文档:**
- `docs/QUICKSTART.md` - 5 分钟快速入门
- `docs/PROJECT_OVERVIEW.md` - 完整功能列表
- `docs/PROJECT_STRUCTURE.md` - 架构详解
- `docs/FUNCTION_CALLING.md` - 多模型函数调用
- `docs/PROMPT_ENGINEERING.md` - 系统提示词和工具描述
- `docs/AGENT_CREATION.md` - Agent 创建方法对比
- `docs/MEMORY_STORAGE.md` - 内存系统指南
- `docs/MIGRATION_GUIDE.md` - 版本迁移说明

**示例:**
- `examples/simple_demo.py` - 最小工作示例
- `examples/basic_agent.py` - 带函数工具的 Agent
- `examples/multi_agent.py` - 多 Agent 协作
- `examples/rag_agent.py` - RAG 实现
- `examples/middleware_agent.py` - 自定义中间件

## 渐进式披露

关于特定主题的详细信息，请参考:
- 架构和设计: 查看 `docs/PROJECT_STRUCTURE.md`
- 测试策略: 查看 `tests/` 目录和现有测试文件
- API 参考: 查看 `lightagent/` 模块中的文档字符串
- 使用模式: 查看 `examples/` 目录

## 常见工作流程

**添加新的模型适配器:**
1. 在 `lightagent/models/base.py` 中扩展 `BaseModelAdapter`
2. 实现异步方法: `initialize()`, `generate()`, `tool_call()`
3. 在 `ModelRegistry` 中注册 (如果需要)
4. 在 `tests/test_models_providers.py` 中添加测试

**创建自定义工具:**
1. 在 `lightagent/tools/base.py` 中扩展 `BaseTool`
2. 实现 `execute()` 异步方法
3. 添加到 Agent: `agent.add_tool(MyTool())`

**添加自定义中间件:**
1. 在 `lightagent/core/middleware.py` 中扩展 `BaseMiddleware`
2. 实现 `process_before()` 和/或 `process_after()`
3. 添加到中间件管理器: `manager.add(MyMiddleware())`

**无 API 调用测试:**
```python
from lightagent import MockAdapter, ModelConfig

mock_adapter = MockAdapter(config=ModelConfig(model_name="mock"))
agent = Agent(config=..., model_adapter=mock_adapter)
```
