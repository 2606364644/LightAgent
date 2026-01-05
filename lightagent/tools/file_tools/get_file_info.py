"""
File information tool
"""
from typing import Any, Dict, Optional
from pathlib import Path
from ..base import BaseTool, FunctionTool
from .config import FileToolConfig, validate_path_safe


async def get_file_info(path: str, config: Optional[FileToolConfig] = None) -> Dict[str, Any]:
    """
    Get detailed file information

    Args:
        path: File path
        config: FileToolConfig instance

    Returns:
        Dictionary with file information
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
        stat = path_obj.stat()

        info = {
            'success': True,
            'path': path,
            'name': path_obj.name,
            'type': 'directory' if path_obj.is_dir() else 'file',
            'size': stat.st_size,
            'created': stat.st_ctime,
            'modified': stat.st_mtime,
            'accessed': stat.st_atime,
            'absolute_path': str(path_obj.absolute())
        }

        # Add extension for files
        if path_obj.is_file():
            info['extension'] = path_obj.suffix

        return info

    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'path': path
        }


def create_get_file_info_tool(config: Optional[FileToolConfig] = None) -> BaseTool:
    """Create a get file info tool"""
    if config is None:
        config = FileToolConfig()

    return FunctionTool(
        name='get_file_info',
        description='Get detailed information about a file or directory including size, timestamps, etc.',
        func=lambda path: get_file_info(path, config),
        parameters={
            'type': 'object',
            'properties': {
                'path': {
                    'type': 'string',
                    'description': 'Path to the file or directory'
                }
            },
            'required': ['path']
        }
    )
