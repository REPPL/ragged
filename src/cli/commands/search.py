"""Advanced search and filtering commands for ragged CLI.

Provides powerful search and filtering across documents and chunks.
"""

import sys
from typing import Any, Dict, List, Optional

import click

from src.cli.common import console
from src.cli.formatters import FORMAT_CHOICES, print_formatted
from src.utils.logging import get_logger

logger = get_logger(__name__)


@click.command()
@click.argument("query", required=False)
@click.option(
    "--path",
    "-p",
    "document_path",
    help="Filter by document path (supports wildcards)",
)
@click.option(
    "--metadata",
    "-m",
    "metadata_filters",
    multiple=True,
    help="Filter by metadata (key=value, can be used multiple times)",
)
@click.option(
    "--min-score",
    "-s",
    type=float,
    help="Minimum relevance score (0.0-1.0)",
)
@click.option(
    "--limit",
    "-n",
    default=10,
    help="Maximum number of results",
)
@click.option(
    "--show-content",
    "-c",
    is_flag=True,
    help="Show chunk content preview",
)
@click.option(
    "--format",
    "-f",
    "output_format",
    type=click.Choice(FORMAT_CHOICES + ["text"], case_sensitive=False),
    default="text",
    help="Output format",
)
def search(
    query: Optional[str],
    document_path: Optional[str],
    metadata_filters: tuple,
    min_score: Optional[float],
    limit: int,
    show_content: bool,
    output_format: str,
) -> None:
    """Advanced search across documents with filtering.

    Search by semantic similarity (query), document path, and metadata.
    Combine multiple filters for precise results.

    \b
    Examples:
        # Semantic search
        ragged search "machine learning concepts"

        # Search in specific document
        ragged search "neural networks" --path research.pdf

        # Filter by metadata
        ragged search "deep learning" --metadata category=research

        # Multiple filters
        ragged search "AI" --metadata category=research --metadata priority=high

        # Show content preview
        ragged search "transformers" --show-content

        # List all chunks from a document
        ragged search --path document.pdf --limit 100

        # Export results as JSON
        ragged search "topic" --format json > results.json
    """
    from src.retrieval.retriever import Retriever
    from src.storage.vector_store import VectorStore

    if not query and not document_path and not metadata_filters:
        console.print("[yellow]Provide at least one of: query, --path, or --metadata[/yellow]")
        console.print("\nExamples:")
        console.print("  ragged search 'machine learning'")
        console.print("  ragged search --path document.pdf")
        console.print("  ragged search --metadata category=research")
        return

    try:
        vector_store = VectorStore()

        # Build metadata filter
        where_filter: Optional[Dict[str, Any]] = None
        if document_path or metadata_filters:
            where_filter = {}

            if document_path:
                # Support wildcards by checking if path contains wildcard characters
                if "*" in document_path or "?" in document_path:
                    console.print(
                        "[yellow]Note: Wildcard matching not yet supported. "
                        "Matching exact path.[/yellow]"
                    )
                where_filter["document_path"] = document_path

            # Add metadata filters
            for filter_str in metadata_filters:
                if "=" not in filter_str:
                    console.print(f"[red]Invalid filter: {filter_str}. Use key=value[/red]")
                    sys.exit(1)
                key, value = filter_str.split("=", 1)
                where_filter[key] = value

        # Perform search
        if query:
            # Semantic search with optional filters
            retriever = Retriever()

            if where_filter:
                # Use vector store query directly with filter
                results = vector_store.query(
                    query_embedding=retriever.embedder.embed(query),
                    top_k=limit,
                    where=where_filter,
                )
            else:
                # Use retriever for simpler search
                from src.models.chunk import RetrievedChunk

                chunks = retriever.retrieve(query, top_k=limit)
                # Convert to results format
                results = {
                    "ids": [chunk.chunk_id for chunk in chunks],
                    "documents": [chunk.text for chunk in chunks],
                    "metadatas": [chunk.metadata for chunk in chunks],
                    "distances": [1.0 - chunk.score for chunk in chunks],
                }
        else:
            # Metadata-only search (no semantic ranking)
            results = vector_store.get_documents_by_metadata(where_filter or {})
            # Add dummy distances for consistency
            if results and results.get("ids"):
                results["distances"] = [0.0] * len(results["ids"])

        if not results or not results.get("ids"):
            console.print("[yellow]No results found.[/yellow]")
            return

        # Filter by min_score if specified
        if min_score is not None and results.get("distances"):
            # Convert distance to score (similarity)
            filtered_indices = [
                i
                for i, dist in enumerate(results["distances"])  # type: ignore
                if (1.0 - dist) >= min_score
            ]

            if not filtered_indices:
                console.print(f"[yellow]No results with score >= {min_score}[/yellow]")
                return

            # Filter all result arrays
            results["ids"] = [results["ids"][i] for i in filtered_indices]
            results["documents"] = [results["documents"][i] for i in filtered_indices]  # type: ignore
            results["metadatas"] = [results["metadatas"][i] for i in filtered_indices]  # type: ignore
            results["distances"] = [results["distances"][i] for i in filtered_indices]  # type: ignore

        # Format output
        if output_format == "text":
            _print_text_results(results, show_content, query is not None)
        else:
            _print_formatted_results(results, output_format, show_content)

    except Exception as e:
        console.print(f"[bold red]✗[/bold red] Search failed: {e}")
        logger.error(f"Search failed: {e}", exc_info=True)
        sys.exit(1)


def _print_text_results(
    results: Dict[str, Any], show_content: bool, has_query: bool
) -> None:
    """Print results in text format."""
    count = len(results["ids"])
    console.print(f"\n[bold]Found {count} result(s)[/bold]\n")

    for i, chunk_id in enumerate(results["ids"]):
        metadata = results["metadatas"][i] if results.get("metadatas") else {}  # type: ignore
        distance = results["distances"][i] if results.get("distances") else 0.0  # type: ignore
        score = 1.0 - distance if has_query else None

        # Header
        doc_path = metadata.get("document_path", "Unknown")  # type: ignore
        page = metadata.get("page_number", "N/A")  # type: ignore

        if score is not None:
            console.print(f"[bold cyan][{i+1}][/bold cyan] {doc_path} (page {page}) - Score: {score:.3f}")
        else:
            console.print(f"[bold cyan][{i+1}][/bold cyan] {doc_path} (page {page})")

        # Show content preview if requested
        if show_content:
            text = results["documents"][i] if results.get("documents") else ""  # type: ignore
            preview = text[:200] + "..." if len(text) > 200 else text
            console.print(f"  {preview}")

        # Show key metadata
        chunk_idx = metadata.get("chunk_index", "N/A")  # type: ignore
        console.print(f"  Chunk: {chunk_idx}, ID: {chunk_id}")

        console.print()


def _print_formatted_results(
    results: Dict[str, Any], output_format: str, show_content: bool
) -> None:
    """Print results in structured format (JSON, CSV, etc.)."""
    # Prepare data for formatting
    data = []

    for i, chunk_id in enumerate(results["ids"]):
        metadata = results["metadatas"][i] if results.get("metadatas") else {}  # type: ignore
        distance = results["distances"][i] if results.get("distances") else 0.0  # type: ignore
        score = 1.0 - distance

        item = {
            "rank": i + 1,
            "chunk_id": chunk_id,
            "document": metadata.get("document_path", "Unknown"),  # type: ignore
            "page": metadata.get("page_number", "N/A"),  # type: ignore
            "chunk_index": metadata.get("chunk_index", "N/A"),  # type: ignore
            "score": round(score, 3),
        }

        if show_content:
            text = results["documents"][i] if results.get("documents") else ""  # type: ignore
            item["content"] = text

        data.append(item)

    print_formatted(
        data,
        format_type=output_format,  # type: ignore
        title="Search Results",
        console=console,
    )
