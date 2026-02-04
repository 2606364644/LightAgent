"""
多工作流并发执行示例

展示如何在新架构下方便地使用多条工作流
"""
import asyncio
from lightagent import Agent
from lightagent.workflow import WorkflowManager, WorkflowTemplate


async def example_basic_multi_workflow():
    """基础：创建并执行多条工作流"""
    # 创建管理器（只需一次）
    manager = WorkflowManager(agent=agent)

    # ✅ 创建多个独立工作流实例
    workflow1 = await manager.create_workflow(
        workflow_type="research",
        goal="研究Python异步编程的最佳实践"
    )

    workflow2 = await manager.create_workflow(
        workflow_type="code_review",
        goal="审查 src/agent.py 的代码质量"
    )

    workflow3 = await manager.create_workflow(
        workflow_type="testing",
        goal="运行完整的测试套件"
    )

    # ✅ 并发执行（不会互相干扰）
    results = await asyncio.gather(
        manager.start_workflow(workflow1.workflow_id),
        manager.start_workflow(workflow2.workflow_id),
        manager.start_workflow(workflow3.workflow_id)
    )

    print(f"工作流1结果: {results[0]}")
    print(f"工作流2结果: {results[1]}")
    print(f"工作流3结果: {results[2]}")


async def example_with_control():
    """进阶：控制工作流生命周期"""
    manager = WorkflowManager(agent=agent)

    # 创建工作流
    workflow = await manager.create_workflow(
        workflow_type="long_task",
        goal="执行长时间运行的任务"
    )

    # 启动（非阻塞）
    await manager.start_workflow(workflow.workflow_id, block=False)

    # ✅ 查询状态
    status = await manager.get_workflow(workflow.workflow_id)
    print(f"进度: {status.get_progress()}%")
    print(f"状态: {status.status}")

    # ✅ 暂停工作流
    await manager.pause_workflow(workflow.workflow_id)

    # ✅ 恢复工作流
    await manager.resume_workflow(workflow.workflow_id)

    # ✅ 等待完成
    result = await manager.wait_for_completion(workflow.workflow_id)


async def example_list_and_filter():
    """管理：列出和过滤工作流"""
    manager = WorkflowManager(agent=agent)

    # 创建多个工作流
    for i in range(5):
        await manager.create_workflow(
            workflow_type="test",
            goal=f"测试任务 {i+1}"
        )

    # ✅ 查询所有工作流
    all_workflows = await manager.list_workflows()
    print(f"总工作流数: {len(all_workflows)}")

    # ✅ 按状态过滤
    running = await manager.list_workflows(status="running")
    completed = await manager.list_workflows(status="completed")
    print(f"运行中: {len(running)}, 已完成: {len(completed)}")

    # ✅ 清理已完成的工作流
    await manager.cleanup_completed(older_than=3600)  # 1小时前


async def example_template_based():
    """便利：使用工作流模板"""
    manager = WorkflowManager(agent=agent)

    # ✅ 使用预定义模板快速创建工作流

    # 方式1：通过模板名称
    workflow1 = await manager.create_from_template(
        template_name="code_review",
        goal="审查 agent.py",
        context={"file_path": "src/agent.py"}
    )

    # 方式2：直接使用模板对象
    template = WorkflowTemplate(
        name="custom_workflow",
        description="自定义工作流",
        config={"max_parallel_tasks": 5}
    )
    workflow2 = await template.create_instance(
        manager=manager,
        goal="自定义任务"
    )

    # 执行
    await manager.start_workflow(workflow1.workflow_id)


async def example_callbacks():
    """事件：监听工作流事件"""
    manager = WorkflowManager(agent=agent)

    # ✅ 注册事件回调
    @manager.on_workflow_started
    async def on_start(workflow_id: str):
        print(f"工作流 {workflow_id} 已启动")

    @manager.on_task_completed
    async def on_task_complete(workflow_id: str, task_id: str):
        print(f"工作流 {workflow_id} 的任务 {task_id} 已完成")

    @manager.on_workflow_completed
    async def on_complete(workflow_id: str, result: dict):
        print(f"工作流 {workflow_id} 已完成: {result}")

    # 创建并执行
    workflow = await manager.create_workflow("test", "测试")
    await manager.start_workflow(workflow.workflow_id)


async def example_batch_operations():
    """批量：批量操作工作流"""
    manager = WorkflowManager(agent=agent)

    # 批量创建
    goals = [
        "研究主题1",
        "研究主题2",
        "研究主题3",
        "研究主题4",
        "研究主题5"
    ]

    workflows = []
    for goal in goals:
        wf = await manager.create_workflow("research", goal)
        workflows.append(wf)

    # ✅ 批量启动
    workflow_ids = [wf.workflow_id for wf in workflows]
    await manager.start_workflows(workflow_ids)

    # ✅ 批量等待
    results = await manager.wait_for_all(workflow_ids)

    # ✅ 批量取消
    # await manager.cancel_workflows(workflow_ids)


async def example_priority_scheduling():
    """优先级：按优先级调度工作流"""
    manager = WorkflowManager(
        agent=agent,
        max_concurrent_workflows=3  # 限制并发数
    )

    # 创建不同优先级的工作流
    urgent = await manager.create_workflow(
        "urgent_task",
        "紧急任务",
        priority="high"
    )

    normal = await manager.create_workflow(
        "normal_task",
        "普通任务",
        priority="medium"
    )

    low = await manager.create_workflow(
        "low_task",
        "低优先级任务",
        priority="low"
    )

    # ✅ 按优先级智能调度
    # high 优先执行，low 可能需要等待
    await manager.start_workflows([
        urgent.workflow_id,
        normal.workflow_id,
        low.workflow_id
    ])


# 实际应用场景
async def real_world_example_ci_cd():
    """真实场景：CI/CD 流水线"""
    manager = WorkflowManager(agent=agent)

    # 并发执行多个独立的流水线任务
    workflows = {
        "lint": await manager.create_workflow("lint", "代码风格检查"),
        "test": await manager.create_workflow("test", "运行单元测试"),
        "build": await manager.create_workflow("build", "构建项目"),
        "security": await manager.create_workflow("security", "安全扫描"),
    }

    # 并发启动
    await manager.start_workflows(list(workflows.values()))

    # 等待关键任务
    await manager.wait_for_completion(workflows["test"].workflow_id)

    # 如果测试失败，取消其他任务
    test_result = await manager.get_workflow(workflows["test"].workflow_id)
    if not test_result.success:
        await manager.cancel_workflows([
            workflows["build"].workflow_id,
            workflows["security"].workflow_id
        ])
        print("测试失败，已取消后续任务")


async def real_world_example_research():
    """真实场景：并行研究多个主题"""
    manager = WorkflowManager(agent=agent)

    topics = [
        "Python异步编程",
        "LLM Agent架构",
        "向量数据库",
        "RAG系统设计"
    ]

    # 并发研究多个主题
    workflows = []
    for topic in topics:
        wf = await manager.create_workflow(
            workflow_type="research",
            goal=f"深入研究{topic}"
        )
        workflows.append(wf)

    # 并发执行
    await manager.start_workflows([wf.workflow_id for wf in workflows])

    # 监控进度
    while True:
        completed = 0
        for wf in workflows:
            status = await manager.get_workflow(wf.workflow_id)
            if status.status == "completed":
                completed += 1
                print(f"{wf.goal}: 已完成")

        if completed == len(workflows):
            break

        await asyncio.sleep(5)


# 运行示例
if __name__ == "__main__":
    # 初始化 Agent
    agent = Agent(...)

    # 选择要运行的示例
    asyncio.run(example_basic_multi_workflow())
    # asyncio.run(example_with_control())
    # asyncio.run(example_list_and_filter())
    # asyncio.run(example_template_based())
    # asyncio.run(example_callbacks())
    # asyncio.run(example_batch_operations())
    # asyncio.run(example_priority_scheduling())
