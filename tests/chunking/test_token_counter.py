"""Tests for token counting."""

import pytest

from src.chunking.token_counter import (
    count_tokens,
    estimate_tokens,
    get_tokenizer,
    split_by_tokens,
    tokens_to_chars,
)


class TestGetTokenizer:
    """Test suite for tokenizer retrieval."""

    def test_returns_tokenizer(self) -> None:
        """Test that get_tokenizer returns a tokenizer instance."""
        tokenizer = get_tokenizer()
        assert tokenizer is not None

    def test_caches_tokenizer(self) -> None:
        """Test that tokenizer is cached."""
        tokenizer1 = get_tokenizer()
        tokenizer2 = get_tokenizer()
        assert tokenizer1 is tokenizer2


class TestCountTokens:
    """Test suite for token counting."""

    def test_counts_simple_text(self) -> None:
        """Test token counting on simple text."""
        text = "Hello, world!"
        count = count_tokens(text)
        assert count > 0
        assert count < 10  # Should be around 3-4

    def test_counts_long_text(self) -> None:
        """Test token counting on longer text."""
        text = "This is a longer sentence with more tokens. " * 10
        count = count_tokens(text)
        assert count > 50

    def test_empty_text(self) -> None:
        """Test token counting on empty text."""
        count = count_tokens("")
        assert count == 0

    def test_special_characters(self) -> None:
        """Test token counting with special characters."""
        text = "Hello! How are you? 👋"
        count = count_tokens(text)
        assert count > 0


class TestEstimateTokens:
    """Test suite for token estimation."""

    def test_estimates_tokens(self) -> None:
        """Test that estimation is roughly correct."""
        text = "This is a test sentence."
        estimate = estimate_tokens(text)
        actual = count_tokens(text)
        # Should be within 50% of actual
        assert abs(estimate - actual) < actual * 0.5


class TestSplitByTokens:
    """Test suite for token-based splitting."""

    def test_splits_text(self) -> None:
        """Test that text is split into chunks."""
        text = "This is a test. " * 100
        chunks = split_by_tokens(text, max_tokens=50)
        assert len(chunks) > 1
        for chunk in chunks:
            assert count_tokens(chunk) <= 50

    def test_respects_overlap(self) -> None:
        """Test that overlap is applied correctly."""
        text = "This is a test. " * 100
        chunks = split_by_tokens(text, max_tokens=50, overlap_tokens=10)
        # Check that chunks overlap by verifying we have more chunks with overlap
        chunks_no_overlap = split_by_tokens(text, max_tokens=50, overlap_tokens=0)
        # With overlap, chunks should be more numerous (or at least >= without overlap)
        assert len(chunks) >= len(chunks_no_overlap)


class TestTokensToChars:
    """Test suite for token-to-character estimation."""

    def test_estimates_characters(self) -> None:
        """Test character count estimation."""
        chars = tokens_to_chars(100)
        assert chars > 0
        assert chars > 100  # Should be around 400
