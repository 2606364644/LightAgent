"""
Basic Workflow Example

Demonstrates basic usage of the workflow engine
"""
import asyncio
from lightagent.workflow import (
    create_workflow_engine,
    PromptTemplate
)
from lightagent.models.providers import OpenAIAdapter


async def basic_workflow_example():
    """Basic workflow execution example"""

    # Create model adapter (replace with your actual API key)
    model_adapter = OpenAIAdapter(
        api_key="your-api-key-here",
        model="gpt-3.5-turbo"
    )

    # Create workflow engine
    engine = await create_workflow_engine(
        agent=None,  # Can pass agent instance here
        verbose=True
    )

    # Example 1: Simple prompt template
    print("=" * 60)
    print("Example 1: Using Prompt Templates")
    print("=" * 60)

    # Create a custom prompt template
    template = PromptTemplate(
        template="You are a {{role}}. Your task is to {{task}}.",
        description="Simple role-based prompt"
    )

    # Format the template
    prompt = template.format(role="Python expert", task="explain async/await")
    print(f"\nFormatted prompt:\n{prompt}\n")

    # Example 2: Using the workflow engine
    print("=" * 60)
    print("Example 2: Workflow Engine")
    print("=" * 60)

    # Create a simple task
    goal = "Create a Python function to calculate fibonacci numbers"

    # Execute the workflow (requires agent)
    # result = await engine.execute(goal)
    # print(f"\nResult: {result}")

    # Example 3: Available templates
    print("=" * 60)
    print("Example 3: Available Prompt Templates")
    print("=" * 60)

    templates = engine.get_available_prompts()
    print(f"\nAvailable templates: {templates[:5]}...")  # Show first 5

    # Example 4: Using a specific template
    print("=" * 60)
    print("Example 4: Using Built-in Template")
    print("=" * 60)

    try:
        planning_prompt = engine.use_prompt_template(
            'planner.task_decomposition',
            goal="Build a simple web API",
            context="Technology: Python, FastAPI"
        )
        print(f"\nPlanning prompt generated:\n{planning_prompt[:200]}...\n")
    except Exception as e:
        print(f"\nTemplate usage: {e}\n")


if __name__ == "__main__":
    asyncio.run(basic_workflow_example())
