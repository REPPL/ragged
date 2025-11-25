"""Agent error recovery and retry logic.

Provides robust error handling, retry mechanisms, and recovery
strategies for agent operations.
"""

import asyncio
import logging
import random
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from functools import wraps
from typing import Any, Callable, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")
F = TypeVar("F", bound=Callable[..., Any])


class RetryStrategy(Enum):
    """Retry strategy types."""

    IMMEDIATE = "immediate"
    LINEAR = "linear"
    EXPONENTIAL = "exponential"
    FIBONACCI = "fibonacci"


class ErrorCategory(Enum):
    """Categories of errors for handling decisions."""

    TRANSIENT = "transient"  # Temporary, worth retrying
    PERMANENT = "permanent"  # Won't succeed on retry
    RESOURCE = "resource"  # Resource exhaustion
    VALIDATION = "validation"  # Input validation failures
    TIMEOUT = "timeout"  # Timeout errors
    UNKNOWN = "unknown"  # Unclassified errors


@dataclass
class RetryConfig:
    """Configuration for retry behaviour.

    Attributes:
        max_attempts: Maximum number of retry attempts
        strategy: Backoff strategy
        base_delay: Base delay in seconds
        max_delay: Maximum delay between retries
        jitter: Add random jitter to delays
        retryable_exceptions: Exception types to retry
        retryable_categories: Error categories to retry
    """

    max_attempts: int = 3
    strategy: RetryStrategy = RetryStrategy.EXPONENTIAL
    base_delay: float = 1.0
    max_delay: float = 60.0
    jitter: bool = True
    retryable_exceptions: tuple[type[Exception], ...] = (
        TimeoutError,
        ConnectionError,
        asyncio.TimeoutError,
    )
    retryable_categories: tuple[ErrorCategory, ...] = (
        ErrorCategory.TRANSIENT,
        ErrorCategory.TIMEOUT,
        ErrorCategory.RESOURCE,
    )

    def calculate_delay(self, attempt: int) -> float:
        """Calculate delay for a given attempt number."""
        if self.strategy == RetryStrategy.IMMEDIATE:
            delay = 0.0
        elif self.strategy == RetryStrategy.LINEAR:
            delay = self.base_delay * attempt
        elif self.strategy == RetryStrategy.EXPONENTIAL:
            delay = self.base_delay * (2 ** (attempt - 1))
        elif self.strategy == RetryStrategy.FIBONACCI:
            delay = self.base_delay * self._fibonacci(attempt)
        else:
            delay = self.base_delay

        # Apply max delay cap
        delay = min(delay, self.max_delay)

        # Add jitter if enabled
        if self.jitter and delay > 0:
            delay = delay * (0.5 + random.random())

        return delay

    @staticmethod
    def _fibonacci(n: int) -> int:
        """Calculate nth Fibonacci number."""
        if n <= 1:
            return n
        a, b = 0, 1
        for _ in range(2, n + 1):
            a, b = b, a + b
        return b


@dataclass
class RetryState:
    """State tracking for retry operations.

    Attributes:
        attempt: Current attempt number
        total_attempts: Total attempts made
        last_error: Last error encountered
        last_delay: Last delay applied
        started_at: When retries started
        errors: List of all errors
    """

    attempt: int = 0
    total_attempts: int = 0
    last_error: Exception | None = None
    last_delay: float = 0.0
    started_at: datetime = field(default_factory=datetime.now)
    errors: list[tuple[datetime, Exception]] = field(default_factory=list)

    def record_error(self, error: Exception) -> None:
        """Record an error occurrence."""
        self.errors.append((datetime.now(), error))
        self.last_error = error
        self.total_attempts += 1

    @property
    def elapsed_time(self) -> float:
        """Get elapsed time since start."""
        return (datetime.now() - self.started_at).total_seconds()


class ErrorClassifier:
    """Classifies errors into categories for handling decisions."""

    # Default error classifications
    _classifications: dict[type[Exception], ErrorCategory] = {
        TimeoutError: ErrorCategory.TIMEOUT,
        asyncio.TimeoutError: ErrorCategory.TIMEOUT,
        ConnectionError: ErrorCategory.TRANSIENT,
        ConnectionRefusedError: ErrorCategory.TRANSIENT,
        ConnectionResetError: ErrorCategory.TRANSIENT,
        BrokenPipeError: ErrorCategory.TRANSIENT,
        MemoryError: ErrorCategory.RESOURCE,
        ValueError: ErrorCategory.VALIDATION,
        TypeError: ErrorCategory.VALIDATION,
        KeyError: ErrorCategory.VALIDATION,
        PermissionError: ErrorCategory.PERMANENT,
        FileNotFoundError: ErrorCategory.PERMANENT,
    }

    @classmethod
    def classify(cls, error: Exception) -> ErrorCategory:
        """Classify an exception into a category."""
        error_type = type(error)

        # Check direct match
        if error_type in cls._classifications:
            return cls._classifications[error_type]

        # Check parent classes
        for exc_type, category in cls._classifications.items():
            if isinstance(error, exc_type):
                return category

        # Check error message patterns
        message = str(error).lower()
        if any(word in message for word in ["timeout", "timed out"]):
            return ErrorCategory.TIMEOUT
        if any(word in message for word in ["connection", "network", "refused"]):
            return ErrorCategory.TRANSIENT
        if any(word in message for word in ["memory", "resource", "limit"]):
            return ErrorCategory.RESOURCE
        if any(word in message for word in ["invalid", "validation", "required"]):
            return ErrorCategory.VALIDATION

        return ErrorCategory.UNKNOWN

    @classmethod
    def is_retryable(
        cls,
        error: Exception,
        config: RetryConfig | None = None,
    ) -> bool:
        """Determine if an error is worth retrying."""
        if config is None:
            config = RetryConfig()

        # Check exception type
        if isinstance(error, config.retryable_exceptions):
            return True

        # Check error category
        category = cls.classify(error)
        return category in config.retryable_categories

    @classmethod
    def register(cls, exc_type: type[Exception], category: ErrorCategory) -> None:
        """Register a custom error classification."""
        cls._classifications[exc_type] = category


@dataclass
class RecoveryAction:
    """An action to take during error recovery.

    Attributes:
        name: Action identifier
        description: Human-readable description
        handler: Function to execute
        applicable_categories: Categories this action handles
    """

    name: str
    description: str
    handler: Callable[[Exception, dict[str, Any]], Any]
    applicable_categories: tuple[ErrorCategory, ...] = (ErrorCategory.UNKNOWN,)

    def applies_to(self, error: Exception) -> bool:
        """Check if this action applies to the error."""
        category = ErrorClassifier.classify(error)
        return category in self.applicable_categories


class RecoveryManager:
    """Manages error recovery strategies and actions."""

    def __init__(self) -> None:
        """Initialise recovery manager."""
        self._actions: list[RecoveryAction] = []
        self._fallbacks: dict[str, Callable[..., Any]] = {}

    def register_action(self, action: RecoveryAction) -> None:
        """Register a recovery action."""
        self._actions.append(action)

    def register_fallback(
        self,
        name: str,
        handler: Callable[..., Any],
    ) -> None:
        """Register a fallback handler."""
        self._fallbacks[name] = handler

    async def attempt_recovery(
        self,
        error: Exception,
        context: dict[str, Any],
    ) -> Any | None:
        """Attempt to recover from an error.

        Args:
            error: The error to recover from
            context: Execution context

        Returns:
            Recovery result or None if no recovery possible
        """
        for action in self._actions:
            if action.applies_to(error):
                try:
                    logger.info(f"Attempting recovery action: {action.name}")
                    result = action.handler(error, context)
                    if asyncio.iscoroutine(result):
                        result = await result
                    if result is not None:
                        logger.info(f"Recovery successful: {action.name}")
                        return result
                except Exception as recovery_error:
                    logger.warning(
                        f"Recovery action '{action.name}' failed: {recovery_error}"
                    )

        return None

    def get_fallback(self, name: str) -> Callable[..., Any] | None:
        """Get a fallback handler by name."""
        return self._fallbacks.get(name)


class RetryExecutor:
    """Executes operations with retry logic."""

    def __init__(
        self,
        config: RetryConfig | None = None,
        recovery_manager: RecoveryManager | None = None,
    ) -> None:
        """Initialise retry executor.

        Args:
            config: Retry configuration
            recovery_manager: Optional recovery manager
        """
        self.config = config or RetryConfig()
        self.recovery = recovery_manager

    async def execute(
        self,
        operation: Callable[..., Any],
        *args: Any,
        **kwargs: Any,
    ) -> Any:
        """Execute an operation with retries.

        Args:
            operation: The operation to execute
            *args: Positional arguments
            **kwargs: Keyword arguments

        Returns:
            Operation result

        Raises:
            Exception: Last error if all retries exhausted
        """
        state = RetryState()

        while state.attempt < self.config.max_attempts:
            state.attempt += 1

            try:
                result = operation(*args, **kwargs)
                if asyncio.iscoroutine(result):
                    result = await result
                return result

            except Exception as error:
                state.record_error(error)
                logger.warning(
                    f"Attempt {state.attempt}/{self.config.max_attempts} failed: {error}"
                )

                # Check if retryable
                if not ErrorClassifier.is_retryable(error, self.config):
                    logger.error(f"Error not retryable: {type(error).__name__}")
                    raise

                # Attempt recovery
                if self.recovery is not None:
                    context = {"args": args, "kwargs": kwargs, "state": state}
                    recovery_result = await self.recovery.attempt_recovery(
                        error, context
                    )
                    if recovery_result is not None:
                        return recovery_result

                # Check if more attempts remain
                if state.attempt >= self.config.max_attempts:
                    logger.error(f"All {self.config.max_attempts} attempts exhausted")
                    raise

                # Calculate and apply delay
                delay = self.config.calculate_delay(state.attempt)
                state.last_delay = delay
                if delay > 0:
                    logger.info(f"Waiting {delay:.2f}s before retry...")
                    await asyncio.sleep(delay)

        # Should not reach here, but just in case
        if state.last_error is not None:
            raise state.last_error
        raise RuntimeError("Retry logic error - no result or error")


def with_retry(
    config: RetryConfig | None = None,
    on_retry: Callable[[int, Exception], None] | None = None,
) -> Callable[[F], F]:
    """Decorator for adding retry logic to async functions.

    Args:
        config: Retry configuration
        on_retry: Callback invoked on each retry

    Example:
        @with_retry(RetryConfig(max_attempts=5))
        async def fetch_data():
            ...
    """
    if config is None:
        config = RetryConfig()

    def decorator(func: F) -> F:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            executor = RetryExecutor(config)
            state = RetryState()

            while state.attempt < config.max_attempts:
                state.attempt += 1

                try:
                    return await func(*args, **kwargs)

                except Exception as error:
                    state.record_error(error)

                    if not ErrorClassifier.is_retryable(error, config):
                        raise

                    if state.attempt >= config.max_attempts:
                        raise

                    if on_retry is not None:
                        on_retry(state.attempt, error)

                    delay = config.calculate_delay(state.attempt)
                    if delay > 0:
                        await asyncio.sleep(delay)

            if state.last_error is not None:
                raise state.last_error
            raise RuntimeError("Retry logic error")

        return wrapper  # type: ignore

    return decorator


# Pre-configured retry configurations
class RetryConfigs:
    """Pre-configured retry settings for common scenarios."""

    # Quick retries for fast operations
    FAST = RetryConfig(
        max_attempts=3,
        strategy=RetryStrategy.IMMEDIATE,
        base_delay=0.1,
        max_delay=1.0,
    )

    # Standard retries with exponential backoff
    STANDARD = RetryConfig(
        max_attempts=3,
        strategy=RetryStrategy.EXPONENTIAL,
        base_delay=1.0,
        max_delay=30.0,
    )

    # Patient retries for external services
    PATIENT = RetryConfig(
        max_attempts=5,
        strategy=RetryStrategy.EXPONENTIAL,
        base_delay=2.0,
        max_delay=60.0,
        jitter=True,
    )

    # Aggressive retries for critical operations
    AGGRESSIVE = RetryConfig(
        max_attempts=10,
        strategy=RetryStrategy.FIBONACCI,
        base_delay=0.5,
        max_delay=120.0,
        jitter=True,
    )


class CircuitBreaker:
    """Circuit breaker pattern for preventing cascade failures.

    States:
    - CLOSED: Normal operation, requests pass through
    - OPEN: Failing, requests are rejected
    - HALF_OPEN: Testing if service recovered
    """

    class State(Enum):
        CLOSED = "closed"
        OPEN = "open"
        HALF_OPEN = "half_open"

    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: float = 30.0,
        half_open_requests: int = 3,
    ) -> None:
        """Initialise circuit breaker.

        Args:
            failure_threshold: Failures before opening
            recovery_timeout: Seconds before trying half-open
            half_open_requests: Requests to try in half-open state
        """
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.half_open_requests = half_open_requests

        self._state = self.State.CLOSED
        self._failure_count = 0
        self._success_count = 0
        self._last_failure_time: datetime | None = None

    @property
    def state(self) -> State:
        """Get current circuit state."""
        if self._state == self.State.OPEN:
            # Check if recovery timeout has passed
            if self._last_failure_time is not None:
                elapsed = (datetime.now() - self._last_failure_time).total_seconds()
                if elapsed >= self.recovery_timeout:
                    self._state = self.State.HALF_OPEN
                    self._success_count = 0

        return self._state

    def allow_request(self) -> bool:
        """Check if a request should be allowed."""
        state = self.state
        if state == self.State.CLOSED:
            return True
        if state == self.State.HALF_OPEN:
            return self._success_count < self.half_open_requests
        return False

    def record_success(self) -> None:
        """Record a successful request."""
        if self._state == self.State.HALF_OPEN:
            self._success_count += 1
            if self._success_count >= self.half_open_requests:
                self._state = self.State.CLOSED
                self._failure_count = 0
        else:
            self._failure_count = 0

    def record_failure(self) -> None:
        """Record a failed request."""
        self._failure_count += 1
        self._last_failure_time = datetime.now()

        if self._state == self.State.HALF_OPEN:
            self._state = self.State.OPEN
        elif self._failure_count >= self.failure_threshold:
            self._state = self.State.OPEN

    def reset(self) -> None:
        """Reset the circuit breaker."""
        self._state = self.State.CLOSED
        self._failure_count = 0
        self._success_count = 0
        self._last_failure_time = None

    async def execute(
        self,
        operation: Callable[..., Any],
        *args: Any,
        **kwargs: Any,
    ) -> Any:
        """Execute operation with circuit breaker protection."""
        if not self.allow_request():
            raise RuntimeError(
                f"Circuit breaker is {self._state.value} - request rejected"
            )

        try:
            result = operation(*args, **kwargs)
            if asyncio.iscoroutine(result):
                result = await result
            self.record_success()
            return result
        except Exception as error:
            self.record_failure()
            raise
