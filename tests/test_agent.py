"""
Simple tests for LightAgent framework
"""

import asyncio
import pytest
from lightagent import (
    Agent,
    AgentConfig,
    AgentContext,
    MockAdapter,
    ModelConfig,
    FunctionBuilder,
    A2AMessage,
    MessageBus,
    MessageType
)


class TestAgentBasics:
    """Test basic agent functionality"""

    @pytest.fixture
    def model_adapter(self):
        """Create mock model adapter"""
        config = ModelConfig(model_name="test-model")
        return MockAdapter(config=config)

    @pytest.fixture
    async def agent(self, model_adapter):
        """Create a test agent"""
        config = AgentConfig(
            name="test_agent",
            description="Test agent"
        )
        agent = Agent(config=config, model_adapter=model_adapter)
        await agent.initialize()
        return agent

    @pytest.mark.asyncio
    async def test_agent_creation(self, agent):
        """Test agent can be created"""
        assert agent.config.name == "test_agent"
        assert agent.context is not None

    @pytest.mark.asyncio
    async def test_agent_run(self, agent):
        """Test agent can run"""
        result = await agent.run("Hello")
        assert "response" in result
        assert isinstance(result["response"], str)

    @pytest.mark.asyncio
    async def test_context_management(self, agent):
        """Test conversation context"""
        await agent.run("First message")
        await agent.run("Second message")

        context = agent.get_context()
        assert len(context.conversation_history) >= 4  # 2 user + 2 assistant

    @pytest.mark.asyncio
    async def test_context_reset(self, agent):
        """Test context reset"""
        await agent.run("Test")
        agent.reset_context()

        context = agent.get_context()
        assert len(context.conversation_history) == 0


class TestTools:
    """Test tool functionality"""

    @pytest.fixture
    def model_adapter(self):
        config = ModelConfig(model_name="test-model")
        return MockAdapter(config=config)

    @pytest.fixture
    async def calculator_tool(self):
        """Create a calculator tool"""
        async def add(a: float, b: float) -> float:
            return a + b

        return FunctionBuilder.create_tool(
            add,
            name="add",
            description="Add two numbers"
        )

    @pytest.mark.asyncio
    async def test_tool_creation(self, calculator_tool):
        """Test tool can be created"""
        assert calculator_tool.name == "add"
        assert calculator_tool.description is not None

    @pytest.mark.asyncio
    async def test_tool_execution(self, calculator_tool):
        """Test tool can be executed"""
        result = await calculator_tool.execute(a=5, b=3)
        assert result.success is True
        assert result.result == 8

    @pytest.mark.asyncio
    async def test_agent_with_tool(self, model_adapter, calculator_tool):
        """Test agent can use tools"""
        config = AgentConfig(
            name="calculator_agent",
            system_prompt="Use the add tool when asked to add numbers",
            tools=["add"]
        )

        agent = Agent(config=config, model_adapter=model_adapter)
        agent.add_tool(calculator_tool)
        await agent.initialize()

        result = await agent.run("What is 5 plus 3?")
        assert "response" in result


class TestA2AProtocol:
    """Test A2A protocol communication"""

    @pytest.fixture
    def model_adapter(self):
        config = ModelConfig(model_name="test-model")
        return MockAdapter(config=config)

    @pytest.fixture
    async def message_bus(self):
        """Create message bus"""
        return MessageBus()

    @pytest.fixture
    async def agents(self, model_adapter, message_bus):
        """Create two test agents"""
        agent1_config = AgentConfig(name="agent1")
        agent2_config = AgentConfig(name="agent2")

        agent1 = Agent(config=agent1_config, model_adapter=model_adapter)
        agent2 = Agent(config=agent2_config, model_adapter=model_adapter)

        await agent1.initialize()
        await agent2.initialize()

        await message_bus.register_agent("agent1", agent1)
        await message_bus.register_agent("agent2", agent2)

        return {"agent1": agent1, "agent2": agent2, "bus": message_bus}

    @pytest.mark.asyncio
    async def test_message_creation(self):
        """Test A2A message can be created"""
        message = A2AMessage(
            from_agent="agent1",
            to_agent="agent2",
            content="Hello"
        )

        assert message.from_agent == "agent1"
        assert message.to_agent == "agent2"
        assert message.message_type == MessageType.REQUEST

    @pytest.mark.asyncio
    async def test_agent_communication(self, agents):
        """Test agents can communicate"""
        agent1 = agents["agent1"]
        agent2 = agents["agent2"]
        message_bus = agents["bus"]

        message = A2AMessage(
            from_agent="agent1",
            to_agent="agent2",
            content="Hello from agent1"
        )

        response = await message_bus.send(
            from_agent="agent1",
            to_agent="agent2",
            message=message
        )

        assert response is not None
        assert response.to_agent == "agent1"

    @pytest.mark.asyncio
    async def test_broadcast(self, agents):
        """Test broadcast to all agents"""
        agent1 = agents["agent1"]
        message_bus = agents["bus"]

        message = A2AMessage(
            from_agent="agent1",
            to_agent="all",
            content="Broadcast message"
        )

        responses = await message_bus.broadcast(
            from_agent="agent1",
            message=message
        )

        assert len(responses) >= 1


class TestMiddleware:
    """Test middleware functionality"""

    @pytest.fixture
    def model_adapter(self):
        config = ModelConfig(model_name="test-model")
        return MockAdapter(config=config)

    @pytest.mark.asyncio
    async def test_middleware_manager(self):
        """Test middleware manager"""
        from lightagent import MiddlewareManager, LoggingMiddleware

        manager = MiddlewareManager()
        logging_mw = LoggingMiddleware()

        manager.add(logging_mw)

        assert len(manager.pre_middlewares) > 0
        assert len(manager.post_middlewares) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
