"""
File system tools package for agents

This package provides comprehensive file system operations with granular permission control.
Each tool can be used independently to follow the principle of least privilege.

Example usage:
    # Read-only agent
    from lightagent.tools.file_tools import (
        create_read_file_tool,
        FileToolConfig
    )

    config = FileToolConfig()
    tools = [create_read_file_tool(config)]

    # Or get all tools
    from lightagent.tools.file_tools import create_file_tools

    tools = create_file_tools(config)
"""

# Import configuration
from .config import SafePathConfig, FileToolConfig, validate_path_safe

# Import individual tool creation functions
from .read_file import create_read_file_tool
from .write_file import create_write_file_tool
from .list_directory import create_list_directory_tool
from .search_files import create_search_files_tool
from .get_file_info import create_get_file_info_tool
from .create_directory import create_directory_tool

# Import tool functions (for advanced usage)
from .read_file import read_file
from .write_file import write_file
from .list_directory import list_directory
from .search_files import search_files
from .get_file_info import get_file_info
from .create_directory import create_directory

# Import base classes
from ..base import BaseTool

__all__ = [
    # Configuration
    'SafePathConfig',
    'FileToolConfig',
    'validate_path_safe',

    # Tool factory functions
    'create_read_file_tool',
    'create_write_file_tool',
    'create_list_directory_tool',
    'create_search_files_tool',
    'create_get_file_info_tool',
    'create_directory_tool',

    # Tool functions (for advanced usage)
    'read_file',
    'write_file',
    'list_directory',
    'search_files',
    'get_file_info',
    'create_directory',

    # Base classes
    'BaseTool',

    # Convenience function
    'create_file_tools',
]

from typing import List, Optional


def create_file_tools(config: Optional[FileToolConfig] = None) -> List[BaseTool]:
    """
    Create a list of all file system tools

    Args:
        config: Optional FileToolConfig for safety settings

    Returns:
        List of BaseTool instances with all file operations
    """
    return [
        create_read_file_tool(config),
        create_write_file_tool(config),
        create_list_directory_tool(config),
        create_search_files_tool(config),
        create_get_file_info_tool(config),
        create_directory_tool(config)
    ]
