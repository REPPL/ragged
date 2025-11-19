"""Tests for adaptive performance tuning.

v0.2.9: Tests for workload detection and automatic parameter optimisation.
"""

import pytest
import time
import threading
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

from src.utils.adaptive_tuning import (
    HardwareCapabilities,
    WorkloadProfile,
    TuningRecommendations,
    AdaptiveTuner,
    get_tuner,
)


class TestHardwareCapabilities:
    """Tests for HardwareCapabilities."""

    def test_initialization(self):
        """Test hardware capabilities initialization."""
        hw = HardwareCapabilities(
            cpu_count=8,
            total_memory_gb=16.0,
            available_memory_gb=8.0,
            has_gpu=True
        )

        assert hw.cpu_count == 8
        assert hw.total_memory_gb == 16.0
        assert hw.available_memory_gb == 8.0
        assert hw.has_gpu is True

    def test_recommended_workers(self):
        """Test recommended worker count."""
        hw = HardwareCapabilities(
            cpu_count=8,
            total_memory_gb=16.0,
            available_memory_gb=8.0
        )

        workers = hw.get_recommended_workers()
        assert workers == 6  # 75% of 8 = 6

    def test_recommended_workers_minimum(self):
        """Test minimum worker count."""
        hw = HardwareCapabilities(
            cpu_count=1,
            total_memory_gb=2.0,
            available_memory_gb=1.0
        )

        workers = hw.get_recommended_workers()
        assert workers == 1  # Minimum 1

    def test_batch_size_bulk_mode(self):
        """Test batch size recommendation for bulk ingestion."""
        hw = HardwareCapabilities(
            cpu_count=8,
            total_memory_gb=16.0,
            available_memory_gb=8.0
        )

        batch_size = hw.get_recommended_batch_size("bulk_ingestion")
        assert 100 <= batch_size <= 1000

    def test_batch_size_interactive_mode(self):
        """Test batch size recommendation for interactive queries."""
        hw = HardwareCapabilities(
            cpu_count=8,
            total_memory_gb=16.0,
            available_memory_gb=8.0
        )

        batch_size = hw.get_recommended_batch_size("interactive_query")
        assert 10 <= batch_size <= 100

    def test_batch_size_mixed_mode(self):
        """Test batch size recommendation for mixed workload."""
        hw = HardwareCapabilities(
            cpu_count=8,
            total_memory_gb=16.0,
            available_memory_gb=8.0
        )

        batch_size = hw.get_recommended_batch_size("mixed")
        assert 50 <= batch_size <= 500

    def test_cache_size_interactive_mode(self):
        """Test cache size recommendation for interactive mode."""
        hw = HardwareCapabilities(
            cpu_count=8,
            total_memory_gb=16.0,
            available_memory_gb=8.0
        )

        cache_size = hw.get_recommended_cache_size("interactive_query")
        assert cache_size >= 100  # Minimum
        assert cache_size <= 10000  # Maximum

    def test_cache_size_bulk_mode(self):
        """Test cache size recommendation for bulk mode."""
        hw = HardwareCapabilities(
            cpu_count=8,
            total_memory_gb=16.0,
            available_memory_gb=8.0
        )

        cache_size = hw.get_recommended_cache_size("bulk_ingestion")
        assert cache_size >= 50
        assert cache_size <= 1000


class TestWorkloadProfile:
    """Tests for WorkloadProfile."""

    def test_initialization(self):
        """Test workload profile initialization."""
        profile = WorkloadProfile()

        assert profile.query_rate == 0.0
        assert profile.ingestion_rate == 0.0
        assert profile.avg_query_time == 0.0
        assert profile.avg_doc_size == 0.0

    def test_update_query(self):
        """Test recording query execution."""
        profile = WorkloadProfile()

        profile.update_query(query_time=0.5)

        assert len(profile.recent_queries) == 1
        assert profile.recent_queries[0]["duration"] == 0.5

    def test_query_rate_calculation(self):
        """Test query rate calculation."""
        profile = WorkloadProfile()

        # Record 10 queries
        for _ in range(10):
            profile.update_query(query_time=0.5)

        # Should count all 10 (within 1 minute)
        assert profile.query_rate == 10

    def test_avg_query_time_calculation(self):
        """Test average query time calculation."""
        profile = WorkloadProfile()

        profile.update_query(query_time=0.3)
        profile.update_query(query_time=0.5)
        profile.update_query(query_time=0.7)

        # Average should be 0.5
        assert profile.avg_query_time == pytest.approx(0.5)

    def test_update_ingestion(self):
        """Test recording document ingestion."""
        profile = WorkloadProfile()

        profile.update_ingestion(doc_size_kb=10.5)

        assert len(profile.recent_ingestions) == 1
        assert profile.recent_ingestions[0]["size_kb"] == 10.5

    def test_ingestion_rate_calculation(self):
        """Test ingestion rate calculation."""
        profile = WorkloadProfile()

        # Record 20 ingestions
        for _ in range(20):
            profile.update_ingestion(doc_size_kb=10.0)

        assert profile.ingestion_rate == 20

    def test_avg_doc_size_calculation(self):
        """Test average document size calculation."""
        profile = WorkloadProfile()

        profile.update_ingestion(doc_size_kb=5.0)
        profile.update_ingestion(doc_size_kb=10.0)
        profile.update_ingestion(doc_size_kb=15.0)

        # Average should be 10.0
        assert profile.avg_doc_size == pytest.approx(10.0)

    def test_detect_bulk_ingestion_mode(self):
        """Test detection of bulk ingestion mode."""
        profile = WorkloadProfile()

        # Simulate bulk ingestion: high ingestion rate, low query rate
        for _ in range(60):
            profile.update_ingestion(doc_size_kb=10.0)

        for _ in range(2):
            profile.update_query(query_time=0.5)

        mode = profile.detect_mode()
        assert mode == "bulk_ingestion"

    def test_detect_interactive_query_mode(self):
        """Test detection of interactive query mode."""
        profile = WorkloadProfile()

        # Simulate interactive queries: high query rate, low ingestion
        for _ in range(15):
            profile.update_query(query_time=0.5)

        for _ in range(2):
            profile.update_ingestion(doc_size_kb=10.0)

        mode = profile.detect_mode()
        assert mode == "interactive_query"

    def test_detect_mixed_mode(self):
        """Test detection of mixed workload mode."""
        profile = WorkloadProfile()

        # Both queries and ingestion active
        for _ in range(15):
            profile.update_query(query_time=0.5)

        for _ in range(20):
            profile.update_ingestion(doc_size_kb=10.0)

        mode = profile.detect_mode()
        assert mode == "mixed"

    def test_detect_idle_mode(self):
        """Test detection of idle mode."""
        profile = WorkloadProfile()

        # Very low activity
        profile.update_query(query_time=0.5)
        profile.update_ingestion(doc_size_kb=10.0)

        mode = profile.detect_mode()
        assert mode == "idle"

    def test_recent_history_limit(self):
        """Test recent history is limited to 100 entries."""
        profile = WorkloadProfile()

        # Add more than 100 entries
        for _ in range(150):
            profile.update_query(query_time=0.5)

        # Should only keep last 100
        assert len(profile.recent_queries) == 100


class TestTuningRecommendations:
    """Tests for TuningRecommendations."""

    def test_initialization(self):
        """Test recommendations initialization."""
        rec = TuningRecommendations(
            mode="interactive_query",
            batch_size=100,
            cache_size=5000,
            worker_count=4
        )

        assert rec.mode == "interactive_query"
        assert rec.batch_size == 100
        assert rec.cache_size == 5000
        assert rec.worker_count == 4

    def test_to_dict(self):
        """Test conversion to dictionary."""
        rec = TuningRecommendations(
            mode="bulk_ingestion",
            batch_size=500,
            cache_size=1000,
            worker_count=6,
            enable_query_cache=False,
            enable_embedding_cache=True,
            chunk_size=1024,
            chunk_overlap=100
        )

        result = rec.to_dict()

        assert result["mode"] == "bulk_ingestion"
        assert result["batch_size"] == 500
        assert result["cache_size"] == 1000
        assert result["worker_count"] == 6
        assert result["enable_query_cache"] is False
        assert result["enable_embedding_cache"] is True
        assert result["chunk_size"] == 1024
        assert result["chunk_overlap"] == 100


class TestAdaptiveTuner:
    """Tests for AdaptiveTuner."""

    @patch("src.utils.adaptive_tuning.os.cpu_count", return_value=8)
    @patch("src.utils.adaptive_tuning.psutil.virtual_memory")
    def test_initialization(self, mock_memory, mock_cpu):
        """Test tuner initialization."""
        mock_memory.return_value.total = 16 * (1024 ** 3)  # 16GB
        mock_memory.return_value.available = 8 * (1024 ** 3)  # 8GB

        tuner = AdaptiveTuner()

        assert tuner.hardware.cpu_count == 8
        assert tuner.hardware.total_memory_gb == pytest.approx(16.0, abs=0.1)
        assert tuner.hardware.available_memory_gb == pytest.approx(8.0, abs=0.1)

    @patch("src.utils.adaptive_tuning.os.cpu_count", return_value=4)
    @patch("src.utils.adaptive_tuning.psutil.virtual_memory")
    def test_record_query(self, mock_memory, mock_cpu):
        """Test recording query execution."""
        mock_memory.return_value.total = 8 * (1024 ** 3)
        mock_memory.return_value.available = 4 * (1024 ** 3)

        tuner = AdaptiveTuner()
        tuner.record_query(query_time=0.5)

        assert len(tuner.workload.recent_queries) == 1
        assert tuner.workload.recent_queries[0]["duration"] == 0.5

    @patch("src.utils.adaptive_tuning.os.cpu_count", return_value=4)
    @patch("src.utils.adaptive_tuning.psutil.virtual_memory")
    def test_record_ingestion(self, mock_memory, mock_cpu):
        """Test recording document ingestion."""
        mock_memory.return_value.total = 8 * (1024 ** 3)
        mock_memory.return_value.available = 4 * (1024 ** 3)

        tuner = AdaptiveTuner()
        tuner.record_ingestion(doc_size_kb=10.5)

        assert len(tuner.workload.recent_ingestions) == 1
        assert tuner.workload.recent_ingestions[0]["size_kb"] == 10.5

    @patch("src.utils.adaptive_tuning.os.cpu_count", return_value=4)
    @patch("src.utils.adaptive_tuning.psutil.virtual_memory")
    def test_analyse_workload(self, mock_memory, mock_cpu):
        """Test workload analysis."""
        mock_memory.return_value.total = 8 * (1024 ** 3)
        mock_memory.return_value.available = 4 * (1024 ** 3)

        tuner = AdaptiveTuner()

        # Record bulk ingestion pattern
        for _ in range(60):
            tuner.record_ingestion(doc_size_kb=10.0)

        mode = tuner.analyse_workload()
        assert mode == "bulk_ingestion"

    @patch("src.utils.adaptive_tuning.os.cpu_count", return_value=4)
    @patch("src.utils.adaptive_tuning.psutil.virtual_memory")
    def test_generate_recommendations_bulk_mode(self, mock_memory, mock_cpu):
        """Test recommendations for bulk ingestion mode."""
        mock_memory.return_value.total = 8 * (1024 ** 3)
        mock_memory.return_value.available = 4 * (1024 ** 3)

        tuner = AdaptiveTuner()

        # Simulate bulk ingestion
        for _ in range(60):
            tuner.record_ingestion(doc_size_kb=10.0)

        rec = tuner.generate_recommendations()

        assert rec.mode == "bulk_ingestion"
        assert rec.enable_query_cache is False  # Save memory
        assert rec.enable_embedding_cache is True
        assert rec.chunk_size == 1024  # Larger chunks
        assert rec.batch_size >= 100

    @patch("src.utils.adaptive_tuning.os.cpu_count", return_value=4)
    @patch("src.utils.adaptive_tuning.psutil.virtual_memory")
    def test_generate_recommendations_interactive_mode(self, mock_memory, mock_cpu):
        """Test recommendations for interactive query mode."""
        mock_memory.return_value.total = 8 * (1024 ** 3)
        mock_memory.return_value.available = 4 * (1024 ** 3)

        tuner = AdaptiveTuner()

        # Simulate interactive queries
        for _ in range(15):
            tuner.record_query(query_time=0.5)

        rec = tuner.generate_recommendations()

        assert rec.mode == "interactive_query"
        assert rec.enable_query_cache is True
        assert rec.enable_embedding_cache is True
        assert rec.chunk_size == 512  # Smaller chunks

    @patch("src.utils.adaptive_tuning.os.cpu_count", return_value=4)
    @patch("src.utils.adaptive_tuning.psutil.virtual_memory")
    def test_get_recommendations(self, mock_memory, mock_cpu):
        """Test getting current recommendations."""
        mock_memory.return_value.total = 8 * (1024 ** 3)
        mock_memory.return_value.available = 4 * (1024 ** 3)

        tuner = AdaptiveTuner()

        # Initially None
        assert tuner.get_recommendations() is None

        # Generate recommendations
        tuner.generate_recommendations()

        # Should now be available
        rec = tuner.get_recommendations()
        assert rec is not None
        assert isinstance(rec, TuningRecommendations)

    @patch("src.utils.adaptive_tuning.os.cpu_count", return_value=4)
    @patch("src.utils.adaptive_tuning.psutil.virtual_memory")
    def test_get_stats(self, mock_memory, mock_cpu):
        """Test getting tuning statistics."""
        mock_memory.return_value.total = 8 * (1024 ** 3)
        mock_memory.return_value.available = 4 * (1024 ** 3)

        tuner = AdaptiveTuner()
        tuner.record_query(query_time=0.5)
        tuner.record_ingestion(doc_size_kb=10.0)

        stats = tuner.get_stats()

        assert "hardware" in stats
        assert "workload" in stats
        assert "monitoring" in stats

        assert stats["hardware"]["cpu_count"] == 4
        assert stats["workload"]["query_rate"] >= 0
        assert stats["monitoring"]["active"] is False

    @patch("src.utils.adaptive_tuning.os.cpu_count", return_value=4)
    @patch("src.utils.adaptive_tuning.psutil.virtual_memory")
    def test_start_stop_monitoring(self, mock_memory, mock_cpu):
        """Test starting and stopping background monitoring."""
        mock_memory.return_value.total = 8 * (1024 ** 3)
        mock_memory.return_value.available = 4 * (1024 ** 3)

        tuner = AdaptiveTuner(monitoring_interval=0.1)

        # Start monitoring
        tuner.start_monitoring()
        assert tuner._monitoring_thread is not None
        assert tuner._monitoring_thread.is_alive()

        # Give it time to run
        time.sleep(0.2)

        # Stop monitoring
        tuner.stop_monitoring()
        assert tuner._monitoring_thread is None

    @patch("src.utils.adaptive_tuning.os.cpu_count", return_value=4)
    @patch("src.utils.adaptive_tuning.psutil.virtual_memory")
    def test_monitoring_generates_recommendations(self, mock_memory, mock_cpu):
        """Test monitoring loop generates recommendations."""
        mock_memory.return_value.total = 8 * (1024 ** 3)
        mock_memory.return_value.available = 4 * (1024 ** 3)

        tuner = AdaptiveTuner(monitoring_interval=0.1)

        # Record some activity
        for _ in range(15):
            tuner.record_query(query_time=0.5)

        # Start monitoring
        tuner.start_monitoring()

        # Wait for monitoring cycle
        time.sleep(0.3)

        # Should have generated recommendations
        rec = tuner.get_recommendations()
        assert rec is not None

        # Cleanup
        tuner.stop_monitoring()


class TestSingletonTuner:
    """Tests for singleton tuner instance."""

    def test_get_tuner_singleton(self):
        """Test get_tuner returns singleton."""
        # Note: This test may interfere with other tests if singleton is shared
        # In production, consider resetting singleton between tests

        tuner1 = get_tuner()
        tuner2 = get_tuner()

        assert tuner1 is tuner2


class TestIntegrationScenarios:
    """Integration tests for realistic scenarios."""

    @patch("src.utils.adaptive_tuning.os.cpu_count", return_value=8)
    @patch("src.utils.adaptive_tuning.psutil.virtual_memory")
    def test_bulk_ingestion_workflow(self, mock_memory, mock_cpu):
        """Test adaptive tuning during bulk ingestion."""
        mock_memory.return_value.total = 16 * (1024 ** 3)
        mock_memory.return_value.available = 12 * (1024 ** 3)

        tuner = AdaptiveTuner()

        # Simulate bulk document ingestion
        for _ in range(100):
            tuner.record_ingestion(doc_size_kb=15.0)

        # Generate recommendations
        rec = tuner.generate_recommendations()

        # Should optimise for bulk ingestion
        assert rec.mode == "bulk_ingestion"
        assert rec.batch_size >= 100  # Large batches
        assert rec.enable_query_cache is False  # Save memory
        assert rec.chunk_size == 1024  # Larger chunks

    @patch("src.utils.adaptive_tuning.os.cpu_count", return_value=4)
    @patch("src.utils.adaptive_tuning.psutil.virtual_memory")
    def test_interactive_query_workflow(self, mock_memory, mock_cpu):
        """Test adaptive tuning during interactive queries."""
        mock_memory.return_value.total = 8 * (1024 ** 3)
        mock_memory.return_value.available = 6 * (1024 ** 3)

        tuner = AdaptiveTuner()

        # Simulate interactive user queries
        for _ in range(20):
            tuner.record_query(query_time=0.3)

        # Generate recommendations
        rec = tuner.generate_recommendations()

        # Should optimise for interactive queries
        assert rec.mode == "interactive_query"
        assert rec.enable_query_cache is True  # Fast repeat queries
        assert rec.chunk_size == 512  # Smaller chunks for precision

    @patch("src.utils.adaptive_tuning.os.cpu_count", return_value=8)
    @patch("src.utils.adaptive_tuning.psutil.virtual_memory")
    def test_workload_transition(self, mock_memory, mock_cpu):
        """Test transition from bulk to interactive workload."""
        mock_memory.return_value.total = 16 * (1024 ** 3)
        mock_memory.return_value.available = 10 * (1024 ** 3)

        tuner = AdaptiveTuner()

        # Start with bulk ingestion
        for _ in range(60):
            tuner.record_ingestion(doc_size_kb=10.0)

        rec1 = tuner.generate_recommendations()
        assert rec1.mode == "bulk_ingestion"

        # Transition to interactive queries
        # (Simulate time passing - recent history will shift)
        for _ in range(20):
            tuner.record_query(query_time=0.4)

        rec2 = tuner.generate_recommendations()
        assert rec2.mode in ["interactive_query", "mixed"]

    @patch("src.utils.adaptive_tuning.os.cpu_count", return_value=2)
    @patch("src.utils.adaptive_tuning.psutil.virtual_memory")
    def test_low_resource_environment(self, mock_memory, mock_cpu):
        """Test recommendations for low-resource environment."""
        mock_memory.return_value.total = 2 * (1024 ** 3)  # 2GB
        mock_memory.return_value.available = 1 * (1024 ** 3)  # 1GB

        tuner = AdaptiveTuner()

        rec = tuner.generate_recommendations()

        # Should have conservative recommendations
        assert rec.worker_count >= 1  # At least 1 worker
        assert rec.batch_size >= 10  # Minimum batch size
        assert rec.cache_size >= 50  # Minimum cache size

    @patch("src.utils.adaptive_tuning.os.cpu_count", return_value=16)
    @patch("src.utils.adaptive_tuning.psutil.virtual_memory")
    def test_high_resource_environment(self, mock_memory, mock_cpu):
        """Test recommendations for high-resource environment."""
        mock_memory.return_value.total = 64 * (1024 ** 3)  # 64GB
        mock_memory.return_value.available = 48 * (1024 ** 3)  # 48GB

        tuner = AdaptiveTuner()

        # Simulate bulk ingestion
        for _ in range(100):
            tuner.record_ingestion(doc_size_kb=10.0)

        rec = tuner.generate_recommendations()

        # Should have aggressive recommendations
        assert rec.worker_count == 12  # 75% of 16
        assert rec.batch_size >= 500  # Large batches
        assert rec.cache_size >= 100  # Larger cache
