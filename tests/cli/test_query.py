"""Tests for query command."""

from unittest.mock import MagicMock, patch, call
import json
import pytest
from click.testing import CliRunner

from src.cli.commands.query import query
from src.retrieval.models import RetrievedChunk


@pytest.fixture
def sample_chunks():
    """Create sample retrieved chunks."""
    return [
        RetrievedChunk(
            chunk_id="chunk-1",
            text="This is the first chunk of relevant content.",
            score=0.95,
            metadata={
                "document_id": "doc-1",
                "document_path": "/path/to/doc1.txt",
                "chunk_index": 0,
                "page_number": 1,
            },
        ),
        RetrievedChunk(
            chunk_id="chunk-2",
            text="This is the second chunk with more information.",
            score=0.88,
            metadata={
                "document_id": "doc-2",
                "document_path": "/path/to/doc2.pdf",
                "chunk_index": 1,
                "page_number": 5,
            },
        ),
    ]


class TestQueryHelp:
    """Test query command help text."""

    def test_query_help(self, cli_runner: CliRunner):
        """Test that help text is displayed."""
        result = cli_runner.invoke(query, ["--help"])
        assert result.exit_code == 0
        assert "Ask a question and get an answer" in result.output
        assert "--k" in result.output
        assert "--show-sources" in result.output
        assert "--format" in result.output
        assert "--no-history" in result.output


class TestBasicQuery:
    """Test basic query functionality."""

    @patch("src.cli.commands.query.HybridRetriever")
    @patch("src.cli.commands.query.BM25Retriever")
    @patch("src.cli.commands.query.Retriever")
    @patch("src.cli.commands.query.OllamaClient")
    @patch("src.cli.commands.query.get_settings")
    def test_query_basic(
        self,
        mock_settings,
        mock_ollama,
        mock_retriever,
        mock_bm25,
        mock_hybrid,
        cli_runner,
        sample_chunks,
    ):
        """Test basic query execution."""
        # Setup mocks
        settings = MagicMock()
        settings.llm_model = "llama2"
        settings.retrieval_method = "hybrid"
        mock_settings.return_value = settings

        hybrid_instance = MagicMock()
        hybrid_instance.retrieve.return_value = sample_chunks
        mock_hybrid.return_value = hybrid_instance

        ollama_instance = MagicMock()
        ollama_instance.generate.return_value = "This is the answer to your question."
        mock_ollama.return_value = ollama_instance

        result = cli_runner.invoke(query, ["What is the topic?"])

        assert result.exit_code == 0
        assert "Question: What is the topic?" in result.output
        assert "This is the answer to your question" in result.output

        # Verify retrieval was performed
        hybrid_instance.retrieve.assert_called_once()
        # Verify LLM was called
        ollama_instance.generate.assert_called_once()

    @patch("src.cli.commands.query.HybridRetriever")
    @patch("src.cli.commands.query.BM25Retriever")
    @patch("src.cli.commands.query.Retriever")
    @patch("src.cli.commands.query.OllamaClient")
    @patch("src.cli.commands.query.get_settings")
    def test_query_with_k_parameter(
        self,
        mock_settings,
        mock_ollama,
        mock_retriever,
        mock_bm25,
        mock_hybrid,
        cli_runner,
        sample_chunks,
    ):
        """Test query with custom k value."""
        settings = MagicMock()
        settings.llm_model = "llama2"
        settings.retrieval_method = "hybrid"
        mock_settings.return_value = settings

        hybrid_instance = MagicMock()
        hybrid_instance.retrieve.return_value = sample_chunks[:3]
        mock_hybrid.return_value = hybrid_instance

        ollama_instance = MagicMock()
        ollama_instance.generate.return_value = "Answer with 3 chunks."
        mock_ollama.return_value = ollama_instance

        result = cli_runner.invoke(query, ["test question", "--k", "3"])

        assert result.exit_code == 0
        # Verify k=3 was used in retrieval
        call_args = hybrid_instance.retrieve.call_args
        assert call_args[0][1] == 3  # Second argument should be k


class TestOutputFormats:
    """Test different output formats."""

    @patch("src.cli.commands.query.HybridRetriever")
    @patch("src.cli.commands.query.BM25Retriever")
    @patch("src.cli.commands.query.Retriever")
    @patch("src.cli.commands.query.OllamaClient")
    @patch("src.cli.commands.query.get_settings")
    def test_query_json_format(
        self,
        mock_settings,
        mock_ollama,
        mock_retriever,
        mock_bm25,
        mock_hybrid,
        cli_runner,
        sample_chunks,
    ):
        """Test query with JSON output format."""
        settings = MagicMock()
        settings.llm_model = "llama2"
        settings.retrieval_method = "hybrid"
        mock_settings.return_value = settings

        hybrid_instance = MagicMock()
        hybrid_instance.retrieve.return_value = sample_chunks
        mock_hybrid.return_value = hybrid_instance

        ollama_instance = MagicMock()
        ollama_instance.generate.return_value = "JSON format answer."
        mock_ollama.return_value = ollama_instance

        result = cli_runner.invoke(query, ["test", "--format", "json"])

        assert result.exit_code == 0
        # Should be valid JSON
        try:
            data = json.loads(result.output)
            assert "query" in data
            assert "answer" in data
            assert "sources" in data
            assert data["query"] == "test"
        except json.JSONDecodeError:
            pytest.fail("Output is not valid JSON")

    @patch("src.cli.commands.query.HybridRetriever")
    @patch("src.cli.commands.query.BM25Retriever")
    @patch("src.cli.commands.query.Retriever")
    @patch("src.cli.commands.query.OllamaClient")
    @patch("src.cli.commands.query.get_settings")
    def test_query_text_format(
        self,
        mock_settings,
        mock_ollama,
        mock_retriever,
        mock_bm25,
        mock_hybrid,
        cli_runner,
        sample_chunks,
    ):
        """Test query with text output format (default)."""
        settings = MagicMock()
        settings.llm_model = "llama2"
        settings.retrieval_method = "hybrid"
        mock_settings.return_value = settings

        hybrid_instance = MagicMock()
        hybrid_instance.retrieve.return_value = sample_chunks
        mock_hybrid.return_value = hybrid_instance

        ollama_instance = MagicMock()
        ollama_instance.generate.return_value = "Text format answer."
        mock_ollama.return_value = ollama_instance

        result = cli_runner.invoke(query, ["test", "--format", "text"])

        assert result.exit_code == 0
        assert "Question:" in result.output
        assert "Text format answer" in result.output


class TestShowSources:
    """Test showing source chunks."""

    @patch("src.cli.commands.query.HybridRetriever")
    @patch("src.cli.commands.query.BM25Retriever")
    @patch("src.cli.commands.query.Retriever")
    @patch("src.cli.commands.query.OllamaClient")
    @patch("src.cli.commands.query.get_settings")
    def test_query_show_sources(
        self,
        mock_settings,
        mock_ollama,
        mock_retriever,
        mock_bm25,
        mock_hybrid,
        cli_runner,
        sample_chunks,
    ):
        """Test query with --show-sources flag."""
        settings = MagicMock()
        settings.llm_model = "llama2"
        settings.retrieval_method = "hybrid"
        mock_settings.return_value = settings

        hybrid_instance = MagicMock()
        hybrid_instance.retrieve.return_value = sample_chunks
        mock_hybrid.return_value = hybrid_instance

        ollama_instance = MagicMock()
        ollama_instance.generate.return_value = "Answer."
        mock_ollama.return_value = ollama_instance

        result = cli_runner.invoke(query, ["test", "--show-sources"])

        assert result.exit_code == 0
        # Should show source information
        assert "Sources:" in result.output or "Retrieved Chunks" in result.output
        # Should show chunk content
        assert "first chunk of relevant content" in result.output or "doc-1" in result.output

    @patch("src.cli.commands.query.HybridRetriever")
    @patch("src.cli.commands.query.BM25Retriever")
    @patch("src.cli.commands.query.Retriever")
    @patch("src.cli.commands.query.OllamaClient")
    @patch("src.cli.commands.query.get_settings")
    def test_query_without_show_sources(
        self,
        mock_settings,
        mock_ollama,
        mock_retriever,
        mock_bm25,
        mock_hybrid,
        cli_runner,
        sample_chunks,
    ):
        """Test query without --show-sources flag."""
        settings = MagicMock()
        settings.llm_model = "llama2"
        settings.retrieval_method = "hybrid"
        mock_settings.return_value = settings

        hybrid_instance = MagicMock()
        hybrid_instance.retrieve.return_value = sample_chunks
        mock_hybrid.return_value = hybrid_instance

        ollama_instance = MagicMock()
        ollama_instance.generate.return_value = "Answer."
        mock_ollama.return_value = ollama_instance

        result = cli_runner.invoke(query, ["test"])

        assert result.exit_code == 0
        # Should NOT show detailed sources
        # (May still show citations in answer, but not full source details)


class TestHistoryIntegration:
    """Test query history integration."""

    @patch("src.cli.commands.query.QueryHistory")
    @patch("src.cli.commands.query.HybridRetriever")
    @patch("src.cli.commands.query.BM25Retriever")
    @patch("src.cli.commands.query.Retriever")
    @patch("src.cli.commands.query.OllamaClient")
    @patch("src.cli.commands.query.get_settings")
    def test_query_saves_to_history(
        self,
        mock_settings,
        mock_ollama,
        mock_retriever,
        mock_bm25,
        mock_hybrid,
        mock_history,
        cli_runner,
        sample_chunks,
    ):
        """Test that query is saved to history by default."""
        settings = MagicMock()
        settings.llm_model = "llama2"
        settings.retrieval_method = "hybrid"
        mock_settings.return_value = settings

        hybrid_instance = MagicMock()
        hybrid_instance.retrieve.return_value = sample_chunks
        mock_hybrid.return_value = hybrid_instance

        ollama_instance = MagicMock()
        ollama_instance.generate.return_value = "Answer."
        mock_ollama.return_value = ollama_instance

        history_instance = MagicMock()
        mock_history.return_value = history_instance

        result = cli_runner.invoke(query, ["test question"])

        assert result.exit_code == 0
        # Verify history was saved
        history_instance.add.assert_called_once()

    @patch("src.cli.commands.query.QueryHistory")
    @patch("src.cli.commands.query.HybridRetriever")
    @patch("src.cli.commands.query.BM25Retriever")
    @patch("src.cli.commands.query.Retriever")
    @patch("src.cli.commands.query.OllamaClient")
    @patch("src.cli.commands.query.get_settings")
    def test_query_no_history_flag(
        self,
        mock_settings,
        mock_ollama,
        mock_retriever,
        mock_bm25,
        mock_hybrid,
        mock_history,
        cli_runner,
        sample_chunks,
    ):
        """Test that --no-history prevents saving to history."""
        settings = MagicMock()
        settings.llm_model = "llama2"
        settings.retrieval_method = "hybrid"
        mock_settings.return_value = settings

        hybrid_instance = MagicMock()
        hybrid_instance.retrieve.return_value = sample_chunks
        mock_hybrid.return_value = hybrid_instance

        ollama_instance = MagicMock()
        ollama_instance.generate.return_value = "Answer."
        mock_ollama.return_value = ollama_instance

        history_instance = MagicMock()
        mock_history.return_value = history_instance

        result = cli_runner.invoke(query, ["test", "--no-history"])

        assert result.exit_code == 0
        # Verify history was NOT saved
        history_instance.add.assert_not_called()


class TestCitationFormatting:
    """Test citation formatting in responses."""

    @patch("src.cli.commands.query.format_response_with_references")
    @patch("src.cli.commands.query.HybridRetriever")
    @patch("src.cli.commands.query.BM25Retriever")
    @patch("src.cli.commands.query.Retriever")
    @patch("src.cli.commands.query.OllamaClient")
    @patch("src.cli.commands.query.get_settings")
    def test_query_with_citations(
        self,
        mock_settings,
        mock_ollama,
        mock_retriever,
        mock_bm25,
        mock_hybrid,
        mock_format_refs,
        cli_runner,
        sample_chunks,
    ):
        """Test that citations are formatted properly."""
        settings = MagicMock()
        settings.llm_model = "llama2"
        settings.retrieval_method = "hybrid"
        mock_settings.return_value = settings

        hybrid_instance = MagicMock()
        hybrid_instance.retrieve.return_value = sample_chunks
        mock_hybrid.return_value = hybrid_instance

        ollama_instance = MagicMock()
        ollama_instance.generate.return_value = "Answer with [1] citation."
        mock_ollama.return_value = ollama_instance

        mock_format_refs.return_value = "Answer with [1] citation.\n\nReferences:\n[1] doc1.txt"

        result = cli_runner.invoke(query, ["test"])

        assert result.exit_code == 0
        # Verify citation formatter was called
        mock_format_refs.assert_called_once()
        # Verify formatted output includes references
        assert "References:" in result.output or "[1]" in result.output


class TestErrorHandling:
    """Test error handling in query command."""

    @patch("src.cli.commands.query.HybridRetriever")
    @patch("src.cli.commands.query.BM25Retriever")
    @patch("src.cli.commands.query.Retriever")
    @patch("src.cli.commands.query.OllamaClient")
    @patch("src.cli.commands.query.get_settings")
    def test_query_no_documents(
        self,
        mock_settings,
        mock_ollama,
        mock_retriever,
        mock_bm25,
        mock_hybrid,
        cli_runner,
    ):
        """Test query when no documents are found."""
        settings = MagicMock()
        settings.llm_model = "llama2"
        settings.retrieval_method = "hybrid"
        mock_settings.return_value = settings

        hybrid_instance = MagicMock()
        hybrid_instance.retrieve.return_value = []  # No chunks
        mock_hybrid.return_value = hybrid_instance

        ollama_instance = MagicMock()
        ollama_instance.generate.return_value = "I don't have enough information."
        mock_ollama.return_value = ollama_instance

        result = cli_runner.invoke(query, ["test"])

        assert result.exit_code == 0
        # Should still provide an answer (even if not useful)
        assert "don't have" in result.output.lower() or "information" in result.output.lower()

    @patch("src.cli.commands.query.HybridRetriever")
    @patch("src.cli.commands.query.BM25Retriever")
    @patch("src.cli.commands.query.Retriever")
    @patch("src.cli.commands.query.OllamaClient")
    @patch("src.cli.commands.query.get_settings")
    def test_query_ollama_connection_error(
        self,
        mock_settings,
        mock_ollama,
        mock_retriever,
        mock_bm25,
        mock_hybrid,
        cli_runner,
        sample_chunks,
    ):
        """Test query when Ollama is not available."""
        settings = MagicMock()
        settings.llm_model = "llama2"
        settings.retrieval_method = "hybrid"
        mock_settings.return_value = settings

        hybrid_instance = MagicMock()
        hybrid_instance.retrieve.return_value = sample_chunks
        mock_hybrid.return_value = hybrid_instance

        ollama_instance = MagicMock()
        ollama_instance.generate.side_effect = Exception("Connection refused")
        mock_ollama.return_value = ollama_instance

        result = cli_runner.invoke(query, ["test"])

        assert result.exit_code == 1
        assert "Error" in result.output or "failed" in result.output.lower()

    @patch("src.cli.commands.query.HybridRetriever")
    @patch("src.cli.commands.query.BM25Retriever")
    @patch("src.cli.commands.query.Retriever")
    @patch("src.cli.commands.query.OllamaClient")
    @patch("src.cli.commands.query.get_settings")
    def test_query_retrieval_error(
        self,
        mock_settings,
        mock_ollama,
        mock_retriever,
        mock_bm25,
        mock_hybrid,
        cli_runner,
    ):
        """Test query when retrieval fails."""
        settings = MagicMock()
        settings.llm_model = "llama2"
        settings.retrieval_method = "hybrid"
        mock_settings.return_value = settings

        hybrid_instance = MagicMock()
        hybrid_instance.retrieve.side_effect = Exception("ChromaDB connection error")
        mock_hybrid.return_value = hybrid_instance

        result = cli_runner.invoke(query, ["test"])

        assert result.exit_code == 1
        assert "Error" in result.output or "failed" in result.output.lower()


class TestEdgeCases:
    """Test edge cases and special scenarios."""

    @patch("src.cli.commands.query.HybridRetriever")
    @patch("src.cli.commands.query.BM25Retriever")
    @patch("src.cli.commands.query.Retriever")
    @patch("src.cli.commands.query.OllamaClient")
    @patch("src.cli.commands.query.get_settings")
    def test_query_empty_string(
        self,
        mock_settings,
        mock_ollama,
        mock_retriever,
        mock_bm25,
        mock_hybrid,
        cli_runner,
        sample_chunks,
    ):
        """Test query with empty string."""
        settings = MagicMock()
        settings.llm_model = "llama2"
        settings.retrieval_method = "hybrid"
        mock_settings.return_value = settings

        hybrid_instance = MagicMock()
        hybrid_instance.retrieve.return_value = sample_chunks
        mock_hybrid.return_value = hybrid_instance

        ollama_instance = MagicMock()
        ollama_instance.generate.return_value = "Please provide a question."
        mock_ollama.return_value = ollama_instance

        result = cli_runner.invoke(query, [""])

        # Should handle empty query gracefully
        # Exit code may be 0 or 1 depending on validation
        assert "Please" in result.output or "Error" in result.output or "provide" in result.output

    @patch("src.cli.commands.query.HybridRetriever")
    @patch("src.cli.commands.query.BM25Retriever")
    @patch("src.cli.commands.query.Retriever")
    @patch("src.cli.commands.query.OllamaClient")
    @patch("src.cli.commands.query.get_settings")
    def test_query_very_long_question(
        self,
        mock_settings,
        mock_ollama,
        mock_retriever,
        mock_bm25,
        mock_hybrid,
        cli_runner,
        sample_chunks,
    ):
        """Test query with very long question."""
        settings = MagicMock()
        settings.llm_model = "llama2"
        settings.retrieval_method = "hybrid"
        mock_settings.return_value = settings

        hybrid_instance = MagicMock()
        hybrid_instance.retrieve.return_value = sample_chunks
        mock_hybrid.return_value = hybrid_instance

        ollama_instance = MagicMock()
        ollama_instance.generate.return_value = "Answer to long question."
        mock_ollama.return_value = ollama_instance

        long_question = "What is " * 500 + "the answer?"  # Very long question

        result = cli_runner.invoke(query, [long_question])

        assert result.exit_code == 0
        # Should handle long questions without crashing

    @patch("src.cli.commands.query.HybridRetriever")
    @patch("src.cli.commands.query.BM25Retriever")
    @patch("src.cli.commands.query.Retriever")
    @patch("src.cli.commands.query.OllamaClient")
    @patch("src.cli.commands.query.get_settings")
    def test_query_with_special_characters(
        self,
        mock_settings,
        mock_ollama,
        mock_retriever,
        mock_bm25,
        mock_hybrid,
        cli_runner,
        sample_chunks,
    ):
        """Test query with special characters."""
        settings = MagicMock()
        settings.llm_model = "llama2"
        settings.retrieval_method = "hybrid"
        mock_settings.return_value = settings

        hybrid_instance = MagicMock()
        hybrid_instance.retrieve.return_value = sample_chunks
        mock_hybrid.return_value = hybrid_instance

        ollama_instance = MagicMock()
        ollama_instance.generate.return_value = "Answer."
        mock_ollama.return_value = ollama_instance

        result = cli_runner.invoke(query, ["What's the <answer> & \"result\"?"])

        assert result.exit_code == 0
        # Should handle special characters without issues
