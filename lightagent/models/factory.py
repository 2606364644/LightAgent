"""
Factory for creating model adapters
"""
from typing import Optional
from .base import BaseModelAdapter, ModelConfig
from .providers import OpenAIAdapter, AnthropicAdapter, OllamaAdapter, MockAdapter


class AdapterFactory:
    """Factory for creating model adapter instances"""

    _adapters = {
        "openai": OpenAIAdapter,
        "anthropic": AnthropicAdapter,
        "ollama": OllamaAdapter,
        "mock": MockAdapter,
    }

    @classmethod
    def create(cls, provider: str, config: ModelConfig) -> BaseModelAdapter:
        """
        Create a model adapter instance

        Args:
            provider: Provider name (e.g., "openai", "anthropic")
            config: Model configuration

        Returns:
            Model adapter instance

        Raises:
            ValueError: If provider is not supported
        """
        provider_lower = provider.lower()

        if provider_lower not in cls._adapters:
            supported = ", ".join(cls._adapters.keys())
            raise ValueError(
                f"Unsupported provider: {provider}. "
                f"Supported providers: {supported}"
            )

        adapter_class = cls._adapters[provider_lower]
        return adapter_class(config)

    @classmethod
    def register_adapter(cls, provider: str, adapter_class: type):
        """
        Register a new adapter type

        Args:
            provider: Provider name
            adapter_class: Adapter class (must inherit from BaseModelAdapter)
        """
        if not issubclass(adapter_class, BaseModelAdapter):
            raise TypeError(
                f"Adapter class must inherit from BaseModelAdapter, "
                f"got {adapter_class}"
            )

        cls._adapters[provider.lower()] = adapter_class

    @classmethod
    def list_providers(cls) -> list[str]:
        """List all registered providers"""
        return list(cls._adapters.keys())


def create_adapter(provider: str, config: ModelConfig) -> BaseModelAdapter:
    """
    Convenience function to create a model adapter

    Args:
        provider: Provider name (e.g., "openai", "anthropic")
        config: Model configuration

    Returns:
        Model adapter instance
    """
    return AdapterFactory.create(provider, config)
