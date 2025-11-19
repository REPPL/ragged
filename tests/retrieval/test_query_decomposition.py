"""Tests for query decomposition module."""

from unittest.mock import MagicMock, patch

import pytest

from src.retrieval.query_decomposition import (
    DecomposedQuery,
    QueryDecomposer,
    DECOMPOSITION_PROMPT,
)


class TestDecomposedQuery:
    """Test DecomposedQuery dataclass."""

    def test_decomposed_query_creation(self):
        """Test creating a DecomposedQuery."""
        result = DecomposedQuery(
            original_query="What and how?",
            sub_queries=["What?", "How?"],
            was_decomposed=True,
        )

        assert result.original_query == "What and how?"
        assert len(result.sub_queries) == 2
        assert result.was_decomposed is True

    def test_simple_query_representation(self):
        """Test __repr__ for simple queries."""
        result = DecomposedQuery(
            original_query="Simple question",
            sub_queries=["Simple question"],
            was_decomposed=False,
        )

        repr_str = repr(result)
        assert "simple_query" in repr_str
        assert "Simple question" in repr_str


class TestQueryDecomposer:
    """Test QueryDecomposer class."""

    def test_decomposer_initialization(self):
        """Test decomposer initialization."""
        decomposer = QueryDecomposer(enable_caching=True)

        assert decomposer.enable_caching is True
        assert decomposer.max_sub_queries == 4
        assert decomposer.min_query_length == 20

    def test_simple_query_not_decomposed(self):
        """Test that simple queries are not decomposed."""
        decomposer = QueryDecomposer()

        result = decomposer.decompose("What is ML?")

        assert result.was_decomposed is False
        assert len(result.sub_queries) == 1
        assert result.sub_queries[0] == "What is ML?"

    def test_short_query_not_decomposed(self):
        """Test that very short queries are not decomposed."""
        decomposer = QueryDecomposer()

        result = decomposer.decompose("Test")

        assert result.was_decomposed is False
        assert len(result.sub_queries) == 1

    @patch('src.retrieval.query_decomposition.OllamaClient')
    def test_complex_query_decomposed(self, mock_ollama_class):
        """Test that complex queries are decomposed."""
        # Mock LLM response
        mock_client = MagicMock()
        mock_client.generate.return_value = "What methods were used?\nHow do they compare?"
        mock_ollama_class.return_value = mock_client

        decomposer = QueryDecomposer(ollama_client=mock_client)

        result = decomposer.decompose(
            "What methods were used and how do they compare to prior work?"
        )

        assert mock_client.generate.called
        assert result.was_decomposed is True
        assert len(result.sub_queries) == 2

    @patch('src.retrieval.query_decomposition.OllamaClient')
    def test_decomposition_with_llm_call(self, mock_ollama_class):
        """Test decomposition makes LLM call with correct parameters."""
        mock_client = MagicMock()
        mock_client.generate.return_value = "Sub-query 1\nSub-query 2"
        mock_ollama_class.return_value = mock_client

        decomposer = QueryDecomposer(ollama_client=mock_client)

        result = decomposer.decompose(
            "What is the dataset, model, and evaluation used?"
        )

        # Verify LLM was called with prompt containing query
        call_args = mock_client.generate.call_args
        assert "dataset" in call_args[1]["prompt"]
        assert call_args[1]["temperature"] == 0.3

    def test_cache_hit(self):
        """Test that caching works."""
        mock_client = MagicMock()
        mock_client.generate.return_value = "Sub 1\nSub 2"

        decomposer = QueryDecomposer(ollama_client=mock_client, enable_caching=True)

        # First call - should hit LLM
        result1 = decomposer.decompose("Complex query with multiple parts and aspects?")

        # Second call - should hit cache
        result2 = decomposer.decompose("Complex query with multiple parts and aspects?")

        # LLM should only be called once
        assert mock_client.generate.call_count <= 1
        assert result1.original_query == result2.original_query

    def test_max_sub_queries_limit(self):
        """Test that max sub-queries limit is enforced."""
        mock_client = MagicMock()
        # Return more than max (4)
        mock_client.generate.return_value = "Q1\nQ2\nQ3\nQ4\nQ5\nQ6"

        decomposer = QueryDecomposer(ollama_client=mock_client)

        result = decomposer.decompose(
            "Very complex query with many aspects and parts and things?"
        )

        # Should be limited to max_sub_queries
        assert len(result.sub_queries) <= decomposer.max_sub_queries

    def test_is_complex_query_with_and(self):
        """Test complex query detection with 'and'."""
        decomposer = QueryDecomposer()

        assert decomposer._is_complex_query("What methods and how compare?")

    def test_is_complex_query_with_multiple_questions(self):
        """Test complex query detection with multiple '?'."""
        decomposer = QueryDecomposer()

        assert decomposer._is_complex_query("What is this? How does it work?")

    def test_is_complex_query_with_commas(self):
        """Test complex query detection with multiple commas."""
        decomposer = QueryDecomposer()

        assert decomposer._is_complex_query("Explain the dataset, model, and metrics.")

    def test_is_complex_query_simple(self):
        """Test that simple queries are not flagged as complex."""
        decomposer = QueryDecomposer()

        assert not decomposer._is_complex_query("What is machine learning?")

    @patch('src.retrieval.query_decomposition.OllamaClient')
    def test_fallback_on_error(self, mock_ollama_class):
        """Test fallback to original query on error."""
        mock_client = MagicMock()
        mock_client.generate.side_effect = Exception("LLM error")

        decomposer = QueryDecomposer(ollama_client=mock_client)

        result = decomposer.decompose(
            "Complex query that will fail during decomposition?"
        )

        # Should fallback to original query
        assert result.was_decomposed is False
        assert len(result.sub_queries) == 1
        assert result.sub_queries[0] == "Complex query that will fail during decomposition?"

    @patch('src.retrieval.query_decomposition.OllamaClient')
    def test_deduplication(self, mock_ollama_class):
        """Test that duplicate sub-queries are removed."""
        mock_client = MagicMock()
        # Return duplicates
        mock_client.generate.return_value = "What is ML?\nWhat is ML?\nHow does ML work?"

        decomposer = QueryDecomposer(ollama_client=mock_client)

        result = decomposer.decompose(
            "What is ML and what is ML and how does it work?"
        )

        # Duplicates should be removed
        unique_queries = set(q.lower() for q in result.sub_queries)
        assert len(unique_queries) == len(result.sub_queries)

    def test_clear_cache(self):
        """Test clearing the cache."""
        decomposer = QueryDecomposer(enable_caching=True)

        # Add something to cache
        decomposer._cache["test"] = "value"
        assert len(decomposer._cache) > 0

        decomposer.clear_cache()
        assert len(decomposer._cache) == 0

    def test_cache_key_case_insensitive(self):
        """Test that cache keys are case-insensitive."""
        decomposer = QueryDecomposer()

        key1 = decomposer._get_cache_key("Test Query")
        key2 = decomposer._get_cache_key("test query")

        assert key1 == key2

    @patch('src.retrieval.query_decomposition.OllamaClient')
    def test_empty_response_fallback(self, mock_ollama_class):
        """Test fallback when LLM returns empty response."""
        mock_client = MagicMock()
        mock_client.generate.return_value = ""

        decomposer = QueryDecomposer(ollama_client=mock_client)

        result = decomposer.decompose(
            "Complex query that gets empty response?"
        )

        # Should fallback to original
        assert len(result.sub_queries) == 1
        assert result.sub_queries[0] == "Complex query that gets empty response?"
