"""
Jinja2-based template engine for RAG workflows.

v0.3.10: Repeatable query templates with custom functions.
"""

from pathlib import Path
from typing import Any, Callable, Dict, Optional

try:
    import jinja2
    from jinja2 import Environment, FileSystemLoader, TemplateSyntaxError
except ImportError:
    raise ImportError(
        "jinja2 is required for template functionality. "
        "Install with: pip install jinja2>=3.1.0"
    )

from src.utils.logging import get_logger

logger = get_logger(__name__)


class TemplateError(Exception):
    """Template-related errors."""

    pass


class TemplateEngine:
    """
    Jinja2-based template engine for RAG workflows.

    Provides template rendering with custom functions for querying,
    retrieval, and summarisation.

    Example:
        >>> engine = TemplateEngine(query_fn=my_query_function)
        >>> template = "Question: {{ question }}\\nAnswer: {{ query(question) }}"
        >>> result = engine.render_string(template, {"question": "What is RAG?"})
    """

    def __init__(
        self,
        query_fn: Optional[Callable] = None,
        retrieve_fn: Optional[Callable] = None,
        summarise_fn: Optional[Callable] = None,
        template_dir: Optional[Path] = None,
        autoescape: bool = False,
    ):
        """
        Initialise template engine.

        Args:
            query_fn: Function for executing queries (signature: query(question, **kwargs) -> str)
            retrieve_fn: Function for retrieving chunks (signature: retrieve(query, **kwargs) -> List)
            summarise_fn: Function for summarisation (signature: summarise(text, **kwargs) -> str)
            template_dir: Directory containing templates (None = current directory)
            autoescape: Enable HTML autoescaping (default: False for plain text)
        """
        self.query_fn = query_fn
        self.retrieve_fn = retrieve_fn
        self.summarise_fn = summarise_fn
        self.template_dir = template_dir or Path(".")

        # Create Jinja2 environment
        self.env = self._create_environment(autoescape=autoescape)

        logger.info(f"TemplateEngine initialised with template_dir={template_dir}")

    def _create_environment(self, autoescape: bool = False) -> Environment:
        """
        Create Jinja2 environment with custom functions.

        Args:
            autoescape: Enable HTML autoescaping

        Returns:
            Configured Jinja2 environment
        """
        # File system loader for templates
        loader = FileSystemLoader(str(self.template_dir))

        # Create environment
        env = Environment(
            loader=loader,
            autoescape=autoescape,
            trim_blocks=True,
            lstrip_blocks=True,
        )

        # Add custom global functions (always add, even if not configured)
        env.globals["query"] = self._wrap_query_function()
        env.globals["retrieve"] = self._wrap_retrieve_function()
        env.globals["summarise"] = self._wrap_summarise_function()

        # Add custom filters
        env.filters["truncate_words"] = self._truncate_words_filter
        env.filters["chunk_text"] = self._chunk_text_filter

        return env

    def _wrap_query_function(self) -> Callable:
        """
        Wrap query function for template context.

        Returns:
            Wrapped query function
        """

        def query(question: str, **kwargs) -> str:
            """Execute query within template."""
            try:
                if not self.query_fn:
                    raise TemplateError("Query function not configured")

                logger.debug(f"Template query: {question[:50]}...")
                result = self.query_fn(question, **kwargs)
                return str(result)
            except Exception as e:
                logger.error(f"Query function error: {e}")
                raise TemplateError(f"Query failed: {e}") from e

        return query

    def _wrap_retrieve_function(self) -> Callable:
        """
        Wrap retrieve function for template context.

        Returns:
            Wrapped retrieve function
        """

        def retrieve(query: str, **kwargs) -> list:
            """Retrieve chunks within template."""
            try:
                if not self.retrieve_fn:
                    raise TemplateError("Retrieve function not configured")

                logger.debug(f"Template retrieve: {query[:50]}...")
                result = self.retrieve_fn(query, **kwargs)
                return result
            except Exception as e:
                logger.error(f"Retrieve function error: {e}")
                raise TemplateError(f"Retrieve failed: {e}") from e

        return retrieve

    def _wrap_summarise_function(self) -> Callable:
        """
        Wrap summarise function for template context.

        Returns:
            Wrapped summarise function
        """

        def summarise(text: str, **kwargs) -> str:
            """Summarise text within template."""
            try:
                if not self.summarise_fn:
                    raise TemplateError("Summarise function not configured")

                logger.debug(f"Template summarise: {text[:50]}...")
                result = self.summarise_fn(text, **kwargs)
                return str(result)
            except Exception as e:
                logger.error(f"Summarise function error: {e}")
                raise TemplateError(f"Summarise failed: {e}") from e

        return summarise

    def _truncate_words_filter(self, text: str, length: int = 50) -> str:
        """
        Truncate text to specified word count.

        Args:
            text: Text to truncate
            length: Maximum number of words

        Returns:
            Truncated text with ellipsis if needed
        """
        words = text.split()
        if len(words) <= length:
            return text
        return " ".join(words[:length]) + "..."

    def _chunk_text_filter(self, text: str, chunk_size: int = 500) -> list:
        """
        Split text into chunks.

        Args:
            text: Text to chunk
            chunk_size: Maximum characters per chunk

        Returns:
            List of text chunks
        """
        chunks = []
        for i in range(0, len(text), chunk_size):
            chunks.append(text[i : i + chunk_size])
        return chunks

    def render_string(self, template_string: str, variables: Dict[str, Any]) -> str:
        """
        Render template from string.

        Args:
            template_string: Template content
            variables: Template variables

        Returns:
            Rendered template

        Raises:
            TemplateError: If template rendering fails
        """
        try:
            template = self.env.from_string(template_string)
            result = template.render(**variables)
            logger.debug(f"Rendered template: {len(result)} characters")
            return result
        except TemplateSyntaxError as e:
            logger.error(f"Template syntax error: {e}")
            raise TemplateError(f"Template syntax error: {e}") from e
        except Exception as e:
            logger.exception(f"Template rendering error: {e}")
            raise TemplateError(f"Template rendering failed: {e}") from e

    def render_file(self, template_path: Path, variables: Dict[str, Any]) -> str:
        """
        Render template from file.

        Args:
            template_path: Path to template file (relative to template_dir)
            variables: Template variables

        Returns:
            Rendered template

        Raises:
            TemplateError: If template file not found or rendering fails
        """
        try:
            # Get template relative to template_dir
            if template_path.is_absolute():
                # Make relative to template_dir
                try:
                    rel_path = template_path.relative_to(self.template_dir)
                except ValueError:
                    raise TemplateError(
                        f"Template path {template_path} is not within template_dir {self.template_dir}"
                    )
            else:
                rel_path = template_path

            template = self.env.get_template(str(rel_path))
            result = template.render(**variables)
            logger.info(f"Rendered template file: {rel_path}")
            return result
        except jinja2.TemplateNotFound as e:
            logger.error(f"Template file not found: {e}")
            raise TemplateError(f"Template file not found: {e}") from e
        except TemplateSyntaxError as e:
            logger.error(f"Template syntax error in {template_path}: {e}")
            raise TemplateError(f"Template syntax error: {e}") from e
        except Exception as e:
            logger.exception(f"Template rendering error: {e}")
            raise TemplateError(f"Template rendering failed: {e}") from e

    def validate_template(self, template_string: str) -> Dict[str, Any]:
        """
        Validate template syntax.

        Args:
            template_string: Template content to validate

        Returns:
            Validation result with 'valid' boolean and optional 'error' message
        """
        try:
            self.env.from_string(template_string)
            logger.debug("Template validation passed")
            return {"valid": True}
        except TemplateSyntaxError as e:
            logger.warning(f"Template validation failed: {e}")
            return {"valid": False, "error": str(e), "line": e.lineno}
        except Exception as e:
            logger.error(f"Template validation error: {e}")
            return {"valid": False, "error": str(e)}

    def list_templates(self) -> list:
        """
        List available templates in template_dir.

        Returns:
            List of template file paths
        """
        try:
            templates = []
            for path in self.template_dir.rglob("*.j2"):
                rel_path = path.relative_to(self.template_dir)
                templates.append(rel_path)

            logger.info(f"Found {len(templates)} templates")
            return sorted(templates)
        except Exception as e:
            logger.exception(f"Error listing templates: {e}")
            return []


# Convenience function
def create_template_engine(
    query_fn: Optional[Callable] = None,
    retrieve_fn: Optional[Callable] = None,
    template_dir: Optional[Path] = None,
) -> TemplateEngine:
    """
    Create a template engine.

    Args:
        query_fn: Function for executing queries
        retrieve_fn: Function for retrieving chunks
        template_dir: Directory containing templates

    Returns:
        TemplateEngine instance

    Example:
        >>> def my_query(question, **kwargs):
        ...     return "This is the answer"
        >>> engine = create_template_engine(query_fn=my_query)
        >>> result = engine.render_string("Q: {{ query('test') }}", {})
    """
    return TemplateEngine(
        query_fn=query_fn, retrieve_fn=retrieve_fn, template_dir=template_dir
    )
