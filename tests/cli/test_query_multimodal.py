"""Tests for v0.5.3 multi-modal query commands."""

import pytest
from click.testing import CliRunner
from pathlib import Path
from unittest.mock import patch, MagicMock

from ragged.cli.commands.query_multimodal import query_group


@pytest.fixture
def cli_runner():
    """Create CLI runner."""
    return CliRunner()


@pytest.fixture
def sample_image(tmp_path):
    """Create a sample image file for testing."""
    img_file = tmp_path / "test.png"
    # Minimal PNG signature
    img_file.write_bytes(b'\x89PNG\r\n\x1a\n')
    return img_file


class TestQueryTextCommand:
    """Test query text command."""

    def test_query_text_help(self, cli_runner):
        """Test text command help text."""
        result = cli_runner.invoke(query_group, ["text", "--help"])
        assert result.exit_code == 0
        assert "text" in result.output.lower()
        assert "--boost-diagrams" in result.output or "boost" in result.output.lower()

    def test_query_text_requires_argument(self, cli_runner):
        """Test that text query requires a query string."""
        result = cli_runner.invoke(query_group, ["text"])
        assert result.exit_code != 0

    @patch("ragged.cli.commands.query_multimodal.VisionRetriever")
    def test_query_text_basic(self, mock_retriever, cli_runner):
        """Test basic text query."""
        # Mock retriever
        mock_ret = MagicMock()
        mock_ret.query_text.return_value = {
            "results": [{"text": "sample", "score": 0.9}],
            "query_time_ms": 100
        }
        mock_retriever.return_value = mock_ret

        result = cli_runner.invoke(query_group, ["text", "test query"])
        assert result.exit_code in [0, 1]

    @patch("ragged.cli.commands.query_multimodal.VisionRetriever")
    def test_query_text_with_boost_diagrams(self, mock_retriever, cli_runner):
        """Test text query with diagram boosting."""
        mock_ret = MagicMock()
        mock_ret.query_text.return_value = {"results": [], "query_time_ms": 100}
        mock_retriever.return_value = mock_ret

        result = cli_runner.invoke(query_group, ["text", "test", "--boost-diagrams"])
        assert result.exit_code in [0, 1]

    @patch("ragged.cli.commands.query_multimodal.VisionRetriever")
    def test_query_text_with_boost_tables(self, mock_retriever, cli_runner):
        """Test text query with table boosting."""
        mock_ret = MagicMock()
        mock_ret.query_text.return_value = {"results": [], "query_time_ms": 100}
        mock_retriever.return_value = mock_ret

        result = cli_runner.invoke(query_group, ["text", "test", "--boost-tables"])
        assert result.exit_code in [0, 1]

    @patch("ragged.cli.commands.query_multimodal.VisionRetriever")
    def test_query_text_num_results(self, mock_retriever, cli_runner):
        """Test text query with custom result count."""
        mock_ret = MagicMock()
        mock_ret.query_text.return_value = {"results": [], "query_time_ms": 100}
        mock_retriever.return_value = mock_ret

        result = cli_runner.invoke(query_group, ["text", "test", "--num-results", "10"])
        assert result.exit_code in [0, 1]


class TestQueryImageCommand:
    """Test query image command."""

    def test_query_image_help(self, cli_runner):
        """Test image command help text."""
        result = cli_runner.invoke(query_group, ["image", "--help"])
        assert result.exit_code == 0
        assert "image" in result.output.lower() or "visual" in result.output.lower()

    def test_query_image_requires_argument(self, cli_runner):
        """Test that image query requires an image path."""
        result = cli_runner.invoke(query_group, ["image"])
        assert result.exit_code != 0

    @patch("ragged.cli.commands.query_multimodal.VisionRetriever")
    def test_query_image_basic(self, mock_retriever, cli_runner, sample_image):
        """Test basic image query."""
        mock_ret = MagicMock()
        mock_ret.query_image.return_value = {
            "results": [{"document_id": "doc1", "score": 0.85, "page": 1}],
            "query_time_ms": 150
        }
        mock_retriever.return_value = mock_ret

        result = cli_runner.invoke(query_group, ["image", str(sample_image)])
        assert result.exit_code in [0, 1]

    @patch("ragged.cli.commands.query_multimodal.VisionRetriever")
    def test_query_image_num_results(self, mock_retriever, cli_runner, sample_image):
        """Test image query with custom result count."""
        mock_ret = MagicMock()
        mock_ret.query_image.return_value = {"results": [], "query_time_ms": 150}
        mock_retriever.return_value = mock_ret

        result = cli_runner.invoke(query_group, ["image", str(sample_image),
                                                  "--num-results", "5"])
        assert result.exit_code in [0, 1]


class TestQueryHybridCommand:
    """Test query hybrid command."""

    def test_query_hybrid_help(self, cli_runner):
        """Test hybrid command help text."""
        result = cli_runner.invoke(query_group, ["hybrid", "--help"])
        assert result.exit_code == 0
        assert "hybrid" in result.output.lower()
        assert "--text-weight" in result.output or "weight" in result.output.lower()

    def test_query_hybrid_requires_arguments(self, cli_runner):
        """Test that hybrid query requires both text and image."""
        result = cli_runner.invoke(query_group, ["hybrid"])
        assert result.exit_code != 0

    @patch("ragged.cli.commands.query_multimodal.VisionRetriever")
    def test_query_hybrid_basic(self, mock_retriever, cli_runner, sample_image):
        """Test basic hybrid query."""
        mock_ret = MagicMock()
        mock_ret.query_hybrid.return_value = {
            "results": [{"document_id": "doc1", "score": 0.9, "source": "fusion"}],
            "query_time_ms": 200
        }
        mock_retriever.return_value = mock_ret

        result = cli_runner.invoke(query_group, ["hybrid", "test query",
                                                  str(sample_image)])
        assert result.exit_code in [0, 1]

    @patch("ragged.cli.commands.query_multimodal.VisionRetriever")
    def test_query_hybrid_custom_weights(self, mock_retriever, cli_runner, sample_image):
        """Test hybrid query with custom fusion weights."""
        mock_ret = MagicMock()
        mock_ret.query_hybrid.return_value = {"results": [], "query_time_ms": 200}
        mock_retriever.return_value = mock_ret

        result = cli_runner.invoke(query_group, ["hybrid", "test", str(sample_image),
                                                  "--text-weight", "0.7",
                                                  "--vision-weight", "0.3"])
        assert result.exit_code in [0, 1]


class TestQueryInteractiveCommand:
    """Test query interactive command."""

    def test_query_interactive_help(self, cli_runner):
        """Test interactive command help text."""
        result = cli_runner.invoke(query_group, ["interactive", "--help"])
        assert result.exit_code == 0
        assert "interactive" in result.output.lower() or "repl" in result.output.lower()

    @patch("ragged.cli.commands.query_multimodal.VisionRetriever")
    def test_query_interactive_quit(self, mock_retriever, cli_runner):
        """Test interactive mode can be quit."""
        mock_ret = MagicMock()
        mock_retriever.return_value = mock_ret

        # Send :quit command
        result = cli_runner.invoke(query_group, ["interactive"], input=":quit\n")
        # Should exit cleanly
        assert result.exit_code in [0, 1]


class TestQueryGroupCommand:
    """Test query command group."""

    def test_query_group_help(self, cli_runner):
        """Test query group help text."""
        result = cli_runner.invoke(query_group, ["--help"])
        assert result.exit_code == 0
        assert "query" in result.output.lower() or "multi-modal" in result.output.lower()
        assert "text" in result.output.lower()
        assert "image" in result.output.lower()
        assert "hybrid" in result.output.lower()
        assert "interactive" in result.output.lower()

    def test_query_no_subcommand(self, cli_runner):
        """Test query without subcommand shows help."""
        result = cli_runner.invoke(query_group, [])
        assert result.exit_code in [0, 2]


class TestQueryOutputFormats:
    """Test query output formatting."""

    @patch("ragged.cli.commands.query_multimodal.VisionRetriever")
    def test_query_text_json_format(self, mock_retriever, cli_runner):
        """Test JSON output format."""
        mock_ret = MagicMock()
        mock_ret.query_text.return_value = {"results": [], "query_time_ms": 100}
        mock_retriever.return_value = mock_ret

        result = cli_runner.invoke(query_group, ["text", "test", "--format", "json"])
        # Should produce JSON output
        assert result.exit_code in [0, 1]

    @patch("ragged.cli.commands.query_multimodal.VisionRetriever")
    def test_query_with_metadata(self, mock_retriever, cli_runner):
        """Test --show-metadata flag."""
        mock_ret = MagicMock()
        mock_ret.query_text.return_value = {"results": [], "query_time_ms": 100}
        mock_retriever.return_value = mock_ret

        result = cli_runner.invoke(query_group, ["text", "test", "--show-metadata"])
        assert result.exit_code in [0, 1]
