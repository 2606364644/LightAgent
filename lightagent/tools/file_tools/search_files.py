"""
File search tool
"""
import aiofiles
from typing import Any, Dict, Optional
from pathlib import Path
from ..base import BaseTool, FunctionTool
from .config import FileToolConfig, validate_path_safe


async def search_files(
    path: str,
    pattern: str = '*',
    content_pattern: Optional[str] = None,
    config: Optional[FileToolConfig] = None
) -> Dict[str, Any]:
    """
    Search for files by name and/or content

    Args:
        path: Root directory to search
        pattern: File name pattern (e.g., '*.py', '*.txt')
        content_pattern: Optional content pattern to search for
        config: FileToolConfig instance

    Returns:
        Dictionary with search results
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

        matches = []
        path_obj = Path(path)

        for file_path in path_obj.rglob(pattern):
            if not file_path.is_file():
                continue

            match_info = {
                'path': str(file_path),
                'name': file_path.name
            }

            # Search content if pattern provided
            if content_pattern:
                try:
                    async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
                        content = await f.read()

                    if content_pattern.lower() in content.lower():
                        match_info['content_matches'] = content.lower().count(content_pattern.lower())
                        matches.append(match_info)

                except Exception:
                    # Skip files that can't be read as text
                    continue
            else:
                matches.append(match_info)

        return {
            'success': True,
            'path': path,
            'pattern': pattern,
            'content_pattern': content_pattern,
            'matches': matches,
            'count': len(matches)
        }

    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'path': path
        }


def create_search_files_tool(config: Optional[FileToolConfig] = None) -> BaseTool:
    """Create a search files tool"""
    if config is None:
        config = FileToolConfig()

    return FunctionTool(
        name='search_files',
        description='Search for files by name pattern and optionally by content pattern.',
        func=lambda path, pattern='*', content_pattern=None: search_files(path, pattern, content_pattern, config),
        parameters={
            'type': 'object',
            'properties': {
                'path': {
                    'type': 'string',
                    'description': 'Root directory to search in'
                },
                'pattern': {
                    'type': 'string',
                    'description': 'File name pattern (e.g., *.py, *.txt)',
                    'default': '*'
                },
                'content_pattern': {
                    'type': 'string',
                    'description': 'Optional text pattern to search for within file contents'
                }
            },
            'required': ['path']
        }
    )
