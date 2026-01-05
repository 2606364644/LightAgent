# LightAgent Project Structure

## Directory Layout

```
LightAgent/
├── lightagent/              # Main package directory
│   ├── __init__.py         # Package exports
│   ├── core/               # Core agent components
│   │   ├── __init__.py
│   │   ├── agent.py        # Agent implementation
│   │   ├── protocol.py     # A2A protocol & message bus
│   │   └── middleware.py   # Middleware system
│   ├── models/             # Model adapters
│   │   ├── __init__.py
│   │   ├── base.py         # Base adapter interface
│   │   └── providers.py    # OpenAI, Anthropic, Ollama, Mock
│   └── tools/              # Tool implementations
│       ├── __init__.py
│       ├── base.py         # Base tool interface
│       ├── mcp_tool.py     # MCP tools
│       ├── function_tool.py # Function calling tools
│       └── rag_tool.py     # RAG tools
│
├── examples/               # Usage examples
│   ├── simple_demo.py      # Minimal demo
│   ├── basic_agent.py      # Basic agent with tools
│   ├── rag_agent.py        # RAG-enabled agent
│   ├── multi_agent.py      # Multi-agent collaboration
│   └── middleware_agent.py # Middleware pipeline demo
│
├── tests/                  # Test files
│   ├── __init__.py
│   └── test_agent.py       # Unit tests
│
├── requirements.txt        # Python dependencies
├── setup.py               # Package setup configuration
├── README.md              # Main documentation
├── QUICKSTART.md          # Quick start guide
└── config_example.yaml    # Configuration example
```

## Core Components

### 1. Agent (`lightagent/core/agent.py`)

Main agent class with reasoning loop:
- Modular configuration (AgentConfig)
- Tool execution
- Sub-agent delegation
- Context management
- Async/await support

Key classes:
- `Agent`: Main agent implementation
- `AgentConfig`: Agent configuration model
- `AgentContext`: Execution context

### 2. Protocol (`lightagent/core/protocol.py`)

A2A (Agent-to-Agent) communication:
- Message passing between agents
- Broadcast support
- Task delegation
- Message history

Key classes:
- `A2AMessage`: Message model
- `MessageBus`: Communication bus
- `MessageType`: Message types (REQUEST, RESPONSE, etc.)

### 3. Middleware (`lightagent/core/middleware.py`)

Pre/post-processing pipeline:
- Built-in middleware
- Custom middleware support
- Phases (pre/post)
- Chaining

Key classes:
- `MiddlewareManager`: Pipeline manager
- `BaseMiddleware`: Base middleware class
- Built-ins: Logging, RateLimit, Cache, Validation, Retry

### 4. Models (`lightagent/models/`)

Multi-model support:
- Abstract adapter interface
- Provider implementations
- Streaming support
- Tool calling

Key classes:
- `BaseModelAdapter`: Base adapter
- `OpenAIAdapter`: OpenAI models
- `AnthropicAdapter`: Claude models
- `OllamaAdapter`: Local models
- `MockAdapter`: Testing adapter

### 5. Tools (`lightagent/tools/`)

Tool system:

#### Base (`base.py`)
- `BaseTool`: Tool interface
- `ToolRegistry`: Tool management
- `FunctionTool`: Wrap functions

#### MCP (`mcp_tool.py`)
- `MCPTool`: Single MCP tool
- `MCPMultiTool`: Multi-tool MCP server

#### Function (`function_tool.py`)
- `FunctionCallTool`: Function calling with prompts
- `FunctionBuilder`: Helper to create tools
- `@tool`: Decorator

#### RAG (`rag_tool.py`)
- `RAGTool`: Retrieval-augmented generation
- `KnowledgeBase`: Document management
- `Document`: Document model
- Embedding and vector store interfaces

## Usage Patterns

### Pattern 1: Basic Agent

```python
agent = Agent(
    config=AgentConfig(name="assistant"),
    model_adapter=OpenAIAdapter(config=ModelConfig(...))
)
await agent.initialize()
result = await agent.run("Hello")
```

### Pattern 2: Agent with Tools

```python
tool = FunctionBuilder.create_tool(my_func)
agent.add_tool(tool)
agent.config.tools = ["my_func"]
```

### Pattern 3: Multi-Agent

```python
bus = MessageBus()
await bus.register_agent("agent1", agent1)
await bus.register_agent("agent2", agent2)
await agent1.send_message("agent2", message)
```

### Pattern 4: Middleware

```python
manager = MiddlewareManager()
manager.add(LoggingMiddleware())
agent.middlewares = manager
```

## Key Features

### 1. Modular Configuration
- Configure tools, models, middleware independently
- Mix and match components
- Easy to extend

### 2. Tool Calling
- MCP: External tool servers
- Function Call: Python functions
- RAG: Semantic search

### 3. Async/Await
- All I/O operations are async
- High performance
- Non-blocking

### 4. Type Safety
- Pydantic models throughout
- Validation
- IDE autocomplete support

### 5. A2A Protocol
- Agent-to-agent communication
- Delegation
- Collaboration

### 6. Middleware Pipeline
- Pre-processing
- Post-processing
- Custom middleware

## Extension Points

### Custom Tools
```python
class MyTool(BaseTool):
    async def execute(self, **kwargs):
        return ToolExecutionResult(success=True, result=...)
```

### Custom Middleware
```python
class MyMiddleware(BaseMiddleware):
    async def process_pre(self, context):
        # Modify input
        return context

    async def process_post(self, context):
        # Modify output
        return context
```

### Custom Model Adapter
```python
class MyAdapter(BaseModelAdapter):
    async def call(self, messages, tools=None, **kwargs):
        # Call your model
        return {"content": "...", "tool_calls": [...]}
```

## Testing Strategy

1. Use `MockAdapter` for unit tests
2. Test tools independently
3. Test middleware pipeline
4. Integration tests with real models (optional)

See `tests/test_agent.py` for examples.

## Configuration

### Environment Variables
- `OPENAI_API_KEY`: OpenAI API key
- `ANTHROPIC_API_KEY`: Anthropic API key

### Config Files
- See `config_example.yaml` for full configuration options

## Dependencies

### Required
- `pydantic>=2.0.0`: Data validation
- `aiohttp>=3.9.0`: Async HTTP client

### Optional
- `openai>=1.0.0`: OpenAI models
- `anthropic>=0.18.0`: Claude models
- `sentence-transformers`: Embeddings (RAG)
- `chromadb`: Vector store (RAG)

## Performance Considerations

1. **Async I/O**: All model calls are async
2. **Caching**: Use CacheMiddleware for repeated queries
3. **Rate Limiting**: Use RateLimitMiddleware to avoid API limits
4. **Streaming**: Use streaming for long responses

## Best Practices

1. Always use `asyncio.run()` for async code
2. Initialize agents before use
3. Use environment variables for API keys
4. Add middleware for production agents
5. Test with MockAdapter first
6. Handle errors in tools
7. Use type hints for better IDE support

## Future Enhancements

Potential additions:
- [ ] More model providers (Gemini, Cohere, etc.)
- [ ] Advanced RAG (hybrid search, reranking)
- [ ] Agent memory/persistence
- [ ] Observability/tracing
- [ ] CLI tool
- [ ] Web UI
- [ ] Agent templates
- [ ] Tool marketplace

## Contributing

1. Add features in appropriate modules
2. Follow existing patterns
3. Add tests
4. Update documentation
5. Use type hints

## License

MIT License - See LICENSE file
