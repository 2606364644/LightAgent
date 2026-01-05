# LightAgent Documentation

Welcome to the LightAgent documentation hub.

## Getting Started

### [Quick Start Guide](QUICKSTART.md)
New to LightAgent? Start here! This guide will get you up and running in 5 minutes.

**Topics covered:**
- Installation
- Your first agent
- Adding tools
- Using real models
- Multiple agents collaboration

## Core Concepts

### [Project Structure](PROJECT_STRUCTURE.md)
Understanding the framework architecture and organization.

**Topics covered:**
- Directory layout
- Core components (Agent, Protocol, Middleware, Models, Tools)
- Usage patterns
- Extension points
- Performance considerations
- Best practices

### [Function Calling Multi-Model Support](FUNCTION_CALLING.md)
Deep dive into function calling across different model providers.

**Topics covered:**
- Format conversion between providers
- Supported providers (OpenAI, Anthropic, Ollama)
- Adding new providers
- Execution flow
- Technical details

### [Prompt Engineering](PROMPT_ENGINEERING.md)
Master prompt engineering with LightAgent.

**Topics covered:**
- System prompt configuration
- Direct model calls with call() method
- Automatic tool description generation
- Custom prompt templates
- Best practices and examples

### [Agent Creation](AGENT_CREATION.md)
Understanding AgentConfig vs Agent.create().

**Topics covered:**
- Two ways to create agents
- When to use each approach
- Configuration management
- File-based config
- Best practices

## Examples

See the `../examples/` directory for working code examples:

1. **simple_demo.py** - Minimal working example
2. **basic_agent.py** - Agent with function tools
3. **rag_agent.py** - Knowledge base with RAG
4. **multi_agent.py** - Agent collaboration
5. **middleware_agent.py** - Custom middleware
6. **multi_model_agent.py** - Multi-model function calling
7. **prompt_engineering.py** - Prompt engineering and tool descriptions
8. **simplified_usage.py** - AgentConfig vs Agent.create() comparison

## Configuration

### Example Configuration
See `../config_example.yaml` for a complete configuration example showing:
- Model configurations
- Agent settings
- Tool definitions
- Middleware setup
- A2A protocol settings
- RAG configuration

## API Reference

### Core Components

#### Agent
```python
from lightagent import Agent, AgentConfig

agent = Agent(
    config=AgentConfig(name="my_agent"),
    model_adapter=model_adapter
)
await agent.initialize()
result = await agent.run("Hello")
```

#### Tools
```python
from lightagent import FunctionBuilder

tool = FunctionBuilder.create_tool(my_function)
agent.add_tool(tool)
```

#### Middleware
```python
from lightagent import MiddlewareManager, CacheMiddleware

manager = MiddlewareManager()
manager.add(CacheMiddleware())
agent.middlewares = manager
```

#### A2A Protocol
```python
from lightagent import MessageBus, A2AMessage

bus = MessageBus()
await bus.register_agent("agent1", agent1)
await bus.register_agent("agent2", agent2)

message = A2AMessage(
    from_agent="agent1",
    to_agent="agent2",
    content="Hello"
)
response = await bus.send("agent1", "agent2", message)
```

## Model Adapters

### OpenAI
```python
from lightagent import OpenAIAdapter, ModelConfig

config = ModelConfig(
    model_name="gpt-3.5-turbo",
    api_key="your-api-key"
)
adapter = OpenAIAdapter(config=config)
```

### Anthropic
```python
from lightagent import AnthropicAdapter, ModelConfig

config = ModelConfig(
    model_name="claude-3-sonnet-20240229",
    api_key="your-api-key"
)
adapter = AnthropicAdapter(config=config)
```

### Ollama (Local)
```python
from lightagent import OllamaAdapter, ModelConfig

config = ModelConfig(
    model_name="llama2",
    api_base="http://localhost:11434"
)
adapter = OllamaAdapter(config=config)
```

### Mock (Testing)
```python
from lightagent import MockAdapter, ModelConfig

config = ModelConfig(model_name="mock")
adapter = MockAdapter(config=config)
```

## Common Tasks

### Creating a Custom Tool

```python
from lightagent import BaseTool, ToolExecutionResult

class MyTool(BaseTool):
    name = "my_tool"
    description = "My custom tool"

    async def execute(self, **kwargs):
        return ToolExecutionResult(
            success=True,
            result="Done"
        )

agent.add_tool(MyTool())
```

### Creating Custom Middleware

```python
from lightagent import BaseMiddleware, MiddlewareContext

class MyMiddleware(BaseMiddleware):
    name = "my_middleware"

    async def process_pre(self, context: MiddlewareContext):
        # Pre-processing
        context.message = context.message.upper()
        return context

    async def process_post(self, context: MiddlewareContext):
        # Post-processing
        return context

agent.middlewares.add(MyMiddleware())
```

### Setting Up Multi-Agent System

```python
from lightagent import Agent, AgentConfig, MessageBus

# Create message bus
bus = MessageBus()

# Create agents
agent1 = Agent(config=AgentConfig(name="agent1"), ...)
agent2 = Agent(config=AgentConfig(name="agent2"), ...)

# Initialize and register
await agent1.initialize()
await agent2.initialize()
await bus.register_agent("agent1", agent1)
await bus.register_agent("agent2", agent2)

# Communicate
await agent1.send_message("agent2", message)
```

## Troubleshooting

### Common Issues

**Import errors**
```bash
# Install dependencies
pip install -r requirements.txt
```

**API key errors**
```bash
# Set environment variables
export OPENAI_API_KEY="your-key"
export ANTHROPIC_API_KEY="your-key"
```

**Async errors**
```python
# Always use asyncio.run()
asyncio.run(main())
```

**Model not responding**
- Check API key is valid
- Verify network connection
- Check rate limits
- Use MockAdapter for testing

## Best Practices

1. **Always use async/await** for I/O operations
2. **Initialize agents** before use
3. **Use environment variables** for API keys
4. **Add middleware** for production (logging, caching, etc.)
5. **Test with MockAdapter** first
6. **Handle errors** in tools gracefully
7. **Use type hints** for better IDE support
8. **Reset context** when starting new conversations

## Performance Tips

1. **Use CacheMiddleware** for repeated queries
2. **Use RateLimitMiddleware** to avoid API limits
3. **Enable streaming** for long responses
4. **Batch tool calls** when possible
5. **Use local models** (Ollama) for faster inference

## Contributing

Want to contribute? Here's how:

1. Check existing issues
2. Fork the repository
3. Create a feature branch
4. Add tests for new features
5. Update documentation
6. Submit a pull request

## License

MIT License - See LICENSE file

## Support

- GitHub Issues: Report bugs and request features
- Examples: Check `../examples/` directory
- Documentation: You're here!

## Changelog

### Version 0.1.0
- Initial release
- Core agent framework
- Tool calling system (MCP, Function, RAG)
- Middleware pipeline
- A2A protocol
- Multi-model support with function calling
- OpenAI, Anthropic, Ollama adapters
- Comprehensive examples
