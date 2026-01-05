"""
PostgreSQL-based storage implementation
"""
from typing import Any, Dict, List, Optional
from datetime import datetime
import json

from ..base import BaseMemoryStore, AgentEvent, EventType


class PostgreSQLMemoryStore(BaseMemoryStore):
    """
    PostgreSQL-based persistent storage
    Suitable for production with advanced querying requirements
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.host = self.config.get("host", "localhost")
        self.port = self.config.get("port", 5432)
        self.user = self.config.get("user", "postgres")
        self.password = self.config.get("password", "")
        self.database = self.config.get("database", "agent_memory")
        self._pool = None

    async def initialize(self):
        """Initialize PostgreSQL connection pool"""
        try:
            import asyncpg
        except ImportError:
            raise ImportError("asyncpg is required for PostgreSQLMemoryStore. Install: pip install asyncpg")

        self._pool = await asyncpg.create_pool(
            host=self.host,
            port=self.port,
            user=self.user,
            password=self.password,
            database=self.database
        )

        await self._create_tables()

    async def _create_tables(self):
        """Create database tables"""
        async with self._pool.acquire() as conn:
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS agent_events (
                    event_id TEXT PRIMARY KEY,
                    agent_name TEXT NOT NULL,
                    session_id TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    timestamp TIMESTAMP NOT NULL,
                    data JSONB NOT NULL,
                    metadata JSONB,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );

                CREATE INDEX IF NOT EXISTS idx_agent ON agent_events(agent_name);
                CREATE INDEX IF NOT EXISTS idx_session ON agent_events(session_id);
                CREATE INDEX IF NOT EXISTS idx_type ON agent_events(event_type);
                CREATE INDEX IF NOT EXISTS idx_timestamp ON agent_events(timestamp);
                CREATE INDEX IF NOT EXISTS idx_data ON agent_events USING gin(data);
            """)

    async def store(self, event: AgentEvent) -> bool:
        """Store event in database"""
        try:
            async with self._pool.acquire() as conn:
                await conn.execute("""
                    INSERT INTO agent_events
                    (event_id, agent_name, session_id, event_type, timestamp, data, metadata)
                    VALUES ($1, $2, $3, $4, $5, $6, $7)
                """,
                    event.event_id,
                    event.agent_name,
                    event.session_id,
                    event.event_type.value,
                    event.timestamp,
                    event.data,
                    event.metadata
                )
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
        conditions = []
        params = []
        param_count = 1

        if agent_name:
            conditions.append(f"agent_name = ${param_count}")
            params.append(agent_name)
            param_count += 1

        if session_id:
            conditions.append(f"session_id = ${param_count}")
            params.append(session_id)
            param_count += 1

        if event_type:
            conditions.append(f"event_type = ${param_count}")
            params.append(event_type.value)
            param_count += 1

        if start_time:
            conditions.append(f"timestamp >= ${param_count}")
            params.append(start_time)
            param_count += 1

        if end_time:
            conditions.append(f"timestamp <= ${param_count}")
            params.append(end_time)
            param_count += 1

        if conditions:
            query += " AND " + " AND ".join(conditions)

        query += f" ORDER BY timestamp DESC LIMIT ${param_count}"
        params.append(limit)

        async with self._pool.acquire() as conn:
            rows = await conn.fetch(query, *params)
            events = []
            for row in rows:
                event = AgentEvent(
                    event_id=row['event_id'],
                    agent_name=row['agent_name'],
                    session_id=row['session_id'],
                    event_type=EventType(row['event_type']),
                    timestamp=row['timestamp'],
                    data=row['data'],
                    metadata=row['metadata']
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
        conditions = []
        params = []
        param_count = 1

        if agent_name:
            conditions.append(f"agent_name = ${param_count}")
            params.append(agent_name)
            param_count += 1

        if session_id:
            conditions.append(f"session_id = ${param_count}")
            params.append(session_id)
            param_count += 1

        if conditions:
            query += " AND " + " AND ".join(conditions)

        async with self._pool.acquire() as conn:
            await conn.execute(query, *params)

    async def get_stats(
        self,
        agent_name: Optional[str] = None,
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get statistics from database"""
        query = """
            SELECT
                COUNT(*) as total,
                event_type
            FROM agent_events
            WHERE 1=1
        """
        conditions = []
        params = []
        param_count = 1

        if agent_name:
            conditions.append(f"agent_name = ${param_count}")
            params.append(agent_name)
            param_count += 1

        if session_id:
            conditions.append(f"session_id = ${param_count}")
            params.append(session_id)
            param_count += 1

        if conditions:
            query += " AND " + " AND ".join(conditions)

        query += " GROUP BY event_type"

        async with self._pool.acquire() as conn:
            rows = await conn.fetch(query, *params)
            return {
                "by_type": {row['event_type']: row['total'] for row in rows},
                "total_events": sum(row['total'] for row in rows)
            }

    async def search(
        self,
        query: str,
        agent_name: Optional[str] = None,
        session_id: Optional[str] = None,
        limit: int = 10
    ) -> List[AgentEvent]:
        """Search events using JSONB query"""
        sql_query = """
            SELECT * FROM agent_events
            WHERE data::text LIKE $1
        """
        params = [f"%{query}%"]
        param_count = 2

        if agent_name:
            sql_query += f" AND agent_name = ${param_count}"
            params.append(agent_name)
            param_count += 1

        if session_id:
            sql_query += f" AND session_id = ${param_count}"
            params.append(session_id)
            param_count += 1

        sql_query += f" ORDER BY timestamp DESC LIMIT ${param_count}"
        params.append(limit)

        async with self._pool.acquire() as conn:
            rows = await conn.fetch(sql_query, *params)
            events = []
            for row in rows:
                event = AgentEvent(
                    event_id=row['event_id'],
                    agent_name=row['agent_name'],
                    session_id=row['session_id'],
                    event_type=EventType(row['event_type']),
                    timestamp=row['timestamp'],
                    data=row['data'],
                    metadata=row['metadata']
                )
                events.append(event)

            return events

    async def close(self):
        """Close connection pool"""
        if self._pool:
            await self._pool.close()
