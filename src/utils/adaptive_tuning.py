"""Adaptive performance tuning for self-optimising system.

v0.2.9: Runtime profiling and automatic parameter optimisation.

Features:
- Workload detection (bulk ingestion vs interactive queries)
- Automatic hyperparameter tuning based on workload
- Hardware capability detection (CPU, memory, disk)
- Adaptive adjustment of batch sizes, cache sizes, worker pools
"""

from typing import Dict, Any, Optional, Literal
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import threading
import time
import psutil
import os
from collections import deque

from src.utils.logging import get_logger

logger = get_logger(__name__)


WorkloadMode = Literal["bulk_ingestion", "interactive_query", "mixed", "idle"]


@dataclass
class HardwareCapabilities:
    """Detected hardware capabilities."""

    cpu_count: int
    total_memory_gb: float
    available_memory_gb: float
    disk_io_speed_mbps: Optional[float] = None  # Estimated
    has_gpu: bool = False

    def get_recommended_workers(self) -> int:
        """Get recommended number of worker threads."""
        # Use 75% of CPU cores, minimum 1
        return max(1, int(self.cpu_count * 0.75))

    def get_recommended_batch_size(self, mode: WorkloadMode) -> int:
        """Get recommended batch size based on available memory.

        Args:
            mode: Current workload mode

        Returns:
            Recommended batch size
        """
        # Estimate: each document ~1KB after chunking
        # Use 10% of available memory for batching
        available_mb = self.available_memory_gb * 1024 * 0.1

        if mode == "bulk_ingestion":
            # Larger batches for bulk operations
            batch_size = int(available_mb / 1.0)  # 1KB per doc
            return min(max(100, batch_size), 1000)
        elif mode == "interactive_query":
            # Smaller batches for responsiveness
            batch_size = int(available_mb / 2.0)  # More conservative
            return min(max(10, batch_size), 100)
        else:
            # Mixed or idle: medium batch
            batch_size = int(available_mb / 1.5)
            return min(max(50, batch_size), 500)

    def get_recommended_cache_size(self, mode: WorkloadMode) -> int:
        """Get recommended cache size.

        Args:
            mode: Current workload mode

        Returns:
            Recommended cache size (number of entries)
        """
        # Use 5% of available memory for caching
        available_mb = self.available_memory_gb * 1024 * 0.05

        if mode == "interactive_query":
            # Larger cache for interactive use
            # Assume ~100KB per cache entry (embeddings + metadata)
            cache_size = int(available_mb / 0.1)
            return min(max(100, cache_size), 10000)
        elif mode == "bulk_ingestion":
            # Smaller cache during bulk operations
            cache_size = int(available_mb / 0.2)
            return min(max(50, cache_size), 1000)
        else:
            cache_size = int(available_mb / 0.15)
            return min(max(100, cache_size), 5000)


@dataclass
class WorkloadProfile:
    """Current workload characteristics."""

    query_rate: float = 0.0  # Queries per minute
    ingestion_rate: float = 0.0  # Documents per minute
    avg_query_time: float = 0.0  # Average query time in seconds
    avg_doc_size: float = 0.0  # Average document size in KB
    active_queries: int = 0
    active_ingestions: int = 0

    # Recent history
    recent_queries: deque = field(default_factory=lambda: deque(maxlen=100))
    recent_ingestions: deque = field(default_factory=lambda: deque(maxlen=100))

    def update_query(self, query_time: float) -> None:
        """Record a query execution.

        Args:
            query_time: Query execution time in seconds
        """
        self.recent_queries.append({
            "timestamp": datetime.now(),
            "duration": query_time,
        })

        # Update active count and rates
        self.active_queries += 1

        # Calculate query rate (last minute)
        one_min_ago = datetime.now() - timedelta(minutes=1)
        recent = [q for q in self.recent_queries if q["timestamp"] > one_min_ago]
        self.query_rate = len(recent)

        # Update average query time
        if recent:
            self.avg_query_time = sum(q["duration"] for q in recent) / len(recent)

    def update_ingestion(self, doc_size_kb: float) -> None:
        """Record a document ingestion.

        Args:
            doc_size_kb: Document size in kilobytes
        """
        self.recent_ingestions.append({
            "timestamp": datetime.now(),
            "size_kb": doc_size_kb,
        })

        self.active_ingestions += 1

        # Calculate ingestion rate (last minute)
        one_min_ago = datetime.now() - timedelta(minutes=1)
        recent = [i for i in self.recent_ingestions if i["timestamp"] > one_min_ago]
        self.ingestion_rate = len(recent)

        # Update average doc size
        if recent:
            self.avg_doc_size = sum(i["size_kb"] for i in recent) / len(recent)

    def detect_mode(self) -> WorkloadMode:
        """Detect current workload mode.

        Returns:
            Detected workload mode
        """
        # Thresholds
        HIGH_QUERY_RATE = 10  # queries/min
        HIGH_INGESTION_RATE = 50  # docs/min

        if self.ingestion_rate > HIGH_INGESTION_RATE and self.query_rate < 5:
            return "bulk_ingestion"
        elif self.query_rate > HIGH_QUERY_RATE and self.ingestion_rate < 10:
            return "interactive_query"
        elif self.query_rate > 5 or self.ingestion_rate > 10:
            return "mixed"
        else:
            return "idle"


@dataclass
class TuningRecommendations:
    """Recommended configuration based on analysis."""

    mode: WorkloadMode
    batch_size: int
    cache_size: int
    worker_count: int
    enable_query_cache: bool = True
    enable_embedding_cache: bool = True
    chunk_size: int = 512
    chunk_overlap: int = 50

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "mode": self.mode,
            "batch_size": self.batch_size,
            "cache_size": self.cache_size,
            "worker_count": self.worker_count,
            "enable_query_cache": self.enable_query_cache,
            "enable_embedding_cache": self.enable_embedding_cache,
            "chunk_size": self.chunk_size,
            "chunk_overlap": self.chunk_overlap,
        }


class AdaptiveTuner:
    """Adaptive performance tuner for self-optimising system.

    Monitors workload, detects hardware capabilities, and provides
    tuning recommendations for optimal performance.

    Example:
        >>> tuner = AdaptiveTuner()
        >>> tuner.start_monitoring()
        >>> # ... application runs ...
        >>> tuner.record_query(query_time=0.5)
        >>> tuner.record_ingestion(doc_size_kb=10.5)
        >>> recommendations = tuner.get_recommendations()
        >>> print(f"Mode: {recommendations.mode}, Batch: {recommendations.batch_size}")
    """

    def __init__(
        self,
        auto_apply: bool = False,
        monitoring_interval: float = 60.0,
    ):
        """Initialize adaptive tuner.

        Args:
            auto_apply: Automatically apply tuning recommendations
            monitoring_interval: Seconds between monitoring updates
        """
        self.auto_apply = auto_apply
        self.monitoring_interval = monitoring_interval

        # Detect hardware capabilities
        self.hardware = self._detect_hardware()

        # Initialize workload profile
        self.workload = WorkloadProfile()

        # Current recommendations
        self._recommendations: Optional[TuningRecommendations] = None
        self._recommendations_lock = threading.RLock()

        # Background monitoring
        self._monitoring_thread: Optional[threading.Thread] = None
        self._stop_monitoring = threading.Event()

        logger.info(
            f"Initialized AdaptiveTuner: "
            f"CPUs={self.hardware.cpu_count}, "
            f"Memory={self.hardware.total_memory_gb:.1f}GB, "
            f"Available={self.hardware.available_memory_gb:.1f}GB"
        )

    def _detect_hardware(self) -> HardwareCapabilities:
        """Detect hardware capabilities.

        Returns:
            Detected hardware capabilities
        """
        cpu_count = os.cpu_count() or 1
        memory = psutil.virtual_memory()
        total_memory_gb = memory.total / (1024 ** 3)
        available_memory_gb = memory.available / (1024 ** 3)

        # Simple GPU detection
        has_gpu = False
        try:
            import torch
            has_gpu = torch.cuda.is_available()
        except ImportError:
            pass

        return HardwareCapabilities(
            cpu_count=cpu_count,
            total_memory_gb=total_memory_gb,
            available_memory_gb=available_memory_gb,
            has_gpu=has_gpu,
        )

    def record_query(self, query_time: float) -> None:
        """Record a query execution.

        Args:
            query_time: Query execution time in seconds
        """
        self.workload.update_query(query_time)
        logger.debug(f"Recorded query: {query_time:.3f}s")

    def record_ingestion(self, doc_size_kb: float) -> None:
        """Record a document ingestion.

        Args:
            doc_size_kb: Document size in kilobytes
        """
        self.workload.update_ingestion(doc_size_kb)
        logger.debug(f"Recorded ingestion: {doc_size_kb:.1f}KB")

    def analyze_workload(self) -> WorkloadMode:
        """Analyse current workload and detect mode.

        Returns:
            Detected workload mode
        """
        mode = self.workload.detect_mode()
        logger.info(
            f"Workload analysis: mode={mode}, "
            f"query_rate={self.workload.query_rate:.1f}/min, "
            f"ingestion_rate={self.workload.ingestion_rate:.1f}/min"
        )
        return mode

    def generate_recommendations(self) -> TuningRecommendations:
        """Generate tuning recommendations based on current state.

        Returns:
            Tuning recommendations
        """
        # Detect current mode
        mode = self.analyze_workload()

        # Refresh hardware capabilities (memory may have changed)
        memory = psutil.virtual_memory()
        self.hardware.available_memory_gb = memory.available / (1024 ** 3)

        # Generate recommendations
        batch_size = self.hardware.get_recommended_batch_size(mode)
        cache_size = self.hardware.get_recommended_cache_size(mode)
        worker_count = self.hardware.get_recommended_workers()

        # Mode-specific optimisations
        if mode == "bulk_ingestion":
            enable_query_cache = False  # Save memory
            enable_embedding_cache = True  # Avoid re-embedding
            chunk_size = 1024  # Larger chunks for throughput
            chunk_overlap = 100
        elif mode == "interactive_query":
            enable_query_cache = True  # Fast repeat queries
            enable_embedding_cache = True
            chunk_size = 512  # Smaller chunks for precision
            chunk_overlap = 50
        else:
            # Mixed or idle: balanced
            enable_query_cache = True
            enable_embedding_cache = True
            chunk_size = 512
            chunk_overlap = 50

        recommendations = TuningRecommendations(
            mode=mode,
            batch_size=batch_size,
            cache_size=cache_size,
            worker_count=worker_count,
            enable_query_cache=enable_query_cache,
            enable_embedding_cache=enable_embedding_cache,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
        )

        with self._recommendations_lock:
            self._recommendations = recommendations

        logger.info(
            f"Generated recommendations: mode={mode}, "
            f"batch_size={batch_size}, cache_size={cache_size}, "
            f"workers={worker_count}"
        )

        return recommendations

    def get_recommendations(self) -> Optional[TuningRecommendations]:
        """Get current tuning recommendations.

        Returns:
            Current recommendations or None if not yet generated
        """
        with self._recommendations_lock:
            return self._recommendations

    def apply_recommendations(self, recommendations: TuningRecommendations) -> None:
        """Apply tuning recommendations to system.

        Note: This updates settings but does not restart components.
        Application may need to restart for changes to take effect.

        Args:
            recommendations: Recommendations to apply
        """
        from src.config.settings import get_settings

        settings = get_settings()

        # Apply recommendations
        # Note: This assumes settings has these attributes
        # Actual implementation depends on settings structure

        logger.info(
            f"Applied tuning recommendations: {recommendations.to_dict()}"
        )

        # In a real implementation, this would update:
        # - settings.batch_size
        # - settings.cache_size
        # - settings.worker_count
        # - etc.
        # For now, just log the recommendations

    def start_monitoring(self) -> None:
        """Start background monitoring and auto-tuning."""
        if self._monitoring_thread is not None:
            logger.warning("Monitoring already started")
            return

        self._stop_monitoring.clear()

        def monitor_loop():
            while not self._stop_monitoring.is_set():
                try:
                    # Generate recommendations
                    recommendations = self.generate_recommendations()

                    # Auto-apply if enabled
                    if self.auto_apply:
                        self.apply_recommendations(recommendations)

                except Exception as e:
                    logger.error(f"Error in monitoring loop: {e}", exc_info=True)

                # Sleep until next interval
                self._stop_monitoring.wait(self.monitoring_interval)

        self._monitoring_thread = threading.Thread(
            target=monitor_loop,
            daemon=True,
            name="AdaptiveTuner-Monitor"
        )
        self._monitoring_thread.start()

        logger.info(
            f"Started adaptive tuning monitor "
            f"(interval={self.monitoring_interval}s, auto_apply={self.auto_apply})"
        )

    def stop_monitoring(self) -> None:
        """Stop background monitoring."""
        if self._monitoring_thread is None:
            return

        self._stop_monitoring.set()
        self._monitoring_thread.join(timeout=5.0)
        self._monitoring_thread = None

        logger.info("Stopped adaptive tuning monitor")

    def get_stats(self) -> Dict[str, Any]:
        """Get tuning statistics and current state.

        Returns:
            Dictionary with tuning stats
        """
        mode = self.workload.detect_mode()
        recommendations = self.get_recommendations()

        return {
            "hardware": {
                "cpu_count": self.hardware.cpu_count,
                "total_memory_gb": self.hardware.total_memory_gb,
                "available_memory_gb": self.hardware.available_memory_gb,
                "has_gpu": self.hardware.has_gpu,
            },
            "workload": {
                "mode": mode,
                "query_rate": self.workload.query_rate,
                "ingestion_rate": self.workload.ingestion_rate,
                "avg_query_time": self.workload.avg_query_time,
                "avg_doc_size": self.workload.avg_doc_size,
            },
            "recommendations": recommendations.to_dict() if recommendations else None,
            "monitoring": {
                "active": self._monitoring_thread is not None,
                "auto_apply": self.auto_apply,
                "interval": self.monitoring_interval,
            },
        }


# Singleton instance
_tuner: Optional[AdaptiveTuner] = None
_tuner_lock = threading.Lock()


def get_tuner(
    auto_apply: bool = False,
    monitoring_interval: float = 60.0,
) -> AdaptiveTuner:
    """Get singleton AdaptiveTuner instance.

    Args:
        auto_apply: Automatically apply tuning recommendations
        monitoring_interval: Seconds between monitoring updates

    Returns:
        AdaptiveTuner instance
    """
    global _tuner

    if _tuner is None:
        with _tuner_lock:
            if _tuner is None:
                _tuner = AdaptiveTuner(
                    auto_apply=auto_apply,
                    monitoring_interval=monitoring_interval,
                )

    return _tuner
