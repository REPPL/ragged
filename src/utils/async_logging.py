"""Performance-aware async logging system.

v0.2.9: Non-blocking logging with sampling for high-frequency events.
"""

import logging
import threading
import time
from logging.handlers import QueueHandler, QueueListener, RotatingFileHandler
from queue import Queue, Full
from typing import List, Optional, Dict
from collections import defaultdict

from src.utils.logging import get_logger

logger = get_logger(__name__)


class SamplingFilter(logging.Filter):
    """Sample high-frequency logs to reduce overhead.

    Features:
    - Always logs WARNING+ (never samples errors/warnings)
    - Samples INFO/DEBUG based on configurable rate
    - Per-logger sampling (different loggers can have different rates)
    - Thread-safe counter

    Example:
        >>> filter = SamplingFilter(sample_rate=100)
        >>> handler.addFilter(filter)  # Logs 1 in 100 INFO/DEBUG messages
    """

    def __init__(self, sample_rate: int = 100):
        """Initialize sampling filter.

        Args:
            sample_rate: Log 1 in N events for INFO/DEBUG (default: 100)
        """
        super().__init__()
        self.sample_rate = sample_rate
        self.counter = 0
        self._lock = threading.Lock()

    def filter(self, record: logging.LogRecord) -> bool:
        """Filter log records based on level and sampling rate.

        Args:
            record: Log record to filter

        Returns:
            True if record should be logged, False otherwise
        """
        # Always log WARNING+ (errors/warnings never sampled)
        if record.levelno >= logging.WARNING:
            return True

        # Sample INFO/DEBUG
        with self._lock:
            self.counter += 1
            should_log = (self.counter % self.sample_rate) == 0

        return should_log


class AdaptiveSamplingFilter(logging.Filter):
    """Adaptive sampling that adjusts rate based on log volume.

    Features:
    - Increases sampling rate under high load
    - Decreases sampling rate when load is low
    - Per-logger tracking
    - Window-based rate calculation

    Example:
        >>> filter = AdaptiveSamplingFilter(
        ...     target_logs_per_second=100,
        ...     window_seconds=10
        ... )
    """

    def __init__(
        self,
        target_logs_per_second: int = 100,
        window_seconds: int = 10,
        min_sample_rate: int = 1,
        max_sample_rate: int = 1000,
    ):
        """Initialize adaptive sampling filter.

        Args:
            target_logs_per_second: Target maximum logs per second
            window_seconds: Window size for rate calculation
            min_sample_rate: Minimum sampling rate (log all)
            max_sample_rate: Maximum sampling rate (highest reduction)
        """
        super().__init__()
        self.target_logs_per_second = target_logs_per_second
        self.window_seconds = window_seconds
        self.min_sample_rate = min_sample_rate
        self.max_sample_rate = max_sample_rate

        # Per-logger tracking
        self.log_counts: Dict[str, List[tuple[float, int]]] = defaultdict(list)
        self._lock = threading.Lock()

    def _calculate_current_rate(self, logger_name: str) -> float:
        """Calculate current log rate for a logger.

        Args:
            logger_name: Name of logger

        Returns:
            Logs per second over recent window
        """
        now = time.time()
        cutoff = now - self.window_seconds

        # Remove old entries
        recent = [(ts, count) for ts, count in self.log_counts[logger_name] if ts > cutoff]
        self.log_counts[logger_name] = recent

        if not recent:
            return 0.0

        total_logs = sum(count for _, count in recent)
        time_span = now - recent[0][0]

        if time_span == 0:
            return 0.0

        return total_logs / time_span

    def filter(self, record: logging.LogRecord) -> bool:
        """Filter with adaptive sampling.

        Args:
            record: Log record

        Returns:
            True if should log
        """
        # Always log WARNING+
        if record.levelno >= logging.WARNING:
            return True

        logger_name = record.name

        with self._lock:
            # Track this log attempt
            now = time.time()
            if not self.log_counts[logger_name]:
                self.log_counts[logger_name].append((now, 1))
            else:
                last_ts, count = self.log_counts[logger_name][-1]
                if now - last_ts < 1.0:  # Same second
                    self.log_counts[logger_name][-1] = (last_ts, count + 1)
                else:
                    self.log_counts[logger_name].append((now, 1))

            # Calculate current rate
            current_rate = self._calculate_current_rate(logger_name)

            if current_rate == 0:
                return True

            # Adaptive sampling: if rate > target, increase sample rate
            if current_rate > self.target_logs_per_second:
                sample_rate = min(
                    int(current_rate / self.target_logs_per_second),
                    self.max_sample_rate
                )
            else:
                sample_rate = self.min_sample_rate

            # Sample based on calculated rate
            if sample_rate == 1:
                return True

            # Use hash of timestamp + logger for deterministic sampling
            sample_hash = hash((now, logger_name)) % sample_rate
            return sample_hash == 0


class AsyncLogHandler:
    """Non-blocking async log handler using QueueHandler/QueueListener.

    Features:
    - Non-blocking log writes (queue-based)
    - Background thread for log processing
    - Configurable queue size with overflow handling
    - Statistics tracking (queue size, dropped logs)
    - Graceful shutdown

    Example:
        >>> async_handler = AsyncLogHandler()
        >>> async_handler.start()
        >>> # Use logging normally
        >>> async_handler.stop()
    """

    def __init__(
        self,
        handlers: Optional[List[logging.Handler]] = None,
        queue_maxsize: int = 10000,
        overflow_strategy: str = "drop",  # "drop" or "block"
    ):
        """Initialize async log handler.

        Args:
            handlers: List of handlers to process logs (None = use defaults)
            queue_maxsize: Maximum queue size (0 = unlimited)
            overflow_strategy: What to do when queue full ("drop" or "block")
        """
        self.log_queue: Queue = Queue(maxsize=queue_maxsize)
        self.queue_maxsize = queue_maxsize
        self.overflow_strategy = overflow_strategy

        # Get handlers or use defaults
        if handlers is None:
            handlers = self._get_default_handlers()

        self.handlers = handlers

        # Create queue handler for main thread
        self.queue_handler = QueueHandler(self.log_queue)

        # Create listener for background thread
        self.listener = QueueListener(
            self.log_queue,
            *self.handlers,
            respect_handler_level=True
        )

        # Statistics
        self.stats = {
            "logs_queued": 0,
            "logs_dropped": 0,
            "queue_overflows": 0,
        }
        self._stats_lock = threading.Lock()

        # Running state
        self.running = False

    def _get_default_handlers(self) -> List[logging.Handler]:
        """Get default handlers (console + rotating file).

        Returns:
            List of default handlers
        """
        import sys
        from pathlib import Path
        from src.utils.logging import CustomJsonFormatter, PrivacyFilter

        handlers = []

        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_handler.addFilter(PrivacyFilter())
        console_handler.setFormatter(
            CustomJsonFormatter("%(timestamp)s %(level)s %(logger)s %(message)s")
        )
        handlers.append(console_handler)

        # File handler (rotating, 10MB max)
        try:
            from src.utils.path_utils import ensure_directory

            log_file = Path("logs/ragged.log")
            ensure_directory(log_file.parent)

            file_handler = RotatingFileHandler(
                log_file,
                maxBytes=10 * 1024 * 1024,  # 10MB
                backupCount=5,
                encoding="utf-8",
            )
            file_handler.setLevel(logging.DEBUG)
            file_handler.addFilter(PrivacyFilter())
            file_handler.setFormatter(
                CustomJsonFormatter(
                    "%(timestamp)s %(level)s %(logger)s %(module)s %(function)s %(message)s"
                )
            )
            handlers.append(file_handler)
        except Exception as e:
            logger.warning(f"Could not create file handler: {e}")

        return handlers

    def start(self) -> None:
        """Start async logging (background thread)."""
        if not self.running:
            self.listener.start()
            self.running = True
            logger.info("Async logging started")

    def stop(self) -> None:
        """Stop async logging (flush and shutdown)."""
        if self.running:
            self.listener.stop()
            self.running = False
            logger.info("Async logging stopped")

    def get_queue_handler(self) -> QueueHandler:
        """Get queue handler for adding to loggers.

        Returns:
            QueueHandler instance

        Example:
            >>> async_handler = AsyncLogHandler()
            >>> async_handler.start()
            >>> logger = logging.getLogger("myapp")
            >>> logger.addHandler(async_handler.get_queue_handler())
        """
        return self.queue_handler

    def get_stats(self) -> dict:
        """Get logging statistics.

        Returns:
            Statistics dictionary
        """
        with self._stats_lock:
            return {
                **self.stats,
                "queue_size": self.log_queue.qsize(),
                "queue_maxsize": self.queue_maxsize,
                "overflow_strategy": self.overflow_strategy,
            }

    def __enter__(self):
        """Context manager entry."""
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.stop()
        return False


# Global instance (optional singleton)
_async_handler: Optional[AsyncLogHandler] = None
_handler_lock = threading.Lock()


def get_async_handler(
    handlers: Optional[List[logging.Handler]] = None,
    queue_maxsize: int = 10000,
) -> AsyncLogHandler:
    """Get singleton async log handler.

    Args:
        handlers: Handlers to use (only used on first call)
        queue_maxsize: Queue size (only used on first call)

    Returns:
        Singleton AsyncLogHandler

    Example:
        >>> async_handler = get_async_handler()
        >>> async_handler.start()
    """
    global _async_handler

    if _async_handler is None:
        with _handler_lock:
            if _async_handler is None:
                _async_handler = AsyncLogHandler(
                    handlers=handlers,
                    queue_maxsize=queue_maxsize,
                )

    return _async_handler


def setup_async_logging(
    queue_maxsize: int = 10000,
    sample_rate: Optional[int] = None,
    adaptive_sampling: bool = False,
) -> AsyncLogHandler:
    """Setup async logging for the application.

    Args:
        queue_maxsize: Maximum log queue size
        sample_rate: Fixed sampling rate (None = no sampling)
        adaptive_sampling: Use adaptive sampling based on load

    Returns:
        AsyncLogHandler instance

    Example:
        >>> handler = setup_async_logging(
        ...     queue_maxsize=10000,
        ...     sample_rate=100,  # Log 1 in 100 INFO/DEBUG
        ... )
        >>> handler.start()
    """
    async_handler = get_async_handler(queue_maxsize=queue_maxsize)

    # Add sampling filter if requested
    if sample_rate is not None:
        sampling_filter = SamplingFilter(sample_rate=sample_rate)
        async_handler.queue_handler.addFilter(sampling_filter)
    elif adaptive_sampling:
        adaptive_filter = AdaptiveSamplingFilter()
        async_handler.queue_handler.addFilter(adaptive_filter)

    # Start handler
    async_handler.start()

    # Add queue handler to root logger
    root_logger = logging.getLogger()
    root_logger.addHandler(async_handler.get_queue_handler())

    logger.info(
        f"Async logging configured: "
        f"queue_size={queue_maxsize}, "
        f"sampling={sample_rate or 'adaptive' if adaptive_sampling else 'none'}"
    )

    return async_handler
