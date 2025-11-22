"""Unified resource governance system for memory, CPU, and concurrency.

v0.2.9: Prevents resource starvation through reservation system with queueing.
"""

import gc
import threading
import time
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from enum import Enum
from queue import Empty, Queue
from typing import Optional

import psutil  # type: ignore[import-untyped]

from src.config.settings import get_settings
from src.utils.logging import get_logger

logger = get_logger(__name__)


class ResourceType(str, Enum):
    """Types of resources that can be governed."""

    MEMORY = "memory"
    CPU = "cpu"
    CONCURRENCY = "concurrency"


class ResourcePriority(int, Enum):
    """Priority levels for resource requests."""

    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4


@dataclass
class ResourceRequest:
    """Resource reservation request."""

    operation_id: str
    memory_mb: int
    cpu_percent: float
    priority: ResourcePriority = ResourcePriority.NORMAL
    timestamp: float = 0.0

    def __post_init__(self):
        """Set timestamp if not provided."""
        if self.timestamp == 0.0:
            self.timestamp = time.time()


@dataclass
class ResourceReservation:
    """Active resource reservation."""

    operation_id: str
    memory_mb: int
    cpu_percent: float
    priority: ResourcePriority
    start_time: float


class ResourceGovernorError(Exception):
    """Base exception for resource governor errors."""
    pass


class ResourceUnavailableError(ResourceGovernorError):
    """Raised when requested resources are not available."""

    def __init__(self, request: ResourceRequest, reason: str):
        super().__init__(
            f"Resources unavailable for '{request.operation_id}': {reason}"
        )
        self.request = request
        self.reason = reason


class ResourceGovernor:
    """Unified resource budget management.

    Manages memory, CPU, and concurrency limits with fair queuing.

    Features:
    - Memory limit enforcement (MB)
    - CPU utilization capping (%)
    - Concurrent operation limiting
    - Priority-based queuing
    - Automatic garbage collection on pressure
    - Thread-safe reservation system

    Example:
        >>> governor = get_governor()
        >>> with governor.reserve("task1", memory_mb=100, cpu_percent=10):
        ...     # Perform task with guaranteed resources
        ...     process_data()
    """

    _instance: Optional['ResourceGovernor'] = None
    _lock = threading.Lock()

    def __init__(
        self,
        memory_limit_mb: int | None = None,
        cpu_limit_percent: float | None = None,
        max_concurrent_ops: int | None = None,
        enable_gc: bool = True,
    ):
        """Initialize resource governor.

        Args:
            memory_limit_mb: Maximum memory budget (default: from settings or 4GB)
            cpu_limit_percent: Maximum CPU utilization (default: from settings or 80%)
            max_concurrent_ops: Maximum concurrent operations (default: from settings or 4)
            enable_gc: Enable automatic garbage collection on memory pressure
        """
        settings = get_settings()

        # Set resource limits from settings or defaults
        if memory_limit_mb is None:
            # Use 80% of available RAM by default
            total_mb = psutil.virtual_memory().total / (1024 * 1024)
            self.memory_limit_mb = int(total_mb * 0.8)
        else:
            self.memory_limit_mb = memory_limit_mb

        self.cpu_limit_percent = cpu_limit_percent or 80.0
        self.max_concurrent_ops = max_concurrent_ops or 4
        self.enable_gc = enable_gc

        # Active reservations
        self.reservations: dict[str, ResourceReservation] = {}

        # Request queue (priority, timestamp, request)
        self.request_queue: Queue = Queue()

        # Thread synchronization
        self._reservation_lock = threading.Lock()

        # Statistics
        self.stats = {
            "total_requests": 0,
            "fulfilled_requests": 0,
            "queued_requests": 0,
            "rejected_requests": 0,
            "gc_triggers": 0,
        }

        logger.info(
            f"ResourceGovernor initialized: "
            f"memory={self.memory_limit_mb}MB, "
            f"cpu={self.cpu_limit_percent}%, "
            f"max_ops={self.max_concurrent_ops}"
        )

    @classmethod
    def get_instance(cls) -> 'ResourceGovernor':
        """Get singleton instance.

        Returns:
            Singleton ResourceGovernor instance
        """
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance

    @classmethod
    def reset_instance(cls) -> None:
        """Reset singleton instance (for testing)."""
        with cls._lock:
            cls._instance = None

    def _get_current_memory_mb(self) -> float:
        """Get current process memory usage in MB.

        Returns:
            Current memory usage in megabytes
        """
        process = psutil.Process()
        return float(process.memory_info().rss / (1024 * 1024))

    def _get_current_cpu_percent(self) -> float:
        """Get current process CPU utilization.

        Returns:
            CPU percentage (0-100)
        """
        process = psutil.Process()
        # Use interval=0.1 for quick but reasonably accurate measurement
        return float(process.cpu_percent(interval=0.1))

    def _total_reserved_memory(self) -> int:
        """Calculate total reserved memory across all operations.

        Returns:
            Total reserved memory in MB
        """
        return sum(res.memory_mb for res in self.reservations.values())

    def _total_reserved_cpu(self) -> float:
        """Calculate total reserved CPU across all operations.

        Returns:
            Total reserved CPU percentage
        """
        return sum(res.cpu_percent for res in self.reservations.values())

    def _trigger_garbage_collection(self) -> int:
        """Force garbage collection to free memory.

        Returns:
            Number of objects collected
        """
        self.stats["gc_triggers"] += 1
        logger.debug("Triggering garbage collection due to memory pressure")
        return gc.collect()

    def _can_fulfill_request(self, request: ResourceRequest) -> tuple[bool, str | None]:
        """Check if request can be fulfilled with current resources.

        Args:
            request: Resource request to check

        Returns:
            Tuple of (can_fulfill, reason_if_not)
        """
        # Check concurrent operations limit
        if len(self.reservations) >= self.max_concurrent_ops:
            return False, f"max concurrent operations ({self.max_concurrent_ops}) reached"

        # Check memory limit
        current_reserved = self._total_reserved_memory()
        if current_reserved + request.memory_mb > self.memory_limit_mb:
            return False, (
                f"memory limit exceeded: "
                f"{current_reserved + request.memory_mb}MB > {self.memory_limit_mb}MB"
            )

        # Check CPU limit
        current_cpu = self._total_reserved_cpu()
        if current_cpu + request.cpu_percent > self.cpu_limit_percent:
            return False, (
                f"CPU limit exceeded: "
                f"{current_cpu + request.cpu_percent}% > {self.cpu_limit_percent}%"
            )

        return True, None

    def request_resources(
        self,
        operation_id: str,
        memory_mb: int,
        cpu_percent: float = 10.0,
        priority: ResourcePriority = ResourcePriority.NORMAL,
        timeout: float | None = None,
    ) -> bool:
        """Request resource reservation.

        Args:
            operation_id: Unique operation identifier
            memory_mb: Memory required in MB
            cpu_percent: CPU percentage required (0-100)
            priority: Request priority
            timeout: Maximum wait time in seconds (None = wait indefinitely)

        Returns:
            True if resources granted, False if timed out

        Raises:
            ResourceUnavailableError: If resources cannot be granted
        """
        self.stats["total_requests"] += 1

        request = ResourceRequest(
            operation_id=operation_id,
            memory_mb=memory_mb,
            cpu_percent=cpu_percent,
            priority=priority,
        )

        with self._reservation_lock:
            # Try immediate fulfillment
            can_fulfill, reason = self._can_fulfill_request(request)

            if can_fulfill:
                # Grant resources immediately
                reservation = ResourceReservation(
                    operation_id=operation_id,
                    memory_mb=memory_mb,
                    cpu_percent=cpu_percent,
                    priority=priority,
                    start_time=time.time(),
                )
                self.reservations[operation_id] = reservation
                self.stats["fulfilled_requests"] += 1

                logger.debug(
                    f"Granted resources for '{operation_id}': "
                    f"{memory_mb}MB, {cpu_percent}% CPU"
                )
                return True

            # Try garbage collection if memory constrained and GC enabled
            if self.enable_gc and "memory" in (reason or ""):
                logger.debug(f"Attempting GC before queuing '{operation_id}'")
                self._trigger_garbage_collection()

                # Retry after GC
                can_fulfill, reason = self._can_fulfill_request(request)
                if can_fulfill:
                    reservation = ResourceReservation(
                        operation_id=operation_id,
                        memory_mb=memory_mb,
                        cpu_percent=cpu_percent,
                        priority=priority,
                        start_time=time.time(),
                    )
                    self.reservations[operation_id] = reservation
                    self.stats["fulfilled_requests"] += 1
                    logger.debug(f"Granted resources for '{operation_id}' after GC")
                    return True

        # Queue request and wait
        self.stats["queued_requests"] += 1
        logger.debug(
            f"Queuing resource request '{operation_id}' "
            f"(priority={priority.name}): {reason}"
        )

        # Priority queue: higher priority = processed first
        # Secondary sort by timestamp (FIFO within same priority)
        self.request_queue.put((
            -priority.value,  # Negative for descending priority
            request.timestamp,
            request
        ))

        # Wait for resources to become available
        start_time = time.time()
        while True:
            # Check timeout
            if timeout is not None and (time.time() - start_time) > timeout:
                self.stats["rejected_requests"] += 1
                logger.warning(f"Resource request '{operation_id}' timed out after {timeout}s")
                return False

            # Try to process queue
            with self._reservation_lock:
                try:
                    # Peek at highest priority request
                    _, _, next_request = self.request_queue.get_nowait()

                    # Check if it's our request
                    if next_request.operation_id == operation_id:
                        can_fulfill, reason = self._can_fulfill_request(next_request)

                        if can_fulfill:
                            reservation = ResourceReservation(
                                operation_id=operation_id,
                                memory_mb=memory_mb,
                                cpu_percent=cpu_percent,
                                priority=priority,
                                start_time=time.time(),
                            )
                            self.reservations[operation_id] = reservation
                            self.stats["fulfilled_requests"] += 1
                            logger.debug(f"Granted queued resources for '{operation_id}'")
                            return True
                        else:
                            # Put back in queue
                            self.request_queue.put((
                                -next_request.priority.value,
                                next_request.timestamp,
                                next_request
                            ))
                    else:
                        # Put back in queue (not our request)
                        self.request_queue.put((
                            -next_request.priority.value,
                            next_request.timestamp,
                            next_request
                        ))

                except Empty:
                    pass

            # Sleep briefly before retry
            time.sleep(0.1)

    def release_resources(self, operation_id: str) -> None:
        """Release reserved resources.

        Args:
            operation_id: Operation identifier to release
        """
        with self._reservation_lock:
            if operation_id in self.reservations:
                reservation = self.reservations[operation_id]
                duration = time.time() - reservation.start_time

                del self.reservations[operation_id]

                logger.debug(
                    f"Released resources for '{operation_id}': "
                    f"{reservation.memory_mb}MB, {reservation.cpu_percent}% CPU "
                    f"(held for {duration:.2f}s)"
                )
            else:
                logger.warning(f"Attempted to release unknown operation '{operation_id}'")

    @contextmanager
    def reserve(
        self,
        operation_id: str,
        memory_mb: int,
        cpu_percent: float = 10.0,
        priority: ResourcePriority = ResourcePriority.NORMAL,
        timeout: float | None = None,
    ) -> Iterator[None]:
        """Context manager for resource reservation.

        Args:
            operation_id: Unique operation identifier
            memory_mb: Memory required in MB
            cpu_percent: CPU percentage required (0-100)
            priority: Request priority
            timeout: Maximum wait time in seconds

        Yields:
            None (resources are reserved during context)

        Raises:
            ResourceUnavailableError: If resources cannot be obtained

        Example:
            >>> governor = get_governor()
            >>> with governor.reserve("batch", memory_mb=500, cpu_percent=20):
            ...     process_batch()
        """
        granted = self.request_resources(
            operation_id=operation_id,
            memory_mb=memory_mb,
            cpu_percent=cpu_percent,
            priority=priority,
            timeout=timeout,
        )

        if not granted:
            raise ResourceUnavailableError(
                request=ResourceRequest(
                    operation_id=operation_id,
                    memory_mb=memory_mb,
                    cpu_percent=cpu_percent,
                    priority=priority,
                ),
                reason=f"timed out after {timeout}s"
            )

        try:
            yield
        finally:
            self.release_resources(operation_id)

    def get_stats(self) -> dict:
        """Get resource governor statistics.

        Returns:
            Statistics dictionary
        """
        with self._reservation_lock:
            return {
                **self.stats,
                "active_reservations": len(self.reservations),
                "queued_requests": self.request_queue.qsize(),
                "current_memory_mb": self._get_current_memory_mb(),
                "reserved_memory_mb": self._total_reserved_memory(),
                "reserved_cpu_percent": self._total_reserved_cpu(),
                "memory_limit_mb": self.memory_limit_mb,
                "cpu_limit_percent": self.cpu_limit_percent,
                "max_concurrent_ops": self.max_concurrent_ops,
            }

    def __repr__(self) -> str:
        """String representation."""
        stats = self.get_stats()
        return (
            f"ResourceGovernor("
            f"memory={stats['reserved_memory_mb']}/{self.memory_limit_mb}MB, "
            f"cpu={stats['reserved_cpu_percent']:.1f}/{self.cpu_limit_percent}%, "
            f"active={stats['active_reservations']}/{self.max_concurrent_ops}"
            f")"
        )


# Singleton accessor
def get_governor() -> ResourceGovernor:
    """Get singleton ResourceGovernor instance.

    Returns:
        Singleton ResourceGovernor

    Example:
        >>> governor = get_governor()
        >>> with governor.reserve("task", memory_mb=100):
        ...     do_work()
    """
    return ResourceGovernor.get_instance()
