"""
Simple demonstration of LightAgent framework

This is a minimal example showing the core features.
"""

import asyncio
from lightagent import (
    Agent,
    AgentConfig,
    FunctionBuilder,
    MockAdapter,
    ModelConfig,
    LoggingMiddleware,
    CacheMiddleware
)


# Define a simple function
async def greet(name: str, title: str = "Mr/Ms") -> str:
    """
    Greet a person

    Args:
        name: Person's name
        title: Optional title

    Returns:
        Greeting message
    """
    return f"Hello, {title} {name}!"


async def main():
    print("=" * 60)
    print("LightAgent - Simple Demo")
    print("=" * 60)
    print()

    # Step 1: Create model adapter (using mock for demo)
    print("[Step 1] Creating model adapter...")
    model_config = ModelConfig(model_name="gpt-3.5-turbo")
    model_adapter = MockAdapter(config=model_config)
    print("Model adapter created (Mock mode)\n")

    # Step 2: Create a tool
    print("[Step 2] Creating tool...")
    greet_tool = FunctionBuilder.create_tool(
        greet,
        name="greet",
        description="Greet someone by name"
    )
    print(f"Tool '{greet_tool.name}' created\n")

    # Step 3: Configure agent
    print("[Step 3] Configuring agent...")
    agent_config = AgentConfig(
        name="demo_agent",
        description="A simple demo agent",
        system_prompt="You are a friendly assistant. Use the greet tool when someone asks to be greeted.",
        tools=["greet"],
        max_iterations=3
    )
    print(f"Agent '{agent_config.name}' configured\n")

    # Step 4: Create and setup agent
    print("[Step 4] Creating agent...")
    agent = Agent(
        config=agent_config,
        model_adapter=model_adapter
    )

    # Add tool
    agent.add_tool(greet_tool)

    # Add middleware (optional)
    from lightagent import MiddlewareManager
    middleware_manager = MiddlewareManager()
    middleware_manager.add(LoggingMiddleware())
    middleware_manager.add(CacheMiddleware())
    agent.middlewares = middleware_manager

    print("Agent created and configured\n")

    # Step 5: Initialize agent
    print("[Step 5] Initializing agent...")
    await agent.initialize()
    print("Agent initialized\n")

    # Step 6: Run agent
    print("[Step 6] Running agent interactions")
    print("-" * 60)

    queries = [
        "Hello!",
        "Please greet Alice",
        "Can you greet Dr. Smith?",
        "Goodbye!"
    ]

    for query in queries:
        print(f"\nUser: {query}")
        result = await agent.run(query)

        status = "SUCCESS" if result.get("success") else "ERROR"
        print(f"Agent [{status}]: {result['response']}")

        if result.get("tool_calls"):
            print(f"  Tools used: {[t['name'] for t in result['tool_calls']]}")

    print()
    print("-" * 60)

    # Show statistics
    print("\n[Session Statistics]")
    context = agent.get_context()
    print(f"Session ID: {context.session_id}")
    print(f"Conversation turns: {len(context.conversation_history)}")
    print(f"Total iterations: {sum(turn.get('iterations', 0) for turn in context.conversation_history if isinstance(turn, dict))}")

    print()
    print("=" * 60)
    print("Demo completed successfully!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
