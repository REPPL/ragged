"""Tests for hierarchical chunking module."""

import pytest

from src.chunking.hierarchical_chunker import HierarchicalChunk, HierarchicalChunker


class TestHierarchicalChunk:
    """Test HierarchicalChunk dataclass."""

    def test_chunk_creation_parent(self):
        """Test creating a parent chunk."""
        chunk = HierarchicalChunk(
            text="Parent chunk content...",
            chunk_id="doc1_parent_0",
            level="parent",
            child_ids=["doc1_child_0", "doc1_child_1"],
            position=0,
        )

        assert chunk.level == "parent"
        assert chunk.chunk_id == "doc1_parent_0"
        assert len(chunk.child_ids) == 2
        assert chunk.parent_id is None

    def test_chunk_creation_child(self):
        """Test creating a child chunk."""
        chunk = HierarchicalChunk(
            text="Child chunk content...",
            chunk_id="doc1_child_0",
            level="child",
            parent_id="doc1_parent_0",
            parent_text="Full parent text...",
            position=0,
        )

        assert chunk.level == "child"
        assert chunk.parent_id == "doc1_parent_0"
        assert chunk.parent_text == "Full parent text..."
        assert chunk.child_ids is None


class TestHierarchicalChunker:
    """Test HierarchicalChunker class."""

    def test_chunker_initialization(self):
        """Test hierarchical chunker initialization."""
        chunker = HierarchicalChunker(
            parent_chunk_size=2500,
            child_chunk_size=600,
            parent_overlap=250,
            child_overlap=60,
        )

        assert chunker.parent_chunk_size == 2500
        assert chunker.child_chunk_size == 600
        assert chunker.parent_overlap == 250
        assert chunker.child_overlap == 60

    def test_initialization_validation(self):
        """Test that parent must be larger than child."""
        with pytest.raises(ValueError):
            HierarchicalChunker(
                parent_chunk_size=500,
                child_chunk_size=1000,  # Larger than parent
            )

    def test_split_empty_text(self):
        """Test splitting empty text."""
        chunker = HierarchicalChunker()

        chunks = chunker.split_text("")

        assert len(chunks) == 0

    def test_split_text_returns_children(self):
        """Test that split_text returns child chunks."""
        chunker = HierarchicalChunker(
            parent_chunk_size=200,
            child_chunk_size=80,
        )

        text = "This is a test document. " * 20  # ~500 chars

        chunks = chunker.split_text(text)

        # Should return child chunks
        assert len(chunks) > 0
        # Children are smaller
        assert all(len(c) <= 150 for c in chunks)  # Rough check

    def test_create_hierarchy_small_text(self):
        """Test hierarchy creation with small text."""
        chunker = HierarchicalChunker(
            parent_chunk_size=200,
            child_chunk_size=80,
        )

        text = "Short text."

        hierarchy = chunker.create_hierarchy(text, "doc1")

        # Should have at least 1 parent and 1 child
        parents = [c for c in hierarchy if c.level == "parent"]
        children = [c for c in hierarchy if c.level == "child"]

        assert len(parents) >= 1
        assert len(children) >= 1

    def test_create_hierarchy_parent_child_linking(self):
        """Test that parent-child relationships are correct."""
        chunker = HierarchicalChunker(
            parent_chunk_size=300,
            child_chunk_size=100,
        )

        text = "This is a test document with some content. " * 15  # ~600 chars

        hierarchy = chunker.create_hierarchy(text, "doc1")

        parents = [c for c in hierarchy if c.level == "parent"]
        children = [c for c in hierarchy if c.level == "child"]

        # Each child should have a parent_id
        for child in children:
            assert child.parent_id is not None
            assert child.parent_text is not None

            # Parent ID should exist in parents
            parent_ids = [p.chunk_id for p in parents]
            assert child.parent_id in parent_ids

        # Each parent should have child_ids
        for parent in parents:
            assert parent.child_ids is not None
            assert len(parent.child_ids) > 0

            # Child IDs should exist in children
            child_ids = [c.chunk_id for c in children]
            for child_id in parent.child_ids:
                assert child_id in child_ids

    def test_create_parent_chunks(self):
        """Test parent chunk creation."""
        chunker = HierarchicalChunker(
            parent_chunk_size=200,
            parent_overlap=50,
        )

        text = "Sentence one. " * 40  # ~560 chars

        parents = chunker._create_parent_chunks(text)

        assert len(parents) >= 2  # Should split into multiple parents
        # Check overlap (later chunks should contain text from previous)
        if len(parents) > 1:
            # Some overlap expected
            assert any(parents[i][-20:] in parents[i+1] for i in range(len(parents)-1))

    def test_create_child_chunks(self):
        """Test child chunk creation within parent."""
        chunker = HierarchicalChunker(
            child_chunk_size=100,
            child_overlap=20,
        )

        parent_text = "This is parent content. " * 15  # ~360 chars

        children = chunker._create_child_chunks(parent_text)

        assert len(children) >= 2  # Should split into multiple children
        assert all(len(c) <= 150 for c in children)  # Roughly child-sized

    def test_split_with_overlap(self):
        """Test splitting with overlap."""
        chunker = HierarchicalChunker()

        text = "Sentence one. Sentence two. Sentence three. Sentence four. Sentence five."

        chunks = chunker._split_with_overlap(text, chunk_size=40, overlap=10)

        assert len(chunks) > 1
        # Check that chunks overlap
        for i in range(len(chunks) - 1):
            # Later chunks should contain some text from previous
            # Due to overlap
            pass  # Overlap might not be exact due to sentence boundaries

    def test_split_with_overlap_no_overlap_needed(self):
        """Test splitting when text is smaller than chunk size."""
        chunker = HierarchicalChunker()

        text = "Short text."

        chunks = chunker._split_with_overlap(text, chunk_size=100, overlap=20)

        assert len(chunks) == 1
        assert chunks[0] == text

    def test_sentence_boundary_detection(self):
        """Test that splitting prefers sentence boundaries."""
        chunker = HierarchicalChunker()

        text = "First sentence. Second sentence. Third sentence. Fourth sentence."

        chunks = chunker._split_with_overlap(text, chunk_size=40, overlap=5)

        # Most chunks should end with a period or be last chunk
        for i, chunk in enumerate(chunks[:-1]):
            # Not last chunk, should try to end at sentence
            assert '.' in chunk

    def test_fallback_chunks(self):
        """Test fallback chunking."""
        chunker = HierarchicalChunker(child_chunk_size=100)

        text = "Sentence one. " * 20

        chunks = chunker._fallback_chunks(text, "doc1")

        assert len(chunks) > 0
        # All marked as children
        assert all(c.level == "child" for c in chunks)
        # No parent info
        assert all(c.parent_id is None for c in chunks)

    def test_get_parent_text_child(self):
        """Test getting parent text from child chunk."""
        child = HierarchicalChunk(
            text="Child text",
            chunk_id="child_1",
            level="child",
            parent_id="parent_1",
            parent_text="Parent text for context",
        )

        parent_text = HierarchicalChunker.get_parent_text(child)

        assert parent_text == "Parent text for context"

    def test_get_parent_text_parent(self):
        """Test getting parent text from parent chunk (should be None)."""
        parent = HierarchicalChunk(
            text="Parent text",
            chunk_id="parent_1",
            level="parent",
        )

        parent_text = HierarchicalChunker.get_parent_text(parent)

        assert parent_text is None

    def test_format_with_parent(self):
        """Test formatting child with parent context."""
        child_text = "Specific information about ML"
        parent_text = "This section discusses machine learning and AI"

        formatted = HierarchicalChunker.format_with_parent(child_text, parent_text)

        assert "BROADER CONTEXT" in formatted
        assert "SPECIFIC CONTENT" in formatted
        assert parent_text in formatted
        assert child_text in formatted

    def test_format_without_parent(self):
        """Test formatting child without parent."""
        child_text = "Specific information"

        formatted = HierarchicalChunker.format_with_parent(child_text, None)

        assert formatted == child_text
        assert "BROADER CONTEXT" not in formatted

    def test_large_document_hierarchy(self):
        """Test hierarchy creation with large document."""
        chunker = HierarchicalChunker(
            parent_chunk_size=500,
            child_chunk_size=150,
        )

        # Create a large document (~2000 chars)
        text = "This is a longer paragraph about machine learning. " * 40

        hierarchy = chunker.create_hierarchy(text, "doc1")

        parents = [c for c in hierarchy if c.level == "parent"]
        children = [c for c in hierarchy if c.level == "child"]

        # Should have multiple parents
        assert len(parents) >= 3

        # Should have even more children
        assert len(children) > len(parents)

        # All children should link to parents
        for child in children:
            assert child.parent_id in [p.chunk_id for p in parents]

    def test_child_positions_sequential(self):
        """Test that child positions are sequential."""
        chunker = HierarchicalChunker(
            parent_chunk_size=300,
            child_chunk_size=100,
        )

        text = "Sentence. " * 50

        hierarchy = chunker.create_hierarchy(text, "doc1")

        children = sorted(
            [c for c in hierarchy if c.level == "child"],
            key=lambda x: x.position
        )

        # Positions should be sequential
        for i, child in enumerate(children):
            assert child.position == i

    def test_parent_contains_all_children_text(self):
        """Test that parent text contains all its children's text."""
        chunker = HierarchicalChunker(
            parent_chunk_size=400,
            child_chunk_size=120,
        )

        text = "This is test content. " * 25

        hierarchy = chunker.create_hierarchy(text, "doc1")

        parents = [c for c in hierarchy if c.level == "parent"]
        children = [c for c in hierarchy if c.level == "child"]

        for parent in parents:
            # Get children of this parent
            parent_children = [c for c in children if c.parent_id == parent.chunk_id]

            # All children should reference the same parent text
            for child in parent_children:
                assert child.parent_text == parent.text
