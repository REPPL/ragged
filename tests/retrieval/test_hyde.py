"""Tests for HyDE (Hypothetical Document Embeddings) module."""

from unittest.mock import MagicMock, patch

import pytest

from src.retrieval.hyde import HyDEGenerator, HypotheticalDocument, HYDE_PROMPT


class TestHypotheticalDocument:
    """Test HypotheticalDocument dataclass."""

    def test_hypothetical_document_creation(self):
        """Test creating a HypotheticalDocument."""
        doc = HypotheticalDocument(
            query="What is ML?",
            hypothetical_text="Machine learning is...",
            confidence=0.85,
            used_for_retrieval=True,
        )

        assert doc.query == "What is ML?"
        assert "Machine learning" in doc.hypothetical_text
        assert doc.confidence == 0.85
        assert doc.used_for_retrieval is True


class TestHyDEGenerator:
    """Test HyDEGenerator class."""

    def test_hyde_generator_initialization(self):
        """Test HyDE generator initialization."""
        hyde = HyDEGenerator(confidence_threshold=0.7)

        assert hyde.confidence_threshold == 0.7
        assert hyde.enable_caching is True

    @patch('src.retrieval.hyde.OllamaClient')
    def test_generate_hypothetical_document(self, mock_ollama_class):
        """Test generating a hypothetical document."""
        mock_client = MagicMock()
        mock_client.generate.return_value = "Machine learning is a subset of AI that enables systems to learn from data."

        hyde = HyDEGenerator(ollama_client=mock_client)

        result = hyde.generate("What is machine learning?")

        assert mock_client.generate.called
        assert "Machine learning" in result.hypothetical_text
        assert result.query == "What is machine learning?"

    @patch('src.retrieval.hyde.OllamaClient')
    def test_llm_called_with_correct_parameters(self, mock_ollama_class):
        """Test that LLM is called with correct parameters."""
        mock_client = MagicMock()
        mock_client.generate.return_value = "Test answer"

        hyde = HyDEGenerator(ollama_client=mock_client)
        hyde.generate("Test query")

        call_args = mock_client.generate.call_args
        assert "Test query" in call_args[1]["prompt"]
        assert call_args[1]["temperature"] == 0.5
        assert call_args[1]["max_tokens"] == 150

    def test_confidence_estimation_good_answer(self):
        """Test confidence estimation for good answer."""
        hyde = HyDEGenerator()

        confidence = hyde._estimate_confidence(
            "What is ML?",
            "Machine learning is a field of artificial intelligence that uses statistical techniques to give computer systems the ability to learn from data."
        )

        assert confidence > 0.7  # Should be reasonably high

    def test_confidence_estimation_with_red_flags(self):
        """Test confidence estimation with red flags."""
        hyde = HyDEGenerator()

        confidence = hyde._estimate_confidence(
            "What is ML?",
            "I don't know what machine learning is."
        )

        assert confidence < 0.5  # Should be low due to red flag

    def test_confidence_estimation_too_short(self):
        """Test confidence estimation for too short answer."""
        hyde = HyDEGenerator()

        confidence = hyde._estimate_confidence(
            "What is ML?",
            "Machine learning."
        )

        assert confidence < 0.7  # Should be lower for short answer

    def test_confidence_estimation_with_questions(self):
        """Test confidence estimation when answer contains questions."""
        hyde = HyDEGenerator()

        confidence = hyde._estimate_confidence(
            "What is ML?",
            "Machine learning is AI. But what is AI?"
        )

        assert confidence < 0.8  # Should be lower when asking questions back

    @patch('src.retrieval.hyde.OllamaClient')
    def test_cache_hit(self, mock_ollama_class):
        """Test that caching works."""
        mock_client = MagicMock()
        mock_client.generate.return_value = "Test answer"

        hyde = HyDEGenerator(ollama_client=mock_client, enable_caching=True)

        # First call
        result1 = hyde.generate("Test query")

        # Second call - should hit cache
        result2 = hyde.generate("Test query")

        # LLM should only be called once
        assert mock_client.generate.call_count == 1
        assert result1.hypothetical_text == result2.hypothetical_text

    @patch('src.retrieval.hyde.OllamaClient')
    def test_fallback_on_error(self, mock_ollama_class):
        """Test fallback when LLM fails."""
        mock_client = MagicMock()
        mock_client.generate.side_effect = Exception("LLM error")

        hyde = HyDEGenerator(ollama_client=mock_client)

        result = hyde.generate("Test query")

        assert result.confidence == 0.0
        assert result.used_for_retrieval is False
        assert result.hypothetical_text == ""

    def test_should_use_hyde_high_confidence(self):
        """Test should_use_hyde with high confidence."""
        hyde = HyDEGenerator(confidence_threshold=0.5)

        doc = HypotheticalDocument(
            query="Test",
            hypothetical_text="Answer",
            confidence=0.8,
            used_for_retrieval=True,
        )

        assert hyde.should_use_hyde("Test", doc) is True

    def test_should_use_hyde_low_confidence(self):
        """Test should_use_hyde with low confidence."""
        hyde = HyDEGenerator(confidence_threshold=0.7)

        doc = HypotheticalDocument(
            query="Test",
            hypothetical_text="Answer",
            confidence=0.5,
            used_for_retrieval=False,
        )

        assert hyde.should_use_hyde("Test", doc) is False

    def test_clear_cache(self):
        """Test clearing the cache."""
        hyde = HyDEGenerator(enable_caching=True)

        hyde._cache["test"] = "value"
        assert len(hyde._cache) > 0

        hyde.clear_cache()
        assert len(hyde._cache) == 0

    def test_cache_key_case_insensitive(self):
        """Test that cache keys are case-insensitive."""
        hyde = HyDEGenerator()

        key1 = hyde._get_cache_key("Test Query")
        key2 = hyde._get_cache_key("test query")

        assert key1 == key2

    @patch('src.retrieval.hyde.OllamaClient')
    def test_used_for_retrieval_flag(self, mock_ollama_class):
        """Test that used_for_retrieval flag is set correctly."""
        mock_client = MagicMock()
        mock_client.generate.return_value = "Machine learning is a field of AI that uses statistical techniques."

        hyde = HyDEGenerator(ollama_client=mock_client, confidence_threshold=0.8)

        result = hyde.generate("What is ML?")

        # Good answer should have high confidence and be used
        if result.confidence >= 0.8:
            assert result.used_for_retrieval is True
        else:
            assert result.used_for_retrieval is False
