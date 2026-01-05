"""
SQLite-based storage implementation
"""
from typing import Any, Dict, List, Optional
from datetime import datetime
import json

from ..base import BaseMemoryStore, AgentEvent, EventType


class SQLiteMemoryStore(BaseMemoryStore):
    """
    SQLite-based persistent storage
    Suitable for production use with persistent storage
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.db_path = self.config.get("db_path", "agent_memory.db")
        self._conn = None

    async def initialize(self):
        """Initialize SQLite database"""
        try:
            import aiosqlite
        except ImportError:
            raise ImportError("aiosqlite is required for SQLiteMemoryStore. Install: pip install aiosqlite")

        self._conn = await aiosqlite.connect(self.db_path)
        await self._create_tables()

    async def _create_tables(self):
        """Create database tables"""
        await self._conn.execute("""
            CREATE TABLE IF NOT EXISTS agent_events (
                event_id TEXT PRIMARY KEY,
                agent_name TEXT NOT NULL,
                session_id TEXT NOT NULL,
                event_type TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                data TEXT NOT NULL,
                metadata TEXT NOT NULL,
                INDEX(agent_name),
                INDEX(session_id),
                INDEX(event_type),
                INDEX(timestamp)
            )
        """)
        await self._conn.commit()

    async def store(self, event: AgentEvent) -> bool:
        """Store event in database"""
        try:
            await self._conn.execute(
                """INSERT INTO agent_events
                   (event_id, agent_name, session_id, event_type, timestamp, data, metadata)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (
                    event.event_id,
                    event.agent_name,
                    event.session_id,
                    event.event_type.value,
                    event.timestamp.isoformat(),
                    event.model_dump_json(),
                    json.dumps(event.metadata)
                )
            )
            await self._conn.commit()
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
        """Retrieve events from database"""
        query = "SELECT * FROM agent_events WHERE 1=1"
        params = []

        if agent_name:
            query += " AND agent_name = ?"
            params.append(agent_name)

        if session_id:
            query += " AND session_id = ?"
            params.append(session_id)

        if event_type:
            query += " AND event_type = ?"
            params.append(event_type.value)

        if start_time:
            query += " AND timestamp >= ?"
            params.append(start_time.isoformat())

        if end_time:
            query += " AND timestamp <= ?"
            params.append(end_time.isoformat())

        query += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)

        async with self._conn.execute(query, params) as cursor:
            rows = await cursor.fetchall()
            events = []
            for row in rows:
                event_data = json.loads(row[5])  # data column
                event = AgentEvent(
                    event_id=row[0],
                    agent_name=row[1],
                    session_id=row[2],
                    event_type=EventType(row[3]),
                    timestamp=datetime.fromisoformat(row[4]),
                    data=event_data.get("data", {}),
                    metadata=json.loads(row[6])
                )
                events.append(event)

            return events

    async def clear(
        self,
        agent_name: Optional[str] = None,
        session_id: Optional[str] = None
    ):
        """Clear events from database"""
        query = "DELETE FROM agent_events WHERE 1=1"
        params = []

        if agent_name:
            query += " AND agent_name = ?"
            params.append(agent_name)

        if session_id:
            query += " AND session_id = ?"
            params.append(session_id)

        await self._conn.execute(query, params)
        await self._conn.commit()

    async def get_stats(
        self,
        agent_name: Optional[str] = None,
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get statistics from database"""
        query = """
            SELECT
                COUNT(*) as total,
                event_type,
                MIN(timestamp) as first_event,
                MAX(timestamp) as last_event
            FROM agent_events
            WHERE 1=1
        """
        params = []

        if agent_name:
            query += " AND agent_name = ?"
            params.append(agent_name)

        if session_id:
            query += " AND session_id = ?"
            params.append(session_id)

        query += " GROUP BY event_type"

        async with self._conn.execute(query, params) as cursor:
            rows = await cursor.fetchall()
            return {
                "by_type": {row[1]: row[0] for row in rows},
                "total_events": sum(row[0] for row in rows),
                "first_event": min(row[2] for row in rows) if rows else None,
                "last_event": max(row[3] for row in rows) if rows else None
            }

    async def search(
        self,
        query: str,
        agent_name: Optional[str] = None,
        session_id: Optional[str] = None,
        limit: int = 10
    ) -> List[AgentEvent]:
        """Search events using LIKE query"""
        sql_query = """
            SELECT * FROM agent_events
            WHERE data LIKE ?
        """
        params = [f"%{query}%"]

        if agent_name:
            sql_query += " AND agent_name = ?"
            params.append(agent_name)

        if session_id:
            sql_query += " AND session_id = ?"
            params.append(session_id)

        sql_query += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)

        async with self._conn.execute(sql_query, params) as cursor:
            rows = await cursor.fetchall()
            events = []
            for row in rows:
                event_data = json.loads(row[5])
                event = AgentEvent(
                    event_id=row[0],
                    agent_name=row[1],
                    session_id=row[2],
                    event_type=EventType(row[3]),
                    timestamp=datetime.fromisoformat(row[4]),
                    data=event_data.get("data", {}),
                    metadata=json.loads(row[6])
                )
                events.append(event)

            return events

    async def close(self):
        """Close database connection"""
        if self._conn:
            await self._conn.close()
