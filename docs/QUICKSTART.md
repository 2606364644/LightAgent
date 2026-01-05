# LightAgent Quick Start Guide

Get started with LightAgent in 5 minutes!

## Installation

```bash
# Clone or download the project
cd LightAgent

# Install dependencies
pip install -r requirements.txt

# Optional: Install specific model providers
pip install openai  # For OpenAI models
# pip install anthropic  # For Claude models
```

## Your First Agent (2 minutes)

Create a file `my_first_agent.py`:

```python
import asyncio
from lightagent import Agent, AgentConfig, MockAdapter, ModelConfig

async def main():
    # Create agent
    agent = Agent(
        config=AgentConfig(
            name="my_first_agent",
            system_prompt="You are a helpful assistant"
        ),
        model_adapter=MockAdapter(config=ModelConfig(model_name="gpt-3.5-turbo"))
    )

    # Initialize
    await agent.initialize()

    # Run
    result = await agent.run("Hello! What can you do?")
    print(result["response"])

asyncio.run(main())
```

Run it:
```bash
python my_first_agent.py
```

## Adding Tools (3 minutes)

Add function calling to your agent:

```python
import asyncio
from lightagent import Agent, AgentConfig, FunctionBuilder, MockAdapter, ModelConfig

# Define your function
async def get_weather(location: str) -> str:
    """Get weather for a location"""
    # Mock implementation
    return f"Weather in {location}: Sunny, 22C"

async def main():
    # Create tool from function
    weather_tool = FunctionBuilder.create_tool(
        get_weather,
        name="get_weather",
        description="Get weather information"
    )

    # Create agent
    agent = Agent(
        config=AgentConfig(
            name="weather_agent",
            system_prompt="Use get_weather tool when asked about weather",
            tools=["get_weather"]
        ),
        model_adapter=MockAdapter(config=ModelConfig(model_name="gpt-3.5-turbo"))
    )

    # Add tool
    agent.add_tool(weather_tool)

    # Initialize and run
    await agent.initialize()
    result = await agent.run("What's the weather in Tokyo?")
    print(result["response"])

asyncio.run(main())
```

## Using Real Models (5 minutes)

Replace MockAdapter with real OpenAI or Anthropic:

```python
import asyncio
from lightagent import Agent, AgentConfig, OpenAIAdapter, ModelConfig

async def main():
    # Configure OpenAI
    model_config = ModelConfig(
        model_name="gpt-3.5-turbo",
        api_key="your-openai-api-key"  # Or set OPENAI_API_KEY env var
    )

    # Create agent
    agent = Agent(
        config=AgentConfig(
            name="assistant",
            system_prompt="You are a helpful assistant"
        ),
        model_adapter=OpenAIAdapter(config=model_config)
    )

    await agent.initialize()
    result = await agent.run("Tell me a joke")
    print(result["response"])

asyncio.run(main())
```

## Multiple Agents Working Together

Create specialized agents that collaborate:

```python
import asyncio
from lightagent import Agent, AgentConfig, MessageBus, MockAdapter, ModelConfig

async def main():
    # Create message bus
    bus = MessageBus()

    # Create specialized agents
    researcher = Agent(
        config=AgentConfig(name="researcher", system_prompt="You research topics"),
        model_adapter=MockAdapter(config=ModelConfig(model_name="gpt-3.5-turbo"))
    )

    writer = Agent(
        config=AgentConfig(name="writer", system_prompt="You write content"),
        model_adapter=MockAdapter(config=ModelConfig(model_name="gpt-3.5-turbo"))
    )

    # Initialize and register
    await researcher.initialize()
    await writer.initialize()
    await bus.register_agent("researcher", researcher)
    await bus.register_agent("writer", writer)

    # Agents can now communicate
    result = await researcher.run("Research Python programming")
    print(f"Researcher: {result['response']}")

asyncio.run(main())
```

## Next Steps

1. **Explore Examples**: Check the `examples/` directory for more demos
   - `basic_agent.py`: Function tools
   - `rag_agent.py`: Knowledge base with RAG
   - `multi_agent.py`: Agent collaboration
   - `middleware_agent.py`: Custom middleware

2. **Read Documentation**: See `README.md` for detailed documentation

3. **Build Your Own**:
   - Create custom tools
   - Write middleware
   - Configure multi-agent workflows

## Common Patterns

### Pattern 1: Tool Creation

```python
# Simple function tool
tool = FunctionBuilder.create_tool(my_function, name="tool_name")

# Custom tool class
from lightagent import BaseTool, ToolExecutionResult

class MyTool(BaseTool):
    name = "my_tool"
    description = "My custom tool"

    async def execute(self, **kwargs):
        return ToolExecutionResult(success=True, result="Done")
```

### Pattern 2: Middleware

```python
from lightagent import MiddlewareManager, CacheMiddleware

manager = MiddlewareManager()
manager.add(CacheMiddleware(ttl_seconds=300))

agent = Agent(
    config=agent_config,
    model_adapter=model_adapter,
    middlewares=manager
)
```

### Pattern 3: Context Management

```python
# Get conversation history
context = agent.get_context()
print(f"Turns: {len(context.conversation_history)}")

# Reset conversation
agent.reset_context()
```

## Environment Variables

Set these for convenience:

```bash
# OpenAI
export OPENAI_API_KEY="your-key"

# Anthropic
export ANTHROPIC_API_KEY="your-key"

# LightAgent can read these automatically
```

## Troubleshooting

**Problem**: Import errors
**Solution**: Run `pip install -r requirements.txt`

**Problem**: API key errors
**Solution**: Set `OPENAI_API_KEY` or `ANTHROPIC_API_KEY` environment variable

**Problem**: Async errors
**Solution**: Always run async code with `asyncio.run(main())`

## Support

- GitHub Issues: Report bugs and request features
- Examples: Check `examples/` directory
- README: Full documentation

Happy building with LightAgent!
