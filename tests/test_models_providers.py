"""
Unit tests for model provider adapters
"""

import asyncio
import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from lightagent.models import (
    ModelConfig,
    AdapterFactory,
    create_adapter,
    OpenAIAdapter,
    AnthropicAdapter,
    OllamaAdapter,
    MockAdapter
)


class TestAdapterFactory:
    """Test adapter factory functionality"""

    @pytest.fixture
    def model_config(self):
        """Create test model config"""
        return ModelConfig(
            model_name="test-model",
            api_key="test-key",
            temperature=0.7,
            max_tokens=1000
        )

    def test_create_openai_adapter(self, model_config):
        """Test creating OpenAI adapter"""
        adapter = AdapterFactory.create("openai", model_config)
        assert isinstance(adapter, OpenAIAdapter)
        assert adapter.config.model_name == "test-model"

    def test_create_anthropic_adapter(self, model_config):
        """Test creating Anthropic adapter"""
        adapter = AdapterFactory.create("anthropic", model_config)
        assert isinstance(adapter, AnthropicAdapter)
        assert adapter.config.model_name == "test-model"

    def test_create_ollama_adapter(self, model_config):
        """Test creating Ollama adapter"""
        adapter = AdapterFactory.create("ollama", model_config)
        assert isinstance(adapter, OllamaAdapter)
        assert adapter.config.model_name == "test-model"

    def test_create_mock_adapter(self, model_config):
        """Test creating Mock adapter"""
        adapter = AdapterFactory.create("mock", model_config)
        assert isinstance(adapter, MockAdapter)
        assert adapter.config.model_name == "test-model"

    def test_case_insensitive_provider_name(self, model_config):
        """Test provider names are case insensitive"""
        adapters = [
            AdapterFactory.create("OpenAI", model_config),
            AdapterFactory.create("ANTHROPIC", model_config),
            AdapterFactory.create("Ollama", model_config),
            AdapterFactory.create("Mock", model_config)
        ]
        assert isinstance(adapters[0], OpenAIAdapter)
        assert isinstance(adapters[1], AnthropicAdapter)
        assert isinstance(adapters[2], OllamaAdapter)
        assert isinstance(adapters[3], MockAdapter)

    def test_invalid_provider_raises_error(self, model_config):
        """Test invalid provider name raises ValueError"""
        with pytest.raises(ValueError) as exc_info:
            AdapterFactory.create("invalid_provider", model_config)
        assert "Unsupported provider" in str(exc_info.value)

    def test_list_providers(self):
        """Test listing all registered providers"""
        providers = AdapterFactory.list_providers()
        assert "openai" in providers
        assert "anthropic" in providers
        assert "ollama" in providers
        assert "mock" in providers
        assert len(providers) == 4

    def test_create_adapter_convenience_function(self, model_config):
        """Test create_adapter convenience function"""
        adapter = create_adapter("openai", model_config)
        assert isinstance(adapter, OpenAIAdapter)


class TestOpenAIAdapter:
    """Test OpenAI adapter functionality"""

    @pytest.fixture
    def config(self):
        """Create OpenAI config"""
        return ModelConfig(
            model_name="gpt-3.5-turbo",
            api_key="test-key"
        )

    @pytest.fixture
    def adapter(self, config):
        """Create OpenAI adapter"""
        return OpenAIAdapter(config)

    @pytest.mark.asyncio
    async def test_supports_function_calling(self, adapter):
        """Test adapter supports function calling"""
        assert adapter.supports_function_calling() is True

    @pytest.mark.asyncio
    async def test_supports_streaming(self, adapter):
        """Test adapter supports streaming"""
        assert adapter.supports_streaming() is True

    @pytest.mark.asyncio
    @patch("openai.AsyncOpenAI")
    async def test_call_with_messages(self, mock_openai, adapter):
        """Test calling OpenAI API with messages"""
        # Setup mock response
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "Test response"
        mock_response.choices[0].message.tool_calls = None
        mock_response.choices[0].finish_reason = "stop"
        mock_response.model = "gpt-3.5-turbo"
        mock_response.usage.prompt_tokens = 10
        mock_response.usage.completion_tokens = 20
        mock_response.usage.total_tokens = 30

        mock_client = AsyncMock()
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
        mock_openai.return_value = mock_client

        # Test call
        messages = [{"role": "user", "content": "Hello"}]
        response = await adapter.call(messages)

        assert response["content"] == "Test response"
        assert response["tool_calls"] == []
        assert response["usage"]["total_tokens"] == 30
        assert response["model"] == "gpt-3.5-turbo"

    @pytest.mark.asyncio
    @patch("openai.AsyncOpenAI")
    async def test_call_with_tools(self, mock_openai, adapter):
        """Test calling OpenAI API with tools"""
        # Setup mock response with tool calls
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = None
        mock_response.choices[0].finish_reason = "tool_calls"
        mock_response.model = "gpt-3.5-turbo"

        # Mock tool call
        mock_tool_call = Mock()
        mock_tool_call.id = "call_123"
        mock_tool_call.function.name = "calculator"
        mock_tool_call.function.arguments = '{"expression": "2+2"}'
        mock_response.choices[0].message.tool_calls = [mock_tool_call]

        mock_response.usage.prompt_tokens = 10
        mock_response.usage.completion_tokens = 20
        mock_response.usage.total_tokens = 30

        mock_client = AsyncMock()
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
        mock_openai.return_value = mock_client

        # Test call with tools
        messages = [{"role": "user", "content": "Calculate 2+2"}]
        tools = [{
            "type": "function",
            "function": {
                "name": "calculator",
                "description": "Calculate expressions",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "expression": {"type": "string"}
                    }
                }
            }
        }]
        response = await adapter.call(messages, tools=tools)

        assert len(response["tool_calls"]) == 1
        assert response["tool_calls"][0]["name"] == "calculator"
        assert response["tool_calls"][0]["arguments"]["expression"] == "2+2"


class TestAnthropicAdapter:
    """Test Anthropic adapter functionality"""

    @pytest.fixture
    def config(self):
        """Create Anthropic config"""
        return ModelConfig(
            model_name="claude-3-sonnet",
            api_key="test-key"
        )

    @pytest.fixture
    def adapter(self, config):
        """Create Anthropic adapter"""
        return AnthropicAdapter(config)

    @pytest.mark.asyncio
    async def test_supports_function_calling(self, adapter):
        """Test adapter supports function calling"""
        assert adapter.supports_function_calling() is True

    @pytest.mark.asyncio
    @patch("anthropic.AsyncAnthropic")
    async def test_call_with_system_message(self, mock_anthropic, adapter):
        """Test calling Anthropic API with system message"""
        # Setup mock response
        mock_response = Mock()
        mock_content_block = Mock()
        mock_content_block.type = "text"
        mock_content_block.text = "Test response"

        mock_response.content = [mock_content_block]
        mock_response.model = "claude-3-sonnet"
        mock_response.stop_reason = "end_turn"
        mock_response.usage.input_tokens = 10
        mock_response.usage.output_tokens = 20

        mock_client = AsyncMock()
        mock_client.messages.create = AsyncMock(return_value=mock_response)
        mock_anthropic.return_value = mock_client

        # Test call with system message
        messages = [
            {"role": "system", "content": "You are a helpful assistant"},
            {"role": "user", "content": "Hello"}
        ]
        response = await adapter.call(messages)

        assert response["content"] == "Test response"
        assert response["usage"]["total_tokens"] == 30
        assert response["finish_reason"] == "end_turn"


class TestOllamaAdapter:
    """Test Ollama adapter functionality"""

    @pytest.fixture
    def config(self):
        """Create Ollama config"""
        return ModelConfig(
            model_name="llama2",
            api_base="http://localhost:11434"
        )

    @pytest.fixture
    def adapter(self, config):
        """Create Ollama adapter"""
        return OllamaAdapter(config)

    @pytest.mark.asyncio
    @patch("aiohttp.ClientSession")
    async def test_call_ollama_api(self, mock_session_cls, adapter):
        """Test calling Ollama API"""
        # Setup mock response
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={
            "message": {"content": "Ollama response"},
            "prompt_eval_count": 10,
            "eval_count": 20
        })

        # Create async context manager for post response
        async def mock_post_context_manager(*args, **kwargs):
            return mock_response

        mock_post_cm = AsyncMock()
        mock_post_cm.__aenter__ = AsyncMock(return_value=mock_response)
        mock_post_cm.__aexit__ = AsyncMock()

        # Setup mock session instance with post method
        mock_session_instance = AsyncMock()
        mock_session_instance.post = Mock(return_value=mock_post_cm)
        mock_session_instance.__aenter__ = AsyncMock(return_value=mock_session_instance)
        mock_session_instance.__aexit__ = AsyncMock()

        # Setup mock session class
        mock_session_cls.return_value = mock_session_instance

        # Test call
        messages = [{"role": "user", "content": "Hello"}]
        response = await adapter.call(messages)

        assert response["content"] == "Ollama response"
        assert response["usage"]["prompt_tokens"] == 10
        assert response["usage"]["completion_tokens"] == 20


class TestMockAdapter:
    """Test Mock adapter functionality"""

    @pytest.fixture
    def config(self):
        """Create mock config"""
        return ModelConfig(model_name="mock-model")

    @pytest.fixture
    def adapter(self, config):
        """Create mock adapter"""
        return MockAdapter(config)

    @pytest.mark.asyncio
    async def test_call_returns_response(self, adapter):
        """Test mock adapter returns response"""
        messages = [{"role": "user", "content": "Hello"}]
        response = await adapter.call(messages)

        assert "content" in response
        assert "Mock response" in response["content"]
        assert response["model"] == "mock-model"
        assert response["finish_reason"] == "stop"

    @pytest.mark.asyncio
    async def test_call_with_tool_simulation(self, adapter):
        """Test mock adapter simulates tool calls"""
        messages = [{"role": "user", "content": "Please calculate 2+2"}]
        tools = [{"name": "calculator"}]
        response = await adapter.call(messages, tools=tools)

        assert len(response["tool_calls"]) > 0
        assert response["tool_calls"][0]["name"] == "calculator"

    @pytest.mark.asyncio
    async def test_stream_returns_text(self, adapter):
        """Test mock adapter streams text"""
        messages = [{"role": "user", "content": "Hello"}]
        chunks = []

        async for chunk in adapter.stream(messages):
            chunks.append(chunk)

        full_response = "".join(chunks)
        assert full_response == "Mock streaming response"

    @pytest.mark.asyncio
    async def test_supports_function_calling(self, adapter):
        """Test mock adapter supports function calling"""
        assert adapter.supports_function_calling() is True

    @pytest.mark.asyncio
    async def test_supports_streaming(self, adapter):
        """Test mock adapter supports streaming"""
        assert adapter.supports_streaming() is True
