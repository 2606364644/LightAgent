# 工作流系统快速参考

## 快速开始

```python
from lightagent import Agent
from lightagent_workflow import WorkflowManager
from lightagent_workflow import register_default_workflow_types
from lightagent_workflow.prompts import create_default_prompt_registry
from lightagent_workflow.tools import create_default_tool_registry

# 1. 创建 Agent
agent = Agent(...)

# 2. 创建 Registries
prompt_registry = create_default_prompt_registry()
tool_registry = create_default_tool_registry()

# 3. 创建 Manager
manager = WorkflowManager(
    agent=agent,
    prompt_registry=prompt_registry,
    tool_registry=tool_registry
)

# 4. 注册工作流类型
register_default_workflow_types(manager)

# 5. 创建并执行工作流
wf = await manager.create_workflow("planning", "研究AI")
result = await manager.start_workflow(wf.workflow_id, "研究AI")
```

---

## 核心 API

### WorkflowManager

```python
# 创建工作流
workflow = await manager.create_workflow(
    workflow_type,    # "planning", "sequential", "interactive", etc.
    goal,             # 目标描述
    config=None       # 可选配置
)

# 执行工作流
result = await manager.start_workflow(
    workflow_id,
    goal,
    context=None,
    block=True,       # 是否等待完成
    timeout=None
)

# 并发执行多个
await manager.start_workflows([id1, id2, id3])

# 生命周期控制
await manager.pause_workflow(workflow_id)
await manager.resume_workflow(workflow_id)
await manager.cancel_workflow(workflow_id)

# 查询
workflow = await manager.get_workflow(workflow_id)
workflows = await manager.list_workflows(status="running")
result = await manager.wait_for_completion(workflow_id)
```

### Prompt 管理

```python
from lightagent_workflow.prompts import WorkflowPromptTemplate

# 创建模板
template = WorkflowPromptTemplate(
    name="my_template",
    workflow_type="planning",
    system_prompt="你是专家",
    task_prompt="任务: {goal}"
)

# 注册模板
prompt_registry.register_template(template)

# 使用模板
from lightagent_workflow.config import ExtendedWorkflowConfig, WorkflowPromptConfig

config = ExtendedWorkflowConfig(
    workflow_type="planning",
    prompts=WorkflowPromptConfig(
        template_name="my_template",
        variables={"key": "value"}
    )
)
```

### 工具管理

```python
# 全局工具（所有工作流都能用）
tool_registry.add_global_tool(tool)

# 工作流特定工具
tool_registry.add_workflow_tool("planning", tool)

# 添加到多个工作流类型
tool_registry.register_tool_for_workflows(
    tool=tool,
    workflow_types=["planning", "sequential", "interactive"]
)

# 实例特定工具
workflow.add_tool(tool)

# 查询工具
print(workflow.list_tools())
print(tool_registry.list_global_tools())
print(tool_registry.list_workflow_tools("planning"))
```

---

## 工作流类型

### 1. Planning Workflow（任务分解型）

```python
config = {
    'max_recursion_depth': 3,
    'execution_mode': 'sequential',  # sequential, parallel, adaptive
    'auto_refine': True
}

wf = await manager.create_workflow("planning", "复杂任务", config=config)
```

**适用场景：**
- 复杂任务分解
- 研究型任务
- 多步骤分析

### 2. Sequential Workflow（固定步骤型）

```python
config = {
    'steps': [
        {'name': '步骤1', 'action': 'action1', 'stop_on_failure': True},
        {'name': '步骤2', 'action': 'action2', 'stop_on_failure': False}
    ],
    'stop_on_first_failure': True
}

wf = await manager.create_workflow("sequential", "流程", config=config)
```

**适用场景：**
- CI/CD 流水线
- 数据处理管道
- 固定流程执行

### 3. Interactive Workflow（多轮对话型）

```python
config = {
    'max_rounds': 10,
    'system_prompt': '你是客服助手'
}

wf = await manager.create_workflow("interactive", "对话", config=config)
```

**适用场景：**
- 聊天机器人
- 问答系统
- 交互式助手

### 4. Code-Execute-Refine Workflow（代码迭代型）

```python
config = {
    'max_iterations': 5,
    'language': 'python'
}

wf = await manager.create_workflow("code_execute_refine", "生成代码", config=config)
```

**适用场景：**
- 代码生成
- 数据分析脚本
- 算法开发

### 5. Human-in-the-Loop Workflow（人工审批型）

```python
config = {
    'max_iterations': 10,
    'auto_approve_safe_actions': False
}

wf = await manager.create_workflow("human_loop", "审查任务", config=config)
```

**适用场景：**
- 内容审核
- 关键决策
- 质量保证

---

## 工具复用模式

### 模式 1: 全局工具

```python
# 所有工作流都能用
tool_registry.add_global_tool(search_tool)
tool_registry.add_global_tool(analyze_tool)
```

### 模式 2: 类型工具

```python
# 只有 planning 工作流能用
tool_registry.add_workflow_tool("planning", planning_tool)

# 只有 code_execute_refine 能用
tool_registry.add_workflow_tool("code_execute_refine", code_tool)
```

### 模式 3: 跨类型复用

```python
# planning 和 sequential 都能用
tool_registry.register_tool_for_workflows(
    tool=common_tool,
    workflow_types=["planning", "sequential"]
)
```

### 模式 4: 实例工具

```python
# 只有这个实例能用
wf1 = await manager.create_workflow("planning", "任务1")
wf1.add_tool(custom_tool)

# wf2 没有 custom_tool
wf2 = await manager.create_workflow("planning", "任务2")
```

---

## 配置复用

### 定义配置模板

```python
from lightagent_workflow.config import (
    ExtendedWorkflowConfig,
    WorkflowPromptConfig,
    WorkflowToolConfig
)

RESEARCH_CONFIG = ExtendedWorkflowConfig(
    workflow_type="planning",
    prompts=WorkflowPromptConfig(
        template_name="research_planning"
    ),
    tools=WorkflowToolConfig(
        include_tools=["search_web", "analyze_data"],
        use_global_tools=True
    )
)
```

### 复用配置

```python
wf1 = await manager.create_workflow(
    "planning",
    "研究AI",
    config=RESEARCH_CONFIG.dict()
)

wf2 = await manager.create_workflow(
    "planning",
    "研究生物",
    config=RESEARCH_CONFIG.dict()
)
```

---

## 事件回调

```python
@manager.on_workflow_started
async def on_start(workflow_id: str):
    print(f"工作流 {workflow_id} 已启动")

@manager.on_task_completed
async def on_task_complete(workflow_id: str, task_id: str):
    print(f"任务 {task_id} 已完成")

@manager.on_workflow_completed
async def on_complete(workflow_id: str, result: dict):
    print(f"工作流完成: {result}")

@manager.on_workflow_failed
async def on_failed(workflow_id: str, error: str):
    print(f"工作流失败: {error}")
```

---

## 自定义工作流类型

```python
from lightagent_workflow import BaseWorkflow

class MyCustomWorkflow(BaseWorkflow):
    workflow_type = "my_custom"

    async def execute(self, goal, context):
        # 实现自定义逻辑
        return {'success': True, 'result': 'done'}

    async def validate(self, goal):
        # 验证目标是否适合此工作流
        return len(goal) > 0

# 注册自定义类型
manager.register_workflow_type('my_custom', MyCustomWorkflow)

# 使用自定义工作流
wf = await manager.create_workflow("my_custom", "自定义任务")
```

---

## 常用命令

### 创建工具

```python
from lightagent.tools import FunctionBuilder

def my_function(param: str) -> str:
    """函数说明"""
    return f"结果: {param}"

tool = FunctionBuilder.create_tool(my_function)
```

### 添加工具

```python
# 全局
tool_registry.add_global_tool(tool)

# 类型
tool_registry.add_workflow_tool("planning", tool)

# 实例
workflow.add_tool(tool)
```

### 查询状态

```python
# 工作流状态
workflow = await manager.get_workflow(workflow_id)
print(f"状态: {workflow.status}")
print(f"进度: {workflow.get_progress()}%")

# 列出工作流
all_wfs = await manager.list_workflows()
running_wfs = await manager.list_workflows(status="running")
planning_wfs = await manager.list_workflows(workflow_type="planning")
```

---

## 文档索引

- **完整架构**: `docs/WORKFLOW_ARCHITECTURE.md`
- **Prompt 和工具**: `docs/WORKFLOW_PROMPTS_AND_TOOLS.md`
- **多工作流指南**: `docs/WORKFLOW_MULTI_GUIDE.md`
- **多工作流系统**: `docs/MULTI_WORKFLOW_SYSTEM.md`

---

## 示例代码

- **基础示例**: `examples/workflow_types_example.py`
- **高级示例**: `examples/workflow_advanced_example.py`
