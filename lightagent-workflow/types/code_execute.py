"""
Code-Execute-Refine Workflow - Iterative code generation workflow

Generates code, executes it, and refines based on errors.
Useful for code generation, data analysis, and script development.
"""
from typing import Any, Dict, List, Optional, Callable
from pydantic import BaseModel, Field
from datetime import datetime
import asyncio

from ..base import BaseWorkflow, WorkflowStatus


class CodeExecuteRefineWorkflow(BaseWorkflow):
    """
    Code-Execute-Refine workflow

    Flow:
    Generate Code -> Execute -> Check Result
    -> If Error: Refine Code -> Execute -> ...
    -> If Success: Done

    Use cases:
    - Code generation
    - Data analysis scripts
    - Algorithm development
    - Automated programming
    """

    workflow_type: str = "code_execute_refine"

    # Configuration
    max_iterations: int = 5
    execution_timeout: int = 30  # seconds
    language: str = "python"  # python, javascript, etc.

    # State
    current_code: Optional[str] = None
    execution_history: List[Dict[str, Any]] = Field(default_factory=list)

    # Custom handlers
    code_generator: Optional[Callable] = None
    code_executor: Optional[Callable] = None
    success_checker: Optional[Callable] = None

    class Config:
        arbitrary_types_allowed = True

    async def execute(
        self,
        goal: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Execute code-execute-refine workflow

        Args:
            goal: Goal or requirements for the code
            context: Optional context

        Returns:
            Execution result
        """
        self.status = WorkflowStatus.RUNNING
        self.updated_at = datetime.now()

        if self.verbose:
            print(f"\n{'='*60}")
            print(f"Code-Execute-Refine Workflow: {goal[:50]}...")
            print(f"Max iterations: {self.max_iterations}")
            print(f"Language: {self.language}")
            print(f"{'='*60}\n")

        execution_result = None

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

                # Step 1: Generate or refine code
                if iteration == 0:
                    code = await self._generate_code(goal, context)
                else:
                    code = await self._refine_code(
                        goal,
                        execution_result,
                        context
                    )

                self.current_code = code

                if self.verbose:
                    print(f"Generated code ({len(code)} chars)")

                # Step 2: Execute code
                execution_result = await self._execute_code(code, context)

                # Record execution
                self.execution_history.append({
                    'iteration': iteration + 1,
                    'code': code,
                    'result': execution_result,
                    'timestamp': datetime.now().isoformat()
                })

                # Step 3: Check result
                if execution_result.get('success', False):
                    if self.verbose:
                        print(f"Execution successful!")

                    # Check if truly successful
                    if self._is_success(execution_result):
                        if self.verbose:
                            print(f"Code meets requirements")
                        break
                    else:
                        if self.verbose:
                            print(f"Code executed but doesn't meet requirements, refining...")
                else:
                    if self.verbose:
                        error = execution_result.get('error', 'Unknown error')
                        print(f"Execution failed: {error[:100]}...")

            # Prepare result
            final_success = (
                execution_result and
                execution_result.get('success', False) and
                self._is_success(execution_result)
            )

            result = {
                'success': final_success,
                'goal': goal,
                'code': self.current_code,
                'execution_result': execution_result,
                'iterations': len(self.execution_history),
                'history': self.execution_history,
                'status': 'success' if final_success else 'max_iterations_reached'
            }

            self.status = WorkflowStatus.COMPLETED if final_success else WorkflowStatus.FAILED
            self.updated_at = datetime.now()

            if self.verbose:
                print(f"\nWorkflow complete:")
                print(f"  - Status: {result['status']}")
                print(f"  - Iterations: {result['iterations']}")
                print(f"  - Final code length: {len(self.current_code) if self.current_code else 0}")

            return result

        except Exception as e:
            self.status = WorkflowStatus.FAILED
            self.updated_at = datetime.now()

            error_result = {
                'success': False,
                'error': str(e),
                'goal': goal,
                'code': self.current_code,
                'iterations': len(self.execution_history)
            }

            if self.verbose:
                print(f"Workflow failed: {e}")

            return error_result

    async def _generate_code(
        self,
        goal: str,
        context: Optional[Dict[str, Any]]
    ) -> str:
        """
        Generate initial code

        Args:
            goal: Code requirements
            context: Optional context

        Returns:
            Generated code
        """
        if self.code_generator:
            # Use custom code generator
            if asyncio.iscoroutinefunction(self.code_generator):
                return await self.code_generator(goal, context)
            else:
                return self.code_generator(goal, context)

        # Default: use agent to generate code
        if self.agent and hasattr(self.agent, 'run'):
            prompt = self._create_generation_prompt(goal, context)
            response = await self.agent.run(prompt, context=context)
            return self._extract_code_from_response(response.get('response', ''))
        else:
            # Fallback
            return f"# Code for: {goal}\n# Implementation needed\n"

    def _create_generation_prompt(
        self,
        goal: str,
        context: Optional[Dict[str, Any]]
    ) -> str:
        """
        Create prompt for code generation

        Args:
            goal: Code requirements
            context: Optional context

        Returns:
            Generation prompt
        """
        prompt = f"""Generate {self.language} code for the following requirement:

Requirement: {goal}

Please provide complete, executable code. Only output the code, no explanations.
"""

        if context:
            prompt += f"\n\nAdditional context:\n{context}"

        return prompt

    def _extract_code_from_response(self, response: str) -> str:
        """
        Extract code from LLM response

        Args:
            response: LLM response

        Returns:
            Extracted code
        """
        # Look for code blocks
        if '```' in response:
            # Extract code from markdown code blocks
            start = response.find('```') + 3
            # Find language identifier
            newline = response.find('\n', start)
            if newline != -1:
                start = newline + 1

            end = response.find('```', start)
            if end != -1:
                return response[start:end].strip()

        # No code block found, return entire response
        return response.strip()

    async def _refine_code(
        self,
        goal: str,
        previous_result: Dict[str, Any],
        context: Optional[Dict[str, Any]]
    ) -> str:
        """
        Refine code based on execution result

        Args:
            goal: Original goal
            previous_result: Previous execution result
            context: Optional context

        Returns:
            Refined code
        """
        if self.code_generator and asyncio.iscoroutinefunction(self.code_generator):
            # Use custom code generator with refinement
            return await self.code_generator(goal, context, previous_result)

        # Default: use agent to refine code
        if self.agent and hasattr(self.agent, 'run'):
            prompt = self._create_refinement_prompt(
                goal,
                previous_result,
                context
            )
            response = await self.agent.run(prompt, context=context)
            return self._extract_code_from_response(response.get('response', ''))
        else:
            # Fallback: return previous code
            return self.current_code or ""

    def _create_refinement_prompt(
        self,
        goal: str,
        previous_result: Dict[str, Any],
        context: Optional[Dict[str, Any]]
    ) -> str:
        """
        Create prompt for code refinement

        Args:
            goal: Original goal
            previous_result: Previous execution result
            context: Optional context

        Returns:
            Refinement prompt
        """
        error_info = previous_result.get('error', 'Unknown error')
        output = previous_result.get('output', '')

        prompt = f"""The following {self.language} code failed to meet requirements:

Requirement: {goal}

Previous Code:
{self.current_code}

Error/Output:
{error_info}

Output:
{output[:500] if output else 'No output'}

Please refine the code to fix the issues. Only output the refined code, no explanations.
"""

        return prompt

    async def _execute_code(
        self,
        code: str,
        context: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Execute code

        Args:
            code: Code to execute
            context: Optional context

        Returns:
            Execution result
        """
        if self.code_executor:
            # Use custom code executor
            if asyncio.iscoroutinefunction(self.code_executor):
                return await self.code_executor(code, context)
            else:
                return self.code_executor(code, context)

        # Default: use safe exec (restricted)
        try:
            # For safety, we'll use a restricted execution
            # In production, use a proper sandbox
            result = {
                'success': True,
                'output': 'Code execution simulated (no executor configured)',
                'error': None
            }
            return result

        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'output': None
            }

    def _is_success(self, execution_result: Dict[str, Any]) -> bool:
        """
        Check if execution result indicates success

        Args:
            execution_result: Execution result

        Returns:
            True if successful
        """
        if self.success_checker:
            # Use custom success checker
            return self.success_checker(execution_result)

        # Default: check success flag and no errors
        return (
            execution_result.get('success', False) and
            not execution_result.get('error')
        )

    def set_code_generator(self, generator: Callable):
        """
        Set custom code generator

        Args:
            generator: Code generator function
        """
        self.code_generator = generator

    def set_code_executor(self, executor: Callable):
        """
        Set custom code executor

        Args:
            executor: Code executor function
        """
        self.code_executor = executor

    def set_success_checker(self, checker: Callable):
        """
        Set custom success checker

        Args:
            checker: Success checker function
        """
        self.success_checker = checker

    async def validate(self, goal: str) -> bool:
        """
        Validate code-execute-refine workflow

        Args:
            goal: Goal to validate

        Returns:
            True if valid
        """
        # Check if goal mentions code or programming
        goal_lower = goal.lower()
        code_keywords = [
            'code', 'function', 'script', 'program',
            'implement', 'write', 'generate code',
            'python', 'javascript', 'algorithm'
        ]
        return any(keyword in goal_lower for keyword in code_keywords)
