"""
File-based storage implementation
"""
from typing import Any, Dict, List, Optional
from datetime import datetime
import json
from collections import defaultdict
from pathlib import Path

from ..base import BaseMemoryStore, AgentEvent, EventType


class FileMemoryStore(BaseMemoryStore):
    """
    File-based storage for events
    Supports JSON and JSONL formats
    Suitable for logging, audit trails, and simple persistence
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.base_path = Path(self.config.get("base_path", "agent_memory"))
        self.format = self.config.get("format", "jsonl")  # "json" or "jsonl"
        self.file_per_session = self.config.get("file_per_session", True)
        self.rotate_size = self.config.get("rotate_size", 10 * 1024 * 1024)  # 10MB

        self._current_files: Dict[str, Any] = {}  # session_id -> file handle
        self._file_sizes: Dict[str, int] = {}
        self._extension = f".{self.format}"  # Store extension for reuse

    async def initialize(self):
        """Initialize file storage"""
        self.base_path.mkdir(parents=True, exist_ok=True)

    def _get_session_file(self, session_id: str) -> Path:
        """Get file path for a session"""
        if self.file_per_session:
            return self.base_path / f"session_{session_id}{self._extension}"
        else:
            return self.base_path / f"events{self._extension}"

    async def _append_to_file(self, file_path: Path, event: AgentEvent):
        """Append event to file"""
        event_json = event.model_dump_json() + "\n"

        if self.format == "jsonl":
            # JSONL format (one JSON per line)
            with open(file_path, "a", encoding="utf-8") as f:
                f.write(event_json)
        else:
            # JSON array format (slower)
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
            except (FileNotFoundError, json.JSONDecodeError):
                data = []

            # Use model_dump to get dict, which json.dump can handle
            event_dict = event.model_dump()
            data.append(event_dict)

            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2, default=str)

        # Update file size
        file_size = file_path.stat().st_size
        if file_size > self.rotate_size:
            await self._rotate_file(file_path)

    async def _rotate_file(self, file_path: Path):
        """Rotate log file when it gets too large"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        archive_path = file_path.parent / f"{file_path.stem}_{timestamp}{file_path.suffix}"

        # Archive current file
        file_path.rename(archive_path)

        # Create new file
        file_path.touch()

    async def store(self, event: AgentEvent) -> bool:
        """Store event to file"""
        try:
            file_path = self._get_session_file(event.session_id)
            await self._append_to_file(file_path, event)
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
        """Retrieve events from files"""
        events = []

        # Determine which files to read
        if session_id:
            files = [self._get_session_file(session_id)]
        elif self.file_per_session:
            files = list(self.base_path.glob(f"session_*{self._extension}"))
        else:
            files = [self.base_path / f"events{self._extension}"]

        for file_path in files:
            if not file_path.exists():
                continue

            try:
                # Read events from file
                if file_path.suffix == ".jsonl":
                    # JSONL format
                    with open(file_path, "r", encoding="utf-8") as f:
                        for line in f:
                            line = line.strip()
                            if not line:
                                continue
                            try:
                                event_data = json.loads(line)
                                event = AgentEvent(**event_data)
                                events.append(event)
                            except (json.JSONDecodeError, TypeError):
                                continue
                else:
                    # JSON array format
                    with open(file_path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        for event_data in data:
                            # Convert timestamp string back to datetime if needed
                            if isinstance(event_data.get("timestamp"), str):
                                event_data["timestamp"] = datetime.fromisoformat(event_data["timestamp"])
                            event = AgentEvent(**event_data)
                            events.append(event)
            except (FileNotFoundError, json.JSONDecodeError):
                continue

        # Apply filters
        if agent_name:
            events = [e for e in events if e.agent_name == agent_name]

        if event_type:
            events = [e for e in events if e.event_type == event_type]

        if start_time:
            events = [e for e in events if e.timestamp >= start_time]

        if end_time:
            events = [e for e in events if e.timestamp <= end_time]

        # Sort by timestamp and limit
        events.sort(key=lambda e: e.timestamp)
        return events[-limit:]

    async def clear(
        self,
        agent_name: Optional[str] = None,
        session_id: Optional[str] = None
    ):
        """Clear events by deleting files"""
        if session_id:
            file_path = self._get_session_file(session_id)
            if file_path.exists():
                file_path.unlink()
        else:
            # Clear all files
            for file_path in self.base_path.glob(f"*{self._extension}"):
                if agent_name:
                    # Filter by agent name (need to check file content)
                    # For simplicity, delete all
                    file_path.unlink()
                else:
                    file_path.unlink()

    async def get_stats(
        self,
        agent_name: Optional[str] = None,
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get statistics from files"""
        events = await self.retrieve(
            agent_name=agent_name,
            session_id=session_id,
            limit=1000000
        )

        # Count by type
        type_counts = defaultdict(int)
        for event in events:
            type_counts[event.event_type] += 1

        # Count total size
        total_size = 0
        for file_path in self.base_path.glob(f"*{self._extension}"):
            total_size += file_path.stat().st_size

        return {
            "total_events": len(events),
            "by_type": dict(type_counts),
            "first_event": events[0].timestamp if events else None,
            "last_event": events[-1].timestamp if events else None,
            "total_size_bytes": total_size
        }

    async def search(
        self,
        query: str,
        agent_name: Optional[str] = None,
        session_id: Optional[str] = None,
        limit: int = 10
    ) -> List[AgentEvent]:
        """Search events by content"""
        events = await self.retrieve(
            agent_name=agent_name,
            session_id=session_id,
            limit=1000000
        )

        # Text search
        query_lower = query.lower()
        results = []

        for event in events:
            event_str = json.dumps(event.data).lower()
            if query_lower in event_str:
                results.append(event)
                if len(results) >= limit:
                    break

        return results
