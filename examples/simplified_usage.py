"""
Simplified Agent Usage Example

This example demonstrates two ways to create agents:
1. Traditional way with AgentConfig
2. Simplified way with Agent.create()
"""

import asyncio
from lightagent import (
    Agent,
    AgentConfig,
    FunctionBuilder,
    MockAdapter,
    ModelConfig,
    MiddlewareManager,
    LoggingMiddleware
)


# Define a tool
async def calculator(expression: str) -> float:
    """Calculate a mathematical expression"""
    import ast
    import operator as op

    operators = {
        ast.Add: op.add,
        ast.Sub: op.sub,
        ast.Mult: op.mul,
        ast.Div: op.truediv,
    }

    def eval_expr(node):
        if isinstance(node, ast.Num):
            return node.n
        elif isinstance(node, ast.BinOp):
            return operators[type(node.op)](
                eval_expr(node.left),
                eval_expr(node.right)
            )
        else:
            raise TypeError(f"Unsupported type: {type(node)}")

    return eval_expr(ast.parse(expression, mode='eval').body)


async def example_1_traditional_way():
    """Example 1: Traditional way with explicit AgentConfig"""
    print("="*60)
    print("Example 1: Traditional Way (with AgentConfig)")
    print("="*60)
    print()

    # Step 1: Create model adapter
    model_config = ModelConfig(model_name="gpt-3.5-turbo")
    model_adapter = MockAdapter(config=model_config)

    # Step 2: Create configuration
    agent_config = AgentConfig(
        name="calculator_agent",
        description="Math calculator agent",
        system_prompt="You are a math calculator. Use the calculator tool.",
        max_iterations=5,
        auto_tool_prompt=True
    )

    # Step 3: Create agent
    agent = Agent(
        config=agent_config,
        model_adapter=model_adapter
    )

    # Step 4: Add tool
    calc_tool = FunctionBuilder.create_tool(calculator, name="calculator")
    agent.add_tool(calc_tool)

    # Step 5: Initialize
    await agent.initialize()

    # Step 6: Run
    result = await agent.run("Calculate 25 * 4")
    print(f"Response: {result['response']}")
    print(f"Tool calls: {len(result.get('tool_calls', []))}")
    print()

    # Pros: Explicit, clear separation
    print("Pros:")
    print("- Explicit configuration")
    print("- Easy to save/load config from file")
    print("- Clear separation of concerns")
    print("- Config validation before agent creation")
    print()


async def example_2_simplified_way():
    """Example 2: Simplified way with Agent.create()"""
    print("="*60)
    print("Example 2: Simplified Way (with Agent.create())")
    print("="*60)
    print()

    # All in one step!
    agent = Agent.create(
        name="calculator_agent",
        model_adapter=MockAdapter(config=ModelConfig(model_name="gpt-3.5-turbo")),
        system_prompt="You are a math calculator. Use the calculator tool.",
        tools=[FunctionBuilder.create_tool(calculator, name="calculator")],
        max_iterations=5
    )

    # Initialize and run
    await agent.initialize()
    result = await agent.run("Calculate 25 * 4")
    print(f"Response: {result['response']}")
    print(f"Tool calls: {len(result.get('tool_calls', []))}")
    print()

    # Pros: Concise, quick
    print("Pros:")
    print("- Less boilerplate code")
    print("- Quick to write")
    print("- All parameters in one place")
    print("- Still creates AgentConfig internally")
    print()


async def example_3_comparison():
    """Example 3: Side-by-side comparison"""
    print("="*60)
    print("Example 3: Side-by-Side Comparison")
    print("="*60)
    print()

    model_adapter = MockAdapter(config=ModelConfig(model_name="gpt-3.5-turbo"))
    calc_tool = FunctionBuilder.create_tool(calculator, name="calculator")

    print("### Traditional Way ###")
    print("""
config = AgentConfig(
    name="agent",
    system_prompt="You are helpful",
    max_iterations=10
)
agent = Agent(config=config, model_adapter=adapter)
agent.add_tool(tool)
await agent.initialize()
""")

    print("### Simplified Way ###")
    print("""
agent = Agent.create(
    name="agent",
    model_adapter=adapter,
    system_prompt="You are helpful",
    tools=[tool],
    max_iterations=10
)
await agent.initialize()
""")

    print("### Code Comparison ###")
    print(f"Traditional: ~10 lines")
    print(f"Simplified: ~5 lines")
    print(f"Reduction: 50% less code!")
    print()


async def example_4_when_to_use_which():
    """Example 4: When to use each approach"""
    print("="*60)
    print("Example 4: When to Use Each Approach")
    print("="*60)
    print()

    print("### Use AgentConfig when: ###")
    print("""
1. Loading config from files
   ```python
   config = AgentConfig.model_validate_json(file_content)
   agent = Agent(config=config, model_adapter=adapter)
   ```

2. Sharing config across agents
   ```python
   shared_config = AgentConfig(...)
   agent1 = Agent(config=shared_config, adapter=adapter1)
   agent2 = Agent(config=shared_config, adapter=adapter2)
   ```

3. Need config validation before creation
   ```python
   try:
       config = AgentConfig(...)  # Validates immediately
   except ValidationError:
       print("Invalid config")
   ```

4. Serializing/saving config
   ```python
   config_dict = agent.config.model_dump()
   json.dump(config_dict, file)
   ```
    """)

    print("### Use Agent.create() when: ###")
    print("""
1. Quick prototyping
   ```python
   agent = Agent.create(name="bot", model_adapter=adapter, ...)
   ```

2. Simple scripts
   ```python
   # One-liner agent creation
   agent = Agent.create("bot", adapter, system_prompt="...")
   ```

3. All config known upfront
   ```python
   agent = Agent.create(
       name="bot",
       model_adapter=adapter,
       system_prompt="...",
       tools=[tool1, tool2],
       max_iterations=10
   )
   ```

4. Don't need config reuse
   """)

    print("### Recommendation ###")
    print("""
- Beginners: Use Agent.create() - simpler
- Production: Use AgentConfig - more control
- Prototyping: Use Agent.create() - faster
- Config Management: Use AgentConfig - easier to manage
    """)


async def example_5_config_file_usage():
    """Example 5: Loading config from file"""
    print("="*60)
    print("Example 5: Config File Usage (AgentConfig benefit)")
    print("="*60)
    print()

    # Simulate loading from file
    config_json = '''{
        "name": "calculator_agent",
        "description": "Loads from config file",
        "system_prompt": "You are a math calculator",
        "max_iterations": 5,
        "auto_tool_prompt": true
    }'''

    print("### config.json ###")
    print(config_json)
    print()

    # Load config
    import json
    config = AgentConfig.model_validate_json(config_json)

    print("### Loaded Config ###")
    print(f"Name: {config.name}")
    print(f"Max iterations: {config.max_iterations}")
    print(f"Auto tool prompt: {config.auto_tool_prompt}")
    print()

    # Create agent
    agent = Agent(
        config=config,
        model_adapter=MockAdapter(config=ModelConfig(model_name="gpt-3.5-turbo"))
    )

    agent.add_tool(FunctionBuilder.create_tool(calculator, name="calculator"))
    await agent.initialize()

    result = await agent.run("Calculate 10 + 20")
    print(f"Response: {result['response']}")
    print()


async def main():
    """Run all examples"""
    print("\n" + "="*60)
    print("LightAgent - Simplified Usage Examples")
    print("="*60)
    print()

    await example_1_traditional_way()
    await example_2_simplified_way()
    await example_3_comparison()
    await example_4_when_to_use_which()
    await example_5_config_file_usage()

    print("="*60)
    print("Summary")
    print("="*60)
    print("""
## Two Ways to Create Agents

### 1. Traditional (AgentConfig)
```python
config = AgentConfig(name="agent", system_prompt="...")
agent = Agent(config=config, model_adapter=adapter)
```

**Advantages:**
- Config validation upfront
- Easy serialization
- Config sharing
- File-based config

**Use when:**
- Production apps
- Config management
- Need validation

### 2. Simplified (Agent.create)
```python
agent = Agent.create(
    name="agent",
    model_adapter=adapter,
    system_prompt="..."
)
```

**Advantages:**
- Less boilerplate
- Quicker to write
- All in one place
- Same power internally

**Use when:**
- Quick prototypes
- Simple scripts
- Learning
- Don't need config reuse

## Key Point

Both create the same Agent with the same AgentConfig internally!

Agent.create() is just a convenience method that creates
AgentConfig for you automatically.

Choose whichever fits your use case!
    """)


if __name__ == "__main__":
    asyncio.run(main())
