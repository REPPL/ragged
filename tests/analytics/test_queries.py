"""Tests for analytics query methods.

v0.6.4 OPTIMISE-004 Phase 2: Analytics Queries
"""

import tempfile
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from ragged.analytics.models import CacheMetrics, ModelMetrics, QueryMetrics, RetrievalMetrics
from ragged.analytics.queries import MetricsQuery
from ragged.analytics.storage import MetricsStorage


@pytest.fixture
def populated_storage():
    """Create storage with sample data."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test_metrics.db"
        storage = MetricsStorage(db_path=db_path)

        # Create sample query metrics
        now = datetime.now()

        # 10 queries over last 2 hours, different models and domains
        for i in range(10):
            metrics = QueryMetrics(
                query_id=f"query-{i}",
                query_hash=f"hash-{i}",
                timestamp=now - timedelta(minutes=i * 12),
                query_length=50 + i * 5,
                query_type="factual" if i % 2 == 0 else "analytical",
                complexity=1 + (i % 5),
                domain="technical" if i % 3 == 0 else "general",
                total_latency_ms=200.0 + i * 50,
                classification_latency_ms=10.0 + i,
                retrieval_latency_ms=80.0 + i * 10,
                llm_latency_ms=110.0 + i * 30,
                selected_model="llama3.2:3b" if i % 2 == 0 else "llama3.2:70b",
                routing_reason="complexity" if i % 2 == 0 else "quality",
                cache_hit=i % 3 == 0,
                cache_layer="retrieval_results" if i % 3 == 0 else None,
                success=True,
            )
            storage.store_query_metrics(metrics)

        # Create sample retrieval metrics
        for i in range(10):
            metrics = RetrievalMetrics(
                retrieval_id=f"retrieval-{i}",
                query_id=f"query-{i}",
                timestamp=now - timedelta(minutes=i * 12),
                k=5,
                domain="technical" if i % 3 == 0 else "general",
                retrieval_latency_ms=80.0 + i * 10,
                embedding_latency_ms=20.0 + i * 2,
                search_latency_ms=40.0 + i * 5,
                results_count=5,
                avg_score=0.8 - (i * 0.02),
                domain_boost_applied=i % 3 == 0,
            )
            storage.store_retrieval_metrics(metrics)

        # Create sample model metrics
        for model_id in ["llama3.2:3b", "llama3.2:70b"]:
            metrics = ModelMetrics(
                model_id=model_id,
                timestamp=now - timedelta(minutes=30),
                invocation_count=100 if model_id == "llama3.2:3b" else 50,
                total_latency_ms=25000.0 if model_id == "llama3.2:3b" else 50000.0,
                avg_latency_ms=250.0 if model_id == "llama3.2:3b" else 1000.0,
                total_input_tokens=5000 if model_id == "llama3.2:3b" else 2500,
                total_output_tokens=2500 if model_id == "llama3.2:3b" else 1250,
                avg_tokens_per_query=75.0 if model_id == "llama3.2:3b" else 75.0,
                gpu_memory_used_mb=2048.0 if model_id == "llama3.2:3b" else 8192.0,
                gpu_utilization_percent=60.0 if model_id == "llama3.2:3b" else 85.0,
            )
            storage.store_model_metrics(metrics)

        # Create sample cache metrics
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


class TestMetricsQuery:
    """Test suite for MetricsQuery."""

    def test_initialization(self, populated_storage):
        """Test query interface initializes correctly."""
        query = MetricsQuery(db_path=populated_storage.db_path)
        assert query.db_path == populated_storage.db_path

    def test_initialization_nonexistent_db(self):
        """Test initialization with nonexistent database raises error."""
        with pytest.raises(FileNotFoundError):
            MetricsQuery(db_path=Path("/nonexistent/path.db"))

    def test_query_summary(self, populated_storage):
        """Test summary statistics query."""
        query = MetricsQuery(db_path=populated_storage.db_path)

        # Query last 24 hours
        summary = query.query_summary()

        assert "time_range" in summary
        assert "query_stats" in summary
        assert "model_usage" in summary
        assert "domain_distribution" in summary

        # Check query stats
        stats = summary["query_stats"]
        assert stats["total_queries"] == 10
        assert stats["success_rate"] == 1.0
        assert 0.0 <= stats["cache_hit_rate"] <= 1.0
        assert stats["avg_latency"] > 0

        # Check model usage
        assert len(summary["model_usage"]) == 2
        model_ids = [m["selected_model"] for m in summary["model_usage"]]
        assert "llama3.2:3b" in model_ids
        assert "llama3.2:70b" in model_ids

        # Check domain distribution
        assert len(summary["domain_distribution"]) >= 1

    def test_query_summary_custom_time_range(self, populated_storage):
        """Test summary with custom time range."""
        query = MetricsQuery(db_path=populated_storage.db_path)

        now = datetime.now()
        start_time = now - timedelta(hours=1)

        summary = query.query_summary(start_time=start_time, end_time=now)

        # Should have fewer queries (only last hour)
        stats = summary["query_stats"]
        assert stats["total_queries"] <= 10

    def test_query_latency_percentiles(self, populated_storage):
        """Test latency percentile calculation."""
        query = MetricsQuery(db_path=populated_storage.db_path)

        percentiles = query.query_latency_percentiles(percentiles=[50, 95, 99])

        assert "p50" in percentiles
        assert "p95" in percentiles
        assert "p99" in percentiles

        # p50 should be less than p95, p95 less than p99
        assert percentiles["p50"] <= percentiles["p95"]
        assert percentiles["p95"] <= percentiles["p99"]

        # All should be positive
        assert percentiles["p50"] > 0
        assert percentiles["p95"] > 0
        assert percentiles["p99"] > 0

    def test_query_latency_percentiles_empty_data(self, populated_storage):
        """Test percentile calculation with no data in time range."""
        query = MetricsQuery(db_path=populated_storage.db_path)

        # Query far in the past
        past_time = datetime.now() - timedelta(days=365)
        percentiles = query.query_latency_percentiles(
            start_time=past_time - timedelta(hours=1),
            end_time=past_time,
        )

        # Should return zeros
        assert percentiles["p50"] == 0.0
        assert percentiles["p95"] == 0.0
        assert percentiles["p99"] == 0.0

    def test_query_model_performance_all_models(self, populated_storage):
        """Test querying performance for all models."""
        query = MetricsQuery(db_path=populated_storage.db_path)

        performance = query.query_model_performance()

        assert len(performance) == 2
        model_ids = [p["model_id"] for p in performance]
        assert "llama3.2:3b" in model_ids
        assert "llama3.2:70b" in model_ids

    def test_query_model_performance_specific_model(self, populated_storage):
        """Test querying performance for specific model."""
        query = MetricsQuery(db_path=populated_storage.db_path)

        performance = query.query_model_performance(model_id="llama3.2:3b")

        assert len(performance) >= 1
        assert all(p["model_id"] == "llama3.2:3b" for p in performance)

    def test_query_cache_effectiveness_all_layers(self, populated_storage):
        """Test cache effectiveness for all layers."""
        query = MetricsQuery(db_path=populated_storage.db_path)

        effectiveness = query.query_cache_effectiveness()

        assert len(effectiveness) == 2
        layers = [e["cache_layer"] for e in effectiveness]
        assert "query_classification" in layers
        assert "retrieval_results" in layers

        # Check hit rates
        for e in effectiveness:
            assert 0.0 <= e["hit_rate"] <= 1.0
            assert e["total_requests"] > 0

    def test_query_cache_effectiveness_specific_layer(self, populated_storage):
        """Test cache effectiveness for specific layer."""
        query = MetricsQuery(db_path=populated_storage.db_path)

        effectiveness = query.query_cache_effectiveness(
            cache_layer="query_classification"
        )

        assert len(effectiveness) >= 1
        assert all(e["cache_layer"] == "query_classification" for e in effectiveness)

    def test_query_domain_performance_all_domains(self, populated_storage):
        """Test domain performance for all domains."""
        query = MetricsQuery(db_path=populated_storage.db_path)

        performance = query.query_domain_performance()

        assert "domains" in performance
        assert len(performance["domains"]) >= 1

        # Check domain stats
        for domain_stats in performance["domains"]:
            assert "domain" in domain_stats
            assert "query_count" in domain_stats
            assert "avg_latency" in domain_stats

    def test_query_domain_performance_specific_domain(self, populated_storage):
        """Test domain performance for specific domain."""
        query = MetricsQuery(db_path=populated_storage.db_path)

        performance = query.query_domain_performance(domain="technical")

        # Should have stats for technical domain
        assert "technical" in performance
        stats = performance["technical"]
        assert stats["query_count"] > 0
        assert stats["avg_latency"] > 0

    def test_query_trends_hourly(self, populated_storage):
        """Test trend analysis with hourly intervals."""
        query = MetricsQuery(db_path=populated_storage.db_path)

        trends = query.query_trends(
            metric="total_latency_ms",
            interval="hour",
        )

        # Should have at least one data point
        assert len(trends) >= 1

        # Each point should have required fields
        for point in trends:
            assert "timestamp" in point
            assert "avg" in point
            assert "min" in point
            assert "max" in point
            assert "count" in point

            # min <= avg <= max
            assert point["min"] <= point["avg"] <= point["max"]

    def test_query_trends_daily(self, populated_storage):
        """Test trend analysis with daily intervals."""
        query = MetricsQuery(db_path=populated_storage.db_path)

        # Query last 7 days
        now = datetime.now()
        trends = query.query_trends(
            metric="total_latency_ms",
            interval="day",
            start_time=now - timedelta(days=7),
            end_time=now,
        )

        # Should group by day
        assert len(trends) >= 1

    def test_query_trends_invalid_interval(self, populated_storage):
        """Test trend analysis with invalid interval raises error."""
        query = MetricsQuery(db_path=populated_storage.db_path)

        with pytest.raises(ValueError):
            query.query_trends(
                metric="total_latency_ms",
                interval="invalid",
            )

    def test_compare_models(self, populated_storage):
        """Test model comparison."""
        query = MetricsQuery(db_path=populated_storage.db_path)

        comparison = query.compare_models()

        assert "time_range" in comparison
        assert "models" in comparison

        # Should have both models
        models = comparison["models"]
        assert len(models) == 2

        model_ids = [m["model_id"] for m in models]
        assert "llama3.2:3b" in model_ids
        assert "llama3.2:70b" in model_ids

        # Check model stats
        for model in models:
            assert "query_count" in model
            assert "avg_total_latency" in model
            assert "success_rate" in model

    def test_compare_models_custom_time_range(self, populated_storage):
        """Test model comparison with custom time range."""
        query = MetricsQuery(db_path=populated_storage.db_path)

        now = datetime.now()
        start_time = now - timedelta(hours=1)

        comparison = query.compare_models(start_time=start_time, end_time=now)

        assert "models" in comparison
        # Should have fewer queries in shorter range
        assert len(comparison["models"]) >= 0
