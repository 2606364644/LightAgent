"""
Tool Schema conversion for different model providers
"""
from typing import Any, Dict, List, Optional
from pydantic import BaseModel
import json


class BaseSchemaConverter(BaseModel):
    """Base class for schema conversion"""

    def convert_to_openai(self, tool_schema: Dict[str, Any]) -> Dict[str, Any]:
        """Convert tool schema to OpenAI format"""
        return {
            "type": "function",
            "function": {
                "name": tool_schema.get("name"),
                "description": tool_schema.get("description", ""),
                "parameters": tool_schema.get("parameters", {})
            }
        }

    def convert_to_anthropic(self, tool_schema: Dict[str, Any]) -> Dict[str, Any]:
        """Convert tool schema to Anthropic (Claude) format"""
        parameters = tool_schema.get("parameters", {})

        return {
            "name": tool_schema.get("name"),
            "description": tool_schema.get("description", ""),
            "input_schema": parameters
        }

    def convert_to_ollama(self, tool_schema: Dict[str, Any]) -> Dict[str, Any]:
        """Convert tool schema to Ollama format"""
        return {
            "function": {
                "name": tool_schema.get("name"),
                "description": tool_schema.get("description", ""),
                "parameters": tool_schema.get("parameters", {})
            }
        }


class ToolCallFormatter(BaseModel):
    """Format tool calls for different providers"""

    @staticmethod
    def format_openai_tool_call(tool_call: Dict[str, Any]) -> Dict[str, Any]:
        """Format tool call from OpenAI response"""
        return {
            "id": tool_call.get("id", ""),
            "name": tool_call.get("function", {}).get("name", ""),
            "arguments": json.loads(tool_call.get("function", {}).get("arguments", "{}"))
        }

    @staticmethod
    def format_anthropic_tool_call(tool_call: Dict[str, Any]) -> Dict[str, Any]:
        """Format tool call from Anthropic response"""
        return {
            "id": tool_call.get("id", ""),
            "name": tool_call.get("name", ""),
            "arguments": tool_call.get("input", {})
        }

    @staticmethod
    def format_ollama_tool_call(tool_call: Dict[str, Any]) -> Dict[str, Any]:
        """Format tool call from Ollama response"""
        return {
            "id": tool_call.get("id", ""),
            "name": tool_call.get("name", ""),
            "arguments": tool_call.get("arguments", {})
        }


class FunctionCallAdapter(BaseModel):
    """
    Adapter for handling function calling across different model providers
    Converts between universal format and provider-specific formats
    """

    provider: str = "openai"  # openai, anthropic, ollama
    schema_converter: BaseSchemaConverter = BaseSchemaConverter()
    call_formatter: ToolCallFormatter = ToolCallFormatter()

    def convert_schemas(
        self,
        tool_schemas: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Convert tool schemas to provider format

        Args:
            tool_schemas: List of tool schemas in universal format

        Returns:
            List of provider-formatted schemas
        """
        converted = []

        for schema in tool_schemas:
            if self.provider == "openai":
                converted.append(self.schema_converter.convert_to_openai(schema))
            elif self.provider == "anthropic":
                converted.append(self.schema_converter.convert_to_anthropic(schema))
            elif self.provider == "ollama":
                converted.append(self.schema_converter.convert_to_ollama(schema))
            else:
                # Default to OpenAI format
                converted.append(self.schema_converter.convert_to_openai(schema))

        return converted

    def parse_tool_calls(
        self,
        raw_tool_calls: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Parse tool calls from provider response

        Args:
            raw_tool_calls: Tool calls from provider

        Returns:
            List of standardized tool calls
        """
        parsed = []

        for call in raw_tool_calls:
            if self.provider == "openai":
                parsed.append(self.call_formatter.format_openai_tool_call(call))
            elif self.provider == "anthropic":
                parsed.append(self.call_formatter.format_anthropic_tool_call(call))
            elif self.provider == "ollama":
                parsed.append(self.call_formatter.format_ollama_tool_call(call))
            else:
                # Default: assume already in standard format
                parsed.append(call)

        return parsed

    def format_tool_call_request(
        self,
        tool_name: str,
        arguments: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Format tool call for execution

        Args:
            tool_name: Name of the tool
            arguments: Tool arguments

        Returns:
            Formatted tool call
        """
        return {
            "id": f"call_{tool_name}",
            "name": tool_name,
            "arguments": arguments
        }


# Pre-configured adapters for common providers
OPENAI_ADAPTER = FunctionCallAdapter(provider="openai")
ANTHROPIC_ADAPTER = FunctionCallAdapter(provider="anthropic")
OLLAMA_ADAPTER = FunctionCallAdapter(provider="ollama")


def get_function_call_adapter(provider: str) -> FunctionCallAdapter:
    """
    Get function call adapter for provider

    Args:
        provider: Provider name (openai, anthropic, ollama)

    Returns:
        FunctionCallAdapter instance
    """
    adapters = {
        "openai": OPENAI_ADAPTER,
        "anthropic": ANTHROPIC_ADAPTER,
        "ollama": OLLAMA_ADAPTER,
    }

    return adapters.get(provider.lower(), OPENAI_ADAPTER)
