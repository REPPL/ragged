"""Tests for output organization and lineage tracking (v0.4.9).

Tests cover:
- Semantic file naming (title-author-year, hash, original)
- Directory structure creation
- Content-based deduplication
- Lineage tracking in JSONL format
- Duplicate handling with numbering
- Metadata-based search
"""

import json
import tempfile
from pathlib import Path

import pytest

from ragged.processing.output_organizer import OrganizedOutput, OutputOrganizer


class TestOutputOrganizer:
    """Tests for OutputOrganizer class."""

    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for tests."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.fixture
    def sample_files(self, temp_dir):
        """Create sample files for testing."""
        original = temp_dir / "original.pdf"
        corrected = temp_dir / "corrected.pdf"
        markdown = temp_dir / "corrected.md"

        # Create dummy files
        original.write_text("original content")
        corrected.write_text("corrected content")
        markdown.write_text("# Markdown content")

        return {
            "original": original,
            "corrected": corrected,
            "markdown": markdown,
        }

    @pytest.fixture
    def sample_metadata(self):
        """Sample metadata for testing."""
        return {
            "title": "The Art of RAG",
            "author": "John Smith",
            "year": 2024,
            "publisher": "Tech Press",
        }

    def test_init_creates_directory_structure(self, temp_dir):
        """Test that OutputOrganizer creates required directory structure."""
        output_dir = temp_dir / "documents"
        organizer = OutputOrganizer(output_dir=output_dir)

        assert organizer.originals_dir.exists()
        assert organizer.corrected_dir.exists()
        assert organizer.markdown_dir.exists()
        assert organizer.metadata_dir.exists()

        # Use resolve() for path comparison (handles macOS /var vs /private/var symlinks)
        assert organizer.originals_dir.resolve() == (output_dir / "originals").resolve()
        assert organizer.corrected_dir.resolve() == (output_dir / "corrected").resolve()
        assert organizer.markdown_dir.resolve() == (output_dir / "markdown").resolve()
        assert organizer.metadata_dir.resolve() == (output_dir.parent / "metadata").resolve()

    def test_semantic_naming_full_metadata(self, temp_dir, sample_files, sample_metadata):
        """Test semantic naming with complete metadata."""
        organizer = OutputOrganizer(
            output_dir=temp_dir / "documents",
            naming_convention="title-author-year",
        )

        result = organizer.organize(
            original=sample_files["original"],
            corrected=sample_files["corrected"],
            markdown=sample_files["markdown"],
            metadata=sample_metadata,
        )

        # Check filename
        assert result.corrected_path.name == "The-Art-of-RAG-John-Smith-2024.pdf"
        assert result.markdown_path.name == "The-Art-of-RAG-John-Smith-2024.md"

    def test_semantic_naming_partial_metadata(self, temp_dir, sample_files):
        """Test semantic naming with partial metadata."""
        organizer = OutputOrganizer(output_dir=temp_dir / "documents")

        result = organizer.organize(
            original=sample_files["original"],
            corrected=sample_files["corrected"],
            metadata={"title": "The Art of RAG"},  # Only title
        )

        # Should use title only
        assert "The-Art-of-RAG" in result.corrected_path.name

    def test_semantic_naming_no_metadata(self, temp_dir, sample_files):
        """Test semantic naming with no metadata (fallback to timestamp)."""
        organizer = OutputOrganizer(output_dir=temp_dir / "documents")

        result = organizer.organize(
            original=sample_files["original"],
            corrected=sample_files["corrected"],
            metadata={},
        )

        # Should use fallback naming (Scanned-Book-YYYYMMDD)
        assert "Scanned-Book-" in result.corrected_path.name

    def test_hash_based_naming(self, temp_dir, sample_files):
        """Test hash-based naming convention."""
        organizer = OutputOrganizer(
            output_dir=temp_dir / "documents",
            naming_convention="hash",
        )

        result = organizer.organize(
            original=sample_files["original"],
            corrected=sample_files["corrected"],
        )

        # Should use hash (16 characters)
        assert len(result.corrected_path.stem) == 16

    def test_original_naming(self, temp_dir, sample_files):
        """Test original filename preservation."""
        organizer = OutputOrganizer(
            output_dir=temp_dir / "documents",
            naming_convention="original",
        )

        result = organizer.organize(
            original=sample_files["original"],
            corrected=sample_files["corrected"],
        )

        # Should preserve original filename (sanitised)
        assert result.corrected_path.name == "original.pdf"

    def test_duplicate_handling(self, temp_dir, sample_files, sample_metadata):
        """Test automatic numbering for duplicate files."""
        organizer = OutputOrganizer(output_dir=temp_dir / "documents")

        # Create first file
        result1 = organizer.organize(
            original=sample_files["original"],
            corrected=sample_files["corrected"],
            metadata=sample_metadata,
        )

        # Create duplicate (same metadata)
        result2 = organizer.organize(
            original=sample_files["original"],
            corrected=sample_files["corrected"],
            metadata=sample_metadata,
        )

        # Second should have -001 suffix
        assert result1.corrected_path.name == "The-Art-of-RAG-John-Smith-2024.pdf"
        assert result2.corrected_path.name == "The-Art-of-RAG-John-Smith-2024-001.pdf"

    def test_original_backup_with_hash(self, temp_dir, sample_files):
        """Test that originals are backed up with content-based hash."""
        organizer = OutputOrganizer(
            output_dir=temp_dir / "documents",
            keep_originals=True,
        )

        result = organizer.organize(
            original=sample_files["original"],
            corrected=sample_files["corrected"],
        )

        # Check backup exists in hash-based directory
        assert result.original_path.exists()
        assert result.original_path.parent.parent == organizer.originals_dir
        assert result.original_path.name == "original.pdf"

    def test_no_original_backup(self, temp_dir, sample_files):
        """Test that originals are not backed up when disabled."""
        organizer = OutputOrganizer(
            output_dir=temp_dir / "documents",
            keep_originals=False,
        )

        result = organizer.organize(
            original=sample_files["original"],
            corrected=sample_files["corrected"],
        )

        # Original path should be original file (not backup)
        assert result.original_path == sample_files["original"]

    def test_lineage_tracking(self, temp_dir, sample_files, sample_metadata):
        """Test lineage tracking in JSONL format."""
        organizer = OutputOrganizer(
            output_dir=temp_dir / "documents",
            track_lineage=True,
        )

        result = organizer.organize(
            original=sample_files["original"],
            corrected=sample_files["corrected"],
            markdown=sample_files["markdown"],
            metadata=sample_metadata,
        )

        # Check lineage file exists
        lineage_file = organizer.metadata_dir / "processing_log.jsonl"
        assert lineage_file.exists()

        # Read and validate lineage record
        with open(lineage_file, "r") as f:
            record = json.loads(f.readline())

        assert record["lineage_id"] == result.lineage_id
        assert "timestamp" in record
        assert record["original"]["path"] == str(sample_files["original"])
        assert record["processed"]["corrected_pdf"] == str(result.corrected_path)
        assert record["processed"]["markdown"] == str(result.markdown_path)
        assert record["metadata"] == sample_metadata
        assert record["processor_version"] == "v0.4.9"

    def test_no_lineage_tracking(self, temp_dir, sample_files):
        """Test that lineage tracking can be disabled."""
        organizer = OutputOrganizer(
            output_dir=temp_dir / "documents",
            track_lineage=False,
        )

        organizer.organize(
            original=sample_files["original"],
            corrected=sample_files["corrected"],
        )

        # Lineage file should not be created
        lineage_file = organizer.metadata_dir / "processing_log.jsonl"
        assert not lineage_file.exists()

    def test_get_lineage_all(self, temp_dir, sample_files, sample_metadata):
        """Test retrieving all lineage records."""
        organizer = OutputOrganizer(
            output_dir=temp_dir / "documents",
            track_lineage=True,
        )

        # Create multiple records
        result1 = organizer.organize(
            original=sample_files["original"],
            corrected=sample_files["corrected"],
            metadata=sample_metadata,
        )

        result2 = organizer.organize(
            original=sample_files["original"],
            corrected=sample_files["corrected"],
            metadata={"title": "Another Book"},
        )

        # Retrieve all records
        records = organizer.get_lineage()
        assert len(records) == 2
        assert records[0]["lineage_id"] == result1.lineage_id
        assert records[1]["lineage_id"] == result2.lineage_id

    def test_get_lineage_by_id(self, temp_dir, sample_files, sample_metadata):
        """Test retrieving specific lineage record by ID."""
        organizer = OutputOrganizer(
            output_dir=temp_dir / "documents",
            track_lineage=True,
        )

        result = organizer.organize(
            original=sample_files["original"],
            corrected=sample_files["corrected"],
            metadata=sample_metadata,
        )

        # Retrieve specific record
        records = organizer.get_lineage(lineage_id=result.lineage_id)
        assert len(records) == 1
        assert records[0]["lineage_id"] == result.lineage_id

    def test_search_by_title(self, temp_dir, sample_files):
        """Test metadata-based search by title."""
        organizer = OutputOrganizer(
            output_dir=temp_dir / "documents",
            track_lineage=True,
        )

        # Create records with different titles
        organizer.organize(
            original=sample_files["original"],
            corrected=sample_files["corrected"],
            metadata={"title": "The Art of RAG"},
        )

        organizer.organize(
            original=sample_files["original"],
            corrected=sample_files["corrected"],
            metadata={"title": "Machine Learning Basics"},
        )

        # Search by title
        results = organizer.search_by_metadata(title="Art of RAG")
        assert len(results) == 1
        assert "Art of RAG" in results[0]["metadata"]["title"]

    def test_search_by_author(self, temp_dir, sample_files):
        """Test metadata-based search by author."""
        organizer = OutputOrganizer(
            output_dir=temp_dir / "documents",
            track_lineage=True,
        )

        organizer.organize(
            original=sample_files["original"],
            corrected=sample_files["corrected"],
            metadata={"title": "Book 1", "author": "John Smith"},
        )

        organizer.organize(
            original=sample_files["original"],
            corrected=sample_files["corrected"],
            metadata={"title": "Book 2", "author": "Jane Doe"},
        )

        # Search by author
        results = organizer.search_by_metadata(author="Smith")
        assert len(results) == 1
        assert "Smith" in results[0]["metadata"]["author"]

    def test_search_by_year(self, temp_dir, sample_files):
        """Test metadata-based search by year."""
        organizer = OutputOrganizer(
            output_dir=temp_dir / "documents",
            track_lineage=True,
        )

        organizer.organize(
            original=sample_files["original"],
            corrected=sample_files["corrected"],
            metadata={"title": "Book 2024", "year": 2024},
        )

        organizer.organize(
            original=sample_files["original"],
            corrected=sample_files["corrected"],
            metadata={"title": "Book 2023", "year": 2023},
        )

        # Search by year
        results = organizer.search_by_metadata(year=2024)
        assert len(results) == 1
        assert results[0]["metadata"]["year"] == 2024

    def test_filename_sanitization(self, temp_dir, sample_files):
        """Test that special characters are sanitised in filenames."""
        organizer = OutputOrganizer(output_dir=temp_dir / "documents")

        result = organizer.organize(
            original=sample_files["original"],
            corrected=sample_files["corrected"],
            metadata={"title": "Book: A/B Test & Results!"},
        )

        # Special characters should be removed
        assert ":" not in result.corrected_path.name
        assert "/" not in result.corrected_path.name
        assert "&" not in result.corrected_path.name
        assert "!" not in result.corrected_path.name

    def test_long_title_truncation(self, temp_dir, sample_files):
        """Test that very long titles are truncated."""
        organizer = OutputOrganizer(output_dir=temp_dir / "documents")

        long_title = "A" * 150  # Very long title

        result = organizer.organize(
            original=sample_files["original"],
            corrected=sample_files["corrected"],
            metadata={"title": long_title},
        )

        # Filename should be truncated (max 100 chars for semantic name)
        assert len(result.corrected_path.stem) <= 100

    def test_content_deduplication(self, temp_dir, sample_files):
        """Test that same content hash results in same backup location."""
        organizer = OutputOrganizer(
            output_dir=temp_dir / "documents",
            keep_originals=True,
        )

        # Organize same file twice
        result1 = organizer.organize(
            original=sample_files["original"],
            corrected=sample_files["corrected"],
        )

        result2 = organizer.organize(
            original=sample_files["original"],
            corrected=sample_files["corrected"],
        )

        # Same original content should have same backup location
        assert result1.original_path == result2.original_path

    def test_missing_corrected_file_raises_error(self, temp_dir):
        """Test that missing corrected file raises FileNotFoundError."""
        organizer = OutputOrganizer(output_dir=temp_dir / "documents")

        original = temp_dir / "original.pdf"
        corrected = temp_dir / "nonexistent.pdf"

        original.write_text("content")

        with pytest.raises(FileNotFoundError, match="Corrected PDF not found"):
            organizer.organize(
                original=original,
                corrected=corrected,
            )

    def test_optional_markdown(self, temp_dir, sample_files):
        """Test that markdown is optional."""
        organizer = OutputOrganizer(output_dir=temp_dir / "documents")

        result = organizer.organize(
            original=sample_files["original"],
            corrected=sample_files["corrected"],
            markdown=None,  # No markdown
        )

        assert result.markdown_path is None
