"""Tests for storage schema migration (v0.4 → v0.5)."""

import pytest
import chromadb
from chromadb.api import ClientAPI

from src.storage.migration import StorageMigration
from src.storage.schema import EmbeddingType


@pytest.fixture
def in_memory_client() -> ClientAPI:
    """Create in-memory ChromaDB client for testing."""
    return chromadb.Client()


@pytest.fixture
def migration(in_memory_client: ClientAPI) -> StorageMigration:
    """Create StorageMigration instance with in-memory client."""
    return StorageMigration(in_memory_client)


class TestDetectSchemaVersion:
    """Test schema version detection."""

    def test_detect_v05_with_metadata(self, in_memory_client: ClientAPI, migration: StorageMigration):
        """Test detection of v0.5 schema via collection metadata."""
        collection = in_memory_client.create_collection(
            name="test_v05", metadata={"schema_version": "v0.5"}
        )

        version = migration.detect_schema_version("test_v05")
        assert version == "v0.5"

    def test_detect_v05_with_embedding_type(self, in_memory_client: ClientAPI, migration: StorageMigration):
        """Test detection of v0.5 schema via embedding_type metadata."""
        collection = in_memory_client.create_collection(name="test_v05_emb")

        # Add embedding with embedding_type field
        collection.add(
            ids=["doc1_chunk_0_text"],
            embeddings=[[0.1] * 384],
            metadatas=[{"document_id": "doc1", "embedding_type": "text"}],
        )

        version = migration.detect_schema_version("test_v05_emb")
        assert version == "v0.5"

    def test_detect_v04_schema(self, in_memory_client: ClientAPI, migration: StorageMigration):
        """Test detection of v0.4 schema (no embedding_type field)."""
        collection = in_memory_client.create_collection(name="test_v04")

        # Add old-style embedding without embedding_type
        collection.add(
            ids=["doc1_chunk_0"],
            embeddings=[[0.1] * 384],
            metadatas=[{"document_id": "doc1", "chunk_id": "chunk_0"}],
        )

        version = migration.detect_schema_version("test_v04")
        assert version == "v0.4"

    def test_detect_empty_collection(self, in_memory_client: ClientAPI, migration: StorageMigration):
        """Test detection on empty collection defaults to v0.4."""
        collection = in_memory_client.create_collection(name="empty_collection")

        version = migration.detect_schema_version("empty_collection")
        assert version == "v0.4"

    def test_detect_nonexistent_collection(self, migration: StorageMigration):
        """Test detection on non-existent collection raises error."""
        with pytest.raises(ValueError, match="Collection .* not found"):
            migration.detect_schema_version("nonexistent")


class TestMigrateCollection:
    """Test collection migration from v0.4 to v0.5."""

    def test_migrate_dry_run(self, in_memory_client: ClientAPI, migration: StorageMigration):
        """Test migration dry run (no actual changes)."""
        collection = in_memory_client.create_collection(name="test_dry_run")

        # Add v0.4 style embeddings
        collection.add(
            ids=["doc1_chunk_0", "doc1_chunk_1"],
            embeddings=[[0.1] * 384, [0.2] * 384],
            metadatas=[{"document_id": "doc1"}, {"document_id": "doc1"}],
            documents=["text 0", "text 1"],
        )

        stats = migration.migrate_collection("test_dry_run", dry_run=True)

        # Check statistics
        assert stats["embeddings_processed"] == 2
        assert stats["ids_renamed"] == 2
        assert stats["metadata_updated"] == 2
        assert stats["skipped"] == 0

        # Verify no actual changes (still v0.4 IDs)
        results = collection.get()
        assert "doc1_chunk_0" in results["ids"]
        assert "doc1_chunk_1" in results["ids"]

    def test_migrate_actual(self, in_memory_client: ClientAPI, migration: StorageMigration):
        """Test actual migration (applies changes)."""
        collection = in_memory_client.create_collection(name="test_migrate")

        # Add v0.4 style embeddings
        collection.add(
            ids=["doc1_chunk_0", "doc1_chunk_1"],
            embeddings=[[0.1] * 384, [0.2] * 384],
            metadatas=[{"document_id": "doc1"}, {"document_id": "doc1"}],
            documents=["text 0", "text 1"],
        )

        stats = migration.migrate_collection("test_migrate", dry_run=False)

        # Check statistics
        assert stats["embeddings_processed"] == 2
        assert stats["ids_renamed"] == 2
        assert stats["metadata_updated"] == 2

        # Verify actual changes
        results = collection.get()

        # New IDs should have _text suffix
        assert "doc1_chunk_0_text" in results["ids"]
        assert "doc1_chunk_1_text" in results["ids"]

        # Old IDs should be gone
        assert "doc1_chunk_0" not in results["ids"]
        assert "doc1_chunk_1" not in results["ids"]

        # Metadata should have embedding_type
        for metadata in results["metadatas"]:
            assert metadata["embedding_type"] == EmbeddingType.TEXT.value

    def test_migrate_skips_already_migrated(self, in_memory_client: ClientAPI, migration: StorageMigration):
        """Test that already migrated embeddings are skipped."""
        collection = in_memory_client.create_collection(name="test_skip")

        # Add mix of v0.4 and v0.5 style embeddings
        collection.add(
            ids=["doc1_chunk_0", "doc1_chunk_1_text"],  # One old, one new
            embeddings=[[0.1] * 384, [0.2] * 384],
            metadatas=[
                {"document_id": "doc1"},
                {"document_id": "doc1", "embedding_type": "text"},
            ],
        )

        stats = migration.migrate_collection("test_skip", dry_run=False)

        # Only one should be processed
        assert stats["embeddings_processed"] == 2
        assert stats["ids_renamed"] == 1  # Only the one without _text suffix
        assert stats["skipped"] == 1  # The one with _text suffix

    def test_migrate_batch_processing(self, in_memory_client: ClientAPI, migration: StorageMigration):
        """Test migration handles batching correctly."""
        collection = in_memory_client.create_collection(name="test_batch")

        # Add 10 embeddings
        ids = [f"doc1_chunk_{i}" for i in range(10)]
        embeddings = [[float(i) / 10] * 384 for i in range(10)]
        metadatas = [{"document_id": "doc1"} for _ in range(10)]

        collection.add(ids=ids, embeddings=embeddings, metadatas=metadatas)

        # Migrate with small batch size
        stats = migration.migrate_collection("test_batch", batch_size=3, dry_run=False)

        assert stats["embeddings_processed"] == 10
        assert stats["ids_renamed"] == 10

        # Verify all migrated
        results = collection.get()
        for i in range(10):
            assert f"doc1_chunk_{i}_text" in results["ids"]

    def test_migrate_preserves_documents(self, in_memory_client: ClientAPI, migration: StorageMigration):
        """Test migration preserves document content."""
        collection = in_memory_client.create_collection(name="test_docs")

        collection.add(
            ids=["doc1_chunk_0"],
            embeddings=[[0.1] * 384],
            metadatas=[{"document_id": "doc1"}],
            documents=["Important text content"],
        )

        migration.migrate_collection("test_docs", dry_run=False)

        results = collection.get(include=["documents"])
        assert results["documents"][0] == "Important text content"

    def test_migrate_already_v05_raises_error(
        self, in_memory_client: ClientAPI, migration: StorageMigration
    ):
        """Test migration of already v0.5 collection raises error."""
        collection = in_memory_client.create_collection(
            name="test_v05", metadata={"schema_version": "v0.5"}
        )

        with pytest.raises(ValueError, match="already v0.5"):
            migration.migrate_collection("test_v05")

    def test_migrate_empty_collection(self, in_memory_client: ClientAPI, migration: StorageMigration):
        """Test migration of empty collection."""
        collection = in_memory_client.create_collection(name="empty")

        stats = migration.migrate_collection("empty", dry_run=False)

        assert stats["embeddings_processed"] == 0
        assert stats["ids_renamed"] == 0
