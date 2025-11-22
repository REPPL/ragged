"""Graceful degradation utilities for fault tolerance.

v0.2.9: Fallback strategies to maintain >99% service availability.
"""

from collections.abc import Callable
from functools import wraps
from typing import Any, TypeVar

from src.utils.logging import get_logger

logger = get_logger(__name__)

T = TypeVar('T')


class ServiceUnavailableError(Exception):
    """Raised when all fallback options are exhausted."""
    pass


class FallbackStrategy:
    """Fallback strategy configuration.

    Defines a sequence of fallback options to try when primary method fails.

    Example:
        >>> strategy = FallbackStrategy(
        ...     primary=lambda: hybrid_search(query),
        ...     fallbacks=[
        ...         lambda: dense_search(query),
        ...         lambda: cached_search(query),
        ...     ],
        ...     name="search"
        ... )
        >>> result = strategy.execute()
    """

    def __init__(
        self,
        primary: Callable[[], T],
        fallbacks: list[Callable[[], T]],
        name: str = "operation"
    ):
        """Initialize fallback strategy.

        Args:
            primary: Primary method to attempt first
            fallbacks: List of fallback methods in order of preference
            name: Operation name for logging
        """
        self.primary = primary
        self.fallbacks = fallbacks
        self.name = name

    def execute(self) -> T:
        """Execute strategy with fallbacks.

        Returns:
            Result from primary or first successful fallback

        Raises:
            ServiceUnavailableError: If all methods fail
        """
        # Try primary first
        try:
            logger.debug(f"Attempting primary {self.name}")
            result = self.primary()
            logger.debug(f"Primary {self.name} succeeded")
            return result
        except Exception as e:
            logger.warning(
                f"Primary {self.name} failed: {e.__class__.__name__}: {str(e)}",
                exc_info=False
            )

        # Try fallbacks in order
        for i, fallback in enumerate(self.fallbacks, 1):
            try:
                logger.info(f"Attempting fallback {i}/{len(self.fallbacks)} for {self.name}")
                result = fallback()
                logger.info(f"Fallback {i} for {self.name} succeeded")
                return result
            except Exception as e:
                logger.warning(
                    f"Fallback {i} for {self.name} failed: {e.__class__.__name__}: {str(e)}",
                    exc_info=False
                )
                continue

        # All methods failed
        error_msg = f"All {self.name} methods failed (1 primary + {len(self.fallbacks)} fallbacks)"
        logger.error(error_msg)
        raise ServiceUnavailableError(error_msg)


def with_fallback(
    fallback_func: Callable | None = None,
    fallback_value: Any = None,
    exceptions: tuple = (Exception,),
    log_level: str = "warning"
):
    """Decorator to add fallback behavior to functions.

    Args:
        fallback_func: Function to call on failure (receives same args)
        fallback_value: Static value to return on failure
        exceptions: Tuple of exception types to catch
        log_level: Logging level for failures ("debug", "info", "warning", "error")

    Example:
        >>> @with_fallback(fallback_value=[], exceptions=(ValueError,))
        ... def get_items():
        ...     raise ValueError("Failed")
        ...     return [1, 2, 3]
        >>> result = get_items()  # Returns [] instead of raising
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except exceptions as e:
                log_func = getattr(logger, log_level, logger.warning)
                log_func(
                    f"{func.__name__} failed ({e.__class__.__name__}: {str(e)}), using fallback",
                    exc_info=False
                )

                # Use fallback function if provided
                if fallback_func is not None:
                    try:
                        return fallback_func(*args, **kwargs)
                    except Exception as fallback_error:
                        logger.error(
                            f"Fallback for {func.__name__} also failed: {fallback_error}",
                            exc_info=True
                        )
                        raise

                # Otherwise return fallback value
                return fallback_value

        return wrapper
    return decorator


class DegradedMode:
    """Context manager for degraded mode operation.

    Temporarily enables degraded mode (e.g., reduced features, lower quality)
    to maintain service availability.

    Example:
        >>> with DegradedMode("high_memory"):
        ...     # Operate with reduced memory footprint
        ...     process_with_smaller_batches()
    """

    _active_modes: set = set()

    def __init__(self, mode: str, reason: str = ""):
        """Initialize degraded mode.

        Args:
            mode: Degraded mode identifier
            reason: Optional reason for degradation
        """
        self.mode = mode
        self.reason = reason

    def __enter__(self):
        """Enter degraded mode."""
        if self.mode not in self._active_modes:
            logger.warning(
                f"Entering degraded mode: {self.mode}" +
                (f" (reason: {self.reason})" if self.reason else "")
            )
            self._active_modes.add(self.mode)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit degraded mode."""
        if self.mode in self._active_modes:
            logger.info(f"Exiting degraded mode: {self.mode}")
            self._active_modes.discard(self.mode)

    @classmethod
    def is_active(cls, mode: str) -> bool:
        """Check if a degraded mode is currently active.

        Args:
            mode: Mode identifier to check

        Returns:
            True if mode is active
        """
        return mode in cls._active_modes

    @classmethod
    def get_active_modes(cls) -> list[str]:
        """Get list of currently active degraded modes.

        Returns:
            List of active mode identifiers
        """
        return list(cls._active_modes)


def safe_execute(
    func: Callable[[], T],
    default: T,
    operation_name: str = "operation",
    log_failure: bool = True
) -> T:
    """Safely execute function with default fallback.

    Args:
        func: Function to execute
        default: Default value to return on failure
        operation_name: Name for logging
        log_failure: Whether to log failures

    Returns:
        Function result or default value

    Example:
        >>> result = safe_execute(
        ...     lambda: risky_operation(),
        ...     default=[],
        ...     operation_name="data_fetch"
        ... )
    """
    try:
        return func()
    except Exception as e:
        if log_failure:
            logger.warning(
                f"{operation_name} failed: {e.__class__.__name__}: {str(e)}. "
                f"Using default value.",
                exc_info=False
            )
        return default


class FallbackChain:
    """Chain of fallback operations with automatic retry.

    Attempts multiple strategies in sequence until one succeeds.

    Example:
        >>> chain = FallbackChain("data_retrieval")
        >>> chain.add(lambda: fetch_from_database())
        >>> chain.add(lambda: fetch_from_cache())
        >>> chain.add(lambda: fetch_from_backup())
        >>> result = chain.execute()
    """

    def __init__(self, name: str = "operation"):
        """Initialize fallback chain.

        Args:
            name: Chain name for logging
        """
        self.name = name
        self.strategies: list[Callable] = []
        self.strategy_names: list[str] = []

    def add(
        self,
        func: Callable,
        name: str | None = None,
        exceptions: tuple = (Exception,)
    ) -> 'FallbackChain':
        """Add a fallback strategy to the chain.

        Args:
            func: Strategy function to execute
            name: Optional name for this strategy
            exceptions: Exceptions to catch and continue

        Returns:
            Self for chaining
        """
        self.strategies.append((func, exceptions))
        self.strategy_names.append(name or f"strategy_{len(self.strategies)}")
        return self

    def execute(self, *args, **kwargs) -> Any:
        """Execute fallback chain.

        Args:
            *args: Arguments to pass to all strategies
            **kwargs: Keyword arguments to pass to all strategies

        Returns:
            Result from first successful strategy

        Raises:
            ServiceUnavailableError: If all strategies fail
        """
        errors = []

        for i, (func, exceptions) in enumerate(self.strategies):
            strategy_name = self.strategy_names[i]

            try:
                logger.debug(
                    f"Trying {self.name} strategy {i+1}/{len(self.strategies)}: {strategy_name}"
                )
                result = func(*args, **kwargs)
                if i > 0:  # Only log if not first attempt
                    logger.info(f"{self.name} succeeded with fallback: {strategy_name}")
                return result

            except exceptions as e:
                error_msg = f"{strategy_name} failed: {e.__class__.__name__}: {str(e)}"
                errors.append(error_msg)
                logger.warning(error_msg, exc_info=False)
                continue

        # All strategies failed
        error_summary = f"All {self.name} strategies failed:\n" + "\n".join(
            f"  {i+1}. {err}" for i, err in enumerate(errors)
        )
        logger.error(error_summary)
        raise ServiceUnavailableError(error_summary)


def adaptive_batch_size(
    current_size: int,
    success: bool,
    min_size: int = 1,
    max_size: int = 1000,
    increase_factor: float = 1.5,
    decrease_factor: float = 0.5
) -> int:
    """Adaptively adjust batch size based on success/failure.

    Increases batch size on success, decreases on failure to handle
    resource constraints gracefully.

    Args:
        current_size: Current batch size
        success: Whether last operation succeeded
        min_size: Minimum allowed batch size
        max_size: Maximum allowed batch size
        increase_factor: Factor to multiply on success
        decrease_factor: Factor to multiply on failure

    Returns:
        Adjusted batch size

    Example:
        >>> size = 100
        >>> size = adaptive_batch_size(size, success=False)  # Reduces to 50
        >>> size = adaptive_batch_size(size, success=True)   # Increases to 75
    """
    if success:
        # Increase batch size
        new_size = int(current_size * increase_factor)
        new_size = min(new_size, max_size)
        if new_size > current_size:
            logger.debug(f"Increasing batch size: {current_size} → {new_size}")
    else:
        # Decrease batch size
        new_size = int(current_size * decrease_factor)
        new_size = max(new_size, min_size)
        if new_size < current_size:
            logger.info(f"Reducing batch size due to failure: {current_size} → {new_size}")

    return new_size


class CircuitBreaker:
    """Simple circuit breaker for degraded services.

    Prevents repeated calls to failing services to allow recovery.

    States:
    - CLOSED: Normal operation
    - OPEN: Service failing, reject calls
    - HALF_OPEN: Testing if service recovered

    Example:
        >>> breaker = CircuitBreaker("external_api", failure_threshold=3)
        >>> if not breaker.is_open():
        ...     result = call_external_api()
        ...     breaker.record_success()
    """

    def __init__(
        self,
        name: str,
        failure_threshold: int = 5,
        recovery_timeout: float = 60.0
    ):
        """Initialize circuit breaker.

        Args:
            name: Service name
            failure_threshold: Failures before opening circuit
            recovery_timeout: Seconds before attempting recovery
        """
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time: float | None = None
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN

    def is_open(self) -> bool:
        """Check if circuit is open (service unavailable).

        Returns:
            True if circuit is open
        """
        if self.state == "OPEN":
            # Check if recovery timeout elapsed
            import time
            if self.last_failure_time and \
               (time.time() - self.last_failure_time) >= self.recovery_timeout:
                logger.info(f"Circuit breaker {self.name}: attempting recovery (HALF_OPEN)")
                self.state = "HALF_OPEN"
                return False
            return True
        return False

    def record_success(self):
        """Record successful operation."""
        if self.state == "HALF_OPEN":
            logger.info(f"Circuit breaker {self.name}: service recovered (CLOSED)")
            self.state = "CLOSED"
        self.failure_count = 0

    def record_failure(self):
        """Record failed operation."""
        import time
        self.failure_count += 1
        self.last_failure_time = time.time()

        if self.failure_count >= self.failure_threshold:
            if self.state != "OPEN":
                logger.error(
                    f"Circuit breaker {self.name}: threshold reached, opening circuit "
                    f"({self.failure_count} failures)"
                )
                self.state = "OPEN"
