"""
File reading tool
"""
import os
import aiofiles
from typing import Any, Dict, Optional
from ..base import BaseTool, FunctionTool
from .config import FileToolConfig, validate_path_safe


async def read_file(
    path: str,
    encoding: str = 'utf-8',
    config: Optional[FileToolConfig] = None
) -> Dict[str, Any]:
    """
    Read file contents

    Args:
        path: File path
        encoding: File encoding (default: utf-8)
        config: FileToolConfig instance

    Returns:
        Dictionary with file content or error
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

        # Check file size
        file_size = os.path.getsize(path)
        if config and config.path_config and file_size > config.path_config.max_file_size:
            return {
                'success': False,
                'error': f'File too large: {file_size} bytes (max: {config.path_config.max_file_size})',
                'path': path
            }

        # Read file
        async with aiofiles.open(path, 'r', encoding=encoding) as f:
            content = await f.read()

        return {
            'success': True,
            'content': content,
            'path': path,
            'size': file_size,
            'encoding': encoding
        }

    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'path': path
        }


def create_read_file_tool(config: Optional[FileToolConfig] = None) -> BaseTool:
    """Create a read file tool"""
    if config is None:
        config = FileToolConfig()

    return FunctionTool(
        name='read_file',
        description='Read the contents of a file. Returns file content as text.',
        func=lambda path, encoding='utf-8': read_file(path, encoding, config),
        parameters={
            'type': 'object',
            'properties': {
                'path': {
                    'type': 'string',
                    'description': 'Path to the file to read'
                },
                'encoding': {
                    'type': 'string',
                    'description': 'File encoding (default: utf-8)',
                    'default': 'utf-8'
                }
            },
            'required': ['path']
        }
    )
