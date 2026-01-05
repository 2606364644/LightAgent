"""
Integration utilities for using workflow with LightAgent agents

Provides helper functions and adapters for seamless integration
"""
from typing import Any, Dict, List, Optional
from pydantic import BaseModel

from .engine import WorkflowEngine, create_workflow_engine
from lightagent.tools import create_file_tools, FileToolConfig


class AgentWorkflowMixin(BaseModel):
    """
    Mixin to add workflow capabilities to agents

    Can be used to extend Agent class with workflow methods
    """

    # Workflow engine (will be initialized lazily)
    _workflow_engine: Optional[WorkflowEngine] = None
    enable_workflow: bool = True
    workflow_verbose: bool = True

    class Config:
        arbitrary_types_allowed = True

    async def get_workflow_engine(self) -> WorkflowEngine:
        """
        Get or create the workflow engine

        Returns:
            WorkflowEngine instance
        """
        if self._workflow_engine is None:
            self._workflow_engine = await create_workflow_engine(
                agent=self,
                verbose=self.workflow_verbose
            )
        return self._workflow_engine

    async def execute_workflow(
        self,
        goal: str,
        context: Optional[Dict[str, Any]] = None,
        execution_mode: str = 'sequential'
    ) -> Dict[str, Any]:
        """
        Execute a workflow with planning and task execution

        Args:
            goal: Goal to achieve
            context: Optional context
            execution_mode: Execution mode

        Returns:
            Workflow result
        """
        if not self.enable_workflow:
            # Fallback to normal execution
            return await self.run(goal)

        engine = await self.get_workflow_engine()
        return await engine.execute(goal, context, execution_mode)

    async def execute_with_file_tools(
        self,
        goal: str,
        file_tool_config: Optional[FileToolConfig] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Execute a goal with file system tools enabled

        Args:
            goal: Goal to achieve
            file_tool_config: Optional file tool config
            context: Optional context

        Returns:
            Execution result
        """
        engine = await self.get_workflow_engine()
        return await engine.execute_with_tools(goal, context=context)

    def add_workflow_tools(
        self,
        config: Optional[FileToolConfig] = None
    ):
        """
        Add file system tools to this agent

        Args:
            config: Optional file tool configuration
        """
        file_tools = create_file_tools(config)

        for tool in file_tools:
            self.add_tool(tool)

    def use_prompt_template(
        self,
        template_name: str,
        **kwargs
    ) -> str:
        """
        Use a prompt template from the workflow system

        Args:
            template_name: Name of the template
            **kwargs: Template variables

        Returns:
            Formatted prompt
        """
        # This would need access to workflow engine
        # For now, return simple formatted string
        return f"Template: {template_name}, Variables: {kwargs}"


async def enhance_agent_with_workflow(
    agent: Any,
    enable_file_tools: bool = True,
    file_tool_config: Optional[FileToolConfig] = None
) -> Any:
    """
    Enhance an agent with workflow capabilities

    Args:
        agent: Agent instance to enhance
        enable_file_tools: Whether to add file tools
        file_tool_config: Optional file tool config

    Returns:
        Enhanced agent (same instance)
    """
    # Add workflow tools if requested
    if enable_file_tools:
        file_tools = create_file_tools(file_tool_config)

        for tool in file_tools:
            agent.add_tool(tool)

    # Create workflow engine and attach to agent
    engine = await create_workflow_engine(
        agent=agent,
        enable_file_tools=False,  # Tools already added
        verbose=False
    )

    agent._workflow_engine = engine

    # Add workflow methods if not already present
    if not hasattr(agent, 'execute_workflow'):
        agent.execute_workflow = lambda goal, **kwargs: engine.execute(goal, **kwargs)

    if not hasattr(agent, 'refine_workflow'):
        agent.refine_workflow = lambda goal, prev_result, feedback, **kwargs: \
            engine.refine_and_retry(goal, prev_result, feedback, **kwargs)

    return agent


def create_workflow_agent(
    agent_factory,
    enable_file_tools: bool = True,
    file_tool_config: Optional[FileToolConfig] = None,
    **agent_kwargs
) -> Any:
    """
    Create a new agent with workflow capabilities

    Args:
        agent_factory: Function to create base agent
        enable_file_tools: Whether to enable file tools
        file_tool_config: Optional file tool config
        **agent_kwargs: Arguments for agent creation

    Returns:
        Agent with workflow capabilities
    """
    # Create base agent
    agent = agent_factory(**agent_kwargs)

    # Enhance with workflow
    return enhance_agent_with_workflow(
        agent,
        enable_file_tools=enable_file_tools,
        file_tool_config=file_tool_config
    )


# Convenience functions for common workflows

async def code_review_workflow(
    agent: Any,
    file_path: str,
    focus_areas: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Execute a code review workflow

    Args:
        agent: Agent to use
        file_path: Path to code file
        focus_areas: Optional list of focus areas

    Returns:
        Review results
    """
    engine = await create_workflow_engine(agent=agent, verbose=False)

    # Use code review prompt template
    prompt = engine.use_prompt_template(
        'coding.review',
        file_path=file_path,
        language=file_path.split('.')[-1],
        code=await _read_file_for_review(file_path),
        focus_areas=', '.join(focus_areas or ['quality', 'security', 'performance'])
    )

    result = await agent.run(prompt)

    return {
        'file': file_path,
        'review': result.get('response', ''),
        'success': result.get('success', True)
    }


async def file_analysis_workflow(
    agent: Any,
    path: str,
    analysis_type: str = 'general'
) -> Dict[str, Any]:
    """
    Execute a file analysis workflow

    Args:
        agent: Agent to use
        path: Path to analyze
        analysis_type: Type of analysis

    Returns:
        Analysis results
    """
    engine = await create_workflow_engine(agent=agent, verbose=False)

    # Get file info
    from .tools import get_file_info
    file_info = await get_file_info(path)

    # Use appropriate prompt template
    template_name = f'filesystem.{analysis_type}_analysis'

    try:
        prompt = engine.use_prompt_template(
            template_name,
            path=path,
            file_type=file_info.get('type', 'unknown'),
            content_summary=str(file_info)
        )
    except Exception:
        # Fallback if template not found
        prompt = f"Analyze this file: {path}\n\nFile info: {file_info}"

    result = await agent.run(prompt)

    return {
        'path': path,
        'analysis': result.get('response', ''),
        'file_info': file_info,
        'success': result.get('success', True)
    }


async def research_workflow(
    agent: Any,
    topic: str,
    objectives: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Execute a research workflow

    Args:
        agent: Agent to use
        topic: Research topic
        objectives: Optional research objectives

    Returns:
        Research results
    """
    engine = await create_workflow_engine(agent=agent, verbose=False)

    # Use research planning template
    prompt = engine.use_prompt_template(
        'research.research_plan',
        topic=topic,
        objectives='\n'.join(objectives or ['Understand the topic']),
        constraints='Time and resource constraints'
    )

    result = await agent.run(prompt)

    return {
        'topic': topic,
        'plan': result.get('response', ''),
        'success': result.get('success', True)
    }


async def _read_file_for_review(file_path: str) -> str:
    """Helper to read file for code review"""
    try:
        from .tools import read_file
        result = await read_file(file_path)
        if result.get('success'):
            return result.get('content', '')[:5000]  # Limit size
        return f"Could not read file: {result.get('error', 'Unknown error')}"
    except Exception as e:
        return f"Error reading file: {str(e)}"
