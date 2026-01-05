"""
MCP (Model Context Protocol) Tool Implementation
"""
from typing import Any, Dict, List, Optional
from pydantic import BaseModel
import asyncio
import json

from .base import BaseTool, ToolExecutionResult, ToolSchema


class MCPToolConfig(BaseModel):
    """Configuration for MCP tool"""
    server_url: str
    api_key: Optional[str] = None
    timeout: float = 30.0
    headers: Dict[str, str] = {}


class MCPTool(BaseTool):
    """
    MCP Tool implementation
    Allows calling external MCP servers
    """

    def __init__(
        self,
        name: str,
        description: str,
        mcp_config: MCPToolConfig,
        tool_schema: Optional[ToolSchema] = None
    ):
        super().__init__()
        self.name = name
        self.description = description
        self.mcp_config = mcp_config
        self._schema = tool_schema

    async def initialize(self):
        """Initialize MCP connection"""
        # Prepare HTTP session for MCP calls
        try:
            import aiohttp
            self._session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=self.mcp_config.timeout),
                headers=self.mcp_config.headers
            )
        except ImportError:
            raise ImportError("aiohttp is required for MCP tools. Install: pip install aiohttp")

    async def execute(self, **kwargs) -> ToolExecutionResult:
        """Execute MCP tool call"""
        try:
            url = f"{self.mcp_config.server_url}/tools/{self.name}"

            headers = {}
            if self.mcp_config.api_key:
                headers["Authorization"] = f"Bearer {self.mcp_config.api_key}"

            async with self._session.post(
                url,
                json=kwargs,
                headers=headers
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    return ToolExecutionResult(
                        success=True,
                        result=data.get("result", data)
                    )
                else:
                    error_text = await response.text()
                    return ToolExecutionResult(
                        success=False,
                        error=f"MCP error {response.status}: {error_text}"
                    )

        except Exception as e:
            return ToolExecutionResult(
                success=False,
                error=str(e)
            )

    def get_schema(self) -> ToolSchema:
        """Get tool schema"""
        if self._schema:
            return self._schema

        return ToolSchema(
            name=self.name,
            description=self.description,
            parameters={
                "type": "object",
                "properties": {},
                "title": f"{self.name}_arguments"
            }
        )

    async def close(self):
        """Close MCP connection"""
        if hasattr(self, '_session'):
            await self._session.close()


class MCPMultiTool(BaseTool):
    """
    MCP Multi-tool that can discover and call multiple tools from an MCP server
    """

    def __init__(self, config: MCPToolConfig):
        super().__init__()
        self.mcp_config = config
        self.available_tools: Dict[str, ToolSchema] = {}

    async def initialize(self):
        """Initialize and discover available tools"""
        try:
            import aiohttp
            self._session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=self.mcp_config.timeout),
                headers=self.mcp_config.headers
            )
        except ImportError:
            raise ImportError("aiohttp is required for MCP tools. Install: pip install aiohttp")

        # Discover available tools
        await self._discover_tools()

    async def _discover_tools(self):
        """Discover available tools from MCP server"""
        try:
            headers = {}
            if self.mcp_config.api_key:
                headers["Authorization"] = f"Bearer {self.mcp_config.api_key}"

            async with self._session.get(
                f"{self.mcp_config.server_url}/tools",
                headers=headers
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    for tool_info in data.get("tools", []):
                        schema = ToolSchema(**tool_info)
                        self.available_tools[schema.name] = schema
        except Exception as e:
            print(f"Error discovering MCP tools: {e}")

    async def execute(self, tool_name: str, **kwargs) -> ToolExecutionResult:
        """Execute a specific MCP tool"""
        try:
            url = f"{self.mcp_config.server_url}/tools/{tool_name}"

            headers = {}
            if self.mcp_config.api_key:
                headers["Authorization"] = f"Bearer {self.mcp_config.api_key}"

            async with self._session.post(
                url,
                json=kwargs,
                headers=headers
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    return ToolExecutionResult(
                        success=True,
                        result=data.get("result", data)
                    )
                else:
                    error_text = await response.text()
                    return ToolExecutionResult(
                        success=False,
                        error=f"MCP error {response.status}: {error_text}"
                    )

        except Exception as e:
            return ToolExecutionResult(
                success=False,
                error=str(e)
            )

    def get_schema(self) -> ToolSchema:
        """Get schema for the multi-tool"""
        return ToolSchema(
            name="mcp_multi_tool",
            description=f"MCP server with {len(self.available_tools)} tools",
            parameters={
                "type": "object",
                "properties": {
                    "tool_name": {
                        "type": "string",
                        "description": "Name of the tool to execute"
                    },
                    "parameters": {
                        "type": "object",
                        "description": "Parameters for the tool"
                    }
                },
                "required": ["tool_name"]
            }
        )

    def list_tools(self) -> List[str]:
        """List available MCP tools"""
        return list(self.available_tools.keys())

    def get_tool_schema(self, tool_name: str) -> Optional[ToolSchema]:
        """Get schema for a specific tool"""
        return self.available_tools.get(tool_name)

    async def close(self):
        """Close MCP connection"""
        if hasattr(self, '_session'):
            await self._session.close()
