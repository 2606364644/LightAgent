"""
Configuration and validation for file tools

Provides safety configuration and path validation for all file system operations.
"""
import os
from typing import Optional, Tuple
from pydantic import BaseModel, Field


class SafePathConfig(BaseModel):
    """Configuration for safe file system access"""
    allowed_roots: list[str] = Field(default_factory=list)
    deny_patterns: list[str] = Field(default_factory=list)
    max_file_size: int = 10 * 1024 * 1024  # 10MB default


class FileToolConfig(BaseModel):
    """Configuration for file tools"""
    safe_mode: bool = True
    path_config: Optional[SafePathConfig] = None


def validate_path_safe(path: str, config: SafePathConfig) -> Tuple[bool, Optional[str]]:
    """
    Validate that a path is safe to access

    Args:
        path: Path to validate
        config: SafePathConfig instance

    Returns:
        Tuple of (is_safe, error_message)
    """
    if not config.allowed_roots:
        return True, None

    try:
        abs_path = os.path.abspath(path)

        # Check if path is under allowed roots
        for root in config.allowed_roots:
            abs_root = os.path.abspath(root)
            if abs_path.startswith(abs_root + os.sep) or abs_path == abs_root:
                return True, None

        return False, f"Path '{path}' is not under allowed roots"

    except Exception as e:
        return False, f"Path validation error: {str(e)}"
