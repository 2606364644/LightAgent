"""
Directory creation tool
"""
from typing import Any, Dict, Optional
from pathlib import Path
from ..base import BaseTool, FunctionTool
from .config import FileToolConfig, validate_path_safe


async def create_directory(
    path: str,
    parents: bool = True,
    config: Optional[FileToolConfig] = None
) -> Dict[str, Any]:
    """
    Create a directory

    Args:
        path: Directory path
        parents: Create parent directories if needed
        config: FileToolConfig instance

    Returns:
        Dictionary with success status
    """
    try:
        # Validate path if in safe mode
        if config and config.safe_mode and config.path_config:
            is_safe, error = validate_path_safe(path, config.path_config)
            if not is_safe:
                return {
                    'success': False,
                    'error': error,
                    'path': path
                }

        path_obj = Path(path)
        path_obj.mkdir(parents=parents, exist_ok=True)

        return {
            'success': True,
            'path': path,
            'created': True
        }

    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'path': path
        }


def create_directory_tool(config: Optional[FileToolConfig] = None) -> BaseTool:
    """Create a create directory tool"""
    if config is None:
        config = FileToolConfig()

    return FunctionTool(
        name='create_directory',
        description='Create a directory. Can create parent directories if needed.',
        func=lambda path, parents=True: create_directory(path, parents, config),
        parameters={
            'type': 'object',
            'properties': {
                'path': {
                    'type': 'string',
                    'description': 'Path of the directory to create'
                },
                'parents': {
                    'type': 'boolean',
                    'description': 'Create parent directories if they do not exist',
                    'default': True
                }
            },
            'required': ['path']
        }
    )
