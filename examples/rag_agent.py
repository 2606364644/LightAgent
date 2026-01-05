"""
RAG Agent Example

This example demonstrates:
1. Creating an agent with RAG (Retrieval-Augmented Generation) capabilities
2. Building a knowledge base
3. Querying the knowledge base
"""

import asyncio
from lightagent import (
    Agent,
    AgentConfig,
    RAGTool,
    RAGConfig,
    KnowledgeBase,
    MockAdapter,
    ModelConfig
)


async def main():
    # Create model adapter
    model_config = ModelConfig(model_name="gpt-3.5-turbo")
    model_adapter = MockAdapter(config=model_config)

    # Create RAG tool
    rag_config = RAGConfig(
        top_k=3,
        similarity_threshold=0.0  # Lower threshold for demo
    )

    rag_tool = RAGTool(config=rag_config)

    # Create knowledge base
    knowledge_base = KnowledgeBase(rag_tool=rag_tool)

    # Add documents to knowledge base
    print("=== Building Knowledge Base ===\n")

    sample_documents = [
        {
            "text": """
LightAgent is a lightweight Python framework for building AI agents.
It supports modular agent configuration, tool calling, middleware pipeline,
and agent-to-agent communication using A2A protocol.
            """,
            "metadata": {"title": "About LightAgent", "category": "overview"}
        },
        {
            "text": """
The framework supports multiple tool types:
1. MCP (Model Context Protocol) tools for external integrations
2. Function Call tools for wrapping Python functions
3. RAG tools for retrieval-augmented generation

All tools can be easily configured and extended.
            """,
            "metadata": {"title": "Tool System", "category": "features"}
        },
        {
            "text": """
Middleware system allows pre and post-processing of agent interactions.
Built-in middleware includes logging, rate limiting, caching, validation,
and retry logic. Custom middleware can be easily added.
            """,
            "metadata": {"title": "Middleware System", "category": "features"}
        },
        {
            "text": """
LightAgent supports multiple LLM providers including OpenAI (GPT-3.5, GPT-4),
Anthropic (Claude), Ollama for local models, and a mock adapter for testing.
Switching between models is as simple as changing the model adapter.
            """,
            "metadata": {"title": "Model Support", "category": "features"}
        },
        {
            "text": """
The A2A (Agent-to-Agent) protocol enables inter-agent communication.
Agents can send messages to each other, delegate tasks, and collaborate
to solve complex problems. This enables multi-agent workflows.
            """,
            "metadata": {"title": "A2A Protocol", "category": "communication"}
        }
    ]

    # Add documents to knowledge base
    for doc in sample_documents:
        await knowledge_base.add_text(doc["text"], doc["metadata"])
        print(f"Added: {doc['metadata']['title']}")

    print("\n=== Knowledge Base Ready ===\n")

    # Configure RAG agent
    agent_config = AgentConfig(
        name="rag_assistant",
        description="Assistant with RAG knowledge base",
        system_prompt="""You are a helpful assistant with access to a knowledge base about LightAgent.
When answering questions, use the rag_tool to retrieve relevant information first.""",
        tools=["rag_tool"],
        max_iterations=3
    )

    # Create agent with RAG tool
    agent = Agent(
        config=agent_config,
        model_adapter=model_adapter
    )

    # Add RAG tool
    agent.add_tool(rag_tool)

    # Initialize agent
    await agent.initialize()

    # Example queries
    queries = [
        "What is LightAgent?",
        "What types of tools are supported?",
        "How does middleware work?",
        "Can agents communicate with each other?",
        "Which LLM providers are supported?"
    ]

    print("=== Querying Knowledge Base ===\n")

    for query in queries:
        print(f"Query: {query}")

        # Direct knowledge base search
        search_result = await knowledge_base.search(query, top_k=2)
        print(f"Found {search_result.get('num_results', 0)} relevant documents")

        # Agent query
        result = await agent.run(query)
        print(f"Response: {result['response'][:200]}...")
        print()
        await asyncio.sleep(0.5)  # Small delay between queries


if __name__ == "__main__":
    asyncio.run(main())
