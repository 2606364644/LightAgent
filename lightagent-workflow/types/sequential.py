"""
Sequential Workflow - Fixed step sequence workflow

Executes a predefined sequence of steps in order.
Useful for pipelines, CI/CD, and fixed procedures.
"""
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from datetime import datetime

from ..base import BaseWorkflow, WorkflowStatus, WorkflowStep, WorkflowState


class SimpleStep(WorkflowStep):
    """
    Simple implementation of WorkflowStep
    """

    async def execute(self, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Execute the step

        Args:
            context: Execution context

        Returns:
            Step result
        """
        context = context or {}

        if self.agent and hasattr(self.agent, 'run'):
            # Use agent to execute
            result = await self.agent.run(
                self.description or self.action,
                context=context
            )
            return result
        else:
            # Simple execution
            return {
                'success': True,
                'step': self.name,
                'action': self.action,
                'message': f'Executed step: {self.name}'
            }


class SequentialWorkflow(BaseWorkflow):
    """
    Sequential workflow with fixed steps

    Flow:
    Step1 -> Step2 -> Step3 -> ... -> Finish

    Use cases:
    - CI/CD pipelines
    - Data processing pipelines
    - Multi-step procedures
    - Quality gates
    """

    workflow_type: str = "sequential"

    # Steps
    steps: List[SimpleStep] = Field(default_factory=list)

    # Configuration
    stop_on_first_failure: bool = True
    continue_on_error: bool = False
    skip_existing: bool = False

    class Config:
        arbitrary_types_allowed = True

    def __init__(self, **data):
        super().__init__(**data)

        # Create steps from config if provided
        if 'config' in data and 'steps' in data['config']:
            step_configs = data['config']['steps']
            self.steps = []

            for step_config in step_configs:
                step = SimpleStep(
                    name=step_config.get('name', 'Unnamed'),
                    description=step_config.get('description', ''),
                    action=step_config.get('action'),
                    agent=step_config.get('agent', self.agent),
                    stop_on_failure=step_config.get('stop_on_failure', False),
                    config=step_config.get('config', {})
                )
                self.steps.append(step)

    async def execute(
        self,
        goal: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Execute sequential workflow

        Args:
            goal: Goal (not used in sequential, steps are predefined)
            context: Optional context

        Returns:
            Execution result
        """
        self.status = WorkflowStatus.RUNNING
        self.updated_at = datetime.now()

        if self.verbose:
            print(f"\n{'='*60}")
            print(f"Sequential Workflow: {goal}")
            print(f"Steps: {len(self.steps)}")
            print(f"{'='*60}\n")

        # Initialize state
        self.current_state = WorkflowState(
            workflow_id=self.workflow_id,
            current_step=0,
            total_steps=len(self.steps),
            context=context or {}
        )

        results = []
        failed_steps = []

        try:
            for i, step in enumerate(self.steps):
                if self.verbose:
                    print(f"\nStep {i+1}/{len(self.steps)}: {step.name}")

                # Check if workflow was cancelled
                if self.status == WorkflowStatus.CANCELLED:
                    if self.verbose:
                        print(f"Workflow cancelled at step {i+1}")
                    break

                # Check if workflow was paused
                while self.status == WorkflowStatus.PAUSED:
                    await asyncio.sleep(0.1)

                try:
                    # Execute step
                    result = await step.execute(context)
                    results.append(result)

                    # Update state
                    self.current_state.current_step = i + 1

                    # Check if step failed
                    if not result.get('success', True):
                        failed_steps.append({
                            'step': step.name,
                            'error': result.get('error', 'Unknown error')
                        })

                        if step.stop_on_failure or self.stop_on_first_failure:
                            if self.verbose:
                                print(f"  Step failed, stopping workflow")
                            break
                        elif not self.continue_on_error:
                            if self.verbose:
                                print(f"  Step failed, stopping workflow")
                            break

                    if self.verbose:
                        print(f"  Completed: {result.get('message', 'OK')}")

                except Exception as e:
                    error_msg = str(e)
                    if self.verbose:
                        print(f"  Error: {error_msg}")

                    failed_steps.append({
                        'step': step.name,
                        'error': error_msg
                    })

                    if step.stop_on_failure or self.stop_on_first_failure:
                        break

            # Prepare result
            all_succeeded = len(failed_steps) == 0

            result = {
                'success': all_succeeded,
                'goal': goal,
                'total_steps': len(self.steps),
                'completed_steps': len(results),
                'failed_steps': len(failed_steps),
                'results': results,
                'errors': failed_steps,
                'progress': self.get_progress()
            }

            # Update status
            if all_succeeded:
                self.status = WorkflowStatus.COMPLETED
            else:
                self.status = WorkflowStatus.FAILED

            self.updated_at = datetime.now()

            if self.verbose:
                print(f"\nExecution complete:")
                print(f"  - Completed: {len(results)}/{len(self.steps)}")
                print(f"  - Failed: {len(failed_steps)}")

            return result

        except Exception as e:
            self.status = WorkflowStatus.FAILED
            self.updated_at = datetime.now()

            error_result = {
                'success': False,
                'error': str(e),
                'goal': goal
            }

            if self.verbose:
                print(f"Workflow failed: {e}")

            return error_result

    def add_step(
        self,
        name: str,
        action: Optional[str] = None,
        description: str = "",
        stop_on_failure: bool = False,
        agent: Optional[Any] = None
    ):
        """
        Add a step to the workflow

        Args:
            name: Step name
            action: Action to perform
            description: Step description
            stop_on_failure: Stop workflow if this step fails
            agent: Optional agent for this step
        """
        step = SimpleStep(
            name=name,
            description=description,
            action=action,
            agent=agent or self.agent,
            stop_on_failure=stop_on_failure
        )
        self.steps.append(step)

    def remove_step(self, step_name: str):
        """
        Remove a step by name

        Args:
            step_name: Name of step to remove
        """
        self.steps = [s for s in self.steps if s.name != step_name]

    async def validate(self, goal: str) -> bool:
        """
        Validate sequential workflow

        Args:
            goal: Goal to validate

        Returns:
            True if valid
        """
        # Sequential workflow requires at least one step
        return len(self.steps) > 0


# Import asyncio for async sleep
import asyncio
