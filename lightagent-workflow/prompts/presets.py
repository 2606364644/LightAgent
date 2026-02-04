"""
Predefined prompt templates for common use cases
"""
from typing import List
from .template import PromptTemplate, MultiPartPrompt
from .manager import PromptManager


def load_default_prompts(manager: PromptManager):
    """
    Load default prompt templates into the manager

    Args:
        manager: PromptManager instance
    """

    # === Planning Prompts ===

    manager.create_template_from_string(
        name="planner.task_decomposition",
        template_string="""You are an expert task planner. Your goal is to break down complex tasks into smaller, manageable steps.

Goal: {{goal}}

Context:
{{context}}

Please break this down into a step-by-step plan. For each step:
1. Give it a clear name
2. Describe what should be done
3. Identify dependencies on previous steps
4. Estimate complexity (simple/medium/complex)

Format your response as a numbered list.""",
        category="planning",
        description="Template for decomposing complex tasks into steps"
    )

    manager.create_template_from_string(
        name="planner.refine",
        template_string="""You are refining an existing plan based on feedback.

Original Plan:
{{plan}}

Feedback:
{{feedback}}

Please revise the plan to address the feedback. Maintain the structure but improve the approach.""",
        category="planning",
        description="Template for refining plans based on feedback"
    )

    manager.create_template_from_string(
        name="planner.status_check",
        template_string="""You are checking the status of an ongoing workflow.

Completed Steps:
{{completed_steps}}

Current Step:
{{current_step}}

Remaining Steps:
{{remaining_steps}}

Please provide a status update including:
1. Overall progress percentage
2. Any issues or blockers
3. Next immediate action
4. Estimated completion""",
        category="planning",
        description="Template for checking workflow status"
    )

    # === File System Prompts ===

    manager.create_template_from_string(
        name="filesystem.file_analysis",
        template_string="""You are analyzing files and directories.

Path: {{path}}
File Type: {{file_type}}

Content Summary:
{{content_summary}}

Please provide:
1. Brief description of the file contents
2. Key components or structures identified
3. Potential issues or improvements
4. Recommended actions""",
        category="filesystem",
        description="Template for analyzing file contents"
    )

    manager.create_template_from_string(
        name="filesystem.code_review",
        template_string="""You are reviewing code for quality and best practices.

File: {{file_path}}
Language: {{language}}

Code:
{{code}}

Please review:
1. Code quality and style
2. Potential bugs or issues
3. Security vulnerabilities
4. Performance concerns
5. Suggestions for improvement""",
        category="filesystem",
        description="Template for code review"
    )

    manager.create_template_from_string(
        name="filesystem.search_strategy",
        template_string="""You are planning a file search strategy.

Target: {{search_target}}
Root Directory: {{root_dir}}
Constraints: {{constraints}}

Please propose a search strategy including:
1. Which directories to search
2. File patterns to match
3. Content patterns to search for
4. Order of operations""",
        category="filesystem",
        description="Template for planning file search operations"
    )

    # === Agent Prompts ===

    manager.create_template_from_string(
        name="agent.orchestrator",
        template_string="""You are an agent orchestrator coordinating multiple specialized agents.

Available Agents:
{{agents_list}}

Task: {{task}}

Please determine:
1. Which agents should handle this task
2. The order of delegation
3. What information to pass between agents
4. How to combine their results""",
        category="agent",
        description="Template for orchestrating multiple agents"
    )

    manager.create_template_from_string(
        name="agent.task_assignment",
        template_string="""You are assigning a task to a specialized agent.

Agent: {{agent_name}}
Agent Capabilities: {{capabilities}}

Task: {{task}}
Context: {{context}}

Please prepare:
1. Clear instructions for the agent
2. Required context and data
3. Expected output format
4. Success criteria""",
        category="agent",
        description="Template for assigning tasks to agents"
    )

    # === Research Prompts ===

    manager.create_template_from_string(
        name="research.research_plan",
        template_string="""You are planning a research project.

Research Topic: {{topic}}
Objectives: {{objectives}}
Constraints: {{constraints}}

Please create a research plan including:
1. Key research questions
2. Information sources to explore
3. Research methodology
4. Timeline and milestones
5. Deliverables""",
        category="research",
        description="Template for planning research projects"
    )

    manager.create_template_from_string(
        name="research.synthesis",
        template_string="""You are synthesizing research findings.

Research Topic: {{topic}}
Findings:
{{findings}}

Please provide:
1. Summary of key findings
2. Common themes and patterns
3. Conflicting information and how to resolve
4. Knowledge gaps identified
5. Recommendations based on findings""",
        category="research",
        description="Template for synthesizing research"
    )

    # === Coding Prompts ===

    manager.create_template_from_string(
        name="coding.feature_planning",
        template_string="""You are planning a software feature.

Feature Request: {{feature}}
Requirements: {{requirements}}
Technical Context: {{tech_context}}

Please create an implementation plan:
1. Feature breakdown into tasks
2. Technical approach and architecture
3. Code structure and organization
4. Testing strategy
5. Potential risks and mitigation""",
        category="coding",
        description="Template for planning software features"
    )

    manager.create_template_from_string(
        name="coding.debug_strategy",
        template_string="""You are creating a debugging strategy.

Error: {{error}}
Context: {{context}}
Recent Changes: {{recent_changes}}

Please develop a debugging strategy:
1. Analyze the error
2. Identify potential root causes
3. List diagnostic steps
4. Suggest fixes to try
5. Prevention strategies for the future""",
        category="coding",
        description="Template for debugging strategy"
    )

    # === Multipart Prompts ===

    multipart_system = PromptTemplate(
        template="""You are {{role}} with expertise in {{expertise}}.

Your goal is to {{goal}}.

Guidelines:
- Be thorough and analytical
- Provide clear reasoning
- Consider multiple perspectives
- Acknowledge uncertainties""",
        description="Generic system prompt template"
    )

    multipart_user = PromptTemplate(
        template="""Task: {{task}}

Additional Context:
{{context}}

Please proceed step by step and explain your reasoning.""",
        description="Generic user prompt template"
    )

    manager.register_multipart(
        name="generic.assistant",
        template=MultiPartPrompt(
            system=multipart_system,
            user=multipart_user
        ),
        category="generic",
        description="Generic multi-part prompt for assistant"
    )

    # Code review multipart
    code_review_system = PromptTemplate(
        template="""You are an expert code reviewer with deep knowledge of {{language}} and software best practices.

Your role is to:
1. Identify bugs and potential issues
2. Suggest improvements
3. Ensure code follows best practices
4. Check for security vulnerabilities""",
        description="System prompt for code review"
    )

    code_review_user = PromptTemplate(
        template="""Please review the following code:

File: {{file_path}}
```{{language}}
{{code}}
```

Focus areas: {{focus_areas}}""",
        description="User prompt for code review"
    )

    manager.register_multipart(
        name="coding.review",
        template=MultiPartPrompt(
            system=code_review_system,
            user=code_review_user
        ),
        category="coding",
        description="Multi-part prompt for code review"
    )


def get_default_prompts() -> PromptManager:
    """
    Get a prompt manager with default templates loaded

    Returns:
        PromptManager with default templates
    """
    manager = PromptManager()
    load_default_prompts(manager)
    return manager
