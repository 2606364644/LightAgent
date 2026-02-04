"""
Workflow Tool Management System

Manages tool pools for different workflow types with support for
global tools and workflow-specific tools.
"""
from typing import Any, Dict, List, Optional, Set
from pydantic import BaseModel, Field


class ToolPool(BaseModel):
    """
    A pool of tools that can be shared across workflows
    """
    name: str
    tools: Dict[str, Any] = Field(default_factory=dict)  # tool_name -> tool instance
    description: Optional[str] = None

    def add_tool(self, tool: Any, name: Optional[str] = None):
        """Add a tool to the pool"""
        tool_name = name or getattr(tool, 'name', str(id(tool)))
        self.tools[tool_name] = tool

    def get_tool(self, name: str) -> Optional[Any]:
        """Get a tool by name"""
        return self.tools.get(name)

    def remove_tool(self, name: str):
        """Remove a tool from the pool"""
        if name in self.tools:
            del self.tools[name]

    def list_tools(self) -> List[str]:
        """List all tool names"""
        return list(self.tools.keys())

    def get_tools(self) -> List[Any]:
        """Get all tools"""
        return list(self.tools.values())


class ToolRegistry(BaseModel):
    """
    Global tool registry for managing workflow tools

    Supports:
    - Global tool pool (shared by all workflows)
    - Workflow-specific tool pools
    - Tool inheritance and composition
    """

    # Global tools available to all workflows
    global_pool: ToolPool = Field(default_factory=lambda: ToolPool(name="global"))

    # Workflow-specific tool pools
    workflow_pools: Dict[str, ToolPool] = Field(default_factory=dict)

    class Config:
        arbitrary_types_allowed = True

    def create_workflow_pool(
        self,
        workflow_type: str,
        inherit_global: bool = True,
        description: Optional[str] = None
    ) -> ToolPool:
        """
        Create a tool pool for a specific workflow type

        Args:
            workflow_type: Type of workflow
            inherit_global: Whether to inherit from global pool
            description: Optional description

        Returns:
            ToolPool instance
        """
        pool = ToolPool(
            name=f"{workflow_type}_pool",
            description=description or f"Tools for {workflow_type} workflows"
        )

        # Store workflow-specific pool
        self.workflow_pools[workflow_type] = pool

        return pool

    def get_workflow_pool(self, workflow_type: str) -> Optional[ToolPool]:
        """Get tool pool for a workflow type"""
        return self.workflow_pools.get(workflow_type)

    def get_workflow_tools(
        self,
        workflow_type: str,
        include_global: bool = True
    ) -> List[Any]:
        """
        Get all tools for a workflow type

        Args:
            workflow_type: Type of workflow
            include_global: Whether to include global tools

        Returns:
            List of tools
        """
        tools = []

        # Add global tools first
        if include_global:
            tools.extend(self.global_pool.get_tools())

        # Add workflow-specific tools
        pool = self.get_workflow_pool(workflow_type)
        if pool:
            tools.extend(pool.get_tools())

        # Remove duplicates (keep workflow-specific versions)
        seen = set()
        unique_tools = []
        for tool in reversed(tools):
            tool_name = getattr(tool, 'name', str(id(tool)))
            if tool_name not in seen:
                seen.add(tool_name)
                unique_tools.append(tool)

        return list(reversed(unique_tools))

    def add_global_tool(self, tool: Any, name: Optional[str] = None):
        """
        Add a tool to the global pool

        Args:
            tool: Tool instance
            name: Optional tool name
        """
        self.global_pool.add_tool(tool, name)

    def add_workflow_tool(
        self,
        workflow_type: str,
        tool: Any,
        name: Optional[str] = None
    ):
        """
        Add a tool to a workflow-specific pool

        Args:
            workflow_type: Type of workflow
            tool: Tool instance
            name: Optional tool name
        """
        pool = self.get_workflow_pool(workflow_type)
        if not pool:
            pool = self.create_workflow_pool(workflow_type)

        pool.add_tool(tool, name)

    def register_tool_for_workflows(
        self,
        tool: Any,
        workflow_types: List[str],
        name: Optional[str] = None
    ):
        """
        Register a tool for multiple workflow types

        Args:
            tool: Tool instance
            workflow_types: List of workflow types
            name: Optional tool name
        """
        for workflow_type in workflow_types:
            self.add_workflow_tool(workflow_type, tool, name)

    def list_global_tools(self) -> List[str]:
        """List global tool names"""
        return self.global_pool.list_tools()

    def list_workflow_tools(self, workflow_type: str) -> List[str]:
        """List workflow-specific tool names"""
        pool = self.get_workflow_pool(workflow_type)
        return pool.list_tools() if pool else []

    def get_tool_info(self) -> Dict[str, Dict[str, Any]]:
        """
        Get information about all tools

        Returns:
            Dictionary with tool information
        """
        info = {
            'global': {
                'count': len(self.global_pool.tools),
                'tools': list(self.global_pool.tools.keys())
            }
        }

        for workflow_type, pool in self.workflow_pools.items():
            info[workflow_type] = {
                'count': len(pool.tools),
                'tools': list(pool.tools.keys())
            }

        return info


def create_default_tool_registry() -> ToolRegistry:
    """
    Create tool registry with common tools

    Returns:
        ToolRegistry with default configuration
    """
    registry = ToolRegistry()

    # Import common tools if available
    try:
        from lightagent.tools import FunctionBuilder, MCPTool, RAGTool

        # Add some common function tools to global pool
        # Note: These are examples, actual tools would be created by the user

        pass
    except ImportError:
        pass

    return registry


class WorkflowToolManager(BaseModel):
    """
    Manages tools for a specific workflow instance

    Combines global tools, workflow-type tools, and instance-specific tools.
    """

    workflow_type: str
    tool_registry: ToolRegistry
    instance_tools: Dict[str, Any] = Field(default_factory=dict)

    # Configuration
    use_global_tools: bool = True
    use_workflow_tools: bool = True
    use_instance_tools: bool = True

    class Config:
        arbitrary_types_allowed = True

    def add_tool(self, tool: Any, name: Optional[str] = None):
        """Add an instance-specific tool"""
        tool_name = name or getattr(tool, 'name', str(id(tool)))
        self.instance_tools[tool_name] = tool

    def get_tools(self) -> List[Any]:
        """Get all tools for this workflow instance"""
        tools = []

        # Global tools
        if self.use_global_tools:
            tools.extend(self.tool_registry.global_pool.get_tools())

        # Workflow-type tools
        if self.use_workflow_tools:
            pool = self.tool_registry.get_workflow_pool(self.workflow_type)
            if pool:
                tools.extend(pool.get_tools())

        # Instance-specific tools
        if self.use_instance_tools:
            tools.extend(self.instance_tools.values())

        # Remove duplicates (keep more specific versions)
        seen = set()
        unique_tools = []
        for tool in reversed(tools):
            tool_name = getattr(tool, 'name', str(id(tool)))
            if tool_name not in seen:
                seen.add(tool_name)
                unique_tools.append(tool)

        return list(reversed(unique_tools))

    def get_tool(self, name: str) -> Optional[Any]:
        """Get a specific tool by name"""
        # Check instance tools first
        if name in self.instance_tools:
            return self.instance_tools[name]

        # Check workflow pool
        if self.use_workflow_tools:
            pool = self.tool_registry.get_workflow_pool(self.workflow_type)
            if pool and name in pool.tools:
                return pool.tools[name]

        # Check global pool
        if self.use_global_tools and name in self.tool_registry.global_pool.tools:
            return self.tool_registry.global_pool.tools[name]

        return None

    def list_tools(self) -> List[str]:
        """List all available tool names"""
        tools = set()

        if self.use_global_tools:
            tools.update(self.tool_registry.global_pool.list_tools())

        if self.use_workflow_tools:
            pool = self.tool_registry.get_workflow_pool(self.workflow_type)
            if pool:
                tools.update(pool.list_tools())

        if self.use_instance_tools:
            tools.update(self.instance_tools.keys())

        return list(tools)
