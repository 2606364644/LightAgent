# LightAgent 工作流架构完整总结

## 概述

LightAgent 工作流系统现在支持：
1. ✅ **多种工作流类型** - 不同流程不同处理
2. ✅ **自定义 Prompt** - 每个工作流有自己的 prompt 模板
3. ✅ **工具池管理** - 全局工具、工作流特定工具、实例工具
4. ✅ **工具复用** - 工具可以在多个工作流间共享
5. ✅ **并发执行** - 多个工作流同时运行
6. ✅ **生命周期控制** - 暂停、恢复、取消

---

## 架构层次

```
┌─────────────────────────────────────────────────────────────┐
│                    WorkflowManager                          │
│                   (工作流管理器)                             │
│  - 创建工作流                                                │
│  - 并发执行                                                  │
│  - 生命周期控制                                              │
└─────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┴─────────────────────┐
        │                                           │
┌───────▼────────┐                         ┌────────▼────────┐
│ PromptRegistry │                         │  ToolRegistry   │
│ (Prompt 注册表) │                         │  (工具注册表)    │
│                │                         │                 │
│ - 模板管理      │                         │ - 全局工具池     │
│ - 变量替换      │                         │ - 类型工具池     │
│ - 格式化        │                         │ - 工具复用       │
└────────────────┘                         └─────────────────┘
        │                                           │
        └───────────────────┬───────────────────────┘
                            │
                            ▼
              ┌─────────────────────────┐
              │    BaseWorkflow          │
              │   (工作流基础类)         │
              │                         │
              │ - execute()             │
              │ - validate()            │
              │ - pause/resume/cancel   │
              └─────────────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        │                   │                   │
┌───────▼────────┐  ┌───────▼────────┐  ┌─────▼──────────┐
│PlanningWorkflow│  │SequentialWF   │  │InteractiveWF   │
│(任务分解型)     │  │(固定步骤型)    │  │(多轮对话型)    │
│                │  │               │  │                │
│- 递归分解       │  │- 步骤序列      │  │- 对话历史      │
│- 自动重试       │  │- 失败停止      │  │- 完成检测      │
└────────────────┘  └────────────────┘  └────────────────┘
        │                   │                   │
┌───────▼────────┐  ┌───────▼────────┐  ┌─────▼──────────┐
│CodeExecuteWF   │  │HumanLoopWF    │  │  CustomWF      │
│(代码迭代型)    │  │(人工审批型)    │  │  (自定义型)    │
│                │  │               │  │                │
│- 代码生成      │  │- 人工审批      │  │- 完全自定义     │
│- 错误修复      │  │- 审批历史      │  │- 扩展接口       │
└────────────────┘  └────────────────┘  └────────────────┘
```

---

## 核心组件

### 1. WorkflowManager（工作流管理器）

**职责：** 管理多个工作流实例

```python
manager = WorkflowManager(
    agent=agent,
    prompt_registry=prompt_registry,  # Prompt 注册表
    tool_registry=tool_registry,      # 工具注册表
    max_concurrent_workflows=10
)

# 注册工作流类型
register_default_workflow_types(manager)
```

### 2. PromptRegistry（Prompt 注册表）

**职责：** 管理 prompt 模板

```python
# 创建 registry
prompt_registry = WorkflowPromptRegistry()

# 注册模板
template = WorkflowPromptTemplate(
    name="my_template",
    workflow_type="planning",
    system_prompt="你是专家",
    task_prompt="任务: {goal}"
)
prompt_registry.register_template(template)

# 获取模板
template = prompt_registry.get_template("my_template")
```

### 3. ToolRegistry（工具注册表）

**职责：** 管理工具池

```python
# 创建 registry
tool_registry = ToolRegistry()

# 添加全局工具
tool_registry.add_global_tool(search_tool)

# 添加工作流特定工具
tool_registry.add_workflow_tool("planning", calc_tool)

# 添加到多个工作流类型
tool_registry.register_tool_for_workflows(
    tool=analyze_tool,
    workflow_types=["planning", "sequential"]
)
```

### 4. BaseWorkflow（工作流基础类）

**职责：** 工作流的基础接口

```python
class MyWorkflow(BaseWorkflow):
    workflow_type = "my_custom"

    async def execute(self, goal, context):
        # 实现工作流逻辑
        return {'success': True}

    async def validate(self, goal):
        # 验证目标
        return True
```

---

## 工具继承层次

```
全局工具池 (Global Tool Pool)
    │
    ├─ search_web      ← 所有工作流都能用
    ├─ analyze_data    ← 所有工作流都能用
    └─ calculate       ← 所有工作流都能用
    │
    ▼
Planning 工作流池 (Planning Tool Pool)
    │
    ├─ task_decompose  ← 只有 planning 能用
    ├─ complexity_calc ← 只有 planning 能用
    │
    ▼
Planning 工作流实例 (Instance)
    │
    ├─ custom_tool     ← 只有这个实例能用
    └─ temp_analyzer   ← 只有这个实例能用
```

**访问优先级：** 实例 > 类型 > 全局

---

## Prompt 配置层次

```
WorkflowPromptTemplate
    │
    ├─ system_prompt   ← 系统提示词
    ├─ task_prompt     ← 任务提示词
    └─ variables       ← 模板变量
         │
         ▼
ExtendedWorkflowConfig
    │
    ├─ template_name   ← 使用哪个模板
    ├─ override_system ← 是否覆盖系统提示
    ├─ override_task   ← 是否覆盖任务提示
    └─ variables       ← 额外的变量
```

---

## 使用模式

### 模式 1: 基础使用

```python
# 1. 创建 registries
prompt_registry = create_default_prompt_registry()
tool_registry = create_default_tool_registry()

# 2. 创建 manager
manager = WorkflowManager(
    agent=agent,
    prompt_registry=prompt_registry,
    tool_registry=tool_registry
)

# 3. 创建工作流
wf = await manager.create_workflow("planning", "研究AI")

# 4. 执行
result = await manager.start_workflow(wf.workflow_id, "研究AI")
```

### 模式 2: 自定义 Prompt

```python
# 注册自定义 prompt
custom_prompt = WorkflowPromptTemplate(
    name="research",
    workflow_type="planning",
    system_prompt="你是研究专家",
    task_prompt="研究: {goal}"
)
prompt_registry.register_template(custom_prompt)

# 使用自定义 prompt
config = ExtendedWorkflowConfig(
    workflow_type="planning",
    prompts=WorkflowPromptConfig(
        template_name="research"
    )
)

wf = await manager.create_workflow("planning", "研究", config=config.dict())
```

### 模式 3: 工具复用

```python
# 定义通用工具
def analyze(data: str) -> dict:
    return {"length": len(data)}

tool = FunctionBuilder.create_tool(analyze)

# 添加到多个工作流类型
tool_registry.register_tool_for_workflows(
    tool=tool,
    workflow_types=["planning", "sequential", "interactive"]
)

# 现在三种工作流都能用 analyze 工具
wf1 = await manager.create_workflow("planning", "任务1")
wf2 = await manager.create_workflow("sequential", "任务2")
wf3 = await manager.create_workflow("interactive", "任务3")

# 都有 analyze 工具
assert "analyze" in wf1.list_tools()
assert "analyze" in wf2.list_tools()
assert "analyze" in wf3.list_tools()
```

### 模式 4: 实例特定配置

```python
# 创建工作流
wf1 = await manager.create_workflow("planning", "研究AI")
wf2 = await manager.create_workflow("planning", "研究生物")

# 为 wf1 添加特定工具
wf1.add_tool(ai_tool)

# wf1 有 ai_tool，wf2 没有
assert "ai_tool" in wf1.list_tools()
assert "ai_tool" not in wf2.list_tools()

# 为 wf1 设置特定 prompt
wf1.set_system_prompt("你是AI研究专家")
```

---

## 最佳实践

### 1. Prompt 组织

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

# 批量注册
for wf_type, templates in PROMPTS.items():
    for name, template in templates.items():
        prompt_registry.register_template(template)
```

### 2. 工具分层

```python
# Layer 1: 基础工具（所有工作流）
tool_registry.add_global_tool(basic_tool)

# Layer 2: 类型工具（同类型工作流）
tool_registry.add_workflow_tool("planning", planning_tool)

# Layer 3: 实例工具（特定实例）
workflow.add_tool(instance_tool)
```

### 3. 配置模板化

```python
# 定义配置模板
RESEARCH_CONFIG = ExtendedWorkflowConfig(
    workflow_type="planning",
    prompts=WorkflowPromptConfig(template_name="research"),
    tools=WorkflowToolConfig(include_tools=["search", "analyze"])
)

# 复用配置
wf1 = await manager.create_workflow("planning", "AI", config=RESEARCH_CONFIG.dict())
wf2 = await manager.create_workflow("planning", "生物", config=RESEARCH_CONFIG.dict())
```

---

## 文件清单

### 核心实现

1. **`lightagent-workflow/base.py`**
   - BaseWorkflow 基础接口
   - WorkflowStatus 状态枚举
   - WorkflowStep 步骤类

2. **`lightagent-workflow/manager.py`**
   - WorkflowManager 管理器
   - 工作流创建和执行
   - 生命周期控制

3. **`lightagent-workflow/prompts.py`**
   - WorkflowPromptTemplate Prompt 模板
   - WorkflowPromptRegistry 注册表
   - 默认 prompt 模板

4. **`lightagent-workflow/tools.py`**
   - ToolPool 工具池
   - ToolRegistry 注册表
   - WorkflowToolManager 管理器

5. **`lightagent-workflow/config.py`**
   - ExtendedWorkflowConfig 扩展配置
   - WorkflowPromptConfig Prompt 配置
   - WorkflowToolConfig 工具配置
   - WorkflowExecutionConfig 执行配置

### 工作流类型

6. **`lightagent-workflow/types/planning.py`** - PlanningWorkflow
7. **`lightagent-workflow/types/sequential.py`** - SequentialWorkflow
8. **`lightagent-workflow/types/interactive.py`** - InteractiveWorkflow
9. **`lightagent-workflow/types/code_execute.py`** - CodeExecuteRefineWorkflow
10. **`lightagent-workflow/types/human_loop.py`** - HumanInTheLoopWorkflow

### 文档

11. **`docs/MULTI_WORKFLOW_SYSTEM.md`** - 多工作流系统总结
12. **`docs/WORKFLOW_PROMPTS_AND_TOOLS.md`** - Prompt 和工具指南
13. **`docs/WORKFLOW_MULTI_GUIDE.md`** - 多工作流使用指南

### 示例

14. **`examples/workflow_types_example.py`** - 工作流类型示例
15. **`examples/workflow_advanced_example.py`** - 高级配置示例

---

## 关键特性总结

### ✅ 已实现

1. **多种工作流类型**
   - 5种预定义工作流类型
   - 完全不同的执行流程
   - 可扩展的自定义类型

2. **自定义 Prompt**
   - Prompt 模板系统
   - 变量替换
   - 运行时覆盖

3. **工具池管理**
   - 全局工具池
   - 工作流类型池
   - 实例特定工具

4. **工具复用**
   - 工具可以在多个工作流间共享
   - 继承机制（实例 > 类型 > 全局）
   - 灵活的配置

5. **并发执行**
   - 多个工作流同时运行
   - 独立状态管理
   - 统一控制

6. **生命周期控制**
   - 暂停/恢复
   - 取消
   - 状态查询

---

## 回答你的问题

### 1. 不同的工作流应该有不同的 prompt、不同的工具、不同的工作逻辑

**✅ 已实现**

- **不同 Prompt**：每个工作流类型有独立的 prompt 模板
  ```python
  planning_prompt = WorkflowPromptTemplate(
      workflow_type="planning",
      system_prompt="你是任务规划专家"
  )

  code_prompt = WorkflowPromptTemplate(
      workflow_type="code_execute_refine",
      system_prompt="你是代码生成专家"
  )
  ```

- **不同工具**：每个工作流类型有专属工具池
  ```python
  tool_registry.add_workflow_tool("planning", planning_tool)
  tool_registry.add_workflow_tool("code_execute_refine", code_tool)
  ```

- **不同逻辑**：每个工作流类型有独立的 execute() 实现
  ```python
  class PlanningWorkflow(BaseWorkflow):
      async def execute(self, goal, context):
          # 任务分解逻辑

  class SequentialWorkflow(BaseWorkflow):
      async def execute(self, goal, context):
          # 固定步骤逻辑
  ```

### 2. 工作流1用了工具A，工作流2也要能方便使用工具B

**✅ 已实现**

#### 方式 1: 全局工具（最简单）

```python
# 添加到全局池，所有工作流都能用
tool_registry.add_global_tool(tool_a)
tool_registry.add_global_tool(tool_b)

# 工作流1和2都能用
wf1 = await manager.create_workflow("planning", "任务1")
wf2 = await manager.create_workflow("sequential", "任务2")

# 都有 tool_a 和 tool_b
```

#### 方式 2: 工作流类型复用

```python
# tool_a 供 planning 和 sequential 使用
tool_registry.register_tool_for_workflows(
    tool=tool_a,
    workflow_types=["planning", "sequential"]
)

# tool_b 只供 code_execute_refine 使用
tool_registry.add_workflow_tool("code_execute_refine", tool_b)
```

#### 方式 3: 配置模板

```python
# 定义配置模板
CONFIG_WITH_TOOL_A = ExtendedWorkflowConfig(
    workflow_type="planning",
    tools=WorkflowToolConfig(
        include_tools=["tool_a"]
    )
)

# 复用配置
wf1 = await manager.create_workflow("planning", "任务1", config=CONFIG_WITH_TOOL_A.dict())
wf2 = await manager.create_workflow("planning", "任务2", config=CONFIG_WITH_TOOL_A.dict())
```

---

## 总结

LightAgent 工作流系统现在是一个**完整的、可扩展的、支持复用**的架构：

1. ✅ **不同工作流 = 不同的 prompt、工具、逻辑**
2. ✅ **工具可以在工作流间灵活复用**
3. ✅ **支持自定义配置和扩展**
4. ✅ **完善的文档和示例**

完全满足你的需求！
