"""Metrics collection system for observability.

v0.2.9: Unified metrics collection for monitoring and dashboards.
"""

import threading
import time
from collections import deque
from dataclasses import dataclass
from typing import Any, Optional

import psutil  # type: ignore[import-untyped]

from src.utils.logging import get_logger

logger = get_logger(__name__)


@dataclass
class MetricSnapshot:
    """Snapshot of metrics at a point in time."""

    timestamp: float
    metrics: dict[str, Any]


class MetricsCollector:
    """Centralized metrics collection system.

    Features:
    - System resource metrics (CPU, memory, disk)
    - Application metrics (cache, embedder, queries)
    - Time-series storage for trends
    - Thread-safe metric updates

    Example:
        >>> collector = get_metrics_collector()
        >>> collector.record_metric("query_latency", 0.123)
        >>> metrics = collector.collect_metrics()
    """

    _instance: Optional['MetricsCollector'] = None
    _lock = threading.Lock()

    def __init__(self, history_size: int = 100):
        """Initialize metrics collector.

        Args:
            history_size: Number of historical snapshots to keep
        """
        self.history_size = history_size
        self.history: deque = deque(maxlen=history_size)

        # Metric counters
        self.counters: dict[str, int] = {}
        self.gauges: dict[str, float] = {}
        self.timers: dict[str, list[float]] = {}

        # Locks for thread safety
        self._counters_lock = threading.Lock()
        self._gauges_lock = threading.Lock()
        self._timers_lock = threading.Lock()

        logger.debug("MetricsCollector initialized")

    @classmethod
    def get_instance(cls) -> 'MetricsCollector':
        """Get singleton instance.

        Returns:
            Singleton MetricsCollector
        """
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance

    @classmethod
    def reset_instance(cls) -> None:
        """Reset singleton (for testing)."""
        with cls._lock:
            cls._instance = None

    def increment_counter(self, name: str, value: int = 1) -> None:
        """Increment a counter metric.

        Args:
            name: Counter name
            value: Increment value
        """
        with self._counters_lock:
            self.counters[name] = self.counters.get(name, 0) + value

    def set_gauge(self, name: str, value: float) -> None:
        """Set a gauge metric.

        Args:
            name: Gauge name
            value: Gauge value
        """
        with self._gauges_lock:
            self.gauges[name] = value

    def record_timer(self, name: str, duration: float) -> None:
        """Record a timing metric.

        Args:
            name: Timer name
            duration: Duration in seconds
        """
        with self._timers_lock:
            if name not in self.timers:
                self.timers[name] = []
            self.timers[name].append(duration)

            # Keep only last 100 values
            if len(self.timers[name]) > 100:
                self.timers[name] = self.timers[name][-100:]

    def collect_system_metrics(self) -> dict[str, Any]:
        """Collect system resource metrics.

        Returns:
            System metrics dictionary
        """
        cpu_percent = psutil.cpu_percent(interval=0.1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')

        return {
            "cpu_percent": cpu_percent,
            "memory_percent": memory.percent,
            "memory_available_mb": memory.available / (1024 ** 2),
            "memory_total_mb": memory.total / (1024 ** 2),
            "disk_percent": disk.percent,
            "disk_free_gb": disk.free / (1024 ** 3),
        }

    def collect_application_metrics(self) -> dict[str, Any]:
        """Collect application-specific metrics.

        Returns:
            Application metrics dictionary
        """
        metrics = {}

        # Cache metrics
        try:
            from src.retrieval.cache import get_query_cache
            cache = get_query_cache()
            cache_stats = cache.stats()
            metrics["cache_hit_rate"] = cache_stats.get("hit_rate", 0.0)
            metrics["cache_size"] = cache_stats.get("size", 0)
        except Exception as e:
            logger.debug(f"Could not collect cache metrics: {e}")
            metrics["cache_hit_rate"] = 0.0
            metrics["cache_size"] = 0

        # Resource governor metrics
        try:
            from src.utils.resource_governor import get_governor
            governor = get_governor()
            gov_stats = governor.get_stats()
            metrics["active_operations"] = gov_stats.get("active_reservations", 0)
            metrics["queued_operations"] = gov_stats.get("queued_requests", 0)
        except Exception as e:
            logger.debug(f"Could not collect governor metrics: {e}")
            metrics["active_operations"] = 0
            metrics["queued_operations"] = 0

        # Async logging metrics
        try:
            from src.utils.async_logging import get_async_handler
            async_handler = get_async_handler()
            log_stats = async_handler.get_stats()
            metrics["log_queue_size"] = log_stats.get("queue_size", 0)
            metrics["logs_dropped"] = log_stats.get("logs_dropped", 0)
        except Exception as e:
            logger.debug(f"Could not collect logging metrics: {e}")
            metrics["log_queue_size"] = 0
            metrics["logs_dropped"] = 0

        # Add counters
        with self._counters_lock:
            metrics.update({f"counter_{k}": v for k, v in self.counters.items()})

        # Add gauges
        with self._gauges_lock:
            metrics.update({f"gauge_{k}": v for k, v in self.gauges.items()})

        # Add timer statistics
        with self._timers_lock:
            for name, values in self.timers.items():
                if values:
                    metrics[f"timer_{name}_avg"] = sum(values) / len(values)
                    metrics[f"timer_{name}_min"] = min(values)
                    metrics[f"timer_{name}_max"] = max(values)

        return metrics

    def collect_metrics(self) -> dict[str, Any]:
        """Collect all metrics.

        Returns:
            Complete metrics dictionary
        """
        metrics = {
            "timestamp": time.time(),
            **self.collect_system_metrics(),
            **self.collect_application_metrics(),
        }

        # Add to history
        snapshot = MetricSnapshot(
            timestamp=metrics["timestamp"],
            metrics=metrics
        )
        self.history.append(snapshot)

        return metrics

    def get_history(self, duration_seconds: float | None = None) -> list[MetricSnapshot]:
        """Get historical metrics.

        Args:
            duration_seconds: Only return metrics from last N seconds (None = all)

        Returns:
            List of metric snapshots
        """
        if duration_seconds is None:
            return list(self.history)

        cutoff_time = time.time() - duration_seconds
        return [
            snapshot for snapshot in self.history
            if snapshot.timestamp >= cutoff_time
        ]

    def get_metric_trend(self, metric_name: str, duration_seconds: float = 60.0) -> list[float]:
        """Get trend for a specific metric.

        Args:
            metric_name: Name of metric
            duration_seconds: Time window

        Returns:
            List of values over time
        """
        history = self.get_history(duration_seconds)
        return [
            snapshot.metrics.get(metric_name, 0.0)
            for snapshot in history
        ]

    def reset_metrics(self) -> None:
        """Reset all metrics."""
        with self._counters_lock:
            self.counters.clear()

        with self._gauges_lock:
            self.gauges.clear()

        with self._timers_lock:
            self.timers.clear()

        self.history.clear()

        logger.debug("Metrics reset")

    def export_prometheus(self) -> str:
        """Export metrics in Prometheus format.

        Returns:
            Prometheus-formatted metrics string
        """
        metrics = self.collect_metrics()
        lines = []

        for key, value in metrics.items():
            if key == "timestamp":
                continue

            # Convert to Prometheus format
            metric_name = f"ragged_{key.replace('.', '_')}"

            if isinstance(value, (int, float)):
                lines.append(f"{metric_name} {value}")

        return "\n".join(lines)


# Singleton accessor
def get_metrics_collector() -> MetricsCollector:
    """Get singleton MetricsCollector.

    Returns:
        Singleton MetricsCollector

    Example:
        >>> collector = get_metrics_collector()
        >>> collector.increment_counter("queries")
    """
    return MetricsCollector.get_instance()


# Context manager for timing
class timer:
    """Context manager for timing operations.

    Example:
        >>> with timer("query_execution"):
        ...     execute_query()
    """

    def __init__(self, name: str):
        """Initialize timer.

        Args:
            name: Timer name
        """
        self.name = name
        self.start_time = 0.0
        self.collector = get_metrics_collector()

    def __enter__(self):
        """Start timing."""
        self.start_time = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Record duration."""
        duration = time.time() - self.start_time
        self.collector.record_timer(self.name, duration)
        return False
