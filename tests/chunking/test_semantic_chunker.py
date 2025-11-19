"""Tests for semantic chunking module."""

from unittest.mock import MagicMock

import numpy as np
import pytest

from src.chunking.semantic_chunker import SemanticChunker


class TestSemanticChunker:
    """Test SemanticChunker class."""

    def test_chunker_initialization(self):
        """Test semantic chunker initialization."""
        chunker = SemanticChunker(
            similarity_threshold=0.8,
            min_chunk_size=300,
            max_chunk_size=2000,
        )

        assert chunker.similarity_threshold == 0.8
        assert chunker.min_chunk_size == 300
        assert chunker.max_chunk_size == 2000
        assert chunker._model is None  # Lazy load

    def test_split_empty_text(self):
        """Test splitting empty text."""
        chunker = SemanticChunker()

        chunks = chunker.split_text("")

        assert len(chunks) == 0

    def test_split_sentences(self):
        """Test sentence splitting."""
        chunker = SemanticChunker()

        text = "First sentence. Second sentence! Third sentence?"
        sentences = chunker._split_sentences(text)

        assert len(sentences) == 3
        assert "First sentence" in sentences[0]
        assert "Second sentence" in sentences[1]
        assert "Third sentence" in sentences[2]

    def test_split_sentences_empty(self):
        """Test sentence splitting with empty text."""
        chunker = SemanticChunker()

        sentences = chunker._split_sentences("")

        assert len(sentences) == 0

    def test_calculate_similarities(self):
        """Test similarity calculation between embeddings."""
        chunker = SemanticChunker()

        # Create test embeddings (3 sentences)
        embeddings = np.array([
            [1.0, 0.0, 0.0],  # Sentence 1
            [0.9, 0.1, 0.0],  # Sentence 2 (very similar to 1)
            [0.0, 0.0, 1.0],  # Sentence 3 (very different)
        ])

        similarities = chunker._calculate_similarities(embeddings)

        assert len(similarities) == 2  # n-1 similarities
        assert similarities[0] > 0.8  # High similarity between 1 and 2
        assert similarities[1] < 0.5  # Low similarity between 2 and 3

    def test_identify_boundaries(self):
        """Test topic boundary identification."""
        chunker = SemanticChunker(similarity_threshold=0.7)

        # High, high, low, high similarities
        similarities = [0.9, 0.85, 0.5, 0.8]

        boundaries = chunker._identify_boundaries(similarities)

        assert 0 in boundaries  # Always start at 0
        assert 3 in boundaries  # Boundary after low similarity (index 2)

    def test_create_chunks_from_boundaries(self):
        """Test chunk creation from sentences and boundaries."""
        chunker = SemanticChunker(min_sentences_per_chunk=1)

        sentences = ["S1.", "S2.", "S3.", "S4.", "S5."]
        boundaries = [0, 2, 4]  # Split at positions 2 and 4

        chunks = chunker._create_chunks(sentences, boundaries)

        assert len(chunks) == 3
        assert "S1" in chunks[0] and "S2" in chunks[0]
        assert "S3" in chunks[1] and "S4" in chunks[1]
        assert "S5" in chunks[2]

    def test_create_chunks_min_sentences(self):
        """Test minimum sentences per chunk constraint."""
        chunker = SemanticChunker(min_sentences_per_chunk=2)

        sentences = ["S1.", "S2.", "S3."]
        boundaries = [0, 1, 2]  # Each sentence separate

        chunks = chunker._create_chunks(sentences, boundaries)

        # Small chunks should be merged
        assert len(chunks) < 3

    def test_validate_chunks_too_large(self):
        """Test chunk validation for oversized chunks."""
        chunker = SemanticChunker(max_chunk_size=50)

        # Create a chunk that's too large
        large_chunk = "This is a very long chunk " * 10  # >50 chars
        chunks = [large_chunk]

        validated = chunker._validate_chunks(chunks)

        # Should be split into multiple chunks
        assert len(validated) > 1
        assert all(len(c) <= chunker.max_chunk_size + 100 for c in validated)  # Some tolerance

    def test_validate_chunks_too_small(self):
        """Test chunk validation for undersized chunks."""
        chunker = SemanticChunker(min_chunk_size=100, max_chunk_size=500)

        # Create chunks where one is too small
        chunks = ["This is a normal chunk " * 5, "Tiny"]

        validated = chunker._validate_chunks(chunks)

        # Small chunk should be merged with previous
        assert len(validated) == 1
        assert "Tiny" in validated[0]

    def test_split_large_chunk(self):
        """Test splitting of oversized chunks."""
        chunker = SemanticChunker(max_chunk_size=100)

        large_chunk = "Sentence one. " * 20  # Much larger than 100

        sub_chunks = chunker._split_large_chunk(large_chunk)

        assert len(sub_chunks) > 1
        assert all(len(c) <= chunker.max_chunk_size + 50 for c in sub_chunks)  # Some tolerance

    def test_fallback_split(self):
        """Test fallback splitting when model unavailable."""
        chunker = SemanticChunker(max_chunk_size=100)

        text = "Sentence one. " * 20

        chunks = chunker._fallback_split(text)

        assert len(chunks) > 1
        assert all(len(c) <= chunker.max_chunk_size + 50 for c in chunks)

    def test_split_text_with_model(self):
        """Test full split_text with mocked model."""
        # Mock the model
        mock_model = MagicMock()

        # Create embeddings that show topic change
        # Sentences 0-2 similar, then sentences 3-4 different
        embeddings = np.array([
            [1.0, 0.0, 0.0],
            [0.95, 0.05, 0.0],
            [0.9, 0.1, 0.0],
            [0.0, 0.0, 1.0],
            [0.0, 0.05, 0.95],
        ])
        mock_model.encode.return_value = embeddings

        chunker = SemanticChunker(
            similarity_threshold=0.8,
            min_sentences_per_chunk=1,
            min_chunk_size=30,  # Low min to allow small test chunks
            max_chunk_size=500,
        )
        chunker._model = mock_model

        text = "First topic sentence. Still first topic. First topic continues. Second topic starts. Second topic continues."

        chunks = chunker.split_text(text)

        assert len(chunks) >= 2  # Should detect topic change
        assert mock_model.encode.called

    def test_split_text_single_sentence(self):
        """Test split_text with single sentence."""
        chunker = SemanticChunker()

        text = "Just one sentence."

        chunks = chunker.split_text(text)

        assert len(chunks) == 1
        assert chunks[0] == text

    def test_split_text_fallback_on_error(self):
        """Test fallback when model fails."""
        mock_model = MagicMock()
        mock_model.encode.side_effect = Exception("Model error")

        chunker = SemanticChunker()
        chunker._model = mock_model

        text = "Sentence one. " * 20

        chunks = chunker.split_text(text)

        # Should fallback and still produce chunks
        assert len(chunks) > 0

    def test_chunk_boundaries_at_sentences(self):
        """Test that chunks end at sentence boundaries when possible."""
        chunker = SemanticChunker(max_chunk_size=100)

        text = "This is sentence one. This is sentence two. This is sentence three. " * 10

        chunks = chunker._fallback_split(text)

        # Chunks should end near sentence boundaries
        for chunk in chunks:
            # Should end with . or be last chunk
            assert chunk.endswith('.') or chunk == chunks[-1].strip()

    def test_preserves_complete_thoughts(self):
        """Test that semantic chunking preserves complete thoughts."""
        mock_model = MagicMock()

        # All sentences in same topic (high similarity)
        embeddings = np.array([
            [1.0, 0.0, 0.0],
            [0.95, 0.05, 0.0],
            [0.92, 0.08, 0.0],
        ])
        mock_model.encode.return_value = embeddings

        chunker = SemanticChunker(similarity_threshold=0.7)
        chunker._model = mock_model

        text = "Sentence about ML. Another ML sentence. Third ML sentence."

        chunks = chunker.split_text(text)

        # All sentences similar, should stay together
        assert len(chunks) == 1
        assert all(s in chunks[0] for s in ["ML", "Another", "Third"])

    def test_different_similarity_thresholds(self):
        """Test chunking with different similarity thresholds."""
        mock_model = MagicMock()

        embeddings = np.array([
            [1.0, 0.0, 0.0],
            [0.8, 0.2, 0.0],  # 0.8 similarity
            [0.6, 0.4, 0.0],  # Lower similarity
        ])
        mock_model.encode.return_value = embeddings

        text = "Sent 1. Sent 2. Sent 3."

        # High threshold (0.9) - more boundaries
        chunker_strict = SemanticChunker(similarity_threshold=0.9, min_sentences_per_chunk=1)
        chunker_strict._model = mock_model
        chunks_strict = chunker_strict.split_text(text)

        # Low threshold (0.5) - fewer boundaries
        chunker_loose = SemanticChunker(similarity_threshold=0.5, min_sentences_per_chunk=1)
        chunker_loose._model = mock_model
        chunks_loose = chunker_loose.split_text(text)

        # Strict should create more/smaller chunks
        assert len(chunks_strict) >= len(chunks_loose)
