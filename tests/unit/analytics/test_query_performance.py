"""Unit tests for query performance analytics module."""

import pytest
from datetime import datetime, timedelta

from ragged.analytics.query_performance import (
    AggregationPeriod,
    QueryRecord,
    PerformanceMetrics,
    PerformanceAnomaly,
    QueryPerformanceTracker,
    PerformanceAggregator,
    AnomalyDetector,
    QueryPerformanceAnalytics,
    get_query_performance_analytics,
)


class TestQueryRecord:
    """Tests for QueryRecord dataclass."""

    def test_create_record(self):
        """Test creating a query record."""
        timestamp = datetime.now()
        record = QueryRecord(
            query_id="q1",
            query_text="What is Python?",
            timestamp=timestamp,
            latency_ms=150.5,
            result_count=5,
            model="llama3",
            success=True,
        )
        assert record.query_id == "q1"
        assert record.latency_ms == 150.5
        assert record.result_count == 5
        assert record.model == "llama3"
        assert record.success is True

    def test_to_dict(self):
        """Test record serialisation."""
        record = QueryRecord(
            query_id="q1",
            query_text="Test query",
            timestamp=datetime(2024, 1, 1, 12, 0),
            latency_ms=100.0,
            result_count=3,
        )
        d = record.to_dict()
        assert d["query_id"] == "q1"
        assert d["latency_ms"] == 100.0
        assert d["result_count"] == 3
        assert "timestamp" in d

    def test_long_query_text_truncated(self):
        """Test that long query text is truncated in dict output."""
        long_text = "a" * 200
        record = QueryRecord(
            query_id="q1",
            query_text=long_text,
            timestamp=datetime.now(),
            latency_ms=100.0,
            result_count=1,
        )
        d = record.to_dict()
        assert len(d["query_text"]) == 103  # 100 chars + "..."


class TestPerformanceMetrics:
    """Tests for PerformanceMetrics dataclass."""

    def test_create_metrics(self):
        """Test creating performance metrics."""
        start = datetime(2024, 1, 1, 12, 0)
        end = datetime(2024, 1, 1, 13, 0)
        metrics = PerformanceMetrics(
            period_start=start,
            period_end=end,
            query_count=100,
            success_count=95,
            error_count=5,
            latency_p50=50.0,
            latency_p95=150.0,
            latency_p99=300.0,
        )
        assert metrics.query_count == 100
        assert metrics.success_count == 95
        assert metrics.error_count == 5

    def test_to_dict(self):
        """Test metrics serialisation."""
        metrics = PerformanceMetrics(
            period_start=datetime(2024, 1, 1, 12, 0),
            period_end=datetime(2024, 1, 1, 13, 0),
            query_count=100,
            success_count=90,
            error_count=10,
        )
        d = metrics.to_dict()
        assert d["query_count"] == 100
        assert d["error_rate"] == 0.1
        assert "latency" in d


class TestPerformanceAnomaly:
    """Tests for PerformanceAnomaly dataclass."""

    def test_create_anomaly(self):
        """Test creating a performance anomaly."""
        anomaly = PerformanceAnomaly(
            timestamp=datetime.now(),
            metric="latency_p95",
            value=500.0,
            expected=200.0,
            deviation=3.5,
            severity="high",
            description="Latency spike detected",
        )
        assert anomaly.metric == "latency_p95"
        assert anomaly.severity == "high"
        assert anomaly.deviation == 3.5

    def test_to_dict(self):
        """Test anomaly serialisation."""
        anomaly = PerformanceAnomaly(
            timestamp=datetime(2024, 1, 1, 12, 0),
            metric="error_rate",
            value=0.15,
            expected=0.02,
            deviation=4.0,
        )
        d = anomaly.to_dict()
        assert d["metric"] == "error_rate"
        assert d["value"] == 0.15
        assert d["deviation"] == 4.0


class TestQueryPerformanceTracker:
    """Tests for QueryPerformanceTracker."""

    @pytest.fixture
    def tracker(self):
        """Create a performance tracker."""
        return QueryPerformanceTracker(max_records=100)

    def test_record_query(self, tracker):
        """Test recording a query."""
        record = tracker.record(
            query_id="q1",
            query_text="Test query",
            latency_ms=100.0,
            result_count=5,
            model="llama3",
        )
        assert record.query_id == "q1"
        assert tracker.record_count == 1

    def test_record_multiple_queries(self, tracker):
        """Test recording multiple queries."""
        for i in range(10):
            tracker.record(
                query_id=f"q{i}",
                query_text=f"Query {i}",
                latency_ms=100.0 + i * 10,
                result_count=i,
            )
        assert tracker.record_count == 10

    def test_max_records_trimming(self):
        """Test that old records are trimmed when exceeding max."""
        tracker = QueryPerformanceTracker(max_records=5)
        for i in range(10):
            tracker.record(
                query_id=f"q{i}",
                query_text=f"Query {i}",
                latency_ms=100.0,
                result_count=1,
            )
        assert tracker.record_count == 5
        # Should keep most recent
        records = tracker.get_records()
        assert records[0].query_id == "q5"

    def test_get_records_with_filters(self, tracker):
        """Test filtering records."""
        now = datetime.now()
        # Record some queries
        for i in range(5):
            tracker.record(
                query_id=f"q{i}",
                query_text=f"Query {i}",
                latency_ms=100.0,
                result_count=1,
                model="llama3" if i % 2 == 0 else "mistral",
                success=i != 3,
            )

        # Filter by model
        llama_records = tracker.get_records(model="llama3")
        assert len(llama_records) == 3

        # Filter by success
        success_records = tracker.get_records(success_only=True)
        assert len(success_records) == 4

    def test_clear_records(self, tracker):
        """Test clearing records."""
        tracker.record("q1", "Test", 100.0, 1)
        tracker.record("q2", "Test", 100.0, 1)
        assert tracker.record_count == 2

        tracker.clear()
        assert tracker.record_count == 0


class TestPerformanceAggregator:
    """Tests for PerformanceAggregator."""

    @pytest.fixture
    def aggregator(self):
        """Create a performance aggregator."""
        return PerformanceAggregator()

    def test_aggregate_empty(self, aggregator):
        """Test aggregating empty records."""
        result = aggregator.aggregate([])
        assert result == []

    def test_aggregate_single_hour(self, aggregator):
        """Test aggregating records in a single hour."""
        base_time = datetime(2024, 1, 1, 12, 0)
        records = [
            QueryRecord(
                f"q{i}",
                f"Query {i}",
                base_time + timedelta(minutes=i * 5),
                100.0 + i * 20,
                i + 1,
            )
            for i in range(10)
        ]

        metrics = aggregator.aggregate(records, AggregationPeriod.HOUR)

        assert len(metrics) == 1
        assert metrics[0].query_count == 10
        assert metrics[0].latency_min == 100.0
        assert metrics[0].latency_max == 280.0  # 100 + 9*20

    def test_aggregate_multiple_hours(self, aggregator):
        """Test aggregating records across multiple hours."""
        records = []
        for hour in range(3):
            base_time = datetime(2024, 1, 1, 10 + hour, 0)
            for i in range(5):
                records.append(
                    QueryRecord(
                        f"q{hour}_{i}",
                        "Query",
                        base_time + timedelta(minutes=i * 10),
                        100.0,
                        1,
                    )
                )

        metrics = aggregator.aggregate(records, AggregationPeriod.HOUR)

        assert len(metrics) == 3
        for m in metrics:
            assert m.query_count == 5

    def test_percentile_calculation(self, aggregator):
        """Test percentile calculations."""
        base_time = datetime(2024, 1, 1, 12, 0)
        # Create records with known latencies
        latencies = [10, 20, 30, 40, 50, 60, 70, 80, 90, 100]
        records = [
            QueryRecord(f"q{i}", "Query", base_time, lat, 1)
            for i, lat in enumerate(latencies)
        ]

        metrics = aggregator.aggregate(records, AggregationPeriod.HOUR)

        assert len(metrics) == 1
        # p50 should be around 55 (median of 10 values)
        assert 50 <= metrics[0].latency_p50 <= 60
        # p95 should be close to 100
        assert metrics[0].latency_p95 >= 90

    def test_throughput_calculation(self, aggregator):
        """Test throughput (queries per minute) calculation."""
        base_time = datetime(2024, 1, 1, 12, 0)
        # 60 queries in one hour = 1 query per minute
        records = [
            QueryRecord(f"q{i}", "Query", base_time + timedelta(minutes=i), 100.0, 1)
            for i in range(60)
        ]

        metrics = aggregator.aggregate(records, AggregationPeriod.HOUR)

        assert len(metrics) == 1
        assert metrics[0].throughput == 1.0  # 60 queries / 60 minutes

    def test_day_aggregation(self, aggregator):
        """Test daily aggregation."""
        records = []
        for day in range(3):
            base_time = datetime(2024, 1, 1 + day, 12, 0)
            records.append(QueryRecord(f"q{day}", "Query", base_time, 100.0, 1))

        metrics = aggregator.aggregate(records, AggregationPeriod.DAY)

        assert len(metrics) == 3


class TestAnomalyDetector:
    """Tests for AnomalyDetector."""

    @pytest.fixture
    def detector(self):
        """Create an anomaly detector."""
        return AnomalyDetector(baseline_periods=3, deviation_threshold=2.0)

    def test_not_enough_data(self, detector):
        """Test with insufficient data for baseline."""
        metrics = [
            PerformanceMetrics(
                datetime(2024, 1, 1, i, 0),
                datetime(2024, 1, 1, i + 1, 0),
                query_count=10,
                latency_p95=100.0,
            )
            for i in range(3)
        ]

        anomalies = detector.detect(metrics)
        assert len(anomalies) == 0

    def test_detect_latency_spike(self, detector):
        """Test detecting latency spike."""
        # Create baseline with slight variation (needed for stdev > 0)
        baseline_latencies = [100.0, 102.0, 98.0, 101.0]
        metrics = [
            PerformanceMetrics(
                datetime(2024, 1, 1, i, 0),
                datetime(2024, 1, 1, i + 1, 0),
                query_count=10,
                latency_p95=baseline_latencies[i],
            )
            for i in range(4)
        ]
        # Add spike (significant deviation from baseline ~100ms)
        metrics.append(
            PerformanceMetrics(
                datetime(2024, 1, 1, 4, 0),
                datetime(2024, 1, 1, 5, 0),
                query_count=10,
                latency_p95=500.0,  # 5x normal
            )
        )

        anomalies = detector.detect(metrics)

        # Should detect at least latency anomaly
        latency_anomalies = [a for a in anomalies if a.metric == "latency_p95"]
        assert len(latency_anomalies) >= 1

    def test_detect_error_rate_spike(self, detector):
        """Test detecting error rate spike."""
        # Create baseline with low error rate (slight variation for stdev > 0)
        error_counts = [2, 3, 1, 2]
        metrics = [
            PerformanceMetrics(
                datetime(2024, 1, 1, i, 0),
                datetime(2024, 1, 1, i + 1, 0),
                query_count=100,
                success_count=100 - error_counts[i],
                error_count=error_counts[i],
                latency_p95=100.0,
            )
            for i in range(4)
        ]
        # Add error spike
        metrics.append(
            PerformanceMetrics(
                datetime(2024, 1, 1, 4, 0),
                datetime(2024, 1, 1, 5, 0),
                query_count=100,
                success_count=50,
                error_count=50,  # 50% error rate
                latency_p95=100.0,
            )
        )

        anomalies = detector.detect(metrics)

        error_anomalies = [a for a in anomalies if a.metric == "error_rate"]
        assert len(error_anomalies) >= 1

    def test_detect_throughput_drop(self, detector):
        """Test detecting throughput drop."""
        # Create baseline with slight variation (needed for stdev > 0)
        throughputs = [10.0, 10.5, 9.8, 10.2]
        metrics = [
            PerformanceMetrics(
                datetime(2024, 1, 1, i, 0),
                datetime(2024, 1, 1, i + 1, 0),
                query_count=100,
                throughput=throughputs[i],
                latency_p95=100.0,
            )
            for i in range(4)
        ]
        # Add throughput drop
        metrics.append(
            PerformanceMetrics(
                datetime(2024, 1, 1, 4, 0),
                datetime(2024, 1, 1, 5, 0),
                query_count=10,
                throughput=1.0,  # 1 query/min
                latency_p95=100.0,
            )
        )

        anomalies = detector.detect(metrics)

        throughput_anomalies = [a for a in anomalies if a.metric == "throughput"]
        assert len(throughput_anomalies) >= 1

    def test_severity_levels(self, detector):
        """Test anomaly severity classification."""
        # Create metrics with slight variation (needed for stdev > 0)
        baseline_latencies = [100.0, 102.0, 98.0, 101.0]
        metrics = [
            PerformanceMetrics(
                datetime(2024, 1, 1, i, 0),
                datetime(2024, 1, 1, i + 1, 0),
                query_count=10,
                latency_p95=baseline_latencies[i],
            )
            for i in range(4)
        ]
        # Add extreme spike (should be high severity)
        metrics.append(
            PerformanceMetrics(
                datetime(2024, 1, 1, 4, 0),
                datetime(2024, 1, 1, 5, 0),
                query_count=10,
                latency_p95=1000.0,  # 10x normal
            )
        )

        anomalies = detector.detect(metrics)

        # Should have high severity anomaly
        high_severity = [a for a in anomalies if a.severity == "high"]
        assert len(high_severity) >= 1


class TestQueryPerformanceAnalytics:
    """Tests for QueryPerformanceAnalytics."""

    @pytest.fixture
    def analytics(self):
        """Create query performance analytics instance."""
        return QueryPerformanceAnalytics()

    def test_record_query(self, analytics):
        """Test recording a query."""
        record = analytics.record_query(
            query_id="q1",
            query_text="Test query",
            latency_ms=100.0,
            result_count=5,
            model="llama3",
        )
        assert record.query_id == "q1"
        assert analytics.tracker.record_count == 1

    def test_get_performance_trends(self, analytics):
        """Test getting performance trends."""
        # Record some queries
        base_time = datetime.now() - timedelta(hours=2)
        for i in range(20):
            analytics.record_query(
                query_id=f"q{i}",
                query_text=f"Query {i}",
                latency_ms=100.0 + i * 5,
                result_count=i % 5,
            )

        result = analytics.get_performance_trends(period=AggregationPeriod.HOUR)

        assert "metrics" in result
        assert "anomalies" in result
        assert "insights" in result
        assert "summary" in result

    def test_summary_generation(self, analytics):
        """Test summary generation."""
        # Record queries with some errors
        for i in range(10):
            analytics.record_query(
                query_id=f"q{i}",
                query_text=f"Query {i}",
                latency_ms=100.0,
                result_count=1,
                success=i != 5,  # One failure
            )

        result = analytics.get_performance_trends()

        summary = result["summary"]
        assert summary["total_queries"] == 10
        assert summary["total_errors"] == 1

    def test_insights_for_high_error_rate(self, analytics):
        """Test insights when error rate is high."""
        # Record queries with high error rate
        for i in range(10):
            analytics.record_query(
                query_id=f"q{i}",
                query_text=f"Query {i}",
                latency_ms=100.0,
                result_count=1,
                success=i < 5,  # 50% failure rate
            )

        result = analytics.get_performance_trends()

        # Should have insight about high error rate
        insights = result["insights"]
        assert any("error" in i.lower() for i in insights)

    def test_get_query_performance_analytics_singleton(self):
        """Test the global singleton function."""
        analytics1 = get_query_performance_analytics()
        analytics2 = get_query_performance_analytics()
        assert analytics1 is analytics2

