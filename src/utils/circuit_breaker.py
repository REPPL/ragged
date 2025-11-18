"""Circuit breaker pattern for preventing cascade failures.

v0.2.9: Implements circuit breaker to protect services from repeated failures.
"""

import enum
import functools
import threading
import time
from collections import deque
from typing import Callable, Deque, Optional

from src.exceptions import RaggedError
from src.utils.logging import get_logger

logger = get_logger(__name__)


class CircuitState(enum.Enum):
    """Circuit breaker states."""

    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Failing, rejecting requests
    HALF_OPEN = "half_open"  # Testing if service recovered


class CircuitBreakerOpenError(RaggedError):
    """
    Raised when circuit breaker is open and rejecting requests.

    v0.2.9: Indicates service is temporarily unavailable due to repeated failures.
    """

    def __init__(self, service: str, failure_count: int, reset_timeout: float):
        """
        Initialize circuit breaker error.

        Args:
            service: Name of protected service
            failure_count: Number of failures that opened circuit
            reset_timeout: Seconds until circuit tries to recover
        """
        super().__init__(
            f"Circuit breaker OPEN for '{service}' "
            f"(failures={failure_count}, retry_in={reset_timeout:.1f}s)",
            {
                "service": service,
                "failure_count": failure_count,
                "reset_timeout": reset_timeout,
            },
        )


class CircuitBreaker:
    """
    Circuit breaker for protecting services from cascade failures.

    v0.2.9: Automatically opens circuit after threshold failures, preventing
    further damage. Periodically tests recovery with half-open state.

    States:
    - CLOSED: Normal operation, requests pass through
    - OPEN: Service failing, requests rejected immediately
    - HALF_OPEN: Testing recovery, limited requests allowed

    Example:
        >>> breaker = CircuitBreaker(name="vector_store", failure_threshold=5)
        >>> @breaker.protect
        ... def query_vector_store(query):
        ...     return vector_store.query(query)
        >>>
        >>> result = query_vector_store("test")  # Automatic circuit protection
    """

    def __init__(
        self,
        name: str = "service",
        failure_threshold: int = 5,
        recovery_timeout: float = 60.0,
        half_open_max_calls: int = 3,
        success_threshold: int = 2,
    ):
        """
        Initialize circuit breaker.

        Args:
            name: Service name for logging
            failure_threshold: Failures before opening circuit
            recovery_timeout: Seconds to wait before trying half-open
            half_open_max_calls: Max calls allowed in half-open state
            success_threshold: Successes needed to close from half-open
        """
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.half_open_max_calls = half_open_max_calls
        self.success_threshold = success_threshold

        # State tracking
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._success_count = 0
        self._last_failure_time: Optional[float] = None
        self._half_open_calls = 0

        # Thread safety
        self._lock = threading.Lock()

        # Recent failures for debugging
        self._recent_failures: Deque[str] = deque(maxlen=10)

        logger.info(
            f"CircuitBreaker '{name}' initialized "
            f"(threshold={failure_threshold}, timeout={recovery_timeout}s)"
        )

    @property
    def state(self) -> CircuitState:
        """Get current circuit state."""
        return self._state

    @property
    def is_closed(self) -> bool:
        """Check if circuit is closed (normal operation)."""
        return self._state == CircuitState.CLOSED

    @property
    def is_open(self) -> bool:
        """Check if circuit is open (rejecting requests)."""
        return self._state == CircuitState.OPEN

    @property
    def is_half_open(self) -> bool:
        """Check if circuit is half-open (testing recovery)."""
        return self._state == CircuitState.HALF_OPEN

    def _transition_to_open(self) -> None:
        """Transition to OPEN state (rejecting requests)."""
        self._state = CircuitState.OPEN
        self._last_failure_time = time.time()
        self._half_open_calls = 0
        logger.warning(
            f"CircuitBreaker '{self.name}' OPENED "
            f"(failures={self._failure_count}/{self.failure_threshold})"
        )

    def _transition_to_half_open(self) -> None:
        """Transition to HALF_OPEN state (testing recovery)."""
        self._state = CircuitState.HALF_OPEN
        self._success_count = 0
        self._half_open_calls = 0
        logger.info(f"CircuitBreaker '{self.name}' HALF_OPEN (testing recovery)")

    def _transition_to_closed(self) -> None:
        """Transition to CLOSED state (normal operation)."""
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._success_count = 0
        self._recent_failures.clear()
        logger.info(
            f"CircuitBreaker '{self.name}' CLOSED (service recovered)"
        )

    def _record_success(self) -> None:
        """Record a successful call."""
        with self._lock:
            if self._state == CircuitState.HALF_OPEN:
                self._success_count += 1
                logger.debug(
                    f"CircuitBreaker '{self.name}': Success "
                    f"{self._success_count}/{self.success_threshold} in HALF_OPEN"
                )

                # Enough successes to close circuit
                if self._success_count >= self.success_threshold:
                    self._transition_to_closed()
            elif self._state == CircuitState.CLOSED:
                # Reset failure count on success
                self._failure_count = 0

    def _record_failure(self, exception: Exception) -> None:
        """Record a failed call."""
        with self._lock:
            failure_message = f"{type(exception).__name__}: {str(exception)[:100]}"
            self._recent_failures.append(failure_message)

            if self._state == CircuitState.HALF_OPEN:
                # Failure in half-open immediately reopens circuit
                self._transition_to_open()
            elif self._state == CircuitState.CLOSED:
                self._failure_count += 1
                logger.debug(
                    f"CircuitBreaker '{self.name}': Failure "
                    f"{self._failure_count}/{self.failure_threshold}"
                )

                # Open circuit if threshold reached
                if self._failure_count >= self.failure_threshold:
                    self._transition_to_open()

    def _check_recovery(self) -> None:
        """Check if circuit should transition from OPEN to HALF_OPEN."""
        with self._lock:
            if self._state == CircuitState.OPEN and self._last_failure_time:
                elapsed = time.time() - self._last_failure_time
                if elapsed >= self.recovery_timeout:
                    self._transition_to_half_open()

    def call(self, func: Callable, *args, **kwargs):
        """
        Execute function with circuit breaker protection.

        Args:
            func: Function to call
            *args: Positional arguments for func
            **kwargs: Keyword arguments for func

        Returns:
            Result from func

        Raises:
            CircuitBreakerOpenError: If circuit is open
            Exception: Any exception from func

        Example:
            >>> breaker = CircuitBreaker(name="api")
            >>> result = breaker.call(api_request, "GET", "/users")
        """
        # Check if we should try recovery
        if self._state == CircuitState.OPEN:
            self._check_recovery()

        # Reject if still open
        if self._state == CircuitState.OPEN:
            raise CircuitBreakerOpenError(
                service=self.name,
                failure_count=self._failure_count,
                reset_timeout=self.recovery_timeout,
            )

        # Limit calls in half-open state
        if self._state == CircuitState.HALF_OPEN:
            with self._lock:
                if self._half_open_calls >= self.half_open_max_calls:
                    raise CircuitBreakerOpenError(
                        service=self.name,
                        failure_count=self._failure_count,
                        reset_timeout=0.0,  # Already in half-open
                    )
                self._half_open_calls += 1

        # Execute function
        try:
            result = func(*args, **kwargs)
            self._record_success()
            return result
        except Exception as e:
            self._record_failure(e)
            raise

    def protect(self, func: Callable) -> Callable:
        """
        Decorator to protect a function with circuit breaker.

        v0.2.9: Automatically wraps function calls with circuit protection.

        Args:
            func: Function to protect

        Returns:
            Protected function

        Example:
            >>> breaker = CircuitBreaker(name="database")
            >>> @breaker.protect
            ... def query_database(query):
            ...     return db.execute(query)
        """

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            return self.call(func, *args, **kwargs)

        return wrapper

    def get_stats(self) -> dict:
        """
        Get circuit breaker statistics.

        Returns:
            Dictionary with current stats

        Example:
            >>> breaker = CircuitBreaker(name="service")
            >>> stats = breaker.get_stats()
            >>> print(f"State: {stats['state']}, Failures: {stats['failure_count']}")
        """
        with self._lock:
            return {
                "name": self.name,
                "state": self._state.value,
                "failure_count": self._failure_count,
                "failure_threshold": self.failure_threshold,
                "success_count": self._success_count,
                "recent_failures": list(self._recent_failures),
                "half_open_calls": self._half_open_calls,
                "last_failure_time": self._last_failure_time,
            }

    def reset(self) -> None:
        """
        Manually reset circuit breaker to CLOSED state.

        v0.2.9: Use with caution - only when you know service recovered.

        Example:
            >>> breaker.reset()  # Manually close circuit
        """
        with self._lock:
            self._transition_to_closed()
            logger.info(f"CircuitBreaker '{self.name}' manually reset")
