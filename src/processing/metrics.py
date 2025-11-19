"""
Processing metrics collection and tracking for routing decisions.

This module collects and tracks metrics about document processing,
routing decisions, quality scores, and processing performance. Metrics
are used to monitor system behaviour and optimise routing strategies.

v0.3.4b: Intelligent Routing
"""

from __future__ import annotations

import json
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

from src.processing.router import ProcessingRoute
from src.utils.logging import get_logger

logger = get_logger(__name__)


@dataclass
class RoutingMetric:
    """
    Single routing decision metric.

    Attributes:
        timestamp: When routing occurred
        file_name: Name of processed file
        file_size: Size of file in bytes
        processor: Selected processor name
        quality_score: Overall quality score
        is_born_digital: Whether document was born-digital
        is_scanned: Whether document was scanned
        quality_tier: Quality tier (high/medium/low)
        processing_mode: Processing mode used
        has_tables: Whether document had tables
        layout_complexity: Layout complexity score
        estimated_time: Estimated processing time
        actual_time: Actual processing time (if available)
        success: Whether processing succeeded
        error_message: Error message if processing failed
        metadata: Additional metric metadata
    """

    timestamp: str
    file_name: str
    file_size: int
    processor: str
    quality_score: float
    is_born_digital: bool
    is_scanned: bool
    quality_tier: str
    processing_mode: str
    has_tables: bool
    layout_complexity: float
    estimated_time: float
    actual_time: Optional[float] = None
    success: bool = True
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class MetricsSummary:
    """
    Aggregated metrics summary.

    Attributes:
        total_documents: Total documents processed
        by_processor: Count by processor name
        by_quality_tier: Count by quality tier
        avg_quality_score: Average quality score
        avg_processing_time: Average processing time
        success_rate: Processing success rate (0-1)
        born_digital_rate: Rate of born-digital documents (0-1)
        time_range: Time range of metrics (start, end)
    """

    total_documents: int
    by_processor: Dict[str, int]
    by_quality_tier: Dict[str, int]
    avg_quality_score: float
    avg_processing_time: float
    success_rate: float
    born_digital_rate: float
    time_range: tuple[str, str]


class ProcessingMetrics:
    """
    Collect and manage processing metrics.

    This class tracks routing decisions, quality scores, processing times,
    and success rates. Metrics can be exported for analysis and monitoring.

    Example:
        >>> metrics = ProcessingMetrics(retention_days=30)
        >>> metrics.record_routing(route)
        >>> metrics.record_processing_result(route, success=True, time=2.5)
        >>> summary = metrics.get_summary()
        >>> print(f"Success rate: {summary.success_rate:.1%}")
    """

    def __init__(
        self,
        retention_days: int = 30,
        storage_dir: Optional[Path] = None,
        auto_save: bool = True,
    ):
        """
        Initialise metrics collection.

        Args:
            retention_days: Days to retain metrics
            storage_dir: Directory for metrics storage (None = no persistence)
            auto_save: Automatically save metrics after recording
        """
        self.retention_days = retention_days
        self.storage_dir = storage_dir
        self.auto_save = auto_save

        self._metrics: List[RoutingMetric] = []
        self._start_time = time.time()

        # Create storage directory if needed
        if self.storage_dir:
            self.storage_dir.mkdir(parents=True, exist_ok=True)
            self._load_metrics()

        logger.debug(
            f"Metrics collection initialised: "
            f"retention={retention_days} days, "
            f"storage={storage_dir}, auto_save={auto_save}"
        )

    def record_routing(self, route: ProcessingRoute) -> None:
        """
        Record a routing decision.

        Args:
            route: Processing route decision
        """
        metric = RoutingMetric(
            timestamp=datetime.now().isoformat(),
            file_name=route.quality.metadata.get("file_name", "unknown"),
            file_size=route.quality.metadata.get("file_size", 0),
            processor=route.processor,
            quality_score=route.quality.overall_score,
            is_born_digital=route.quality.is_born_digital,
            is_scanned=route.quality.is_scanned,
            quality_tier=route.config.options.get("quality_tier", "unknown"),
            processing_mode=route.config.options.get("processing_mode", "standard"),
            has_tables=route.quality.has_tables,
            layout_complexity=route.quality.layout_complexity,
            estimated_time=route.estimated_time,
        )

        self._metrics.append(metric)

        logger.debug(
            f"Recorded routing metric: {metric.file_name} → {metric.processor} "
            f"(quality={metric.quality_score:.2f})"
        )

        if self.auto_save:
            self._save_metrics()

    def record_processing_result(
        self,
        route: ProcessingRoute,
        success: bool,
        processing_time: Optional[float] = None,
        error_message: Optional[str] = None,
    ) -> None:
        """
        Record processing result for a route.

        Updates the most recent metric for the file with actual results.

        Args:
            route: Processing route that was executed
            success: Whether processing succeeded
            processing_time: Actual processing time in seconds
            error_message: Error message if processing failed
        """
        file_name = route.quality.metadata.get("file_name", "unknown")

        # Find most recent metric for this file
        for metric in reversed(self._metrics):
            if metric.file_name == file_name:
                metric.success = success
                metric.actual_time = processing_time
                metric.error_message = error_message

                logger.debug(
                    f"Updated processing result: {file_name} "
                    f"(success={success}, time={processing_time}s)"
                )

                if self.auto_save:
                    self._save_metrics()

                return

        logger.warning(f"No routing metric found for {file_name}")

    def get_summary(
        self,
        since: Optional[datetime] = None,
        processor: Optional[str] = None,
    ) -> MetricsSummary:
        """
        Get aggregated metrics summary.

        Args:
            since: Only include metrics since this time
            processor: Only include metrics for this processor

        Returns:
            Aggregated metrics summary
        """
        # Filter metrics
        metrics = self._metrics

        if since:
            metrics = [
                m for m in metrics
                if datetime.fromisoformat(m.timestamp) >= since
            ]

        if processor:
            metrics = [m for m in metrics if m.processor == processor]

        if not metrics:
            return MetricsSummary(
                total_documents=0,
                by_processor={},
                by_quality_tier={},
                avg_quality_score=0.0,
                avg_processing_time=0.0,
                success_rate=0.0,
                born_digital_rate=0.0,
                time_range=("", ""),
            )

        # Calculate aggregates
        total_documents = len(metrics)

        by_processor: Dict[str, int] = {}
        for m in metrics:
            by_processor[m.processor] = by_processor.get(m.processor, 0) + 1

        by_quality_tier: Dict[str, int] = {}
        for m in metrics:
            by_quality_tier[m.quality_tier] = by_quality_tier.get(m.quality_tier, 0) + 1

        avg_quality_score = sum(m.quality_score for m in metrics) / total_documents

        # Processing time (only for completed metrics)
        times = [m.actual_time for m in metrics if m.actual_time is not None]
        avg_processing_time = sum(times) / len(times) if times else 0.0

        successes = sum(1 for m in metrics if m.success)
        success_rate = successes / total_documents

        born_digital_count = sum(1 for m in metrics if m.is_born_digital)
        born_digital_rate = born_digital_count / total_documents

        time_range = (
            min(m.timestamp for m in metrics),
            max(m.timestamp for m in metrics),
        )

        return MetricsSummary(
            total_documents=total_documents,
            by_processor=by_processor,
            by_quality_tier=by_quality_tier,
            avg_quality_score=avg_quality_score,
            avg_processing_time=avg_processing_time,
            success_rate=success_rate,
            born_digital_rate=born_digital_rate,
            time_range=time_range,
        )

    def get_quality_distribution(
        self,
        bins: int = 10,
    ) -> Dict[str, int]:
        """
        Get quality score distribution.

        Args:
            bins: Number of bins for distribution

        Returns:
            Dictionary mapping bin ranges to counts
        """
        distribution: Dict[str, int] = {}

        for metric in self._metrics:
            # Determine bin
            bin_idx = min(int(metric.quality_score * bins), bins - 1)
            bin_start = bin_idx / bins
            bin_end = (bin_idx + 1) / bins
            bin_key = f"{bin_start:.2f}-{bin_end:.2f}"

            distribution[bin_key] = distribution.get(bin_key, 0) + 1

        return distribution

    def get_processing_times_by_tier(self) -> Dict[str, List[float]]:
        """
        Get processing times grouped by quality tier.

        Returns:
            Dictionary mapping tier name to list of processing times
        """
        times_by_tier: Dict[str, List[float]] = {
            "high": [],
            "medium": [],
            "low": [],
        }

        for metric in self._metrics:
            if metric.actual_time is not None:
                tier = metric.quality_tier
                if tier in times_by_tier:
                    times_by_tier[tier].append(metric.actual_time)

        return times_by_tier

    def export_json(self, file_path: Path) -> None:
        """
        Export metrics to JSON file.

        Args:
            file_path: Path to output JSON file
        """
        data = {
            "metadata": {
                "exported_at": datetime.now().isoformat(),
                "retention_days": self.retention_days,
                "total_metrics": len(self._metrics),
            },
            "metrics": [asdict(m) for m in self._metrics],
        }

        with open(file_path, "w") as f:
            json.dump(data, f, indent=2)

        logger.info(f"Exported {len(self._metrics)} metrics to {file_path}")

    def export_summary(self, file_path: Path) -> None:
        """
        Export summary statistics to JSON file.

        Args:
            file_path: Path to output JSON file
        """
        summary = self.get_summary()
        quality_dist = self.get_quality_distribution()
        times_by_tier = self.get_processing_times_by_tier()

        data = {
            "summary": asdict(summary),
            "quality_distribution": quality_dist,
            "processing_times_by_tier": {
                tier: {
                    "count": len(times),
                    "avg": sum(times) / len(times) if times else 0.0,
                    "min": min(times) if times else 0.0,
                    "max": max(times) if times else 0.0,
                }
                for tier, times in times_by_tier.items()
            },
        }

        with open(file_path, "w") as f:
            json.dump(data, f, indent=2)

        logger.info(f"Exported summary to {file_path}")

    def cleanup_old_metrics(self) -> int:
        """
        Remove metrics older than retention period.

        Returns:
            Number of metrics removed
        """
        if self.retention_days <= 0:
            return 0

        cutoff = datetime.now() - timedelta(days=self.retention_days)
        original_count = len(self._metrics)

        self._metrics = [
            m for m in self._metrics
            if datetime.fromisoformat(m.timestamp) >= cutoff
        ]

        removed = original_count - len(self._metrics)

        if removed > 0:
            logger.info(f"Cleaned up {removed} old metrics (retention={self.retention_days} days)")

            if self.auto_save:
                self._save_metrics()

        return removed

    def clear(self) -> None:
        """Clear all metrics."""
        count = len(self._metrics)
        self._metrics.clear()

        logger.info(f"Cleared {count} metrics")

        if self.auto_save:
            self._save_metrics()

    def _save_metrics(self) -> None:
        """Save metrics to storage directory."""
        if not self.storage_dir:
            return

        try:
            metrics_file = self.storage_dir / "routing_metrics.json"
            self.export_json(metrics_file)

            summary_file = self.storage_dir / "routing_summary.json"
            self.export_summary(summary_file)

        except Exception as e:
            logger.warning(f"Failed to save metrics: {e}")

    def _load_metrics(self) -> None:
        """Load metrics from storage directory."""
        if not self.storage_dir:
            return

        try:
            metrics_file = self.storage_dir / "routing_metrics.json"

            if not metrics_file.exists():
                logger.debug("No existing metrics file found")
                return

            with open(metrics_file, "r") as f:
                data = json.load(f)

            # Load metrics
            for metric_data in data.get("metrics", []):
                metric = RoutingMetric(**metric_data)
                self._metrics.append(metric)

            logger.info(f"Loaded {len(self._metrics)} metrics from {metrics_file}")

            # Clean up old metrics
            self.cleanup_old_metrics()

        except Exception as e:
            logger.warning(f"Failed to load metrics: {e}")
