"""
Unit tests for file tools package
"""
import pytest
from lightagent.tools.file_tools import (
    create_read_file_tool,
    create_write_file_tool,
    create_list_directory_tool,
    create_search_files_tool,
    create_get_file_info_tool,
    create_directory_tool,
    create_file_tools,
    FileToolConfig,
    SafePathConfig
)


class TestFileToolsImports:
    """Test that all imports work correctly"""

    def test_factory_functions_import(self):
        """Test that all factory functions are available"""
        assert callable(create_read_file_tool)
        assert callable(create_write_file_tool)
        assert callable(create_list_directory_tool)
        assert callable(create_search_files_tool)
        assert callable(create_get_file_info_tool)
        assert callable(create_directory_tool)
        assert callable(create_file_tools)

    def test_config_classes_import(self):
        """Test that config classes are available"""
        assert FileToolConfig is not None
        assert SafePathConfig is not None


class TestFileToolsCreation:
    """Test tool creation and properties"""

    @pytest.fixture
    def config(self):
        """Create a default file tool config"""
        return FileToolConfig()

    def test_create_read_file_tool(self, config):
        """Test read file tool creation"""
        tool = create_read_file_tool(config)
        assert tool.name == 'read_file'
        assert tool.description is not None
        assert tool.parameters is not None
        assert 'path' in tool.parameters['properties']
        assert 'encoding' in tool.parameters['properties']

    def test_create_write_file_tool(self, config):
        """Test write file tool creation"""
        tool = create_write_file_tool(config)
        assert tool.name == 'write_file'
        assert tool.description is not None
        assert tool.parameters is not None
        assert 'path' in tool.parameters['properties']
        assert 'content' in tool.parameters['properties']

    def test_create_list_directory_tool(self, config):
        """Test list directory tool creation"""
        tool = create_list_directory_tool(config)
        assert tool.name == 'list_directory'
        assert tool.description is not None
        assert tool.parameters is not None
        assert 'path' in tool.parameters['properties']
        assert 'recursive' in tool.parameters['properties']
        assert 'include_hidden' in tool.parameters['properties']

    def test_create_search_files_tool(self, config):
        """Test search files tool creation"""
        tool = create_search_files_tool(config)
        assert tool.name == 'search_files'
        assert tool.description is not None
        assert tool.parameters is not None
        assert 'path' in tool.parameters['properties']
        assert 'pattern' in tool.parameters['properties']
        assert 'content_pattern' in tool.parameters['properties']

    def test_create_get_file_info_tool(self, config):
        """Test get file info tool creation"""
        tool = create_get_file_info_tool(config)
        assert tool.name == 'get_file_info'
        assert tool.description is not None
        assert tool.parameters is not None
        assert 'path' in tool.parameters['properties']

    def test_create_directory_tool(self, config):
        """Test create directory tool creation"""
        tool = create_directory_tool(config)
        assert tool.name == 'create_directory'
        assert tool.description is not None
        assert tool.parameters is not None
        assert 'path' in tool.parameters['properties']
        assert 'parents' in tool.parameters['properties']


class TestFileToolsCombinations:
    """Test different tool combinations for different agent types"""

    @pytest.fixture
    def config(self):
        """Create a default file tool config"""
        return FileToolConfig()

    def test_readonly_agent_tools(self, config):
        """Test read-only agent tool combination"""
        tools = [
            create_read_file_tool(config),
            create_list_directory_tool(config)
        ]
        assert len(tools) == 2
        tool_names = [tool.name for tool in tools]
        assert 'read_file' in tool_names
        assert 'list_directory' in tool_names
        assert 'write_file' not in tool_names

    def test_readwrite_agent_tools(self, config):
        """Test read-write agent tool combination"""
        tools = [
            create_read_file_tool(config),
            create_write_file_tool(config),
            create_directory_tool(config)
        ]
        assert len(tools) == 3
        tool_names = [tool.name for tool in tools]
        assert 'read_file' in tool_names
        assert 'write_file' in tool_names
        assert 'create_directory' in tool_names

    def test_search_agent_tools(self, config):
        """Test search agent tool combination"""
        tools = [
            create_read_file_tool(config),
            create_search_files_tool(config)
        ]
        assert len(tools) == 2
        tool_names = [tool.name for tool in tools]
        assert 'read_file' in tool_names
        assert 'search_files' in tool_names

    def test_full_access_agent_tools(self, config):
        """Test full access agent tool combination"""
        tools = create_file_tools(config)
        assert len(tools) == 6
        tool_names = [tool.name for tool in tools]
        assert 'read_file' in tool_names
        assert 'write_file' in tool_names
        assert 'list_directory' in tool_names
        assert 'search_files' in tool_names
        assert 'get_file_info' in tool_names
        assert 'create_directory' in tool_names


class TestFileToolsConfig:
    """Test file tools configuration"""

    def test_default_config(self):
        """Test default configuration"""
        config = FileToolConfig()
        assert config.safe_mode is True
        assert config.path_config is None

    def test_config_with_path_restrictions(self):
        """Test configuration with path restrictions"""
        config = FileToolConfig(
            safe_mode=True,
            path_config=SafePathConfig(
                allowed_roots=['./logs', './docs'],
                max_file_size=5 * 1024 * 1024
            )
        )
        assert config.safe_mode is True
        assert config.path_config is not None
        assert len(config.path_config.allowed_roots) == 2
        assert './logs' in config.path_config.allowed_roots
        assert './docs' in config.path_config.allowed_roots
        assert config.path_config.max_file_size == 5 * 1024 * 1024

    def test_config_with_deny_patterns(self):
        """Test configuration with deny patterns"""
        config = FileToolConfig(
            path_config=SafePathConfig(
                deny_patterns=['*.tmp', '*.bak']
            )
        )
        assert config.path_config is not None
        assert len(config.path_config.deny_patterns) == 2
        assert '*.tmp' in config.path_config.deny_patterns

    def test_unsafe_mode_config(self):
        """Test unsafe mode configuration"""
        config = FileToolConfig(safe_mode=False)
        assert config.safe_mode is False

    def test_tools_with_restrictions(self):
        """Test that tools can be created with restrictions"""
        config = FileToolConfig(
            safe_mode=True,
            path_config=SafePathConfig(
                allowed_roots=['./safe_dir'],
                max_file_size=1 * 1024 * 1024
            )
        )
        tools = [
            create_read_file_tool(config),
            create_list_directory_tool(config)
        ]
        assert len(tools) == 2


class TestSafePathConfig:
    """Test SafePathConfig validation"""

    def test_safe_path_config_defaults(self):
        """Test SafePathConfig default values"""
        config = SafePathConfig()
        assert len(config.allowed_roots) == 0
        assert len(config.deny_patterns) == 0
        assert config.max_file_size == 10 * 1024 * 1024

    def test_safe_path_config_custom_values(self):
        """Test SafePathConfig with custom values"""
        config = SafePathConfig(
            allowed_roots=['./dir1', './dir2'],
            deny_patterns=['*.log'],
            max_file_size=20 * 1024 * 1024
        )
        assert len(config.allowed_roots) == 2
        assert len(config.deny_patterns) == 1
        assert config.max_file_size == 20 * 1024 * 1024
