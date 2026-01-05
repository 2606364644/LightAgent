"""
Base model adapter interface
"""
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from abc import ABC, abstractmethod
import asyncio


class ModelConfig(BaseModel):
    """Configuration for model adapter"""
    model_name: str
    api_key: Optional[str] = None
    api_base: Optional[str] = None
    temperature: float = 0.7
    max_tokens: int = 2000
    timeout: float = 30.0
    extra_params: Dict[str, Any] = Field(default_factory=dict)


class ModelResponse(BaseModel):
    """Standard model response"""
    content: str
    tool_calls: List[Dict[str, Any]] = Field(default_factory=list)
    usage: Optional[Dict[str, Any]] = None
    model: str = ""
    finish_reason: Optional[str] = None


class BaseModelAdapter(ABC):
    """Base adapter for LLM models"""

    config: ModelConfig

    def __init__(self, config: ModelConfig):
        self.config = config

    @abstractmethod
    async def call(
        self,
        messages: List[Dict[str, str]],
        tools: Optional[List[Dict[str, Any]]] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Call the model with messages

        Args:
            messages: List of message dicts with 'role' and 'content'
            tools: Optional list of tool schemas for function calling
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            **kwargs: Additional model-specific parameters

        Returns:
            Dictionary with 'content', 'tool_calls', and other metadata
        """
        pass

    @abstractmethod
    async def stream(
        self,
        messages: List[Dict[str, str]],
        **kwargs
    ):
        """
        Stream model response

        Args:
            messages: List of message dicts
            **kwargs: Additional parameters

        Yields:
            Chunks of the response
        """
        pass

    def supports_function_calling(self) -> bool:
        """Check if model supports function calling"""
        return True

    def supports_streaming(self) -> bool:
        """Check if model supports streaming"""
        return True

    async def validate_connection(self) -> bool:
        """Validate model connection"""
        try:
            response = await self.call([{"role": "user", "content": "test"}])
            return True
        except:
            return False


class ModelRegistry(BaseModel):
    """Registry for managing model adapters"""

    models: Dict[str, BaseModelAdapter] = Field(default_factory=dict)

    model_config = {"arbitrary_types_allowed": True}

    def register(self, name: str, adapter: BaseModelAdapter):
        """Register a model adapter"""
        self.models[name] = adapter

    def unregister(self, name: str):
        """Unregister a model adapter"""
        if name in self.models:
            del self.models[name]

    def get(self, name: str) -> Optional[BaseModelAdapter]:
        """Get a model adapter by name"""
        return self.models.get(name)

    def list_models(self) -> List[str]:
        """List all registered model names"""
        return list(self.models.keys())
