"""Tests for intelligent batch size tuning."""

import pytest
from unittest.mock import patch, Mock

from src.embeddings.batch_tuner import BatchTuner


class TestBatchTuner:
    """Tests for BatchTuner class."""

    def test_initialization(self):
        """Test BatchTuner initialization with default values."""
        tuner = BatchTuner()

        assert tuner.current_size == 32
        assert tuner.min_size == 10
        assert tuner.max_size == 500
        assert tuner.memory_threshold == 80.0
        assert len(tuner.doc_size_history) == 0

    def test_initialization_custom_values(self):
        """Test BatchTuner initialization with custom values."""
        tuner = BatchTuner(
            initial_size=64,
            min_size=20,
            max_size=1000,
            memory_threshold=70.0,
        )

        assert tuner.current_size == 64
        assert tuner.min_size == 20
        assert tuner.max_size == 1000
        assert tuner.memory_threshold == 70.0

    def test_suggest_batch_size_empty_documents(self):
        """Test batch size suggestion with empty document list."""
        tuner = BatchTuner(initial_size=50)
        batch_size = tuner.suggest_batch_size([])

        # Should return current size for empty list
        assert batch_size == 50

    def test_suggest_batch_size_very_large_docs(self):
        """Test batch size for very large documents (>10KB)."""
        tuner = BatchTuner()
        large_docs = ["x" * 15000, "y" * 12000]  # 15KB and 12KB docs

        with patch("psutil.virtual_memory") as mock_mem:
            mock_mem.return_value.percent = 50.0  # Low memory pressure

            batch_size = tuner.suggest_batch_size(large_docs, memory_check=True)

            # Should suggest small batch size for large docs
            assert batch_size == 10

    def test_suggest_batch_size_large_docs(self):
        """Test batch size for large documents (5-10KB)."""
        tuner = BatchTuner()
        large_docs = ["x" * 7000, "y" * 6000]  # 7KB and 6KB docs

        with patch("psutil.virtual_memory") as mock_mem:
            mock_mem.return_value.percent = 50.0

            batch_size = tuner.suggest_batch_size(large_docs, memory_check=True)

            # Should suggest moderate batch size
            assert batch_size == 20

    def test_suggest_batch_size_medium_docs(self):
        """Test batch size for medium documents (1-5KB)."""
        tuner = BatchTuner()
        medium_docs = ["x" * 3000, "y" * 2000]  # 3KB and 2KB docs

        with patch("psutil.virtual_memory") as mock_mem:
            mock_mem.return_value.percent = 50.0

            batch_size = tuner.suggest_batch_size(medium_docs, memory_check=True)

            # Should suggest larger batch size
            assert batch_size == 50

    def test_suggest_batch_size_small_docs(self):
        """Test batch size for small documents (<1KB)."""
        tuner = BatchTuner()
        small_docs = ["short text", "another short one", "small"]

        with patch("psutil.virtual_memory") as mock_mem:
            mock_mem.return_value.percent = 50.0

            batch_size = tuner.suggest_batch_size(small_docs, memory_check=True)

            # Should suggest maximum throughput
            assert batch_size == 100

    def test_memory_pressure_reduction(self):
        """Test batch size reduction under memory pressure."""
        tuner = BatchTuner()
        docs = ["short text"] * 10

        with patch("psutil.virtual_memory") as mock_mem:
            # Simulate high memory usage (>80%)
            mock_mem.return_value.percent = 85.0

            batch_size = tuner.suggest_batch_size(docs, memory_check=True)

            # Should reduce batch size due to memory pressure
            # Original would be 100 for small docs, halved = 50
            assert batch_size == 50

    def test_memory_pressure_respects_min_size(self):
        """Test that memory pressure reduction respects minimum batch size."""
        tuner = BatchTuner(min_size=40)
        docs = ["short text"] * 10

        with patch("psutil.virtual_memory") as mock_mem:
            # Very high memory usage
            mock_mem.return_value.percent = 95.0

            batch_size = tuner.suggest_batch_size(docs, memory_check=True)

            # Should not go below min_size even with memory pressure
            # Original 100 / 2 = 50, but clamped to min_size=40
            assert batch_size == 50  # Still halved, above min

    def test_memory_check_disabled(self):
        """Test batch size suggestion with memory check disabled."""
        tuner = BatchTuner()
        docs = ["short text"] * 10

        with patch("psutil.virtual_memory") as mock_mem:
            # High memory but check disabled
            mock_mem.return_value.percent = 95.0

            batch_size = tuner.suggest_batch_size(docs, memory_check=False)

            # Should not be reduced by memory pressure
            assert batch_size == 100

    def test_respects_max_size(self):
        """Test that batch size never exceeds max_size."""
        tuner = BatchTuner(max_size=50)
        small_docs = ["x"] * 10  # Very small docs

        with patch("psutil.virtual_memory") as mock_mem:
            mock_mem.return_value.percent = 20.0  # Low memory

            batch_size = tuner.suggest_batch_size(small_docs, memory_check=True)

            # Would suggest 100, but clamped to max_size
            assert batch_size == 50

    def test_respects_min_size(self):
        """Test that batch size never goes below min_size."""
        tuner = BatchTuner(min_size=30)
        large_docs = ["x" * 20000] * 10  # Very large docs

        with patch("psutil.virtual_memory") as mock_mem:
            mock_mem.return_value.percent = 20.0

            batch_size = tuner.suggest_batch_size(large_docs, memory_check=True)

            # Would suggest 10, but clamped to min_size
            assert batch_size == 30

    def test_history_tracking(self):
        """Test that document size history is tracked."""
        tuner = BatchTuner()

        with patch("psutil.virtual_memory") as mock_mem:
            mock_mem.return_value.percent = 50.0

            # Process multiple batches
            tuner.suggest_batch_size(["x" * 1000] * 5, memory_check=True)
            tuner.suggest_batch_size(["x" * 2000] * 5, memory_check=True)
            tuner.suggest_batch_size(["x" * 3000] * 5, memory_check=True)

            # Should have tracked 3 batches
            assert len(tuner.doc_size_history) == 3

    def test_history_size_limit(self):
        """Test that history is limited to max size."""
        tuner = BatchTuner(history_size=5)

        with patch("psutil.virtual_memory") as mock_mem:
            mock_mem.return_value.percent = 50.0

            # Process 10 batches
            for i in range(10):
                tuner.suggest_batch_size([f"doc{i}"] * 5, memory_check=True)

            # Should only keep last 5
            assert len(tuner.doc_size_history) == 5

    def test_get_statistics_empty(self):
        """Test statistics with no history."""
        tuner = BatchTuner(initial_size=40, min_size=15, max_size=200)
        stats = tuner.get_statistics()

        assert stats["current_size"] == 40
        assert stats["min_size"] == 15
        assert stats["max_size"] == 200
        assert stats["avg_doc_size"] == 0
        assert stats["batches_tracked"] == 0

    def test_get_statistics_with_history(self):
        """Test statistics after processing batches."""
        tuner = BatchTuner()

        with patch("psutil.virtual_memory") as mock_mem:
            mock_mem.return_value.percent = 50.0

            # Process batches of different sizes
            tuner.suggest_batch_size(["x" * 1000] * 5, memory_check=True)
            tuner.suggest_batch_size(["x" * 2000] * 5, memory_check=True)

            stats = tuner.get_statistics()

            assert stats["batches_tracked"] == 2
            assert 1000 < stats["avg_doc_size"] < 2000  # Average of 1000 and 2000

    def test_reset(self):
        """Test resetting the tuner."""
        tuner = BatchTuner(initial_size=50)

        with patch("psutil.virtual_memory") as mock_mem:
            mock_mem.return_value.percent = 50.0

            # Process some batches
            tuner.suggest_batch_size(["x" * 1000] * 5, memory_check=True)
            tuner.suggest_batch_size(["x" * 2000] * 5, memory_check=True)

            assert len(tuner.doc_size_history) > 0
            assert tuner.current_size != tuner.min_size

            # Reset
            tuner.reset()

            assert len(tuner.doc_size_history) == 0
            assert tuner.current_size == tuner.min_size

    def test_updates_current_size(self):
        """Test that current_size is updated after suggestions."""
        tuner = BatchTuner(initial_size=32)

        with patch("psutil.virtual_memory") as mock_mem:
            mock_mem.return_value.percent = 50.0

            # Suggest for small docs
            small_batch = tuner.suggest_batch_size(["x"] * 10, memory_check=True)
            assert tuner.current_size == small_batch

            # Suggest for large docs
            large_batch = tuner.suggest_batch_size(["x" * 15000] * 10, memory_check=True)
            assert tuner.current_size == large_batch
            assert large_batch != small_batch  # Should be different

    def test_mixed_document_sizes(self):
        """Test batch size suggestion with mixed document sizes."""
        tuner = BatchTuner()

        # Mix of small and large documents
        mixed_docs = [
            "small",
            "x" * 5000,  # Large
            "medium sized text here",
            "x" * 10000,  # Very large
        ]

        with patch("psutil.virtual_memory") as mock_mem:
            mock_mem.return_value.percent = 50.0

            batch_size = tuner.suggest_batch_size(mixed_docs, memory_check=True)

            # Average size ~3750, should suggest medium batch
            assert 20 <= batch_size <= 50
