"""
In-memory storage implementation
"""
from typing import Any, Dict, List, Optional
from datetime import datetime
from collections import defaultdict

from ..base import BaseMemoryStore, AgentEvent, EventType


class InMemoryMemoryStore(BaseMemoryStore):
    """
    In-memory storage for events
    Suitable for testing and short-lived applications
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.events: List[AgentEvent] = []
        self.events_by_session: Dict[str, List[AgentEvent]] = defaultdict(list)
        self.events_by_agent: Dict[str, List[AgentEvent]] = defaultdict(list)
        self.events_by_type: Dict[EventType, List[AgentEvent]] = defaultdict(list)

    async def initialize(self):
        """Initialize (no-op for in-memory)"""
        pass

    async def store(self, event: AgentEvent) -> bool:
        """Store event in memory"""
        try:
            self.events.append(event)
            self.events_by_session[event.session_id].append(event)
            self.events_by_agent[event.agent_name].append(event)
            self.events_by_type[event.event_type].append(event)
            return True
        except Exception:
            return False

    async def retrieve(
        self,
        agent_name: Optional[str] = None,
        session_id: Optional[str] = None,
        event_type: Optional[EventType] = None,
        limit: int = 100,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> List[AgentEvent]:
        """Retrieve events"""
        results = self.events

        # Filter by agent
        if agent_name:
            if agent_name not in self.events_by_agent:
                return []
            results = self.events_by_agent[agent_name]

        # Filter by session
        if session_id:
            if session_id not in self.events_by_session:
                return []
            results = self.events_by_session[session_id]

        # Filter by type
        if event_type:
            if isinstance(results, list):
                results = [e for e in results if e.event_type == event_type]
            else:
                results = self.events_by_type.get(event_type, [])

        # Filter by time range
        if start_time:
            results = [e for e in results if e.timestamp >= start_time]
        if end_time:
            results = [e for e in results if e.timestamp <= end_time]

        # Limit
        return results[-limit:]

    async def clear(
        self,
        agent_name: Optional[str] = None,
        session_id: Optional[str] = None
    ):
        """Clear events"""
        if agent_name and session_id:
            # Clear specific agent and session
            to_remove = [
                e for e in self.events
                if e.agent_name == agent_name and e.session_id == session_id
            ]
            for e in to_remove:
                self.events.remove(e)
        elif agent_name:
            # Clear all events for agent
            self.events = [e for e in self.events if e.agent_name != agent_name]
            if agent_name in self.events_by_agent:
                del self.events_by_agent[agent_name]
        elif session_id:
            # Clear all events for session
            self.events = [e for e in self.events if e.session_id != session_id]
            if session_id in self.events_by_session:
                del self.events_by_session[session_id]
        else:
            # Clear all
            self.events.clear()
            self.events_by_session.clear()
            self.events_by_agent.clear()
            self.events_by_type.clear()

    async def get_stats(
        self,
        agent_name: Optional[str] = None,
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get statistics"""
        events = await self.retrieve(
            agent_name=agent_name,
            session_id=session_id,
            limit=1000000
        )

        # Count by type
        type_counts = defaultdict(int)
        for event in events:
            type_counts[event.event_type] += 1

        return {
            "total_events": len(events),
            "by_type": dict(type_counts),
            "first_event": events[0].timestamp if events else None,
            "last_event": events[-1].timestamp if events else None
        }
