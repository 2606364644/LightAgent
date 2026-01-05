"""
LightAgent - A lightweight, modular Python Agent framework

Features:
- Modular agent configuration
- Tool calling (MCP, Function Call, RAG)
- Middleware pipeline
- A2A (Agent-to-Agent) protocol
- Memory storage system
- Multi-model support
- Async/await for high performance
"""

from .core.agent import Agent, AgentContext
from .core.protocol import A2AMessage, MessageBus, MessageType
from .core.middleware import (
    MiddlewareManager,
    BaseMiddleware,
    LoggingMiddleware,
    RateLimitMiddleware,
    CacheMiddleware,
    ValidationMiddleware,
    RetryMiddleware
)
from .memory.base import BaseMemoryStore, AgentEvent, EventType
from .memory.stores import (
    InMemoryMemoryStore,
    FileMemoryStore,
    SQLiteMemoryStore,
    MySQLMemoryStore,
    PostgreSQLMemoryStore
)
from .models.base import BaseModelAdapter, ModelConfig, ModelRegistry
from .models.providers import (
    OpenAIAdapter,
    AnthropicAdapter,
    MockAdapter,
    OllamaAdapter
)
from .tools.base import BaseTool, ToolRegistry, FunctionTool
from .tools.mcp_tool import MCPTool, MCPToolConfig, MCPMultiTool
from .tools.function_tool import (
    FunctionCallTool,
    FunctionCallConfig,
    FunctionBuilder,
    tool
)
from .tools.rag_tool import (
    RAGTool,
    RAGConfig,
    Document,
    KnowledgeBase
)

__version__ = "0.1.0"
__author__ = "LightAgent Team"

__all__ = [
    # Core
    "Agent",
    "AgentContext",

    # Protocol
    "A2AMessage",
    "MessageBus",
    "MessageType",

    # Middleware
    "MiddlewareManager",
    "BaseMiddleware",
    "LoggingMiddleware",
    "RateLimitMiddleware",
    "CacheMiddleware",
    "ValidationMiddleware",
    "RetryMiddleware",

    # Memory
    "BaseMemoryStore",
    "AgentEvent",
    "EventType",
    "InMemoryMemoryStore",
    "FileMemoryStore",
    "SQLiteMemoryStore",
    "MySQLMemoryStore",
    "PostgreSQLMemoryStore",

    # Models
    "BaseModelAdapter",
    "ModelConfig",
    "ModelRegistry",
    "OpenAIAdapter",
    "AnthropicAdapter",
    "MockAdapter",
    "OllamaAdapter",

    # Tools
    "BaseTool",
    "ToolRegistry",
    "FunctionTool",
    "MCPTool",
    "MCPToolConfig",
    "MCPMultiTool",
    "FunctionCallTool",
    "FunctionCallConfig",
    "FunctionBuilder",
    "tool",
    "RAGTool",
    "RAGConfig",
    "Document",
    "KnowledgeBase",
]
