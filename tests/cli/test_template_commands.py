"""Tests for template CLI commands.

v0.3.11: Test template command integration.
"""

import tempfile
from pathlib import Path

import pytest
from click.testing import CliRunner

from src.cli.commands.template import template


class TestTemplateCommands:
    """Test template CLI commands."""

    @pytest.fixture
    def runner(self):
        """Create CLI runner."""
        return CliRunner()

    @pytest.fixture
    def temp_template(self, tmp_path):
        """Create temporary template file."""
        template_file = tmp_path / "test.j2"
        template_file.write_text("Hello {{ name }}!")
        return template_file

    def test_render_basic(self, runner, temp_template):
        """Test basic template rendering."""
        result = runner.invoke(
            template,
            ["render", str(temp_template), "-v", "name=World"],
        )

        assert result.exit_code == 0
        assert "Hello World!" in result.output

    def test_render_with_output_file(self, runner, temp_template, tmp_path):
        """Test rendering to output file."""
        output_file = tmp_path / "output.txt"

        result = runner.invoke(
            template,
            ["render", str(temp_template), "-v", "name=Test", "-o", str(output_file)],
        )

        assert result.exit_code == 0
        assert output_file.exists()
        assert output_file.read_text() == "Hello Test!"

    def test_render_invalid_variable_format(self, runner, temp_template):
        """Test rendering with invalid variable format."""
        result = runner.invoke(
            template,
            ["render", str(temp_template), "-v", "invalid"],
        )

        assert result.exit_code != 0
        assert "Invalid variable format" in result.output

    def test_validate_valid_template(self, runner, temp_template):
        """Test validating valid template."""
        result = runner.invoke(
            template,
            ["validate", str(temp_template)],
        )

        assert result.exit_code == 0
        assert "valid" in result.output.lower()

    def test_validate_invalid_template(self, runner, tmp_path):
        """Test validating invalid template."""
        invalid_template = tmp_path / "invalid.j2"
        invalid_template.write_text("{{ unclosed")

        result = runner.invoke(
            template,
            ["validate", str(invalid_template)],
        )

        assert result.exit_code != 0
        assert "error" in result.output.lower()

    def test_list_templates(self, runner, tmp_path):
        """Test listing templates."""
        # Create some templates
        (tmp_path / "template1.j2").write_text("Template 1")
        (tmp_path / "template2.j2").write_text("Template 2")

        result = runner.invoke(
            template,
            ["list", "-d", str(tmp_path)],
        )

        assert result.exit_code == 0
        assert "template1.j2" in result.output
        assert "template2.j2" in result.output

    def test_list_templates_empty(self, runner, tmp_path):
        """Test listing templates in empty directory."""
        result = runner.invoke(
            template,
            ["list", "-d", str(tmp_path)],
        )

        assert result.exit_code == 0
        assert "No templates found" in result.output

    def test_show_template(self, runner, temp_template):
        """Test showing template contents."""
        result = runner.invoke(
            template,
            ["show", str(temp_template)],
        )

        assert result.exit_code == 0
        assert "Hello {{ name }}!" in result.output

    def test_show_template_no_highlight(self, runner, temp_template):
        """Test showing template without syntax highlighting."""
        result = runner.invoke(
            template,
            ["show", str(temp_template), "--no-syntax-highlight"],
        )

        assert result.exit_code == 0
        assert "Hello {{ name }}!" in result.output
