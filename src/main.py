"""
Command-line interface for ragged.

Provides CLI commands for document ingestion, querying, and management.
"""

import sys
from pathlib import Path
from typing import Optional

try:
    import click
    from rich.console import Console
    from rich.progress import Progress
    from rich.table import Table
except ImportError:
    click = None
    Console = None
    Progress = None
    Table = None

from src import __version__
from src.config.settings import get_settings
from src.utils.logging import get_logger, setup_logging

logger = get_logger(__name__)
console = Console() if Console else None


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
@click.argument("file_path", type=click.Path(exists=True, path_type=Path))
@click.option("--format", "-f", type=str, help="Force document format (pdf, txt, md, html)")
def add(file_path: Path, format: Optional[str]) -> None:
    """
    Ingest a document into the system.
    """
    from src.chunking.splitters import chunk_document
    from src.embeddings.factory import get_embedder
    from src.ingestion.loaders import load_document
    from src.storage.vector_store import VectorStore

    console.print(f"[bold blue]Ingesting document:[/bold blue] {file_path}")

    try:
        with Progress() as progress:
            task = progress.add_task("Processing...", total=100)

            # Load document
            progress.update(task, description="Loading document...", advance=10)
            document = load_document(file_path, format=format)
            progress.update(task, advance=10)

            # Chunk document
            progress.update(task, description="Chunking document...", advance=10)
            chunks = chunk_document(document)
            document.chunks = chunks
            progress.update(task, advance=20)

            # Generate embeddings
            progress.update(task, description="Generating embeddings...", advance=10)
            embedder = get_embedder()
            chunk_texts = [chunk.content for chunk in chunks]
            embeddings = embedder.embed_batch(chunk_texts)
            progress.update(task, advance=30)

            # Store in vector database
            progress.update(task, description="Storing in database...", advance=10)
            vector_store = VectorStore()

            ids = [chunk.chunk_id for chunk in chunks]
            metadatas = [chunk.metadata.model_dump() for chunk in chunks]

            vector_store.add(
                ids=ids,
                embeddings=embeddings,
                documents=chunk_texts,
                metadatas=metadatas,
            )
            progress.update(task, advance=10)

        console.print(f"[bold green]✓[/bold green] Document ingested: {document.document_id}")
        console.print(f"  Chunks: {len(chunks)}")
        console.print(f"  Path: {file_path}")

    except Exception as e:
        console.print(f"[bold red]✗[/bold red] Failed to ingest document: {e}")
        logger.error(f"Ingestion failed: {e}", exc_info=True)
        sys.exit(1)


@cli.command()
@click.argument("query")
@click.option("--k", "-k", default=5, help="Number of chunks to retrieve")
@click.option("--show-sources", is_flag=True, help="Show retrieved source chunks")
def query(query: str, k: int, show_sources: bool) -> None:
    """
    Ask a question and get an answer from your documents.
    """
    from src.generation.ollama_client import OllamaClient
    from src.generation.prompts import RAG_SYSTEM_PROMPT, build_rag_prompt
    from src.generation.response_parser import parse_response
    from src.retrieval.retriever import Retriever

    console.print(f"[bold blue]Question:[/bold blue] {query}")
    console.print()

    try:
        # Retrieve relevant chunks
        retriever = Retriever()
        chunks = retriever.retrieve(query, k=k)

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
        with Progress() as progress:
            task = progress.add_task("Generating answer...", total=100)
            ollama_client = OllamaClient()
            progress.update(task, advance=30)

            prompt = build_rag_prompt(query, chunks)
            progress.update(task, advance=20)

            response_text = ollama_client.generate(prompt, system=RAG_SYSTEM_PROMPT)
            progress.update(task, advance=40)

            response = parse_response(response_text)
            progress.update(task, advance=10)

        console.print("[bold]Answer:[/bold]")
        console.print(response.answer)

        if response.citations:
            console.print()
            console.print("[bold]Sources:[/bold]")
            for source in response.citations:
                console.print(f"  - {source}")

    except Exception as e:
        console.print(f"[bold red]✗[/bold red] Query failed: {e}")
        logger.error(f"Query failed: {e}", exc_info=True)
        sys.exit(1)


@cli.command("list")
def list_docs() -> None:
    """
    List all ingested documents.
    """
    from src.storage.vector_store import VectorStore

    try:
        vector_store = VectorStore()
        info = vector_store.get_collection_info()

        table = Table(title="Vector Store Information")
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


@cli.command()
@click.option("--force", "-f", is_flag=True, help="Skip confirmation")
def clear(force: bool) -> None:
    """
    Clear all ingested documents from the database.
    """
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


@cli.group()
def config() -> None:
    """Manage configuration."""
    pass


@config.command("show")
def config_show() -> None:
    """
    Show current configuration.
    """
    settings = get_settings()

    table = Table(title="Configuration")
    table.add_column("Setting", style="cyan")
    table.add_column("Value", style="magenta")

    table.add_row("Environment", settings.environment)
    table.add_row("Log Level", settings.log_level)
    table.add_row("Data Directory", str(settings.data_dir))
    table.add_row("Embedding Model", settings.embedding_model.value)
    table.add_row("Embedding Model Name", settings.embedding_model_name)
    table.add_row("LLM Model", settings.llm_model)
    table.add_row("Chunk Size", str(settings.chunk_size))
    table.add_row("Chunk Overlap", str(settings.chunk_overlap))
    table.add_row("ChromaDB URL", settings.chroma_url)
    table.add_row("Ollama URL", settings.ollama_url)

    console.print(table)


@config.command("set")
@click.argument("key")
@click.argument("value")
def config_set(key: str, value: str) -> None:
    """
    Set a configuration value.
    """
    console.print("[yellow]Config modification not yet implemented. Edit .env file manually.[/yellow]")
    console.print(f"To set {key}={value}, add to .env file:")


@cli.command()
def health() -> None:
    """
    Check health of all services.
    """
    from src.generation.ollama_client import OllamaClient
    from src.storage.vector_store import VectorStore

    console.print("[bold]Checking services...[/bold]")
    console.print()

    all_healthy = True

    # Ollama
    try:
        client = OllamaClient()
        if client.health_check():
            console.print("[green]✓[/green] Ollama: Running")
        else:
            console.print("[red]✗[/red] Ollama: Not responding")
            all_healthy = False
    except Exception as e:
        console.print(f"[red]✗[/red] Ollama: {e}")
        all_healthy = False

    # ChromaDB
    try:
        vector_store = VectorStore()
        if vector_store.health_check():
            count = vector_store.count()
            console.print(f"[green]✓[/green] ChromaDB: Running ({count} chunks stored)")
        else:
            console.print("[red]✗[/red] ChromaDB: Not responding")
            all_healthy = False
    except Exception as e:
        console.print(f"[red]✗[/red] ChromaDB: {e}")
        all_healthy = False

    console.print()
    if all_healthy:
        console.print("[bold green]All services healthy![/bold green]")
    else:
        console.print("[bold yellow]Some services are not available.[/bold yellow]")
        sys.exit(1)


def main() -> None:
    """Main entry point."""
    if click is None:
        print("Error: click and rich required. Install with: pip install click rich")
        sys.exit(1)
    cli()


if __name__ == "__main__":
    main()
