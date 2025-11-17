"""Output formatters for CLI commands.

Provides consistent formatting across different output formats (JSON, CSV, table, markdown).
"""

import csv
import io
import json
from typing import Any, Dict, List, Literal, Optional, Union

from rich.console import Console
from rich.table import Table

FormatType = Literal["json", "csv", "table", "markdown", "yaml"]


class OutputFormatter:
    """Unified output formatter for CLI commands."""

    def __init__(self, console: Optional[Console] = None):
        """Initialize formatter with optional console."""
        self.console = console or Console()

    def format(
        self,
        data: Union[List[Dict[str, Any]], Dict[str, Any]],
        format_type: FormatType = "table",
        columns: Optional[List[str]] = None,
        title: Optional[str] = None,
    ) -> str:
        """Format data according to specified format type.

        Args:
            data: Data to format (list of dicts or single dict)
            format_type: Output format (json, csv, table, markdown, yaml)
            columns: Specific columns to include (None = all)
            title: Optional title for table/markdown formats

        Returns:
            Formatted string output
        """
        # Normalize to list of dicts
        if isinstance(data, dict):
            data = [data]

        if not data:
            return self._format_empty(format_type)

        # Filter columns if specified
        if columns:
            data = [{k: v for k, v in item.items() if k in columns} for item in data]

        # Format based on type
        if format_type == "json":
            return self._format_json(data)
        elif format_type == "csv":
            return self._format_csv(data)
        elif format_type == "markdown":
            return self._format_markdown(data, title)
        elif format_type == "yaml":
            return self._format_yaml(data)
        else:  # table
            return self._format_table(data, title)

    def _format_empty(self, format_type: FormatType) -> str:
        """Format empty result based on format type."""
        if format_type == "json":
            return "[]"
        elif format_type == "csv":
            return ""
        elif format_type == "yaml":
            return "[]"
        else:
            return "No results found."

    def _format_json(self, data: List[Dict[str, Any]]) -> str:
        """Format as JSON."""
        return json.dumps(data, indent=2, default=str)

    def _format_csv(self, data: List[Dict[str, Any]]) -> str:
        """Format as CSV."""
        if not data:
            return ""

        output = io.StringIO()
        # Get all unique keys from all dicts
        fieldnames = list(dict.fromkeys(k for item in data for k in item.keys()))

        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)

        return output.getvalue()

    def _format_table(self, data: List[Dict[str, Any]], title: Optional[str] = None) -> str:
        """Format as Rich table."""
        if not data:
            return "No results found."

        # Create table
        table = Table(title=title, show_header=True, header_style="bold cyan")

        # Add columns from first item
        for key in data[0].keys():
            table.add_column(str(key).replace("_", " ").title())

        # Add rows
        for item in data:
            table.add_row(*[str(v) for v in item.values()])

        # Render to string
        with self.console.capture() as capture:
            self.console.print(table)

        return capture.get()

    def _format_markdown(self, data: List[Dict[str, Any]], title: Optional[str] = None) -> str:
        """Format as Markdown table."""
        if not data:
            return "_No results found._"

        lines = []

        # Add title if provided
        if title:
            lines.append(f"## {title}")
            lines.append("")

        # Get column names
        columns = list(data[0].keys())

        # Create header
        header = "| " + " | ".join(str(col).replace("_", " ").title() for col in columns) + " |"
        lines.append(header)

        # Create separator
        separator = "| " + " | ".join("---" for _ in columns) + " |"
        lines.append(separator)

        # Add data rows
        for item in data:
            row = "| " + " | ".join(str(item.get(col, "")) for col in columns) + " |"
            lines.append(row)

        return "\n".join(lines)

    def _format_yaml(self, data: List[Dict[str, Any]]) -> str:
        """Format as YAML."""
        try:
            import yaml

            return yaml.dump(data, default_flow_style=False, allow_unicode=True)
        except ImportError:
            # Fallback to simple YAML-like format
            lines = []
            for i, item in enumerate(data):
                if i > 0:
                    lines.append("")
                lines.append(f"- item_{i}:")
                for key, value in item.items():
                    lines.append(f"    {key}: {value}")
            return "\n".join(lines)


def format_output(
    data: Union[List[Dict[str, Any]], Dict[str, Any]],
    format_type: FormatType = "table",
    columns: Optional[List[str]] = None,
    title: Optional[str] = None,
    console: Optional[Console] = None,
) -> str:
    """Convenience function for formatting output.

    Args:
        data: Data to format
        format_type: Output format
        columns: Specific columns to include
        title: Optional title
        console: Optional Rich console

    Returns:
        Formatted string
    """
    formatter = OutputFormatter(console)
    return formatter.format(data, format_type, columns, title)


def print_formatted(
    data: Union[List[Dict[str, Any]], Dict[str, Any]],
    format_type: FormatType = "table",
    columns: Optional[List[str]] = None,
    title: Optional[str] = None,
    console: Optional[Console] = None,
) -> None:
    """Format and print data to console.

    Args:
        data: Data to format
        format_type: Output format
        columns: Specific columns to include
        title: Optional title
        console: Optional Rich console
    """
    output = format_output(data, format_type, columns, title, console)
    if console:
        if format_type == "table":
            # Already rendered with Rich, just print
            print(output, end="")
        else:
            console.print(output)
    else:
        print(output)


# Format type choices for Click options
FORMAT_CHOICES = ["json", "csv", "table", "markdown", "yaml"]


def add_format_option(func: Any) -> Any:
    """Decorator to add --format option to Click commands.

    Usage:
        @click.command()
        @add_format_option
        def my_command(format: str):
            # format will be available as parameter
            pass
    """
    import click

    return click.option(
        "--format",
        "-f",
        "format",
        type=click.Choice(FORMAT_CHOICES, case_sensitive=False),
        default="table",
        help="Output format",
    )(func)
