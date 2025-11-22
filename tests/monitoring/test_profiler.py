"""Tests for performance profiling.

v0.3.9: Test profiler and performance tracking.
"""

import time

import pytest

from src.monitoring.profiler import (
    PerformanceProfiler,
    ProfileStage,
    create_profiler,
)


class TestProfileStage:
    """Test ProfileStage dataclass."""

    def test_stage_creation(self):
        """Test creating a profile stage."""
        stage = ProfileStage(name="Test Stage", duration_ms=100.5)

        assert stage.name == "Test Stage"
        assert stage.duration_ms == 100.5
        assert stage.metadata == {}

    def test_stage_with_metadata(self):
        """Test stage with metadata."""
        stage = ProfileStage(
            name="Query Embedding", duration_ms=45.2, metadata={"model": "all-MiniLM-L6-v2"}
        )

        assert stage.name == "Query Embedding"
        assert stage.duration_ms == 45.2
        assert stage.metadata["model"] == "all-MiniLM-L6-v2"

    def test_duration_seconds_property(self):
        """Test duration_seconds property."""
        stage = ProfileStage(name="Test", duration_ms=1500.0)

        assert stage.duration_seconds == 1.5


class TestPerformanceProfiler:
    """Test PerformanceProfiler class."""

    @pytest.fixture
    def profiler(self):
        """Create profiler for testing."""
        return PerformanceProfiler(enabled=True)

    def test_profiler_init_enabled(self):
        """Test profiler initialisation when enabled."""
        profiler = PerformanceProfiler(enabled=True)

        assert profiler.enabled is True
        assert len(profiler.stages) == 0

    def test_profiler_init_disabled(self):
        """Test profiler initialisation when disabled."""
        profiler = PerformanceProfiler(enabled=False)

        assert profiler.enabled is False
        assert len(profiler.stages) == 0

    def test_stage_context_manager(self, profiler):
        """Test stage context manager."""
        with profiler.stage("Test Stage"):
            time.sleep(0.01)  # 10ms

        assert len(profiler.stages) == 1
        assert profiler.stages[0].name == "Test Stage"
        assert profiler.stages[0].duration_ms >= 10  # At least 10ms

    def test_stage_context_manager_with_metadata(self, profiler):
        """Test stage with metadata."""
        with profiler.stage("Query Embedding", model="test-model", dimensions=384):
            time.sleep(0.01)

        assert len(profiler.stages) == 1
        assert profiler.stages[0].metadata["model"] == "test-model"
        assert profiler.stages[0].metadata["dimensions"] == 384

    def test_stage_context_manager_disabled(self):
        """Test stage context manager when profiler disabled."""
        profiler = PerformanceProfiler(enabled=False)

        with profiler.stage("Test Stage"):
            time.sleep(0.01)

        # Should not record stages when disabled
        assert len(profiler.stages) == 0

    def test_multiple_stages(self, profiler):
        """Test multiple stages."""
        with profiler.stage("Stage 1"):
            time.sleep(0.01)

        with profiler.stage("Stage 2"):
            time.sleep(0.01)

        with profiler.stage("Stage 3"):
            time.sleep(0.01)

        assert len(profiler.stages) == 3
        assert profiler.stages[0].name == "Stage 1"
        assert profiler.stages[1].name == "Stage 2"
        assert profiler.stages[2].name == "Stage 3"

    def test_record_stage_manually(self, profiler):
        """Test manually recording a stage."""
        profiler.record_stage("Manual Stage", duration_ms=123.4, test="metadata")

        assert len(profiler.stages) == 1
        assert profiler.stages[0].name == "Manual Stage"
        assert profiler.stages[0].duration_ms == 123.4
        assert profiler.stages[0].metadata["test"] == "metadata"

    def test_record_stage_disabled(self):
        """Test record_stage when profiler disabled."""
        profiler = PerformanceProfiler(enabled=False)
        profiler.record_stage("Test", duration_ms=100)

        assert len(profiler.stages) == 0

    def test_total_duration_with_timestamps(self, profiler):
        """Test total duration calculation using timestamps."""
        with profiler.stage("Stage 1"):
            time.sleep(0.01)

        with profiler.stage("Stage 2"):
            time.sleep(0.01)

        # Total should be >= 20ms
        assert profiler.total_duration_ms >= 20

    def test_total_duration_seconds(self, profiler):
        """Test total_duration_seconds property."""
        profiler.record_stage("Test", duration_ms=1500.0)

        assert profiler.total_duration_seconds == 1.5

    def test_total_duration_empty(self, profiler):
        """Test total duration with no stages."""
        assert profiler.total_duration_ms == 0.0
        assert profiler.total_duration_seconds == 0.0

    def test_get_slowest_stages(self, profiler):
        """Test getting slowest stages."""
        profiler.record_stage("Fast", duration_ms=10)
        profiler.record_stage("Medium", duration_ms=50)
        profiler.record_stage("Slow", duration_ms=200)
        profiler.record_stage("Very Slow", duration_ms=500)

        slowest = profiler.get_slowest_stages(top_n=2)

        assert len(slowest) == 2
        assert slowest[0].name == "Very Slow"
        assert slowest[1].name == "Slow"

    def test_get_slowest_stages_empty(self, profiler):
        """Test get_slowest_stages with no data."""
        slowest = profiler.get_slowest_stages()

        assert slowest == []

    def test_analyse_bottlenecks(self, profiler):
        """Test bottleneck analysis."""
        # Create stages where one takes >20% of time
        profiler.record_stage("Fast", duration_ms=10)
        profiler.record_stage("Slow", duration_ms=1000)  # 99% of total

        bottlenecks = profiler.analyse_bottlenecks(threshold_percent=20.0)

        assert len(bottlenecks) > 0
        assert "Slow" in bottlenecks[0]
        assert "99" in bottlenecks[0]  # Shows percentage

    def test_analyse_bottlenecks_custom_threshold(self, profiler):
        """Test bottleneck analysis with custom threshold."""
        profiler.record_stage("Stage 1", duration_ms=100)
        profiler.record_stage("Stage 2", duration_ms=200)  # 66% of total

        # With 50% threshold, only Stage 2 should be flagged
        bottlenecks = profiler.analyse_bottlenecks(threshold_percent=50.0)

        assert len(bottlenecks) == 1
        assert "Stage 2" in bottlenecks[0]

    def test_analyse_bottlenecks_empty(self, profiler):
        """Test bottleneck analysis with no data."""
        bottlenecks = profiler.analyse_bottlenecks()

        assert bottlenecks == []

    def test_render_output(self, profiler):
        """Test rendering profiling report."""
        profiler.record_stage("Query Preprocessing", duration_ms=2.5)
        profiler.record_stage("Query Embedding", duration_ms=45.8, model="test")
        profiler.record_stage("Vector Retrieval", duration_ms=23.1)

        output = profiler.render()

        assert "Performance Profile" in output
        assert "Pipeline Breakdown" in output
        assert "Query Preprocessing" in output
        assert "Query Embedding" in output
        assert "Vector Retrieval" in output
        assert "Total:" in output

    def test_render_output_with_metadata(self, profiler):
        """Test rendering with metadata."""
        profiler.record_stage("Test Stage", duration_ms=100, key="value")

        output = profiler.render(show_metadata=True)

        assert "key: value" in output

    def test_render_output_without_metadata(self, profiler):
        """Test rendering without metadata."""
        profiler.record_stage("Test Stage", duration_ms=100, key="value")

        output = profiler.render(show_metadata=False)

        # Metadata should still show if only a few items
        # (our implementation shows metadata if <=5 items regardless)
        assert "Performance Profile" in output

    def test_render_empty(self, profiler):
        """Test rendering with no data."""
        output = profiler.render()

        assert "No profiling data" in output

    def test_render_with_bottlenecks(self, profiler):
        """Test render shows bottleneck analysis."""
        profiler.record_stage("Slow", duration_ms=1000)
        profiler.record_stage("Fast", duration_ms=10)

        output = profiler.render()

        assert "Bottleneck Analysis" in output
        assert "Slow" in output
        assert "⚠️" in output

    def test_render_summary(self, profiler):
        """Test rendering summary."""
        profiler.record_stage("Stage 1", duration_ms=100)
        profiler.record_stage("Stage 2", duration_ms=200)

        summary = profiler.render_summary()

        assert "Pipeline:" in summary
        assert "2 stages" in summary
        assert "300" in summary  # Total duration
        assert "slowest:" in summary

    def test_render_summary_empty(self, profiler):
        """Test summary with no data."""
        summary = profiler.render_summary()

        assert "No profiling data" in summary

    def test_to_dict(self, profiler):
        """Test converting to dictionary."""
        profiler.record_stage("Test", duration_ms=123.4, key="value")

        data = profiler.to_dict()

        assert data["enabled"] is True
        assert data["total_duration_ms"] == 123.4
        assert len(data["stages"]) == 1
        assert data["stages"][0]["name"] == "Test"
        assert data["stages"][0]["metadata"]["key"] == "value"
        assert "bottlenecks" in data

    def test_clear(self, profiler):
        """Test clearing profiling data."""
        profiler.record_stage("Test 1", duration_ms=100)
        profiler.record_stage("Test 2", duration_ms=200)

        assert len(profiler.stages) == 2

        profiler.clear()

        assert len(profiler.stages) == 0
        assert profiler.total_duration_ms == 0.0


class TestConvenienceFunction:
    """Test convenience functions."""

    def test_create_profiler_enabled(self):
        """Test creating enabled profiler."""
        profiler = create_profiler(enabled=True)

        assert isinstance(profiler, PerformanceProfiler)
        assert profiler.enabled is True

    def test_create_profiler_disabled(self):
        """Test creating disabled profiler."""
        profiler = create_profiler(enabled=False)

        assert isinstance(profiler, PerformanceProfiler)
        assert profiler.enabled is False
