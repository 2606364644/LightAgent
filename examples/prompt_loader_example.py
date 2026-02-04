"""
文件系统 Prompt 加载示例

展示如何从文件系统加载 prompt 模板，而不是全部存储在代码中。
"""
import asyncio
import sys
from pathlib import Path

# 添加 lightagent-workflow 到路径
sys.path.insert(0, str(Path(__file__).parent.parent / "lightagent-workflow"))

from lightagent import Agent, MockAdapter, ModelConfig
from lightagent_workflow import WorkflowManager
from lightagent_workflow.prompt_loader import create_prompt_loader
from lightagent_workflow.tools import create_default_toolRegistry
from lightagent_workflow import register_default_workflow_types


async def example_1_load_from_files():
    """示例 1: 从文件系统加载 prompt"""
    print("\n" + "="*70)
    print("示例 1: 从文件系统加载 Prompt")
    print("="*70)

    # 创建 agent
    agent = Agent(
        name="agent",
        model_adapter=MockAdapter(config=ModelConfig(model_name="mock"))
    )

    # 创建 prompt loader（从 examples/prompts 目录加载）
    prompt_loader = create_prompt_loader(
        base_path="examples/prompts",
        format="yaml"  # 支持 yaml, json, txt
    )

    print(f"\n已加载的 prompt 模板:")
    available = prompt_loader.list_available_prompts()
    for wf_type, prompts in available.items():
        print(f"  {wf_type}: {', '.join(prompts)}")

    # 创建 tool registry
    tool_registry = create_default_tool_registry()

    # 创建 manager（使用 loader 的 registry）
    manager = WorkflowManager(
        agent=agent,
        prompt_registry=prompt_loader.registry,  # 使用 loader 的 registry
        tool_registry=tool_registry,
        verbose=True
    )

    register_default_workflow_types(manager)

    # 使用文件中的 prompt
    wf = await manager.create_workflow(
        "planning",
        "研究机器学习算法",
        config={
            'prompts': {
                'template_name': 'research_planning'  # 使用 prompts/planning/research.yaml
            }
        }
    )

    print(f"\n工作流将使用 prompts/planning/research.yaml 中的 prompt")


async def example_2_different_formats():
    """示例 2: 使用不同的文件格式"""
    print("\n" + "="*70)
    print("示例 2: 不同的文件格式（YAML/JSON/TXT）")
    print("="*70)

    # YAML 格式
    yaml_loader = create_prompt_loader(
        base_path="examples/prompts",
        format="yaml"
    )
    print(f"\nYAML 格式: {len([p for wf in yaml_loader.list_available_prompts().values() for p in wf])} 个模板")

    # TXT 格式
    txt_loader = create_prompt_loader(
        base_path="examples/prompts",
        format="txt"
    )
    print(f"TXT 格式: {len([p for wf in txt_loader.list_available_prompts().values() for p in wf])} 个模板")


async def example_3_save_new_prompt():
    """示例 3: 保存新的 prompt 到文件"""
    print("\n" + "="*70)
    print("示例 3: 保存新的 Prompt 到文件")
    print("="*70)

    from lightagent_workflow.prompts import WorkflowPromptTemplate
    from lightagent_workflow.prompt_loader import PromptFileLoader, PromptFileConfig

    # 创建新 prompt
    new_prompt = WorkflowPromptTemplate(
        name="my_custom_planning",
        workflow_type="planning",
        system_prompt="你是我的专属规划助手",
        task_prompt="任务: {goal}\n请帮我制定计划",
        variables={"custom_var": "value"}
    )

    # 创建 loader
    loader = PromptFileLoader(
        config=PromptFileConfig(
            base_path=Path("examples/prompts"),
            format="yaml"
        )
    )

    # 保存到文件
    file_path = loader.save_prompt(new_prompt)
    print(f"\n已保存 prompt 到: {file_path}")

    # 重新加载
    loader.load_from_directory()

    # 验证
    template = loader.registry.get_template("my_custom_planning")
    print(f"已加载: {template.name if template else 'None'}")

    # 清理（删除测试文件）
    if file_path.exists():
        file_path.unlink()
        print(f"已清理测试文件")


async def example_4_hot_reload():
    """示例 4: 热重载（文件变化时自动重载）"""
    print("\n" + "="*70)
    print("示例 4: 热重载 - 文件变化时自动更新")
    print("="*70)

    from lightagent_workflow.prompt_loader import PromptFileLoader, PromptFileConfig

    # 创建启用热重载的 loader
    loader = PromptFileLoader(
        config=PromptFileConfig(
            base_path=Path("examples/prompts"),
            format="yaml",
            watch_changes=True  # 启用热重载
        )
    )

    loader.load_from_directory()

    print(f"\n初始加载完成")
    print(f"启用热重载: watch_changes=True")

    # 检查文件变化
    reloaded = loader.reload_if_changed()
    print(f"\n检查文件变化: {reloaded} 个文件已更新")


async def example_5_custom_directory():
    """示例 5: 使用自定义目录"""
    print("\n" + "="*70)
    print("示例 5: 使用自定义 Prompt 目录")
    print("="*70)

    # 项目可以有自定义的 prompt 目录
    custom_loader = create_prompt_loader(
        base_path="my_prompts",  # 自定义目录
        format="yaml"
    )

    print(f"\n自定义目录: my_prompts/")
    print(f"如果目录不存在，会自动创建")


async def example_6_mixed_usage():
    """示例 6: 混合使用（文件 + 代码定义）"""
    print("\n" + "="*70)
    print("示例 6: 混合使用（文件 Prompt + 代码 Prompt）")
    print("="*70)

    from lightagent_workflow.prompts import WorkflowPromptTemplate, WorkflowPromptRegistry

    # 从文件加载
    file_loader = create_prompt_loader(
        base_path="examples/prompts",
        format="yaml"
    )

    # 在代码中定义额外的 prompt
    code_prompt = WorkflowPromptTemplate(
        name="code_defined_prompt",
        workflow_type="planning",
        system_prompt="这是在代码中定义的 prompt",
        task_prompt="任务: {goal}"
    )

    # 注册代码定义的 prompt 到同一个 registry
    file_loader.registry.register_template(code_prompt)

    print(f"\n总 prompt 数: {len(file_loader.registry.templates)}")
    print(f"  - 从文件加载: {len(file_loader.registry.templates) - 1}")
    print(f"  - 代码定义: 1")


async def main():
    """运行所有示例"""
    print("\n" + "="*70)
    print("文件系统 Prompt 加载示例")
    print("="*70)

    await example_1_load_from_files()
    await example_2_different_formats()
    await example_3_save_new_prompt()
    await example_4_hot_reload()
    await example_5_custom_directory()
    await example_6_mixed_usage()

    print("\n" + "="*70)
    print("所有示例运行完成")
    print("="*70)

    print("\n关键要点:")
    print("1. Prompt 存储在文件系统中，不在代码里")
    print("2. 支持 YAML、JSON、TXT 三种格式")
    print("3. 可以按工作流类型组织文件")
    print("4. 支持热重载（文件变化自动更新）")
    print("5. 可以保存新 prompt 到文件")
    print("6. 可以混合使用文件和代码定义的 prompt")


if __name__ == "__main__":
    asyncio.run(main())
