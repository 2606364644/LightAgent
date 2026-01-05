"""
MySQL-based storage implementation
"""
from typing import Any, Dict, List, Optional
from datetime import datetime
import json

from ..base import BaseMemoryStore, AgentEvent, EventType


class MySQLMemoryStore(BaseMemoryStore):
    """
    MySQL-based persistent storage
    Suitable for production with high-volume requirements
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.host = self.config.get("host", "localhost")
        self.port = self.config.get("port", 3306)
        self.user = self.config.get("user", "root")
        self.password = self.config.get("password", "")
        self.database = self.config.get("database", "agent_memory")
        self._pool = None

    async def initialize(self):
        """Initialize MySQL connection pool"""
        try:
            import aiomysql
        except ImportError:
            raise ImportError("aiomysql is required for MySQLMemoryStore. Install: pip install aiomysql")

        self._pool = await aiomysql.create_pool(
            host=self.host,
            port=self.port,
            user=self.user,
            password=self.password,
            db=self.database,
            autocommit=True
        )

        await self._create_tables()

    async def _create_tables(self):
        """Create database tables"""
        async with self._pool.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute("""
                    CREATE TABLE IF NOT EXISTS agent_events (
                        event_id VARCHAR(255) PRIMARY KEY,
                        agent_name VARCHAR(255) NOT NULL,
                        session_id VARCHAR(255) NOT NULL,
                        event_type VARCHAR(50) NOT NULL,
                        timestamp DATETIME NOT NULL,
                        data JSON NOT NULL,
                        metadata JSON,
                        INDEX idx_agent (agent_name),
                        INDEX idx_session (session_id),
                        INDEX idx_type (event_type),
                        INDEX idx_time (timestamp)
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
                """)

    async def store(self, event: AgentEvent) -> bool:
        """Store event in database"""
        try:
            async with self._pool.acquire() as conn:
                async with conn.cursor() as cursor:
                    await cursor.execute("""
                        INSERT INTO agent_events
                        (event_id, agent_name, session_id, event_type, timestamp, data, metadata)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """, (
                        event.event_id,
                        event.agent_name,
                        event.session_id,
                        event.event_type.value,
                        event.timestamp,
                        event.model_dump_json(),
                        json.dumps(event.metadata)
                    ))
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
            query += " AND agent_name = %s"
            params.append(agent_name)

        if session_id:
            query += " AND session_id = %s"
            params.append(session_id)

        if event_type:
            query += " AND event_type = %s"
            params.append(event_type.value)

        if start_time:
            query += " AND timestamp >= %s"
            params.append(start_time)

        if end_time:
            query += " AND timestamp <= %s"
            params.append(end_time)

        query += " ORDER BY timestamp DESC LIMIT %s"
        params.append(limit)

        async with self._pool.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute(query, params)
                rows = await cursor.fetchall()
                events = []
                for row in rows:
                    event_data = json.loads(row[5])
                    event = AgentEvent(
                        event_id=row[0],
                        agent_name=row[1],
                        session_id=row[2],
                        event_type=EventType(row[3]),
                        timestamp=row[4],
                        data=event_data.get("data", {}),
                        metadata=json.loads(row[6]) if row[6] else {}
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
            query += " AND agent_name = %s"
            params.append(agent_name)

        if session_id:
            query += " AND session_id = %s"
            params.append(session_id)

        async with self._pool.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute(query, params)

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
            query += " AND agent_name = %s"
            params.append(agent_name)

        if session_id:
            query += " AND session_id = %s"
            params.append(session_id)

        query += " GROUP BY event_type"

        async with self._pool.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute(query, params)
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
            WHERE data LIKE %s
        """
        params = [f"%{query}%"]

        if agent_name:
            sql_query += " AND agent_name = %s"
            params.append(agent_name)

        if session_id:
            sql_query += " AND session_id = %s"
            params.append(session_id)

        sql_query += " ORDER BY timestamp DESC LIMIT %s"
        params.append(limit)

        async with self._pool.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute(sql_query, params)
                rows = await cursor.fetchall()
                events = []
                for row in rows:
                    event_data = json.loads(row[5])
                    event = AgentEvent(
                        event_id=row[0],
                        agent_name=row[1],
                        session_id=row[2],
                        event_type=EventType(row[3]),
                        timestamp=row[4],
                        data=event_data.get("data", {}),
                        metadata=json.loads(row[6]) if row[6] else {}
                    )
                    events.append(event)

                return events

    async def close(self):
        """Close connection pool"""
        if self._pool:
            self._pool.close()
            await self._pool.wait_closed()
