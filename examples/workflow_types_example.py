"""
多工作流类型系统使用示例

展示如何使用不同的工作流类型处理各种任务
"""
import asyncio
from pathlib import Path
import sys

# 添加 lightagent-workflow 到路径
sys.path.insert(0, str(Path(__file__).parent.parent / "lightagent-workflow"))

from lightagent import Agent, MockAdapter, ModelConfig
from lightagent_workflow import (
    WorkflowManager,
    create_workflow_manager,
    PlanningWorkflow,
    SequentialWorkflow,
    InteractiveWorkflow,
    CodeExecuteRefineWorkflow,
    HumanInTheLoopWorkflow,
    register_default_workflow_types
)


async def example_planning_workflow():
    """示例 1: Planning Workflow（任务分解型）"""
    print("\n" + "="*70)
    print("示例 1: Planning Workflow - 任务分解并执行")
    print("="*70)

    # 创建 agent
    agent = Agent(
        name="planning-agent",
        model_adapter=MockAdapter(config=ModelConfig(model_name="mock"))
    )

    # 创建管理器
    manager = await create_workflow_manager(agent=agent, verbose=True)

    # 注册默认工作流类型
    register_default_workflow_types(manager)

    # 创建 Planning Workflow
    workflow = await manager.create_workflow(
        workflow_type="planning",
        goal="研究并实现一个向量数据库系统",
        config={
            'max_recursion_depth': 3,
            'execution_mode': 'sequential',
            'auto_refine': True
        }
    )

    # 执行工作流
    result = await manager.start_workflow(
        workflow.workflow_id,
        goal="研究并实现一个向量数据库系统"
    )

    print(f"\n结果: {result}")


async def example_sequential_workflow():
    """示例 2: Sequential Workflow（固定步骤型）"""
    print("\n" + "="*70)
    print("示例 2: Sequential Workflow - 固定步骤序列")
    print("="*70)

    # 创建 agent
    agent = Agent(
        name="sequential-agent",
        model_adapter=MockAdapter(config=ModelConfig(model_name="mock"))
    )

    # 创建管理器
    manager = await create_workflow_manager(agent=agent, verbose=True)
    register_default_workflow_types(manager)

    # 创建 Sequential Workflow
    workflow = await manager.create_workflow(
        workflow_type="sequential",
        goal="CI/CD 流水线",
        config={
            'steps': [
                {
                    'name': '代码检查',
                    'action': 'run_linter',
                    'description': '运行代码风格检查',
                    'stop_on_failure': True
                },
                {
                    'name': '运行测试',
                    'action': 'run_tests',
                    'description': '运行单元测试',
                    'stop_on_failure': True
                },
                {
                    'name': '构建项目',
                    'action': 'build_project',
                    'description': '构建生产版本',
                    'stop_on_failure': False
                },
                {
                    'name': '部署',
                    'action': 'deploy',
                    'description': '部署到服务器',
                    'stop_on_failure': False
                }
            ],
            'stop_on_first_failure': True
        }
    )

    # 执行工作流
    result = await manager.start_workflow(
        workflow.workflow_id,
        goal="CI/CD 流水线"
    )

    print(f"\n结果: {result}")


async def example_interactive_workflow():
    """示例 3: Interactive Workflow（多轮对话型）"""
    print("\n" + "="*70)
    print("示例 3: Interactive Workflow - 多轮对话")
    print("="*70)

    # 创建 agent
    agent = Agent(
        name="interactive-agent",
        model_adapter=MockAdapter(config=ModelConfig(model_name="mock"))
    )

    # 创建管理器
    manager = await create_workflow_manager(agent=agent, verbose=True)
    register_default_workflow_types(manager)

    # 创建 Interactive Workflow
    workflow = await manager.create_workflow(
        workflow_type="interactive",
        goal="客户服务对话",
        config={
            'max_rounds': 5,
            'system_prompt': '你是一个友好的客户服务助手'
        }
    )

    # 执行工作流
    result = await manager.start_workflow(
        workflow.workflow_id,
        goal="你好，我需要帮助"
    )

    print(f"\n对话轮数: {result['total_rounds']}")
    print(f"完成状态: {result['completed']}")


async def example_code_execute_refine_workflow():
    """示例 4: Code-Execute-Refine Workflow（代码执行反馈型）"""
    print("\n" + "="*70)
    print("示例 4: Code-Execute-Refine Workflow - 代码生成和迭代")
    print("="*70)

    # 创建 agent
    agent = Agent(
        name="code-agent",
        model_adapter=MockAdapter(config=ModelConfig(model_name="mock"))
    )

    # 创建管理器
    manager = await create_workflow_manager(agent=agent, verbose=True)
    register_default_workflow_types(manager)

    # 创建 Code-Execute-Refine Workflow
    workflow = await manager.create_workflow(
        workflow_type="code_execute_refine",
        goal="编写一个 Python 函数计算斐波那契数列",
        config={
            'max_iterations': 5,
            'language': 'python'
        }
    )

    # 执行工作流
    result = await manager.start_workflow(
        workflow.workflow_id,
        goal="编写一个 Python 函数计算斐波那契数列"
    )

    print(f"\n迭代次数: {result['iterations']}")
    print(f"最终状态: {result['status']}")


async def example_human_in_loop_workflow():
    """示例 5: Human-in-the-Loop Workflow（人工审批型）"""
    print("\n" + "="*70)
    print("示例 5: Human-in-the-Loop Workflow - 人工审批")
    print("="*70)

    # 创建 agent
    agent = Agent(
        name="human-loop-agent",
        model_adapter=MockAdapter(config=ModelConfig(model_name="mock"))
    )

    # 创建管理器
    manager = await create_workflow_manager(agent=agent, verbose=True)
    register_default_workflow_types(manager)

    # 创建 Human-in-the-Loop Workflow
    workflow = await manager.create_workflow(
        workflow_type="human_loop",
        goal="审查并修改代码",
        config={
            'max_iterations': 10,
            'auto_approve_safe_actions': False
        }
    )

    # 设置自定义审批处理器
    async def custom_approval_requester(proposal, context):
        """自定义审批请求处理器"""
        print(f"\n需要审批的操作:")
        print(f"  类型: {proposal.action_type}")
        print(f"  描述: {proposal.description}")
        # 在实际应用中，这里会等待人工输入
        # 示例中自动批准
        from lightagent_workflow.types.human_loop import ApprovalResult
        return ApprovalResult(approved=True, feedback=None)

    workflow.approval_requester = custom_approval_requester

    # 执行工作流
    result = await manager.start_workflow(
        workflow.workflow_id,
        goal="审查并修改代码"
    )

    print(f"\n提案总数: {result['total_proposals']}")
    print(f"批准: {result['approved']}")
    print(f"拒绝: {result['rejected']}")


async def example_multiple_workflows():
    """示例 6: 多工作流并发执行"""
    print("\n" + "="*70)
    print("示例 6: 多工作流并发执行")
    print("="*70)

    # 创建 agent
    agent = Agent(
        name="multi-workflow-agent",
        model_adapter=MockAdapter(config=ModelConfig(model_name="mock"))
    )

    # 创建管理器
    manager = await create_workflow_manager(
        agent=agent,
        max_concurrent_workflows=5,
        verbose=True
    )
    register_default_workflow_types(manager)

    # 创建多个不同类型的工作流
    workflows = []

    # Planning Workflow
    wf1 = await manager.create_workflow(
        "planning",
        "研究主题 A"
    )
    workflows.append(('planning', wf1.workflow_id, "研究主题 A"))

    # Sequential Workflow
    wf2 = await manager.create_workflow(
        "sequential",
        "数据处理流程",
        config={
            'steps': [
                {'name': '提取', 'action': 'extract'},
                {'name': '转换', 'action': 'transform'},
                {'name': '加载', 'action': 'load'}
            ]
        }
    )
    workflows.append(('sequential', wf2.workflow_id, "数据处理流程"))

    # Interactive Workflow
    wf3 = await manager.create_workflow(
        "interactive",
        "客户咨询"
    )
    workflows.append(('interactive', wf3.workflow_id, "客户咨询"))

    # 并发启动所有工作流
    print(f"\n并发启动 {len(workflows)} 个工作流...")

    tasks = []
    for wf_type, wf_id, goal in workflows:
        task = asyncio.create_task(
            manager.start_workflow(wf_id, goal)
        )
        tasks.append((wf_type, wf_id, task))

    # 等待所有工作流完成
    results = []
    for wf_type, wf_id, task in tasks:
        try:
            result = await task
            results.append((wf_type, wf_id, result))
            print(f"\n{wf_type} 工作流完成")
        except Exception as e:
            print(f"\n{wf_type} 工作流失败: {e}")

    print(f"\n完成的工作流数量: {len(results)}")


async def example_workflow_control():
    """示例 7: 工作流生命周期控制"""
    print("\n" + "="*70)
    print("示例 7: 工作流生命周期控制（暂停/恢复/取消）")
    print("="*70)

    # 创建 agent
    agent = Agent(
        name="control-agent",
        model_adapter=MockAdapter(config=ModelConfig(model_name="mock"))
    )

    # 创建管理器
    manager = await create_workflow_manager(agent=agent, verbose=True)
    register_default_workflow_types(manager)

    # 创建长时间运行的工作流
    workflow = await manager.create_workflow(
        "planning",
        "复杂的研究任务",
        config={'max_recursion_depth': 5}
    )

    # 非阻塞启动
    await manager.start_workflow(
        workflow.workflow_id,
        "复杂的研究任务",
        block=False
    )

    # 查询状态
    status = await manager.get_workflow(workflow.workflow_id)
    print(f"\n工作流状态: {status.status}")
    print(f"进度: {status.get_progress():.1f}%")

    # 暂停工作流
    await manager.pause_workflow(workflow.workflow_id)
    print(f"\n已暂停工作流")

    # 恢复工作流
    await manager.resume_workflow(workflow.workflow_id)
    print(f"已恢复工作流")

    # 取消工作流
    # await manager.cancel_workflow(workflow.workflow_id)
    # print(f"已取消工作流")

    # 等待完成
    result = await manager.wait_for_completion(workflow.workflow_id)
    print(f"\n工作流完成: {result['success']}")


async def example_list_and_filter():
    """示例 8: 列出和过滤工作流"""
    print("\n" + "="*70)
    print("示例 8: 列出和过滤工作流")
    print("="*70)

    # 创建 agent
    agent = Agent(
        name="list-agent",
        model_adapter=MockAdapter(config=ModelConfig(model_name="mock"))
    )

    # 创建管理器
    manager = await create_workflow_manager(agent=agent, verbose=False)
    register_default_workflow_types(manager)

    # 创建多个工作流
    for i in range(5):
        await manager.create_workflow(
            "planning",
            f"任务 {i+1}"
        )

    # 列出所有工作流
    all_workflows = await manager.list_workflows()
    print(f"\n总工作流数: {len(all_workflows)}")

    # 按状态过滤
    pending = await manager.list_workflows(status="pending")
    print(f"待执行: {len(pending)}")

    # 按类型过滤
    planning = await manager.list_workflows(workflow_type="planning")
    print(f"Planning 类型: {len(planning)}")


async def main():
    """运行所有示例"""
    print("\n" + "="*70)
    print("多工作流类型系统示例")
    print("="*70)

    # 运行示例（可以注释掉不需要的）
    await example_planning_workflow()
    # await example_sequential_workflow()
    # await example_interactive_workflow()
    # await example_code_execute_refine_workflow()
    # await example_human_in_loop_workflow()
    # await example_multiple_workflows()
    # await example_workflow_control()
    # await example_list_and_filter()

    print("\n" + "="*70)
    print("所有示例运行完成")
    print("="*70)


if __name__ == "__main__":
    asyncio.run(main())
