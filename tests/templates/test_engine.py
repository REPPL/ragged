"""Tests for template engine.

v0.3.10: Test Jinja2-based query templating.
"""

import tempfile
from pathlib import Path

import pytest

from src.templates.engine import (
    TemplateEngine,
    TemplateError,
    create_template_engine,
)


class TestTemplateEngineInit:
    """Test TemplateEngine initialisation."""

    def test_init_minimal(self):
        """Test initialisation with minimal parameters."""
        engine = TemplateEngine()

        assert engine.query_fn is None
        assert engine.retrieve_fn is None
        assert engine.summarise_fn is None
        assert engine.template_dir == Path(".")

    def test_init_with_functions(self):
        """Test initialisation with custom functions."""

        def mock_query(question, **kwargs):
            return "answer"

        def mock_retrieve(query, **kwargs):
            return ["chunk1", "chunk2"]

        engine = TemplateEngine(query_fn=mock_query, retrieve_fn=mock_retrieve)

        assert engine.query_fn is mock_query
        assert engine.retrieve_fn is mock_retrieve

    def test_init_with_template_dir(self, tmp_path):
        """Test initialisation with custom template directory."""
        template_dir = tmp_path / "templates"
        template_dir.mkdir()

        engine = TemplateEngine(template_dir=template_dir)

        assert engine.template_dir == template_dir


class TestTemplateRenderingString:
    """Test template rendering from strings."""

    def test_render_simple_string(self):
        """Test rendering simple template."""
        engine = TemplateEngine()

        template = "Hello {{ name }}!"
        result = engine.render_string(template, {"name": "World"})

        assert result == "Hello World!"

    def test_render_with_loop(self):
        """Test rendering template with loop."""
        engine = TemplateEngine()

        template = """
{% for item in items %}
- {{ item }}
{% endfor %}
""".strip()

        result = engine.render_string(template, {"items": ["apple", "banana", "cherry"]})

        assert "- apple" in result
        assert "- banana" in result
        assert "- cherry" in result

    def test_render_with_conditional(self):
        """Test rendering template with conditional."""
        engine = TemplateEngine()

        template = """
{% if show_greeting %}
Hello {{ name }}!
{% else %}
Goodbye {{ name }}!
{% endif %}
""".strip()

        result1 = engine.render_string(template, {"show_greeting": True, "name": "Alice"})
        result2 = engine.render_string(template, {"show_greeting": False, "name": "Bob"})

        assert "Hello Alice!" in result1
        assert "Goodbye Bob!" in result2

    def test_render_syntax_error(self):
        """Test rendering with syntax error."""
        engine = TemplateEngine()

        template = "{{ unclosed"

        with pytest.raises(TemplateError, match="syntax error"):
            engine.render_string(template, {})


class TestQueryFunction:
    """Test query function in templates."""

    def test_query_function_basic(self):
        """Test basic query function."""

        def mock_query(question, **kwargs):
            return f"Answer to: {question}"

        engine = TemplateEngine(query_fn=mock_query)

        template = "Q: {{ question }}\nA: {{ query(question) }}"
        result = engine.render_string(template, {"question": "What is RAG?"})

        assert "Q: What is RAG?" in result
        assert "A: Answer to: What is RAG?" in result

    def test_query_function_with_kwargs(self):
        """Test query function with keyword arguments."""

        def mock_query(question, **kwargs):
            document = kwargs.get("document", "unknown")
            return f"Answer from {document}: {question}"

        engine = TemplateEngine(query_fn=mock_query)

        template = "{{ query('What?', document='paper.pdf') }}"
        result = engine.render_string(template, {})

        assert "Answer from paper.pdf" in result

    def test_query_function_not_configured(self):
        """Test query function when not configured."""
        engine = TemplateEngine()

        template = "{{ query('test') }}"

        with pytest.raises(TemplateError, match="not configured"):
            engine.render_string(template, {})

    def test_query_function_error(self):
        """Test query function error handling."""

        def mock_query(question, **kwargs):
            raise ValueError("Query failed")

        engine = TemplateEngine(query_fn=mock_query)

        template = "{{ query('test') }}"

        with pytest.raises(TemplateError, match="Query failed"):
            engine.render_string(template, {})


class TestRetrieveFunction:
    """Test retrieve function in templates."""

    def test_retrieve_function_basic(self):
        """Test basic retrieve function."""

        def mock_retrieve(query, **kwargs):
            return ["chunk1", "chunk2", "chunk3"]

        engine = TemplateEngine(retrieve_fn=mock_retrieve)

        template = """
{% for chunk in retrieve('test query') %}
- {{ chunk }}
{% endfor %}
""".strip()

        result = engine.render_string(template, {})

        assert "- chunk1" in result
        assert "- chunk2" in result
        assert "- chunk3" in result

    def test_retrieve_function_not_configured(self):
        """Test retrieve function when not configured."""
        engine = TemplateEngine()

        template = "{{ retrieve('test') }}"

        with pytest.raises(TemplateError, match="not configured"):
            engine.render_string(template, {})


class TestSummariseFunction:
    """Test summarise function in templates."""

    def test_summarise_function_basic(self):
        """Test basic summarise function."""

        def mock_summarise(text, **kwargs):
            return f"Summary of: {text[:20]}..."

        engine = TemplateEngine(summarise_fn=mock_summarise)

        template = "{{ summarise('This is a long text that needs summarising') }}"
        result = engine.render_string(template, {})

        assert "Summary of: This is a long text" in result

    def test_summarise_function_not_configured(self):
        """Test summarise function when not configured."""
        engine = TemplateEngine()

        template = "{{ summarise('test') }}"

        with pytest.raises(TemplateError, match="not configured"):
            engine.render_string(template, {})


class TestCustomFilters:
    """Test custom Jinja2 filters."""

    def test_truncate_words_filter(self):
        """Test truncate_words filter."""
        engine = TemplateEngine()

        template = "{{ text | truncate_words(3) }}"
        result = engine.render_string(
            template, {"text": "This is a long sentence with many words"}
        )

        assert result == "This is a..."

    def test_truncate_words_no_truncation(self):
        """Test truncate_words when text is short."""
        engine = TemplateEngine()

        template = "{{ text | truncate_words(10) }}"
        result = engine.render_string(template, {"text": "Short text"})

        assert result == "Short text"

    def test_chunk_text_filter(self):
        """Test chunk_text filter."""
        engine = TemplateEngine()

        template = """
{% for chunk in text | chunk_text(10) %}
{{ loop.index }}: {{ chunk }}
{% endfor %}
""".strip()

        result = engine.render_string(
            template, {"text": "This is a test text for chunking"}
        )

        assert "1: This is a " in result
        assert "2: test text " in result


class TestTemplateValidation:
    """Test template validation."""

    def test_validate_valid_template(self):
        """Test validation of valid template."""
        engine = TemplateEngine()

        result = engine.validate_template("Hello {{ name }}!")

        assert result["valid"] is True
        assert "error" not in result

    def test_validate_syntax_error(self):
        """Test validation of template with syntax error."""
        engine = TemplateEngine()

        result = engine.validate_template("{{ unclosed")

        assert result["valid"] is False
        assert "error" in result
        assert "line" in result


class TestFileTemplates:
    """Test template rendering from files."""

    @pytest.fixture
    def template_dir(self, tmp_path):
        """Create temporary template directory."""
        template_dir = tmp_path / "templates"
        template_dir.mkdir()
        return template_dir

    def test_render_file_basic(self, template_dir):
        """Test rendering template from file."""
        template_file = template_dir / "test.j2"
        template_file.write_text("Hello {{ name }}!")

        engine = TemplateEngine(template_dir=template_dir)
        result = engine.render_file(Path("test.j2"), {"name": "World"})

        assert result == "Hello World!"

    def test_render_file_not_found(self, template_dir):
        """Test rendering non-existent template file."""
        engine = TemplateEngine(template_dir=template_dir)

        with pytest.raises(TemplateError, match="not found"):
            engine.render_file(Path("nonexistent.j2"), {})

    def test_render_file_absolute_path(self, template_dir):
        """Test rendering with absolute path."""
        template_file = template_dir / "test.j2"
        template_file.write_text("Hello {{ name }}!")

        engine = TemplateEngine(template_dir=template_dir)
        result = engine.render_file(template_file, {"name": "World"})

        assert result == "Hello World!"

    def test_render_file_outside_template_dir(self, tmp_path):
        """Test rendering file outside template directory."""
        template_dir = tmp_path / "templates"
        template_dir.mkdir()

        other_dir = tmp_path / "other"
        other_dir.mkdir()
        template_file = other_dir / "test.j2"
        template_file.write_text("Test")

        engine = TemplateEngine(template_dir=template_dir)

        with pytest.raises(TemplateError, match="not within template_dir"):
            engine.render_file(template_file, {})


class TestListTemplates:
    """Test listing available templates."""

    @pytest.fixture
    def template_dir_with_files(self, tmp_path):
        """Create template directory with multiple files."""
        template_dir = tmp_path / "templates"
        template_dir.mkdir()

        # Create some templates
        (template_dir / "template1.j2").write_text("Template 1")
        (template_dir / "template2.j2").write_text("Template 2")

        # Create subdirectory with template
        subdir = template_dir / "subdir"
        subdir.mkdir()
        (subdir / "template3.j2").write_text("Template 3")

        return template_dir

    def test_list_templates(self, template_dir_with_files):
        """Test listing templates."""
        engine = TemplateEngine(template_dir=template_dir_with_files)

        templates = engine.list_templates()

        assert len(templates) == 3
        assert Path("template1.j2") in templates
        assert Path("template2.j2") in templates
        assert Path("subdir/template3.j2") in templates

    def test_list_templates_empty(self, tmp_path):
        """Test listing templates in empty directory."""
        template_dir = tmp_path / "empty"
        template_dir.mkdir()

        engine = TemplateEngine(template_dir=template_dir)

        templates = engine.list_templates()

        assert templates == []


class TestConvenienceFunction:
    """Test convenience function."""

    def test_create_template_engine(self):
        """Test creating template engine with convenience function."""

        def mock_query(question, **kwargs):
            return "answer"

        engine = create_template_engine(query_fn=mock_query)

        assert isinstance(engine, TemplateEngine)
        assert engine.query_fn is mock_query

    def test_create_template_engine_with_template_dir(self, tmp_path):
        """Test creating engine with template directory."""
        engine = create_template_engine(template_dir=tmp_path)

        assert engine.template_dir == tmp_path
