"""Tests for CLI evaluate command.

Note: Full integration tests are covered by manual testing.
These tests focus on error handling and validation logic.
"""

import json
from click.testing import CliRunner

from src.cli.commands.evaluate import evaluate, ragas


class TestEvaluateCommand:
    """Tests for evaluate command group."""

    def test_evaluate_help(self) -> None:
        """Test evaluate command help message."""
        runner = CliRunner()
        result = runner.invoke(evaluate, ["--help"])

        assert result.exit_code == 0
        assert "Evaluate RAG pipeline quality" in result.output
        assert "ragas" in result.output


class TestRagasCommand:
    """Tests for ragas evaluation command."""

    def test_ragas_missing_file(self) -> None:
        """Test error handling for missing test set file."""
        runner = CliRunner()
        result = runner.invoke(ragas, ["nonexistent.json"])

        # Click returns exit code 2 for usage errors
        assert result.exit_code != 0
        assert "does not exist" in result.output.lower() or "not found" in result.output.lower()

    def test_ragas_invalid_json(self) -> None:
        """Test error handling for invalid JSON in test set."""
        runner = CliRunner()
        with runner.isolated_filesystem():
            # Create invalid JSON file
            with open("invalid.json", "w") as f:
                f.write("{ invalid json }")

            result = runner.invoke(ragas, ["invalid.json"])

            assert result.exit_code == 1
            assert "Invalid JSON" in result.output or "error" in result.output.lower()

    def test_ragas_empty_test_set(self) -> None:
        """Test error handling for empty test set."""
        runner = CliRunner()
        with runner.isolated_filesystem():
            # Create empty test set
            with open("empty.json", "w") as f:
                json.dump([], f)

            result = runner.invoke(ragas, ["empty.json"])

            assert result.exit_code == 1
            assert "non-empty" in result.output.lower()

    def test_ragas_missing_question_field(self) -> None:
        """Test validation of test set format."""
        runner = CliRunner()
        with runner.isolated_filesystem():
            # Create test set missing 'question' field
            with open("bad.json", "w") as f:
                json.dump([{"answer": "No question field"}], f)

            result = runner.invoke(ragas, ["bad.json"])

            assert result.exit_code == 1
            assert "missing 'question'" in result.output.lower()

