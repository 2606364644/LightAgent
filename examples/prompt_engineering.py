"""
Prompt Engineering Example

This example demonstrates:
1. Configuring system prompts
2. Using the call() method for direct model calls
3. Automatic tool prompt generation
4. Custom tool prompt templates
"""

import asyncio
from lightagent import (
    Agent,
    AgentConfig,
    FunctionBuilder,
    MockAdapter,
    ModelConfig
)


# Define tools
async def get_weather(location: str, unit: str = "celsius") -> dict:
    """
    Get current weather for a location

    Args:
        location: City name or location
        unit: Temperature unit (celsius or fahrenheit)

    Returns:
        Weather information
    """
    return {
        "location": location,
        "temperature": 22 if unit == "celsius" else 72,
        "condition": "Sunny",
        "humidity": 65,
        "unit": unit
    }


async def search_web(query: str, num_results: int = 5) -> list:
    """
    Search the web for information

    Args:
        query: Search query
        num_results: Number of results to return

    Returns:
        List of search results
    """
    return [
        {
            "title": f"Result {i+1} for '{query}'",
            "url": f"https://example.com/{i+1}",
            "snippet": f"This is result {i+1}"
        }
        for i in range(num_results)
    ]


async def calculator(expression: str) -> float:
    """
    Calculate a mathematical expression

    Args:
        expression: Mathematical expression (e.g., '2 + 2 * 3')

    Returns:
        Calculation result
    """
    import ast
    import operator as op

    operators = {
        ast.Add: op.add,
        ast.Sub: op.sub,
        ast.Mult: op.mul,
        ast.Div: op.truediv,
        ast.Pow: op.pow,
        ast.USub: op.neg,
    }

    def eval_expr(node):
        if isinstance(node, ast.Num):
            return node.n
        elif isinstance(node, ast.BinOp):
            return operators[type(node.op)](
                eval_expr(node.left),
                eval_expr(node.right)
            )
        elif isinstance(node, ast.UnaryOp):
            return operators[type(node.op)](eval_expr(node.operand))
        else:
            raise TypeError(f"Unsupported type: {type(node)}")

    return eval_expr(ast.parse(expression, mode='eval').body)


async def example_1_basic_system_prompt():
    """Example 1: Basic system prompt configuration"""
    print("="*60)
    print("Example 1: Basic System Prompt")
    print("="*60)
    print()

    # Configure agent with system prompt
    agent_config = AgentConfig(
        name="assistant",
        system_prompt="""You are a helpful assistant specialized in weather information.
Always provide accurate and helpful responses.
When asked about weather, use the get_weather tool."""
    )

    model_config = ModelConfig(model_name="gpt-3.5-turbo")
    agent = Agent(config=agent_config, model_adapter=MockAdapter(config=model_config))

    # Add tool
    weather_tool = FunctionBuilder.create_tool(get_weather, name="get_weather")
    agent.add_tool(weather_tool)

    await agent.initialize()

    # Check the built system prompt (includes tool descriptions)
    print("Built System Prompt:")
    print("-"*60)
    print(agent._build_system_prompt())
    print("-"*60)
    print()

    # Run agent
    result = await agent.run("What's the weather in Tokyo?")
    print(f"Response: {result['response']}\n")


async def example_2_call_method():
    """Example 2: Using call() method for direct invocation"""
    print("="*60)
    print("Example 2: Direct Call Method")
    print("="*60)
    print()

    agent_config = AgentConfig(
        name="assistant",
        system_prompt="You are a helpful assistant."
    )

    model_config = ModelConfig(model_name="gpt-3.5-turbo")
    agent = Agent(config=agent_config, model_adapter=MockAdapter(config=model_config))

    # Add multiple tools
    agent.add_tool(FunctionBuilder.create_tool(get_weather, name="get_weather"))
    agent.add_tool(FunctionBuilder.create_tool(search_web, name="search_web"))
    agent.add_tool(FunctionBuilder.create_tool(calculator, name="calculator"))

    await agent.initialize()

    # Call with custom system prompt
    print("1. Call with custom system prompt:")
    result = await agent.call(
        user_prompt="Calculate 25 * 4",
        system_prompt="You are a math expert. Use the calculator tool."
    )
    print(f"Response: {result['response']}\n")

    # Call with specific tools
    print("2. Call with only weather tool:")
    result = await agent.call(
        user_prompt="What's the weather in Paris?",
        tools=["get_weather"]
    )
    print(f"Response: {result['response']}\n")


async def example_3_auto_tool_prompt():
    """Example 3: Automatic tool prompt generation"""
    print("="*60)
    print("Example 3: Automatic Tool Prompt")
    print("="*60)
    print()

    agent_config = AgentConfig(
        name="assistant",
        system_prompt="You are a helpful assistant.",
        auto_tool_prompt=True  # Enable automatic tool prompt
    )

    model_config = ModelConfig(model_name="gpt-3.5-turbo")
    agent = Agent(config=agent_config, model_adapter=MockAdapter(config=model_config))

    # Add tools with parameters
    agent.add_tool(FunctionBuilder.create_tool(get_weather, name="get_weather"))
    agent.add_tool(FunctionBuilder.create_tool(calculator, name="calculator"))

    await agent.initialize()

    # Show generated tool prompt
    tool_prompt = agent._generate_tool_prompt()
    print("Generated Tool Prompt:")
    print("-"*60)
    print(tool_prompt)
    print("-"*60)
    print()


async def example_4_custom_tool_template():
    """Example 4: Custom tool prompt template"""
    print("="*60)
    print("Example 4: Custom Tool Template")
    print("="*60)
    print()

    custom_template = """## Available Tools

You can use these tools to help the user:

{tool_descriptions}

**Instructions**:
- Think step by step before using tools
- Explain which tool you're using and why
- Show the tool results to the user
- Always be helpful and accurate"""

    agent_config = AgentConfig(
        name="assistant",
        system_prompt="You are a helpful AI assistant.",
        auto_tool_prompt=True,
        tool_prompt_template=custom_template
    )

    model_config = ModelConfig(model_name="gpt-3.5-turbo")
    agent = Agent(config=agent_config, model_adapter=MockAdapter(config=model_config))

    agent.add_tool(FunctionBuilder.create_tool(get_weather, name="get_weather"))
    agent.add_tool(FunctionBuilder.create_tool(search_web, name="search_web"))

    await agent.initialize()

    # Show custom formatted prompt
    print("Custom Tool Prompt:")
    print("-"*60)
    print(agent._build_system_prompt())
    print("-"*60)
    print()


async def example_5_disable_auto_tool_prompt():
    """Example 5: Disable automatic tool prompt"""
    print("="*60)
    print("Example 5: Manual Tool Prompt Control")
    print("="*60)
    print()

    # Manually include tool info in system prompt
    manual_system_prompt = """You are a helpful assistant.

You have access to a weather tool and a calculator.
Use them when appropriate to help users."""

    agent_config = AgentConfig(
        name="assistant",
        system_prompt=manual_system_prompt,
        auto_tool_prompt=False  # Disable automatic tool prompt
    )

    model_config = ModelConfig(model_name="gpt-3.5-turbo")
    agent = Agent(config=agent_config, model_adapter=MockAdapter(config=model_config))

    agent.add_tool(FunctionBuilder.create_tool(get_weather, name="get_weather"))
    agent.add_tool(FunctionBuilder.create_tool(calculator, name="calculator"))

    await agent.initialize()

    print("System Prompt (without auto-generated tool descriptions):")
    print("-"*60)
    print(agent._build_system_prompt())
    print("-"*60)
    print()


async def main():
    """Run all examples"""
    print("\n" + "="*60)
    print("LightAgent - Prompt Engineering Examples")
    print("="*60)
    print()

    await example_1_basic_system_prompt()
    await example_2_call_method()
    await example_3_auto_tool_prompt()
    await example_4_custom_tool_template()
    await example_5_disable_auto_tool_prompt()

    print("="*60)
    print("Summary")
    print("="*60)
    print("""
Key Features:

1. **System Prompt Configuration**
   - Set base system prompt in AgentConfig
   - Override with call(system_prompt=...)

2. **Direct Call Method**
   - agent.call(user_prompt="...")
   - Optional custom system prompt
   - Optional tool filtering

3. **Automatic Tool Prompt**
   - Auto-generates tool descriptions
   - Includes parameters and requirements
   - Controlled by auto_tool_prompt flag

4. **Custom Templates**
   - Define your own tool prompt template
   - Use {tool_descriptions} placeholder
   - Full control over formatting

5. **Manual Control**
   - Disable auto_tool_prompt for manual control
   - Include tool info directly in system prompt
   - Useful for specialized prompts

Usage:

```python
# Basic
agent = Agent(config=AgentConfig(
    system_prompt="You are a helpful assistant"
))
result = await agent.run("Hello")

# Direct call with custom prompt
result = await agent.call(
    user_prompt="Calculate something",
    system_prompt="You are a math expert",
    tools=["calculator"]
)

# Custom tool template
agent.config.tool_prompt_template = "Tools: {tool_descriptions}"
```
    """)


if __name__ == "__main__":
    asyncio.run(main())
