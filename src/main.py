"""
Command-line interface for ragged.

Provides CLI commands for document ingestion, querying, and management.
"""

import sys
from pathlib import Path
from typing import Any, Dict, Literal, Optional, cast

from src import __version__
from src.cli.common import click, console, ConsoleType, ProgressType, TableType
from src.config.settings import get_settings
from src.utils.logging import get_logger, setup_logging

logger = get_logger(__name__)


@click.group()
@click.version_option(version=__version__)
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose logging")
@click.option("--debug", is_flag=True, help="Enable debug logging")
def cli(verbose: bool, debug: bool) -> None:
    """ragged - Privacy-first local RAG system."""
    if click is None:
        print("Error: click and rich required. Install with: pip install click rich")
        sys.exit(1)
    log_level = "DEBUG" if debug else ("INFO" if verbose else "WARNING")
    setup_logging(log_level=log_level, json_format=False)


@cli.command()
@click.argument("query")
@click.option("--k", "-k", default=5, help="Number of chunks to retrieve")
@click.option("--show-sources", is_flag=True, help="Show retrieved source chunks")
def query(query: str, k: int, show_sources: bool) -> None:
    """
    Ask a question and get an answer from your documents.
    """
    from src.config.settings import get_settings
    from src.generation.ollama_client import OllamaClient
    from src.generation.prompts import RAG_SYSTEM_PROMPT, build_rag_prompt
    from src.generation.response_parser import parse_response
    from src.generation.citation_formatter import format_response_with_references
    from src.retrieval.retriever import Retriever
    from src.retrieval.bm25 import BM25Retriever
    from src.retrieval.hybrid import HybridRetriever

    console.print(f"[bold blue]Question:[/bold blue] {query}")
    console.print()

    try:
        # Retrieve relevant chunks using hybrid retrieval
        settings = get_settings()
        vector_retriever = Retriever()
        bm25_retriever = BM25Retriever()
        hybrid_retriever = HybridRetriever(
            vector_retriever=vector_retriever,
            bm25_retriever=bm25_retriever
        )
        chunks = hybrid_retriever.retrieve(
            query,
            top_k=k,
            method=cast(Optional[Literal['vector', 'bm25', 'hybrid']], settings.retrieval_method)
        )

        if not chunks:
            console.print("[yellow]No relevant documents found. Have you ingested any documents yet?[/yellow]")
            console.print("Use: ragged add <file_path> to ingest documents.")
            sys.exit(1)

        if show_sources:
            console.print("[bold]Retrieved sources:[/bold]")
            for i, chunk in enumerate(chunks, 1):
                console.print(f"  [{i}] {chunk.document_path} (score: {chunk.score:.3f})")
                preview = chunk.text[:100] + "..." if len(chunk.text) > 100 else chunk.text
                console.print(f"      {preview}")
            console.print()

        # Generate answer
        with ProgressType() as progress:
            task = progress.add_task("Generating answer...", total=100)
            ollama_client = OllamaClient()
            progress.update(task, advance=30)

            prompt = build_rag_prompt(query, chunks)
            progress.update(task, advance=20)

            response_text = ollama_client.generate(prompt, system=RAG_SYSTEM_PROMPT)
            progress.update(task, advance=40)

            # Format response with IEEE-style references
            formatted_response = format_response_with_references(
                response_text,
                chunks,
                show_file_path=True,
                include_unused_refs=False
            )
            progress.update(task, advance=10)

        console.print("[bold]Answer:[/bold]")
        console.print(formatted_response)

    except Exception as e:
        console.print(f"[bold red]✗[/bold red] Query failed: {e}")
        logger.error(f"Query failed: {e}", exc_info=True)
        sys.exit(1)


# Document management and config commands extracted to cli/commands/


# Import commands from modules
from src.cli.commands.add import add
from src.cli.commands.health import health
from src.cli.commands.docs import list_docs, clear
from src.cli.commands.config import config

# Register commands
cli.add_command(add)
cli.add_command(health)
cli.add_command(list_docs)
cli.add_command(clear)
cli.add_command(config)


def main() -> None:
    """Main entry point."""
    if click is None:
        print("Error: click and rich required. Install with: pip install click rich")
        sys.exit(1)
    cli()


if __name__ == "__main__":
    main()
