"""
Ollama model adapter for local models
"""
from typing import Any, Dict, List, Optional, AsyncIterator
import json

from ..base import BaseModelAdapter, ModelConfig


class OllamaAdapter(BaseModelAdapter):
    """
    Ollama model adapter for local models
    Supports running local LLMs via Ollama
    """

    def __init__(self, config: ModelConfig):
        super().__init__(config)
        self.api_base = config.api_base or "http://localhost:11434"

    async def call(
        self,
        messages: List[Dict[str, str]],
        tools: Optional[List[Dict[str, Any]]] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Call Ollama API"""
        try:
            import aiohttp
        except ImportError:
            raise ImportError("aiohttp is required for Ollama. Install: pip install aiohttp")

        url = f"{self.api_base}/api/chat"

        payload = {
            "model": self.config.model_name,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": temperature or self.config.temperature,
                "num_predict": max_tokens or self.config.max_tokens
            }
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise RuntimeError(f"Ollama API error: {error_text}")

                data = await response.json()

                return {
                    "content": data.get("message", {}).get("content", ""),
                    "tool_calls": [],
                    "usage": {
                        "prompt_tokens": data.get("prompt_eval_count", 0),
                        "completion_tokens": data.get("eval_count", 0),
                        "total_tokens": data.get("prompt_eval_count", 0) + data.get("eval_count", 0)
                    },
                    "model": self.config.model_name,
                    "finish_reason": "stop"
                }

    async def stream(
        self,
        messages: List[Dict[str, str]],
        **kwargs
    ) -> AsyncIterator[str]:
        """Stream Ollama response"""
        try:
            import aiohttp
        except ImportError:
            raise ImportError("aiohttp is required for Ollama. Install: pip install aiohttp")

        url = f"{self.api_base}/api/chat"

        payload = {
            "model": self.config.model_name,
            "messages": messages,
            "stream": True
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload) as response:
                async for line in response.content:
                    if line:
                        try:
                            data = json.loads(line)
                            if "message" in data and "content" in data["message"]:
                                yield data["message"]["content"]
                        except json.JSONDecodeError:
                            continue
