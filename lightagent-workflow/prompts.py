"""
Workflow Prompt and Tool Management System

Manages prompt templates and tool pools for different workflow types.
"""
from typing import Any, Dict, List, Optional, Type
from pydantic import BaseModel, Field
from pathlib import Path


class WorkflowPromptTemplate(BaseModel):
    """
    Prompt template for a specific workflow type
    """
    name: str
    workflow_type: str
    system_prompt: Optional[str] = None
    task_prompt: Optional[str] = None
    variables: Dict[str, Any] = Field(default_factory=dict)

    def format(self, **kwargs) -> str:
        """Format prompt with variables"""
        prompt = self.task_prompt or ""
        for key, value in {**self.variables, **kwargs}.items():
            prompt = prompt.replace(f"{{{key}}}", str(value))
        return prompt

    def get_system_prompt(self, **kwargs) -> str:
        """Get formatted system prompt"""
        if not self.system_prompt:
            return ""
        prompt = self.system_prompt
        for key, value in kwargs.items():
            prompt = prompt.replace(f"{{{key}}}", str(value))
        return prompt


class WorkflowPromptRegistry(BaseModel):
    """
    Registry for workflow prompt templates

    Manages prompt templates for different workflow types.
    """
    templates: Dict[str, WorkflowPromptTemplate] = Field(default_factory=dict)

    def register_template(self, template: WorkflowPromptTemplate):
        """Register a prompt template"""
        self.templates[template.name] = template

    def get_template(self, name: str) -> Optional[WorkflowPromptTemplate]:
        """Get a prompt template by name"""
        return self.templates.get(name)

    def get_templates_for_workflow(
        self,
        workflow_type: str
    ) -> List[WorkflowPromptTemplate]:
        """Get all templates for a workflow type"""
        return [
            t for t in self.templates.values()
            if t.workflow_type == workflow_type
        ]

    def list_templates(self, workflow_type: Optional[str] = None) -> List[str]:
        """List template names"""
        if workflow_type:
            return [
                t.name for t in self.templates.values()
                if t.workflow_type == workflow_type
            ]
        return list(self.templates.keys())


# Default prompt templates for each workflow type
DEFAULT_PLANNING_PROMPT = WorkflowPromptTemplate(
    name="default_planning",
    workflow_type="planning",
    system_prompt="""You are an expert task planner. Your job is to break down complex goals into clear, actionable steps.

For each task, provide:
1. Task name (short and clear)
2. Detailed description
3. Dependencies (which tasks must be completed first)
4. Complexity level (simple/medium/complex)
5. Priority (low/medium/high/critical)

Think step by step and create a comprehensive plan.""",
    task_prompt="""Goal: {goal}

{context_info}

Please create a detailed step-by-step plan to achieve this goal.

Format your response as a numbered list, with each step including:
- Name
- Description
- Dependencies
- Complexity
- Priority"""
)

DEFAULT_SEQUENTIAL_PROMPT = WorkflowPromptTemplate(
    name="default_sequential",
    workflow_type="sequential",
    system_prompt="""You are a reliable workflow executor. You execute steps sequentially and carefully.""",
    task_prompt="""Execute step: {step_name}

Description: {description}

Context: {context}"""
)

DEFAULT_INTERACTIVE_PROMPT = WorkflowPromptTemplate(
    name="default_interactive",
    workflow_type="interactive",
    system_prompt="""You are a helpful conversational AI assistant. Engage in natural, friendly dialogue.""",
    task_prompt="""{conversation_history}

User: {user_input}

Provide a helpful response."""
)

DEFAULT_CODE_EXECUTE_PROMPT = WorkflowPromptTemplate(
    name="default_code_execute",
    workflow_type="code_execute_refine",
    system_prompt="""You are an expert programmer. Write clean, efficient, and well-documented code.

Always:
1. Write complete, executable code
2. Include error handling
3. Add comments for clarity
4. Follow best practices
5. Consider edge cases""",
    task_prompt="""Write {language} code for the following requirement:

Requirement: {goal}

{context_info}

Provide only the executable code, no explanations."""
)

DEFAULT_CODE_REFINE_PROMPT = WorkflowPromptTemplate(
    name="default_code_refine",
    workflow_type="code_execute_refine",
    system_prompt="""You are an expert at debugging and refining code. Analyze errors and provide fixes.""",
    task_prompt="""The following code failed:

Original Code:
{current_code}

Error/Issue:
{error_info}

Output:
{output}

Please refine the code to fix the issue. Provide only the corrected code."""
)

DEFAULT_HUMAN_LOOP_PROMPT = WorkflowPromptTemplate(
    name="default_human_loop",
    workflow_type="human_loop",
    system_prompt="""You are a helpful AI assistant. When proposing actions, be clear and provide all necessary details for human review.""",
    task_prompt="""Goal: {goal}

{context_info}

Propose an action to make progress toward this goal.

Provide:
1. Action type (create/modify/analyze/review/etc.)
2. Description of what you will do
3. Details of the action

Format as JSON."""
)


def create_default_prompt_registry() -> WorkflowPromptRegistry:
    """Create prompt registry with default templates"""
    registry = WorkflowPromptRegistry()

    # Register all default templates
    registry.register_template(DEFAULT_PLANNING_PROMPT)
    registry.register_template(DEFAULT_SEQUENTIAL_PROMPT)
    registry.register_template(DEFAULT_INTERACTIVE_PROMPT)
    registry.register_template(DEFAULT_CODE_EXECUTE_PROMPT)
    registry.register_template(DEFAULT_CODE_REFINE_PROMPT)
    registry.register_template(DEFAULT_HUMAN_LOOP_PROMPT)

    return registry
