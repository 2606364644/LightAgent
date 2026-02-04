# 多工作流类型系统实现总结

## 概述

成功实现了 LightAgent 的多工作流类型系统，支持不同类型的工作流流程，不再局限于单一的"任务分解 -> 执行"模式。

## 实现的功能

### 1. 基础架构

#### BaseWorkflow（基础工作流接口）
- 文件：`lightagent-workflow/base.py`
- 提供统一的工作流接口
- 支持暂停/恢复/取消操作
- 进度追踪和状态管理

#### WorkflowManager（工作流管理器）
- 文件：`lightagent-workflow/manager.py`
- 管理多个工作流实例
- 支持并发执行
- 统一的生命周期控制
- 事件回调系统

### 2. 工作流类型

#### PlanningWorkflow（任务分解型）
- 文件：`lightagent-workflow/types/planning.py`
- 流程：分解任务 -> 执行任务列表 -> 验证 -> 优化
- 特性：
  - LLM 自动任务分解
  - 支持递归分解（max_recursion_depth）
  - 三种执行模式（sequential/parallel/adaptive）
  - 失败任务自动重试

**适用场景：**
- 复杂任务分解
- 研究型任务
- 多步骤分析

#### SequentialWorkflow（固定步骤型）
- 文件：`lightagent-workflow/types/sequential.py`
- 流程：Step1 -> Step2 -> Step3 -> ... -> 完成
- 特性：
  - 预定义步骤序列
  - 支持步骤失败停止
  - 支持跳过机制
  - 可动态添加/删除步骤

**适用场景：**
- CI/CD 流水线
- 数据处理管道
- 固定流程执行

#### InteractiveWorkflow（多轮对话型）
- 文件：`lightagent-workflow/types/interactive.py`
- 流程：用户输入 -> LLM -> 输出 -> 用户输入 -> ...
- 特性：
  - 对话历史管理
  - 自动完成检测
  - 支持自定义输入/输出处理器
  - 系统提示词设置

**适用场景：**
- 聊天机器人
- 问答系统
- 交互式助手

#### CodeExecuteRefineWorkflow（代码执行反馈型）
- 文件：`lightagent-workflow/types/code_execute.py`
- 流程：生成代码 -> 执行 -> 检查结果 -> 优化 -> 执行 -> ...
- 特性：
  - 迭代代码生成
  - 执行结果反馈
  - 错误自动修复
  - 支持多种编程语言

**适用场景：**
- 代码生成
- 数据分析脚本
- 算法开发

#### HumanInTheLoopWorkflow（人工审批型）
- 文件：`lightagent-workflow/types/human_loop.py`
- 流程：Agent 提议 -> 人工审批 -> 执行/重试
- 特性：
  - 动作提议机制
  - 人工审批接口
  - 审批历史记录
  - 支持自动批准安全操作

**适用场景：**
- 内容审核
- 关键决策
- 质量保证

### 3. 核心特性

#### 多工作流并发
```python
manager = WorkflowManager(agent=agent)

# 创建多个工作流
wf1 = await manager.create_workflow("planning", "任务1")
wf2 = await manager.create_workflow("sequential", "任务2")
wf3 = await manager.create_workflow("interactive", "任务3")

# 并发执行
await manager.start_workflows([wf1.workflow_id, wf2.workflow_id, wf3.workflow_id])
```

#### 生命周期控制
```python
# 启动（非阻塞）
await manager.start_workflow(workflow_id, block=False)

# 暂停
await manager.pause_workflow(workflow_id)

# 恢复
await manager.resume_workflow(workflow_id)

# 取消
await manager.cancel_workflow(workflow_id)

# 等待完成
result = await manager.wait_for_completion(workflow_id)
```

#### 查询和过滤
```python
# 获取工作流
workflow = await manager.get_workflow(workflow_id)

# 列出所有工作流
all_workflows = await manager.list_workflows()

# 按状态过滤
running = await manager.list_workflows(status="running")

# 按类型过滤
planning_wfs = await manager.list_workflows(workflow_type="planning")
```

#### 事件回调
```python
@manager.on_workflow_started
async def on_start(workflow_id: str):
    print(f"工作流 {workflow_id} 已启动")

@manager.on_workflow_completed
async def on_complete(workflow_id: str, result: dict):
    print(f"工作流 {workflow_id} 已完成")
```

## 文件结构

```
lightagent-workflow/
├── __init__.py              # 模块导出（已更新）
├── base.py                  # 基础接口（已扩展）
├── manager.py               # 工作流管理器（新增）
├── engine.py                # 原工作流引擎（保留）
├── types/                   # 工作流类型目录（新增）
│   ├── __init__.py         # 类型注册
│   ├── planning.py         # Planning Workflow
│   ├── sequential.py       # Sequential Workflow
│   ├── interactive.py      # Interactive Workflow
│   ├── code_execute.py     # Code-Execute-Refine Workflow
│   └── human_loop.py       # Human-in-the-Loop Workflow
└── ...（其他原有文件）
```

## 使用方式

### 基础使用

```python
from lightagent import Agent
from lightagent_workflow import WorkflowManager, create_workflow_manager

# 1. 创建 Agent
agent = Agent(...)

# 2. 创建 WorkflowManager
manager = await create_workflow_manager(agent=agent)

# 3. 注册工作流类型
from lightagent_workflow import register_default_workflow_types
register_default_workflow_types(manager)

# 4. 创建工作流
workflow = await manager.create_workflow(
    workflow_type="planning",  # 工作流类型
    goal="研究并实现 RAG 系统"
)

# 5. 执行工作流
result = await manager.start_workflow(
    workflow.workflow_id,
    goal="研究并实现 RAG 系统"
)
```

### 高级使用

```python
# 自定义配置
workflow = await manager.create_workflow(
    workflow_type="planning",
    goal="复杂任务",
    config={
        'max_recursion_depth': 5,  # 最大递归深度
        'execution_mode': 'parallel',  # 并行执行
        'auto_refine': True  # 自动重试失败任务
    }
)

# 自定义处理器（对于不同工作流类型）
if workflow.workflow_type == "code_execute_refine":
    workflow.set_code_generator(my_generator)
    workflow.set_code_executor(my_executor)
    workflow.set_success_checker(my_checker)

# 批量操作
workflow_ids = [wf1.workflow_id, wf2.workflow_id, wf3.workflow_id]
await manager.start_workflows(workflow_ids)
results = await manager.wait_for_all(workflow_ids)
```

## 与原系统的兼容性

- **保留原 WorkflowEngine**：`lightagent-workflow/engine.py` 保持不变
- **向后兼容**：现有代码可以继续使用 `WorkflowEngine`
- **渐进式迁移**：可以逐步迁移到新的多工作流系统

## 扩展性

### 添加自定义工作流类型

```python
from lightagent_workflow import BaseWorkflow

class MyCustomWorkflow(BaseWorkflow):
    workflow_type = "my_custom"

    async def execute(self, goal, context):
        # 实现自定义流程
        return {'success': True}

    async def validate(self, goal):
        # 验证目标是否适合此工作流
        return True

# 注册自定义类型
manager.register_workflow_type('my_custom', MyCustomWorkflow)
```

## 示例代码

完整示例：`examples/workflow_types_example.py`

包含 8 个示例：
1. Planning Workflow 示例
2. Sequential Workflow 示例
3. Interactive Workflow 示例
4. Code-Execute-Refine Workflow 示例
5. Human-in-the-Loop Workflow 示例
6. 多工作流并发执行
7. 工作流生命周期控制
8. 列出和过滤工作流

## 总结

### 实现的核心价值

1. **灵活性**：不同工作流有不同的执行流程，不再局限于单一模式
2. **可扩展**：轻松添加新的工作流类型
3. **并发支持**：支持多个工作流并发执行
4. **统一管理**：WorkflowManager 提供统一的管理接口
5. **生命周期控制**：暂停、恢复、取消等工作流操作
6. **向后兼容**：保留原有接口，渐进式升级

### 回答你的三个问题

1. **当前工作流是什么流程？**
   - 答：现在支持多种流程，不仅仅是"todolist -> 执行"
   - 包括：任务分解、固定步骤、多轮对话、代码迭代、人工审批等

2. **当前结构是否只能一条工作流？**
   - 答：不再限制！
   - 通过 `WorkflowManager` 可以创建和管理多个工作流
   - 支持并发执行、独立状态管理

3. **工作流能处理复杂任务吗？递归执行 todolist？**
   - 答：完全支持！
   - `PlanningWorkflow` 支持递归任务分解（max_recursion_depth）
   - 可以配置停止条件（stop_when_simple）
   - 支持手动指定任务列表（通过 config）

## 下一步

建议的使用步骤：

1. **测试基本功能**
   ```bash
   python examples/workflow_types_example.py
   ```

2. **阅读示例代码**
   - `examples/workflow_types_example.py` - 各种工作流类型示例
   - `examples/workflow_multi_example.py` - 多工作流并发示例

3. **集成到项目**
   - 根据需求选择合适的工作流类型
   - 配置工作流参数
   - 实现自定义处理器（如需要）

4. **扩展自定义类型**
   - 继承 `BaseWorkflow`
   - 实现 `execute()` 和 `validate()` 方法
   - 注册到 `WorkflowManager`
