"""
File tools usage examples for different agent types

Demonstrates how to assign different file operation permissions to different agents
following the principle of least privilege.
"""
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


def example_readonly_agent():
    """
    Agent that can only read files
    Use case: Log analyzer, code reviewer, documentation reader
    """
    config = FileToolConfig(
        safe_mode=True,
        path_config=SafePathConfig(
            allowed_roots=['./logs', './docs'],
            max_file_size=5 * 1024 * 1024  # 5MB
        )
    )

    tools = [
        create_read_file_tool(config),
        create_list_directory_tool(config),
        create_get_file_info_tool(config)
    ]

    agent = Agent(tools=tools)
    return agent


def example_writer_agent():
    """
    Agent that can read and write files
    Use case: Report generator, code modifier, file updater
    """
    config = FileToolConfig(
        safe_mode=True,
        path_config=SafePathConfig(
            allowed_roots=['./output', './reports'],
            max_file_size=10 * 1024 * 1024  # 10MB
        )
    )

    tools = [
        create_read_file_tool(config),
        create_write_file_tool(config),
        create_list_directory_tool(config),
        create_get_file_info_tool(config),
        create_directory_tool(config)
    ]

    agent = Agent(tools=tools)
    return agent


def example_search_agent():
    """
    Agent that can search and read files
    Use case: Code search assistant, information finder
    """
    config = FileToolConfig(
        safe_mode=True,
        path_config=SafePathConfig(
            allowed_roots=['./src', './project'],
            max_file_size=2 * 1024 * 1024  # 2MB
        )
    )

    tools = [
        create_read_file_tool(config),
        create_search_files_tool(config),
        create_list_directory_tool(config),
        create_get_file_info_tool(config)
    ]

    agent = Agent(tools=tools)
    return agent


def example_full_access_agent():
    """
    Agent with full file access
    Use case: Development assistant, system administrator
    WARNING: Only use with trusted agents
    """
    config = FileToolConfig(
        safe_mode=False  # Disable path restrictions
    )

    tools = create_file_tools(config)  # Get all tools

    agent = Agent(tools=tools)
    return agent


def example_minimal_agent():
    """
    Minimal agent - can only read specific directory
    Use case: Single-purpose reader with restricted access
    """
    config = FileToolConfig(
        safe_mode=True,
        path_config=SafePathConfig(
            allowed_roots=['./public'],
            max_file_size=1 * 1024 * 1024  # 1MB
        )
    )

    tools = [
        create_read_file_tool(config)
    ]

    agent = Agent(tools=tools)
    return agent


# Example usage scenarios
if __name__ == '__main__':
    # Scenario 1: Create a readonly log analyzer
    log_analyzer = example_readonly_agent()
    print("Log analyzer created with read-only access")

    # Scenario 2: Create a report generator with write access
    report_generator = example_writer_agent()
    print("Report generator created with read/write access")

    # Scenario 3: Create a code search assistant
    code_searcher = example_search_agent()
    print("Code search assistant created with search capabilities")

    # Scenario 4: Create a development assistant with full access
    # WARNING: Only use in trusted environments
    dev_assistant = example_full_access_agent()
    print("Development assistant created with full file access")


# Placeholder Agent class for demonstration
class Agent:
    """Simple Agent class for demonstration"""
    def __init__(self, tools):
        self.tools = tools
        print(f"Agent initialized with {len(tools)} tools:")
        for tool in tools:
            print(f"  - {tool.name}")
