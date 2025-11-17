"""Metadata management commands for ragged CLI.

Allows viewing and updating document metadata without re-ingestion.
"""

import json
import sys
from typing import Any, Dict, List, Optional

import click

from src.cli.common import console
from src.cli.formatters import FORMAT_CHOICES, print_formatted
from src.utils.logging import get_logger

logger = get_logger(__name__)


@click.group()
def metadata() -> None:
    """Manage document metadata.

    View, update, and search document metadata without re-ingestion.
    """
    pass


@metadata.command("list")
@click.option(
    "--limit",
    "-n",
    default=100,
    help="Maximum number of documents to list",
)
@click.option(
    "--format",
    "-f",
    "output_format",
    type=click.Choice(FORMAT_CHOICES, case_sensitive=False),
    default="table",
    help="Output format",
)
def list_metadata(limit: int, output_format: str) -> None:
    """List all documents with their metadata.

    \b
    Examples:
        ragged metadata list
        ragged metadata list --limit 50
        ragged metadata list --format json
    """
    from src.storage.vector_store import VectorStore

    try:
        vector_store = VectorStore()

        # Get all documents (ChromaDB returns unique documents by metadata)
        results = vector_store.collection.get(limit=limit)

        if not results or not results.get("ids"):
            console.print("[yellow]No documents found in the database.[/yellow]")
            return

        # Group by document_path to show unique documents
        from collections import defaultdict

        docs_by_path: Dict[str, Dict[str, Any]] = defaultdict(dict)

        for i, doc_id in enumerate(results["ids"]):
            metadata = results["metadatas"][i] if results.get("metadatas") else {}  # type: ignore
            doc_path = metadata.get("document_path", "Unknown")

            if doc_path not in docs_by_path:
                docs_by_path[doc_path] = {
                    "document": doc_path,
                    "chunks": 0,
                    "pages": metadata.get("total_pages", "N/A"),
                    "file_hash": metadata.get("file_hash", "N/A"),
                    "ingestion_date": metadata.get("ingestion_date", "N/A"),
                }

            docs_by_path[doc_path]["chunks"] += 1

        # Convert to list for formatting
        doc_list = list(docs_by_path.values())

        print_formatted(
            doc_list,
            format_type=output_format,  # type: ignore
            title=f"Documents ({len(doc_list)} total)",
            console=console,
        )

    except Exception as e:
        console.print(f"[bold red]✗[/bold red] Failed to list metadata: {e}")
        logger.error(f"List metadata failed: {e}", exc_info=True)
        sys.exit(1)


@metadata.command("show")
@click.argument("document_path")
@click.option(
    "--format",
    "-f",
    "output_format",
    type=click.Choice(["text", "json"], case_sensitive=False),
    default="text",
    help="Output format",
)
def show_metadata(document_path: str, output_format: str) -> None:
    """Show metadata for a specific document.

    \b
    Examples:
        ragged metadata show document.pdf
        ragged metadata show document.pdf --format json
    """
    from src.storage.vector_store import VectorStore

    try:
        vector_store = VectorStore()

        # Get document by path
        results = vector_store.get_documents_by_metadata({"document_path": document_path})

        if not results or not results.get("ids"):
            console.print(f"[yellow]Document not found: {document_path}[/yellow]")
            sys.exit(1)

        if output_format == "json":
            # Get first chunk's metadata as representative
            metadata = results["metadatas"][0] if results.get("metadatas") else {}  # type: ignore
            print(json.dumps(metadata, indent=2))
        else:
            console.print(f"[bold]Document:[/bold] {document_path}")
            console.print(f"[bold]Chunks:[/bold] {len(results['ids'])}")
            console.print()

            if results.get("metadatas"):
                # Show first chunk's metadata
                metadata = results["metadatas"][0]  # type: ignore
                console.print("[bold]Metadata:[/bold]")
                for key, value in sorted(metadata.items()):  # type: ignore
                    console.print(f"  {key}: {value}")

    except Exception as e:
        console.print(f"[bold red]✗[/bold red] Failed to show metadata: {e}")
        logger.error(f"Show metadata failed: {e}", exc_info=True)
        sys.exit(1)


@metadata.command("update")
@click.argument("document_path")
@click.option("--set", "-s", "updates", multiple=True, help="Set metadata (key=value)")
@click.option("--delete", "-d", "deletions", multiple=True, help="Delete metadata key")
def update_metadata(document_path: str, updates: tuple, deletions: tuple) -> None:
    """Update metadata for a document.

    Updates all chunks of the specified document.

    \b
    Examples:
        ragged metadata update document.pdf --set category=research
        ragged metadata update document.pdf --set tags=ml,ai --set priority=high
        ragged metadata update document.pdf --delete old_key
    """
    from src.storage.vector_store import VectorStore

    if not updates and not deletions:
        console.print("[yellow]No updates specified. Use --set or --delete.[/yellow]")
        return

    try:
        vector_store = VectorStore()

        # Get document chunks
        results = vector_store.get_documents_by_metadata({"document_path": document_path})

        if not results or not results.get("ids"):
            console.print(f"[yellow]Document not found: {document_path}[/yellow]")
            sys.exit(1)

        ids = results["ids"]
        metadatas = results["metadatas"]  # type: ignore

        # Parse updates
        update_dict: Dict[str, Any] = {}
        for update_str in updates:
            if "=" not in update_str:
                console.print(f"[red]Invalid update format: {update_str}. Use key=value[/red]")
                sys.exit(1)
            key, value = update_str.split("=", 1)
            update_dict[key] = value

        # Apply updates to each chunk's metadata
        updated_metadatas = []
        for metadata in metadatas:
            # Create copy and apply updates
            new_metadata = dict(metadata)
            new_metadata.update(update_dict)

            # Apply deletions
            for key in deletions:
                new_metadata.pop(key, None)

            updated_metadatas.append(new_metadata)

        # Update in vector store
        vector_store.update_metadata(ids, updated_metadatas)

        console.print(f"[green]✓[/green] Updated metadata for {len(ids)} chunks of {document_path}")

        if updates:
            console.print(f"  Set: {', '.join(f'{k}={v}' for k, v in update_dict.items())}")
        if deletions:
            console.print(f"  Deleted: {', '.join(deletions)}")

    except Exception as e:
        console.print(f"[bold red]✗[/bold red] Failed to update metadata: {e}")
        logger.error(f"Update metadata failed: {e}", exc_info=True)
        sys.exit(1)


@metadata.command("search")
@click.option("--filter", "-f", "filters", multiple=True, help="Filter by metadata (key=value)")
@click.option(
    "--format",
    "-o",
    "output_format",
    type=click.Choice(FORMAT_CHOICES, case_sensitive=False),
    default="table",
    help="Output format",
)
def search_metadata(filters: tuple, output_format: str) -> None:
    """Search documents by metadata.

    \b
    Examples:
        ragged metadata search --filter category=research
        ragged metadata search --filter category=research --filter priority=high
        ragged metadata search --filter tags=ml --format json
    """
    from src.storage.vector_store import VectorStore

    if not filters:
        console.print("[yellow]No filters specified. Use --filter key=value.[/yellow]")
        return

    try:
        # Parse filters
        where: Dict[str, Any] = {}
        for filter_str in filters:
            if "=" not in filter_str:
                console.print(f"[red]Invalid filter format: {filter_str}. Use key=value[/red]")
                sys.exit(1)
            key, value = filter_str.split("=", 1)
            where[key] = value

        vector_store = VectorStore()
        results = vector_store.get_documents_by_metadata(where)

        if not results or not results.get("ids"):
            console.print("[yellow]No documents found matching filters.[/yellow]")
            return

        # Group by document
        from collections import defaultdict

        docs_by_path: Dict[str, Dict[str, Any]] = defaultdict(dict)

        for i, doc_id in enumerate(results["ids"]):
            metadata = results["metadatas"][i] if results.get("metadatas") else {}  # type: ignore
            doc_path = metadata.get("document_path", "Unknown")

            if doc_path not in docs_by_path:
                docs_by_path[doc_path] = {
                    "document": doc_path,
                    "chunks": 0,
                }
                # Add filter fields to output
                for key in where.keys():
                    docs_by_path[doc_path][key] = metadata.get(key, "N/A")

            docs_by_path[doc_path]["chunks"] += 1

        doc_list = list(docs_by_path.values())

        print_formatted(
            doc_list,
            format_type=output_format,  # type: ignore
            title=f"Search Results ({len(doc_list)} documents)",
            console=console,
        )

    except Exception as e:
        console.print(f"[bold red]✗[/bold red] Failed to search metadata: {e}")
        logger.error(f"Search metadata failed: {e}", exc_info=True)
        sys.exit(1)
