"""
Directory listing tool
"""
from typing import Any, Dict, Optional
from pathlib import Path
from ..base import BaseTool, FunctionTool
from .config import FileToolConfig, validate_path_safe


async def list_directory(
    path: str,
    recursive: bool = False,
    include_hidden: bool = False,
    config: Optional[FileToolConfig] = None
) -> Dict[str, Any]:
    """
    List directory contents

    Args:
        path: Directory path
        recursive: List recursively
        include_hidden: Include hidden files/directories
        config: FileToolConfig instance

    Returns:
        Dictionary with directory contents
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

        items = []
        path_obj = Path(path)

        if recursive:
            # Recursive listing
            for item in path_obj.rglob('*'):
                if not include_hidden and item.name.startswith('.'):
                    continue

                items.append({
                    'name': item.name,
                    'path': str(item),
                    'type': 'directory' if item.is_dir() else 'file',
                    'size': item.stat().st_size if item.is_file() else None
                })
        else:
            # Non-recursive listing
            for item in path_obj.iterdir():
                if not include_hidden and item.name.startswith('.'):
                    continue

                items.append({
                    'name': item.name,
                    'path': str(item),
                    'type': 'directory' if item.is_dir() else 'file',
                    'size': item.stat().st_size if item.is_file() else None
                })

        return {
            'success': True,
            'path': path,
            'items': items,
            'count': len(items)
        }

    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'path': path
        }


def create_list_directory_tool(config: Optional[FileToolConfig] = None) -> BaseTool:
    """Create a list directory tool"""
    if config is None:
        config = FileToolConfig()

    return FunctionTool(
        name='list_directory',
        description='List contents of a directory. Can list recursively.',
        func=lambda path, recursive=False, include_hidden=False: list_directory(path, recursive, include_hidden, config),
        parameters={
            'type': 'object',
            'properties': {
                'path': {
                    'type': 'string',
                    'description': 'Path to the directory'
                },
                'recursive': {
                    'type': 'boolean',
                    'description': 'List directories recursively',
                    'default': False
                },
                'include_hidden': {
                    'type': 'boolean',
                    'description': 'Include hidden files and directories',
                    'default': False
                }
            },
            'required': ['path']
        }
    )
