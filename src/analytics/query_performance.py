"""Query performance analytics.

Provides performance tracking, trend analysis, and anomaly detection
for query operations.
"""

import logging
import statistics
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class AggregationPeriod(Enum):
    """Time period for aggregating metrics."""

    MINUTE = "minute"
    HOUR = "hour"
    DAY = "day"
    WEEK = "week"


@dataclass
class QueryRecord:
    """A single query performance record.

    Attributes:
        query_id: Unique query identifier
        query_text: The query text
        timestamp: When the query was executed
        latency_ms: Query latency in milliseconds
        result_count: Number of results returned
        model: Model used for generation
        success: Whether query succeeded
        error: Error message if failed
        metadata: Additional metadata
    """

    query_id: str
    query_text: str
    timestamp: datetime
    latency_ms: float
    result_count: int
    model: str = ""
    success: bool = True
    error: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "query_id": self.query_id,
            "query_text": self.query_text[:100] + "..." if len(self.query_text) > 100 else self.query_text,
            "timestamp": self.timestamp.isoformat(),
            "latency_ms": self.latency_ms,
            "result_count": self.result_count,
            "model": self.model,
            "success": self.success,
            "error": self.error,
            "metadata": self.metadata,
        }


@dataclass
class PerformanceMetrics:
    """Aggregated performance metrics for a time period.

    Attributes:
        period_start: Start of aggregation period
        period_end: End of aggregation period
        query_count: Total queries in period
        success_count: Successful queries
        error_count: Failed queries
        latency_p50: 50th percentile latency
        latency_p95: 95th percentile latency
        latency_p99: 99th percentile latency
        latency_avg: Average latency
        latency_min: Minimum latency
        latency_max: Maximum latency
        results_avg: Average result count
        throughput: Queries per minute
    """

    period_start: datetime
    period_end: datetime
    query_count: int = 0
    success_count: int = 0
    error_count: int = 0
    latency_p50: float = 0.0
    latency_p95: float = 0.0
    latency_p99: float = 0.0
    latency_avg: float = 0.0
    latency_min: float = 0.0
    latency_max: float = 0.0
    results_avg: float = 0.0
    throughput: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "period_start": self.period_start.isoformat(),
            "period_end": self.period_end.isoformat(),
            "query_count": self.query_count,
            "success_count": self.success_count,
            "error_count": self.error_count,
            "error_rate": self.error_count / self.query_count if self.query_count > 0 else 0,
            "latency": {
                "p50": self.latency_p50,
                "p95": self.latency_p95,
                "p99": self.latency_p99,
                "avg": self.latency_avg,
                "min": self.latency_min,
                "max": self.latency_max,
            },
            "results_avg": self.results_avg,
            "throughput": self.throughput,
        }


@dataclass
class PerformanceAnomaly:
    """A detected performance anomaly.

    Attributes:
        timestamp: When anomaly occurred
        metric: Which metric is anomalous
        value: Actual value
        expected: Expected value (baseline)
        deviation: Standard deviations from expected
        severity: Anomaly severity (low, medium, high)
        description: Human-readable description
    """

    timestamp: datetime
    metric: str
    value: float
    expected: float
    deviation: float
    severity: str = "low"
    description: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "timestamp": self.timestamp.isoformat(),
            "metric": self.metric,
            "value": self.value,
            "expected": self.expected,
            "deviation": self.deviation,
            "severity": self.severity,
            "description": self.description,
        }


class QueryPerformanceTracker:
    """Tracks and stores query performance records."""

    def __init__(self, max_records: int = 10000) -> None:
        """Initialise performance tracker.

        Args:
            max_records: Maximum records to keep in memory
        """
        self.max_records = max_records
        self._records: list[QueryRecord] = []

    def record(
        self,
        query_id: str,
        query_text: str,
        latency_ms: float,
        result_count: int,
        model: str = "",
        success: bool = True,
        error: str = "",
        metadata: dict[str, Any] | None = None,
    ) -> QueryRecord:
        """Record a query execution.

        Args:
            query_id: Unique query identifier
            query_text: The query text
            latency_ms: Query latency in milliseconds
            result_count: Number of results returned
            model: Model used
            success: Whether query succeeded
            error: Error message if failed
            metadata: Additional metadata

        Returns:
            The recorded query record
        """
        record = QueryRecord(
            query_id=query_id,
            query_text=query_text,
            timestamp=datetime.now(),
            latency_ms=latency_ms,
            result_count=result_count,
            model=model,
            success=success,
            error=error,
            metadata=metadata or {},
        )

        self._records.append(record)

        # Trim old records if exceeding max
        if len(self._records) > self.max_records:
            self._records = self._records[-self.max_records :]

        return record

    def get_records(
        self,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
        model: str | None = None,
        success_only: bool = False,
    ) -> list[QueryRecord]:
        """Get filtered query records.

        Args:
            start_time: Filter records after this time
            end_time: Filter records before this time
            model: Filter by model
            success_only: Only return successful queries

        Returns:
            Filtered list of query records
        """
        records = self._records

        if start_time:
            records = [r for r in records if r.timestamp >= start_time]
        if end_time:
            records = [r for r in records if r.timestamp <= end_time]
        if model:
            records = [r for r in records if r.model == model]
        if success_only:
            records = [r for r in records if r.success]

        return records

    def clear(self) -> None:
        """Clear all records."""
        self._records.clear()

    @property
    def record_count(self) -> int:
        """Get total record count."""
        return len(self._records)


class PerformanceAggregator:
    """Aggregates query performance metrics over time periods."""

    def aggregate(
        self,
        records: list[QueryRecord],
        period: AggregationPeriod = AggregationPeriod.HOUR,
    ) -> list[PerformanceMetrics]:
        """Aggregate records into time-period buckets.

        Args:
            records: Query records to aggregate
            period: Aggregation period

        Returns:
            List of aggregated metrics per period
        """
        if not records:
            return []

        # Sort by timestamp
        sorted_records = sorted(records, key=lambda r: r.timestamp)

        # Group by period
        buckets: dict[datetime, list[QueryRecord]] = {}
        for record in sorted_records:
            bucket_key = self._get_bucket_key(record.timestamp, period)
            if bucket_key not in buckets:
                buckets[bucket_key] = []
            buckets[bucket_key].append(record)

        # Aggregate each bucket
        metrics = []
        for bucket_start, bucket_records in sorted(buckets.items()):
            bucket_end = self._get_bucket_end(bucket_start, period)
            metrics.append(self._aggregate_bucket(bucket_records, bucket_start, bucket_end))

        return metrics

    def _get_bucket_key(self, timestamp: datetime, period: AggregationPeriod) -> datetime:
        """Get the bucket start time for a timestamp."""
        if period == AggregationPeriod.MINUTE:
            return timestamp.replace(second=0, microsecond=0)
        elif period == AggregationPeriod.HOUR:
            return timestamp.replace(minute=0, second=0, microsecond=0)
        elif period == AggregationPeriod.DAY:
            return timestamp.replace(hour=0, minute=0, second=0, microsecond=0)
        elif period == AggregationPeriod.WEEK:
            # Start of week (Monday)
            days_since_monday = timestamp.weekday()
            week_start = timestamp - timedelta(days=days_since_monday)
            return week_start.replace(hour=0, minute=0, second=0, microsecond=0)
        return timestamp

    def _get_bucket_end(self, bucket_start: datetime, period: AggregationPeriod) -> datetime:
        """Get the bucket end time."""
        if period == AggregationPeriod.MINUTE:
            return bucket_start + timedelta(minutes=1)
        elif period == AggregationPeriod.HOUR:
            return bucket_start + timedelta(hours=1)
        elif period == AggregationPeriod.DAY:
            return bucket_start + timedelta(days=1)
        elif period == AggregationPeriod.WEEK:
            return bucket_start + timedelta(weeks=1)
        return bucket_start + timedelta(hours=1)

    def _aggregate_bucket(
        self,
        records: list[QueryRecord],
        period_start: datetime,
        period_end: datetime,
    ) -> PerformanceMetrics:
        """Aggregate records in a single bucket."""
        latencies = [r.latency_ms for r in records]
        result_counts = [r.result_count for r in records]

        success_count = sum(1 for r in records if r.success)
        error_count = len(records) - success_count

        # Calculate percentiles
        sorted_latencies = sorted(latencies)
        p50 = self._percentile(sorted_latencies, 50)
        p95 = self._percentile(sorted_latencies, 95)
        p99 = self._percentile(sorted_latencies, 99)

        # Calculate throughput (queries per minute)
        duration_minutes = (period_end - period_start).total_seconds() / 60
        throughput = len(records) / duration_minutes if duration_minutes > 0 else 0

        return PerformanceMetrics(
            period_start=period_start,
            period_end=period_end,
            query_count=len(records),
            success_count=success_count,
            error_count=error_count,
            latency_p50=p50,
            latency_p95=p95,
            latency_p99=p99,
            latency_avg=statistics.mean(latencies) if latencies else 0,
            latency_min=min(latencies) if latencies else 0,
            latency_max=max(latencies) if latencies else 0,
            results_avg=statistics.mean(result_counts) if result_counts else 0,
            throughput=throughput,
        )

    def _percentile(self, sorted_values: list[float], percentile: int) -> float:
        """Calculate percentile from sorted values."""
        if not sorted_values:
            return 0.0

        n = len(sorted_values)
        index = (percentile / 100) * (n - 1)
        lower = int(index)
        upper = lower + 1

        if upper >= n:
            return sorted_values[-1]

        weight = index - lower
        return sorted_values[lower] * (1 - weight) + sorted_values[upper] * weight


class AnomalyDetector:
    """Detects performance anomalies."""

    def __init__(
        self,
        baseline_periods: int = 7,
        deviation_threshold: float = 2.0,
    ) -> None:
        """Initialise anomaly detector.

        Args:
            baseline_periods: Number of periods for baseline calculation
            deviation_threshold: Standard deviations for anomaly
        """
        self.baseline_periods = baseline_periods
        self.deviation_threshold = deviation_threshold

    def detect(
        self,
        metrics: list[PerformanceMetrics],
    ) -> list[PerformanceAnomaly]:
        """Detect anomalies in performance metrics.

        Args:
            metrics: Time-series of performance metrics

        Returns:
            List of detected anomalies
        """
        if len(metrics) < self.baseline_periods + 1:
            return []  # Not enough data for baseline

        anomalies = []

        # Check each metric after baseline period
        for i in range(self.baseline_periods, len(metrics)):
            current = metrics[i]
            baseline = metrics[i - self.baseline_periods : i]

            # Check latency anomalies
            latency_anomaly = self._check_metric_anomaly(
                current_value=current.latency_p95,
                baseline_values=[m.latency_p95 for m in baseline],
                metric_name="latency_p95",
                timestamp=current.period_start,
            )
            if latency_anomaly:
                anomalies.append(latency_anomaly)

            # Check error rate anomalies
            current_error_rate = (
                current.error_count / current.query_count
                if current.query_count > 0
                else 0
            )
            baseline_error_rates = [
                m.error_count / m.query_count if m.query_count > 0 else 0
                for m in baseline
            ]
            error_anomaly = self._check_metric_anomaly(
                current_value=current_error_rate,
                baseline_values=baseline_error_rates,
                metric_name="error_rate",
                timestamp=current.period_start,
            )
            if error_anomaly:
                anomalies.append(error_anomaly)

            # Check throughput drop
            throughput_anomaly = self._check_metric_anomaly(
                current_value=current.throughput,
                baseline_values=[m.throughput for m in baseline],
                metric_name="throughput",
                timestamp=current.period_start,
                check_decrease=True,  # Anomaly if throughput decreases
            )
            if throughput_anomaly:
                anomalies.append(throughput_anomaly)

        return anomalies

    def _check_metric_anomaly(
        self,
        current_value: float,
        baseline_values: list[float],
        metric_name: str,
        timestamp: datetime,
        check_decrease: bool = False,
    ) -> PerformanceAnomaly | None:
        """Check if a metric value is anomalous."""
        if not baseline_values:
            return None

        mean = statistics.mean(baseline_values)
        if len(baseline_values) < 2:
            return None

        stdev = statistics.stdev(baseline_values)
        if stdev == 0:
            return None

        deviation = (current_value - mean) / stdev

        # Check for anomaly (increase for latency/errors, decrease for throughput)
        is_anomaly = False
        if check_decrease:
            is_anomaly = deviation < -self.deviation_threshold
        else:
            is_anomaly = deviation > self.deviation_threshold

        if not is_anomaly:
            return None

        # Determine severity
        abs_deviation = abs(deviation)
        if abs_deviation > 4:
            severity = "high"
        elif abs_deviation > 3:
            severity = "medium"
        else:
            severity = "low"

        # Generate description
        if check_decrease:
            direction = "decreased"
            comparison = f"{((mean - current_value) / mean * 100):.1f}% below"
        else:
            direction = "increased"
            comparison = f"{((current_value - mean) / mean * 100):.1f}% above"

        description = f"{metric_name} {direction} to {current_value:.2f} ({comparison} baseline)"

        return PerformanceAnomaly(
            timestamp=timestamp,
            metric=metric_name,
            value=current_value,
            expected=mean,
            deviation=deviation,
            severity=severity,
            description=description,
        )


class QueryPerformanceAnalytics:
    """High-level query performance analytics interface."""

    def __init__(self) -> None:
        """Initialise query performance analytics."""
        self.tracker = QueryPerformanceTracker()
        self.aggregator = PerformanceAggregator()
        self.anomaly_detector = AnomalyDetector()

    def record_query(
        self,
        query_id: str,
        query_text: str,
        latency_ms: float,
        result_count: int,
        model: str = "",
        success: bool = True,
        error: str = "",
        metadata: dict[str, Any] | None = None,
    ) -> QueryRecord:
        """Record a query execution."""
        return self.tracker.record(
            query_id=query_id,
            query_text=query_text,
            latency_ms=latency_ms,
            result_count=result_count,
            model=model,
            success=success,
            error=error,
            metadata=metadata,
        )

    def get_performance_trends(
        self,
        period: AggregationPeriod = AggregationPeriod.HOUR,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
    ) -> dict[str, Any]:
        """Get performance trends over time.

        Args:
            period: Aggregation period
            start_time: Start of time range
            end_time: End of time range

        Returns:
            Performance trends data
        """
        records = self.tracker.get_records(start_time=start_time, end_time=end_time)
        metrics = self.aggregator.aggregate(records, period)
        anomalies = self.anomaly_detector.detect(metrics)

        # Generate insights
        insights = self._generate_insights(metrics, anomalies)

        return {
            "metrics": [m.to_dict() for m in metrics],
            "anomalies": [a.to_dict() for a in anomalies],
            "insights": insights,
            "summary": self._generate_summary(metrics),
        }

    def _generate_summary(self, metrics: list[PerformanceMetrics]) -> dict[str, Any]:
        """Generate summary statistics."""
        if not metrics:
            return {}

        total_queries = sum(m.query_count for m in metrics)
        total_errors = sum(m.error_count for m in metrics)
        all_latencies = [m.latency_avg for m in metrics if m.query_count > 0]

        return {
            "total_queries": total_queries,
            "total_errors": total_errors,
            "error_rate": total_errors / total_queries if total_queries > 0 else 0,
            "avg_latency": statistics.mean(all_latencies) if all_latencies else 0,
            "period_count": len(metrics),
        }

    def _generate_insights(
        self,
        metrics: list[PerformanceMetrics],
        anomalies: list[PerformanceAnomaly],
    ) -> list[str]:
        """Generate human-readable insights."""
        insights = []

        if not metrics:
            return ["No query data available"]

        # Latency trend
        if len(metrics) >= 2:
            first_half = metrics[: len(metrics) // 2]
            second_half = metrics[len(metrics) // 2 :]

            first_avg = statistics.mean([m.latency_avg for m in first_half])
            second_avg = statistics.mean([m.latency_avg for m in second_half])

            if second_avg > first_avg * 1.2:
                change = ((second_avg - first_avg) / first_avg) * 100
                insights.append(f"Query latency increased by {change:.1f}% over the period")
            elif second_avg < first_avg * 0.8:
                change = ((first_avg - second_avg) / first_avg) * 100
                insights.append(f"Query latency improved by {change:.1f}% over the period")

        # Anomaly insights
        high_severity = [a for a in anomalies if a.severity == "high"]
        if high_severity:
            insights.append(f"{len(high_severity)} high-severity anomalies detected")

        # Error rate
        total_queries = sum(m.query_count for m in metrics)
        total_errors = sum(m.error_count for m in metrics)
        if total_queries > 0:
            error_rate = total_errors / total_queries
            if error_rate > 0.1:
                insights.append(f"High error rate: {error_rate:.1%} of queries failed")
            elif error_rate == 0:
                insights.append("All queries executed successfully")

        return insights


# Module-level convenience functions
_analytics: QueryPerformanceAnalytics | None = None


def get_query_performance_analytics() -> QueryPerformanceAnalytics:
    """Get global query performance analytics instance."""
    global _analytics
    if _analytics is None:
        _analytics = QueryPerformanceAnalytics()
    return _analytics
