"""Tests for quality metrics collection.

v0.3.9: Test metrics collector and quality tracking.
"""

import tempfile
from datetime import datetime
from pathlib import Path

import pytest

from src.monitoring.metrics import (
    MetricsCollector,
    QualityMetrics,
    create_metrics_collector,
)


class TestQualityMetrics:
    """Test QualityMetrics dataclass."""

    def test_metrics_creation(self):
        """Test creating quality metrics."""
        metrics = QualityMetrics(
            query_hash="abc123",
            timestamp=datetime.now(),
            duration_ms=1234.5,
            chunks_retrieved=5,
            avg_confidence=0.89,
        )

        assert metrics.query_hash == "abc123"
        assert metrics.duration_ms == 1234.5
        assert metrics.chunks_retrieved == 5
        assert metrics.avg_confidence == 0.89
        assert metrics.success is True

    def test_metrics_with_ragas_scores(self):
        """Test metrics with RAGAS scores."""
        metrics = QualityMetrics(
            query_hash="test",
            timestamp=datetime.now(),
            duration_ms=1000,
            chunks_retrieved=5,
            avg_confidence=0.9,
            context_precision=0.87,
            context_recall=0.82,
            faithfulness=0.91,
            answer_relevancy=0.85,
            ragas_score=0.86,
        )

        assert metrics.context_precision == 0.87
        assert metrics.context_recall == 0.82
        assert metrics.faithfulness == 0.91
        assert metrics.answer_relevancy == 0.85
        assert metrics.ragas_score == 0.86

    def test_metrics_to_dict(self):
        """Test converting metrics to dictionary."""
        timestamp = datetime.now()
        metrics = QualityMetrics(
            query_hash="test",
            timestamp=timestamp,
            duration_ms=1000,
            chunks_retrieved=5,
            avg_confidence=0.9,
            ragas_score=0.85,
        )

        data = metrics.to_dict()

        assert data["query_hash"] == "test"
        assert data["timestamp"] == timestamp.isoformat()
        assert data["duration_ms"] == 1000
        assert data["ragas_score"] == 0.85

    def test_metrics_from_dict(self):
        """Test creating metrics from dictionary."""
        timestamp = datetime.now()
        data = {
            "query_hash": "test",
            "timestamp": timestamp.isoformat(),
            "duration_ms": 1000,
            "chunks_retrieved": 5,
            "avg_confidence": 0.9,
            "ragas_score": 0.85,
            "success": True,
            "metadata": {"key": "value"},
        }

        metrics = QualityMetrics.from_dict(data)

        assert metrics.query_hash == "test"
        assert metrics.duration_ms == 1000
        assert metrics.ragas_score == 0.85
        assert metrics.metadata["key"] == "value"


class TestMetricsCollector:
    """Test MetricsCollector class."""

    @pytest.fixture
    def temp_storage(self, tmp_path):
        """Create temporary storage path."""
        return tmp_path / "metrics.json"

    @pytest.fixture
    def collector(self, temp_storage):
        """Create collector with temporary storage."""
        return MetricsCollector(storage_path=temp_storage)

    def test_collector_init(self, temp_storage):
        """Test collector initialisation."""
        collector = MetricsCollector(storage_path=temp_storage)

        assert collector.storage_path == temp_storage
        assert len(collector.metrics) == 0

    def test_collector_init_creates_directory(self, tmp_path):
        """Test collector creates storage directory."""
        storage_path = tmp_path / "subdir" / "metrics.json"
        collector = MetricsCollector(storage_path=storage_path)

        assert storage_path.parent.exists()

    def test_record_metrics(self, collector):
        """Test recording metrics."""
        metrics = QualityMetrics(
            query_hash="test1",
            timestamp=datetime.now(),
            duration_ms=1000,
            chunks_retrieved=5,
            avg_confidence=0.9,
        )

        collector.record(metrics)

        assert len(collector.metrics) == 1
        assert collector.metrics[0].query_hash == "test1"

    def test_record_multiple_metrics(self, collector):
        """Test recording multiple metrics."""
        for i in range(5):
            metrics = QualityMetrics(
                query_hash=f"test{i}",
                timestamp=datetime.now(),
                duration_ms=1000 + i * 100,
                chunks_retrieved=5,
                avg_confidence=0.9,
            )
            collector.record(metrics)

        assert len(collector.metrics) == 5

    def test_record_persists_to_storage(self, collector, temp_storage):
        """Test that recording saves to file."""
        metrics = QualityMetrics(
            query_hash="test",
            timestamp=datetime.now(),
            duration_ms=1000,
            chunks_retrieved=5,
            avg_confidence=0.9,
        )

        collector.record(metrics)

        # File should exist
        assert temp_storage.exists()

        # Load new collector from same file
        collector2 = MetricsCollector(storage_path=temp_storage)

        assert len(collector2.metrics) == 1
        assert collector2.metrics[0].query_hash == "test"

    def test_get_recent(self, collector):
        """Test getting recent metrics."""
        # Add metrics with different timestamps
        import time

        for i in range(10):
            metrics = QualityMetrics(
                query_hash=f"test{i}",
                timestamp=datetime.now(),
                duration_ms=1000,
                chunks_retrieved=5,
                avg_confidence=0.9,
            )
            collector.record(metrics)
            time.sleep(0.001)  # Small delay to ensure different timestamps

        recent = collector.get_recent(limit=5)

        # Should get 5 most recent (most recent first)
        assert len(recent) == 5
        # Most recent should have highest index
        assert "test9" in recent[0].query_hash

    def test_get_statistics_empty(self, collector):
        """Test statistics with no data."""
        stats = collector.get_statistics()

        assert stats["count"] == 0
        assert stats["avg_duration_ms"] == 0.0

    def test_get_statistics(self, collector):
        """Test computing statistics."""
        # Add some metrics
        for i in range(10):
            metrics = QualityMetrics(
                query_hash=f"test{i}",
                timestamp=datetime.now(),
                duration_ms=1000 + i * 100,  # 1000, 1100, 1200, ...
                chunks_retrieved=5,
                avg_confidence=0.8 + i * 0.01,  # 0.8, 0.81, 0.82, ...
                success=True,
            )
            collector.record(metrics)

        stats = collector.get_statistics(last_n=10)

        assert stats["count"] == 10
        assert stats["success_count"] == 10
        assert stats["success_rate"] == 1.0
        assert stats["avg_duration_ms"] == 1450.0  # Mean of 1000..1900
        assert 0.84 < stats["avg_confidence"] < 0.85  # Approximately 0.845

    def test_get_statistics_with_failures(self, collector):
        """Test statistics with some failures."""
        # Add successful and failed metrics
        for i in range(10):
            metrics = QualityMetrics(
                query_hash=f"test{i}",
                timestamp=datetime.now(),
                duration_ms=1000,
                chunks_retrieved=5,
                avg_confidence=0.9,
                success=i < 8,  # First 8 succeed, last 2 fail
            )
            collector.record(metrics)

        stats = collector.get_statistics(last_n=10)

        assert stats["count"] == 10
        assert stats["success_count"] == 8
        assert stats["failure_count"] == 2
        assert stats["success_rate"] == 0.8

    def test_get_statistics_with_ragas_scores(self, collector):
        """Test statistics with RAGAS scores."""
        for i in range(5):
            metrics = QualityMetrics(
                query_hash=f"test{i}",
                timestamp=datetime.now(),
                duration_ms=1000,
                chunks_retrieved=5,
                avg_confidence=0.9,
                ragas_score=0.8 + i * 0.01,  # 0.8, 0.81, 0.82, 0.83, 0.84
                context_precision=0.85,
                context_recall=0.82,
                faithfulness=0.91,
                answer_relevancy=0.85,
            )
            collector.record(metrics)

        stats = collector.get_statistics(last_n=5)

        assert "avg_ragas_score" in stats
        assert 0.81 < stats["avg_ragas_score"] < 0.83  # Mean of 0.8..0.84
        assert stats["avg_context_precision"] == 0.85
        assert stats["avg_context_recall"] == 0.82

    def test_render_dashboard_empty(self, collector):
        """Test rendering dashboard with no data."""
        dashboard = collector.render_dashboard()

        assert "No metrics recorded" in dashboard

    def test_render_dashboard(self, collector):
        """Test rendering dashboard."""
        # Add some metrics
        for i in range(10):
            metrics = QualityMetrics(
                query_hash=f"test{i}",
                timestamp=datetime.now(),
                duration_ms=1000 + i * 100,
                chunks_retrieved=5,
                avg_confidence=0.9,
                ragas_score=0.85,
            )
            collector.record(metrics)

        dashboard = collector.render_dashboard()

        assert "Quality Metrics Dashboard" in dashboard
        assert "Total Queries: 10" in dashboard
        assert "Success Rate" in dashboard
        assert "Avg Duration" in dashboard
        assert "Overall RAGAS: 0.850" in dashboard

    def test_render_dashboard_quality_assessment(self, collector):
        """Test dashboard quality assessment."""
        # Add metrics with high RAGAS score
        for i in range(5):
            metrics = QualityMetrics(
                query_hash=f"test{i}",
                timestamp=datetime.now(),
                duration_ms=1000,
                chunks_retrieved=5,
                avg_confidence=0.9,
                ragas_score=0.85,  # Good score >= 0.8
            )
            collector.record(metrics)

        dashboard = collector.render_dashboard()

        assert "Excellent" in dashboard or "Good" in dashboard

    def test_export(self, collector, tmp_path):
        """Test exporting metrics."""
        # Add some metrics
        for i in range(5):
            metrics = QualityMetrics(
                query_hash=f"test{i}",
                timestamp=datetime.now(),
                duration_ms=1000,
                chunks_retrieved=5,
                avg_confidence=0.9,
            )
            collector.record(metrics)

        export_path = tmp_path / "export.json"
        collector.export(export_path)

        # File should exist
        assert export_path.exists()

        # Verify contents
        import json

        with open(export_path) as f:
            data = json.load(f)

        assert data["metrics_count"] == 5
        assert len(data["metrics"]) == 5
        assert "export_timestamp" in data

    def test_export_limit(self, collector, tmp_path):
        """Test exporting with limit."""
        # Add 10 metrics
        for i in range(10):
            metrics = QualityMetrics(
                query_hash=f"test{i}",
                timestamp=datetime.now(),
                duration_ms=1000,
                chunks_retrieved=5,
                avg_confidence=0.9,
            )
            collector.record(metrics)

        export_path = tmp_path / "export.json"
        collector.export(export_path, last_n=3)

        # Should only export 3 most recent
        import json

        with open(export_path) as f:
            data = json.load(f)

        assert data["metrics_count"] == 3

    def test_clear(self, collector):
        """Test clearing metrics."""
        # Add some metrics
        for i in range(5):
            metrics = QualityMetrics(
                query_hash=f"test{i}",
                timestamp=datetime.now(),
                duration_ms=1000,
                chunks_retrieved=5,
                avg_confidence=0.9,
            )
            collector.record(metrics)

        assert len(collector.metrics) == 5

        count = collector.clear(confirm=True)

        assert count == 5
        assert len(collector.metrics) == 0

    def test_clear_requires_confirmation(self, collector):
        """Test that clear requires confirmation."""
        # Add metrics
        metrics = QualityMetrics(
            query_hash="test",
            timestamp=datetime.now(),
            duration_ms=1000,
            chunks_retrieved=5,
            avg_confidence=0.9,
        )
        collector.record(metrics)

        # Should raise error without confirmation
        with pytest.raises(ValueError, match="confirm"):
            collector.clear(confirm=False)

        # Metrics should still be there
        assert len(collector.metrics) == 1


class TestConvenienceFunction:
    """Test convenience functions."""

    def test_create_metrics_collector(self):
        """Test creating metrics collector."""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage_path = Path(tmpdir) / "metrics.json"
            collector = create_metrics_collector(storage_path=storage_path)

            assert isinstance(collector, MetricsCollector)
            assert collector.storage_path == storage_path

    def test_create_metrics_collector_default_path(self):
        """Test creating collector with default path."""
        collector = create_metrics_collector()

        assert isinstance(collector, MetricsCollector)
        # Default path should be in home directory
        assert ".ragged" in str(collector.storage_path)
