"""
Core Agent implementation with modular configuration support
"""
from typing import Any, Dict, List, Optional, Callable, TypeVar, Generic
from pydantic import BaseModel, Field
import asyncio
import uuid
from datetime import datetime
from contextlib import asynccontextmanager

from ..models.base import BaseModelAdapter
from ..models.schemas import get_function_call_adapter
from ..tools.base import BaseTool
from ..memory.base import BaseMemoryStore, AgentEvent, EventType
from .middleware import MiddlewareManager
from .protocol import A2AMessage, MessageBus


T = TypeVar('T')


class AgentContext(BaseModel):
    """Execution context for agent"""
    session_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    conversation_history: List[Dict[str, Any]] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    current_iteration: int = 0


class Agent(BaseModel):
    """
    Modular Agent implementation supporting:
    - Multiple tools (MCP, Function Call, RAG)
    - Middleware pipeline (pre/post processing)
    - Sub-agent delegation
    - A2A protocol communication
    - Memory storage for events
    """
    # Core configuration
    name: str
    model_adapter: BaseModelAdapter
    model_provider: str = "openai"
    description: str = ""
    system_prompt: Optional[str] = None
    max_iterations: int = 10
    timeout: float = 30.0
    enable_middleware: bool = True
    auto_tool_prompt: bool = True
    tool_prompt_template: Optional[str] = None
    enable_memory: bool = True  # Enable/disable memory storage

    # Components
    tools: Dict[str, BaseTool] = Field(default_factory=dict)
    middlewares: MiddlewareManager = Field(default_factory=MiddlewareManager)
    sub_agents: Dict[str, 'Agent'] = Field(default_factory=dict)
    message_bus: Optional[MessageBus] = None
    memory_store: Optional[BaseMemoryStore] = None

    # Runtime state
    context: Optional[AgentContext] = None

    class Config:
        arbitrary_types_allowed = True

    @classmethod
    def create(
        cls,
        name: str,
        model_adapter: BaseModelAdapter,
        system_prompt: Optional[str] = None,
        tools: Optional[List[BaseTool]] = None,
        middlewares: Optional[MiddlewareManager] = None,
        memory_store: Optional[BaseMemoryStore] = None,
        max_iterations: int = 10,
        model_provider: str = "openai",
        auto_tool_prompt: bool = True,
        **kwargs
    ) -> 'Agent':
        """
        Simplified agent creation

        Args:
            name: Agent name
            model_adapter: Model adapter instance
            system_prompt: Optional system prompt
            tools: Optional list of tools to add
            middlewares: Optional middleware manager
            memory_store: Optional memory store instance
            max_iterations: Maximum reasoning iterations
            model_provider: Model provider name
            auto_tool_prompt: Auto-generate tool descriptions
            **kwargs: Additional parameters (description, timeout, etc.)

        Returns:
            Configured Agent instance

        Example:
            ```python
            agent = Agent.create(
                name="assistant",
                model_adapter=OpenAIAdapter(...),
                system_prompt="You are helpful",
                tools=[weather_tool, calc_tool],
                memory_store=SQLiteMemoryStore()
            )
            ```
        """
        # Create agent with all parameters
        agent = cls(
            name=name,
            model_adapter=model_adapter,
            system_prompt=system_prompt,
            max_iterations=max_iterations,
            model_provider=model_provider,
            auto_tool_prompt=auto_tool_prompt,
            memory_store=memory_store,
            **kwargs
        )

        # Add tools if provided
        if tools:
            for tool in tools:
                agent.add_tool(tool)

        # Set middlewares if provided
        if middlewares:
            agent.middlewares = middlewares

        return agent

    def __init__(self, **data):
        super().__init__(**data)
        if self.context is None:
            self.context = AgentContext()

    async def initialize(self):
        """Initialize agent and all components"""
        # Initialize memory store
        if self.memory_store and self.enable_memory:
            await self.memory_store.initialize()
            await self._record_event(
                EventType.AGENT_INIT,
                message="Agent initialized"
            )

        # Initialize tools
        for tool in self.tools.values():
            if hasattr(tool, 'initialize'):
                await tool.initialize()

        # Initialize middlewares
        await self.middlewares.initialize(self)

        # Initialize sub-agents
        for sub_agent in self.sub_agents.values():
            await sub_agent.initialize()

        # Register with message bus if provided
        if self.message_bus:
            await self.message_bus.register_agent(self.name, self)

    async def _record_event(
        self,
        event_type: EventType,
        **data
    ):
        """
        Record an event to memory store

        Args:
            event_type: Type of event
            **data: Event data as keyword arguments
        """
        if not (self.memory_store and self.enable_memory):
            return

        event = AgentEvent(
            agent_name=self.name,
            session_id=self.context.session_id if self.context else "unknown",
            event_type=event_type,
            data=data,
            metadata={}
        )
        await self.memory_store.store(event)

    @asynccontextmanager
    async def _track(
        self,
        event_type: EventType,
        auto_error: bool = True,
        **initial_data
    ):
        """
        Automatically track operation lifecycle (start/success/failure)

        Args:
            event_type: Event type to track
            auto_error: Whether to re-raise exception (default True)
            **initial_data: Initial data to include in events

        Example:
            ```python
            async with self._track(EventType.TOOL_CALL_START, tool_name="search"):
                result = await tool.execute()
            ```
        """
        await self._record_event(event_type, status="started", **initial_data)

        try:
            yield
            await self._record_event(event_type, status="completed", **initial_data)
        except Exception as e:
            await self._record_event(
                EventType.AGENT_ERROR,
                status="failed",
                error=str(e),
                error_type=type(e).__name__,
                **initial_data
            )
            if auto_error:
                raise

    async def run(
        self,
        message: str,
        context: Optional[AgentContext] = None
    ) -> Dict[str, Any]:
        """
        Main execution loop for agent

        Args:
            message: User input message
            context: Optional agent context

        Returns:
            Agent response
        """
        if context:
            self.context = context

        # Record user message event (simplified with **kwargs)
        await self._record_event(
            EventType.USER_MESSAGE,
            message=message,
            message_length=len(message)
        )

        self.context.conversation_history.append({
            "role": "user",
            "content": message,
            "timestamp": datetime.now().isoformat()
        })

        try:
            # Pre-processing middleware
            processed_message = message
            if self.enable_middleware:
                await self._record_event(
                    EventType.MIDDLEWARE_PRE,
                    original_message=message
                )
                processed_message = await self.middlewares.process_pre(
                    self, processed_message
                )

            # Main reasoning loop
            result = await self._reasoning_loop(processed_message)

            # Post-processing middleware
            if self.enable_middleware:
                result = await self.middlewares.process_post(self, result)
                await self._record_event(
                    EventType.MIDDLEWARE_POST,
                    response_length=len(result.get("response", ""))
                )

            # Add to conversation history
            self.context.conversation_history.append({
                "role": "assistant",
                "content": result.get("response", ""),
                "timestamp": datetime.now().isoformat(),
                "tool_calls": result.get("tool_calls", [])
            })

            # Record model response event (simplified with **kwargs)
            await self._record_event(
                EventType.MODEL_RESPONSE,
                response=result.get("response", ""),
                tool_calls_count=len(result.get("tool_calls", [])),
                iterations=result.get("iterations", 0),
                success=result.get("success", True)
            )

            return result

        except Exception as e:
            error_result = {
                "response": f"Error: {str(e)}",
                "error": str(e),
                "success": False
            }

            # Record error event (simplified with **kwargs)
            await self._record_event(
                EventType.AGENT_ERROR,
                error=str(e),
                error_type=type(e).__name__
            )

            self.context.conversation_history.append({
                "role": "error",
                "content": str(e),
                "timestamp": datetime.now().isoformat()
            })
            return error_result

    async def call(
        self,
        user_prompt: str,
        system_prompt: Optional[str] = None,
        tools: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Direct model call with prompt

        Args:
            user_prompt: User message/prompt
            system_prompt: Optional override system prompt
            tools: Optional list of tool names to use (default: all configured tools)

        Returns:
            Agent response
        """
        # Save original system prompt
        original_system_prompt = self.system_prompt

        # Override system prompt if provided
        if system_prompt is not None:
            self.system_prompt = system_prompt

        # Temporarily filter tools if specified
        original_tools = None
        if tools is not None:
            original_tools = list(self.tools.keys())
            active_tools = {
                name: tool for name, tool in self.tools.items()
                if name in tools
            }
            self.tools = active_tools

        try:
            # Execute with single call (no reasoning loop)
            result = await self.run(user_prompt)
            return result
        finally:
            # Restore original system prompt
            self.system_prompt = original_system_prompt

            # Restore original tools if they were filtered
            if original_tools is not None:
                for name in original_tools:
                    if name not in self.tools and name in self.__dict__.get('_original_tools', {}):
                        self.tools[name] = self._original_tools[name]

    def _generate_tool_prompt(self) -> str:
        """
        Generate tool descriptions for prompt

        Returns:
            Formatted tool descriptions
        """
        if not self.tools:
            return ""

        # Use custom template if provided
        if self.tool_prompt_template:
            template = self.tool_prompt_template
        else:
            # Default template
            template = """You have access to the following tools:

{tool_descriptions}

When you need to use a tool, respond with a tool call in the appropriate format.
Only use tools when necessary. If you can answer directly, do so."""

        # Generate tool descriptions
        tool_descriptions = []

        for tool_name, tool in self.tools.items():
            if not tool.is_available():
                continue

            schema = tool.get_schema()

            # Build tool description
            desc = f"\n## {tool_name}\n"
            desc += f"**Description**: {schema.description}\n"

            # Add parameters if available
            if hasattr(schema, 'parameters') and schema.parameters:
                params = schema.parameters
                if isinstance(params, dict):
                    desc += "**Parameters**:\n"

                    properties = params.get('properties', {})
                    required = params.get('required', [])

                    for param_name, param_info in properties.items():
                        req_marker = " (required)" if param_name in required else " (optional)"
                        param_desc = param_info.get('description', param_info.get('type', 'unknown'))
                        desc += f"- `{param_name}`{req_marker}: {param_desc}\n"

            tool_descriptions.append(desc)

        # Format template
        if tool_descriptions:
            return template.format(tool_descriptions="".join(tool_descriptions))
        else:
            return ""

    def _build_system_prompt(self) -> str:
        """
        Build complete system prompt with tool descriptions

        Returns:
            Complete system prompt
        """
        base_prompt = self.system_prompt or ""

        # Add tool descriptions if enabled
        if self.auto_tool_prompt:
            tool_prompt = self._generate_tool_prompt()
            if tool_prompt:
                if base_prompt:
                    return f"{base_prompt}\n\n{tool_prompt}"
                else:
                    return tool_prompt

        return base_prompt

    async def _reasoning_loop(
        self,
        message: str
    ) -> Dict[str, Any]:
        """
        Core reasoning loop with tool calling support
        """
        self.context.current_iteration = 0
        final_response = None

        # Get function call adapter for the model provider
        fc_adapter = get_function_call_adapter(self.model_provider)

        while self.context.current_iteration < self.max_iterations:
            self.context.current_iteration += 1

            # Prepare messages for model
            messages = self._prepare_messages(message, final_response)

            # Get available tools schema
            tools_schema = [
                tool.get_schema()
                for tool in self.tools.values()
                if tool.is_available()
            ]

            # Convert tool schemas to provider-specific format
            provider_tools_schema = None
            if tools_schema:
                # Convert to dict format
                tools_schema_dicts = [
                    schema.model_dump() if hasattr(schema, 'model_dump') else schema
                    for schema in tools_schema
                ]
                # Convert to provider format
                provider_tools_schema = fc_adapter.convert_schemas(tools_schema_dicts)

            # Call model
            model_response = await self.model_adapter.call(
                messages=messages,
                tools=provider_tools_schema if provider_tools_schema else None,
                temperature=0.7
            )

            # Check if model wants to call tools
            raw_tool_calls = model_response.get("tool_calls", [])

            # Parse tool calls from provider format to standard format
            tool_calls = fc_adapter.parse_tool_calls(raw_tool_calls) if raw_tool_calls else []

            if not tool_calls:
                # No tool calls, return final response
                return {
                    "response": model_response.get("content", ""),
                    "tool_calls": [],
                    "iterations": self.context.current_iteration,
                    "success": True
                }

            # Execute tool calls
            tool_results = []
            for tool_call in tool_calls:
                result = await self._execute_tool_call(tool_call)
                tool_results.append(result)

                # Check if we should delegate to sub-agent
                if result.get("delegate_to"):
                    sub_agent_name = result["delegate_to"]
                    if sub_agent_name in self.sub_agents:
                        sub_response = await self.sub_agents[sub_agent_name].run(
                            result.get("delegate_message", "")
                        )
                        return {
                            "response": sub_response.get("response", ""),
                            "tool_calls": tool_calls,
                            "tool_results": tool_results,
                            "sub_agent": sub_agent_name,
                            "iterations": self.context.current_iteration,
                            "success": True
                        }

            # Update final response with tool results
            final_response = model_response.get("content", "")

        # Max iterations reached
        return {
            "response": final_response or "Maximum iterations reached",
            "tool_calls": tool_calls if tool_calls else [],
            "iterations": self.context.current_iteration,
            "success": True
        }

    async def _execute_tool_call(
        self,
        tool_call: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute a single tool call"""
        tool_name = tool_call.get("name")
        tool_args = tool_call.get("arguments", {})

        # Check if tool exists
        if tool_name not in self.tools:
            error_msg = f"Tool '{tool_name}' not found"
            await self._record_event(
                EventType.TOOL_CALL_ERROR,
                tool_name=tool_name,
                error=error_msg
            )
            return {
                "tool": tool_name,
                "error": error_msg,
                "success": False
            }

        tool = self.tools[tool_name]

        # Use _track context manager for automatic lifecycle tracking
        async with self._track(EventType.TOOL_CALL_START, tool_name=tool_name, arguments=tool_args):
            result = await tool.execute(**tool_args)

            # Manually record success with result details
            await self._record_event(
                EventType.TOOL_CALL_SUCCESS,
                tool_name=tool_name,
                result=str(result)[:500]  # Limit result size
            )

            return {
                "tool": tool_name,
                "result": result,
                "success": True
            }

    def _prepare_messages(
        self,
        user_message: str,
        previous_response: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Prepare message list for model API

        Automatically includes:
        1. System prompt with tool descriptions
        2. Conversation history
        3. Current user message

        Args:
            user_message: Current user message
            previous_response: Previous model response (for multi-turn)

        Returns:
            List of message dictionaries
        """
        messages = []

        # Build complete system prompt (including tool descriptions)
        system_prompt = self._build_system_prompt()

        # Add system prompt
        if system_prompt:
            messages.append({
                "role": "system",
                "content": system_prompt
            })

        # Add conversation history (excluding the current message that was just added)
        history_to_include = self.context.conversation_history[:-1] if self.context.conversation_history else []

        for msg in history_to_include:
            if msg["role"] in ["user", "assistant"]:
                content = msg.get("content", "")
                # Skip tool_call messages for models that don't support them
                if content or msg.get("tool_calls"):
                    messages.append({
                        "role": msg["role"],
                        "content": content
                    })

        # Add current message
        if user_message:
            messages.append({
                "role": "user",
                "content": user_message
            })

        return messages

    async def send_message(
        self,
        to_agent: str,
        message: A2AMessage
    ) -> Optional[A2AMessage]:
        """Send message to another agent via A2A protocol"""
        if not self.message_bus:
            raise RuntimeError("Message bus not configured")

        return await self.message_bus.send(
            from_agent=self.name,
            to_agent=to_agent,
            message=message
        )

    async def receive_message(self, message: A2AMessage) -> Optional[A2AMessage]:
        """Handle incoming message from another agent"""
        # Process the message
        response = await self.run(message.content)

        # Create response message
        return A2AMessage(
            from_agent=self.name,
            to_agent=message.from_agent,
            content=response.get("response", ""),
            message_type=A2AMessage.MessageType.RESPONSE,
            reply_to=message.message_id
        )

    def add_tool(self, tool: BaseTool):
        """Add a tool to this agent"""
        self.tools[tool.name] = tool

    def add_sub_agent(self, name: str, agent: 'Agent'):
        """Add a sub-agent for delegation"""
        self.sub_agents[name] = agent

    def add_middleware(self, middleware: Callable, position: str = "after"):
        """Add middleware to the pipeline"""
        self.middlewares.add(middleware, position)

    def get_context(self) -> AgentContext:
        """Get current agent context"""
        return self.context

    def reset_context(self):
        """Reset conversation context"""
        self.context = AgentContext()

    async def get_memory(
        self,
        event_type: Optional[EventType] = None,
        limit: int = 100,
        session_id: Optional[str] = None
    ) -> List[AgentEvent]:
        """
        Retrieve events from memory

        Args:
            event_type: Filter by event type
            limit: Maximum number of events
            session_id: Filter by session ID

        Returns:
            List of events
        """
        if not self.memory_store:
            raise RuntimeError("Memory store not configured")

        return await self.memory_store.retrieve(
            agent_name=self.name,
            session_id=session_id or (self.context.session_id if self.context else None),
            event_type=event_type,
            limit=limit
        )

    async def search_memory(
        self,
        query: str,
        limit: int = 10
    ) -> List[AgentEvent]:
        """
        Search memory for events

        Args:
            query: Search query
            limit: Maximum results

        Returns:
            Matching events
        """
        if not self.memory_store:
            raise RuntimeError("Memory store not configured")

        return await self.memory_store.search(
            query=query,
            agent_name=self.name,
            session_id=self.context.session_id if self.context else None,
            limit=limit
        )

    async def get_memory_stats(self) -> Dict[str, Any]:
        """
        Get memory statistics

        Returns:
            Statistics dictionary
        """
        if not self.memory_store:
            raise RuntimeError("Memory store not configured")

        return await self.memory_store.get_stats(
            agent_name=self.name,
            session_id=self.context.session_id if self.context else None
        )

    async def clear_memory(self, session_id: Optional[str] = None):
        """
        Clear memory

        Args:
            session_id: Clear specific session, or all if None
        """
        if not self.memory_store:
            raise RuntimeError("Memory store not configured")

        await self.memory_store.clear(
            agent_name=self.name,
            session_id=session_id
        )