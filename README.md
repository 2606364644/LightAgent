# LightAgent

A lightweight, modular Python framework for building AI agents with async/await support.

## Features

- **Modular Agent Configuration**: Configure tools, models, middleware, and sub-agents
- **Tool Calling System**: Support for MCP, Function Call, and RAG tools
- **Multi-Model Function Calling**: Automatic format conversion for OpenAI, Anthropic, Ollama
- **Prompt Engineering**: Flexible system prompt and automatic tool description generation
- **Middleware Pipeline**: Pre and post-processing with built-in and custom middleware
- **A2A Protocol**: Agent-to-Agent communication for multi-agent workflows
- **Multi-Model Support**: OpenAI, Anthropic, Ollama, and custom adapters
- **Async/Await**: High performance async I/O for model interactions
- **Type Safety**: Built with Pydantic for validation and type hints

## Installation

```bash
# Install core dependencies
pip install -r requirements.txt

# For OpenAI models
pip install openai

# For Anthropic models
pip install anthropic

# For Ollama (local models)
# Install Ollama from https://ollama.ai
```

## Quick Start

### Basic Agent

```python
import asyncio
from lightagent import Agent, AgentConfig, OpenAIAdapter, ModelConfig, FunctionBuilder

# Define a function
async def get_weather(location: str) -> str:
    return f"Weather in {location}: Sunny, 22C"

# Create agent
async def main():
    model_config = ModelConfig(
        model_name="gpt-3.5-turbo",
        api_key="your-api-key"
    )

    agent = Agent(
        config=AgentConfig(
            name="assistant",
            system_prompt="You are a helpful assistant"
        ),
        model_adapter=OpenAIAdapter(config=model_config)
    )

    # Add tool
    weather_tool = FunctionBuilder.create_tool(get_weather, name="get_weather")
    agent.add_tool(weather_tool)

    # Initialize and run
    await agent.initialize()
    result = await agent.run("What's the weather in Tokyo?")
    print(result['response'])

asyncio.run(main())
```

### Multi-Agent Collaboration

```python
from lightagent import Agent, AgentConfig, MessageBus, MockAdapter, ModelConfig

# Create specialized agents
sales_agent = Agent(config=AgentConfig(name="sales"), model_adapter=...)
support_agent = Agent(config=AgentConfig(name="support"), model_adapter=...)

# Set up communication
message_bus = MessageBus()
await message_bus.register_agent("sales", sales_agent)
await message_bus.register_agent("support", support_agent)

# Agents can now communicate
await sales_agent.send_message("support", message)
```

### RAG Agent

```python
from lightagent import RAGTool, KnowledgeBase, Agent, AgentConfig

# Create RAG tool
rag_tool = RAGTool()
kb = KnowledgeBase(rag_tool=rag_tool)

# Add documents
await kb.add_text("LightAgent is a Python agent framework")

# Create agent with RAG
agent = Agent(
    config=AgentConfig(
        name="rag_assistant",
        tools=["rag_tool"]
    ),
    model_adapter=...
)
agent.add_tool(rag_tool)

# Query knowledge base
result = await agent.run("What is LightAgent?")
```

### Middleware Pipeline

```python
from lightagent import (
    Agent, AgentConfig,
    LoggingMiddleware,
    CacheMiddleware,
    ValidationMiddleware
)

# Create middleware manager
middleware_manager = MiddlewareManager()
middleware_manager.add(LoggingMiddleware())
middleware_manager.add(CacheMiddleware())
middleware_manager.add(ValidationMiddleware())

# Create agent with middleware
agent = Agent(
    config=AgentConfig(
        name="assistant",
        enable_middleware=True
    ),
    model_adapter=...,
    middlewares=middleware_manager
)
```

## Architecture

### Core Components

- **Agent**: Main agent class with reasoning loop and tool execution
- **MessageBus**: Handles A2A protocol communication between agents
- **MiddlewareManager**: Manages pre/post-processing pipeline
- **ModelAdapter**: Abstract interface for different LLM providers

### Tools

1. **MCP Tools**: Call external MCP servers
2. **Function Tools**: Wrap Python functions as tools
3. **RAG Tools**: Retrieval-augmented generation with vector search

### Model Adapters

- **OpenAIAdapter**: GPT-3.5, GPT-4, etc.
- **AnthropicAdapter**: Claude 3, Claude 3.5, etc.
- **OllamaAdapter**: Local models via Ollama
- **MockAdapter**: Testing without API calls

### Multi-Model Function Calling

The framework automatically handles function calling format differences:

```python
# Configure agent for specific provider
agent = Agent(
    config=AgentConfig(
        name="assistant",
        model_provider="openai",  # or "anthropic", "ollama"
        tools=["my_tool"]
    ),
    model_adapter=OpenAIAdapter(...)
)

# Tools work the same way regardless of provider
tool = FunctionBuilder.create_tool(my_function)
agent.add_tool(tool)
```

**Supported Providers:**
- OpenAI: Standard function calling format
- Anthropic: Claude tool use format
- Ollama: OpenAI-compatible format
- Custom: Easy to extend

### Middleware

- **LoggingMiddleware**: Log all interactions
- **RateLimitMiddleware**: Rate limiting
- **CacheMiddleware**: Response caching
- **ValidationMiddleware**: Input/output validation
- **RetryMiddleware**: Automatic retry on failures
- **Custom**: Easy to create your own

## Examples

See the `examples/` directory for complete examples:

- `simple_demo.py`: Minimal demo (5 minutes)
- `basic_agent.py`: Simple agent with function tools
- `rag_agent.py`: RAG-enabled agent with knowledge base
- `multi_agent.py`: Multi-agent collaboration
- `middleware_agent.py`: Custom middleware pipeline
- `multi_model_agent.py`: Function calling with different model providers
- `prompt_engineering.py`: Prompt engineering and automatic tool descriptions
- `simplified_usage.py`: Agent creation methods comparison

## Documentation

Complete documentation is available in the [docs/](docs/) directory:

- [Documentation Index](docs/README.md) - Central hub for all documentation
- [Quick Start Guide](docs/QUICKSTART.md) - Get started in 5 minutes
- [Project Overview](docs/PROJECT_OVERVIEW.md) - Complete feature list and architecture
- [Project Structure](docs/PROJECT_STRUCTURE.md) - Detailed architecture explanation
- [Function Calling Guide](docs/FUNCTION_CALLING.md) - Multi-model function calling details
- [Prompt Engineering Guide](docs/PROMPT_ENGINEERING.md) - System prompt and tool description generation
- [Agent Creation Guide](docs/AGENT_CREATION.md) - AgentConfig vs Agent.create() comparison

## Configuration

### Agent Config

```python
AgentConfig(
    name="agent_name",
    model_name="gpt-3.5-turbo",
    description="Agent description",
    system_prompt="System prompt",
    tools=["tool1", "tool2"],
    max_iterations=10,
    timeout=30.0,
    enable_middleware=True
)
```

### Model Config

```python
ModelConfig(
    model_name="gpt-3.5-turbo",
    api_key="your-key",
    api_base="https://api.example.com",
    temperature=0.7,
    max_tokens=2000,
    timeout=30.0
)
```

## A2A Protocol

Agents can communicate using the A2A (Agent-to-Agent) protocol:

```python
from lightagent import A2AMessage, MessageType

# Create message
message = A2AMessage(
    from_agent="agent1",
    to_agent="agent2",
    content="Hello from agent1",
    message_type=MessageType.REQUEST
)

# Send via message bus
response = await message_bus.send(
    from_agent="agent1",
    to_agent="agent2",
    message=message
)

# Broadcast to all agents
responses = await message_bus.broadcast(
    from_agent="agent1",
    message=message
)

# Delegate task
response = await message_bus.delegate(
    from_agent="agent1",
    to_agent="agent2",
    message=message,
    context={"task": "complex_task"}
)
```

## Custom Tools

Create custom tools by extending `BaseTool`:

```python
from lightagent import BaseTool, ToolExecutionResult

class MyTool(BaseTool):
    name = "my_tool"
    description = "My custom tool"

    async def execute(self, **kwargs) -> ToolExecutionResult:
        try:
            # Your logic here
            result = do_something(kwargs)
            return ToolExecutionResult(success=True, result=result)
        except Exception as e:
            return ToolExecutionResult(success=False, error=str(e))

# Add to agent
agent.add_tool(MyTool())
```

## Testing

Use MockAdapter for testing without API calls:

```python
from lightagent import MockAdapter, ModelConfig

mock_adapter = MockAdapter(config=ModelConfig(model_name="mock"))
agent = Agent(config=..., model_adapter=mock_adapter)
```

## Requirements

- Python 3.8+
- pydantic >= 2.0.0
- aiohttp >= 3.9.0
- openai or anthropic (depending on model used)

## License

MIT License

## Contributing

Contributions are welcome! Please feel free to submit issues or pull requests.
