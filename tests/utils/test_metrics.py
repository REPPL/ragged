"""Tests for metrics collection system.

v0.2.9: Tests for observability metrics.
"""

import pytest
import time
from unittest.mock import patch, Mock

from src.utils.metrics import (
    MetricsCollector,
    MetricSnapshot,
    get_metrics_collector,
    timer,
)


@pytest.fixture(autouse=True)
def reset_collector():
    """Reset singleton before each test."""
    MetricsCollector.reset_instance()
    yield
    MetricsCollector.reset_instance()


@pytest.fixture
def collector():
    """Create fresh collector instance."""
    return MetricsCollector()


class TestMetricsCollector:
    """Tests for MetricsCollector."""

    def test_initialization(self, collector):
        """Test collector initializes correctly."""
        assert len(collector.counters) == 0
        assert len(collector.gauges) == 0
        assert len(collector.timers) == 0
        assert len(collector.history) == 0

    def test_singleton_pattern(self):
        """Test singleton pattern works."""
        c1 = get_metrics_collector()
        c2 = get_metrics_collector()
        assert c1 is c2

    def test_increment_counter(self, collector):
        """Test incrementing counters."""
        collector.increment_counter("queries")
        assert collector.counters["queries"] == 1

        collector.increment_counter("queries", 5)
        assert collector.counters["queries"] == 6

    def test_set_gauge(self, collector):
        """Test setting gauges."""
        collector.set_gauge("temperature", 72.5)
        assert collector.gauges["temperature"] == 72.5

        collector.set_gauge("temperature", 75.0)
        assert collector.gauges["temperature"] == 75.0

    def test_record_timer(self, collector):
        """Test recording timers."""
        collector.record_timer("query_time", 0.123)
        collector.record_timer("query_time", 0.456)

        assert len(collector.timers["query_time"]) == 2
        assert 0.123 in collector.timers["query_time"]
        assert 0.456 in collector.timers["query_time"]

    def test_timer_limit(self, collector):
        """Test timer values are limited."""
        # Record 150 values
        for i in range(150):
            collector.record_timer("test", i * 0.001)

        # Should keep only last 100
        assert len(collector.timers["test"]) == 100

    @patch('psutil.cpu_percent')
    @patch('psutil.virtual_memory')
    @patch('psutil.disk_usage')
    def test_collect_system_metrics(
        self, mock_disk, mock_memory, mock_cpu, collector
    ):
        """Test system metrics collection."""
        mock_cpu.return_value = 45.5
        mock_memory.return_value = Mock(
            percent=60.0,
            available=4 * 1024 ** 3,
            total=16 * 1024 ** 3
        )
        mock_disk.return_value = Mock(
            percent=50.0,
            free=100 * 1024 ** 3
        )

        metrics = collector.collect_system_metrics()

        assert metrics["cpu_percent"] == 45.5
        assert metrics["memory_percent"] == 60.0
        assert metrics["memory_available_mb"] == 4096.0
        assert metrics["disk_percent"] == 50.0

    def test_collect_application_metrics(self, collector):
        """Test application metrics collection."""
        # Set some metrics
        collector.increment_counter("queries", 10)
        collector.set_gauge("cache_size", 42.0)
        collector.record_timer("latency", 0.123)

        metrics = collector.collect_application_metrics()

        assert metrics.get("counter_queries") == 10
        assert metrics.get("gauge_cache_size") == 42.0
        assert "timer_latency_avg" in metrics

    def test_collect_metrics(self, collector):
        """Test complete metrics collection."""
        metrics = collector.collect_metrics()

        assert "timestamp" in metrics
        assert "cpu_percent" in metrics
        assert "memory_percent" in metrics

    def test_history_tracking(self, collector):
        """Test metric history is tracked."""
        # Collect metrics twice
        collector.collect_metrics()
        time.sleep(0.1)
        collector.collect_metrics()

        assert len(collector.history) == 2
        assert isinstance(collector.history[0], MetricSnapshot)

    def test_history_limit(self):
        """Test history is limited to maxsize."""
        collector = MetricsCollector(history_size=5)

        # Collect 10 metrics
        for _ in range(10):
            collector.collect_metrics()

        # Should keep only last 5
        assert len(collector.history) == 5

    def test_get_history(self, collector):
        """Test getting historical metrics."""
        # Collect some metrics
        for _ in range(5):
            collector.collect_metrics()
            time.sleep(0.05)

        # Get all history
        history = collector.get_history()
        assert len(history) == 5

        # Get recent history (last 0.2 seconds)
        recent = collector.get_history(duration_seconds=0.2)
        assert len(recent) <= 5

    def test_get_metric_trend(self, collector):
        """Test getting metric trend."""
        # Record some metrics
        for i in range(5):
            collector.set_gauge("test_metric", float(i))
            collector.collect_metrics()

        trend = collector.get_metric_trend("gauge_test_metric")

        assert len(trend) == 5
        assert trend[-1] == 4.0  # Last value

    def test_reset_metrics(self, collector):
        """Test resetting all metrics."""
        collector.increment_counter("test", 10)
        collector.set_gauge("gauge", 5.0)
        collector.record_timer("timer", 0.1)
        collector.collect_metrics()

        collector.reset_metrics()

        assert len(collector.counters) == 0
        assert len(collector.gauges) == 0
        assert len(collector.timers) == 0
        assert len(collector.history) == 0

    def test_export_prometheus(self, collector):
        """Test Prometheus export format."""
        collector.increment_counter("requests", 100)
        collector.set_gauge("temperature", 72.5)

        output = collector.export_prometheus()

        assert "ragged_" in output
        assert "100" in output or "72.5" in output


class TestTimerContextManager:
    """Tests for timer context manager."""

    def test_timer_context_manager(self, collector):
        """Test timer context manager records duration."""
        with timer("test_operation"):
            time.sleep(0.1)

        assert "test_operation" in collector.timers
        assert len(collector.timers["test_operation"]) == 1
        assert collector.timers["test_operation"][0] >= 0.1

    def test_timer_multiple_uses(self, collector):
        """Test timer can be used multiple times."""
        for _ in range(3):
            with timer("operation"):
                time.sleep(0.01)

        assert len(collector.timers["operation"]) == 3

    def test_timer_exception_handling(self, collector):
        """Test timer records duration even on exception."""
        try:
            with timer("failing_operation"):
                raise ValueError("Test error")
        except ValueError:
            pass

        assert "failing_operation" in collector.timers


class TestThreadSafety:
    """Tests for thread safety."""

    def test_concurrent_counter_increments(self, collector):
        """Test concurrent counter increments are safe."""
        import threading

        def increment():
            for _ in range(100):
                collector.increment_counter("concurrent")

        threads = [threading.Thread(target=increment) for _ in range(4)]

        for t in threads:
            t.start()

        for t in threads:
            t.join()

        # Should be exactly 400
        assert collector.counters["concurrent"] == 400

    def test_concurrent_gauge_sets(self, collector):
        """Test concurrent gauge sets are safe."""
        import threading

        def set_gauge(value):
            for _ in range(10):
                collector.set_gauge("concurrent_gauge", value)

        threads = [threading.Thread(target=set_gauge, args=(i,)) for i in range(4)]

        for t in threads:
            t.start()

        for t in threads:
            t.join()

        # Should have some value (race condition, but no crash)
        assert "concurrent_gauge" in collector.gauges

    def test_concurrent_timer_records(self, collector):
        """Test concurrent timer records are safe."""
        import threading

        def record_timer():
            for i in range(10):
                collector.record_timer("concurrent_timer", i * 0.001)

        threads = [threading.Thread(target=record_timer) for _ in range(4)]

        for t in threads:
            t.start()

        for t in threads:
            t.join()

        # Should have 40 values
        assert len(collector.timers["concurrent_timer"]) == 40


class TestMetricSnapshot:
    """Tests for MetricSnapshot dataclass."""

    def test_metric_snapshot(self):
        """Test creating metric snapshot."""
        metrics = {"cpu": 50.0, "memory": 60.0}
        snapshot = MetricSnapshot(timestamp=time.time(), metrics=metrics)

        assert snapshot.timestamp > 0
        assert snapshot.metrics == metrics


class TestIntegrationScenarios:
    """Integration tests for realistic scenarios."""

    def test_complete_monitoring_workflow(self, collector):
        """Test complete monitoring workflow."""
        # 1. Record some operations
        collector.increment_counter("queries", 10)
        collector.increment_counter("errors", 2)

        # 2. Record timings
        with timer("query_execution"):
            time.sleep(0.05)

        # 3. Set gauges
        collector.set_gauge("active_users", 5.0)

        # 4. Collect metrics
        metrics = collector.collect_metrics()

        # 5. Verify metrics
        assert metrics["counter_queries"] == 10
        assert metrics["counter_errors"] == 2
        assert metrics["gauge_active_users"] == 5.0
        assert "timer_query_execution_avg" in metrics

        # 6. Export Prometheus
        prometheus_output = collector.export_prometheus()
        assert "ragged_" in prometheus_output
