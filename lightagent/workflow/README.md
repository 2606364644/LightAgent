# LightAgent Workflow Module

A comprehensive workflow system inspired by DeepAgents, providing advanced capabilities for complex AI agent tasks.

## Features

### 1. Enhanced Prompts System
- **Template Management**: Create, organize, and reuse prompt templates
- **Variable Substitution**: Dynamic prompt generation with `{{variable}}` syntax
- **Multipart Prompts**: Support for system/user/assistant message formats
- **Template Composition**: Combine multiple templates
- **Built-in Templates**: Pre-configured templates for common scenarios

### 2. Planning Tools
- **Task Decomposition**: Break complex goals into manageable steps
- **LLM-based Planning**: Use LLMs to create intelligent plans
- **Dependency Management**: Handle task dependencies automatically
- **Multiple Execution Modes**: Sequential, parallel, and adaptive execution
- **Progress Tracking**: Monitor task execution in real-time

### 3. File System Access
- **Safe File Operations**: Read, write, and list files with safety checks
- **Path Validation**: Restrict file access to specific directories
- **File Searching**: Search by name and content
- **Size Limits**: Prevent reading oversized files
- **Error Handling**: Comprehensive error handling for file operations

### 4. Workflow Engine
- **Complete Orchestration**: Coordinates planning, prompts, and tools
- **Agent Integration**: Seamless integration with LightAgent agents
- **Retry and Refinement**: Handle failures intelligently
- **Execution History**: Track workflow executions

## Installation

The workflow module is included with LightAgent. No additional installation required.

For full template support with Jinja2:
```bash
pip install jinja2
```

## Quick Start

### Basic Usage

```python
import asyncio
from lightagent.workflow import create_workflow_engine
from lightagent.core.agent import Agent
from lightagent.models.providers import OpenAIAdapter

async def main():
    # Create agent
    model_adapter = OpenAIAdapter(api_key="your-key", model="gpt-3.5-turbo")
    agent = Agent.create(
        name="assistant",
        model_adapter=model_adapter,
        system_prompt="You are a helpful assistant"
    )

    # Create workflow engine
    engine = await create_workflow_engine(agent=agent, verbose=True)

    # Execute a workflow
    result = await engine.execute(
        goal="Create a Python web scraper",
        execution_mode='sequential'
    )

    print(f"Success: {result['success']}")
    print(f"Progress: {result['progress']:.1f}%")

asyncio.run(main())
```

### Using Prompt Templates

```python
from lightagent.workflow import PromptTemplate

# Create a template
template = PromptTemplate(
    template="You are a {{role}}. Task: {{task}}.",
    description="Role-based prompt"
)

# Format with variables
prompt = template.format(
    role="Python expert",
    task="explain decorators"
)

print(prompt)
# Output: "You are a Python expert. Task: explain decorators."
```

### Using File System Tools

```python
# File tools are now in the core tools module
from lightagent.tools import create_file_tools, FileToolConfig, SafePathConfig

# For backward compatibility, you can also import from workflow module
# from lightagent.workflow import create_file_tools, FileToolConfig, SafePathConfig

# Configure with safety
config = FileToolConfig(
    safe_mode=True,
    path_config=SafePathConfig(
        allowed_roots=['/safe/path'],
        max_file_size=10*1024*1024  # 10MB
    )
)

# Create tools
tools = create_file_tools(config)

# Add to agent
for tool in tools:
    agent.add_tool(tool)

# Now agent can read/write files safely
```

### Task Planning

```python
from lightagent.workflow import create_planner

# Create planner
planner = create_planner(planner_type='llm', agent=agent)

# Plan a goal
plan = await planner.plan(
    goal="Build a REST API",
    context={"language": "Python"}
)

# Plan contains tasks with dependencies
for task in plan:
    print(f"{task['step']}. {task['name']}")
    print(f"   Priority: {task['priority']}")
    print(f"   Dependencies: {task['dependencies']}")
```

### Task Graphs

```python
from lightagent.workflow import TaskGraph, Task

# Create task graph
graph = TaskGraph()

# Add tasks
task1 = Task(name="Design", description="Design system", priority="high")
task2 = Task(name="Implement", description="Write code", priority="high")
task3 = Task(name="Test", description="Add tests", priority="medium")

graph.add_task(task1)
graph.add_task(task2)
graph.add_task(task3)

# Add dependencies
graph.add_dependency(task2.task_id, task1.task_id)
graph.add_dependency(task3.task_id, task2.task_id)

# Get execution plan
levels = graph.get_execution_order()
for i, level in enumerate(levels):
    print(f"Level {i+1}: {[t.name for t in level]}")
```

## Architecture

```
lightagent/workflow/
├── base.py              # Base classes and interfaces
├── prompts/             # Prompt system
│   ├── template.py     # Template implementations
│   ├── manager.py      # Template manager
│   └── presets.py      # Built-in templates
├── planning/            # Planning system
│   ├── task.py         # Task models
│   ├── planner.py      # Planner implementations
│   └── executor.py     # Task executors
├── tools/               # File system tools
│   └── file_tools.py   # File operations
├── engine.py            # Workflow engine
└── integration.py       # Agent integration helpers
```

## Advanced Features

### Custom Prompt Templates

```python
from lightagent.workflow import PromptManager

manager = PromptManager()

# Create custom template
template = PromptTemplate(
    template="Analyze this {{file_type}} file: {{path}}",
    description="File analysis template"
)

# Register it
manager.register_template(
    name='analysis.file',
    template=template,
    category='analysis'
)

# Use it
prompt = manager.get_template('analysis.file').format(
    file_type='Python',
    path='main.py'
)
```

### Workflow Execution Modes

```python
# Sequential execution (one task at a time)
result = await engine.execute(goal, execution_mode='sequential')

# Parallel execution (independent tasks run in parallel)
result = await engine.execute(goal, execution_mode='parallel')

# Adaptive execution (priority-based scheduling)
result = await engine.execute(goal, execution_mode='adaptive')
```

### Integrating with Agents

```python
from lightagent.workflow import enhance_agent_with_workflow

# Enhance existing agent
agent = enhance_agent_with_workflow(
    agent=agent,
    enable_file_tools=True
)

# Use workflow methods
result = await agent.execute_workflow("Build a calculator")
```

## Built-in Templates

The workflow module includes pre-configured templates for:

- **Planning**: Task decomposition, refinement, status checking
- **File System**: File analysis, code review, search strategy
- **Agent**: Orchestration, task assignment
- **Research**: Research planning, synthesis
- **Coding**: Feature planning, debugging strategy

Access them:
```python
from lightagent.workflow import get_default_prompts

manager = get_default_prompts()
templates = manager.list_templates()
```

## Safety Features

### Path Validation
```python
from lightagent.workflow import SafePathConfig

config = SafePathConfig(
    allowed_roots=['/project/src', '/project/docs'],
    deny_patterns=['*.tmp', '*.bak']
)
```

### File Size Limits
```python
config = SafePathConfig(
    max_file_size=5*1024*1024  # 5MB limit
)
```

## Examples

See the `examples/workflow/` directory for complete examples:
- `basic_workflow.py` - Basic usage
- `advanced_workflow.py` - Planning, task graphs, file tools

## Comparison with DeepAgents

| Feature | LightAgent Workflow | DeepAgents |
|---------|-------------------|------------|
| Prompt Templates | ✓ Full support | ✓ |
| Task Planning | ✓ LLM + Rule-based | ✓ |
| File System | ✓ With safety checks | ✓ |
| Sub-Agents | ✓ Via A2A protocol | ✓ |
| Graph-based | ✓ TaskGraph | ✓ |
| Python | ✓ Native | ✓ |
| Async | ✓ First-class | ✓ |

## API Reference

See individual module documentation for detailed API reference:
- `lightagent.workflow.prompts` - Prompt system
- `lightagent.workflow.planning` - Planning system
- `lightagent.workflow.tools` - File tools
- `lightagent.workflow.engine` - Workflow engine

## Contributing

Contributions welcome! Please ensure:
- Code uses UTF-8 encoding
- Follow existing code style
- Add tests for new features
- Update documentation

## License

Same as LightAgent main package.

## Support

For issues and questions:
- GitHub: [LightAgent repository]
- Documentation: See main LightAgent docs
