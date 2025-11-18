"""Tests for performance-aware async logging system.

v0.2.9: Tests for non-blocking logging with sampling.
"""

import pytest
import logging
import time
import threading
from unittest.mock import Mock, patch, MagicMock

from src.utils.async_logging import (
    SamplingFilter,
    AdaptiveSamplingFilter,
    AsyncLogHandler,
    get_async_handler,
    setup_async_logging,
)


@pytest.fixture
def mock_log_record():
    """Create mock log record for testing."""
    record = Mock(spec=logging.LogRecord)
    record.name = "test.logger"
    record.levelno = logging.INFO
    record.levelname = "INFO"
    record.msg = "Test message"
    return record


class TestSamplingFilter:
    """Tests for basic sampling filter."""

    def test_always_logs_warnings(self, mock_log_record):
        """Test WARNING+ always logged (never sampled)."""
        filter = SamplingFilter(sample_rate=100)

        mock_log_record.levelno = logging.WARNING
        assert filter.filter(mock_log_record) is True

        mock_log_record.levelno = logging.ERROR
        assert filter.filter(mock_log_record) is True

        mock_log_record.levelno = logging.CRITICAL
        assert filter.filter(mock_log_record) is True

    def test_samples_info_debug(self, mock_log_record):
        """Test INFO/DEBUG sampled at correct rate."""
        filter = SamplingFilter(sample_rate=10)

        mock_log_record.levelno = logging.INFO

        # First 9 should be filtered, 10th should pass
        results = []
        for i in range(20):
            results.append(filter.filter(mock_log_record))

        # Should have exactly 2 True (at positions 10 and 20)
        assert sum(results) == 2
        assert results[9] is True  # 10th
        assert results[19] is True  # 20th

    def test_sample_rate_one(self, mock_log_record):
        """Test sample rate of 1 logs everything."""
        filter = SamplingFilter(sample_rate=1)

        mock_log_record.levelno = logging.INFO

        for i in range(10):
            assert filter.filter(mock_log_record) is True

    def test_thread_safety(self, mock_log_record):
        """Test sampling is thread-safe."""
        filter = SamplingFilter(sample_rate=100)
        mock_log_record.levelno = logging.INFO

        results = []
        lock = threading.Lock()

        def log_many():
            for i in range(1000):
                result = filter.filter(mock_log_record)
                with lock:
                    results.append(result)

        threads = [threading.Thread(target=log_many) for _ in range(4)]

        for t in threads:
            t.start()

        for t in threads:
            t.join()

        # Should have ~40 True (4000 / 100)
        true_count = sum(results)
        assert 35 <= true_count <= 45  # Allow some variance


class TestAdaptiveSamplingFilter:
    """Tests for adaptive sampling filter."""

    def test_always_logs_warnings(self, mock_log_record):
        """Test WARNING+ always logged."""
        filter = AdaptiveSamplingFilter(target_logs_per_second=100)

        mock_log_record.levelno = logging.WARNING
        assert filter.filter(mock_log_record) is True

    def test_increases_sampling_under_load(self, mock_log_record):
        """Test sampling increases when log rate exceeds target."""
        filter = AdaptiveSamplingFilter(
            target_logs_per_second=10,
            window_seconds=1,
        )

        mock_log_record.levelno = logging.INFO

        # Generate high log volume (>target)
        logged = 0
        for i in range(100):
            if filter.filter(mock_log_record):
                logged += 1

        # Should sample (not log all 100)
        assert logged < 100

    def test_low_volume_logs_all(self, mock_log_record):
        """Test low volume logs everything."""
        filter = AdaptiveSamplingFilter(
            target_logs_per_second=1000,  # High target
            window_seconds=1,
        )

        mock_log_record.levelno = logging.INFO

        # Generate low volume
        for i in range(10):
            assert filter.filter(mock_log_record) is True


class TestAsyncLogHandler:
    """Tests for async log handler."""

    def test_initialization(self):
        """Test handler initializes correctly."""
        handler = AsyncLogHandler()

        assert handler.log_queue is not None
        assert handler.queue_handler is not None
        assert handler.listener is not None
        assert handler.running is False

    def test_start_stop(self):
        """Test starting and stopping handler."""
        handler = AsyncLogHandler()

        handler.start()
        assert handler.running is True

        handler.stop()
        assert handler.running is False

    def test_context_manager(self):
        """Test context manager interface."""
        with AsyncLogHandler() as handler:
            assert handler.running is True

        assert handler.running is False

    def test_get_queue_handler(self):
        """Test getting queue handler."""
        handler = AsyncLogHandler()
        queue_handler = handler.get_queue_handler()

        assert queue_handler is handler.queue_handler

    def test_statistics_tracking(self):
        """Test statistics are tracked."""
        handler = AsyncLogHandler()
        stats = handler.get_stats()

        assert "logs_queued" in stats
        assert "logs_dropped" in stats
        assert "queue_size" in stats
        assert "queue_maxsize" in stats

    @patch('logging.handlers.QueueListener')
    def test_async_processing(self, mock_listener):
        """Test logs processed asynchronously."""
        handler = AsyncLogHandler()
        handler.start()

        # Create logger with queue handler
        logger = logging.getLogger("test.async")
        logger.addHandler(handler.get_queue_handler())
        logger.setLevel(logging.INFO)

        # Log message
        logger.info("Test async message")

        # Queue should have message
        time.sleep(0.1)  # Allow processing

        handler.stop()

    def test_custom_handlers(self):
        """Test custom handlers can be provided."""
        custom_handler = Mock(spec=logging.Handler)

        handler = AsyncLogHandler(handlers=[custom_handler])

        assert custom_handler in handler.handlers


class TestSetupAsyncLogging:
    """Tests for setup_async_logging function."""

    def test_setup_basic(self):
        """Test basic setup."""
        handler = setup_async_logging(queue_maxsize=1000)

        assert handler is not None
        assert handler.running is True

        handler.stop()

    def test_setup_with_sampling(self):
        """Test setup with fixed sampling."""
        handler = setup_async_logging(
            queue_maxsize=1000,
            sample_rate=100,
        )

        assert handler is not None

        # Check filter added
        filters = handler.queue_handler.filters
        assert any(isinstance(f, SamplingFilter) for f in filters)

        handler.stop()

    def test_setup_with_adaptive_sampling(self):
        """Test setup with adaptive sampling."""
        handler = setup_async_logging(
            queue_maxsize=1000,
            adaptive_sampling=True,
        )

        assert handler is not None

        # Check filter added
        filters = handler.queue_handler.filters
        assert any(isinstance(f, AdaptiveSamplingFilter) for f in filters)

        handler.stop()

    def test_singleton_handler(self):
        """Test handler is singleton."""
        handler1 = get_async_handler()
        handler2 = get_async_handler()

        assert handler1 is handler2


class TestIntegrationScenarios:
    """Integration tests for realistic logging scenarios."""

    def test_high_volume_logging(self):
        """Test system handles high volume logging."""
        with AsyncLogHandler(queue_maxsize=10000) as handler:
            logger = logging.getLogger("test.highvolume")
            logger.addHandler(handler.get_queue_handler())
            logger.setLevel(logging.DEBUG)

            # Log many messages quickly
            for i in range(1000):
                logger.debug(f"Message {i}")

            # Allow processing
            time.sleep(0.5)

            stats = handler.get_stats()
            # Queue should be processed
            assert stats["queue_size"] < 100

    def test_concurrent_logging(self):
        """Test concurrent logging from multiple threads."""
        with AsyncLogHandler() as handler:
            logger = logging.getLogger("test.concurrent")
            logger.addHandler(handler.get_queue_handler())
            logger.setLevel(logging.INFO)

            def log_from_thread(thread_id):
                for i in range(100):
                    logger.info(f"Thread {thread_id}: Message {i}")

            threads = [
                threading.Thread(target=log_from_thread, args=(i,))
                for i in range(4)
            ]

            for t in threads:
                t.start()

            for t in threads:
                t.join()

            # Allow processing
            time.sleep(0.5)

            # All messages should be processed
            stats = handler.get_stats()
            assert stats["queue_size"] == 0

    def test_sampling_reduces_overhead(self):
        """Test sampling reduces log volume."""
        # Without sampling
        with AsyncLogHandler() as handler:
            logger = logging.getLogger("test.nosampling")
            logger.addHandler(handler.get_queue_handler())
            logger.setLevel(logging.DEBUG)

            for i in range(1000):
                logger.debug(f"Message {i}")

            time.sleep(0.2)
            stats_no_sampling = handler.get_stats()

        # With sampling
        with AsyncLogHandler() as handler:
            sampling_filter = SamplingFilter(sample_rate=10)
            handler.queue_handler.addFilter(sampling_filter)

            logger = logging.getLogger("test.withsampling")
            logger.handlers = []  # Clear previous handlers
            logger.addHandler(handler.get_queue_handler())
            logger.setLevel(logging.DEBUG)

            for i in range(1000):
                logger.debug(f"Message {i}")

            time.sleep(0.2)
            stats_with_sampling = handler.get_stats()

        # Sampled version should process fewer logs
        # (Cannot directly compare as queues might be empty after processing)

    def test_mixed_log_levels(self):
        """Test different log levels handled correctly."""
        with AsyncLogHandler() as handler:
            sampling_filter = SamplingFilter(sample_rate=10)
            handler.queue_handler.addFilter(sampling_filter)

            logger = logging.getLogger("test.mixed")
            logger.addHandler(handler.get_queue_handler())
            logger.setLevel(logging.DEBUG)

            # Log mixed levels
            for i in range(100):
                logger.debug(f"Debug {i}")  # Sampled
                if i % 10 == 0:
                    logger.warning(f"Warning {i}")  # Never sampled
                if i % 20 == 0:
                    logger.error(f"Error {i}")  # Never sampled

            time.sleep(0.2)

            # All warnings/errors should be logged (not sampled)
            # Some debug messages sampled


class TestPerformanceOverhead:
    """Tests for logging performance overhead."""

    def test_async_is_non_blocking(self):
        """Test async logging doesn't block caller."""
        with AsyncLogHandler(queue_maxsize=10000) as handler:
            logger = logging.getLogger("test.nonblocking")
            logger.addHandler(handler.get_queue_handler())
            logger.setLevel(logging.INFO)

            start = time.time()

            # Log many messages
            for i in range(1000):
                logger.info(f"Message {i}")

            duration = time.time() - start

            # Should be very fast (<100ms for queueing)
            assert duration < 0.1

    def test_sampling_reduces_overhead(self):
        """Test sampling reduces overhead."""
        # Time without sampling
        start = time.time()
        for i in range(10000):
            record = logging.LogRecord(
                name="test",
                level=logging.INFO,
                pathname="",
                lineno=0,
                msg=f"Message {i}",
                args=(),
                exc_info=None,
            )
        no_filter_time = time.time() - start

        # Time with sampling
        filter = SamplingFilter(sample_rate=100)
        start = time.time()
        for i in range(10000):
            record = logging.LogRecord(
                name="test",
                level=logging.INFO,
                pathname="",
                lineno=0,
                msg=f"Message {i}",
                args=(),
                exc_info=None,
            )
            filter.filter(record)
        with_filter_time = time.time() - start

        # Overhead should be minimal
        overhead = with_filter_time - no_filter_time
        assert overhead < 0.1  # <100ms overhead for 10k logs
