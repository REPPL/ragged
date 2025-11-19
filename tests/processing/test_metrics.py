"""
Tests for processing metrics module.

Tests cover:
- Routing metric recording
- Processing result tracking
- Summary generation
- Metrics export
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import Mock

import pytest

from src.processing.base import ProcessorConfig
from src.processing.metrics import MetricsSummary, ProcessingMetrics, RoutingMetric
from src.processing.quality_assessor import QualityAssessment
from src.processing.router import ProcessingRoute


@pytest.fixture
def metrics():
    """Create metrics instance without persistence."""
    return ProcessingMetrics(retention_days=30, storage_dir=None, auto_save=False)


@pytest.fixture
def sample_quality():
    """Create sample quality assessment."""
    return QualityAssessment(
        overall_score=0.85,
        is_born_digital=True,
        is_scanned=False,
        text_quality=0.90,
        layout_complexity=0.3,
        image_quality=0.0,
        has_tables=False,
        has_rotated_content=False,
        metadata={
            "file_name": "test.pdf",
            "file_size": 1024,
            "total_pages": 10,
        },
    )


@pytest.fixture
def sample_route(sample_quality):
    """Create sample processing route."""
    config = ProcessorConfig(
        processor_type="docling",
        enable_table_extraction=False,
        enable_layout_analysis=True,
        options={
            "quality_tier": "high",
            "processing_mode": "standard",
        },
    )

    return ProcessingRoute(
        processor="docling",
        config=config,
        quality=sample_quality,
        reasoning="Test routing",
        estimated_time=5.0,
        fallback_options=["legacy"],
    )


class TestRoutingMetric:
    """Test RoutingMetric dataclass."""

    def test_metric_creation(self):
        """Test routing metric creation."""
        metric = RoutingMetric(
            timestamp=datetime.now().isoformat(),
            file_name="test.pdf",
            file_size=1024,
            processor="docling",
            quality_score=0.85,
            is_born_digital=True,
            is_scanned=False,
            quality_tier="high",
            processing_mode="standard",
            has_tables=False,
            layout_complexity=0.3,
            estimated_time=5.0,
        )

        assert metric.file_name == "test.pdf"
        assert metric.processor == "docling"
        assert metric.quality_score == 0.85
        assert metric.success is True  # Default
        assert metric.error_message is None


class TestProcessingMetrics:
    """Test ProcessingMetrics class."""

    def test_init(self):
        """Test metrics initialisation."""
        metrics = ProcessingMetrics(
            retention_days=30,
            storage_dir=None,
            auto_save=False,
        )

        assert metrics.retention_days == 30
        assert metrics.storage_dir is None
        assert metrics.auto_save is False
        assert len(metrics._metrics) == 0

    def test_record_routing(self, metrics, sample_route):
        """Test recording routing decision."""
        metrics.record_routing(sample_route)

        assert len(metrics._metrics) == 1
        metric = metrics._metrics[0]

        assert metric.file_name == "test.pdf"
        assert metric.processor == "docling"
        assert metric.quality_score == 0.85
        assert metric.quality_tier == "high"
        assert metric.processing_mode == "standard"

    def test_record_multiple_routings(self, metrics, sample_route):
        """Test recording multiple routing decisions."""
        metrics.record_routing(sample_route)
        metrics.record_routing(sample_route)
        metrics.record_routing(sample_route)

        assert len(metrics._metrics) == 3

    def test_record_processing_result_success(self, metrics, sample_route):
        """Test recording successful processing result."""
        metrics.record_routing(sample_route)

        metrics.record_processing_result(
            route=sample_route,
            success=True,
            processing_time=2.5,
        )

        metric = metrics._metrics[0]
        assert metric.success is True
        assert metric.actual_time == 2.5
        assert metric.error_message is None

    def test_record_processing_result_failure(self, metrics, sample_route):
        """Test recording failed processing result."""
        metrics.record_routing(sample_route)

        metrics.record_processing_result(
            route=sample_route,
            success=False,
            processing_time=1.0,
            error_message="Test error",
        )

        metric = metrics._metrics[0]
        assert metric.success is False
        assert metric.actual_time == 1.0
        assert metric.error_message == "Test error"

    def test_get_summary_empty(self, metrics):
        """Test summary generation with no metrics."""
        summary = metrics.get_summary()

        assert summary.total_documents == 0
        assert summary.avg_quality_score == 0.0
        assert summary.success_rate == 0.0

    def test_get_summary_with_metrics(self, metrics, sample_route):
        """Test summary generation with metrics."""
        # Add multiple metrics
        for i in range(5):
            metrics.record_routing(sample_route)
            metrics.record_processing_result(
                route=sample_route,
                success=True,
                processing_time=2.0 + i,
            )

        summary = metrics.get_summary()

        assert summary.total_documents == 5
        assert summary.by_processor["docling"] == 5
        assert summary.by_quality_tier["high"] == 5
        assert summary.avg_quality_score == 0.85
        assert summary.avg_processing_time > 0
        assert summary.success_rate == 1.0
        assert summary.born_digital_rate == 1.0

    def test_get_summary_mixed_success(self, metrics, sample_route):
        """Test summary with mixed success/failure."""
        # 3 successes, 2 failures
        for i in range(5):
            metrics.record_routing(sample_route)
            metrics.record_processing_result(
                route=sample_route,
                success=(i < 3),
                processing_time=2.0,
            )

        summary = metrics.get_summary()

        assert summary.total_documents == 5
        assert summary.success_rate == 0.6  # 3/5

    def test_get_summary_filtered_by_processor(self, metrics, sample_route):
        """Test summary filtered by processor."""
        # Add metrics for different processors
        metrics.record_routing(sample_route)

        # Create route with different processor
        route2 = ProcessingRoute(
            processor="legacy",
            config=sample_route.config,
            quality=sample_route.quality,
            reasoning="Test",
            estimated_time=5.0,
        )
        route2.quality.metadata["file_name"] = "test2.pdf"
        metrics.record_routing(route2)

        summary = metrics.get_summary(processor="docling")

        assert summary.total_documents == 1
        assert "docling" in summary.by_processor

    def test_get_summary_filtered_by_time(self, metrics, sample_route):
        """Test summary filtered by time."""
        metrics.record_routing(sample_route)

        # Only include metrics from future (should be none)
        future = datetime.now() + timedelta(days=1)
        summary = metrics.get_summary(since=future)

        assert summary.total_documents == 0

    def test_get_quality_distribution(self, metrics):
        """Test quality score distribution."""
        # Add metrics with different quality scores
        for score in [0.6, 0.7, 0.75, 0.85, 0.9, 0.95]:
            route = Mock()
            route.quality = Mock()
            route.quality.metadata = {"file_name": f"test_{score}.pdf"}
            route.quality.overall_score = score
            route.processor = "docling"
            route.config = Mock()
            route.config.options = {"quality_tier": "medium"}

            metric = RoutingMetric(
                timestamp=datetime.now().isoformat(),
                file_name=f"test_{score}.pdf",
                file_size=1024,
                processor="docling",
                quality_score=score,
                is_born_digital=True,
                is_scanned=False,
                quality_tier="medium",
                processing_mode="standard",
                has_tables=False,
                layout_complexity=0.3,
                estimated_time=5.0,
            )
            metrics._metrics.append(metric)

        distribution = metrics.get_quality_distribution(bins=10)

        assert isinstance(distribution, dict)
        assert len(distribution) > 0

    def test_get_processing_times_by_tier(self, metrics):
        """Test processing times grouped by tier."""
        # Add metrics for different tiers
        tiers = ["high", "medium", "low"]
        for tier in tiers:
            for i in range(3):
                metric = RoutingMetric(
                    timestamp=datetime.now().isoformat(),
                    file_name=f"test_{tier}_{i}.pdf",
                    file_size=1024,
                    processor="docling",
                    quality_score=0.8,
                    is_born_digital=True,
                    is_scanned=False,
                    quality_tier=tier,
                    processing_mode="standard",
                    has_tables=False,
                    layout_complexity=0.3,
                    estimated_time=5.0,
                    actual_time=2.0 + i,
                )
                metrics._metrics.append(metric)

        times_by_tier = metrics.get_processing_times_by_tier()

        assert len(times_by_tier["high"]) == 3
        assert len(times_by_tier["medium"]) == 3
        assert len(times_by_tier["low"]) == 3

    def test_export_json(self, metrics, sample_route, tmp_path):
        """Test exporting metrics to JSON."""
        metrics.record_routing(sample_route)

        output_file = tmp_path / "metrics.json"
        metrics.export_json(output_file)

        assert output_file.exists()

        with open(output_file) as f:
            data = json.load(f)

        assert "metadata" in data
        assert "metrics" in data
        assert data["metadata"]["total_metrics"] == 1

    def test_export_summary(self, metrics, sample_route, tmp_path):
        """Test exporting summary to JSON."""
        metrics.record_routing(sample_route)
        metrics.record_processing_result(sample_route, success=True, processing_time=2.5)

        output_file = tmp_path / "summary.json"
        metrics.export_summary(output_file)

        assert output_file.exists()

        with open(output_file) as f:
            data = json.load(f)

        assert "summary" in data
        assert "quality_distribution" in data
        assert "processing_times_by_tier" in data

    def test_cleanup_old_metrics(self, metrics):
        """Test cleanup of old metrics."""
        # Add old metric
        old_metric = RoutingMetric(
            timestamp=(datetime.now() - timedelta(days=60)).isoformat(),
            file_name="old.pdf",
            file_size=1024,
            processor="docling",
            quality_score=0.8,
            is_born_digital=True,
            is_scanned=False,
            quality_tier="high",
            processing_mode="standard",
            has_tables=False,
            layout_complexity=0.3,
            estimated_time=5.0,
        )
        metrics._metrics.append(old_metric)

        # Add recent metric
        recent_metric = RoutingMetric(
            timestamp=datetime.now().isoformat(),
            file_name="recent.pdf",
            file_size=1024,
            processor="docling",
            quality_score=0.8,
            is_born_digital=True,
            is_scanned=False,
            quality_tier="high",
            processing_mode="standard",
            has_tables=False,
            layout_complexity=0.3,
            estimated_time=5.0,
        )
        metrics._metrics.append(recent_metric)

        removed = metrics.cleanup_old_metrics()

        assert removed == 1
        assert len(metrics._metrics) == 1
        assert metrics._metrics[0].file_name == "recent.pdf"

    def test_clear(self, metrics, sample_route):
        """Test clearing all metrics."""
        metrics.record_routing(sample_route)
        metrics.record_routing(sample_route)

        assert len(metrics._metrics) == 2

        metrics.clear()

        assert len(metrics._metrics) == 0

    def test_persistence(self, tmp_path, sample_route):
        """Test metrics persistence."""
        storage_dir = tmp_path / "metrics"

        # Create metrics with storage
        metrics = ProcessingMetrics(
            retention_days=30,
            storage_dir=storage_dir,
            auto_save=True,
        )

        # Record metric (should auto-save)
        metrics.record_routing(sample_route)

        # Verify files created
        assert (storage_dir / "routing_metrics.json").exists()
        assert (storage_dir / "routing_summary.json").exists()

        # Create new metrics instance (should load)
        metrics2 = ProcessingMetrics(
            retention_days=30,
            storage_dir=storage_dir,
            auto_save=False,
        )

        assert len(metrics2._metrics) == 1


class TestMetricsSummary:
    """Test MetricsSummary dataclass."""

    def test_summary_creation(self):
        """Test summary creation."""
        summary = MetricsSummary(
            total_documents=100,
            by_processor={"docling": 80, "legacy": 20},
            by_quality_tier={"high": 50, "medium": 30, "low": 20},
            avg_quality_score=0.78,
            avg_processing_time=2.5,
            success_rate=0.95,
            born_digital_rate=0.70,
            time_range=("2024-01-01", "2024-01-31"),
        )

        assert summary.total_documents == 100
        assert summary.by_processor["docling"] == 80
        assert summary.success_rate == 0.95
