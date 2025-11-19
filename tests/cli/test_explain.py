"""Tests for explain commands."""

import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest
import yaml
from click.testing import CliRunner

from src.cli.commands.explain import explain
from src.config.config_manager import RaggedConfig


@pytest.fixture
def cli_runner():
    """Create CLI runner for testing."""
    return CliRunner()


@pytest.fixture
def test_config_file():
    """Create a temporary config file for testing."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yml", delete=False) as f:
        config = {
            "retrieval_method": "hybrid",
            "top_k": 5,
            "enable_reranking": True,
            "persona": "balanced",
        }
        yaml.dump(config, f)
        yield Path(f.name)
    Path(f.name).unlink()


class TestExplainQueryCommand:
    """Test explain query command."""

    def test_explain_query_help(self, cli_runner: CliRunner):
        """Test help text for explain query."""
        result = cli_runner.invoke(explain, ["query", "--help"])
        assert result.exit_code == 0
        assert "Explain what will happen" in result.output

    def test_explain_query_basic(self, cli_runner: CliRunner):
        """Test basic query explanation."""
        result = cli_runner.invoke(
            explain, ["query", "What is machine learning?"]
        )

        assert result.exit_code == 0
        assert "Query Pipeline Explanation" in result.output
        assert "What is machine learning?" in result.output

        # Should show all pipeline stages
        assert "1. Retrieval" in result.output
        assert "2. Query Processing" in result.output
        assert "3. Reranking" in result.output
        assert "4. Generation" in result.output
        assert "5. Quality Assessment" in result.output
        assert "Expected Performance" in result.output

    def test_explain_query_shows_retrieval_config(self, cli_runner: CliRunner):
        """Test that retrieval configuration is displayed."""
        result = cli_runner.invoke(
            explain, ["query", "test query"]
        )

        assert result.exit_code == 0
        assert "Method:" in result.output
        assert "Top-K:" in result.output

    def test_explain_query_with_persona(self, cli_runner: CliRunner):
        """Test query explanation with persona override."""
        result = cli_runner.invoke(
            explain, ["query", "test query", "--persona", "accuracy"]
        )

        assert result.exit_code == 0
        assert "Applied persona: accuracy" in result.output
        assert "Query Pipeline Explanation" in result.output

    def test_explain_query_with_speed_persona(self, cli_runner: CliRunner):
        """Test query explanation with speed persona."""
        result = cli_runner.invoke(
            explain, ["query", "test query", "--persona", "speed"]
        )

        assert result.exit_code == 0
        assert "Applied persona: speed" in result.output
        # Speed persona should show its characteristics
        assert "Very Fast" in result.output or "Fastest" in result.output

    def test_explain_query_with_research_persona(self, cli_runner: CliRunner):
        """Test query explanation with research persona."""
        result = cli_runner.invoke(
            explain, ["query", "test query", "--persona", "research"]
        )

        assert result.exit_code == 0
        assert "Applied persona: research" in result.output
        assert "Slowest" in result.output or "Comprehensive" in result.output

    def test_explain_query_shows_query_processing(self, cli_runner: CliRunner):
        """Test that query processing features are shown."""
        result = cli_runner.invoke(
            explain, ["query", "test query"]
        )

        assert result.exit_code == 0
        assert "Query Processing" in result.output

    def test_explain_query_shows_reranking(self, cli_runner: CliRunner):
        """Test that reranking configuration is shown."""
        result = cli_runner.invoke(
            explain, ["query", "test query"]
        )

        assert result.exit_code == 0
        assert "Reranking" in result.output

    def test_explain_query_shows_generation_config(self, cli_runner: CliRunner):
        """Test that generation configuration is shown."""
        result = cli_runner.invoke(
            explain, ["query", "test query"]
        )

        assert result.exit_code == 0
        assert "Generation" in result.output
        assert "LLM:" in result.output
        assert "Temperature:" in result.output

    def test_explain_query_shows_confidence_threshold(self, cli_runner: CliRunner):
        """Test that confidence threshold is shown."""
        result = cli_runner.invoke(
            explain, ["query", "test query"]
        )

        assert result.exit_code == 0
        assert "Quality Assessment" in result.output
        assert "Confidence threshold:" in result.output

    def test_explain_query_shows_performance_expectations(self, cli_runner: CliRunner):
        """Test that performance expectations are shown."""
        result = cli_runner.invoke(
            explain, ["query", "test query"]
        )

        assert result.exit_code == 0
        assert "Expected Performance" in result.output
        assert "Speed:" in result.output
        assert "Quality:" in result.output

    def test_explain_query_invalid_persona(self, cli_runner: CliRunner):
        """Test query explanation with invalid persona."""
        result = cli_runner.invoke(
            explain, ["query", "test query", "--persona", "invalid"]
        )

        assert result.exit_code != 0
        assert "Error:" in result.output or "Unknown persona" in result.output

    def test_explain_query_with_hybrid_retrieval(self, cli_runner: CliRunner):
        """Test that hybrid retrieval shows weights."""
        with patch("src.cli.commands.explain.RaggedConfig.load") as mock_load:
            config = RaggedConfig()
            config.retrieval_method = "hybrid"
            config.bm25_weight = 0.3
            config.vector_weight = 0.7
            mock_load.return_value = config

            result = cli_runner.invoke(explain, ["query", "test query"])

            assert result.exit_code == 0
            assert "Weights:" in result.output
            assert "BM25" in result.output
            assert "Vector" in result.output

    def test_explain_query_accuracy_persona_shows_advanced_features(self, cli_runner: CliRunner):
        """Test that accuracy persona shows enabled advanced features."""
        result = cli_runner.invoke(
            explain, ["query", "test query", "--persona", "accuracy"]
        )

        assert result.exit_code == 0
        assert "Query decomposition enabled" in result.output or "✓" in result.output


class TestExplainConfigCommand:
    """Test explain config command."""

    def test_explain_config_help(self, cli_runner: CliRunner):
        """Test help text for explain config."""
        result = cli_runner.invoke(explain, ["config", "--help"])
        assert result.exit_code == 0
        assert "Explain current configuration" in result.output

    def test_explain_config_basic(self, cli_runner: CliRunner):
        """Test basic config explanation."""
        result = cli_runner.invoke(explain, ["config"])

        assert result.exit_code == 0
        assert "Current Configuration" in result.output
        assert "Active Persona:" in result.output

    def test_explain_config_shows_retrieval_settings(self, cli_runner: CliRunner):
        """Test that retrieval settings are displayed."""
        result = cli_runner.invoke(explain, ["config"])

        assert result.exit_code == 0
        assert "Retrieval Settings" in result.output
        assert "retrieval_method:" in result.output
        assert "top_k:" in result.output
        assert "bm25_weight:" in result.output
        assert "vector_weight:" in result.output

    def test_explain_config_shows_advanced_features(self, cli_runner: CliRunner):
        """Test that advanced features are displayed."""
        result = cli_runner.invoke(explain, ["config"])

        assert result.exit_code == 0
        assert "Advanced Features" in result.output
        assert "enable_reranking:" in result.output
        assert "enable_query_decomposition:" in result.output
        assert "enable_hyde:" in result.output
        assert "enable_compression:" in result.output

    def test_explain_config_shows_generation_settings(self, cli_runner: CliRunner):
        """Test that generation settings are displayed."""
        result = cli_runner.invoke(explain, ["config"])

        assert result.exit_code == 0
        assert "Generation Settings" in result.output
        assert "llm_model:" in result.output
        assert "temperature:" in result.output
        assert "max_tokens:" in result.output

    def test_explain_config_shows_quality_thresholds(self, cli_runner: CliRunner):
        """Test that quality thresholds are displayed."""
        result = cli_runner.invoke(explain, ["config"])

        assert result.exit_code == 0
        assert "Quality Thresholds" in result.output
        assert "confidence_threshold:" in result.output

    def test_explain_config_shows_configuration_sources(self, cli_runner: CliRunner):
        """Test that configuration sources are mentioned."""
        result = cli_runner.invoke(explain, ["config"])

        assert result.exit_code == 0
        assert "Configuration loaded from:" in result.output
        assert "config.yml" in result.output
        assert "Environment variables" in result.output

    def test_explain_config_with_custom_config(self, cli_runner: CliRunner):
        """Test config explanation with custom settings."""
        with patch("src.cli.commands.explain.RaggedConfig.load") as mock_load:
            config = RaggedConfig()
            config.persona = "accuracy"
            config.retrieval_method = "vector"
            config.top_k = 10
            config.enable_reranking = False
            mock_load.return_value = config

            result = cli_runner.invoke(explain, ["config"])

            assert result.exit_code == 0
            assert "accuracy" in result.output
            assert "vector" in result.output
            assert "10" in result.output


class TestExplainCommandGroup:
    """Test explain command group."""

    def test_explain_help(self, cli_runner: CliRunner):
        """Test help text for explain group."""
        result = cli_runner.invoke(explain, ["--help"])
        assert result.exit_code == 0
        assert "explain" in result.output.lower()

    def test_explain_lists_subcommands(self, cli_runner: CliRunner):
        """Test that subcommands are listed."""
        result = cli_runner.invoke(explain, ["--help"])
        assert result.exit_code == 0
        assert "query" in result.output
        assert "config" in result.output

    def test_explain_no_subcommand_shows_help(self, cli_runner: CliRunner):
        """Test that running explain without subcommand shows help."""
        result = cli_runner.invoke(explain)
        # Should show help or error
        assert "query" in result.output or "Usage" in result.output
