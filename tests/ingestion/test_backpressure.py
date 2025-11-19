"""Tests for async operations with backpressure control.

v0.2.9: Tests for queue depth limits and dynamic scaling.
"""

import pytest
import asyncio
import time
from unittest.mock import Mock, patch, AsyncMock
from pathlib import Path

from src.ingestion.backpressure import (
    AsyncProcessorWithBackpressure,
    BackpressureConfig,
    TaskPriority,
    PriorityTask,
    process_with_backpressure,
)
from src.ingestion.async_processor import ProcessingResult


@pytest.fixture
def config():
    """Create test backpressure configuration."""
    return BackpressureConfig(
        max_queue_depth=10,
        max_concurrent_tasks=3,
        cpu_threshold_percent=80.0,
        enable_dynamic_scaling=False,  # Disable for predictable tests
        min_workers=2,
        max_workers=4,
    )


@pytest.fixture
def processor(config):
    """Create processor with test configuration."""
    return AsyncProcessorWithBackpressure(config)


class TestPriorityTask:
    """Tests for PriorityTask ordering."""

    def test_priority_ordering(self):
        """Test tasks ordered by priority."""
        low = PriorityTask(TaskPriority.LOW, "low_task")
        normal = PriorityTask(TaskPriority.NORMAL, "normal_task")
        high = PriorityTask(TaskPriority.HIGH, "high_task")

        assert high < normal < low  # Higher priority < lower (for sorting)

    def test_fifo_within_priority(self):
        """Test FIFO ordering within same priority."""
        task1 = PriorityTask(TaskPriority.NORMAL, "task1", timestamp=1.0)
        task2 = PriorityTask(TaskPriority.NORMAL, "task2", timestamp=2.0)

        assert task1 < task2  # Earlier timestamp first


class TestBackpressureConfig:
    """Tests for backpressure configuration."""

    def test_default_config(self):
        """Test default configuration values."""
        config = BackpressureConfig()

        assert config.max_queue_depth == 100
        assert config.max_concurrent_tasks == 10
        assert config.enable_dynamic_scaling is True

    def test_custom_config(self):
        """Test custom configuration."""
        config = BackpressureConfig(
            max_queue_depth=50,
            max_concurrent_tasks=5,
        )

        assert config.max_queue_depth == 50
        assert config.max_concurrent_tasks == 5


class TestAsyncProcessorWithBackpressure:
    """Tests for async processor with backpressure."""

    def test_initialization(self, processor, config):
        """Test processor initializes correctly."""
        assert processor.config == config
        assert processor.task_queue.maxsize == config.max_queue_depth
        assert processor.semaphore._value == config.max_concurrent_tasks
        assert processor.current_workers == config.max_workers

    @pytest.mark.asyncio
    async def test_enqueue_task(self, processor):
        """Test enqueueing tasks."""
        result = await processor.enqueue_task("test_task", TaskPriority.NORMAL)

        assert result is True
        assert processor.stats["tasks_queued"] == 1
        assert processor.task_queue.qsize() == 1

    @pytest.mark.asyncio
    async def test_enqueue_with_priority(self, processor):
        """Test priority task enqueueing."""
        await processor.enqueue_task("low", TaskPriority.LOW)
        await processor.enqueue_task("high", TaskPriority.HIGH)
        await processor.enqueue_task("normal", TaskPriority.NORMAL)

        assert processor.task_queue.qsize() == 3

    @pytest.mark.asyncio
    async def test_queue_full_timeout(self):
        """Test queue full causes timeout."""
        config = BackpressureConfig(max_queue_depth=2)
        processor = AsyncProcessorWithBackpressure(config)

        # Fill queue
        await processor.enqueue_task("task1")
        await processor.enqueue_task("task2")

        # This should timeout
        result = await processor.enqueue_task("task3", timeout=0.1)

        assert result is False
        assert processor.stats["queue_full_count"] == 1

    @pytest.mark.asyncio
    async def test_process_with_backpressure(self, processor):
        """Test processing items with backpressure."""
        items = list(range(10))

        def process_fn(item):
            return item * 2

        results = await processor.process_with_backpressure(
            items=items,
            process_fn=process_fn,
        )

        assert len(results) == 10
        assert set(results) == {i * 2 for i in items}
        assert processor.stats["tasks_completed"] == 10

    @pytest.mark.asyncio
    async def test_concurrent_limit(self):
        """Test concurrent tasks are limited."""
        config = BackpressureConfig(
            max_queue_depth=20,
            max_concurrent_tasks=2,
        )
        processor = AsyncProcessorWithBackpressure(config)

        concurrent_count = 0
        max_concurrent = 0

        async def track_concurrency(item):
            nonlocal concurrent_count, max_concurrent
            concurrent_count += 1
            max_concurrent = max(max_concurrent, concurrent_count)
            await asyncio.sleep(0.1)  # Simulate work
            concurrent_count -= 1
            return item

        items = list(range(10))

        await processor.process_with_backpressure(
            items=items,
            process_fn=lambda i: asyncio.run(track_concurrency(i)),
        )

        # Max concurrent should respect semaphore limit
        assert max_concurrent <= config.max_concurrent_tasks

    @pytest.mark.asyncio
    async def test_statistics_tracking(self, processor):
        """Test statistics are tracked correctly."""
        items = [1, 2, 3]

        def process_fn(item):
            if item == 2:
                raise ValueError("Test error")
            return item * 2

        await processor.process_with_backpressure(
            items=items,
            process_fn=process_fn,
        )

        stats = processor.get_stats()
        assert stats["tasks_queued"] == 3
        assert stats["tasks_completed"] == 2
        assert stats["tasks_failed"] == 1

    @pytest.mark.asyncio
    async def test_get_stats(self, processor):
        """Test get_stats returns complete statistics."""
        stats = processor.get_stats()

        assert "tasks_queued" in stats
        assert "tasks_completed" in stats
        assert "tasks_failed" in stats
        assert "queue_size" in stats
        assert "current_workers" in stats
        assert "cpu_usage" in stats


class TestDynamicScaling:
    """Tests for dynamic worker pool scaling."""

    @pytest.mark.asyncio
    async def test_scaling_disabled_by_config(self):
        """Test scaling doesn't occur when disabled."""
        config = BackpressureConfig(
            enable_dynamic_scaling=False,
            min_workers=2,
            max_workers=4,
        )
        processor = AsyncProcessorWithBackpressure(config)

        initial_workers = processor.current_workers

        # Trigger scaling attempt
        await processor._adjust_workers()

        # Workers should not change
        assert processor.current_workers == initial_workers

    @pytest.mark.asyncio
    @patch('src.ingestion.backpressure.psutil.cpu_percent')
    async def test_scale_down_on_high_cpu(self, mock_cpu):
        """Test worker pool scales down on high CPU."""
        config = BackpressureConfig(
            enable_dynamic_scaling=True,
            cpu_threshold_percent=80.0,
            min_workers=2,
            max_workers=4,
        )
        processor = AsyncProcessorWithBackpressure(config)
        processor.last_scale_time = 0  # Allow immediate scaling

        # Simulate high CPU
        mock_cpu.return_value = 90.0

        initial_workers = processor.current_workers
        await processor._adjust_workers()

        # Should scale down
        assert processor.current_workers < initial_workers
        assert processor.current_workers >= config.min_workers

    @pytest.mark.asyncio
    @patch('src.ingestion.backpressure.psutil.cpu_percent')
    async def test_scale_up_on_low_cpu_and_queue(self, mock_cpu):
        """Test worker pool scales up on low CPU and growing queue."""
        config = BackpressureConfig(
            enable_dynamic_scaling=True,
            cpu_threshold_percent=80.0,
            min_workers=2,
            max_workers=4,
        )
        processor = AsyncProcessorWithBackpressure(config)
        processor.current_workers = 2  # Start at min
        processor.last_scale_time = 0  # Allow immediate scaling

        # Simulate low CPU
        mock_cpu.return_value = 40.0

        # Fill queue to >50%
        for i in range(6):  # >50% of max_queue_depth=10
            await processor.enqueue_task(f"task{i}")

        initial_workers = processor.current_workers
        await processor._adjust_workers()

        # Should scale up
        assert processor.current_workers > initial_workers
        assert processor.current_workers <= config.max_workers

    @pytest.mark.asyncio
    async def test_cooldown_prevents_frequent_scaling(self):
        """Test scaling cooldown prevents frequent adjustments."""
        config = BackpressureConfig(
            enable_dynamic_scaling=True,
            min_workers=2,
            max_workers=4,
        )
        processor = AsyncProcessorWithBackpressure(config)

        # Set last scale time to now
        processor.last_scale_time = time.time()

        initial_workers = processor.current_workers
        await processor._adjust_workers()

        # Should not scale (cooldown active)
        assert processor.current_workers == initial_workers


class TestDocumentProcessing:
    """Tests for document processing with backpressure."""

    @pytest.mark.asyncio
    @patch('src.ingestion.backpressure.AsyncProcessorWithBackpressure.load_document_async')
    @patch('src.ingestion.backpressure.AsyncProcessorWithBackpressure.process_document_async')
    async def test_process_documents_with_backpressure(
        self, mock_process, mock_load, processor
    ):
        """Test processing documents with backpressure."""
        # Setup mocks
        mock_doc = Mock()
        mock_doc.document_id = "test_doc"
        mock_load.return_value = mock_doc

        mock_result = ProcessingResult(
            document_id="test_doc",
            success=True,
            duration=0.1,
            chunks_created=5,
        )
        mock_process.return_value = mock_result

        file_paths = [Path(f"doc{i}.txt") for i in range(3)]

        results = await processor.process_documents_with_backpressure(
            file_paths=file_paths,
            chunker=Mock(),
        )

        assert len(results) == 3
        assert all(r.success for r in results)
        assert mock_load.call_count == 3
        assert mock_process.call_count == 3


class TestConvenienceFunction:
    """Tests for convenience function."""

    @pytest.mark.asyncio
    async def test_process_with_backpressure_function(self):
        """Test convenience function works correctly."""
        items = list(range(5))

        def process_fn(item):
            return item * 3

        results = await process_with_backpressure(
            items=items,
            process_fn=process_fn,
            max_queue_depth=10,
            max_concurrent=2,
        )

        assert len(results) == 5
        assert set(results) == {i * 3 for i in items}


class TestAsyncContextManager:
    """Tests for async context manager."""

    @pytest.mark.asyncio
    async def test_context_manager_cleanup(self):
        """Test context manager properly cleans up."""
        config = BackpressureConfig(max_workers=2)

        async with AsyncProcessorWithBackpressure(config) as processor:
            # Use processor
            await processor.enqueue_task("test")
            assert processor.task_queue.qsize() == 1

        # Executor should be shut down after context
        # (Can't easily test shutdown state, but ensure no errors)


class TestErrorHandling:
    """Tests for error handling."""

    @pytest.mark.asyncio
    async def test_processing_error_continues(self, processor):
        """Test processing continues after errors."""
        items = [1, 2, 3, 4, 5]

        def process_fn(item):
            if item == 3:
                raise ValueError("Test error")
            return item * 2

        results = await processor.process_with_backpressure(
            items=items,
            process_fn=process_fn,
        )

        # Should have 5 results (4 successful, 1 None)
        assert len(results) == 5
        assert processor.stats["tasks_completed"] == 4
        assert processor.stats["tasks_failed"] == 1

    @pytest.mark.asyncio
    @patch('src.ingestion.backpressure.AsyncProcessorWithBackpressure.load_document_async')
    async def test_document_load_failure(self, mock_load, processor):
        """Test handling of document load failures."""
        mock_load.return_value = None  # Simulate load failure

        file_paths = [Path("failed.txt")]

        results = await processor.process_documents_with_backpressure(
            file_paths=file_paths,
            chunker=Mock(),
        )

        assert len(results) == 1
        assert not results[0].success
        assert "Failed to load" in results[0].error


class TestIntegrationScenarios:
    """Integration tests for realistic scenarios."""

    @pytest.mark.asyncio
    async def test_high_volume_processing(self):
        """Test processing large volume of items."""
        config = BackpressureConfig(
            max_queue_depth=100,
            max_concurrent_tasks=5,
        )
        processor = AsyncProcessorWithBackpressure(config)

        items = list(range(50))

        def process_fn(item):
            time.sleep(0.01)  # Simulate work
            return item ** 2

        results = await processor.process_with_backpressure(
            items=items,
            process_fn=process_fn,
        )

        assert len(results) == 50
        assert processor.stats["tasks_completed"] == 50
        assert processor.stats["tasks_failed"] == 0

    @pytest.mark.asyncio
    async def test_mixed_priority_processing(self):
        """Test processing with mixed priorities."""
        processor = AsyncProcessorWithBackpressure()

        # Enqueue tasks with different priorities
        await processor.enqueue_task("low1", TaskPriority.LOW)
        await processor.enqueue_task("high1", TaskPriority.HIGH)
        await processor.enqueue_task("normal1", TaskPriority.NORMAL)
        await processor.enqueue_task("critical1", TaskPriority.CRITICAL)

        # Process should handle all priorities
        assert processor.task_queue.qsize() == 4
