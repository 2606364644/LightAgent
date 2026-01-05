"""
Advanced Workflow Example

Demonstrates planning, file system tools, and complex workflows
"""
import asyncio
from lightagent.workflow import (
    create_workflow_engine,
    create_planner,
    create_executor,
    TaskGraph,
    Task,
    FileToolConfig,
    SafePathConfig
)
from lightagent.core.agent import Agent
from lightagent.models.providers import OpenAIAdapter


async def planning_workflow_example():
    """Example of planning and task execution"""

    print("=" * 60)
    print("Planning Workflow Example")
    print("=" * 60)

    # Create a simple planner
    planner = create_planner(planner_type='simple')

    # Plan a goal
    goal = "Build a simple REST API"
    plan = await planner.plan(goal)

    print(f"\nGoal: {goal}")
    print(f"Plan created with {len(plan)} tasks:")
    for i, task in enumerate(plan):
        print(f"\n  {i+1}. {task.get('name')}")
        print(f"     Description: {task.get('description')[:100]}...")
        print(f"     Priority: {task.get('priority')}")
        print(f"     Dependencies: {task.get('dependencies')}")


async def task_graph_example():
    """Example of using task graphs"""

    print("\n" + "=" * 60)
    print("Task Graph Example")
    print("=" * 60)

    # Create a task graph
    graph = TaskGraph()

    # Add tasks with dependencies
    task1 = Task(name="Design database schema", description="Design the database", priority="high")
    task2 = Task(name="Create models", description="Create ORM models", priority="high")
    task3 = Task(name="Build API endpoints", description="Create REST endpoints", priority="medium")
    task4 = Task(name="Write tests", description="Add unit tests", priority="medium")
    task5 = Task(name="Deploy", description="Deploy to production", priority="low")

    graph.add_task(task1)
    graph.add_task(task2)
    graph.add_task(task3)
    graph.add_task(task4)
    graph.add_task(task5)

    # Add dependencies
    graph.add_dependency(task2.task_id, task1.task_id)  # models depend on schema
    graph.add_dependency(task3.task_id, task2.task_id)  # API depends on models
    graph.add_dependency(task4.task_id, task3.task_id)  # tests depend on API
    graph.add_dependency(task5.task_id, task4.task_id)  # deploy depends on tests

    print(f"\nTask graph created with {len(graph.tasks)} tasks")

    # Get execution order
    levels = graph.get_execution_order()
    print(f"\nExecution levels (parallel execution):")
    for i, level in enumerate(levels):
        print(f"  Level {i+1}: {[t.name for t in level]}")

    # Get ready tasks
    ready = graph.get_ready_tasks()
    print(f"\nReady tasks: {[t.name for t in ready]}")

    # Validate
    errors = graph.validate_dependencies()
    print(f"\nValidation: {'Valid' if not errors else f'Errors: {errors'}")

    # Get stats
    stats = graph.get_stats()
    print(f"\nStats: {stats}")


async def file_tools_example():
    """Example of file system tools"""

    print("\n" + "=" * 60)
    print("File System Tools Example")
    print("=" * 60)

    from lightagent.tools import create_file_tools, list_directory, read_file

    # Create file tools with safety config
    config = FileToolConfig(
        safe_mode=True,
        path_config=SafePathConfig(
            allowed_roots=['D:/MyProject/python/LightAgent/examples'],
            max_file_size=1024 * 1024  # 1MB
        )
    )

    tools = create_file_tools(config)

    print(f"\nCreated {len(tools)} file system tools:")
    for tool in tools:
        print(f"  - {tool.name}: {tool.get_schema().description}")

    # Example usage (if safe)
    print("\nExample: List directory")
    try:
        result = await list_directory(
            'D:/MyProject/python/LightAgent/examples/workflow',
            recursive=False,
            config=config
        )

        if result['success']:
            print(f"  Found {result['count']} items:")
            for item in result['items'][:5]:  # Show first 5
                print(f"    - {item['name']} ({item['type']})")
        else:
            print(f"  Error: {result['error']}")

    except Exception as e:
        print(f"  Error: {e}")


async def workflow_with_agent_example():
    """Example of complete workflow with agent (requires API key)"""

    print("\n" + "=" * 60)
    print("Complete Workflow with Agent")
    print("=" * 60)

    # This example requires a valid API key
    # Uncomment to run with your API key

    """
    # Create agent
    model_adapter = OpenAIAdapter(
        api_key="your-api-key-here",
        model="gpt-3.5-turbo"
    )

    agent = Agent.create(
        name="assistant",
        model_adapter=model_adapter,
        system_prompt="You are a helpful assistant"
    )

    # Create workflow engine
    engine = await create_workflow_engine(
        agent=agent,
        enable_file_tools=True,
        verbose=True
    )

    # Execute a workflow
    result = await engine.execute(
        goal="Create a simple Python class for managing a todo list",
        execution_mode='sequential'
    )

    print(f"\nWorkflow result:")
    print(f"  Success: {result['success']}")
    print(f"  Completed tasks: {result.get('completed_tasks', 0)}/{result.get('total_tasks', 0)}")
    print(f"  Progress: {result.get('progress', 0):.1f}%")
    """


async def prompt_template_example():
    """Example of advanced prompt templates"""

    print("\n" + "=" * 60)
    print("Advanced Prompt Templates")
    print("=" * 60)

    from lightagent.workflow import (
        PromptTemplate,
        MultiPartPrompt,
        PromptManager
    )

    # Create manager
    manager = PromptManager()

    # Create custom templates
    system_template = PromptTemplate(
        template="You are a {{language}} expert with {{experience}} experience.",
        description="System prompt template"
    )

    user_template = PromptTemplate(
        template="""Task: {{task}}

Context:
{{context}}

Please provide a detailed solution.""",
        description="User prompt template"
    )

    # Register templates
    manager.register_template('system.system_prompt', system_template, category='system')
    manager.register_template('user.user_prompt', user_template, category='user')

    # Create multipart prompt
    multipart = MultiPartPrompt(
        system=system_template,
        user=user_template
    )

    # Format and display
    messages = multipart.to_messages(
        language="Python",
        experience="5 years",
        task="Write a function to parse JSON",
        context="The function should handle errors gracefully"
    )

    print("\nMulti-part prompt messages:")
    for msg in messages:
        print(f"\n{msg['role'].upper()}:")
        print(f"{msg['content'][:150]}...")

    # List templates
    templates = manager.list_templates()
    print(f"\nTotal templates registered: {len(templates)}")


async def main():
    """Run all examples"""

    print("\n" + "="*60)
    print("LightAgent Workflow - Advanced Examples")
    print("="*60)

    await planning_workflow_example()
    await task_graph_example()
    await file_tools_example()
    await prompt_template_example()
    # await workflow_with_agent_example()  # Requires API key

    print("\n" + "="*60)
    print("All examples completed!")
    print("="*60)


if __name__ == "__main__":
    asyncio.run(main())
