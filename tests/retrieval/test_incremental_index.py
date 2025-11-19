"""Tests for incremental index operations.

v0.2.9: Tests for differential updates and checkpointing.
"""

import pytest
import tempfile
from pathlib import Path
from unittest.mock import patch, Mock

from src.retrieval.incremental_index import (
    IncrementalBM25Retriever,
    IndexCheckpoint,
)


@pytest.fixture
def temp_checkpoint_dir():
    """Create temporary checkpoint directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def retriever(temp_checkpoint_dir):
    """Create retriever with temporary checkpoint directory."""
    return IncrementalBM25Retriever(
        checkpoint_dir=temp_checkpoint_dir,
        enable_checkpoints=True,
        compaction_threshold=0.5,
    )


@pytest.fixture
def sample_docs():
    """Sample documents for testing."""
    return {
        "docs": ["Document one about cats", "Document two about dogs", "Document three about birds"],
        "ids": ["doc1", "doc2", "doc3"],
        "metadatas": [{"topic": "cats"}, {"topic": "dogs"}, {"topic": "birds"}],
    }


class TestIncrementalBM25Retriever:
    """Tests for incremental BM25 retriever."""

    def test_initialization(self, retriever, temp_checkpoint_dir):
        """Test retriever initializes correctly."""
        assert retriever.checkpoint_dir == temp_checkpoint_dir
        assert retriever.enable_checkpoints is True
        assert retriever.compaction_threshold == 0.5
        assert len(retriever.deleted_ids) == 0
        assert retriever.version == 0

    def test_initial_indexing(self, retriever, sample_docs):
        """Test initial document indexing."""
        retriever.index_documents(
            sample_docs["docs"],
            sample_docs["ids"],
            sample_docs["metadatas"]
        )

        assert retriever.count() == 3
        assert retriever.version == 0  # Initial indexing doesn't increment version

    def test_add_documents_incremental(self, retriever, sample_docs):
        """Test adding documents incrementally."""
        # Initial index
        retriever.index_documents(
            sample_docs["docs"][:2],
            sample_docs["ids"][:2],
            sample_docs["metadatas"][:2]
        )

        initial_count = retriever.count()
        initial_version = retriever.version

        # Add one more document
        retriever.add_documents(
            [sample_docs["docs"][2]],
            [sample_docs["ids"][2]],
            [sample_docs["metadatas"][2]]
        )

        assert retriever.count() == initial_count + 1
        assert retriever.version == initial_version + 1

    def test_remove_documents_lazy(self, retriever, sample_docs):
        """Test lazy document removal."""
        retriever.index_documents(
            sample_docs["docs"],
            sample_docs["ids"],
            sample_docs["metadatas"]
        )

        # Remove one document
        retriever.remove_documents(["doc2"])

        # Document still in corpus (lazy deletion)
        assert retriever.count() == 3
        # But marked as deleted
        assert "doc2" in retriever.deleted_ids

    def test_search_filters_deleted(self, retriever, sample_docs):
        """Test search filters out deleted documents."""
        retriever.index_documents(
            sample_docs["docs"],
            sample_docs["ids"],
            sample_docs["metadatas"]
        )

        # Remove one document
        retriever.remove_documents(["doc2"])

        # Search should not return deleted document
        results = retriever.search("dogs", top_k=5)

        result_ids = [doc_id for doc_id, _, _, _ in results]
        assert "doc2" not in result_ids

    def test_fragmentation_ratio(self, retriever, sample_docs):
        """Test fragmentation ratio calculation."""
        retriever.index_documents(
            sample_docs["docs"],
            sample_docs["ids"],
            sample_docs["metadatas"]
        )

        # No deletions
        assert retriever.fragmentation_ratio() == 0.0

        # Delete one of three (33% fragmentation)
        retriever.remove_documents(["doc1"])
        assert abs(retriever.fragmentation_ratio() - 0.333) < 0.01

        # Delete two of three (66% fragmentation)
        retriever.remove_documents(["doc2"])
        assert abs(retriever.fragmentation_ratio() - 0.666) < 0.01

    def test_compaction_threshold(self, retriever, sample_docs):
        """Test compaction triggers at threshold."""
        retriever.index_documents(
            sample_docs["docs"],
            sample_docs["ids"],
            sample_docs["metadatas"]
        )

        # Delete below threshold (33% < 50%)
        retriever.remove_documents(["doc1"])
        assert retriever.count() == 3  # No compaction

        # Delete above threshold (66% > 50%)
        retriever.remove_documents(["doc2"])

        # Should trigger automatic compaction
        # (compact_if_needed called in remove_documents)
        # After compaction, deleted should be cleared
        assert len(retriever.deleted_ids) == 0
        assert retriever.count() == 1  # Only doc3 remains

    def test_manual_compaction(self, retriever, sample_docs):
        """Test manual compaction."""
        retriever.index_documents(
            sample_docs["docs"],
            sample_docs["ids"],
            sample_docs["metadatas"]
        )

        # Delete documents
        retriever.remove_documents(["doc1", "doc2"])

        # Force compaction
        result = retriever.compact_if_needed(force=True)

        assert result is True
        assert len(retriever.deleted_ids) == 0
        assert retriever.count() == 1

    def test_checkpoint_saving(self, retriever, sample_docs, temp_checkpoint_dir):
        """Test checkpoint is saved."""
        retriever.index_documents(
            sample_docs["docs"],
            sample_docs["ids"],
            sample_docs["metadatas"]
        )

        # Add documents (triggers checkpoint)
        retriever.add_documents(
            ["New document"],
            ["doc4"],
            [{"topic": "new"}]
        )

        # Check checkpoint file exists
        checkpoints = list(temp_checkpoint_dir.glob("bm25_checkpoint_v*.pkl"))
        assert len(checkpoints) > 0

    def test_checkpoint_loading(self, retriever, sample_docs):
        """Test checkpoint can be loaded."""
        # Create initial index
        retriever.index_documents(
            sample_docs["docs"],
            sample_docs["ids"],
            sample_docs["metadatas"]
        )

        # Add documents (creates checkpoint)
        retriever.add_documents(
            ["New document"],
            ["doc4"],
            [{"topic": "new"}]
        )

        version = retriever.version
        count = retriever.count()

        # Create new retriever and load checkpoint
        new_retriever = IncrementalBM25Retriever(
            checkpoint_dir=retriever.checkpoint_dir,
            enable_checkpoints=True
        )

        result = new_retriever.load_checkpoint()

        assert result is True
        assert new_retriever.version == version
        assert new_retriever.count() == count

    def test_checkpoint_cleanup(self, retriever, sample_docs, temp_checkpoint_dir):
        """Test old checkpoints are cleaned up."""
        retriever.index_documents(
            sample_docs["docs"],
            sample_docs["ids"],
            sample_docs["metadatas"]
        )

        # Create multiple versions (4 checkpoints)
        for i in range(4):
            retriever.add_documents(
                [f"Doc {i}"],
                [f"doc_{i}"],
                [{"num": i}]
            )

        # Should keep only last 3
        checkpoints = list(temp_checkpoint_dir.glob("bm25_checkpoint_v*.pkl"))
        assert len(checkpoints) <= 3

    def test_rebuild_index(self, retriever, sample_docs):
        """Test full index rebuild."""
        retriever.index_documents(
            sample_docs["docs"],
            sample_docs["ids"],
            sample_docs["metadatas"]
        )

        # Delete some documents
        retriever.remove_documents(["doc2"])

        initial_version = retriever.version

        # Rebuild
        retriever.rebuild_index()

        assert retriever.version > initial_version
        assert len(retriever.deleted_ids) == 0
        assert retriever.count() == 2  # Compacted

    def test_get_stats(self, retriever, sample_docs):
        """Test statistics retrieval."""
        retriever.index_documents(
            sample_docs["docs"],
            sample_docs["ids"],
            sample_docs["metadatas"]
        )

        retriever.remove_documents(["doc1"])

        stats = retriever.get_stats()

        assert stats["total_documents"] == 3
        assert stats["active_documents"] == 2
        assert stats["deleted_documents"] == 1
        assert stats["version"] == 0
        assert stats["checkpoints_enabled"] is True

    def test_checkpoints_disabled(self, temp_checkpoint_dir, sample_docs):
        """Test retriever works with checkpoints disabled."""
        retriever = IncrementalBM25Retriever(
            checkpoint_dir=temp_checkpoint_dir,
            enable_checkpoints=False
        )

        retriever.index_documents(
            sample_docs["docs"],
            sample_docs["ids"],
            sample_docs["metadatas"]
        )

        retriever.add_documents(
            ["New doc"],
            ["doc4"],
        )

        # No checkpoint files should be created
        checkpoints = list(temp_checkpoint_dir.glob("bm25_checkpoint_v*.pkl"))
        assert len(checkpoints) == 0

    def test_concurrent_compaction_prevention(self, retriever, sample_docs):
        """Test concurrent compaction is prevented."""
        retriever.index_documents(
            sample_docs["docs"],
            sample_docs["ids"],
            sample_docs["metadatas"]
        )

        retriever.remove_documents(["doc1", "doc2"])

        # Simulate compaction in progress
        retriever.compaction_in_progress = True

        result = retriever.compact_if_needed(force=True)

        # Should return False (compaction blocked)
        assert result is False


class TestEdgeCases:
    """Tests for edge cases and error conditions."""

    def test_empty_documents(self, retriever):
        """Test handling of empty document list."""
        retriever.add_documents([], [], [])

        assert retriever.count() == 0

    def test_mismatched_lengths(self, retriever):
        """Test error on mismatched document/ID lengths."""
        with pytest.raises(ValueError):
            retriever.add_documents(
                ["doc1", "doc2"],
                ["id1"],  # Mismatched
            )

    def test_search_before_indexing(self, retriever):
        """Test search fails before indexing."""
        with pytest.raises(RuntimeError):
            retriever.search("query")

    def test_remove_nonexistent_documents(self, retriever, sample_docs):
        """Test removing non-existent documents."""
        retriever.index_documents(
            sample_docs["docs"],
            sample_docs["ids"],
            sample_docs["metadatas"]
        )

        # Remove non-existent IDs
        retriever.remove_documents(["nonexistent1", "nonexistent2"])

        # Should be added to deleted set
        assert "nonexistent1" in retriever.deleted_ids

    def test_load_checkpoint_when_disabled(self, temp_checkpoint_dir):
        """Test loading checkpoint when disabled."""
        retriever = IncrementalBM25Retriever(
            checkpoint_dir=temp_checkpoint_dir,
            enable_checkpoints=False
        )

        result = retriever.load_checkpoint()

        assert result is False

    def test_load_nonexistent_checkpoint(self, temp_checkpoint_dir):
        """Test loading non-existent checkpoint."""
        retriever = IncrementalBM25Retriever(
            checkpoint_dir=temp_checkpoint_dir,
            enable_checkpoints=True
        )

        result = retriever.load_checkpoint()

        assert result is False


class TestIntegrationScenarios:
    """Integration tests for realistic scenarios."""

    def test_incremental_workflow(self, retriever, sample_docs):
        """Test complete incremental indexing workflow."""
        # 1. Initial indexing
        retriever.index_documents(
            sample_docs["docs"][:2],
            sample_docs["ids"][:2],
            sample_docs["metadatas"][:2]
        )

        assert retriever.count() == 2

        # 2. Add documents
        retriever.add_documents(
            [sample_docs["docs"][2]],
            [sample_docs["ids"][2]],
            [sample_docs["metadatas"][2]]
        )

        assert retriever.count() == 3

        # 3. Search
        results = retriever.search("cats", top_k=5)
        assert len(results) > 0

        # 4. Remove documents
        retriever.remove_documents(["doc1"])

        # 5. Search again (deleted filtered)
        results = retriever.search("cats", top_k=5)
        result_ids = [doc_id for doc_id, _, _, _ in results]
        assert "doc1" not in result_ids

        # 6. Compact
        retriever.compact_if_needed(force=True)
        assert retriever.count() == 2

    def test_recovery_from_checkpoint(self, retriever, sample_docs):
        """Test recovery from checkpoint after crash."""
        # Index and add documents
        retriever.index_documents(
            sample_docs["docs"],
            sample_docs["ids"],
            sample_docs["metadatas"]
        )

        retriever.add_documents(
            ["Extra document"],
            ["doc4"],
            [{"topic": "extra"}]
        )

        retriever.remove_documents(["doc2"])

        # Simulate crash - create new retriever
        new_retriever = IncrementalBM25Retriever(
            checkpoint_dir=retriever.checkpoint_dir,
            enable_checkpoints=True
        )

        # Load checkpoint
        result = new_retriever.load_checkpoint()

        assert result is True
        assert new_retriever.count() == 4
        assert "doc2" in new_retriever.deleted_ids

        # Search should work
        results = new_retriever.search("cats", top_k=5)
        assert len(results) > 0
