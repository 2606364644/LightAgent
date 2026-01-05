"""
Basic Agent Example

This example demonstrates:
1. Creating a simple agent with function tools
2. Running the agent with user input
3. Handling tool calls
"""

import asyncio
from lightagent import (
    Agent,
    AgentConfig,
    FunctionBuilder,
    OpenAIAdapter,
    ModelConfig,
    MockAdapter
)


# Define custom functions
async def get_current_time(timezone: str = "UTC") -> str:
    """
    Get the current time for a given timezone

    Args:
        timezone: Timezone name (e.g., 'UTC', 'America/New_York')

    Returns:
        Current time as string
    """
    from datetime import datetime
    import pytz

    try:
        tz = pytz.timezone(timezone)
        current_time = datetime.now(tz)
        return current_time.strftime("%Y-%m-%d %H:%M:%S %Z")
    except Exception as e:
        return f"Error getting time for {timezone}: {str(e)}"


async def calculate(expression: str) -> float:
    """
    Calculate a mathematical expression

    Args:
        expression: Mathematical expression (e.g., '2 + 2 * 3')

    Returns:
        Calculation result
    """
    try:
        # Safe evaluation of mathematical expressions
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
    except Exception as e:
        raise ValueError(f"Invalid expression: {str(e)}")


async def main():
    # Create model adapter (using MockAdapter for demonstration)
    # For production, replace with OpenAIAdapter or AnthropicAdapter
    model_config = ModelConfig(
        model_name="gpt-3.5-turbo",
        api_key="your-api-key-here"  # Replace with actual API key
    )

    # Use MockAdapter for testing without API calls
    model_adapter = MockAdapter(config=model_config)

    # Or use OpenAI (uncomment to use):
    # model_adapter = OpenAIAdapter(config=model_config)

    # Create function tools
    time_tool = FunctionBuilder.create_tool(
        get_current_time,
        name="get_current_time",
        description="Get the current time for any timezone"
    )

    calc_tool = FunctionBuilder.create_tool(
        calculate,
        name="calculate",
        description="Calculate mathematical expressions"
    )

    # Configure agent
    agent_config = AgentConfig(
        name="assistant",
        description="A helpful assistant with time and calculation tools",
        system_prompt="""You are a helpful assistant that can:
1. Get the current time in any timezone
2. Calculate mathematical expressions

When users ask for time or calculations, use the appropriate tools.""",
        tools=["get_current_time", "calculate"],
        max_iterations=5
    )

    # Create agent
    agent = Agent(
        config=agent_config,
        model_adapter=model_adapter
    )

    # Add tools to agent
    agent.add_tool(time_tool)
    agent.add_tool(calc_tool)

    # Initialize agent
    await agent.initialize()

    # Example 1: Simple conversation
    print("=== Example 1: Simple conversation ===")
    result = await agent.run("Hello! What can you do?")
    print(f"Response: {result['response']}\n")

    # Example 2: Tool call - Get time
    print("=== Example 2: Get current time ===")
    result = await agent.run("What time is it in Tokyo?")
    print(f"Response: {result['response']}")
    print(f"Tool calls made: {len(result.get('tool_calls', []))}\n")

    # Example 3: Tool call - Calculate
    print("=== Example 3: Calculate expression ===")
    result = await agent.run("Calculate 25 * 4 + 10")
    print(f"Response: {result['response']}")
    print(f"Tool calls made: {len(result.get('tool_calls', []))}\n")

    # Example 4: Multiple tool calls
    print("=== Example 4: Multiple operations ===")
    result = await agent.run("What time is it in London, and also calculate 100 / 4")
    print(f"Response: {result['response']}")
    print(f"Tool calls made: {len(result.get('tool_calls', []))}")
    print(f"Iterations: {result.get('iterations', 0)}\n")


if __name__ == "__main__":
    asyncio.run(main())
