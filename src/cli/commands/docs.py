"""Document management commands for ragged CLI."""

import sys

import click

from src.cli.common import console, TableType
from src.utils.logging import get_logger

logger = get_logger(__name__)


@click.command("list")
def list_docs() -> None:
    """List all ingested documents."""
    from src.storage.vector_store import VectorStore

    try:
        vector_store = VectorStore()
        info = vector_store.get_collection_info()

        table = TableType(title="Vector Store Information")
        table.add_column("Property", style="cyan")
        table.add_column("Value", style="magenta")

        table.add_row("Collection Name", info["name"])
        table.add_row("Total Chunks", str(info["count"]))

        console.print(table)
        console.print()
        console.print("[italic]Note: Document-level listing will be added in v0.2[/italic]")

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
