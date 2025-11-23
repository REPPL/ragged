"""
Tests for vision embedding encryption (v0.5.7 CRITICAL-1).

Security Feature: Encryption at rest for GDPR compliance
Reference: docs/development/roadmap/version/v0.5.7/README.md
"""
import base64
import tempfile
from pathlib import Path

import chromadb
import numpy as np
import pytest

from ragged.security.encryption import EncryptionManager, get_encryption_manager
from ragged.storage.dual_store import DualEmbeddingStore


@pytest.fixture
def isolated_client():
    """Create isolated ChromaDB client for each test."""
    # Use temporary directory for each test
    with tempfile.TemporaryDirectory() as tmpdir:
        client = chromadb.PersistentClient(path=str(tmpdir))
        yield client


@pytest.fixture
def encrypted_store(isolated_client):
    """Create encrypted store with isolated client."""
    return DualEmbeddingStore(client=isolated_client, enable_encryption=True)


@pytest.fixture
def unencrypted_store(isolated_client):
    """Create unencrypted store with isolated client."""
    return DualEmbeddingStore(client=isolated_client, enable_encryption=False)


class TestVisionEmbeddingEncryption:
    """Test encryption of vision embeddings and metadata."""

    def test_encryption_enabled_by_default(self, isolated_client):
        """Test that encryption is enabled by default for GDPR compliance."""
        store = DualEmbeddingStore(client=isolated_client)
        assert store.enable_encryption is True
        assert store.encryption_manager is not None

    def test_encryption_can_be_disabled(self, isolated_client):
        """Test that encryption can be disabled (for testing/migration)."""
        store = DualEmbeddingStore(client=isolated_client, enable_encryption=False)
        assert store.enable_encryption is False
        assert store.encryption_manager is None

    def test_add_vision_embedding_encrypts_metadata(self, encrypted_store):
        """Test that vision embedding metadata is encrypted at storage."""
        store = encrypted_store

        # Create sample vision embedding
        embedding = np.random.rand(128).astype(np.float32)
        document_id = "doc123"
        page_number = 0
        image_hash = "abc123def456"  # SHA-256 hash

        # Add embedding
        embedding_id = store.add_vision_embedding(
            document_id=document_id,
            page_number=page_number,
            embedding=embedding,
            image_hash=image_hash,
            has_diagrams=True,
        )

        # Retrieve raw metadata from ChromaDB (bypassing decryption)
        raw_results = store.vision_collection.get(
            ids=[embedding_id],
            include=["metadatas"]
        )

        assert len(raw_results["ids"]) == 1
        raw_metadata = raw_results["metadatas"][0]

        # Check that image_hash is encrypted (base64-encoded ciphertext)
        assert "image_hash" in raw_metadata
        encrypted_hash = raw_metadata["image_hash"]

        # Encrypted hash should be different from plaintext
        assert encrypted_hash != image_hash

        # Encrypted hash should be base64-encoded
        try:
            base64.b64decode(encrypted_hash)
        except Exception:
            pytest.fail("Encrypted image_hash is not valid base64")

        # Metadata should be marked as encrypted
        assert raw_metadata.get("encrypted") == "true"

    def test_query_vision_decrypts_metadata(self, encrypted_store):
        """Test that vision queries return decrypted metadata."""
        store = encrypted_store

        # Add vision embedding
        embedding = np.random.rand(128).astype(np.float32)
        image_hash = "abc123def456"

        store.add_vision_embedding(
            document_id="doc123",
            page_number=0,
            embedding=embedding,
            image_hash=image_hash,
        )

        # Query vision embeddings
        query_embedding = np.random.rand(128).astype(np.float32)
        results = store.query_vision(query_embedding, k=5)

        # Check that metadata is decrypted
        assert len(results["metadatas"][0]) > 0
        decrypted_metadata = results["metadatas"][0][0]

        # image_hash should be decrypted to original plaintext
        assert decrypted_metadata["image_hash"] == image_hash

    def test_get_by_document_decrypts_vision_metadata(self, encrypted_store):
        """Test that get_by_document returns decrypted vision metadata."""
        store = encrypted_store

        # Add vision embedding
        embedding = np.random.rand(128).astype(np.float32)
        document_id = "doc123"
        image_hash = "abc123def456"

        store.add_vision_embedding(
            document_id=document_id,
            page_number=0,
            embedding=embedding,
            image_hash=image_hash,
        )

        # Get embeddings by document
        from ragged.storage.schema import EmbeddingType
        results = store.get_by_document(document_id, EmbeddingType.VISION)

        # Check that metadata is decrypted
        assert len(results["metadatas"]) > 0
        decrypted_metadata = results["metadatas"][0]
        assert decrypted_metadata["image_hash"] == image_hash

    def test_get_all_vision_documents_decrypts_metadata(self, encrypted_store):
        """Test that get_all_vision_documents returns decrypted metadata."""
        store = encrypted_store

        # Add vision embeddings
        image_hashes = ["hash1", "hash2", "hash3"]
        for i, image_hash in enumerate(image_hashes):
            embedding = np.random.rand(128).astype(np.float32)
            store.add_vision_embedding(
                document_id=f"doc{i}",
                page_number=0,
                embedding=embedding,
                image_hash=image_hash,
            )

        # Get all vision documents
        results = store.get_all_vision_documents()

        # Check that all metadata is decrypted
        assert len(results["metadatas"]) == 3
        for i, metadata in enumerate(results["metadatas"]):
            assert metadata["image_hash"] == image_hashes[i]

    def test_encryption_backward_compatible_with_unencrypted_data(self, isolated_client):
        """Test that encrypted store can read legacy unencrypted metadata."""
        # Create store without encryption (legacy data)
        store_unencrypted = DualEmbeddingStore(client=isolated_client, enable_encryption=False)

        embedding = np.random.rand(128).astype(np.float32)
        image_hash = "legacy_hash_123"

        store_unencrypted.add_vision_embedding(
            document_id="doc123",
            page_number=0,
            embedding=embedding,
            image_hash=image_hash,
        )

        # Create new store with encryption enabled (current version)
        store_encrypted = DualEmbeddingStore(
            enable_encryption=True,
            client=isolated_client  # Same ChromaDB client
        )

        # Query should still work and return plaintext metadata
        query_embedding = np.random.rand(128).astype(np.float32)
        results = store_encrypted.query_vision(query_embedding, k=5)

        assert len(results["metadatas"][0]) > 0
        metadata = results["metadatas"][0][0]

        # Should return plaintext for legacy unencrypted data
        assert metadata["image_hash"] == image_hash
        assert metadata.get("encrypted") == "false"

    def test_encryption_manager_singleton(self, isolated_client):
        """Test that encryption manager is singleton across stores."""
        store1 = DualEmbeddingStore(client=isolated_client)
        store2 = DualEmbeddingStore(client=isolated_client)

        # Both stores should use same encryption manager
        assert store1.encryption_manager is store2.encryption_manager

    def test_encrypted_metadata_cannot_be_read_without_key(self, encrypted_store):
        """Test that encrypted metadata is secure (cannot be decrypted without key)."""
        import tempfile
        from pathlib import Path

        store = encrypted_store

        # Add vision embedding
        embedding = np.random.rand(128).astype(np.float32)
        image_hash = "sensitive_hash_abc123"

        store.add_vision_embedding(
            document_id="doc123",
            page_number=0,
            embedding=embedding,
            image_hash=image_hash,
        )

        # Get raw encrypted metadata
        results = store.vision_collection.get(include=["metadatas"])
        encrypted_hash = results["metadatas"][0]["image_hash"]

        # Try to decrypt with wrong encryption manager (new key in different location)
        with tempfile.TemporaryDirectory() as tmpdir:
            wrong_key_file = Path(tmpdir) / "wrong_key.key"
            wrong_manager = EncryptionManager(key_file=wrong_key_file)  # Different key

            encrypted_bytes = base64.b64decode(encrypted_hash)

            # Should fail to decrypt with wrong key
            with pytest.raises(Exception):
                wrong_manager.decrypt(encrypted_bytes)

    def test_hybrid_query_decrypts_vision_metadata(self, encrypted_store):
        """Test that hybrid queries decrypt vision metadata in RRF fusion."""
        store = encrypted_store

        # Add text embedding
        text_embedding = np.random.rand(384).astype(np.float32)
        store.add_text_embedding(
            document_id="doc123",
            chunk_id="chunk1",
            chunk_index=0,
            embedding=text_embedding,
            text_content="Sample text",
        )

        # Add vision embedding
        vision_embedding = np.random.rand(128).astype(np.float32)
        image_hash = "hybrid_hash_xyz789"
        store.add_vision_embedding(
            document_id="doc123",
            page_number=0,
            embedding=vision_embedding,
            image_hash=image_hash,
        )

        # Hybrid query
        query_text = np.random.rand(384).astype(np.float32)
        query_vision = np.random.rand(128).astype(np.float32)

        results = store.query_hybrid(
            text_embedding=query_text,
            vision_embedding=query_vision,
            k=5
        )

        # Check that vision metadata in hybrid results is decrypted
        # Find vision result in merged results
        vision_metadata = None
        for metadata in results["metadatas"][0]:
            if "image_hash" in metadata:
                vision_metadata = metadata
                break

        assert vision_metadata is not None
        assert vision_metadata["image_hash"] == image_hash

    def test_collection_metadata_reflects_encryption_status(self, isolated_client):
        """Test that ChromaDB collection metadata reflects encryption status."""
        store_encrypted = DualEmbeddingStore(
            client=isolated_client,
            collection_name="encrypted_docs",
            enable_encryption=True
        )
        collection_metadata = store_encrypted.vision_collection.metadata
        assert collection_metadata["encryption_enabled"] == "True"

        store_unencrypted = DualEmbeddingStore(
            client=isolated_client,
            collection_name="unencrypted_docs",
            enable_encryption=False
        )
        collection_metadata = store_unencrypted.vision_collection.metadata
        assert collection_metadata["encryption_enabled"] == "False"

    def test_schema_version_updated_to_v0_5_7(self, encrypted_store):
        """Test that schema version is updated to v0.5.7."""
        store = encrypted_store

        text_metadata = store.text_collection.metadata
        vision_metadata = store.vision_collection.metadata

        assert text_metadata["schema_version"] == "v0.5.7"
        assert vision_metadata["schema_version"] == "v0.5.7"


class TestEncryptionPerformance:
    """Test encryption performance impact."""

    def test_encryption_overhead_acceptable(self, isolated_client):
        """Test that encryption overhead is minimal (<100ms for batch of 10)."""
        import time

        store = DualEmbeddingStore(client=isolated_client, enable_encryption=True)

        # Add 10 vision embeddings with encryption
        start = time.time()
        for i in range(10):
            embedding = np.random.rand(128).astype(np.float32)
            store.add_vision_embedding(
                document_id=f"doc{i}",
                page_number=0,
                embedding=embedding,
                image_hash=f"hash_{i}_abcdef123456",
            )
        encrypted_time = time.time() - start

        # Add 10 vision embeddings without encryption
        store_unencrypted = DualEmbeddingStore(client=isolated_client, enable_encryption=False)
        start = time.time()
        for i in range(10):
            embedding = np.random.rand(128).astype(np.float32)
            store_unencrypted.add_vision_embedding(
                document_id=f"doc{i}",
                page_number=0,
                embedding=embedding,
                image_hash=f"hash_{i}_abcdef123456",
            )
        unencrypted_time = time.time() - start

        # Encryption overhead should be minimal (<100ms for 10 embeddings)
        overhead = encrypted_time - unencrypted_time
        assert overhead < 0.1, f"Encryption overhead too high: {overhead*1000:.2f}ms"


class TestGDPRCompliance:
    """Test GDPR Article 32 compliance."""

    def test_encryption_at_rest_satisfied(self, encrypted_store):
        """Test that encryption at rest satisfies GDPR Article 32."""
        store = encrypted_store

        # Add sensitive vision embedding
        embedding = np.random.rand(128).astype(np.float32)
        image_hash = "patient_xray_sha256_hash"  # Simulated healthcare data

        store.add_vision_embedding(
            document_id="patient_record_123",
            page_number=0,
            embedding=embedding,
            image_hash=image_hash,
            has_diagrams=True,
        )

        # Verify that sensitive metadata (image_hash) is encrypted at rest
        raw_results = store.vision_collection.get(include=["metadatas"])
        stored_hash = raw_results["metadatas"][0]["image_hash"]

        # Stored hash should NOT be plaintext
        assert stored_hash != image_hash

        # Stored hash should be encrypted (base64 ciphertext)
        assert len(stored_hash) > len(image_hash)  # Ciphertext is longer
        assert raw_results["metadatas"][0]["encrypted"] == "true"

        # GDPR Article 32 requirement: "encryption of personal data" ✓

    def test_right_to_erasure_preserves_encryption(self, encrypted_store):
        """Test that document deletion (GDPR Article 17) works with encryption."""
        store = encrypted_store

        # Add vision embedding
        embedding = np.random.rand(128).astype(np.float32)
        document_id = "gdpr_test_doc"

        store.add_vision_embedding(
            document_id=document_id,
            page_number=0,
            embedding=embedding,
            image_hash="sensitive_hash",
        )

        # Exercise right to erasure (GDPR Article 17)
        deleted_count = store.delete_document(document_id)
        assert deleted_count > 0

        # Verify data is actually deleted
        from ragged.storage.schema import EmbeddingType
        results = store.get_by_document(document_id, EmbeddingType.VISION)
        assert len(results["ids"]) == 0
