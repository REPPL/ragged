"""Query command for ragged CLI."""

import json
import sys
from typing import Literal, Optional, cast

import click

from src.cli.common import console, ProgressType
from src.cli.formatters import FORMAT_CHOICES, print_formatted
from src.utils.logging import get_logger

logger = get_logger(__name__)


@click.command()
@click.argument("query")
@click.option("--k", "-k", default=5, help="Number of chunks to retrieve")
@click.option("--show-sources", is_flag=True, help="Show retrieved source chunks")
@click.option(
    "--format",
    "-f",
    "output_format",
    type=click.Choice(["text", "json"], case_sensitive=False),
    default="text",
    help="Output format (text for human-readable, json for programmatic use)",
)
def query(query: str, k: int, show_sources: bool, output_format: str) -> None:
    """Ask a question and get an answer from your documents.

    \b
    Examples:
        ragged query "What is the main topic?"
        ragged query "Explain the process" --show-sources
        ragged query "Summary?" --format json > result.json
    """
    from src.config.settings import get_settings
    from src.generation.ollama_client import OllamaClient
    from src.generation.prompts import RAG_SYSTEM_PROMPT, build_rag_prompt
    from src.generation.response_parser import parse_response
    from src.generation.citation_formatter import format_response_with_references
    from src.retrieval.retriever import Retriever
    from src.retrieval.bm25 import BM25Retriever
    from src.retrieval.hybrid import HybridRetriever

    if output_format == "text":
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
            if output_format == "json":
                print(json.dumps({"error": "No relevant documents found", "query": query}))
            else:
                console.print("[yellow]No relevant documents found. Have you ingested any documents yet?[/yellow]")
                console.print("Use: ragged add <file_path> to ingest documents.")
            sys.exit(1)

        # Generate answer
        if output_format == "text":
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
        else:
            # JSON format: no progress bar
            ollama_client = OllamaClient()
            prompt = build_rag_prompt(query, chunks)
            response_text = ollama_client.generate(prompt, system=RAG_SYSTEM_PROMPT)
            formatted_response = format_response_with_references(
                response_text,
                chunks,
                show_file_path=True,
                include_unused_refs=False
            )

        # Output results
        if output_format == "json":
            result = {
                "query": query,
                "answer": formatted_response,
                "sources": [
                    {
                        "document": chunk.document_path,
                        "score": chunk.score,
                        "text": chunk.text,
                        "page": chunk.page_number,
                    }
                    for chunk in chunks
                ],
                "retrieval_method": settings.retrieval_method,
                "top_k": k,
            }
            print(json.dumps(result, indent=2))
        else:
            if show_sources:
                console.print("[bold]Retrieved sources:[/bold]")
                for i, chunk in enumerate(chunks, 1):
                    console.print(f"  [{i}] {chunk.document_path} (score: {chunk.score:.3f})")
                    preview = chunk.text[:100] + "..." if len(chunk.text) > 100 else chunk.text
                    console.print(f"      {preview}")
                console.print()

            console.print("[bold]Answer:[/bold]")
            console.print(formatted_response)

    except Exception as e:
        if output_format == "json":
            print(json.dumps({"error": str(e), "query": query}))
        else:
            console.print(f"[bold red]✗[/bold red] Query failed: {e}")
        logger.error(f"Query failed: {e}", exc_info=True)
        sys.exit(1)
