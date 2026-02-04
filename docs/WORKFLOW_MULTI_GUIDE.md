# 多工作流使用指南

## 核心概念对比

### 当前架构（单工作流）
```python
# ❌ 问题：只能执行一条工作流
engine = WorkflowEngine(agent=agent)
result1 = await engine.execute("任务1")
result2 = await engine.execute("任务2")  # 丢失 result1 的状态
```

**限制：**
- 一次只能有一个 `current_state`
- 无法并发执行
- 无法暂停/恢复
- 无法追踪多个工作流

---

### 新架构（多工作流）
```python
# ✅ 解决：每个工作流是独立实例
manager = WorkflowManager(agent=agent)

# 创建多个独立工作流
wf1 = await manager.create_workflow("type1", "任务1")
wf2 = await manager.create_workflow("type2", "任务2")
wf3 = await manager.create_workflow("type3", "任务3")

# 并发执行（互不干扰）
results = await asyncio.gather(
    manager.start_workflow(wf1.workflow_id),
    manager.start_workflow(wf2.workflow_id),
    manager.start_workflow(wf3.workflow_id)
)
```

**优势：**
- 每个工作流有独立的状态和生命周期
- 支持并发执行
- 可以暂停/恢复/取消
- 统一管理所有工作流

---

## 常见使用模式

### 1. 基础：创建多条工作流

```python
from lightagent.workflow import WorkflowManager

manager = WorkflowManager(agent=agent)

# 创建多个工作流
workflows = []
for i in range(5):
    wf = await manager.create_workflow(
        workflow_type="research",
        goal=f"研究主题 {i+1}"
    )
    workflows.append(wf)

# 并发执行所有工作流
for wf in workflows:
    await manager.start_workflow(wf.workflow_id)
```

---

### 2. 管理：查询和控制

```python
# 查询特定工作流
workflow = await manager.get_workflow(workflow_id)
print(f"状态: {workflow.status}")
print(f"进度: {workflow.get_progress()}%")

# 列出所有工作流
all_workflows = await manager.list_workflows()
for wf in all_workflows:
    print(f"{wf.workflow_id}: {wf.status}")

# 按状态过滤
running = await manager.list_workflows(status="running")
failed = await manager.list_workflows(status="failed")
```

---

### 3. 生命周期控制

```python
# 启动（阻塞等待完成）
await manager.start_workflow(workflow_id, block=True)

# 启动（非阻塞）
await manager.start_workflow(workflow_id, block=False)

# 暂停
await manager.pause_workflow(workflow_id)

# 恢复
await manager.resume_workflow(workflow_id)

# 取消
await manager.cancel_workflow(workflow_id)

# 等待完成
result = await manager.wait_for_completion(workflow_id, timeout=300)
```

---

### 4. 批量操作

```python
# 批量创建
workflow_ids = []
for goal in goals:
    wf = await manager.create_workflow("research", goal)
    workflow_ids.append(wf.workflow_id)

# 批量启动
await manager.start_workflows(workflow_ids)

# 批量等待
results = await manager.wait_for_all(workflow_ids)

# 批量取消
await manager.cancel_workflows(workflow_ids)
```

---

### 5. 模板化工作流

```python
# 使用预定义模板
workflow = await manager.create_from_template(
    template_name="code_review",
    goal="审查 agent.py",
    context={
        "file_path": "src/agent.py",
        "focus_areas": ["性能", "安全"]
    }
)

await manager.start_workflow(workflow.workflow_id)
```

---

### 6. 事件监听

```python
# 监听工作流事件
@manager.on_workflow_started
async def handle_start(workflow_id: str):
    print(f"工作流 {workflow_id} 已启动")

@manager.on_task_completed
async def handle_task_complete(workflow_id: str, task_id: str):
    print(f"任务 {task_id} 已完成")

@manager.on_workflow_completed
async def handle_complete(workflow_id: str, result: dict):
    print(f"工作流完成: {result}")
```

---

## 实际应用场景

### 场景 1：CI/CD 流水线

```python
async def ci_cd_pipeline():
    manager = WorkflowManager(agent=agent, max_concurrent_workflows=3)

    # 并发执行多个流水线任务
    tasks = {
        "lint": await manager.create_workflow("lint", "代码检查"),
        "test": await manager.create_workflow("test", "运行测试"),
        "build": await manager.create_workflow("build", "构建项目"),
        "scan": await manager.create_workflow("scan", "安全扫描"),
    }

    # 并发启动
    await manager.start_workflows([wf.workflow_id for wf in tasks.values()])

    # 等待测试完成
    test_result = await manager.wait_for_completion(tasks["test"].workflow_id)

    # 如果测试失败，取消后续任务
    if not test_result["success"]:
        await manager.cancel_workflows([
            tasks["build"].workflow_id,
            tasks["scan"].workflow_id
        ])

    # 收集结果
    results = {}
    for name, wf in tasks.items():
        result = await manager.get_workflow(wf.workflow_id)
        results[name] = result

    return results
```

---

### 场景 2：并行研究

```python
async def parallel_research(topics: List[str]):
    manager = WorkflowManager(agent=agent)

    # 为每个主题创建研究工作流
    workflows = []
    for topic in topics:
        wf = await manager.create_workflow(
            workflow_type="research",
            goal=f"深入研究{topic}",
            context={"depth": "comprehensive"}
        )
        workflows.append(wf)

    # 并发执行
    await manager.start_workflows([wf.workflow_id for wf in workflows])

    # 监控进度
    while True:
        completed = sum(
            1 for wf in workflows
            if (await manager.get_workflow(wf.workflow_id)).status == "completed"
        )

        print(f"进度: {completed}/{len(workflows)}")

        if completed == len(workflows):
            break

        await asyncio.sleep(10)

    # 收集结果
    results = []
    for wf in workflows:
        result = await manager.get_workflow(wf.workflow_id)
        results.append({
            "topic": wf.goal,
            "result": result.result
        })

    return results
```

---

### 场景 3：批量处理

```python
async def batch_process_files(file_paths: List[str]):
    manager = WorkflowManager(
        agent=agent,
        max_concurrent_workflows=5  # 限制并发数
    )

    # 为每个文件创建处理工作流
    workflows = []
    for file_path in file_paths:
        wf = await manager.create_workflow(
            workflow_type="file_process",
            goal=f"处理文件 {file_path}",
            context={"file_path": file_path}
        )
        workflows.append(wf)

    # 分批执行（避免过载）
    batch_size = 5
    for i in range(0, len(workflows), batch_size):
        batch = workflows[i:i+batch_size]
        await manager.start_workflows([wf.workflow_id for wf in batch])

        # 等待批次完成
        await manager.wait_for_all([wf.workflow_id for wf in batch])

    return True
```

---

### 场景 4：优先级调度

```python
async def priority_scheduling():
    manager = WorkflowManager(
        agent=agent,
        max_concurrent_workflows=3
    )

    # 创建不同优先级的工作流
    urgent = await manager.create_workflow(
        "urgent",
        "紧急任务",
        priority="critical"
    )

    normal = await manager.create_workflow(
        "normal",
        "普通任务",
        priority="medium"
    )

    # 高优先级任务会优先执行
    await manager.start_workflows([
        urgent.workflow_id,
        normal.workflow_id
    ])
```

---

## API 快速参考

### WorkflowManager

```python
# 创建工作流
await manager.create_workflow(workflow_type, goal, context=None)
await manager.create_from_template(template_name, goal, context=None)

# 执行控制
await manager.start_workflow(workflow_id, block=True)
await manager.start_workflows(workflow_ids)
await manager.pause_workflow(workflow_id)
await manager.resume_workflow(workflow_id)
await manager.cancel_workflow(workflow_id)

# 查询
await manager.get_workflow(workflow_id)
await manager.list_workflows(status=None)
await manager.wait_for_completion(workflow_id, timeout=None)
await manager.wait_for_all(workflow_ids)

# 清理
await manager.cleanup_completed(older_than)
```

### WorkflowInstance

```python
# 属性
workflow.workflow_id      # 唯一标识
workflow.status           # 状态
workflow.goal             # 目标
workflow.created_at       # 创建时间

# 方法
await workflow.start()
await workflow.pause()
await workflow.resume()
await workflow.cancel()
workflow.get_progress()   # 返回进度百分比
```

---

## 与迁移到 lightagent/workflow/ 的关系

### ✅ 多工作流支持与目录位置无关

**重要的是架构改进，不是目录位置：**

| 方面 | 独立包 `lightagent-workflow/` | 合并到 `lightagent/workflow/` |
|------|------------------------------|------------------------------|
| 多工作流支持 | ✅ 完全支持 | ✅ 完全支持 |
| API 便利性 | ✅ 同样便利 | ✅ 同样便利 |
| 导入路径 | `from lightagent_workflow import ...` | `from lightagent.workflow import ...` |
| 安装方式 | `pip install lightagent lightagent-workflow` | `pip install lightagent` |
| 与 Agent 集成 | 需要适配层 | 无缝集成 |

### 结论

**多工作流的便利性来自架构设计（WorkflowManager + WorkflowInstance），与是否放在 `lightagent/workflow/` 无关。**

但合并到 `lightagent/workflow/` 的额外好处：
- 统一的导入体验
- 更简单的安装
- 与其他模块（core, memory, tools）一致的组织方式

---

## 迁移步骤

如果您决定迁移，步骤如下：

### 1. 移动文件
```bash
mv lightagent-workflow/* lightagent/workflow/
```

### 2. 更新导入
```python
# 之前
from lightagent_workflow import WorkflowManager

# 之后
from lightagent.workflow import WorkflowManager
```

### 3. 安装
```bash
# 之前
pip install lightagent lightagent-workflow

# 之后
pip install lightagent  # 一次安装
```

### 4. 代码无需修改（除了导入）
多工作流的使用方式完全一样！
