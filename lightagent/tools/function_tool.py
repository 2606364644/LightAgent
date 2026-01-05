"""
Function Call Tool Implementation
"""
from typing import Any, Dict, List, Optional, Callable
from pydantic import BaseModel, Field
import asyncio
import inspect
import json

from .base import BaseTool, ToolExecutionResult, ToolSchema, FunctionTool


class FunctionCallConfig(BaseModel):
    """Configuration for function call tool"""
    prompt_template: Optional[str] = None
    require_arguments: bool = True
    validate_output: bool = True
    max_retries: int = 3


class FunctionCallTool(BaseTool):
    """
    Function Call tool with configurable prompt template
    Allows wrapping any Python function as a tool with custom prompts
    """

    def __init__(
        self,
        func: Callable,
        name: Optional[str] = None,
        description: Optional[str] = None,
        config: Optional[FunctionCallConfig] = None
    ):
        super().__init__()
        self.func = func
        self.name = name or func.__name__
        self.description = description or func.__doc__ or f"Execute function: {self.name}"
        self.config = config or FunctionCallConfig()

        # Extract function signature
        self._parse_signature()

    def _parse_signature(self):
        """Parse function signature for parameters"""
        sig = inspect.signature(self.func)
        self.parameters = {}

        properties = {}
        required = []

        for param_name, param in sig.parameters.items():
            param_type = param.annotation if param.annotation != inspect.Parameter.empty else Any

            param_info = {
                "type": self._get_type_name(param_type),
                "description": f"Parameter: {param_name}"
            }

            if param.default == inspect.Parameter.empty:
                required.append(param_name)
            else:
                param_info["default"] = param.default

            properties[param_name] = param_info

        self.parameters = {
            "type": "object",
            "properties": properties,
            "required": required
        }

    def _get_type_name(self, type_hint) -> str:
        """Get JSON schema type name from Python type hint"""
        type_mapping = {
            str: "string",
            int: "integer",
            float: "number",
            bool: "boolean",
            list: "array",
            dict: "object"
        }

        if type_hint in type_mapping:
            return type_mapping[type_hint]

        return "string"

    async def execute(self, **kwargs) -> ToolExecutionResult:
        """Execute the function call"""
        retry_count = 0

        while retry_count <= self.config.max_retries:
            try:
                # Validate arguments if required
                if self.config.require_arguments:
                    self._validate_arguments(kwargs)

                # Execute function
                if asyncio.iscoroutinefunction(self.func):
                    result = await self.func(**kwargs)
                else:
                    result = self.func(**kwargs)

                # Validate output if required
                if self.config.validate_output:
                    self._validate_output(result)

                return ToolExecutionResult(
                    success=True,
                    result=result
                )

            except Exception as e:
                retry_count += 1
                if retry_count > self.config.max_retries:
                    return ToolExecutionResult(
                        success=False,
                        error=f"Function call failed after {self.config.max_retries} retries: {str(e)}"
                    )

                await asyncio.sleep(0.1 * retry_count)

    def _validate_arguments(self, kwargs: Dict[str, Any]):
        """Validate function arguments"""
        sig = inspect.signature(self.func)

        for param_name, param in sig.parameters.items():
            if param_name not in kwargs and param.default == inspect.Parameter.empty:
                raise ValueError(f"Missing required parameter: {param_name}")

    def _validate_output(self, result: Any):
        """Validate function output"""
        if result is None:
            raise ValueError("Function returned None")

    def get_schema(self) -> ToolSchema:
        """Get tool schema with custom prompt template"""
        description = self.description

        if self.config.prompt_template:
            description = f"{description}\n\nUsage: {self.config.prompt_template}"

        return ToolSchema(
            name=self.name,
            description=description,
            parameters=self.parameters
        )

    @classmethod
    def from_function(
        cls,
        func: Callable,
        name: Optional[str] = None,
        description: Optional[str] = None,
        prompt_template: Optional[str] = None
    ) -> 'FunctionCallTool':
        """Create a FunctionCallTool from a function"""
        config = FunctionCallConfig(prompt_template=prompt_template)
        return cls(func, name, description, config)


class FunctionBuilder:
    """Helper class to build function tools"""

    @staticmethod
    def create_tool(
        func: Callable,
        name: Optional[str] = None,
        description: Optional[str] = None,
        prompt_template: Optional[str] = None
    ) -> FunctionCallTool:
        """Create a function call tool"""
        return FunctionCallTool.from_function(
            func,
            name,
            description,
            prompt_template
        )

    @staticmethod
    def create_tools_from_dict(
        functions: Dict[str, Callable],
        descriptions: Optional[Dict[str, str]] = None
    ) -> Dict[str, FunctionCallTool]:
        """Create multiple tools from a dictionary of functions"""
        tools = {}
        descriptions = descriptions or {}

        for name, func in functions.items():
            tools[name] = FunctionCallTool(
                func,
                name=name,
                description=descriptions.get(name)
            )

        return tools


# Example helper decorators and utilities
def tool(
    name: Optional[str] = None,
    description: Optional[str] = None,
    prompt_template: Optional[str] = None
):
    """Decorator to convert a function into a FunctionCallTool"""

    def decorator(func: Callable) -> FunctionCallTool:
        return FunctionCallTool.from_function(
            func,
            name,
            description,
            prompt_template
        )

    return decorator


# Example usage functions
async def example_calculator(expression: str) -> float:
    """
    Calculate a mathematical expression safely

    Args:
        expression: Mathematical expression to evaluate

    Returns:
        Calculation result
    """
    import ast
    import operator as op

    operators = {
        ast.Add: op.add,
        ast.Sub: op.sub,
        ast.Mult: op.mul,
        ast.Div: op.truediv,
        ast.Pow: op.pow,
        ast.USub: op.neg,
    }

    def eval_expr(node):
        if isinstance(node, ast.Num):
            return node.n
        elif isinstance(node, ast.BinOp):
            return operators[type(node.op)](
                eval_expr(node.left),
                eval_expr(node.right)
            )
        elif isinstance(node, ast.UnaryOp):
            return operators[type(node.op)](eval_expr(node.operand))
        else:
            raise TypeError(f"Unsupported type: {type(node)}")

    try:
        return eval_expr(ast.parse(expression, mode='eval').body)
    except Exception as e:
        raise ValueError(f"Invalid expression: {str(e)}")


async def example_get_weather(location: str, unit: str = "celsius") -> Dict[str, Any]:
    """
    Get weather information for a location (example/mock function)

    Args:
        location: City name or location
        unit: Temperature unit (celsius or fahrenheit)

    Returns:
        Weather information
    """
    # Mock weather data
    return {
        "location": location,
        "temperature": 22 if unit == "celsius" else 72,
        "unit": unit,
        "condition": "Sunny",
        "humidity": 65
    }


async def example_search_web(query: str, num_results: int = 5) -> List[Dict[str, str]]:
    """
    Search the web for information (example/mock function)

    Args:
        query: Search query
        num_results: Number of results to return

    Returns:
        List of search results
    """
    # Mock search results
    return [
        {
            "title": f"Result {i+1} for '{query}'",
            "url": f"https://example.com/{i+1}",
            "snippet": f"This is a mock search result {i+1} for the query."
        }
        for i in range(num_results)
    ]
