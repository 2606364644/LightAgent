"""
工作流 Prompt 和工具复用示例

展示如何：
1. 为不同工作流配置自定义 prompt
2. 设置全局工具池和工作流特定工具
3. 实现工具在不同工作流间的复用
"""
import asyncio
import sys
from pathlib import Path

# 添加 lightagent-workflow 到路径
sys.path.insert(0, str(Path(__file__).parent.parent / "lightagent-workflow"))

from lightagent import Agent, MockAdapter, ModelConfig
from lightagent.tools import FunctionBuilder
from lightagent_workflow import (
    WorkflowManager,
    create_default_prompt_registry,
    create_default_tool_registry
)
from lightagent_workflow.prompts import WorkflowPromptTemplate, WorkflowPromptRegistry
from lightagent_workflow.config import (
    ExtendedWorkflowConfig,
    WorkflowPromptConfig,
    WorkflowToolConfig
)


# ==================== 定义工具 ====================

def search_web(query: str) -> str:
    """搜索网络（模拟）"""
    return f"搜索结果: 关于'{query}'找到了5篇文章"


def analyze_data(data: str) -> dict:
    """分析数据"""
    return {
        "length": len(data),
        "words": len(data.split()),
        "summary": data[:50] + "..." if len(data) > 50 else data
    }


def calculate(expression: str) -> float:
    """计算表达式"""
    try:
        return eval(expression)
    except:
        return 0.0


def generate_code(requirement: str, language: str = "python") -> str:
    """生成代码"""
    return f"# {language} 代码\n# 实现: {requirement}\nprint('Hello World')"


def review_code(code: str) -> dict:
    """审查代码"""
    return {
        "issues": [],
        "suggestions": ["添加注释", "处理错误"],
        "score": 8.5
    }


# 创建工具实例
search_tool = FunctionBuilder.create_tool(search_web)
analyze_tool = FunctionBuilder.create_tool(analyze_data)
calc_tool = FunctionBuilder.create_tool(calculate)
code_gen_tool = FunctionBuilder.create_tool(generate_code)
code_review_tool = FunctionBuilder.create_tool(review_code)


async def example_1_global_tools():
    """示例 1: 全局工具 - 所有工作流都能使用"""
    print("\n" + "="*70)
    print("示例 1: 全局工具池")
    print("="*70)

    # 创建 agent
    agent = Agent(
        name="agent",
        model_adapter=MockAdapter(config=ModelConfig(model_name="mock"))
    )

    # 创建 registries
    prompt_registry = create_default_prompt_registry()
    tool_registry = create_default_tool_registry()

    # 添加全局工具（所有工作流都能使用）
    tool_registry.add_global_tool(search_tool)
    tool_registry.add_global_tool(analyze_tool)

    print(f"\n全局工具: {tool_registry.list_global_tools()}")

    # 创建管理器
    manager = WorkflowManager(
        agent=agent,
        prompt_registry=prompt_registry,
        tool_registry=tool_registry,
        verbose=True
    )

    # 注册工作流类型
    from lightagent_workflow import register_default_workflow_types
    register_default_workflow_types(manager)

    # 创建两个不同类型的工作流
    wf1 = await manager.create_workflow("planning", "研究AI")
    wf2 = await manager.create_workflow("sequential", "数据处理")

    # 两个工作流都能访问全局工具
    print(f"\nPlanning 工作流工具: {wf1.list_tools()}")
    print(f"Sequential 工作流工具: {wf2.list_tools()}")

    # 验证：两个工作流都有 search 和 analyze 工具
    assert "search_web" in wf1.list_tools()
    assert "analyze_data" in wf1.list_tools()
    assert "search_web" in wf2.list_tools()
    assert "analyze_data" in wf2.list_tools()


async def example_2_workflow_specific_tools():
    """示例 2: 工作流特定工具"""
    print("\n" + "="*70)
    print("示例 2: 工作流特定工具")
    print("="*70)

    agent = Agent(
        name="agent",
        model_adapter=MockAdapter(config=ModelConfig(model_name="mock"))
    )

    prompt_registry = create_default_prompt_registry()
    tool_registry = create_default_tool_registry()

    # 全局工具
    tool_registry.add_global_tool(analyze_tool)

    # 为 planning 工作流添加特定工具
    tool_registry.add_workflow_tool("planning", calc_tool)
    print(f"\n添加 calc_tool 到 planning 工作流")

    # 为 code_execute_refine 工作流添加特定工具
    tool_registry.add_workflow_tool("code_execute_refine", code_gen_tool)
    tool_registry.add_workflow_tool("code_execute_refine", code_review_tool)
    print(f"添加 code_gen_tool 和 code_review_tool 到 code_execute_refine 工作流")

    manager = WorkflowManager(
        agent=agent,
        prompt_registry=prompt_registry,
        tool_registry=tool_registry,
        verbose=True
    )

    from lightagent_workflow import register_default_workflow_types
    register_default_workflow_types(manager)

    # 创建不同类型的工作流
    planning_wf = await manager.create_workflow("planning", "研究计划")
    code_wf = await manager.create_workflow("code_execute_refine", "生成代码")
    sequential_wf = await manager.create_workflow("sequential", "数据流")

    # 查看每个工作流的工具
    print(f"\nPlanning 工作流工具: {planning_wf.list_tools()}")
    print(f"  - 全局工具: analyze_data")
    print(f"  - 类型工具: calculate")

    print(f"\nCode-Execute 工作流工具: {code_wf.list_tools()}")
    print(f"  - 全局工具: analyze_data")
    print(f"  - 类型工具: generate_code, review_code")

    print(f"\nSequential 工作流工具: {sequential_wf.list_tools()}")
    print(f"  - 全局工具: analyze_data")
    print(f"  - 类型工具: (无)")


async def example_3_instance_tools():
    """示例 3: 实例特定工具"""
    print("\n" + "="*70)
    print("示例 3: 实例特定工具（不影响其他实例）")
    print("="*70)

    agent = Agent(
        name="agent",
        model_adapter=MockAdapter(config=ModelConfig(model_name="mock"))
    )

    prompt_registry = create_default_prompt_registry()
    tool_registry = create_default_tool_registry()

    # 全局工具
    tool_registry.add_global_tool(search_tool)

    manager = WorkflowManager(
        agent=agent,
        prompt_registry=prompt_registry,
        tool_registry=tool_registry,
        verbose=True
    )

    from lightagent_workflow import register_default_workflow_types
    register_default_workflow_types(manager)

    # 创建两个相同类型的工作流
    wf1 = await manager.create_workflow("planning", "研究AI")
    wf2 = await manager.create_workflow("planning", "研究生物")

    print(f"\nWF1 初始工具: {wf1.list_tools()}")
    print(f"WF2 初始工具: {wf2.list_tools()}")

    # 为 wf1 添加实例特定工具
    def ai_analyzer(topic: str) -> str:
        return f"AI分析: {topic}"

    ai_tool = FunctionBuilder.create_tool(ai_analyzer)
    wf1.add_tool(ai_tool)

    print(f"\n为 WF1 添加 ai_analyzer 工具后:")
    print(f"WF1 工具: {wf1.list_tools()}")
    print(f"WF2 工具: {wf2.list_tools()}")

    # 验证：wf1 有新工具，wf2 没有
    assert "ai_analyzer" in wf1.list_tools()
    assert "ai_analyzer" not in wf2.list_tools()


async def example_4_custom_prompts():
    """示例 4: 自定义 Prompt"""
    print("\n" + "="*70)
    print("示例 4: 自定义 Prompt 模板")
    print("="*70)

    agent = Agent(
        name="agent",
        model_adapter=MockAdapter(config=ModelConfig(model_name="mock"))
    )

    # 创建 prompt registry
    prompt_registry = create_default_prompt_registry()

    # 添加自定义 prompt
    research_prompt = WorkflowPromptTemplate(
        name="research_planning",
        workflow_type="planning",
        system_prompt="你是专业的研究规划助手。你的任务是制定详细、可行的研究计划。",
        task_prompt="""研究目标: {goal}

背景: {context}

请制定详细的研究计划，包括:
1. 研究阶段划分
2. 每个阶段的具体任务
3. 时间估算
4. 所需资源

格式: 分步骤列表"""
    )
    prompt_registry.register_template(research_prompt)

    tool_registry = create_default_tool_registry()
    tool_registry.add_global_tool(search_tool)

    manager = WorkflowManager(
        agent=agent,
        prompt_registry=prompt_registry,
        tool_registry=tool_registry,
        verbose=True
    )

    from lightagent_workflow import register_default_workflow_types
    register_default_workflow_types(manager)

    # 创建配置，使用自定义 prompt
    config = ExtendedWorkflowConfig(
        workflow_type="planning",
        prompts=WorkflowPromptConfig(
            template_name="research_planning",  # 使用自定义模板
            variables={"default_duration": "4周"}
        )
    )

    # 创建工作流
    wf = await manager.create_workflow(
        "planning",
        "研究大语言模型的优化方法",
        config=config.dict()
    )

    print(f"\n工作流将使用自定义的 research_planning prompt")
    print(f"Prompt 变量: {config.prompts.variables}")


async def example_5_tool_reuse():
    """示例 5: 工具在多个工作流类型间复用"""
    print("\n" + "="*70)
    print("示例 5: 工具复用 - 一个工具用于多个工作流类型")
    print("="*70)

    agent = Agent(
        name="agent",
        model_adapter=MockAdapter(config=ModelConfig(model_name="mock"))
    )

    prompt_registry = create_default_prompt_registry()
    tool_registry = create_default_tool_registry()

    # analyze_data 工具会被多个工作流类型使用
    tool_registry.add_global_tool(analyze_tool)

    # 为多个工作流类型添加相同的工具
    tool_registry.register_tool_for_workflows(
        tool=search_tool,
        workflow_types=["planning", "sequential", "interactive"]
    )

    print(f"\n为 planning, sequential, interactive 三个工作流类型都添加了 search_tool")

    manager = WorkflowManager(
        agent=agent,
        prompt_registry=prompt_registry,
        tool_registry=tool_registry,
        verbose=True
    )

    from lightagent_workflow import register_default_workflow_types
    register_default_workflow_types(manager)

    # 创建不同类型的工作流
    wf1 = await manager.create_workflow("planning", "研究")
    wf2 = await manager.create_workflow("sequential", "流程")
    wf3 = await manager.create_workflow("interactive", "对话")

    # 所有工作流都有 analyze_data 和 search_web
    print(f"\nPlanning 工具: {wf1.list_tools()}")
    print(f"Sequential 工具: {wf2.list_tools()}")
    print(f"Interactive 工具: {wf3.list_tools()}")

    # 验证工具复用
    for wf in [wf1, wf2, wf3]:
        assert "analyze_data" in wf.list_tools()
        assert "search_web" in wf.list_tools()


async def example_6_combined():
    """示例 6: 综合示例 - Prompt + 工具 + 复用"""
    print("\n" + "="*70)
    print("示例 6: 综合示例")
    print("="*70)

    agent = Agent(
        name="agent",
        model_adapter=MockAdapter(config=ModelConfig(model_name="mock"))
    )

    # ========== Prompt 配置 ==========
    prompt_registry = create_default_prompt_registry()

    # 自定义研究 prompt
    research_prompt = WorkflowPromptTemplate(
        name="custom_research",
        workflow_type="planning",
        system_prompt="你是AI研究专家",
        task_prompt="研究: {goal}"
    )
    prompt_registry.register_template(research_prompt)

    # ========== 工具配置 ==========
    tool_registry = create_default_tool_registry()

    # 全局工具
    tool_registry.add_global_tool(search_tool)
    tool_registry.add_global_tool(analyze_tool)

    # Planning 工作流特定工具
    tool_registry.add_workflow_tool("planning", calc_tool)

    # Code 工作流特定工具
    tool_registry.add_workflow_tool("code_execute_refine", code_gen_tool)

    print(f"\n配置完成:")
    print(f"  - Prompt 模板: {len(prompt_registry.list_templates())}")
    print(f"  - 全局工具: {tool_registry.list_global_tools()}")
    print(f"  - Planning工具: {tool_registry.list_workflow_tools('planning')}")
    print(f"  - Code工具: {tool_registry.list_workflow_tools('code_execute_refine')}")

    # ========== 创建管理器 ==========
    manager = WorkflowManager(
        agent=agent,
        prompt_registry=prompt_registry,
        tool_registry=tool_registry,
        verbose=True
    )

    from lightagent_workflow import register_default_workflow_types
    register_default_workflow_types(manager)

    # ========== 创建工作流 ==========
    config = ExtendedWorkflowConfig(
        workflow_type="planning",
        prompts=WorkflowPromptConfig(
            template_name="custom_research"
        )
    )

    wf = await manager.create_workflow(
        "planning",
        "研究深度学习",
        config=config.dict()
    )

    print(f"\n工作流配置:")
    print(f"  - 类型: {wf.workflow_type}")
    print(f"  - Prompt模板: custom_research")
    print(f"  - 可用工具: {wf.list_tools()}")
    print(f"    * 全局: search_web, analyze_data")
    print(f"    * 类型: calculate")


async def main():
    """运行所有示例"""
    print("\n" + "="*70)
    print("工作流 Prompt 和工具复用示例")
    print("="*70)

    await example_1_global_tools()
    await example_2_workflow_specific_tools()
    await example_3_instance_tools()
    await example_4_custom_prompts()
    await example_5_tool_reuse()
    await example_6_combined()

    print("\n" + "="*70)
    print("所有示例运行完成")
    print("="*70)
    print("\n关键要点:")
    print("1. 全局工具: 所有工作流都能使用")
    print("2. 工作流特定工具: 只供特定类型的工作流使用")
    print("3. 实例工具: 只供特定实例使用")
    print("4. Prompt 模板: 每个工作流可以有自己的 prompt")
    print("5. 工具复用: 工具可以在多个工作流类型间共享")


if __name__ == "__main__":
    asyncio.run(main())
