"""Query command for ragged CLI."""

import sys
from typing import Literal, Optional, cast

import click

from src.cli.common import console, ProgressType
from src.utils.logging import get_logger

logger = get_logger(__name__)


@click.command()
@click.argument("query")
@click.option("--k", "-k", default=5, help="Number of chunks to retrieve")
@click.option("--show-sources", is_flag=True, help="Show retrieved source chunks")
def query(query: str, k: int, show_sources: bool) -> None:
    """Ask a question and get an answer from your documents."""
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
