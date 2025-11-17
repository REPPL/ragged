"""Document management commands for ragged CLI."""

import sys

import click

from src.cli.common import console, TableType
from src.cli.formatters import FORMAT_CHOICES, print_formatted
from src.utils.logging import get_logger

logger = get_logger(__name__)


@click.command("list")
@click.option(
    "--format",
    "-f",
    "output_format",
    type=click.Choice(FORMAT_CHOICES, case_sensitive=False),
    default="table",
    help="Output format (table, json, csv, markdown, yaml)",
)
def list_docs(output_format: str) -> None:
    """List all ingested documents.

    \b
    Examples:
        ragged list                    # Show as table
        ragged list --format json      # Export as JSON
        ragged list --format csv       # Export as CSV
        ragged list --format markdown  # Export as Markdown
    """
    from src.storage.vector_store import VectorStore

    try:
        vector_store = VectorStore()
        info = vector_store.get_collection_info()

        # Format data for output
        data = {
            "Collection Name": info["name"],
            "Total Chunks": info["count"],
            "Note": "Document-level listing will be added in v0.2",
        }

        # Print in requested format
        print_formatted([data], format_type=output_format, title="Vector Store Information", console=console)  # type: ignore

    except Exception as e:
        console.print(f"[bold red]✗[/bold red] Failed to list documents: {e}")
        logger.error(f"List failed: {e}", exc_info=True)
        sys.exit(1)


@click.command()
@click.option("--force", "-f", is_flag=True, help="Skip confirmation")
def clear(force: bool) -> None:
    """Clear all ingested documents from the database."""
    from src.storage.vector_store import VectorStore

    try:
        vector_store = VectorStore()
        count = vector_store.count()

        if count == 0:
            console.print("[yellow]No documents to clear.[/yellow]")
            return

        if not force:
            if not click.confirm(f"Are you sure you want to clear {count} chunks?"):
                console.print("[yellow]Cancelled.[/yellow]")
                return

        vector_store.clear()
        console.print(f"[bold green]✓[/bold green] Cleared {count} chunks from the database")

    except Exception as e:
        console.print(f"[bold red]✗[/bold red] Failed to clear database: {e}")
        logger.error(f"Clear failed: {e}", exc_info=True)
        sys.exit(1)
