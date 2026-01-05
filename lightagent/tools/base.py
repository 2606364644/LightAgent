"""
Base tool definitions and interfaces
"""
from typing import Any, Dict, List, Optional, TypeVar, Generic
from pydantic import BaseModel, Field
from abc import ABC, abstractmethod
import asyncio


class ToolSchema(BaseModel):
    """Tool schema for function calling"""
    name: str
    description: str
    parameters: Dict[str, Any] = Field(default_factory=dict)
    returns: Dict[str, Any] = Field(default_factory=dict)


class ToolExecutionResult(BaseModel):
    """Result of tool execution"""
    success: bool
    result: Any = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class BaseTool(ABC):
    """Base class for all tools"""

    name: str = ""
    description: str = ""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}

    @abstractmethod
    async def execute(self, **kwargs) -> ToolExecutionResult:
        """Execute the tool with given parameters"""
        pass

    async def initialize(self):
        """Initialize the tool (optional)"""
        pass

    def is_available(self) -> bool:
        """Check if tool is available for use"""
        return True

    def get_schema(self) -> ToolSchema:
        """Get tool schema for function calling"""
        return ToolSchema(
            name=self.name,
            description=self.description
        )


class FunctionTool(BaseTool):
    """Wrap a Python function as a tool"""

    def __init__(
        self,
        func: callable,
        name: Optional[str] = None,
        description: Optional[str] = None,
        parameters: Optional[Dict[str, Any]] = None
    ):
        super().__init__()
        self.func = func
        self.name = name or func.__name__
        self.description = description or func.__doc__ or f"Tool: {self.name}"
        self.parameters = parameters or {}

    async def execute(self, **kwargs) -> ToolExecutionResult:
        try:
            if asyncio.iscoroutinefunction(self.func):
                result = await self.func(**kwargs)
            else:
                result = self.func(**kwargs)

            return ToolExecutionResult(
                success=True,
                result=result
            )
        except Exception as e:
            return ToolExecutionResult(
                success=False,
                error=str(e)
            )

    def get_schema(self) -> ToolSchema:
        return ToolSchema(
            name=self.name,
            description=self.description,
            parameters=self.parameters
        )


class ToolRegistry(BaseModel):
    """Registry for managing tools"""

    tools: Dict[str, BaseTool] = Field(default_factory=dict)

    model_config = {"arbitrary_types_allowed": True}

    def register(self, tool: BaseTool):
        """Register a tool"""
        self.tools[tool.name] = tool

    def unregister(self, name: str):
        """Unregister a tool"""
        if name in self.tools:
            del self.tools[name]

    def get(self, name: str) -> Optional[BaseTool]:
        """Get a tool by name"""
        return self.tools.get(name)

    def list_tools(self) -> List[str]:
        """List all registered tool names"""
        return list(self.tools.keys())

    def get_schemas(self) -> List[ToolSchema]:
        """Get all tool schemas"""
        return [tool.get_schema() for tool in self.tools.values()]

    async def execute(
        self,
        name: str,
        **kwargs
    ) -> ToolExecutionResult:
        """Execute a tool by name"""
        tool = self.get(name)
        if not tool:
            return ToolExecutionResult(
                success=False,
                error=f"Tool '{name}' not found"
            )

        return await tool.execute(**kwargs)
