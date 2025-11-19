"""Async operations with backpressure control.

v0.2.9: Enhanced async processing with queue depth limits and dynamic scaling.
"""

import asyncio
import psutil  # type: ignore[import-untyped]
import time
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import List, Optional, Callable, Any, TypeVar, Generic
from concurrent.futures import ThreadPoolExecutor

from src.ingestion.async_processor import AsyncDocumentProcessor, ProcessingResult
from src.ingestion.models import Document
from src.utils.logging import get_logger

logger = get_logger(__name__)

T = TypeVar('T')


class TaskPriority(int, Enum):
    """Task priority levels for queue processing."""

    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4


@dataclass
class PriorityTask(Generic[T]):
    """Task with priority for queue processing."""

    priority: TaskPriority
    task: T
    timestamp: float = 0.0

    def __post_init__(self):
        """Set timestamp if not provided."""
        if self.timestamp == 0.0:
            self.timestamp = time.time()

    def __lt__(self, other: 'PriorityTask') -> bool:
        """Compare tasks by priority (higher priority first), then timestamp (FIFO)."""
        if self.priority != other.priority:
            return self.priority > other.priority  # Higher priority first
        return self.timestamp < other.timestamp  # FIFO within same priority


class BackpressureConfig:
    """Configuration for backpressure control."""

    def __init__(
        self,
        max_queue_depth: int = 100,
        max_concurrent_tasks: int = 10,
        cpu_threshold_percent: float = 80.0,
        enable_dynamic_scaling: bool = True,
        min_workers: int = 2,
        max_workers: Optional[int] = None,
    ):
        """Initialize backpressure configuration.

        Args:
            max_queue_depth: Maximum items in queue before blocking
            max_concurrent_tasks: Maximum concurrent operations
            cpu_threshold_percent: CPU usage threshold for scaling down
            enable_dynamic_scaling: Enable dynamic worker pool adjustment
            min_workers: Minimum worker count
            max_workers: Maximum worker count (None = CPU count)
        """
        self.max_queue_depth = max_queue_depth
        self.max_concurrent_tasks = max_concurrent_tasks
        self.cpu_threshold_percent = cpu_threshold_percent
        self.enable_dynamic_scaling = enable_dynamic_scaling
        self.min_workers = min_workers
        self.max_workers = max_workers or psutil.cpu_count()


class AsyncProcessorWithBackpressure(AsyncDocumentProcessor):
    """Async document processor with backpressure control.

    Features:
    - Queue depth limits to prevent memory overflow
    - Semaphore-based concurrency control
    - Priority queue for task ordering
    - Dynamic worker pool scaling based on CPU usage
    - Backpressure signals when queue is full

    Example:
        >>> config = BackpressureConfig(max_queue_depth=50, max_concurrent_tasks=5)
        >>> processor = AsyncProcessorWithBackpressure(config)
        >>> async with processor:
        ...     results = await processor.process_with_backpressure(items)
    """

    def __init__(
        self,
        config: Optional[BackpressureConfig] = None,
        max_workers: Optional[int] = None,
    ):
        """Initialize processor with backpressure.

        Args:
            config: Backpressure configuration (None = use defaults)
            max_workers: Override max workers from config
        """
        self.config = config or BackpressureConfig()

        # Override max_workers if provided
        if max_workers is not None:
            self.config.max_workers = max_workers

        super().__init__(max_workers=self.config.max_workers)

        # Backpressure controls
        self.task_queue: asyncio.Queue = asyncio.Queue(
            maxsize=self.config.max_queue_depth
        )
        self.semaphore = asyncio.Semaphore(self.config.max_concurrent_tasks)

        # Statistics
        self.stats = {
            "tasks_queued": 0,
            "tasks_completed": 0,
            "tasks_failed": 0,
            "queue_full_count": 0,
            "max_queue_size": 0,
            "worker_adjustments": 0,
        }
        self._stats_lock = asyncio.Lock()

        # Dynamic scaling state
        self.current_workers = self.config.max_workers
        self.last_scale_time = time.time()
        self.scale_cooldown = 10.0  # Seconds between scaling adjustments

        logger.info(
            f"Async processor with backpressure initialized: "
            f"queue_depth={self.config.max_queue_depth}, "
            f"max_concurrent={self.config.max_concurrent_tasks}, "
            f"workers={self.current_workers}"
        )

    async def _update_stats(self, **kwargs):
        """Update statistics atomically.

        Args:
            **kwargs: Stats to update
        """
        async with self._stats_lock:
            for key, value in kwargs.items():
                if key in self.stats:
                    if isinstance(value, (int, float)):
                        self.stats[key] += value
                    else:
                        self.stats[key] = value

    def _get_cpu_usage(self) -> float:
        """Get current CPU usage percentage.

        Returns:
            CPU usage (0-100)
        """
        return psutil.cpu_percent(interval=0.1)

    async def _adjust_workers(self) -> None:
        """Dynamically adjust worker pool size based on CPU usage."""
        if not self.config.enable_dynamic_scaling:
            return

        # Check cooldown
        now = time.time()
        if now - self.last_scale_time < self.scale_cooldown:
            return

        cpu_usage = self._get_cpu_usage()

        # Scale down if CPU usage is high
        if cpu_usage > self.config.cpu_threshold_percent:
            if self.current_workers > self.config.min_workers:
                self.current_workers = max(
                    self.config.min_workers,
                    self.current_workers - 1
                )
                self.last_scale_time = now
                await self._update_stats(worker_adjustments=1)
                logger.debug(
                    f"Scaled down workers to {self.current_workers} "
                    f"(CPU: {cpu_usage:.1f}%)"
                )

        # Scale up if CPU usage is low and queue is growing
        elif cpu_usage < self.config.cpu_threshold_percent * 0.6:  # 60% of threshold
            queue_size = self.task_queue.qsize()
            if queue_size > self.config.max_queue_depth * 0.5:  # Queue >50% full
                if self.current_workers < self.config.max_workers:
                    self.current_workers = min(
                        self.config.max_workers,
                        self.current_workers + 1
                    )
                    self.last_scale_time = now
                    await self._update_stats(worker_adjustments=1)
                    logger.debug(
                        f"Scaled up workers to {self.current_workers} "
                        f"(CPU: {cpu_usage:.1f}%, queue: {queue_size})"
                    )

    async def enqueue_task(
        self,
        task: Any,
        priority: TaskPriority = TaskPriority.NORMAL,
        timeout: Optional[float] = None,
    ) -> bool:
        """Enqueue task with priority.

        Args:
            task: Task to enqueue
            priority: Task priority
            timeout: Maximum time to wait for queue space (None = wait forever)

        Returns:
            True if enqueued, False if timeout

        Raises:
            asyncio.QueueFull: If timeout and queue full
        """
        priority_task = PriorityTask(priority=priority, task=task)

        try:
            await asyncio.wait_for(
                self.task_queue.put(priority_task),
                timeout=timeout
            )
            await self._update_stats(tasks_queued=1)

            # Track max queue size
            queue_size = self.task_queue.qsize()
            if queue_size > self.stats["max_queue_size"]:
                await self._update_stats(max_queue_size=queue_size)

            return True

        except asyncio.TimeoutError:
            await self._update_stats(queue_full_count=1)
            logger.warning(
                f"Queue full ({self.config.max_queue_depth}), "
                f"task dropped (priority={priority.name})"
            )
            return False

    async def process_with_backpressure(
        self,
        items: List[Any],
        process_fn: Callable[[Any], Any],
        priority: TaskPriority = TaskPriority.NORMAL,
        progress_callback: Optional[Callable[[int, int], None]] = None,
    ) -> List[Any]:
        """Process items with backpressure control.

        Args:
            items: Items to process
            process_fn: Processing function
            priority: Task priority
            progress_callback: Optional progress callback

        Returns:
            List of results
        """
        logger.info(f"Processing {len(items)} items with backpressure...")

        start_time = time.time()
        results = []

        # Worker coroutine
        async def worker():
            """Worker that processes tasks from queue."""
            while True:
                try:
                    # Get task from queue with timeout
                    priority_task = await asyncio.wait_for(
                        self.task_queue.get(),
                        timeout=1.0
                    )

                    async with self.semaphore:
                        # Adjust workers dynamically
                        await self._adjust_workers()

                        # Process task
                        try:
                            result = await asyncio.get_event_loop().run_in_executor(
                                self.executor,
                                process_fn,
                                priority_task.task
                            )
                            results.append(result)
                            await self._update_stats(tasks_completed=1)

                        except Exception as e:
                            logger.error(f"Task processing failed: {e}")
                            results.append(None)
                            await self._update_stats(tasks_failed=1)

                        finally:
                            self.task_queue.task_done()

                            # Progress callback
                            if progress_callback:
                                completed = self.stats["tasks_completed"] + self.stats["tasks_failed"]
                                progress_callback(completed, len(items))

                except asyncio.TimeoutError:
                    # No tasks available, check if done
                    if self.task_queue.empty() and len(results) >= len(items):
                        break

        # Enqueue all items
        for item in items:
            await self.enqueue_task(item, priority=priority)

        # Start workers
        workers = [
            asyncio.create_task(worker())
            for _ in range(self.current_workers)
        ]

        # Wait for all tasks to complete
        await self.task_queue.join()

        # Cancel workers
        for w in workers:
            w.cancel()

        # Wait for workers to finish
        await asyncio.gather(*workers, return_exceptions=True)

        duration = time.time() - start_time

        logger.info(
            f"Processed {len(results)}/{len(items)} items in {duration:.2f}s "
            f"({len(results)/duration:.1f} items/s)"
        )

        return results

    async def process_documents_with_backpressure(
        self,
        file_paths: List[Path],
        chunker: Any,
        embed_fn: Optional[Callable[..., Any]] = None,
        priority: TaskPriority = TaskPriority.NORMAL,
        progress_callback: Optional[Callable[[int, int], None]] = None,
    ) -> List[ProcessingResult]:
        """Process documents with backpressure control.

        Args:
            file_paths: Document paths
            chunker: Chunking strategy
            embed_fn: Optional embedding function
            priority: Task priority
            progress_callback: Optional progress callback

        Returns:
            List of processing results
        """
        logger.info(
            f"Processing {len(file_paths)} documents with backpressure "
            f"(priority={priority.name})..."
        )

        # Define processing function
        async def process_doc(file_path: Path) -> ProcessingResult:
            """Load and process single document."""
            # Load document
            doc = await self.load_document_async(file_path)
            if not doc:
                return ProcessingResult(
                    document_id=str(file_path),
                    success=False,
                    duration=0.0,
                    error="Failed to load document"
                )

            # Process document
            return await self.process_document_async(doc, chunker, embed_fn)

        # Create tasks
        tasks = [process_doc(fp) for fp in file_paths]

        # Process with semaphore control
        results = []
        for i, task in enumerate(asyncio.as_completed(tasks), 1):
            async with self.semaphore:
                result = await task
                results.append(result)

                if progress_callback:
                    progress_callback(i, len(file_paths))

        return results

    def get_stats(self) -> dict:
        """Get processing statistics.

        Returns:
            Statistics dictionary
        """
        return {
            **self.stats,
            "queue_size": self.task_queue.qsize(),
            "max_queue_depth": self.config.max_queue_depth,
            "current_workers": self.current_workers,
            "max_workers": self.config.max_workers,
            "cpu_usage": self._get_cpu_usage(),
        }

    async def __aenter__(self) -> 'AsyncProcessorWithBackpressure':
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Async context manager exit."""
        self.shutdown(wait=True)


# Convenience function
async def process_with_backpressure(
    items: List[Any],
    process_fn: Callable[[Any], Any],
    max_queue_depth: int = 100,
    max_concurrent: int = 10,
    priority: TaskPriority = TaskPriority.NORMAL,
) -> List[Any]:
    """Process items with backpressure (convenience function).

    Args:
        items: Items to process
        process_fn: Processing function
        max_queue_depth: Maximum queue size
        max_concurrent: Maximum concurrent tasks
        priority: Task priority

    Returns:
        List of results

    Example:
        >>> results = await process_with_backpressure(
        ...     items=documents,
        ...     process_fn=lambda d: process(d),
        ...     max_concurrent=5
        ... )
    """
    config = BackpressureConfig(
        max_queue_depth=max_queue_depth,
        max_concurrent_tasks=max_concurrent,
    )

    async with AsyncProcessorWithBackpressure(config) as processor:
        return await processor.process_with_backpressure(
            items=items,
            process_fn=process_fn,
            priority=priority,
        )
