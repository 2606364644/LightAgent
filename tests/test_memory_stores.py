"""
Unit tests for memory storage system
"""
import asyncio
import pytest
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Any
import json
import shutil

from lightagent.memory.base import AgentEvent, EventType
from lightagent.memory.stores import InMemoryMemoryStore, FileMemoryStore


class TestInMemoryMemoryStore:
    """Test InMemoryMemoryStore functionality"""

    @pytest.fixture
    async def store(self):
        """Create a fresh store for each test"""
        store = InMemoryMemoryStore()
        await store.initialize()
        return store

    @pytest.fixture
    def sample_events(self):
        """Create sample events for testing"""
        events = []
        base_time = datetime.now()
        for i in range(5):
            event = AgentEvent(
                event_id=f"evt_{i}",
                agent_name="test_agent",
                session_id="session_123",
                event_type=EventType.USER_MESSAGE if i % 2 == 0 else EventType.MODEL_RESPONSE,
                timestamp=base_time + timedelta(seconds=i),
                data={"message": f"Test message {i}"},
                metadata={"index": i}
            )
            events.append(event)
        return events

    @pytest.mark.asyncio
    async def test_initialize(self, store):
        """Test store initialization"""
        assert store is not None
        assert len(store.events) == 0

    @pytest.mark.asyncio
    async def test_store_event(self, store, sample_events):
        """Test storing events"""
        for event in sample_events:
            result = await store.store(event)
            assert result is True

        assert len(store.events) == 5

    @pytest.mark.asyncio
    async def test_retrieve_all(self, store, sample_events):
        """Test retrieving all events"""
        for event in sample_events:
            await store.store(event)

        events = await store.retrieve()
        assert len(events) == 5

    @pytest.mark.asyncio
    async def test_retrieve_by_agent(self, store, sample_events):
        """Test filtering by agent name"""
        for event in sample_events:
            await store.store(event)

        events = await store.retrieve(agent_name="test_agent")
        assert len(events) == 5

        events = await store.retrieve(agent_name="unknown_agent")
        assert len(events) == 0

    @pytest.mark.asyncio
    async def test_retrieve_by_session(self, store, sample_events):
        """Test filtering by session ID"""
        for event in sample_events:
            await store.store(event)

        events = await store.retrieve(session_id="session_123")
        assert len(events) == 5

        events = await store.retrieve(session_id="unknown_session")
        assert len(events) == 0

    @pytest.mark.asyncio
    async def test_retrieve_by_event_type(self, store, sample_events):
        """Test filtering by event type"""
        for event in sample_events:
            await store.store(event)

        events = await store.retrieve(event_type=EventType.USER_MESSAGE)
        assert len(events) == 3

        events = await store.retrieve(event_type=EventType.MODEL_RESPONSE)
        assert len(events) == 2

    @pytest.mark.asyncio
    async def test_retrieve_with_limit(self, store, sample_events):
        """Test limiting results"""
        for event in sample_events:
            await store.store(event)

        events = await store.retrieve(limit=3)
        assert len(events) == 3

    @pytest.mark.asyncio
    async def test_retrieve_with_time_range(self, store, sample_events):
        """Test filtering by time range"""
        for event in sample_events:
            await store.store(event)

        # Use the actual timestamps from the events
        start_time = sample_events[1].timestamp  # Second event
        end_time = sample_events[3].timestamp  # Fourth event

        events = await store.retrieve(start_time=start_time, end_time=end_time)
        assert len(events) == 3

    @pytest.mark.asyncio
    async def test_clear_by_session(self, store, sample_events):
        """Test clearing events by session"""
        for event in sample_events:
            await store.store(event)

        await store.clear(session_id="session_123")
        assert len(store.events) == 0

    @pytest.mark.asyncio
    async def test_clear_all(self, store, sample_events):
        """Test clearing all events"""
        for event in sample_events:
            await store.store(event)

        await store.clear()
        assert len(store.events) == 0
        assert len(store.events_by_session) == 0
        assert len(store.events_by_agent) == 0
        assert len(store.events_by_type) == 0

    @pytest.mark.asyncio
    async def test_get_stats(self, store, sample_events):
        """Test getting statistics"""
        for event in sample_events:
            await store.store(event)

        stats = await store.get_stats()
        assert stats["total_events"] == 5
        assert stats["by_type"][EventType.USER_MESSAGE] == 3
        assert stats["by_type"][EventType.MODEL_RESPONSE] == 2
        assert stats["first_event"] is not None
        assert stats["last_event"] is not None

    @pytest.mark.asyncio
    async def test_search(self, store, sample_events):
        """Test searching events"""
        for event in sample_events:
            await store.store(event)

        results = await store.search("message")
        assert len(results) == 5

        results = await store.search("message 1")
        assert len(results) == 1


class TestFileMemoryStoreJSONL:
    """Test FileMemoryStore with JSONL format"""

    @pytest.fixture
    def temp_dir(self, tmp_path):
        """Create temporary directory for test files"""
        test_dir = tmp_path / "test_memory_jsonl"
        test_dir.mkdir(exist_ok=True)
        return test_dir

    @pytest.fixture
    async def store(self, temp_dir):
        """Create a fresh store for each test"""
        store = FileMemoryStore(config={
            "base_path": str(temp_dir),
            "format": "jsonl",
            "file_per_session": True
        })
        await store.initialize()
        return store

    @pytest.fixture
    def sample_events(self):
        """Create sample events for testing"""
        events = []
        base_time = datetime.now()
        for i in range(5):
            event = AgentEvent(
                event_id=f"evt_{i}",
                agent_name="test_agent",
                session_id="session_123",
                event_type=EventType.USER_MESSAGE if i % 2 == 0 else EventType.MODEL_RESPONSE,
                timestamp=base_time + timedelta(seconds=i),
                data={"message": f"Test message {i}"},
                metadata={"index": i}
            )
            events.append(event)
        return events

    @pytest.mark.asyncio
    async def test_initialize(self, store, temp_dir):
        """Test store initialization"""
        assert store is not None
        assert temp_dir.exists()

    @pytest.mark.asyncio
    async def test_store_and_retrieve(self, store, sample_events):
        """Test storing and retrieving events"""
        for event in sample_events:
            result = await store.store(event)
            assert result is True

        events = await store.retrieve()
        assert len(events) == 5

    @pytest.mark.asyncio
    async def test_file_creation(self, store, sample_events, temp_dir):
        """Test that files are created correctly"""
        for event in sample_events:
            await store.store(event)

        files = list(temp_dir.glob("*.jsonl"))
        assert len(files) == 1
        assert files[0].name == "session_session_123.jsonl"

    @pytest.mark.asyncio
    async def test_jsonl_format(self, store, sample_events, temp_dir):
        """Test JSONL file format"""
        for event in sample_events:
            await store.store(event)

        file_path = temp_dir / "session_session_123.jsonl"
        with open(file_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
            assert len(lines) == 5

            for line in lines:
                data = json.loads(line.strip())
                assert "event_id" in data
                assert "agent_name" in data

    @pytest.mark.asyncio
    async def test_retrieve_by_session(self, store, sample_events):
        """Test retrieving by session ID"""
        for event in sample_events:
            await store.store(event)

        events = await store.retrieve(session_id="session_123")
        assert len(events) == 5

        events = await store.retrieve(session_id="unknown_session")
        assert len(events) == 0

    @pytest.mark.asyncio
    async def test_multiple_sessions(self, store, sample_events, temp_dir):
        """Test handling multiple sessions"""
        session1_events = sample_events[:3]
        session2_events = sample_events[3:]

        for event in session1_events:
            await store.store(event)

        for event in session2_events:
            event.session_id = "session_456"
            await store.store(event)

        files = list(temp_dir.glob("*.jsonl"))
        assert len(files) == 2

        session1_events = await store.retrieve(session_id="session_123")
        session2_events = await store.retrieve(session_id="session_456")

        assert len(session1_events) == 3
        assert len(session2_events) == 2

    @pytest.mark.asyncio
    async def test_clear_by_session(self, store, sample_events, temp_dir):
        """Test clearing events by session"""
        for event in sample_events:
            await store.store(event)

        file_path = temp_dir / "session_session_123.jsonl"
        assert file_path.exists()

        await store.clear(session_id="session_123")
        assert not file_path.exists()

    @pytest.mark.asyncio
    async def test_get_stats(self, store, sample_events):
        """Test getting statistics"""
        for event in sample_events:
            await store.store(event)

        stats = await store.get_stats()
        assert stats["total_events"] == 5
        assert stats["by_type"][EventType.USER_MESSAGE] == 3
        assert stats["by_type"][EventType.MODEL_RESPONSE] == 2
        assert "total_size_bytes" in stats

    @pytest.mark.asyncio
    async def test_search(self, store, sample_events):
        """Test searching events"""
        for event in sample_events:
            await store.store(event)

        results = await store.search("message")
        assert len(results) == 5

        results = await store.search("message 1")
        assert len(results) == 1


class TestFileMemoryStoreJSON:
    """Test FileMemoryStore with JSON format"""

    @pytest.fixture
    def temp_dir(self, tmp_path):
        """Create temporary directory for test files"""
        test_dir = tmp_path / "test_memory_json"
        test_dir.mkdir(exist_ok=True)
        return test_dir

    @pytest.fixture
    async def store(self, temp_dir):
        """Create a fresh store for each test"""
        store = FileMemoryStore(config={
            "base_path": str(temp_dir),
            "format": "json",
            "file_per_session": True
        })
        await store.initialize()
        return store

    @pytest.fixture
    def sample_events(self):
        """Create sample events for testing"""
        events = []
        for i in range(3):
            event = AgentEvent(
                event_id=f"evt_{i}",
                agent_name="test_agent",
                session_id="session_123",
                event_type=EventType.USER_MESSAGE,
                timestamp=datetime.now() + timedelta(seconds=i),
                data={"message": f"Test message {i}"},
                metadata={"index": i}
            )
            events.append(event)
        return events

    @pytest.mark.asyncio
    async def test_json_format(self, store, sample_events, temp_dir):
        """Test JSON file format"""
        for event in sample_events:
            await store.store(event)

        file_path = temp_dir / "session_session_123.json"
        assert file_path.exists()

        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            assert isinstance(data, list)
            assert len(data) == 3

    @pytest.mark.asyncio
    async def test_store_and_retrieve(self, store, sample_events):
        """Test storing and retrieving events"""
        for event in sample_events:
            await store.store(event)

        events = await store.retrieve()
        assert len(events) == 3


class TestFileMemoryStoreSingleFile:
    """Test FileMemoryStore with single file mode"""

    @pytest.fixture
    def temp_dir(self, tmp_path):
        """Create temporary directory for test files"""
        test_dir = tmp_path / "test_memory_single"
        test_dir.mkdir(exist_ok=True)
        return test_dir

    @pytest.fixture
    async def store(self, temp_dir):
        """Create a fresh store for each test"""
        store = FileMemoryStore(config={
            "base_path": str(temp_dir),
            "format": "jsonl",
            "file_per_session": False
        })
        await store.initialize()
        return store

    @pytest.fixture
    def sample_events(self):
        """Create sample events for testing"""
        events = []
        for i in range(5):
            event = AgentEvent(
                event_id=f"evt_{i}",
                agent_name="test_agent",
                session_id=f"session_{i % 2}",
                event_type=EventType.USER_MESSAGE,
                timestamp=datetime.now() + timedelta(seconds=i),
                data={"message": f"Test message {i}"},
                metadata={"index": i}
            )
            events.append(event)
        return events

    @pytest.mark.asyncio
    async def test_single_file_mode(self, store, sample_events, temp_dir):
        """Test single file mode"""
        for event in sample_events:
            await store.store(event)

        files = list(temp_dir.glob("*.jsonl"))
        assert len(files) == 1
        assert files[0].name == "events.jsonl"

    @pytest.mark.asyncio
    async def test_retrieve_all_sessions(self, store, sample_events):
        """Test retrieving events from all sessions"""
        for event in sample_events:
            await store.store(event)

        events = await store.retrieve()
        assert len(events) == 5


class TestFileMemoryStoreRotation:
    """Test FileMemoryStore file rotation"""

    @pytest.fixture
    def temp_dir(self, tmp_path):
        """Create temporary directory for test files"""
        test_dir = tmp_path / "test_memory_rotation"
        test_dir.mkdir(exist_ok=True)
        return test_dir

    @pytest.fixture
    async def store(self, temp_dir):
        """Create a fresh store with small rotation size"""
        store = FileMemoryStore(config={
            "base_path": str(temp_dir),
            "format": "jsonl",
            "file_per_session": False,
            "rotate_size": 1024
        })
        await store.initialize()
        return store

    @pytest.mark.asyncio
    async def test_file_rotation(self, store, temp_dir):
        """Test file rotation when size exceeds limit"""
        # Create enough events to trigger rotation
        for i in range(50):
            event = AgentEvent(
                event_id=f"evt_{i}",
                agent_name="test_agent",
                session_id="session_123",
                event_type=EventType.USER_MESSAGE,
                timestamp=datetime.now() + timedelta(seconds=i),
                data={"message": f"Test message {i} with some extra data to increase size"},
                metadata={"index": i, "extra": "data" * 10}
            )
            await store.store(event)

        files = list(temp_dir.glob("*.jsonl"))
        assert len(files) >= 2

        # Check that we have events.jsonl and archived files
        main_file = temp_dir / "events.jsonl"
        assert main_file.exists()


class TestFileMemoryStorePerformance:
    """Test FileMemoryStore performance characteristics"""

    @pytest.fixture
    def temp_dir(self, tmp_path):
        """Create temporary directory for test files"""
        test_dir = tmp_path / "test_memory_perf"
        test_dir.mkdir(exist_ok=True)
        return test_dir

    @pytest.mark.asyncio
    async def test_jsonl_vs_json_performance(self, temp_dir):
        """Compare JSONL and JSON format performance"""
        import time

        # Test JSONL format
        store_jsonl = FileMemoryStore(config={
            "base_path": str(temp_dir / "jsonl"),
            "format": "jsonl"
        })
        await store_jsonl.initialize()

        start = time.time()
        for i in range(100):
            event = AgentEvent(
                event_id=f"evt_jsonl_{i}",
                agent_name="test_agent",
                session_id="session_123",
                event_type=EventType.USER_MESSAGE,
                timestamp=datetime.now() + timedelta(seconds=i),
                data={"message": f"Test message {i}"},
                metadata={"index": i}
            )
            await store_jsonl.store(event)
        jsonl_time = time.time() - start

        # Test JSON format
        store_json = FileMemoryStore(config={
            "base_path": str(temp_dir / "json"),
            "format": "json"
        })
        await store_json.initialize()

        start = time.time()
        for i in range(100):
            event = AgentEvent(
                event_id=f"evt_json_{i}",
                agent_name="test_agent",
                session_id="session_123",
                event_type=EventType.USER_MESSAGE,
                timestamp=datetime.now() + timedelta(seconds=i),
                data={"message": f"Test message {i}"},
                metadata={"index": i}
            )
            await store_json.store(event)
        json_time = time.time() - start

        # JSONL should be faster (append-only)
        print(f"\nJSONL time: {jsonl_time:.3f}s")
        print(f"JSON time: {json_time:.3f}s")
        print(f"Speedup: {json_time / jsonl_time:.2f}x")

        assert jsonl_time < json_time


@pytest.fixture
def cleanup_temp_dirs(tmp_path):
    """Clean up temporary directories after tests"""
    yield
    # Cleanup happens automatically with tmp_path fixture
    pass
