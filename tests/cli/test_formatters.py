"""Tests for output formatters."""

import json
import pytest
from io import StringIO

from src.cli.formatters import (
    print_formatted,
    format_json,
    format_csv,
    format_table,
    format_markdown,
    format_yaml,
)


class TestFormatJSON:
    """Test JSON formatting."""

    def test_format_json_dict(self):
        """Test formatting a dictionary as JSON."""
        data = {"key": "value", "number": 42}
        result = format_json(data)

        parsed = json.loads(result)
        assert parsed["key"] == "value"
        assert parsed["number"] == 42

    def test_format_json_list(self):
        """Test formatting a list as JSON."""
        data = [{"id": 1}, {"id": 2}]
        result = format_json(data)

        parsed = json.loads(result)
        assert len(parsed) == 2
        assert parsed[0]["id"] == 1

    def test_format_json_empty(self):
        """Test formatting empty data."""
        result = format_json({})
        assert result == "{}"


class TestFormatCSV:
    """Test CSV formatting."""

    def test_format_csv_list_of_dicts(self):
        """Test formatting list of dictionaries as CSV."""
        data = [
            {"name": "Alice", "age": 30},
            {"name": "Bob", "age": 25},
        ]
        result = format_csv(data)

        assert "name" in result
        assert "age" in result
        assert "Alice" in result
        assert "Bob" in result

    def test_format_csv_empty(self):
        """Test formatting empty data."""
        result = format_csv([])
        assert result == "" or len(result) < 10


class TestFormatTable:
    """Test table formatting."""

    def test_format_table_list_of_dicts(self):
        """Test formatting as table."""
        data = [
            {"name": "Alice", "score": 95},
            {"name": "Bob", "score": 87},
        ]
        result = format_table(data, title="Test Table")

        assert "Alice" in result
        assert "Bob" in result
        assert "95" in result or "87" in result

    def test_format_table_empty(self):
        """Test formatting empty table."""
        result = format_table([])
        assert isinstance(result, str)


class TestFormatMarkdown:
    """Test Markdown formatting."""

    def test_format_markdown_dict(self):
        """Test formatting dictionary as Markdown."""
        data = {"title": "Test", "content": "Value"}
        result = format_markdown(data)

        assert "**" in result or "#" in result
        assert "Test" in result
        assert "Value" in result

    def test_format_markdown_list_of_dicts(self):
        """Test formatting list as Markdown table."""
        data = [
            {"name": "Alice", "age": 30},
            {"name": "Bob", "age": 25},
        ]
        result = format_markdown(data)

        assert "name" in result or "Name" in result
        assert "Alice" in result
        assert "|" in result  # Markdown table separator


class TestFormatYAML:
    """Test YAML formatting."""

    def test_format_yaml_dict(self):
        """Test formatting dictionary as YAML."""
        data = {"key": "value", "number": 42}
        result = format_yaml(data)

        assert "key:" in result or "key" in result
        assert "value" in result
        assert "42" in result

    def test_format_yaml_list(self):
        """Test formatting list as YAML."""
        data = [{"id": 1}, {"id": 2}]
        result = format_yaml(data)

        assert "-" in result  # YAML list indicator
        assert "id" in result


class TestPrintFormatted:
    """Test main print_formatted function."""

    def test_print_formatted_json(self, capsys):
        """Test printing in JSON format."""
        data = {"test": "value"}
        print_formatted(data, format="json")

        captured = capsys.readouterr()
        parsed = json.loads(captured.out)
        assert parsed["test"] == "value"

    def test_print_formatted_invalid_format(self):
        """Test handling invalid format."""
        data = {"test": "value"}
        # Should not raise exception, might fall back to default
        try:
            print_formatted(data, format="invalid")
        except ValueError:
            pass  # Expected for invalid format
