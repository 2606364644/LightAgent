"""
Memory storage system for agents
"""
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field
from abc import ABC, abstractmethod
from datetime import datetime
from enum import Enum
import json


class EventType(str, Enum):
    """Types of events that can be stored"""
    # User interactions
    USER_MESSAGE = "user_message"
    # Model responses
    MODEL_RESPONSE = "model_response"
    # Tool calls
    TOOL_CALL_START = "tool_call_start"
    TOOL_CALL_SUCCESS = "tool_call_success"
    TOOL_CALL_ERROR = "tool_call_error"
    # Agent lifecycle
    AGENT_INIT = "agent_init"
    AGENT_ERROR = "agent_error"
    # Middleware events
    MIDDLEWARE_PRE = "middleware_pre"
    MIDDLEWARE_POST = "middleware_post"
    # Custom
    CUSTOM = "custom"


class AgentEvent(BaseModel):
    """
    Event model for storing agent interactions

    Fields:
        event_id: Unique event identifier
        agent_name: Name of the agent
        session_id: Session identifier
        event_type: Type of event
        timestamp: Event timestamp
        data: Event data (flexible schema)
        metadata: Additional metadata
    """
    event_id: str = Field(default_factory=lambda: f"evt_{datetime.now().timestamp()}")
    agent_name: str
    session_id: str
    event_type: EventType
    timestamp: datetime = Field(default_factory=datetime.now)
    data: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary"""
        return self.model_dump()

    def to_json(self) -> str:
        """Convert event to JSON string"""
        return self.model_dump_json()


class BaseMemoryStore(ABC):
    """Base class for memory storage implementations"""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}

    @abstractmethod
    async def initialize(self):
        """Initialize the memory store"""
        pass

    @abstractmethod
    async def store(self, event: AgentEvent) -> bool:
        """
        Store an event

        Args:
            event: Event to store

        Returns:
            True if successful, False otherwise
        """
        pass

    @abstractmethod
    async def retrieve(
        self,
        agent_name: Optional[str] = None,
        session_id: Optional[str] = None,
        event_type: Optional[EventType] = None,
        limit: int = 100,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> List[AgentEvent]:
        """
        Retrieve events from memory

        Args:
            agent_name: Filter by agent name
            session_id: Filter by session ID
            event_type: Filter by event type
            limit: Maximum number of events to return
            start_time: Filter events after this time
            end_time: Filter events before this time

        Returns:
            List of events
        """
        pass

    @abstractmethod
    async def clear(
        self,
        agent_name: Optional[str] = None,
        session_id: Optional[str] = None
    ):
        """
        Clear events from memory

        Args:
            agent_name: Clear events for this agent
            session_id: Clear events for this session
        """
        pass

    @abstractmethod
    async def get_stats(
        self,
        agent_name: Optional[str] = None,
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get statistics about stored events

        Args:
            agent_name: Filter by agent name
            session_id: Filter by session ID

        Returns:
            Statistics dictionary
        """
        pass

    async def search(
        self,
        query: str,
        agent_name: Optional[str] = None,
        session_id: Optional[str] = None,
        limit: int = 10
    ) -> List[AgentEvent]:
        """
        Search events by content

        Args:
            query: Search query
            agent_name: Filter by agent name
            session_id: Filter by session ID
            limit: Maximum results

        Returns:
            Matching events
        """
        # Default implementation - can be overridden
        events = await self.retrieve(
            agent_name=agent_name,
            session_id=session_id,
            limit=limit
        )

        # Simple text search
        query_lower = query.lower()
        results = []
        for event in events:
            event_str = json.dumps(event.data).lower()
            if query_lower in event_str:
                results.append(event)

        return results

    async def close(self):
        """Close the memory store and cleanup resources"""
        pass
