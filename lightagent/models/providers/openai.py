"""
OpenAI model adapter
"""
from typing import Any, Dict, List, Optional, AsyncIterator
import json

from ..base import BaseModelAdapter, ModelConfig


class OpenAIAdapter(BaseModelAdapter):
    """
    OpenAI model adapter
    Supports GPT-3.5, GPT-4, and other OpenAI models
    """

    def __init__(self, config: ModelConfig):
        super().__init__(config)
        self._client = None

    async def _get_client(self):
        """Get or create OpenAI client"""
        if self._client is None:
            try:
                from openai import AsyncOpenAI
                self._client = AsyncOpenAI(
                    api_key=self.config.api_key,
                    base_url=self.config.api_base
                )
            except ImportError:
                raise ImportError("openai package is required. Install: pip install openai")

        return self._client

    async def call(
        self,
        messages: List[Dict[str, str]],
        tools: Optional[List[Dict[str, Any]]] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Call OpenAI API"""
        client = await self._get_client()

        params = {
            "model": self.config.model_name,
            "messages": messages,
            "temperature": temperature or self.config.temperature,
            "max_tokens": max_tokens or self.config.max_tokens,
            **self.config.extra_params
        }

        # Add tools if provided
        if tools and self.supports_function_calling():
            params["tools"] = tools
            params["tool_choice"] = "auto"

        try:
            response = await client.chat.completions.create(**params)

            # Extract response
            message = response.choices[0].message

            # Parse tool calls
            tool_calls = []
            if hasattr(message, 'tool_calls') and message.tool_calls:
                for tool_call in message.tool_calls:
                    tool_calls.append({
                        "id": tool_call.id,
                        "name": tool_call.function.name,
                        "arguments": json.loads(tool_call.function.arguments)
                    })

            return {
                "content": message.content or "",
                "tool_calls": tool_calls,
                "usage": {
                    "prompt_tokens": response.usage.prompt_tokens if response.usage else 0,
                    "completion_tokens": response.usage.completion_tokens if response.usage else 0,
                    "total_tokens": response.usage.total_tokens if response.usage else 0
                },
                "model": response.model,
                "finish_reason": response.choices[0].finish_reason
            }

        except Exception as e:
            raise RuntimeError(f"OpenAI API error: {str(e)}")

    async def stream(
        self,
        messages: List[Dict[str, str]],
        **kwargs
    ) -> AsyncIterator[str]:
        """Stream OpenAI response"""
        client = await self._get_client()

        params = {
            "model": self.config.model_name,
            "messages": messages,
            "temperature": kwargs.get("temperature", self.config.temperature),
            "max_tokens": kwargs.get("max_tokens", self.config.max_tokens),
            "stream": True,
            **self.config.extra_params
        }

        try:
            stream = await client.chat.completions.create(**params)

            async for chunk in stream:
                if chunk.choices and chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content

        except Exception as e:
            raise RuntimeError(f"OpenAI streaming error: {str(e)}")
