"""
Memory Storage Example

This example demonstrates:
1. Using different memory storage backends
2. Recording events automatically
3. Querying memory
4. Memory statistics
"""

import asyncio
from lightagent import (
    Agent,
    FunctionBuilder,
    MockAdapter,
    ModelConfig,
    InMemoryMemoryStore,
    SQLiteMemoryStore,
    EventType
)


# Define a tool
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


async def example_1_in_memory_storage():
    """Example 1: In-memory storage"""
    print("="*60)
    print("Example 1: In-Memory Storage")
    print("="*60)
    print()

    # Create agent with in-memory storage
    agent = Agent.create(
        name="math_assistant",
        model_adapter=MockAdapter(config=ModelConfig(model_name="gpt-3.5-turbo")),
        system_prompt="You are a math assistant. Use the calculator tool.",
        tools=[FunctionBuilder.create_tool(calculator, name="calculator")],
        memory_store=InMemoryMemoryStore()
    )

    await agent.initialize()

    # Run some queries
    print("Running queries...")
    await agent.run("Calculate 25 * 4")
    await agent.run("What is 100 / 5?")
    await agent.run("Calculate 10 + 20")

    print()

    # Query memory
    print("Querying memory...")
    events = await agent.get_memory(limit=10)

    print(f"Total events recorded: {len(events)}")
    for i, event in enumerate(events[-5:], 1):
        print(f"{i}. {event.event_type.value}: {event.data}")

    print()

    # Get statistics
    stats = await agent.get_memory_stats()
    print("Statistics:")
    print(f"  Total events: {stats['total_events']}")
    print(f"  By type: {stats['by_type']}")

    print()


async def example_2_sqlite_storage():
    """Example 2: SQLite persistent storage"""
    print("="*60)
    print("Example 2: SQLite Storage")
    print("="*60)
    print()

    # Create agent with SQLite storage
    agent = Agent.create(
        name="math_assistant_db",
        model_adapter=MockAdapter(config=ModelConfig(model_name="gpt-3.5-turbo")),
        system_prompt="You are a math assistant.",
        tools=[FunctionBuilder.create_tool(calculator, name="calculator")],
        memory_store=SQLiteMemoryStore(config={"db_path": ":memory:"})  # In-memory SQLite
    )

    await agent.initialize()

    # Run queries
    print("Running queries...")
    await agent.run("Calculate 5 * 6")
    await agent.run("What is 50 / 2?")

    print()

    # Filter by event type
    print("Filtering by TOOL_CALL_SUCCESS...")
    tool_events = await agent.get_memory(event_type=EventType.TOOL_CALL_SUCCESS)

    for event in tool_events:
        print(f"  Tool: {event.data.get('tool_name')}")
        print(f"  Result: {event.data.get('result')}")

    print()


async def example_3_search_memory():
    """Example 3: Search memory"""
    print("="*60)
    print("Example 3: Search Memory")
    print("="*60)
    print()

    agent = Agent.create(
        name="search_demo",
        model_adapter=MockAdapter(config=ModelConfig(model_name="gpt-3.5-turbo")),
        memory_store=InMemoryMemoryStore()
    )

    await agent.initialize()

    # Run various queries
    await agent.run("Calculate 123 * 456")
    await agent.run("What is the weather?")
    await agent.run("Calculate 10 + 20")

    print()

    # Search for calculator-related events
    print("Searching for 'calculator'...")
    results = await agent.search_memory("calculator", limit=5)

    print(f"Found {len(results)} results:")
    for event in results:
        print(f"  - {event.event_type.value}: {event.data}")

    print()


async def example_4_memory_statistics():
    """Example 4: Memory statistics and analysis"""
    print("="*60)
    print("Example 4: Memory Statistics")
    print("="*60)
    print()

    agent = Agent.create(
        name="stats_agent",
        model_adapter=MockAdapter(config=ModelConfig(model_name="gpt-3.5-turbo")),
        tools=[FunctionBuilder.create_tool(calculator, name="calculator")],
        memory_store=InMemoryMemoryStore()
    )

    await agent.initialize()

    # Run multiple operations
    print("Running operations...")
    for i in range(5):
        await agent.run(f"Calculate {i} * {i}")

    # One that will fail
    agent.tools = {}  # Remove tools
    await agent.run("Calculate something")

    print()

    # Get detailed statistics
    stats = await agent.get_memory_stats()

    print("Event Breakdown:")
    for event_type, count in stats["by_type"].items():
        print(f"  {event_type}: {count}")

    print(f"\nFirst event: {stats.get('first_event')}")
    print(f"Last event: {stats.get('last_event')}")

    print()


async def example_5_disable_memory():
    """Example 5: Disable memory storage"""
    print("="*60)
    print("Example 5: Disable Memory")
    print("="*60)
    print()

    # Create agent without memory
    agent = Agent.create(
        name="no_memory_agent",
        model_adapter=MockAdapter(config=ModelConfig(model_name="gpt-3.5-turbo")),
        enable_memory=False  # Disable memory
        memory_store=InMemoryMemoryStore()  # This will be ignored
    )

    await agent.initialize()

    # Run queries
    await agent.run("Hello")

    # Try to get memory - will fail
    try:
        events = await agent.get_memory()
    except RuntimeError as e:
        print(f"Expected error: {e}")

    print()


async def example_6_session_isolation():
    """Example 6: Session-based memory isolation"""
    print("="*60)
    print("Example 6: Session Isolation")
    print("="*60)
    print()

    agent = Agent.create(
        name="session_agent",
        model_adapter=MockAdapter(config=ModelConfig(model_name="gpt-3.5-turbo")),
        memory_store=InMemoryMemoryStore()
    )

    await agent.initialize()

    # Session 1
    print("Session 1:")
    await agent.run("Hello from session 1")
    session1_id = agent.context.session_id

    # Create new context (session 2)
    agent.reset_context()
    print("\nSession 2:")
    await agent.run("Hello from session 2")
    session2_id = agent.context.session_id

    print()

    # Query all events
    all_events = await agent.get_memory(limit=100)
    print(f"Total events: {len(all_events)}")

    # Query session 1 only
    session1_events = await agent.get_memory(session_id=session1_id)
    print(f"Session 1 events: {len(session1_events)}")

    # Query session 2 only
    session2_events = await agent.get_memory(session_id=session2_id)
    print(f"Session 2 events: {len(session2_events)}")

    print()


async def example_7_custom_event_recording():
    """Example 7: Custom event recording"""
    print("="*60)
    print("Example 7: Custom Events")
    print("="*60)
    print()

    agent = Agent.create(
        name="custom_agent",
        model_adapter=MockAdapter(config=ModelConfig(model_name="gpt-3.5-turbo")),
        memory_store=InMemoryMemoryStore()
    )

    await agent.initialize()

    # Record custom events
    from lightagent import AgentEvent

    await agent._record_event(
        EventType.CUSTOM,
        {
            "action": "user_login",
            "user_id": "user123",
            "ip": "192.168.1.1"
        },
        metadata={
            "source": "web",
            "user_agent": "Mozilla/5.0"
        }
    )

    await agent._record_event(
        EventType.CUSTOM,
        {
            "action": "page_view",
            "page": "/dashboard"
        }
    )

    # Query custom events
    custom_events = await agent.get_memory(event_type=EventType.CUSTOM)

    print(f"Custom events: {len(custom_events)}")
    for event in custom_events:
        print(f"  Action: {event.data.get('action')}")
        print(f"  Metadata: {event.metadata}")

    print()


async def main():
    """Run all examples"""
    print("\n" + "="*60)
    print("LightAgent - Memory Storage Examples")
    print("="*60)
    print()

    await example_1_in_memory_storage()
    await example_2_sqlite_storage()
    await example_3_search_memory()
    await example_4_memory_statistics()
    await example_5_disable_memory()
    await example_6_session_isolation()
    await example_7_custom_event_recording()

    print("="*60)
    print("Summary")
    print("="*60)
    print("""
## Memory Storage Features

1. **Modular Storage Backends**
   - InMemoryMemoryStore: In-memory (testing)
   - SQLiteMemoryStore: SQLite database (embedded)
   - MySQLMemoryStore: MySQL server (production)
   - PostgreSQLMemoryStore: PostgreSQL (production)

2. **Automatic Event Recording**
   - USER_MESSAGE: User inputs
   - MODEL_RESPONSE: Model outputs
   - TOOL_CALL_START: Tool invocations
   - TOOL_CALL_SUCCESS: Successful tool calls
   - TOOL_CALL_ERROR: Failed tool calls
   - AGENT_ERROR: Agent errors
   - MIDDLEWARE_PRE/POST: Middleware events
   - CUSTOM: User-defined events

3. **Query Capabilities**
   - Filter by agent/session/type
   - Full-text search
   - Time-range queries
   - Statistics

4. **Usage**
   ```python
   # Create agent with memory
   agent = Agent.create(
       name="assistant",
       model_adapter=adapter,
       memory_store=SQLiteMemoryStore()
   )

   # Events are recorded automatically
   await agent.run("Hello")

   # Query memory
   events = await agent.get_memory()

   # Search memory
   results = await agent.search_memory("hello")

   # Get statistics
   stats = await agent.get_memory_stats()
   ```

5. **Benefits**
   - Debug agent behavior
   - Analyze performance
   - Audit trails
   - Conversation history
   - Usage analytics
    """)


if __name__ == "__main__":
    asyncio.run(main())
