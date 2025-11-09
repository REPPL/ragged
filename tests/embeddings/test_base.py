"""Tests for base embedder interface."""

import pytest
from abc import ABC
from src.embeddings.base import BaseEmbedder


class TestBaseEmbedder:
    """Tests for BaseEmbedder abstract class."""

    def test_base_embedder_is_abstract(self):
        """Test that BaseEmbedder cannot be instantiated directly."""
        with pytest.raises(TypeError):
            BaseEmbedder()

    def test_concrete_implementation_must_implement_embed_text(self):
        """Test that concrete classes must implement embed_text."""

        class IncompleteEmbedder(BaseEmbedder):
            """Incomplete embedder missing embed_text."""
            pass

        with pytest.raises(TypeError):
            IncompleteEmbedder()

    def test_concrete_implementation_must_implement_embed_batch(self):
        """Test that concrete classes must implement embed_batch."""

        class IncompleteEmbedder(BaseEmbedder):
            """Incomplete embedder missing embed_batch."""

            def embed_text(self, text: str) -> list[float]:
                return [0.1, 0.2, 0.3]

        with pytest.raises(TypeError):
            IncompleteEmbedder()

    def test_concrete_implementation_must_implement_dimension(self):
        """Test that concrete classes must implement dimension property."""

        class IncompleteEmbedder(BaseEmbedder):
            """Incomplete embedder missing dimension."""

            def embed_text(self, text: str) -> list[float]:
                return [0.1, 0.2, 0.3]

            def embed_batch(self, texts: list[str]) -> list[list[float]]:
                return [[0.1, 0.2, 0.3] for _ in texts]

        with pytest.raises(TypeError):
            IncompleteEmbedder()

    def test_concrete_implementation_works(self):
        """Test that a complete implementation can be instantiated."""

        class CompleteEmbedder(BaseEmbedder):
            """Complete embedder implementation."""

            @property
            def dimension(self) -> int:
                return 3

            def embed_text(self, text: str) -> list[float]:
                return [0.1, 0.2, 0.3]

            def embed_batch(self, texts: list[str]) -> list[list[float]]:
                return [[0.1, 0.2, 0.3] for _ in texts]

        # Should not raise
        embedder = CompleteEmbedder()
        assert embedder is not None
        assert embedder.dimension == 3

    def test_concrete_implementation_embed_text(self):
        """Test embed_text method on concrete implementation."""

        class TestEmbedder(BaseEmbedder):
            @property
            def dimension(self) -> int:
                return 4

            def embed_text(self, text: str) -> list[float]:
                # Simple mock: return length-based embedding
                length = len(text)
                return [float(length), 0.5, 0.5, 0.5]

            def embed_batch(self, texts: list[str]) -> list[list[float]]:
                return [self.embed_text(text) for text in texts]

        embedder = TestEmbedder()
        result = embedder.embed_text("test")

        assert isinstance(result, list)
        assert len(result) == 4
        assert all(isinstance(x, float) for x in result)

    def test_concrete_implementation_embed_batch(self):
        """Test embed_batch method on concrete implementation."""

        class TestEmbedder(BaseEmbedder):
            @property
            def dimension(self) -> int:
                return 3

            def embed_text(self, text: str) -> list[float]:
                return [0.1, 0.2, 0.3]

            def embed_batch(self, texts: list[str]) -> list[list[float]]:
                return [self.embed_text(text) for text in texts]

        embedder = TestEmbedder()
        results = embedder.embed_batch(["text1", "text2", "text3"])

        assert isinstance(results, list)
        assert len(results) == 3
        assert all(isinstance(embedding, list) for embedding in results)
        assert all(len(embedding) == 3 for embedding in results)
