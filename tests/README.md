# LightAgent Unit Tests

## Overview

This directory contains unit tests for the LightAgent framework, specifically testing the memory storage system.

## Test Files

- `test_memory_stores.py` - Comprehensive tests for memory storage backends
  - InMemoryMemoryStore tests
  - FileMemoryStore tests (JSONL format)
  - FileMemoryStore tests (JSON format)
  - File rotation tests
  - Performance comparison tests

## Running Tests

### Install Dependencies

```bash
pip install pytest pytest-asyncio
```

### Run All Tests

```bash
pytest tests/
```

### Run Specific Test Class

```bash
pytest tests/test_memory_stores.py::TestInMemoryMemoryStore
pytest tests/test_memory_stores.py::TestFileMemoryStoreJSONL
```

### Run Specific Test

```bash
pytest tests/test_memory_stores.py::TestInMemoryMemoryStore::test_store_event
```

### Run with Verbose Output

```bash
pytest tests/ -v
```

### Run with Coverage

```bash
pip install pytest-cov
pytest tests/ --cov=lightagent --cov-report=html
```

## Test Coverage

The test suite covers:

### InMemoryMemoryStore
- Initialization
- Event storage and retrieval
- Filtering by agent, session, event type
- Time range queries
- Event limiting
- Clear operations (by session and all)
- Statistics
- Search functionality

### FileMemoryStore (JSONL)
- File creation and management
- JSONL format validation
- Per-session file organization
- Multi-session handling
- File clearing
- Statistics
- Search functionality

### FileMemoryStore (JSON)
- JSON array format
- Read/write operations
- Event retrieval

### FileMemoryStore (Single File Mode)
- Single file organization
- Cross-session retrieval

### FileMemoryStore (Rotation)
- Automatic file rotation
- Size-based triggering
- Archive file creation

### Performance
- JSONL vs JSON format comparison
- Speed measurements

## Test Data

Tests use temporary directories that are automatically cleaned up after each test using pytest's `tmp_path` fixture.

## Writing New Tests

When adding new tests:

1. Use pytest fixtures for setup/teardown
2. Mark async tests with `@pytest.mark.asyncio`
3. Use descriptive test names (e.g., `test_store_event`)
4. Clean up resources in fixtures
5. Test both success and failure cases

Example:

```python
class TestMyFeature:
    @pytest.fixture
    async def setup(self):
        store = MyStore()
        await store.initialize()
        yield store
        # Cleanup

    @pytest.mark.asyncio
    async def test_something(self, setup):
        result = await setup.do_something()
        assert result is True
```

## Troubleshooting

### Import Errors

Make sure you're in the project root directory:

```bash
cd /path/to/LightAgent
pytest tests/
```

### Asyncio Errors

Ensure pytest-asyncio is installed:

```bash
pip install pytest-asyncio
```

### Temporary Files

If tests fail to clean up temporary files, manually remove them:

```bash
rm -rf /tmp/test_memory_*
```
