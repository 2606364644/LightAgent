"""
Multi-Agent Collaboration Example

This example demonstrates:
1. Creating multiple specialized agents
2. Setting up A2A (Agent-to-Agent) communication
3. Agent delegation and collaboration
"""

import asyncio
from lightagent import (
    Agent,
    AgentConfig,
    MessageBus,
    FunctionBuilder,
    MockAdapter,
    ModelConfig
)


# Define specialized functions for each agent
async def search_database(query: str) -> str:
    """
    Search the internal database

    Args:
        query: Search query

    Returns:
        Search results
    """
    # Mock database search
    database = {
        "product": "We have 150 products in our catalog",
        "price": "Prices range from $10 to $1000",
        "stock": "Most items are in stock and ready to ship",
        "shipping": "We offer free shipping on orders over $50"
    }

    for key, value in database.items():
        if key in query.lower():
            return f"Database result: {value}"

    return "Database: No specific information found"


async def calculate_discount(total: float, customer_type: str = "regular") -> dict:
    """
    Calculate discount based on customer type and total

    Args:
        total: Purchase total
        customer_type: Type of customer (regular, vip, wholesale)

    Returns:
        Discount information
    """
    discount_rates = {
        "regular": 0.0,
        "vip": 0.15,
        "wholesale": 0.25
    }

    rate = discount_rates.get(customer_type.lower(), 0.0)
    discount_amount = total * rate
    final_total = total - discount_amount

    return {
        "original_total": total,
        "discount_rate": rate,
        "discount_amount": discount_amount,
        "final_total": final_total,
        "customer_type": customer_type
    }


async def process_order(items: list, address: str) -> dict:
    """
    Process customer order

    Args:
        items: List of items to order
        address: Shipping address

    Returns:
        Order confirmation
    """
    import uuid

    order_id = str(uuid.uuid4())[:8]

    return {
        "order_id": order_id,
        "status": "confirmed",
        "items": items,
        "address": address,
        "estimated_delivery": "3-5 business days"
    }


async def create_agents():
    """Create specialized agents"""

    # Shared model adapter
    model_config = ModelConfig(model_name="gpt-3.5-turbo")
    model_adapter = MockAdapter(config=model_config)

    # Create tools for each agent
    search_tool = FunctionBuilder.create_tool(
        search_database,
        name="search_database",
        description="Search internal database for information"
    )

    discount_tool = FunctionBuilder.create_tool(
        calculate_discount,
        name="calculate_discount",
        description="Calculate discounts based on customer type"
    )

    order_tool = FunctionBuilder.create_tool(
        process_order,
        name="process_order",
        description="Process customer orders"
    )

    # Agent 1: Sales Assistant
    sales_config = AgentConfig(
        name="sales_assistant",
        description="Handles product inquiries and sales",
        system_prompt="""You are a sales assistant. Help customers with:
- Product information
- Pricing questions
- Stock availability
- General inquiries

Use the search_database tool for accurate information.""",
        tools=["search_database"]
    )

    sales_agent = Agent(
        config=sales_config,
        model_adapter=model_adapter
    )
    sales_agent.add_tool(search_tool)

    # Agent 2: Discount Calculator
    discount_config = AgentConfig(
        name="discount_agent",
        description="Calculates discounts and pricing",
        system_prompt="""You are a discount specialist. You can:
- Calculate discounts based on customer type
- Determine final pricing
- Explain discount policies

Use the calculate_discount tool for computations.""",
        tools=["calculate_discount"]
    )

    discount_agent = Agent(
        config=discount_config,
        model_adapter=model_adapter
    )
    discount_agent.add_tool(discount_tool)

    # Agent 3: Order Processor
    order_config = AgentConfig(
        name="order_agent",
        description="Processes orders and shipments",
        system_prompt="""You are an order processing specialist. You can:
- Process new orders
- Confirm shipping details
- Provide order status

Use the process_order tool for order processing.""",
        tools=["process_order"]
    )

    order_agent = Agent(
        config=order_config,
        model_adapter=model_adapter
    )
    order_agent.add_tool(order_tool)

    # Agent 4: Coordinator (orchestrates other agents)
    coordinator_config = AgentConfig(
        name="coordinator",
        description="Main coordinator agent",
        system_prompt="""You are a customer service coordinator. You can:
- Handle general inquiries
- Delegate to specialists when needed
- Coordinate complex requests

For specific tasks, delegate to appropriate agents:
- sales_assistant: Product and pricing questions
- discount_agent: Discount calculations
- order_agent: Order processing""",
        tools=[]
    )

    coordinator = Agent(
        config=coordinator_config,
        model_adapter=model_adapter
    )

    # Create message bus for A2A communication
    message_bus = MessageBus()

    # Initialize all agents
    await sales_agent.initialize()
    await discount_agent.initialize()
    await order_agent.initialize()
    await coordinator.initialize()

    # Register agents with message bus
    await message_bus.register_agent("sales_assistant", sales_agent)
    await message_bus.register_agent("discount_agent", discount_agent)
    await message_bus.register_agent("order_agent", order_agent)
    await message_bus.register_agent("coordinator", coordinator)

    return {
        "coordinator": coordinator,
        "sales": sales_agent,
        "discount": discount_agent,
        "order": order_agent,
        "message_bus": message_bus
    }


async def main():
    # Create agents
    print("=== Initializing Multi-Agent System ===\n")
    agents = await create_agents()

    coordinator = agents["coordinator"]
    message_bus = agents["message_bus"]

    print("Agents ready:")
    print("- coordinator (main)")
    print("- sales_assistant")
    print("- discount_agent")
    print("- order_agent")
    print()

    # Example 1: Product inquiry (delegated to sales)
    print("=== Example 1: Product Inquiry ===")
    result = await coordinator.run("What products do you have and what are the prices?")
    print(f"Response: {result['response']}\n")

    # Example 2: Discount calculation (delegated to discount agent)
    print("=== Example 2: VIP Discount ===")
    result = await coordinator.run("I'm a VIP customer spending $200. What's my discount?")
    print(f"Response: {result['response']}\n")

    # Example 3: Order processing (delegated to order agent)
    print("=== Example 3: Process Order ===")
    result = await coordinator.run("I want to order 2 items to New York")
    print(f"Response: {result['response']}\n")

    # Example 4: Direct A2A communication
    print("=== Example 4: Direct Agent Communication ===")

    # Create message from sales to discount
    message = agents["sales"].context.conversation_history[-1] if agents["sales"].context.conversation_history else None

    # Sales agent sends request to discount agent
    from lightagent import A2AMessage, MessageType

    inquiry = A2AMessage(
        from_agent="sales_assistant",
        to_agent="discount_agent",
        content="Customer wants to know VIP discount on $500 purchase",
        message_type=MessageType.REQUEST
    )

    response = await message_bus.send(
        from_agent="sales_assistant",
        to_agent="discount_agent",
        message=inquiry
    )

    if response:
        print(f"Direct message from sales to discount:")
        print(f"Request: {inquiry.content}")
        print(f"Response: {response.content}\n")

    # Example 5: Broadcast to all agents
    print("=== Example 5: Broadcast Message ===")

    announcement = A2AMessage(
        from_agent="coordinator",
        to_agent="all",
        content="New promotion: 20% off everything!",
        message_type=MessageType.NOTIFICATION
    )

    responses = await message_bus.broadcast(
        from_agent="coordinator",
        message=announcement
    )

    print(f"Broadcast sent to {len(responses)} agents")
    for resp in responses:
        print(f"- {resp.from_agent}: {resp.content[:50]}...")

    # Show message history
    print("\n=== Message History ===")
    history = message_bus.get_message_history(limit=10)
    print(f"Total messages: {len(history)}")
    for msg in history[-5:]:
        print(f"{msg.from_agent} -> {msg.to_agent}: {msg.message_type}")


if __name__ == "__main__":
    asyncio.run(main())
