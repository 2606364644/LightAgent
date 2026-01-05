"""
Anthropic (Claude) model adapter
"""
from typing import Any, Dict, List, Optional, AsyncIterator

from ..base import BaseModelAdapter, ModelConfig


class AnthropicAdapter(BaseModelAdapter):
    """
    Anthropic (Claude) model adapter
    Supports Claude 3, Claude 3.5, and other Anthropic models
    """

    def __init__(self, config: ModelConfig):
        super().__init__(config)
        self._client = None

    async def _get_client(self):
        """Get or create Anthropic client"""
        if self._client is None:
            try:
                import anthropic
                self._client = anthropic.AsyncAnthropic(
                    api_key=self.config.api_key,
                    base_url=self.config.api_base
                )
            except ImportError:
                raise ImportError("anthropic package is required. Install: pip install anthropic")

        return self._client

    async def call(
        self,
        messages: List[Dict[str, str]],
        tools: Optional[List[Dict[str, Any]]] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Call Anthropic API"""
        client = await self._get_client()

        # Convert messages to Anthropic format
        system_message = None
        anthropic_messages = []

        for msg in messages:
            if msg["role"] == "system":
                system_message = msg["content"]
            else:
                anthropic_messages.append({
                    "role": msg["role"],
                    "content": msg["content"]
                })

        params = {
            "model": self.config.model_name,
            "messages": anthropic_messages,
            "max_tokens": max_tokens or self.config.max_tokens,
            "temperature": temperature or self.config.temperature,
            **self.config.extra_params
        }

        if system_message:
            params["system"] = system_message

        # Add tools if provided
        if tools and self.supports_function_calling():
            params["tools"] = tools

        try:
            response = await client.messages.create(**params)

            # Extract content and tool calls
            content = ""
            tool_calls = []

            for block in response.content:
                if block.type == "text":
                    content += block.text
                elif block.type == "tool_use":
                    tool_calls.append({
                        "id": block.id,
                        "name": block.name,
                        "arguments": block.input
                    })

            return {
                "content": content,
                "tool_calls": tool_calls,
                "usage": {
                    "prompt_tokens": response.usage.input_tokens,
                    "completion_tokens": response.usage.output_tokens,
                    "total_tokens": response.usage.input_tokens + response.usage.output_tokens
                },
                "model": response.model,
                "finish_reason": response.stop_reason
            }

        except Exception as e:
            raise RuntimeError(f"Anthropic API error: {str(e)}")

    async def stream(
        self,
        messages: List[Dict[str, str]],
        **kwargs
    ) -> AsyncIterator[str]:
        """Stream Anthropic response"""
        client = await self._get_client()

        # Convert messages to Anthropic format
        system_message = None
        anthropic_messages = []

        for msg in messages:
            if msg["role"] == "system":
                system_message = msg["content"]
            else:
                anthropic_messages.append({
                    "role": msg["role"],
                    "content": msg["content"]
                })

        params = {
            "model": self.config.model_name,
            "messages": anthropic_messages,
            "max_tokens": kwargs.get("max_tokens", self.config.max_tokens),
            "temperature": kwargs.get("temperature", self.config.temperature),
            "stream": True,
            **self.config.extra_params
        }

        if system_message:
            params["system"] = system_message

        try:
            async with client.messages.stream(**params) as stream:
                async for text in stream.text_stream:
                    yield text

        except Exception as e:
            raise RuntimeError(f"Anthropic streaming error: {str(e)}")
