"""
File writing tool
"""
import os
import aiofiles
from typing import Any, Dict, Optional
from ..base import BaseTool, FunctionTool
from .config import FileToolConfig, validate_path_safe


async def write_file(
    path: str,
    content: str,
    encoding: str = 'utf-8',
    config: Optional[FileToolConfig] = None
) -> Dict[str, Any]:
    """
    Write content to file

    Args:
        path: File path
        content: Content to write
        encoding: File encoding (default: utf-8)
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

        # Create directory if it doesn't exist
        directory = os.path.dirname(path)
        if directory:
            os.makedirs(directory, exist_ok=True)

        # Write file
        async with aiofiles.open(path, 'w', encoding=encoding) as f:
            await f.write(content)

        return {
            'success': True,
            'path': path,
            'bytes_written': len(content.encode(encoding))
        }

    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'path': path
        }


def create_write_file_tool(config: Optional[FileToolConfig] = None) -> BaseTool:
    """Create a write file tool"""
    if config is None:
        config = FileToolConfig()

    return FunctionTool(
        name='write_file',
        description='Write content to a file. Creates the file and parent directories if they do not exist.',
        func=lambda path, content, encoding='utf-8': write_file(path, content, encoding, config),
        parameters={
            'type': 'object',
            'properties': {
                'path': {
                    'type': 'string',
                    'description': 'Path to the file to write'
                },
                'content': {
                    'type': 'string',
                    'description': 'Content to write to the file'
                },
                'encoding': {
                    'type': 'string',
                    'description': 'File encoding (default: utf-8)',
                    'default': 'utf-8'
                }
            },
            'required': ['path', 'content']
        }
    )
