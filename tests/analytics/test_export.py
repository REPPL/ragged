"""Tests for analytics export and visualisation.

v0.6.4 OPTIMISE-004 Phase 3: Data Export & Visualisation
"""

import tempfile
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from ragged.analytics.export import (
    ASCIIVisualiser,
    MetricsExporter,
    export_query_metrics_to_csv,
    export_summary_to_json,
    visualise_cache_effectiveness,
    visualise_latency_distribution,
    visualise_model_usage,
)
from ragged.analytics.models import CacheMetrics, QueryMetrics
from ragged.analytics.queries import MetricsQuery
from ragged.analytics.storage import MetricsStorage


@pytest.fixture
def sample_data():
    """Create sample data for testing."""
    return {
        "total_queries": 100,
        "avg_latency": 250.5,
        "cache_hit_rate": 0.65,
        "success_rate": 0.98,
        "timestamp": datetime.now(),
        "models": [
            {"model_id": "llama3.2:3b", "query_count": 60},
            {"model_id": "llama3.2:70b", "query_count": 40},
        ],
    }


@pytest.fixture
def populated_storage():
    """Create storage with sample data."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test_metrics.db"
        storage = MetricsStorage(db_path=db_path)

        now = datetime.now()

        # Add query metrics
        for i in range(10):
            metrics = QueryMetrics(
                query_id=f"query-{i}",
                query_hash=f"hash-{i}",
                timestamp=now - timedelta(minutes=i * 12),
                query_length=50 + i * 5,
                query_type="factual",
                total_latency_ms=200.0 + i * 50,
                selected_model="llama3.2:3b" if i % 2 == 0 else "llama3.2:70b",
                cache_hit=i % 3 == 0,
                success=True,
            )
            storage.store_query_metrics(metrics)

        # Add cache metrics
        for cache_layer in ["query_classification", "retrieval_results"]:
            metrics = CacheMetrics(
                cache_layer=cache_layer,
                timestamp=now - timedelta(minutes=30),
                total_requests=1000,
                cache_hits=600 if cache_layer == "query_classification" else 400,
                cache_misses=400 if cache_layer == "query_classification" else 600,
                hit_rate=0.6 if cache_layer == "query_classification" else 0.4,
                avg_hit_latency_ms=5.0,
                avg_miss_latency_ms=200.0,
                latency_saved_ms=117000.0,
                cache_size_entries=500,
                cache_size_bytes=1024 * 1024,
                cache_size_mb=1.0,
            )
            storage.store_cache_metrics(metrics)

        yield storage


class TestMetricsExporter:
    """Test suite for MetricsExporter."""

    def test_export_to_json_string(self, sample_data):
        """Test JSON export to string."""
        json_str = MetricsExporter.export_to_json(sample_data, pretty=True)

        assert "total_queries" in json_str
        assert "100" in json_str
        assert "avg_latency" in json_str
        assert "250.5" in json_str

    def test_export_to_json_file(self, sample_data):
        """Test JSON export to file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "export.json"

            json_str = MetricsExporter.export_to_json(
                sample_data, file_path=file_path, pretty=True
            )

            # File should exist
            assert file_path.exists()

            # Content should match
            assert file_path.read_text() == json_str

    def test_export_to_json_datetime_conversion(self, sample_data):
        """Test datetime objects are converted to ISO format."""
        json_str = MetricsExporter.export_to_json(sample_data, pretty=False)

        # Datetime should be ISO format string
        assert "T" in json_str  # ISO format includes 'T'
        assert sample_data["timestamp"].isoformat() in json_str

    def test_export_to_csv(self):
        """Test CSV export."""
        data = [
            {"query_id": "q1", "latency_ms": 250.5, "success": True},
            {"query_id": "q2", "latency_ms": 180.2, "success": True},
            {"query_id": "q3", "latency_ms": 320.8, "success": False},
        ]

        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "export.csv"

            MetricsExporter.export_to_csv(data, file_path)

            # File should exist
            assert file_path.exists()

            # Read and verify content
            content = file_path.read_text()
            assert "query_id" in content
            assert "latency_ms" in content
            assert "q1" in content
            assert "250.5" in content

    def test_export_to_csv_empty_data(self):
        """Test CSV export with empty data."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "export.csv"

            MetricsExporter.export_to_csv([], file_path)

            # File should not be created for empty data
            assert not file_path.exists()

    def test_export_to_csv_custom_fieldnames(self):
        """Test CSV export with custom fieldnames."""
        data = [
            {"query_id": "q1", "latency_ms": 250.5, "extra_field": "ignored"},
            {"query_id": "q2", "latency_ms": 180.2, "extra_field": "also_ignored"},
        ]

        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "export.csv"

            MetricsExporter.export_to_csv(
                data, file_path, fieldnames=["query_id", "latency_ms"]
            )

            content = file_path.read_text()
            assert "query_id" in content
            assert "latency_ms" in content
            assert "extra_field" not in content  # Should be excluded


class TestASCIIVisualiser:
    """Test suite for ASCIIVisualiser."""

    def test_bar_chart_basic(self):
        """Test basic bar chart creation."""
        data = {"Model A": 100, "Model B": 75, "Model C": 50}

        chart = ASCIIVisualiser.bar_chart(data, title="Model Usage")

        assert "Model Usage" in chart
        assert "Model A" in chart
        assert "Model B" in chart
        assert "Model C" in chart
        assert "█" in chart  # Should contain bar characters

    def test_bar_chart_empty_data(self):
        """Test bar chart with empty data."""
        chart = ASCIIVisualiser.bar_chart({})
        assert "No data" in chart

    def test_bar_chart_show_values(self):
        """Test bar chart with value display."""
        data = {"Item 1": 42.5, "Item 2": 30.2}

        chart = ASCIIVisualiser.bar_chart(data, show_values=True)

        assert "42.5" in chart or "42.50" in chart
        assert "30.2" in chart or "30.20" in chart

    def test_bar_chart_hide_values(self):
        """Test bar chart without value display."""
        data = {"Item 1": 42.5, "Item 2": 30.2}

        chart = ASCIIVisualiser.bar_chart(data, show_values=False)

        # Values should not appear
        assert "42.5" not in chart
        assert "30.2" not in chart

    def test_line_chart_basic(self):
        """Test basic line chart creation."""
        data = [
            ("Mon", 100),
            ("Tue", 120),
            ("Wed", 110),
            ("Thu", 130),
            ("Fri", 125),
        ]

        chart = ASCIIVisualiser.line_chart(data, title="Query Volume")

        assert "Query Volume" in chart
        assert "Mon" in chart
        assert "Fri" in chart
        assert "●" in chart or "·" in chart  # Should contain plot characters

    def test_line_chart_empty_data(self):
        """Test line chart with empty data."""
        chart = ASCIIVisualiser.line_chart([])
        assert "No data" in chart

    def test_summary_table_basic(self):
        """Test basic summary table creation."""
        data = {
            "Total Queries": 1000,
            "Average Latency": 250.5,
            "Cache Hit Rate": 0.65,
        }

        table = ASCIIVisualiser.summary_table(data, title="Summary Stats")

        assert "Summary Stats" in table
        assert "Total Queries" in table
        assert "1000" in table
        assert "Average Latency" in table
        assert "250.5" in table or "250.50" in table

    def test_summary_table_empty_data(self):
        """Test summary table with empty data."""
        table = ASCIIVisualiser.summary_table({})
        assert "No data" in table


class TestExportHelpers:
    """Test suite for export helper functions."""

    def test_export_summary_to_json(self, populated_storage):
        """Test exporting summary to JSON."""
        query = MetricsQuery(db_path=populated_storage.db_path)

        json_str = export_summary_to_json(query)

        assert "query_stats" in json_str
        assert "model_usage" in json_str
        assert "domain_distribution" in json_str

    def test_export_summary_to_json_with_file(self, populated_storage):
        """Test exporting summary to JSON file."""
        query = MetricsQuery(db_path=populated_storage.db_path)

        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "summary.json"

            json_str = export_summary_to_json(query, file_path=file_path)

            assert file_path.exists()
            assert file_path.read_text() == json_str

    def test_export_query_metrics_to_csv(self, populated_storage):
        """Test exporting query metrics to CSV."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "queries.csv"

            export_query_metrics_to_csv(populated_storage, file_path)

            assert file_path.exists()
            content = file_path.read_text()
            assert "query_id" in content
            assert "total_latency_ms" in content

    def test_visualise_latency_distribution(self, populated_storage):
        """Test latency distribution visualisation."""
        query = MetricsQuery(db_path=populated_storage.db_path)

        chart = visualise_latency_distribution(query)

        assert "Latency Distribution" in chart
        assert "p50" in chart
        assert "p95" in chart
        assert "p99" in chart

    def test_visualise_model_usage(self, populated_storage):
        """Test model usage visualisation."""
        query = MetricsQuery(db_path=populated_storage.db_path)

        chart = visualise_model_usage(query)

        assert "Model Usage" in chart
        assert "llama3.2:3b" in chart or "llama3.2:70b" in chart

    def test_visualise_cache_effectiveness(self, populated_storage):
        """Test cache effectiveness visualisation."""
        query = MetricsQuery(db_path=populated_storage.db_path)

        chart = visualise_cache_effectiveness(query)

        assert "Cache Hit Rates" in chart
        assert "query_classification" in chart or "retrieval_results" in chart
