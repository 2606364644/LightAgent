"""
Interactive Workflow - Multi-round conversation workflow

Manages conversational interactions with multiple turns.
Useful for chatbots, Q&A systems, and interactive assistants.
"""
from typing import Any, Dict, List, Optional, Callable
from pydantic import BaseModel, Field
from datetime import datetime
import asyncio

from ..base import BaseWorkflow, WorkflowStatus


class Message(BaseModel):
    """A message in the conversation"""
    role: str  # 'user', 'assistant', 'system'
    content: str
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
    metadata: Dict[str, Any] = Field(default_factory=dict)


class InteractiveWorkflow(BaseWorkflow):
    """
    Interactive multi-round conversation workflow

    Flow:
    User Input -> LLM -> Output -> User Input -> LLM -> ...

    Use cases:
    - Chatbots
    - Q&A systems
    - Interactive assistants
    - Conversational agents
    """

    workflow_type: str = "interactive"

    # Configuration
    max_rounds: int = 10
    min_rounds: int = 1
    conversation_timeout: int = 300  # seconds

    # Conversation state
    conversation_history: List[Message] = Field(default_factory=list)
    system_prompt: Optional[str] = None

    # Input/output handlers
    input_handler: Optional[Callable] = None
    output_handler: Optional[Callable] = None
    completion_checker: Optional[Callable] = None

    class Config:
        arbitrary_types_allowed = True

    async def execute(
        self,
        goal: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Execute interactive workflow

        Args:
            goal: Initial goal or message
            context: Optional context

        Returns:
            Conversation result
        """
        self.status = WorkflowStatus.RUNNING
        self.updated_at = datetime.now()

        if self.verbose:
            print(f"\n{'='*60}")
            print(f"Interactive Workflow: {goal[:50]}...")
            print(f"Max rounds: {self.max_rounds}")
            print(f"{'='*60}\n")

        # Initialize conversation
        if self.system_prompt:
            self.conversation_history.append(
                Message(role='system', content=self.system_prompt)
            )

        # Add initial user message
        self.conversation_history.append(
            Message(role='user', content=goal)
        )

        try:
            for round_num in range(self.max_rounds):
                if self.verbose:
                    print(f"\n--- Round {round_num + 1}/{self.max_rounds} ---")

                # Check for cancellation
                if self.status == WorkflowStatus.CANCELLED:
                    if self.verbose:
                        print("Conversation cancelled")
                    break

                # Check for pause
                while self.status == WorkflowStatus.PAUSED:
                    await asyncio.sleep(0.1)

                # Get assistant response
                response = await self._get_agent_response(context)

                # Add to history
                self.conversation_history.append(
                    Message(role='assistant', content=response)
                )

                if self.verbose:
                    print(f"Assistant: {response[:200]}...")

                # Check if conversation is complete
                if self._is_conversation_complete():
                    if self.verbose:
                        print("\nConversation complete")
                    break

                # Get next user input
                user_input = await self._get_user_input(goal, context)

                if not user_input:
                    # No more input
                    break

                # Add user input to history
                self.conversation_history.append(
                    Message(role='user', content=user_input)
                )

                if self.verbose:
                    print(f"User: {user_input[:200]}...")

            # Prepare result
            result = {
                'success': True,
                'goal': goal,
                'total_rounds': len([m for m in self.conversation_history if m.role == 'user']),
                'conversation': [msg.dict() for msg in self.conversation_history],
                'completed': self._is_conversation_complete()
            }

            self.status = WorkflowStatus.COMPLETED
            self.updated_at = datetime.now()

            if self.verbose:
                print(f"\nConversation complete:")
                print(f"  - Total rounds: {result['total_rounds']}")
                print(f"  - Messages: {len(self.conversation_history)}")

            return result

        except Exception as e:
            self.status = WorkflowStatus.FAILED
            self.updated_at = datetime.now()

            error_result = {
                'success': False,
                'error': str(e),
                'goal': goal,
                'conversation': [msg.dict() for msg in self.conversation_history]
            }

            if self.verbose:
                print(f"Workflow failed: {e}")

            return error_result

    async def _get_agent_response(
        self,
        context: Optional[Dict[str, Any]]
    ) -> str:
        """
        Get agent response for current conversation

        Args:
            context: Optional context

        Returns:
            Agent response
        """
        # Format conversation history for agent
        conversation_text = self._format_conversation()

        # Call agent
        if self.agent and hasattr(self.agent, 'run'):
            response = await self.agent.run(
                conversation_text,
                context=context
            )
            return response.get('response', str(response))
        else:
            # Fallback
            return "I'm sorry, I don't have an agent to respond."

    def _format_conversation(self) -> str:
        """
        Format conversation history for agent

        Returns:
            Formatted conversation
        """
        lines = []
        for msg in self.conversation_history:
            if msg.role == 'system':
                lines.append(f"[System]: {msg.content}")
            elif msg.role == 'user':
                lines.append(f"[User]: {msg.content}")
            elif msg.role == 'assistant':
                lines.append(f"[Assistant]: {msg.content}")

        return '\n'.join(lines)

    async def _get_user_input(
        self,
        goal: str,
        context: Optional[Dict[str, Any]]
    ) -> Optional[str]:
        """
        Get next user input

        Args:
            goal: Original goal
            context: Optional context

        Returns:
            User input or None if no more input
        """
        if self.input_handler:
            # Use custom input handler
            if asyncio.iscoroutinefunction(self.input_handler):
                return await self.input_handler(self.conversation_history)
            else:
                return self.input_handler(self.conversation_history)
        else:
            # Default: return None (end conversation)
            return None

    def _is_conversation_complete(self) -> bool:
        """
        Check if conversation is complete

        Returns:
            True if complete
        """
        if self.completion_checker:
            # Use custom completion checker
            return self.completion_checker(self.conversation_history)
        else:
            # Default: check last assistant message for completion signals
            if self.conversation_history:
                last_msg = self.conversation_history[-1]
                if last_msg.role == 'assistant':
                    content_lower = last_msg.content.lower()
                    completion_signals = [
                        'is there anything else',
                        'anything else i can help',
                        'let me know if you need',
                        'conversation complete'
                    ]
                    return any(signal in content_lower for signal in completion_signals)
            return False

    def set_system_prompt(self, prompt: str):
        """
        Set system prompt for the conversation

        Args:
            prompt: System prompt
        """
        self.system_prompt = prompt

    def set_input_handler(self, handler: Callable):
        """
        Set custom input handler

        Args:
            handler: Input handler function
        """
        self.input_handler = handler

    def set_output_handler(self, handler: Callable):
        """
        Set custom output handler

        Args:
            handler: Output handler function
        """
        self.output_handler = handler

    def set_completion_checker(self, checker: Callable):
        """
        Set custom completion checker

        Args:
            checker: Completion checker function
        """
        self.completion_checker = checker

    def get_conversation_summary(self) -> Dict[str, Any]:
        """
        Get summary of conversation

        Returns:
            Conversation summary
        """
        return {
            'total_messages': len(self.conversation_history),
            'user_messages': len([m for m in self.conversation_history if m.role == 'user']),
            'assistant_messages': len([m for m in self.conversation_history if m.role == 'assistant']),
            'system_messages': len([m for m in self.conversation_history if m.role == 'system']),
            'history': [msg.dict() for msg in self.conversation_history]
        }

    async def validate(self, goal: str) -> bool:
        """
        Validate interactive workflow

        Args:
            goal: Goal to validate

        Returns:
            True if valid
        """
        # Interactive workflow can handle any goal
        return len(goal.strip()) > 0
