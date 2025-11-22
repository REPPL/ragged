"""Tests for document version tracking."""

import pytest
import tempfile
from pathlib import Path
from datetime import datetime

from src.storage.version_tracker import VersionTracker, DocumentVersion


class TestVersionTracker:
    """Tests for VersionTracker class."""

    @pytest.fixture
    def temp_db(self):
        """Create temporary database for testing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test_versions.db"
            yield db_path

    @pytest.fixture
    def tracker(self, temp_db):
        """Create VersionTracker instance."""
        return VersionTracker(db_path=temp_db)

    def test_init_creates_database(self, temp_db):
        """Test that initialisation creates database file."""
        tracker = VersionTracker(db_path=temp_db)
        assert temp_db.exists()

    def test_calculate_content_hash(self, tracker):
        """Test content hash calculation."""
        content = b"test document content"
        page_contents = [b"page 1", b"page 2", b"page 3"]

        content_hash, page_hashes = tracker.calculate_content_hash(
            content,
            page_contents
        )

        assert isinstance(content_hash, str)
        assert len(content_hash) == 64  # SHA-256 hex digest
        assert len(page_hashes) == 3
        assert all(len(h) == 64 for h in page_hashes)

    def test_calculate_content_hash_without_pages(self, tracker):
        """Test content hash without page-level hashes."""
        content = b"test document content"

        content_hash, page_hashes = tracker.calculate_content_hash(content)

        assert isinstance(content_hash, str)
        assert len(content_hash) == 64
        assert len(page_hashes) == 0

    def test_track_new_document(self, tracker):
        """Test tracking a new document."""
        version = tracker.track_document(
            file_path="/path/to/doc.pdf",
            content_hash="abc123" * 10 + "abcd",  # 64 chars
            page_hashes=["page1hash" * 6 + "p1p1", "page2hash" * 6 + "p2p2"],
            metadata={"file_size": 1024, "page_count": 2}
        )

        assert isinstance(version, DocumentVersion)
        assert version.version_number == 1
        assert version.content_hash == "abc123" * 10 + "abcd"
        assert len(version.page_hashes) == 2
        assert version.metadata["file_size"] == 1024

    def test_track_updated_document(self, tracker):
        """Test tracking an updated version of a document."""
        # Track version 1
        v1 = tracker.track_document(
            file_path="/path/to/doc.pdf",
            content_hash="version1hash" * 5 + "v1v1",
            page_hashes=["page1v1" * 6 + "p1p1"]
        )

        assert v1.version_number == 1

        # Track version 2 (different content hash, same file)
        v2 = tracker.track_document(
            file_path="/path/to/doc.pdf",
            content_hash="version2hash" * 5 + "v2v2",
            page_hashes=["page1v2" * 6 + "p1p1", "page2v2" * 6 + "p2p2"]
        )

        assert v2.version_number == 2
        assert v2.doc_id == v1.doc_id  # Same document
        assert v2.content_hash != v1.content_hash

    def test_track_duplicate_version(self, tracker):
        """Test tracking duplicate version returns existing version."""
        # Track version 1
        v1 = tracker.track_document(
            file_path="/path/to/doc.pdf",
            content_hash="samehash" * 8,
            page_hashes=["page1" * 10 + "p1p1p1"]
        )

        # Try to track same content again
        v2 = tracker.track_document(
            file_path="/path/to/doc.pdf",
            content_hash="samehash" * 8,
            page_hashes=["page1" * 10 + "p1p1p1"]
        )

        assert v1.version_id == v2.version_id
        assert v1.version_number == v2.version_number
        assert v1.version_number == 1

    def test_is_new_version_for_new_document(self, tracker):
        """Test is_new_version for new document."""
        is_new = tracker.is_new_version(
            file_path="/path/to/new_doc.pdf",
            content_hash="newhash" * 8
        )

        assert is_new is True

    def test_is_new_version_for_updated_document(self, tracker):
        """Test is_new_version for updated document."""
        # Track version 1
        tracker.track_document(
            file_path="/path/to/doc.pdf",
            content_hash="oldhash" * 8
        )

        # Check new content hash
        is_new = tracker.is_new_version(
            file_path="/path/to/doc.pdf",
            content_hash="newhash" * 8
        )

        assert is_new is True

    def test_is_new_version_for_existing_version(self, tracker):
        """Test is_new_version for existing version."""
        content_hash = "samehash" * 8

        # Track version 1
        tracker.track_document(
            file_path="/path/to/doc.pdf",
            content_hash=content_hash
        )

        # Check same content hash
        is_new = tracker.is_new_version(
            file_path="/path/to/doc.pdf",
            content_hash=content_hash
        )

        assert is_new is False

    def test_get_version_by_number(self, tracker):
        """Test getting specific version by number."""
        # Track two versions
        v1 = tracker.track_document(
            file_path="/path/to/doc.pdf",
            content_hash="hash1" * 8
        )

        v2 = tracker.track_document(
            file_path="/path/to/doc.pdf",
            content_hash="hash2" * 8
        )

        # Get version 1
        retrieved_v1 = tracker.get_version(v1.doc_id, version_number=1)
        assert retrieved_v1 is not None
        assert retrieved_v1.version_number == 1
        assert retrieved_v1.content_hash == "hash1" * 8

        # Get version 2
        retrieved_v2 = tracker.get_version(v2.doc_id, version_number=2)
        assert retrieved_v2 is not None
        assert retrieved_v2.version_number == 2
        assert retrieved_v2.content_hash == "hash2" * 8

    def test_get_latest_version(self, tracker):
        """Test getting latest version when no number specified."""
        # Track three versions
        v1 = tracker.track_document(
            file_path="/path/to/doc.pdf",
            content_hash="hash1" * 8
        )

        tracker.track_document(
            file_path="/path/to/doc.pdf",
            content_hash="hash2" * 8
        )

        v3 = tracker.track_document(
            file_path="/path/to/doc.pdf",
            content_hash="hash3" * 8
        )

        # Get latest (should be v3)
        latest = tracker.get_version(v1.doc_id)
        assert latest is not None
        assert latest.version_number == 3
        assert latest.version_id == v3.version_id

    def test_get_version_nonexistent(self, tracker):
        """Test getting non-existent version returns None."""
        version = tracker.get_version("nonexistent-doc-id", version_number=1)
        assert version is None

    def test_get_version_by_id(self, tracker):
        """Test getting version by version ID."""
        v1 = tracker.track_document(
            file_path="/path/to/doc.pdf",
            content_hash="hash1" * 8
        )

        retrieved = tracker.get_version_by_id(v1.version_id)
        assert retrieved is not None
        assert retrieved.version_id == v1.version_id
        assert retrieved.content_hash == v1.content_hash

    def test_get_version_by_hash(self, tracker):
        """Test getting version by content hash."""
        content_hash = "specifichash" * 5 + "hash"

        v1 = tracker.track_document(
            file_path="/path/to/doc.pdf",
            content_hash=content_hash
        )

        retrieved = tracker.get_version_by_hash(content_hash)
        assert retrieved is not None
        assert retrieved.version_id == v1.version_id
        assert retrieved.content_hash == content_hash

    def test_list_versions(self, tracker):
        """Test listing all versions of a document."""
        # Track three versions
        v1 = tracker.track_document(
            file_path="/path/to/doc.pdf",
            content_hash="hash1" * 8
        )

        tracker.track_document(
            file_path="/path/to/doc.pdf",
            content_hash="hash2" * 8
        )

        tracker.track_document(
            file_path="/path/to/doc.pdf",
            content_hash="hash3" * 8
        )

        versions = tracker.list_versions(v1.doc_id)

        assert len(versions) == 3
        assert versions[0].version_number == 1
        assert versions[1].version_number == 2
        assert versions[2].version_number == 3

    def test_find_document_by_path(self, tracker):
        """Test finding document ID by file path."""
        v1 = tracker.track_document(
            file_path="/path/to/doc.pdf",
            content_hash="hash1" * 8
        )

        doc_id = tracker.find_document_by_path("/path/to/doc.pdf")
        assert doc_id == v1.doc_id

    def test_find_document_by_path_nonexistent(self, tracker):
        """Test finding non-existent document returns None."""
        doc_id = tracker.find_document_by_path("/nonexistent/doc.pdf")
        assert doc_id is None

    def test_link_chunk_to_version(self, tracker):
        """Test linking chunk to version."""
        v1 = tracker.track_document(
            file_path="/path/to/doc.pdf",
            content_hash="hash1" * 8
        )

        # Link chunk
        tracker.link_chunk_to_version(
            chunk_id="chunk_abc123",
            version_id=v1.version_id,
            page_number=1,
            chunk_sequence=1
        )

        # Verify link
        version = tracker.get_chunk_version("chunk_abc123")
        assert version is not None
        assert version.version_id == v1.version_id

    def test_get_chunk_version_nonexistent(self, tracker):
        """Test getting version for non-existent chunk returns None."""
        version = tracker.get_chunk_version("nonexistent-chunk")
        assert version is None

    def test_multiple_documents(self, tracker):
        """Test tracking multiple different documents."""
        # Track doc1
        doc1_v1 = tracker.track_document(
            file_path="/path/to/doc1.pdf",
            content_hash="doc1hash" * 7 + "d1"
        )

        # Track doc2
        doc2_v1 = tracker.track_document(
            file_path="/path/to/doc2.pdf",
            content_hash="doc2hash" * 7 + "d2"
        )

        # Update doc1
        doc1_v2 = tracker.track_document(
            file_path="/path/to/doc1.pdf",
            content_hash="doc1newh" * 7 + "d1"
        )

        # Verify doc IDs are different
        assert doc1_v1.doc_id != doc2_v1.doc_id

        # Verify doc1 has 2 versions
        doc1_versions = tracker.list_versions(doc1_v1.doc_id)
        assert len(doc1_versions) == 2

        # Verify doc2 has 1 version
        doc2_versions = tracker.list_versions(doc2_v1.doc_id)
        assert len(doc2_versions) == 1

    def test_version_metadata_persistence(self, tracker):
        """Test that version metadata is persisted correctly."""
        metadata = {
            "file_size": 2048,
            "page_count": 5,
            "author": "Test Author",
            "tags": ["test", "document"]
        }

        v1 = tracker.track_document(
            file_path="/path/to/doc.pdf",
            content_hash="hash1" * 8,
            metadata=metadata
        )

        # Retrieve and verify metadata
        retrieved = tracker.get_version_by_id(v1.version_id)
        assert retrieved is not None
        assert retrieved.metadata == metadata

    def test_absolute_path_handling(self, tracker):
        """Test that relative paths are converted to absolute."""
        # Track with relative path
        v1 = tracker.track_document(
            file_path="relative/path/doc.pdf",
            content_hash="hash1" * 8
        )

        # File path should be absolute
        assert Path(v1.file_path).is_absolute()

    def test_concurrent_version_tracking(self, tracker):
        """Test tracking versions maintains correct numbering."""
        # Track multiple versions rapidly
        versions = []
        for i in range(5):
            v = tracker.track_document(
                file_path="/path/to/doc.pdf",
                content_hash=f"hash{i}" * 8
            )
            versions.append(v)

        # Verify version numbers are sequential
        for i, v in enumerate(versions, start=1):
            assert v.version_number == i

    def test_page_hash_persistence(self, tracker):
        """Test that page hashes are persisted correctly."""
        page_hashes = [
            "page1hash" * 7 + "p1",
            "page2hash" * 7 + "p2",
            "page3hash" * 7 + "p3"
        ]

        v1 = tracker.track_document(
            file_path="/path/to/doc.pdf",
            content_hash="dochash" * 8,
            page_hashes=page_hashes
        )

        # Retrieve and verify page hashes
        retrieved = tracker.get_version_by_id(v1.version_id)
        assert retrieved is not None
        assert retrieved.page_hashes == page_hashes
