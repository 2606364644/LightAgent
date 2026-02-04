"""
Human-in-the-Loop Workflow - Human approval workflow

Agent proposes actions, human approves/rejects, then continues.
Useful for content moderation, critical decisions, and supervised workflows.
"""
from typing import Any, Dict, List, Optional, Callable
from pydantic import BaseModel, Field
from datetime import datetime
import asyncio

from ..base import BaseWorkflow, WorkflowStatus


class ActionProposal(BaseModel):
    """An action proposal from the agent"""
    action_id: str
    action_type: str
    description: str
    details: Dict[str, Any] = Field(default_factory=dict)
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())


class ApprovalResult(BaseModel):
    """Result of human approval"""
    approved: bool
    feedback: Optional[str] = None
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())


class HumanInTheLoopWorkflow(BaseWorkflow):
    """
    Human-in-the-loop workflow with approval mechanism

    Flow:
    Agent Proposes Action -> Human Reviews -> Approve/Reject
    -> If Approved: Execute -> Continue
    -> If Rejected: Provide Feedback -> Retry

    Use cases:
    - Content moderation
    - Critical decisions
    - Supervised automation
    - Quality assurance
    """

    workflow_type: str = "human_loop"

    # Configuration
    max_iterations: int = 10
    require_approval: bool = True
    auto_approve_safe_actions: bool = False

    # State
    proposal_history: List[Dict[str, Any]] = Field(default_factory=list)
    current_proposal: Optional[ActionProposal] = None

    # Custom handlers
    action_proposer: Optional[Callable] = None
    action_executor: Optional[Callable] = None
    approval_requester: Optional[Callable] = None
    completion_checker: Optional[Callable] = None

    class Config:
        arbitrary_types_allowed = True

    async def execute(
        self,
        goal: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Execute human-in-the-loop workflow

        Args:
            goal: Goal to achieve
            context: Optional context

        Returns:
            Execution result
        """
        self.status = WorkflowStatus.RUNNING
        self.updated_at = datetime.now()

        if self.verbose:
            print(f"\n{'='*60}")
            print(f"Human-in-the-Loop Workflow: {goal[:50]}...")
            print(f"Max iterations: {self.max_iterations}")
            print(f"{'='*60}\n")

        context = context or {}

        try:
            for iteration in range(self.max_iterations):
                if self.verbose:
                    print(f"\n--- Iteration {iteration + 1}/{self.max_iterations} ---")

                # Check for cancellation
                if self.status == WorkflowStatus.CANCELLED:
                    if self.verbose:
                        print("Workflow cancelled")
                    break

                # Check for pause
                while self.status == WorkflowStatus.PAUSED:
                    await asyncio.sleep(0.1)

                # Step 1: Check if complete
                if self._is_complete(context):
                    if self.verbose:
                        print("Goal completed")
                    break

                # Step 2: Agent proposes action
                proposal = await self._propose_action(goal, context)
                self.current_proposal = proposal

                if self.verbose:
                    print(f"Proposed action: {proposal.action_type}")
                    print(f"Description: {proposal.description}")

                # Step 3: Request human approval
                approval = await self._request_approval(proposal, context)

                # Record proposal
                self.proposal_history.append({
                    'iteration': iteration + 1,
                    'proposal': proposal.dict(),
                    'approval': approval.dict(),
                    'timestamp': datetime.now().isoformat()
                })

                if not approval.approved:
                    if self.verbose:
                        print(f"Action rejected: {approval.feedback or 'No feedback'}")

                    # Add feedback to context and retry
                    context['last_feedback'] = approval.feedback
                    context['last_proposal'] = proposal.dict()
                    continue

                # Step 4: Execute approved action
                if self.verbose:
                    print(f"Action approved, executing...")

                execution_result = await self._execute_action(proposal, context)

                # Update context with execution result
                context['last_result'] = execution_result
                context['last_proposal'] = proposal.dict()

                if self.verbose:
                    print(f"Execution complete: {execution_result.get('message', 'OK')}")

            # Prepare result
            is_complete = self._is_complete(context)
            total_approved = len([
                p for p in self.proposal_history
                if p['approval']['approved']
            ])
            total_rejected = len([
                p for p in self.proposal_history
                if not p['approval']['approved']
            ])

            result = {
                'success': is_complete,
                'goal': goal,
                'completed': is_complete,
                'total_proposals': len(self.proposal_history),
                'approved': total_approved,
                'rejected': total_rejected,
                'proposal_history': self.proposal_history,
                'final_context': context
            }

            self.status = WorkflowStatus.COMPLETED if is_complete else WorkflowStatus.FAILED
            self.updated_at = datetime.now()

            if self.verbose:
                print(f"\nWorkflow complete:")
                print(f"  - Status: {'Completed' if is_complete else 'Incomplete'}")
                print(f"  - Total proposals: {len(self.proposal_history)}")
                print(f"  - Approved: {total_approved}")
                print(f"  - Rejected: {total_rejected}")

            return result

        except Exception as e:
            self.status = WorkflowStatus.FAILED
            self.updated_at = datetime.now()

            error_result = {
                'success': False,
                'error': str(e),
                'goal': goal,
                'proposal_history': self.proposal_history
            }

            if self.verbose:
                print(f"Workflow failed: {e}")

            return error_result

    async def _propose_action(
        self,
        goal: str,
        context: Dict[str, Any]
    ) -> ActionProposal:
        """
        Generate action proposal

        Args:
            goal: Current goal
            context: Execution context

        Returns:
            Action proposal
        """
        if self.action_proposer:
            # Use custom action proposer
            if asyncio.iscoroutinefunction(self.action_proposer):
                return await self.action_proposer(goal, context)
            else:
                return self.action_proposer(goal, context)

        # Default: use agent to propose action
        if self.agent and hasattr(self.agent, 'run'):
            prompt = self._create_proposal_prompt(goal, context)
            response = await self.agent.run(prompt, context=context)
            return self._parse_proposal(response.get('response', ''))
        else:
            # Fallback
            return ActionProposal(
                action_id=str(hash(goal)),
                action_type="general",
                description=f"Work on: {goal}"
            )

    def _create_proposal_prompt(
        self,
        goal: str,
        context: Dict[str, Any]
    ) -> str:
        """
        Create prompt for action proposal

        Args:
            goal: Current goal
            context: Execution context

        Returns:
            Proposal prompt
        """
        prompt = f"""Propose an action to achieve the following goal:

Goal: {goal}
"""

        if context.get('last_feedback'):
            prompt += f"\nPrevious feedback: {context['last_feedback']}"

        if context.get('last_result'):
            prompt += f"\nPrevious result: {context['last_result']}"

        prompt += """
Please provide:
1. Action type (e.g., 'create', 'modify', 'analyze', 'review')
2. Description of what you will do
3. Details of the action

Format as JSON:
{
  "action_type": "...",
  "description": "...",
  "details": {...}
}
"""

        return prompt

    def _parse_proposal(self, response: str) -> ActionProposal:
        """
        Parse action proposal from response

        Args:
            response: Agent response

        Returns:
            Action proposal
        """
        import json

        try:
            # Try to parse JSON
            if '```json' in response:
                start = response.find('```json') + 7
                end = response.find('```', start)
                json_str = response[start:end].strip()
                data = json.loads(json_str)
            else:
                # Try to find JSON object
                start = response.find('{')
                end = response.rfind('}') + 1
                if start != -1 and end > start:
                    json_str = response[start:end]
                    data = json.loads(json_str)
                else:
                    raise ValueError("No JSON found")

            return ActionProposal(
                action_id=str(hash(data.get('description', ''))),
                action_type=data.get('action_type', 'general'),
                description=data.get('description', ''),
                details=data.get('details', {})
            )

        except Exception as e:
            # Fallback
            return ActionProposal(
                action_id=str(hash(response)),
                action_type="general",
                description=response[:200],
                details={'raw_response': response}
            )

    async def _request_approval(
        self,
        proposal: ActionProposal,
        context: Dict[str, Any]
    ) -> ApprovalResult:
        """
        Request human approval

        Args:
            proposal: Action proposal
            context: Execution context

        Returns:
            Approval result
        """
        if self.approval_requester:
            # Use custom approval requester
            if asyncio.iscoroutinefunction(self.approval_requester):
                return await self.approval_requester(proposal, context)
            else:
                return self.approval_requester(proposal, context)

        # Default: auto-approve if configured
        if self.auto_approve_safe_actions:
            safe_actions = ['analyze', 'review', 'read']
            if proposal.action_type.lower() in safe_actions:
                return ApprovalResult(approved=True, feedback=None)

        # Otherwise, require manual approval (return pending)
        # In real usage, this would wait for human input
        return ApprovalResult(
            approved=False,
            feedback="No approval handler configured"
        )

    async def _execute_action(
        self,
        proposal: ActionProposal,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute approved action

        Args:
            proposal: Approved action proposal
            context: Execution context

        Returns:
            Execution result
        """
        if self.action_executor:
            # Use custom action executor
            if asyncio.iscoroutinefunction(self.action_executor):
                return await self.action_executor(proposal, context)
            else:
                return self.action_executor(proposal, context)

        # Default: use agent to execute
        if self.agent and hasattr(self.agent, 'run'):
            prompt = f"Execute the following action:\n{proposal.description}"
            if proposal.details:
                prompt += f"\n\nDetails: {proposal.details}"

            response = await self.agent.run(prompt, context=context)
            return response
        else:
            # Fallback
            return {
                'success': True,
                'message': f"Executed: {proposal.description}",
                'proposal': proposal.dict()
            }

    def _is_complete(self, context: Dict[str, Any]) -> bool:
        """
        Check if goal is complete

        Args:
            context: Execution context

        Returns:
            True if complete
        """
        if self.completion_checker:
            # Use custom completion checker
            return self.completion_checker(context)

        # Default: check context for completion flag
        return context.get('completed', False)

    def set_action_proposer(self, proposer: Callable):
        """
        Set custom action proposer

        Args:
            proposer: Action proposer function
        """
        self.action_proposer = proposer

    def set_action_executor(self, executor: Callable):
        """
        Set custom action executor

        Args:
            executor: Action executor function
        """
        self.action_executor = executor

    def set_approval_requester(self, requester: Callable):
        """
        Set custom approval requester

        Args:
            requester: Approval requester function
        """
        self.approval_requester = requester

    def set_completion_checker(self, checker: Callable):
        """
        Set custom completion checker

        Args:
            checker: Completion checker function
        """
        self.completion_checker = checker

    async def validate(self, goal: str) -> bool:
        """
        Validate human-in-the-loop workflow

        Args:
            goal: Goal to validate

        Returns:
            True if valid
        """
        # Human-in-the-loop is suitable for any goal
        return len(goal.strip()) > 0
