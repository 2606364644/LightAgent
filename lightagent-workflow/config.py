"""
Workflow Configuration System

Provides configuration classes for workflows with support for
custom prompts, tools, and execution parameters.
"""
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field
from .prompts import WorkflowPromptTemplate, WorkflowPromptRegistry
from .tools import ToolRegistry, WorkflowToolManager


class WorkflowToolConfig(BaseModel):
    """
    Tool configuration for a workflow
    """
    # Tool sources
    use_global_tools: bool = True
    use_workflow_tools: bool = True
    additional_tools: List[Any] = Field(default_factory=list)

    # Tool filtering
    include_tools: Optional[List[str]] = None  # Whitelist
    exclude_tools: Optional[List[str]] = None  # Blacklist

    class Config:
        arbitrary_types_allowed = True


class WorkflowPromptConfig(BaseModel):
    """
    Prompt configuration for a workflow
    """
    # Prompt template
    template_name: Optional[str] = None
    system_prompt: Optional[str] = None
    task_prompt: Optional[str] = None

    # Prompt variables
    variables: Dict[str, Any] = Field(default_factory=dict)

    # Prompt overrides
    override_system_prompt: bool = False
    override_task_prompt: bool = False


class WorkflowExecutionConfig(BaseModel):
    """
    Execution configuration for a workflow
    """
    # Execution mode
    execution_mode: str = "sequential"  # sequential, parallel, adaptive
    max_iterations: int = 10
    timeout: Optional[int] = None

    # Error handling
    stop_on_first_error: bool = False
    retry_errors: bool = True
    max_retries: int = 3

    # Verbosity
    verbose: bool = True
    log_interval: int = 1


class ExtendedWorkflowConfig(BaseModel):
    """
    Extended workflow configuration

    Combines prompt, tool, and execution configurations
    for comprehensive workflow customization.
    """

    # Basic info
    workflow_type: str
    name: Optional[str] = None
    description: Optional[str] = None

    # Prompt configuration
    prompts: WorkflowPromptConfig = Field(default_factory=WorkflowPromptConfig)

    # Tool configuration
    tools: WorkflowToolConfig = Field(default_factory=WorkflowToolConfig)

    # Execution configuration
    execution: WorkflowExecutionConfig = Field(default_factory=WorkflowExecutionConfig)

    # Custom configuration
    custom: Dict[str, Any] = Field(default_factory=dict)

    # Registry references (usually not set by user)
    _prompt_registry: Optional[WorkflowPromptRegistry] = None
    _tool_registry: Optional[ToolRegistry] = None

    class Config:
        arbitrary_types_allowed = True

    def get_prompt_template(
        self,
        registry: WorkflowPromptRegistry
    ) -> Optional[WorkflowPromptTemplate]:
        """
        Get prompt template for this workflow

        Args:
            registry: Prompt registry

        Returns:
            Prompt template or None
        """
        # Use specified template
        if self.prompts.template_name:
            return registry.get_template(self.prompts.template_name)

        # Get default template for workflow type
        templates = registry.get_templates_for_workflow(self.workflow_type)
        if templates:
            return templates[0]

        return None

    def get_system_prompt(
        self,
        registry: WorkflowPromptRegistry,
        **variables
    ) -> str:
        """
        Get system prompt

        Args:
            registry: Prompt registry
            **variables: Additional variables

        Returns:
            Formatted system prompt
        """
        # Override if specified
        if self.prompts.override_system_prompt and self.prompts.system_prompt:
            prompt = self.prompts.system_prompt
            for key, value in {**self.prompts.variables, **variables}.items():
                prompt = prompt.replace(f"{{{key}}}", str(value))
            return prompt

        # Use template
        template = self.get_prompt_template(registry)
        if template:
            return template.get_system_prompt(
                **{**self.prompts.variables, **variables}
            )

        return ""

    def get_task_prompt(
        self,
        registry: WorkflowPromptRegistry,
        **variables
    ) -> str:
        """
        Get task prompt

        Args:
            registry: Prompt registry
            **variables: Additional variables

        Returns:
            Formatted task prompt
        """
        # Override if specified
        if self.prompts.override_task_prompt and self.prompts.task_prompt:
            prompt = self.prompts.task_prompt
            for key, value in {**self.prompts.variables, **variables}.items():
                prompt = prompt.replace(f"{{{key}}}", str(value))
            return prompt

        # Use template
        template = self.get_prompt_template(registry)
        if template:
            return template.format(**{**self.prompts.variables, **variables})

        return "{goal}"

    def get_tool_manager(
        self,
        registry: ToolRegistry
    ) -> WorkflowToolManager:
        """
        Get tool manager for this workflow

        Args:
            registry: Tool registry

        Returns:
            WorkflowToolManager instance
        """
        manager = WorkflowToolManager(
            workflow_type=self.workflow_type,
            tool_registry=registry,
            use_global_tools=self.tools.use_global_tools,
            use_workflow_tools=self.tools.use_workflow_tools
        )

        # Add additional tools
        for tool in self.tools.additional_tools:
            manager.add_tool(tool)

        # Apply filters
        if self.tools.include_tools:
            # Only include specified tools
            all_tools = manager.get_tools()
            for tool in all_tools:
                tool_name = getattr(tool, 'name', '')
                if tool_name not in self.tools.include_tools:
                    manager.instance_tools.pop(tool_name, None)

        if self.tools.exclude_tools:
            # Exclude specified tools
            for tool_name in self.tools.exclude_tools:
                # Would need to implement removal in manager
                pass

        return manager


def create_workflow_config(
    workflow_type: str,
    **kwargs
) -> ExtendedWorkflowConfig:
    """
    Create workflow configuration with defaults

    Args:
        workflow_type: Type of workflow
        **kwargs: Additional configuration

    Returns:
        ExtendedWorkflowConfig instance
    """
    return ExtendedWorkflowConfig(
        workflow_type=workflow_type,
        **kwargs
    )


# Predefined configurations for common use cases

def planning_workflow_config(
    max_recursion_depth: int = 3,
    execution_mode: str = "sequential",
    **kwargs
) -> ExtendedWorkflowConfig:
    """Configuration for planning workflow"""
    return create_workflow_config(
        workflow_type="planning",
        execution=WorkflowExecutionConfig(
            execution_mode=execution_mode,
            max_iterations=max_recursion_depth,
            verbose=True
        ),
        prompts=WorkflowPromptConfig(
            template_name="default_planning"
        ),
        **kwargs
    )


def sequential_workflow_config(
    steps: List[Dict[str, Any]],
    stop_on_first_failure: bool = True,
    **kwargs
) -> ExtendedWorkflowConfig:
    """Configuration for sequential workflow"""
    return create_workflow_config(
        workflow_type="sequential",
        execution=WorkflowExecutionConfig(
            stop_on_first_error=stop_on_first_failure,
            verbose=True
        ),
        custom={'steps': steps},
        **kwargs
    )


def interactive_workflow_config(
    max_rounds: int = 10,
    system_prompt: Optional[str] = None,
    **kwargs
) -> ExtendedWorkflowConfig:
    """Configuration for interactive workflow"""
    return create_workflow_config(
        workflow_type="interactive",
        execution=WorkflowExecutionConfig(
            max_iterations=max_rounds,
            verbose=True
        ),
        prompts=WorkflowPromptConfig(
            template_name="default_interactive",
            system_prompt=system_prompt,
            override_system_prompt=bool(system_prompt)
        ),
        **kwargs
    )


def code_execute_workflow_config(
    language: str = "python",
    max_iterations: int = 5,
    **kwargs
) -> ExtendedWorkflowConfig:
    """Configuration for code-execute-refine workflow"""
    return create_workflow_config(
        workflow_type="code_execute_refine",
        execution=WorkflowExecutionConfig(
            max_iterations=max_iterations,
            verbose=True
        ),
        prompts=WorkflowPromptConfig(
            template_name="default_code_execute"
        ),
        custom={'language': language},
        **kwargs
    )


def human_loop_workflow_config(
    max_iterations: int = 10,
    auto_approve_safe: bool = False,
    **kwargs
) -> ExtendedWorkflowConfig:
    """Configuration for human-in-the-loop workflow"""
    return create_workflow_config(
        workflow_type="human_loop",
        execution=WorkflowExecutionConfig(
            max_iterations=max_iterations,
            verbose=True
        ),
        prompts=WorkflowPromptConfig(
            template_name="default_human_loop"
        ),
        custom={'auto_approve_safe_actions': auto_approve_safe},
        **kwargs
    )
