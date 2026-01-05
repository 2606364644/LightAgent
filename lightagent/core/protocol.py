"""
A2A (Agent-to-Agent) Protocol Implementation
"""
from typing import Any, Dict, List, Optional, Callable
from pydantic import BaseModel, Field
from enum import Enum
import asyncio
import uuid
from datetime import datetime
import json


class MessageType(str, Enum):
    """Message types in A2A protocol"""
    REQUEST = "request"
    RESPONSE = "response"
    NOTIFICATION = "notification"
    DELEGATE = "delegate"
    BROADCAST = "broadcast"


class A2AMessage(BaseModel):
    """
    A2A Protocol Message Model
    """
    message_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    from_agent: str
    to_agent: str
    content: str
    message_type: MessageType = MessageType.REQUEST
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
    reply_to: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    payload: Dict[str, Any] = Field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert message to dictionary"""
        return self.model_dump()

    def to_json(self) -> str:
        """Convert message to JSON string"""
        return self.model_dump_json()

    @classmethod
    def from_json(cls, json_str: str) -> 'A2AMessage':
        """Create message from JSON string"""
        return cls.model_validate_json(json_str)

    def create_reply(self, content: str, **kwargs) -> 'A2AMessage':
        """Create a reply message"""
        return A2AMessage(
            from_agent=self.to_agent,
            to_agent=self.from_agent,
            content=content,
            message_type=MessageType.RESPONSE,
            reply_to=self.message_id,
            **kwargs
        )

    def create_delegate(self, delegate_to: str, content: str) -> 'A2AMessage':
        """Create a delegation message"""
        return A2AMessage(
            from_agent=self.from_agent,
            to_agent=delegate_to,
            content=content,
            message_type=MessageType.DELEGATE,
            reply_to=self.message_id,
            metadata={"original_sender": self.to_agent}
        )


class MessageBus(BaseModel):
    """
    Message bus for agent-to-agent communication
    Implements A2A protocol with async support
    """
    agents: Dict[str, 'Agent'] = Field(default_factory=dict)
    message_history: List[A2AMessage] = Field(default_factory=list)
    max_history: int = 1000
    _running: bool = False

    class Config:
        arbitrary_types_allowed = True

    def __init__(self, **data):
        super().__init__(**data)
        self._message_queue: asyncio.Queue = asyncio.Queue()
        self._handlers: Dict[str, Callable] = {}

    async def register_agent(self, name: str, agent: 'Agent'):
        """Register an agent with the message bus"""
        self.agents[name] = agent
        agent.message_bus = self

    async def unregister_agent(self, name: str):
        """Unregister an agent from the message bus"""
        if name in self.agents:
            del self.agents[name]

    async def send(
        self,
        from_agent: str,
        to_agent: str,
        message: A2AMessage
    ) -> Optional[A2AMessage]:
        """
        Send a message from one agent to another

        Args:
            from_agent: Sender agent name
            to_agent: Receiver agent name
            message: Message to send

        Returns:
            Response message if applicable
        """
        if to_agent not in self.agents:
            raise ValueError(f"Agent '{to_agent}' not registered")

        message.from_agent = from_agent
        message.to_agent = to_agent

        # Add to history
        self.message_history.append(message)
        if len(self.message_history) > self.max_history:
            self.message_history.pop(0)

        # Get receiver agent
        receiver = self.agents[to_agent]

        # Process message
        response = await receiver.receive_message(message)

        return response

    async def broadcast(
        self,
        from_agent: str,
        message: A2AMessage,
        exclude: Optional[List[str]] = None
    ) -> List[A2AMessage]:
        """
        Broadcast a message to all agents

        Args:
            from_agent: Sender agent name
            message: Message to broadcast
            exclude: List of agent names to exclude

        Returns:
            List of responses from all agents
        """
        exclude = exclude or []
        exclude.append(from_agent)

        responses = []
        for agent_name, agent in self.agents.items():
            if agent_name not in exclude:
                msg_copy = A2AMessage(**message.to_dict())
                msg_copy.to_agent = agent_name
                msg_copy.message_type = MessageType.BROADCAST

                response = await agent.receive_message(msg_copy)
                if response:
                    responses.append(response)

        return responses

    async def delegate(
        self,
        from_agent: str,
        to_agent: str,
        message: A2AMessage,
        context: Optional[Dict[str, Any]] = None
    ) -> A2AMessage:
        """
        Delegate a task to another agent

        Args:
            from_agent: Sender agent name
            to_agent: Agent to delegate to
            message: Original message
            context: Additional context for delegation

        Returns:
            Response from delegated agent
        """
        delegate_msg = A2AMessage(
            from_agent=from_agent,
            to_agent=to_agent,
            content=message.content,
            message_type=MessageType.DELEGATE,
            reply_to=message.message_id,
            payload={"original_message": message.to_dict(), "context": context}
        )

        return await self.send(from_agent, to_agent, delegate_msg)

    def get_message_history(
        self,
        agent_name: Optional[str] = None,
        limit: int = 100
    ) -> List[A2AMessage]:
        """
        Get message history

        Args:
            agent_name: Filter by agent name (optional)
            limit: Maximum number of messages to return

        Returns:
            List of messages
        """
        if agent_name:
            history = [
                msg for msg in self.message_history
                if msg.from_agent == agent_name or msg.to_agent == agent_name
            ]
        else:
            history = self.message_history

        return history[-limit:]

    def clear_history(self):
        """Clear message history"""
        self.message_history.clear()

    async def start(self):
        """Start the message bus (for future event loop support)"""
        self._running = True

    async def stop(self):
        """Stop the message bus"""
        self._running = False
