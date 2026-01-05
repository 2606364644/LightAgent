"""
File Memory Storage Example

This example demonstrates the FileMemoryStore for persistent event logging
"""

import asyncio
from lightagent import (
    Agent,
    FunctionBuilder,
    MockAdapter,
    ModelConfig,
    FileMemoryStore,
    EventType
)


async def calculator(expression: str) -> float:
    """Calculate a mathematical expression"""
    import ast
    import operator as op

    operators = {
        ast.Add: op.add,
        ast.Sub: op.sub,
        ast.Mult: op.mul,
        ast.Div: op.truediv,
    }

    def eval_expr(node):
        if isinstance(node, ast.Num):
            return node.n
        elif isinstance(node, ast.BinOp):
            return operators[type(node.op)](
                eval_expr(node.left),
                eval_expr(node.right)
            )
        else:
            raise TypeError(f"Unsupported type: {type(node)}")

    return eval_expr(ast.parse(expression, mode='eval').body)


async def example_1_jsonl_format():
    """Example 1: Using JSONL format (recommended)"""
    print("="*60)
    print("Example 1: JSONL Format Storage")
    print("="*60)
    print()

    # Create agent with file storage
    agent = Agent.create(
        name="math_assistant",
        model_adapter=MockAdapter(config=ModelConfig(model_name="gpt-3.5-turbo")),
        system_prompt="You are a math assistant",
        tools=[FunctionBuilder.create_tool(calculator, name="calculator")],
        memory_store=FileMemoryStore(config={
            "base_path": "./agent_memory_logs",
            "format": "jsonl",  # JSONL format - one JSON per line
            "file_per_session": True  # Separate file per session
        })
    )

    await agent.initialize()

    # Run some queries
    print("Running queries...")
    await agent.run("Calculate 25 * 4")
    await agent.run("What is 100 / 5?")
    await agent.run("Calculate 10 + 20")

    print()

    # Show file content
    import os
    log_dir = agent.memory_store.base_path
    log_files = list(log_dir.glob("*.jsonl"))

    print(f"Log files created: {len(log_files)}")
    for log_file in log_files:
        print(f"\n{log_file.name}:")
        with open(log_file, "r", encoding="utf-8") as f:
            lines = f.readlines()
            print(f"  Events: {len(lines)}")
            for line in lines[:3]:  # Show first 3 events
                event_data = eval(line.strip())
                print(f"  - {event_data['event_type']}: {event_data['data']}")
            if len(lines) > 3:
                print(f"  ... and {len(lines) - 3} more")

    print()


async def example_2_single_file():
    """Example 2: Single file for all sessions"""
    print("="*60)
    print("Example 2: Single File Mode")
    print("="*60)
    print()

    agent = Agent.create(
        name="assistant",
        model_adapter=MockAdapter(config=ModelConfig(model_name="gpt-3.5-turbo")),
        memory_store=FileMemoryStore(config={
            "base_path": "./memory_all",
            "file_per_session": False,  # All sessions in one file
            "format": "jsonl"
        })
    )

    await agent.initialize()

    # Multiple sessions
    print("Session 1:")
    await agent.run("Hello from session 1")
    session1_id = agent.context.session_id

    print("\nSession 2:")
    agent.reset_context()
    await agent.run("Hello from session 2")
    session2_id = agent.context.session_id

    print()

    # Show combined file
    log_file = agent.memory_store.base_path / "events.jsonl"
    if log_file.exists():
        with open(log_file, "r", encoding="utf-8") as f:
            lines = f.readlines()
            print(f"Total events in single file: {len(lines)}")

    print()


async def example_3_file_rotation():
    """Example 3: File rotation based on size"""
    print("="*60)
    print("Example 3: File Rotation")
    print("="*60)
    print()

    agent = Agent.create(
        name="rotation_test",
        model_adapter=MockAdapter(config=ModelConfig(model_name="gpt-3.5-turbo")),
        memory_store=FileMemoryStore(config={
            "base_path": "./memory_rotated",
            "rotate_size": 1024  # Very small for demo (1KB)
        })
    )

    await agent.initialize()

    # Generate enough events to trigger rotation
    print("Generating events to trigger rotation...")
    for i in range(10):
        await agent.run(f"Message {i}")

    print()

    # Show rotated files
    log_dir = agent.memory_store.base_path
    all_files = list(log_dir.glob("*.jsonl"))

    print(f"Files created (including rotated): {len(all_files)}")
    for file_path in sorted(all_files):
        size = file_path.stat().st_size
        print(f"  {file_path.name}: {size} bytes")

    print()


async def example_4_json_format():
    """Example 4: JSON array format (human-readable)"""
    print("="*60)
    print("Example 4: JSON Array Format")
    print("="*60)
    print()

    agent = Agent.create(
        name="json_format",
        model_adapter=MockAdapter(config=ModelConfig(model_name="gpt-3.5-turbo")),
        memory_store=FileMemoryStore(config={
            "base_path": "./memory_json",
            "format": "json"  # JSON array format
        })
    )

    await agent.initialize()
    await agent.run("Hello")
    await agent.run("Calculate 5 * 6")

    print()

    # Show JSON file
    json_file = agent.memory_store.base_path / "events.json"
    if json_file.exists():
        with open(json_file, "r", encoding="utf-8") as f:
            content = f.read()
            print(f"JSON file content:")
            print(content[:500] + "..." if len(content) > 500 else content)

    print()


async def example_5_query_and_search():
    """Example 5: Query and search file-based memory"""
    print("="*60)
    print("Example 5: Query and Search")
    print("="*60)
    print()

    agent = Agent.create(
        name="search_demo",
        model_adapter=MockAdapter(config=ModelConfig(model_name="gpt-3.5-turbo")),
        tools=[FunctionBuilder.create_tool(calculator, name="calculator")],
        memory_store=FileMemoryStore(config={
            "base_path": "./memory_search",
            "format": "jsonl"
        })
    )

    await agent.initialize()

    # Generate some events
    await agent.run("Calculate 10 * 20")
    await agent.run("What's the weather?")
    await agent.run("Calculate 5 + 5")

    print()

    # Query tool calls
    print("Searching for calculator events...")
    results = await agent.search_memory("calculator", limit=10)

    print(f"Found {len(results)} results")
    for event in results:
        print(f"  - {event.event_type.value}: {event.data}")

    print()

    # Get statistics
    stats = await agent.get_memory_stats()
    print("Statistics:")
    print(f"  Total events: {stats['total_events']}")
    print(f"  Total size: {stats['total_size_bytes']} bytes")
    print(f"  By type: {stats['by_type']}")

    print()


async def example_6_file_cleanup():
    """Example 6: File cleanup and maintenance"""
    print("="*60)
    print("Example 6: File Cleanup")
    print("="*60)
    print()

    agent = Agent.create(
        name="cleanup_demo",
        model_adapter=MockAdapter(config=ModelConfig(model_name="gpt-3.5-turbo")),
        memory_store=FileMemoryStore(config={
            "base_path": "./memory_cleanup",
        })
    )

    await agent.initialize()
    await agent.run("Test message 1")

    session_id = agent.context.session_id
    print(f"Session ID: {session_id}")

    # Show files before cleanup
    log_dir = agent.memory_store.base_path
    files_before = list(log_dir.glob("*.jsonl"))
    print(f"Files before cleanup: {len(files_before)}")

    # Clean up specific session
    await agent.clear_memory(session_id=session_id)

    # Show files after cleanup
    files_after = list(log_dir.glob("*.jsonl"))
    print(f"Files after cleanup: {len(files_after)}")

    print()


async def example_7_comparison():
    """Example 7: Compare JSONL vs JSON performance"""
    print("="*60)
    print("Example 7: Format Comparison")
    print("="*60)
    print()

    import time

    # JSONL format
    agent_jsonl = Agent.create(
        name="perf_test_jsonl",
        model_adapter=MockAdapter(config=ModelConfig(model_name="gpt-3.5-turbo")),
        memory_store=FileMemoryStore(config={
            "base_path": "./perf_jsonl",
            "format": "jsonl"
        })
    )

    await agent_jsonl.initialize()

    start = time.time()
    for i in range(100):
        await agent_jsonl.run(f"Message {i}")
    jsonl_time = time.time() - start

    # JSON format
    agent_json = Agent.create(
        name="perf_test_json",
        model_adapter=MockAdapter(config=ModelConfig(model_name="gpt-3.5-turbo")),
        memory_store=FileMemoryStore(config={
            "base_path": "./perf_json",
            "format": "json"
        })
    )

    await agent_json.initialize()

    start = time.time()
    for i in range(100):
        await agent_json.run(f"Message {i}")
    json_time = time.time() - start

    print("Performance comparison (100 events):")
    print(f"  JSONL format: {jsonl_time:.2f}s")
    print(f"  JSON format: {json_time:.2f}s")
    print(f"  Speedup: {json_time / jsonl_time:.2f}x")
    print()
    print("Note: JSONL is faster because it's append-only")

    print()


async def main():
    """Run all examples"""
    print("\n" + "="*60)
    print("LightAgent - File Memory Storage Examples")
    print("="*60)
    print()

    await example_1_jsonl_format()
    await example_2_single_file()
    await example_3_file_rotation()
    await example_4_json_format()
    await example_5_query_and_search()
    await example_6_file_cleanup()
    await example_7_comparison()

    print("="*60)
    print("Summary")
    print("="*60)
    print("""
## File Memory Storage Features

### 1. Format Options

**JSONL Format** (Recommended)
```python
memory_store=FileMemoryStore(config={
    "base_path": "./logs",
    "format": "jsonl"  # One JSON per line
})
```

- Faster (append-only)
- Smaller files
- Easy to parse
- Log-friendly

**JSON Format** (Human-readable)
```python
memory_store=FileMemoryStore(config={
    "base_path": "./logs",
    "format": "json"  # JSON array
})
```

- Human-readable
- Easy to inspect
- Slower for large files

### 2. File Organization

**Per-Session Files**
```python
config={
    "file_per_session": True  # Default
}
```
- Creates: session_abc123.jsonl
- Better for multi-session apps
- Easier session management

**Single File**
```python
config={
    "file_per_session": False
}
```
- Creates: events.jsonl
- All sessions in one file
- Simpler file structure

### 3. File Rotation

```python
config={
    "rotate_size": 10 * 1024 * 1024  # 10MB
}
```

- Automatically rotates when file gets too big
- Archives old files with timestamp
- Creates new log file

### 4. Use Cases

**Development/Testing:**
```python
FileMemoryStore(config={"base_path": "./dev_logs"})
```

**Production Logging:**
```python
FileMemoryStore(config={
    "base_path": "/var/log/agent",
    "rotate_size": 100 * 1024 * 1024  # 100MB
})
```

**Audit Trails:**
```python
FileMemoryStore(config={
    "base_path": "./audit",
    "format": "jsonl",
    "file_per_session": True
})
```

### 5. Advantages

- Simple file-based storage
- No database dependencies
- Easy to backup
- Human-readable (JSON format)
- Supports external tools (grep, jq, etc.)

### 6. File Format Examples

**JSONL format:**
```json
{"event_id":"evt_123","agent_name":"assistant","event_type":"user_message",...}
{"event_id":"evt_124","agent_name":"assistant","event_type":"model_response",...}
```

**JSON format:**
```json
[
  {"event_id":"evt_123","agent_name":"assistant",...},
  {"event_id":"evt_124","agent_name":"assistant",...}
]
```

### 7. External Tool Integration

```bash
# Count events
wc -l agent_memory_logs/session_*.jsonl

# Search for errors
grep "TOOL_CALL_ERROR" agent_memory_logs/session_*.jsonl

# Parse with jq
cat agent_memory_logs/session_*.jsonl | jq '.event_type'
```
    """)


if __name__ == "__main__":
    asyncio.run(main())
