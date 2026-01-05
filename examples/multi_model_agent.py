"""
Multi-Model Function Calling Example

This example demonstrates how to use function calling
with different model providers (OpenAI, Anthropic, etc.)
"""

import asyncio
from lightagent import (
    Agent,
    AgentConfig,
    FunctionBuilder,
    MockAdapter,
    OpenAIAdapter,
    AnthropicAdapter,
    OllamaAdapter,
    ModelConfig
)


# Define example functions
async def get_stock_price(symbol: str) -> dict:
    """
    Get stock price for a given symbol

    Args:
        symbol: Stock symbol (e.g., AAPL, GOOGL)

    Returns:
        Stock price information
    """
    # Mock stock data
    mock_prices = {
        "AAPL": {"price": 178.52, "change": "+2.3%"},
        "GOOGL": {"price": 141.80, "change": "-0.5%"},
        "MSFT": {"price": 378.91, "change": "+1.2%"}
    }

    return mock_prices.get(
        symbol.upper(),
        {"price": "Unknown", "change": "N/A"}
    )


async def convert_currency(amount: float, from_currency: str, to_currency: str) -> dict:
    """
    Convert currency amount

    Args:
        amount: Amount to convert
        from_currency: Source currency (e.g., USD, EUR)
        to_currency: Target currency (e.g., USD, EUR)

    Returns:
        Conversion result
    """
    # Mock exchange rates
    rates = {
        "USD": 1.0,
        "EUR": 0.92,
        "GBP": 0.79,
        "JPY": 149.50
    }

    from_rate = rates.get(from_currency, 1.0)
    to_rate = rates.get(to_currency, 1.0)

    converted = (amount / from_rate) * to_rate

    return {
        "amount": amount,
        "from_currency": from_currency,
        "to_currency": to_currency,
        "result": round(converted, 2),
        "rate": to_rate / from_rate
    }


async def demo_with_provider(provider_name: str, model_adapter):
    """Demo agent with specific provider"""
    print(f"\n{'='*60}")
    print(f"Demo with {provider_name}")
    print(f"{'='*60}\n")

    # Create tools
    stock_tool = FunctionBuilder.create_tool(
        get_stock_price,
        name="get_stock_price",
        description="Get stock price for a symbol"
    )

    currency_tool = FunctionBuilder.create_tool(
        convert_currency,
        name="convert_currency",
        description="Convert between currencies"
    )

    # Configure agent
    agent_config = AgentConfig(
        name=f"{provider_name.lower()}_assistant",
        model_name="gpt-3.5-turbo",  # This would change per provider
        model_provider=provider_name.lower(),
        system_prompt="""You are a financial assistant. Use the available tools to help with:
1. Stock price queries
2. Currency conversions

Always use the tools when users ask about stocks or currencies.""",
        tools=["get_stock_price", "convert_currency"]
    )

    # Create agent
    agent = Agent(
        config=agent_config,
        model_adapter=model_adapter
    )

    agent.add_tool(stock_tool)
    agent.add_tool(currency_tool)

    # Initialize
    await agent.initialize()

    # Test queries
    queries = [
        "What's the stock price of AAPL?",
        "Convert 100 USD to EUR",
        "How much is 50 GBP in JPY?"
    ]

    for query in queries:
        print(f"Query: {query}")
        result = await agent.run(query)

        if result.get("success"):
            print(f"Response: {result['response']}")
            if result.get("tool_calls"):
                tools_used = [tc.get("name", "unknown") for tc in result["tool_calls"]]
                print(f"Tools used: {tools_used}")
        else:
            print(f"Error: {result.get('error')}")
        print()


async def main():
    print("=" * 60)
    print("LightAgent - Multi-Model Function Calling Demo")
    print("=" * 60)

    # Demo 1: Mock adapter (for testing)
    print("\n### Demo 1: Mock Adapter (Testing) ###")
    mock_config = ModelConfig(model_name="mock-model")
    mock_adapter = MockAdapter(config=mock_config)
    await demo_with_provider("Mock", mock_adapter)

    # Demo 2: OpenAI (uncomment to use with real API)
    # print("\n### Demo 2: OpenAI ###")
    # openai_config = ModelConfig(
    #     model_name="gpt-3.5-turbo",
    #     api_key="your-openai-api-key"  # Or set OPENAI_API_KEY env var
    # )
    # openai_adapter = OpenAIAdapter(config=openai_config)
    # await demo_with_provider("OpenAI", openai_adapter)

    # Demo 3: Anthropic (uncomment to use with real API)
    # print("\n### Demo 3: Anthropic (Claude) ###")
    # anthropic_config = ModelConfig(
    #     model_name="claude-3-sonnet-20240229",
    #     api_key="your-anthropic-api-key"  # Or set ANTHROPIC_API_KEY env var
    # )
    # anthropic_adapter = AnthropicAdapter(config=anthropic_config)
    # await demo_with_provider("Anthropic", anthropic_adapter)

    # Demo 4: Ollama (uncomment if you have Ollama running)
    # print("\n### Demo 4: Ollama (Local) ###")
    # ollama_config = ModelConfig(
    #     model_name="llama2",
    #     api_base="http://localhost:11434"
    # )
    # ollama_adapter = OllamaAdapter(config=ollama_config)
    # await demo_with_provider("Ollama", ollama_adapter)

    print("\n" + "=" * 60)
    print("Summary")
    print("=" * 60)
    print("""
The framework automatically handles function calling format differences
between model providers:

1. OpenAI: Uses standard OpenAI function calling format
2. Anthropic: Uses Claude's tool use format
3. Ollama: Uses OpenAI-compatible format
4. Custom: Easy to add new providers

Key features:
- Automatic schema conversion
- Transparent tool call parsing
- Provider-agnostic tool definitions
- Easy to switch between models

To use with real models:
1. Set your API key as environment variable
2. Uncomment the provider section above
3. Run the script

Example:
  export OPENAI_API_KEY="sk-..."
  python multi_model_agent.py
    """)


if __name__ == "__main__":
    asyncio.run(main())
