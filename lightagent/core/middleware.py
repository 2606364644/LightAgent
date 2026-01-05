"""
Middleware system for pre/post processing
"""
from typing import Any, Dict, Callable, List, Optional
from pydantic import BaseModel, Field
from enum import Enum
import asyncio
import logging

logger = logging.getLogger(__name__)


class MiddlewarePhase(str, Enum):
    """Middleware execution phases"""
    PRE_MODEL_CALL = "pre_model_call"
    POST_MODEL_CALL = "post_model_call"
    PRE_TOOL_EXECUTION = "pre_tool_execution"
    POST_TOOL_EXECUTION = "post_tool_execution"
    PRE_RESPONSE = "pre_response"
    POST_RESPONSE = "post_response"


class MiddlewareContext(BaseModel):
    """Context passed through middleware pipeline"""
    agent: Any = None
    message: str
    phase: MiddlewarePhase
    metadata: Dict[str, Any] = Field(default_factory=dict)
    should_continue: bool = True
    modified_message: Optional[str] = None
    response_data: Optional[Dict[str, Any]] = None


class BaseMiddleware:
    """Base class for middleware components"""

    name: str = "base_middleware"

    async def process_pre(self, context: MiddlewareContext) -> MiddlewareContext:
        """Process before model call"""
        return context

    async def process_post(self, context: MiddlewareContext) -> MiddlewareContext:
        """Process after model call"""
        return context


class LoggingMiddleware(BaseMiddleware):
    """Log all agent interactions"""

    name = "logging_middleware"

    async def process_pre(self, context: MiddlewareContext) -> MiddlewareContext:
        logger.info(f"[PRE] Agent: {context.agent.config.name if context.agent else 'Unknown'}")
        logger.info(f"[PRE] Message: {context.message[:100]}...")
        return context

    async def process_post(self, context: MiddlewareContext) -> MiddlewareContext:
        logger.info(f"[POST] Response: {str(context.response_data)[:100]}...")
        return context


class RateLimitMiddleware(BaseMiddleware):
    """Rate limiting for agent calls"""

    name = "rate_limit_middleware"

    def __init__(self, calls_per_minute: int = 60):
        self.calls_per_minute = calls_per_minute
        self.call_times: List[float] = []

    async def process_pre(self, context: MiddlewareContext) -> MiddlewareContext:
        import time
        current_time = time.time()

        # Remove old calls
        self.call_times = [
            t for t in self.call_times
            if current_time - t < 60
        ]

        # Check rate limit
        if len(self.call_times) >= self.calls_per_minute:
            sleep_time = 60 - (current_time - self.call_times[0])
            if sleep_time > 0:
                await asyncio.sleep(sleep_time)

        self.call_times.append(current_time)
        return context


class CacheMiddleware(BaseMiddleware):
    """Cache responses for repeated queries"""

    name = "cache_middleware"

    def __init__(self, ttl_seconds: int = 300):
        self.ttl_seconds = ttl_seconds
        self.cache: Dict[str, tuple] = {}

    def _get_cache_key(self, message: str) -> str:
        """Generate cache key from message"""
        import hashlib
        return hashlib.md5(message.encode()).hexdigest()

    async def process_pre(self, context: MiddlewareContext) -> MiddlewareContext:
        import time
        cache_key = self._get_cache_key(context.message)

        if cache_key in self.cache:
            cached_time, cached_response = self.cache[cache_key]
            if time.time() - cached_time < self.ttl_seconds:
                context.response_data = cached_response
                context.metadata["from_cache"] = True
                context.should_continue = False

        return context

    async def process_post(self, context: MiddlewareContext) -> MiddlewareContext:
        import time
        if context.response_data and not context.metadata.get("from_cache"):
            cache_key = self._get_cache_key(context.message)
            self.cache[cache_key] = (time.time(), context.response_data)

        return context


class ValidationMiddleware(BaseMiddleware):
    """Validate input and output"""

    name = "validation_middleware"

    def __init__(self, max_length: int = 10000):
        self.max_length = max_length

    async def process_pre(self, context: MiddlewareContext) -> MiddlewareContext:
        if len(context.message) > self.max_length:
            raise ValueError(f"Message too long: {len(context.message)} > {self.max_length}")

        if not context.message.strip():
            raise ValueError("Empty message")

        return context

    async def process_post(self, context: MiddlewareContext) -> MiddlewareContext:
        if context.response_data:
            response_text = context.response_data.get("response", "")
            if len(response_text) > self.max_length * 2:
                context.response_data["response"] = response_text[:self.max_length * 2]

        return context


class RetryMiddleware(BaseMiddleware):
    """Retry failed model calls"""

    name = "retry_middleware"

    def __init__(self, max_retries: int = 3, backoff_factor: float = 1.5):
        self.max_retries = max_retries
        self.backoff_factor = backoff_factor

    async def process_post(self, context: MiddlewareContext) -> MiddlewareContext:
        if not context.response_data.get("success") and context.should_continue:
            retry_count = context.metadata.get("retry_count", 0)

            if retry_count < self.max_retries:
                import time
                wait_time = self.backoff_factor ** retry_count
                await asyncio.sleep(wait_time)

                context.metadata["retry_count"] = retry_count + 1
                # Mark for retry by setting should_continue to True
                # The agent will need to handle this logic

        return context


class MiddlewareManager(BaseModel):
    """Manages middleware pipeline"""

    pre_middlewares: List[Callable] = Field(default_factory=list)
    post_middlewares: List[Callable] = Field(default_factory=list)
    _agent: Any = None

    class Config:
        arbitrary_types_allowed = True

    async def initialize(self, agent: Any):
        """Initialize middleware with agent reference"""
        self._agent = agent

        # Initialize middleware if needed
        for middleware in self.pre_middlewares + self.post_middlewares:
            if hasattr(middleware, 'initialize'):
                await middleware.initialize(agent)

    def add(self, middleware: Callable, position: str = "after"):
        """Add middleware to pipeline

        Args:
            middleware: Middleware instance or callable
            position: 'before' or 'after' (insertion point)
        """
        if isinstance(middleware, BaseMiddleware):
            # Add to both pre and post
            if position == "before":
                self.pre_middlewares.insert(0, middleware)
            else:
                self.pre_middlewares.append(middleware)
                self.post_middlewares.append(middleware)
        else:
            # Add as custom middleware
            if position == "before":
                self.pre_middlewares.insert(0, middleware)
            else:
                self.post_middlewares.append(middleware)

    async def process_pre(self, agent: Any, message: str) -> str:
        """Process message through pre-middlewares"""
        context = MiddlewareContext(
            agent=agent,
            message=message,
            phase=MiddlewarePhase.PRE_MODEL_CALL
        )

        for middleware in self.pre_middlewares:
            try:
                if asyncio.iscoroutinefunction(middleware.process_pre):
                    context = await middleware.process_pre(context)
                else:
                    context = middleware.process_pre(context)

                # Check if processing should stop
                if not context.should_continue:
                    break

                # Update message if modified
                if context.modified_message:
                    context.message = context.modified_message

            except Exception as e:
                logger.error(f"Error in pre-middleware {middleware}: {e}")
                raise

        return context.message

    async def process_post(
        self,
        agent: Any,
        response_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Process response through post-middlewares"""
        context = MiddlewareContext(
            agent=agent,
            message="",
            phase=MiddlewarePhase.POST_MODEL_CALL,
            response_data=response_data
        )

        for middleware in self.post_middlewares:
            try:
                if asyncio.iscoroutinefunction(middleware.process_post):
                    context = await middleware.process_post(context)
                else:
                    context = middleware.process_post(context)

                # Update response data
                if context.response_data:
                    response_data = context.response_data

            except Exception as e:
                logger.error(f"Error in post-middleware {middleware}: {e}")
                # Continue processing even if one middleware fails

        return response_data
