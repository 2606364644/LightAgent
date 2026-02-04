"""
Enhanced Prompts System

Provides advanced prompt template management with support for:
- Variable substitution
- Template composition
- Multipart prompts
- Template management and organization
"""

from .template import (
    PromptTemplate,
    JinjaStyleTemplate,
    MultiPartPrompt,
    Jinja2PromptTemplate
)

from .manager import (
    PromptManager,
    get_global_manager
)

from .presets import (
    load_default_prompts,
    get_default_prompts
)

__all__ = [
    # Templates
    'PromptTemplate',
    'JinjaStyleTemplate',
    'MultiPartPrompt',
    'Jinja2PromptTemplate',

    # Manager
    'PromptManager',
    'get_global_manager',

    # Presets
    'load_default_prompts',
    'get_default_prompts',
]
