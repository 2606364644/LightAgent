"""
Mock model adapter for testing
"""
from typing import Any, Dict, List, Optional, AsyncIterator
import asyncio

from ..base import BaseModelAdapter, ModelConfig


class MockAdapter(BaseModelAdapter):
    """
    Mock model adapter for testing
    Returns pre-defined responses without calling actual APIs
    """

    async def call(
        self,
        messages: List[Dict[str, str]],
        tools: Optional[List[Dict[str, Any]]] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Mock call that returns test response"""
        # Get last user message
        last_message = ""
        for msg in reversed(messages):
            if msg["role"] == "user":
                last_message = msg["content"]
                break

        # Simulate tool call based on message content
        tool_calls = []
        if tools and "calculate" in last_message.lower():
            tool_calls.append({
                "id": "mock_tool_1",
                "name": "calculator",
                "arguments": {"expression": "2 + 2"}
            })

        return {
            "content": f"Mock response to: {last_message[:100]}",
            "tool_calls": tool_calls,
            "usage": {
                "prompt_tokens": sum(len(m.get("content", "")) for m in messages),
                "completion_tokens": 50,
                "total_tokens": 100
            },
            "model": self.config.model_name,
            "finish_reason": "stop"
        }

    async def stream(
        self,
        messages: List[Dict[str, str]],
        **kwargs
    ) -> AsyncIterator[str]:
        """Mock streaming"""
        response = "Mock streaming response"
        for char in response:
            yield char
            await asyncio.sleep(0.01)
