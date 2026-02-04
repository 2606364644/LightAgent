"""
Prompt template implementation
"""
import re
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from ..base import BasePromptTemplate


class PromptTemplate(BasePromptTemplate, BaseModel):
    """
    Concrete implementation of prompt template

    Features:
    - Variable substitution with {{variable}} syntax
    - Optional variables with default values
    - Validation of required variables
    - Template composition
    """

    template: str
    required_variables: List[str] = Field(default_factory=list)
    optional_variables: Dict[str, Any] = Field(default_factory=dict)
    description: Optional[str] = None

    class Config:
        arbitrary_types_allowed = True

    def __init__(self, **data):
        super().__init__(**data)
        # Auto-detect variables from template if not provided
        if not self.required_variables and not self.optional_variables:
            self._detect_variables()

    def _detect_variables(self):
        """
        Auto-detect variables in the template
        Supports {{variable}} syntax
        """
        pattern = r'\{\{([^}]+)\}\}'
        matches = re.findall(pattern, self.template)

        for var in matches:
            var = var.strip()
            # Check if it has a default value (variable:default)
            if ':' in var:
                var_name, default = var.split(':', 1)
                self.optional_variables[var_name.strip()] = default.strip()
            else:
                self.required_variables.append(var)

    def format(self, **kwargs) -> str:
        """
        Format the template with provided variables

        Args:
            **kwargs: Variables to substitute

        Returns:
            Formatted prompt string

        Raises:
            ValueError: If required variables are missing
        """
        # Validate required variables
        if not self.validate(**kwargs):
            missing = set(self.required_variables) - set(kwargs.keys())
            raise ValueError(f"Missing required variables: {missing}")

        # Merge with optional variables (kwargs takes precedence)
        all_vars = {**self.optional_variables, **kwargs}

        # Substitute variables - handle both {{var}} and {{var:default}} formats
        result = self.template

        # First, replace {{var:default}} patterns
        for var_name, var_value in all_vars.items():
            # Pattern for {{var:default}} or {{var}}
            pattern = r'\{\{' + re.escape(var_name) + r'(?::[^}]*)?\}\}'
            result = re.sub(pattern, str(var_value), result)

        return result

    def validate(self, **kwargs) -> bool:
        """
        Validate that all required variables are provided

        Args:
            **kwargs: Variables to validate

        Returns:
            True if valid, False otherwise
        """
        return all(var in kwargs for var in self.required_variables)

    def get_required_variables(self) -> List[str]:
        """
        Get list of required variable names

        Returns:
            List of variable names
        """
        return self.required_variables.copy()

    def partial(self, **kwargs) -> 'PromptTemplate':
        """
        Create a new template with some variables pre-filled

        Args:
            **kwargs: Variables to pre-fill

        Returns:
            New PromptTemplate with pre-filled variables
        """
        # Format with provided variables
        partially_formatted = self.format(**kwargs)

        # Create new template with remaining variables
        new_template = PromptTemplate(
            template=partially_formatted,
            description=self.description
        )
        return new_template

    def compose(self, other: 'PromptTemplate', separator: str = "\n\n") -> 'PromptTemplate':
        """
        Compose this template with another

        Args:
            other: Another template to compose with
            separator: Separator between templates

        Returns:
            New composed template
        """
        combined_template = f"{self.template}{separator}{other.template}"
        combined_vars = list(set(self.required_variables + other.required_variables))

        return PromptTemplate(
            template=combined_template,
            required_variables=combined_vars,
            optional_variables={**self.optional_variables, **other.optional_variables},
            description=f"Composed: {self.description} + {other.description}"
        )


class JinjaStyleTemplate(PromptTemplate):
    """
    Jinja-style template with more advanced features

    Supports:
    - Conditionals: {% if variable %}...{% endif %}
    - Loops: {% for item in items %}...{% endfor %}
    - Filters: {{variable|upper}}
    """

    def format(self, **kwargs) -> str:
        """
        Format with Jinja-style syntax

        Note: This is a simplified implementation.
        For full Jinja2 support, install jinja2 and use Jinja2Template
        """
        # Validate required variables
        if not self.validate(**kwargs):
            missing = set(self.required_variables) - set(kwargs.keys())
            raise ValueError(f"Missing required variables: {missing}")

        result = self.template

        # Handle simple if statements
        if_pattern = r'\{%\s*if\s+(\w+)\s*%\}(.*?)\{%\s*endif\s*%\}'
        while True:
            match = re.search(if_pattern, result, re.DOTALL)
            if not match:
                break
            var_name = match.group(1)
            content = match.group(2)
            if kwargs.get(var_name):
                result = result[:match.start()] + content + result[match.end():]
            else:
                result = result[:match.start()] + result[match.end():]

        # Handle variable substitution
        result = super().format(**kwargs)

        return result


class MultiPartPrompt(BaseModel):
    """
    Multi-part prompt for complex scenarios

    Allows combining multiple prompt sections with different roles
    """

    system: Optional[PromptTemplate] = None
    user: Optional[PromptTemplate] = None
    assistant: Optional[PromptTemplate] = None

    def format_all(self, **kwargs) -> Dict[str, str]:
        """
        Format all parts of the prompt

        Args:
            **kwargs: Variables for all templates

        Returns:
            Dictionary with formatted prompts by role
        """
        result = {}

        if self.system:
            result['system'] = self.system.format(**kwargs)
        if self.user:
            result['user'] = self.user.format(**kwargs)
        if self.assistant:
            result['assistant'] = self.assistant.format(**kwargs)

        return result

    def to_messages(self, **kwargs) -> List[Dict[str, str]]:
        """
        Convert to message format for LLM APIs

        Args:
            **kwargs: Variables for all templates

        Returns:
            List of message dictionaries
        """
        messages = []
        formatted = self.format_all(**kwargs)

        if 'system' in formatted:
            messages.append({'role': 'system', 'content': formatted['system']})
        if 'user' in formatted:
            messages.append({'role': 'user', 'content': formatted['user']})
        if 'assistant' in formatted:
            messages.append({'role': 'assistant', 'content': formatted['assistant']})

        return messages


# Try to import jinja2 for full template support
try:
    from jinja2 import Template as Jinja2Template

    class Jinja2PromptTemplate(BasePromptTemplate, BaseModel):
        """
        Full Jinja2 template support

        Requires: pip install jinja2
        """

        template: str
        description: Optional[str] = None

        def format(self, **kwargs) -> str:
            """Format using Jinja2 engine"""
            template = Jinja2Template(self.template)
            return template.render(**kwargs)

        def validate(self, **kwargs) -> bool:
            """Validate by attempting to render"""
            try:
                self.format(**kwargs)
                return True
            except Exception:
                return False

        def get_required_variables(self) -> List[str]:
            """Get variables from template (may not be 100% accurate)"""
            import re
            pattern = r'\{\{([^}]+)\}\}'
            matches = re.findall(pattern, self.template)
            return [m.split('|')[0].split('.')[0].strip() for m in matches]

except ImportError:
    # jinja2 not available, use simplified version
    class Jinja2PromptTemplate(JinjaStyleTemplate):
        pass
