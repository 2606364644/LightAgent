# 工作流 Prompt 和工具复用指南

## 概述

本文档介绍如何为不同的工作流类型配置**自定义 prompt** 和**工具**，以及如何实现**工具复用**。

### 核心概念

1. **WorkflowPromptRegistry** - 管理 prompt 模板
2. **ToolRegistry** - 管理工具池（全局 + 工作流特定）
3. **ExtendedWorkflowConfig** - 统一配置系统
4. **工具复用** - 工作流间共享工具

---

## 1. Prompt 模板系统

### 1.1 创建自定义 Prompt 模板

```python
from lightagent_workflow.prompts import WorkflowPromptTemplate, WorkflowPromptRegistry

# 创建 registry
registry = WorkflowPromptRegistry()

# 定义自定义 prompt 模板
research_prompt = WorkflowPromptTemplate(
    name="research_planning",
    workflow_type="planning",
    system_prompt="""你是一个专业的研究助手。你的任务是制定详细的研究计划。

研究计划应该包括：
1. 文献综述
2. 数据收集
3. 分析方法
4. 验证步骤""",
    task_prompt="""研究目标：{goal}

背景信息：{context}

请制定详细的研究计划，包括每个步骤的时间估算。"""
)

# 注册模板
registry.register_template(research_prompt)
```

### 1.2 使用 Prompt 模板

```python
from lightagent_workflow.config import ExtendedWorkflowConfig

# 创建配置，指定使用自定义 prompt
config = ExtendedWorkflowConfig(
    workflow_type="planning",
    prompts=WorkflowPromptConfig(
        template_name="research_planning",  # 使用自定义模板
        variables={'default_duration': '2 weeks'}
    )
)
```

---

## 2. 工具池系统

### 2.1 全局工具池

**全局工具**会被所有工作流继承使用。

```python
from lightagent_workflow.tools import ToolRegistry
from lightagent.tools import FunctionBuilder, MCPTool

# 创建工具注册表
tool_registry = ToolRegistry()

# 添加全局工具
def search_web(query: str) -> str:
    """搜索网络"""
    return f"搜索结果: {query}"

def calculate(expression: str) -> float:
    """计算表达式"""
    return eval(expression)

# 创建工具实例
search_tool = FunctionBuilder.create_tool(search_web)
calc_tool = FunctionBuilder.create_tool(calculate)

# 添加到全局池（所有工作流都能使用）
tool_registry.add_global_tool(search_tool)
tool_registry.add_global_tool(calc_tool)

print(f"全局工具: {tool_registry.list_global_tools()}")
# 输出: ['search_web', 'calculate']
```

### 2.2 工作流特定工具

为特定工作流类型添加专属工具。

```python
# 为 Planning 工作流添加特定工具
def decompose_task(task: str) -> list:
    """分解任务"""
    return [f"子任务1: {task}", f"子任务2: {task}"]

decompose_tool = FunctionBuilder.create_tool(decompose_task)

# 只添加到 planning 工作流
tool_registry.add_workflow_tool(
    workflow_type="planning",
    tool=decompose_tool
)

# 为 Code-Execute 工作流添加特定工具
def execute_python(code: str) -> str:
    """执行 Python 代码"""
    exec(code)
    return "执行成功"

execute_tool = FunctionBuilder.create_tool(execute_python)

# 只添加到 code_execute_refine 工作流
tool_registry.add_workflow_tool(
    workflow_type="code_execute_refine",
    tool=execute_tool
)
```

### 2.3 工作流实例工具

为**特定工作流实例**添加工具（不影响其他实例）。

```python
from lightagent_workflow import WorkflowManager

manager = WorkflowManager(agent=agent, tool_registry=tool_registry)

# 创建工作流1，添加专用工具
wf1 = await manager.create_workflow("planning", "研究AI")

# 为这个特定实例添加工具
wf1.add_tool(my_custom_tool, name="custom_analysis")

# 创建工作流2（不会继承 wf1 的实例工具）
wf2 = await manager.create_workflow("planning", "研究生物")
# wf2 没有 custom_analysis 工具
```

---

## 3. 工具复用机制

### 3.1 工具继承层次

```
全局工具池 (Global)
    ↓
工作流类型池 (Workflow Type)  - 例如: planning 池
    ↓
工作流实例 (Instance)         - 例如: wf1 实例
```

**工作流可以访问：**
1. 全局工具（所有工作流）
2. 工作流类型工具（同一类型的工作流）
3. 实例特定工具（仅此实例）

### 3.2 查看可用工具

```python
# 查看全局工具
print("全局工具:", tool_registry.list_global_tools())

# 查看 planning 工作流的工具
print("Planning工具:", tool_registry.list_workflow_tools("planning"))

# 查看工作流实例的可用工具
workflow = await manager.create_workflow("planning", "...")
tools = workflow.tool_manager.get_tools()
tool_names = [getattr(t, 'name', 'unknown') for t in tools]
print("实例可用工具:", tool_names)
```

### 3.3 工具复用示例

```python
# 定义一个通用的分析工具
def analyze_data(data: str) -> dict:
    """分析数据"""
    return {"summary": f"分析了 {len(data)} 字符", "keywords": []}

analysis_tool = FunctionBuilder.create_tool(analyze_data)

# 添加到多个工作流类型
tool_registry.register_tool_for_workflows(
    tool=analysis_tool,
    workflow_types=["planning", "sequential", "interactive"]
)

# 现在这三种工作流都能使用 analysis_tool
```

---

## 4. 完整使用示例

### 4.1 设置阶段

```python
import asyncio
from lightagent import Agent, MockAdapter, ModelConfig
from lightagent_workflow import (
    WorkflowManager,
    create_workflow_manager
)
from lightagent_workflow.prompts import create_default_prompt_registry
from lightagent_workflow.tools import create_default_tool_registry
from lightagent.tools import FunctionBuilder

# ========== 1. 创建 Agent ==========
agent = Agent(
    name="workflow-agent",
    model_adapter=MockAdapter(config=ModelConfig(model_name="mock"))
)

# ========== 2. 创建 Prompt Registry ==========
prompt_registry = create_default_prompt_registry()

# 添加自定义 prompt
custom_research_prompt = WorkflowPromptTemplate(
    name="custom_research",
    workflow_type="planning",
    system_prompt="你是专业研究助手",
    task_prompt="研究目标: {goal}\n请制定详细计划"
)
prompt_registry.register_template(custom_research_prompt)

# ========== 3. 创建 Tool Registry ==========
tool_registry = create_default_tool_registry()

# 添加全局工具
def web_search(query: str) -> str:
    return f"搜索结果: {query}"

search_tool = FunctionBuilder.create_tool(web_search)
tool_registry.add_global_tool(search_tool)

# 为 planning 工作流添加特定工具
def task_decompose(task: str) -> list:
    return [f"步骤1: {task}", f"步骤2: {task}"]

decompose_tool = FunctionBuilder.create_tool(task_decompose)
tool_registry.add_workflow_tool("planning", decompose_tool)

# ========== 4. 创建 WorkflowManager ==========
manager = WorkflowManager(
    agent=agent,
    prompt_registry=prompt_registry,  # 传入 prompt registry
    tool_registry=tool_registry       # 传入 tool registry
)
```

### 4.2 使用阶段

#### 示例 1: 使用自定义 Prompt

```python
from lightagent_workflow.config import ExtendedWorkflowConfig, WorkflowPromptConfig

# 创建配置，使用自定义 prompt
config = ExtendedWorkflowConfig(
    workflow_type="planning",
    prompts=WorkflowPromptConfig(
        template_name="custom_research"  # 使用自定义模板
    )
)

# 创建工作流
workflow = await manager.create_workflow(
    workflow_type="planning",
    goal="研究大语言模型",
    config=config.dict()
)

# 执行时会使用自定义 prompt
result = await manager.start_workflow(workflow.workflow_id, "研究大语言模型")
```

#### 示例 2: 工具复用

```python
# 创建两个不同类型的工作流
wf1 = await manager.create_workflow("planning", "研究AI")
wf2 = await manager.create_workflow("sequential", "数据分析")

# 两个工作流都有 web_search 工具（来自全局池）
print("WF1 工具:", wf1.list_tools())
print("WF2 工具:", wf2.list_tools())

# 输出:
# WF1 工具: ['web_search', 'task_decompose']  # 全局 + planning特定
# WF2 工具: ['web_search']                    # 只有全局
```

#### 示例 3: 动态添加工具

```python
# 为特定工作流实例添加临时工具
def custom_analyzer(text: str) -> dict:
    return {"length": len(text)}

analyzer_tool = FunctionBuilder.create_tool(custom_analyzer)

# 添加到 wf1 实例（不影响其他工作流）
wf1.add_tool(analyzer_tool)

print("WF1 工具:", wf1.list_tools())
# 输出: ['web_search', 'task_decompose', 'custom_analyzer']

print("WF2 工具:", wf2.list_tools())
# 输出: ['web_search']
```

---

## 5. 高级配置

### 5.1 工具过滤

```python
from lightagent_workflow.config import WorkflowToolConfig

# 只使用指定的工具
config = ExtendedWorkflowConfig(
    workflow_type="planning",
    tools=WorkflowToolConfig(
        include_tools=["web_search", "task_decompose"],  # 白名单
        use_global_tools=True,
        use_workflow_tools=True
    )
)
```

### 5.2 Prompt 变量

```python
config = ExtendedWorkflowConfig(
    workflow_type="planning",
    prompts=WorkflowPromptConfig(
        template_name="custom_research",
        variables={  # prompt 中的变量
            "default_duration": "2 weeks",
            "team_size": "5 people"
        }
    )
)
```

### 5.3 动态 Prompt

```python
# 在执行时动态设置 prompt
wf1 = await manager.create_workflow("planning", "研究AI")

# 运行时设置 system prompt
wf1.set_system_prompt("你现在是高级研究顾问")

# 运行时设置 prompt 变量
wf1.config['prompt_variables'] = {
    "deadline": "2024-12-31",
    "budget": "$10,000"
}
```

---

## 6. 最佳实践

### 6.1 Prompt 组织

```python
# 按工作流类型组织 prompt
PROMPTS = {
    "planning": {
        "research": WorkflowPromptTemplate(...),
        "development": WorkflowPromptTemplate(...)
    },
    "sequential": {
        "deployment": WorkflowPromptTemplate(...),
        "testing": WorkflowPromptTemplate(...)
    }
}

# 注册所有 prompt
for workflow_type, templates in PROMPTS.items():
    for name, template in templates.items():
        registry.register_template(template)
```

### 6.2 工具分层

```python
# Layer 1: 基础工具（所有工作流）
tool_registry.add_global_tool(basic_tool)

# Layer 2: 类型工具（同类型工作流）
tool_registry.add_workflow_tool("planning", planning_tool)

# Layer 3: 实例工具（特定实例）
workflow.add_tool(instance_tool)
```

### 6.3 配置复用

```python
# 定义常用配置模板
RESEARCH_CONFIG = ExtendedWorkflowConfig(
    workflow_type="planning",
    prompts=WorkflowPromptConfig(template_name="research_planning"),
    tools=WorkflowToolConfig(include_tools=["web_search", "analyze"])
)

# 复用配置
wf1 = await manager.create_workflow("planning", "研究AI", config=RESEARCH_CONFIG.dict())
wf2 = await manager.create_workflow("planning", "研究生物", config=RESEARCH_CONFIG.dict())
```

---

## 7. 总结

### 关键要点

1. **Prompt 模板**
   - 每个工作流类型有独立的 prompt 模板
   - 支持模板变量和格式化
   - 可以运行时覆盖

2. **工具分层**
   - 全局工具 → 工作流类型工具 → 实例工具
   - 自动继承和覆盖
   - 支持工具过滤

3. **复用机制**
   - 工具可以在多个工作流类型间共享
   - 配置可以定义和复用
   - 实例间互不影响

### 实际应用场景

- **研究型工作流**：文献搜索 + 数据分析工具
- **开发型工作流**：代码生成 + 测试工具
- **部署型工作流**：CI/CD + 监控工具
- **客服型工作流**：知识库 + 对话管理工具

通过合理配置 prompt 和工具，可以让不同工作流各司其职，同时实现工具的高效复用。
