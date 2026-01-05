# File Tools - Permission Management Guide

## Overview

The file tools have been refactored to support granular permission control, allowing you to assign specific file operation capabilities to different agents following the principle of least privilege.

## Available Tool Factory Functions

Each tool now has its own factory function for independent creation:

### 1. **create_read_file_tool()** - Read-only access
```python
from lightagent.tools.file_tools import create_read_file_tool

tool = create_read_file_tool(config)
```
**Capabilities:** Read file contents
**Use cases:** Log analyzers, documentation readers, code reviewers

### 2. **create_write_file_tool()** - Write access
```python
from lightagent.tools.file_tools import create_write_file_tool

tool = create_write_file_tool(config)
```
**Capabilities:** Write/create files
**Use cases:** Report generators, file updaters
**Warning:** Should typically be paired with read_file_tool

### 3. **create_list_directory_tool()** - Directory listing
```python
from lightagent.tools.file_tools import create_list_directory_tool

tool = create_list_directory_tool(config)
```
**Capabilities:** List directory contents (recursive or non-recursive)
**Use cases:** File browsers, directory navigators

### 4. **create_search_files_tool()** - File search
```python
from lightagent.tools.file_tools import create_search_files_tool

tool = create_search_files_tool(config)
```
**Capabilities:** Search files by name pattern and content
**Use cases:** Code search assistants, information finders

### 5. **create_get_file_info_tool()** - File metadata
```python
from lightagent.tools.file_tools import create_get_file_info_tool

tool = create_get_file_info_tool(config)
```
**Capabilities:** Get file/directory metadata (size, timestamps, etc.)
**Use cases:** File inspectors, system monitors

### 6. **create_directory_tool()** - Directory creation
```python
from lightagent.tools.file_tools import create_directory_tool

tool = create_directory_tool(config)
```
**Capabilities:** Create directories
**Use cases:** File organizers, project scaffolders

### 7. **create_file_tools()** - All tools
```python
from lightagent.tools.file_tools import create_file_tools

tools = create_file_tools(config)  # Returns all 6 tools
```
**Capabilities:** All file operations
**Use cases:** Full-featured development assistants
**Warning:** Only use with trusted agents

## Configuration

### Basic Configuration
```python
from lightagent.tools.file_tools import FileToolConfig

config = FileToolConfig(
    safe_mode=True  # Enable path restrictions (default: True)
)
```

### Advanced Configuration with Path Restrictions
```python
from lightagent.tools.file_tools import FileToolConfig, SafePathConfig

config = FileToolConfig(
    safe_mode=True,
    path_config=SafePathConfig(
        allowed_roots=['./logs', './output'],  # Only allow these paths
        deny_patterns=['*.tmp', '*.bak'],      # Block these patterns
        max_file_size=10 * 1024 * 1024         # 10MB limit
    )
)
```

## Common Agent Configurations

### Read-Only Agent (Safe)
```python
config = FileToolConfig(
    safe_mode=True,
    path_config=SafePathConfig(
        allowed_roots=['./public', './docs'],
        max_file_size=5 * 1024 * 1024
    )
)

tools = [
    create_read_file_tool(config),
    create_list_directory_tool(config),
    create_get_file_info_tool(config)
]

agent = Agent(tools=tools)
```

### Read-Write Agent (Moderate Risk)
```python
config = FileToolConfig(
    safe_mode=True,
    path_config=SafePathConfig(
        allowed_roots=['./workspace', './output'],
        max_file_size=10 * 1024 * 1024
    )
)

tools = [
    create_read_file_tool(config),
    create_write_file_tool(config),
    create_list_directory_tool(config),
    create_directory_tool(config)
]

agent = Agent(tools=tools)
```

### Full Access Agent (High Risk - Use with Caution)
```python
config = FileToolConfig(
    safe_mode=False  # No restrictions
)

tools = create_file_tools(config)

agent = Agent(tools=tools)
```

## Migration Guide

### Before (Old API)
```python
from lightagent.tools.file_tools import create_file_tools

# Get all tools
tools = create_file_tools(config)
agent = Agent(tools=tools)
```

### After (New API - Granular Control)
```python
from lightagent.tools.file_tools import create_read_file_tool

# Get only what you need
tools = [create_read_file_tool(config)]
agent = Agent(tools=tools)
```

### Backward Compatibility
The old `create_file_tools()` function still works and returns all 6 tools:
```python
from lightagent.tools.file_tools import create_file_tools

tools = create_file_tools(config)  # Still works!
```

## Best Practices

1. **Principle of Least Privilege**: Only give agents the minimum permissions they need
2. **Use safe_mode=True** for production environments
3. **Set allowed_roots** to restrict file access to specific directories
4. **Set max_file_size** to prevent memory issues
5. **Never use safe_mode=False** with untrusted agents
6. **Pair write_file_tool with read_file_tool** for most use cases

## Security Considerations

### Risk Levels
- **Low Risk**: read_file, list_directory, get_file_info, search_files
- **Medium Risk**: create_directory
- **High Risk**: write_file (can modify/delete data)

### Recommendations
- Start with read-only tools, add write permissions only if needed
- Always test in isolated environments first
- Use path restrictions to limit damage from potential issues
- Monitor agent actions in production
- Consider implementing audit logs for write operations

## Examples

See `examples/file_tools_usage.py` for complete working examples of different agent configurations.

## API Reference

All factory functions accept the same parameter:
- `config` (FileToolConfig, optional): Configuration for safety settings

All factory functions return:
- `BaseTool`: A tool instance that can be added to an agent's tool list
