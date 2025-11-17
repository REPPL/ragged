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
@click.argument("path", type=click.Path(exists=True, path_type=Path))
@click.option("--format", "-f", type=str, help="Force document format (pdf, txt, md, html)")
@click.option("--recursive/--no-recursive", default=True, help="Scan subdirectories (default: True)")
@click.option("--max-depth", type=int, help="Maximum directory depth (unlimited by default)")
@click.option("--fail-fast", is_flag=True, help="Stop on first error instead of continuing")
def add(
    path: Path,
    format: Optional[str],
    recursive: bool,
    max_depth: Optional[int],
    fail_fast: bool,
) -> None:
    """
    Ingest document(s) into the system.

    PATH can be a single file or directory.
    When PATH is a directory, all supported documents are ingested recursively.
    Supported formats: PDF, TXT, MD, HTML
    """
    from src.chunking.splitters import chunk_document
    from src.embeddings.factory import get_embedder
    from src.ingestion.loaders import load_document
    from src.ingestion.scanner import DocumentScanner
    from src.ingestion.batch import BatchIngester, IngestionStatus
    from src.storage.vector_store import VectorStore

    # Determine if we're processing a single file or directory
    is_directory = path.is_dir()

    if is_directory:
        # Folder ingestion with batch processing
        console.print(f"[bold blue]Scanning:[/bold blue] {path}")

        scanner = DocumentScanner(
            follow_symlinks=False,
            max_depth=max_depth if not recursive else None,
        )

        file_paths = scanner.scan(path)

        if not file_paths:
            console.print("[yellow]No supported documents found.[/yellow]")
            console.print("Supported formats: PDF, TXT, MD, HTML")
            return

        console.print(f"Found {len(file_paths)} documents")

        # Batch ingestion
        batch_ingester = BatchIngester(
            console=console,
            continue_on_error=not fail_fast,
            skip_duplicates=True,  # Auto-skip duplicates in batch mode
        )

        with ProgressType() as progress:
            summary = batch_ingester.ingest_batch(file_paths, progress)

        # Display summary
        console.print()
        console.print("[bold]Summary:[/bold]")
        console.print(f"  ✓ Successful: {summary.successful}")
        console.print(f"  ⊗ Duplicates: {summary.duplicates} (skipped)")
        console.print(f"  ✗ Failed: {summary.failed}")
        console.print(f"  📊 Total chunks: {summary.total_chunks}")

        # Show failed documents if any
        if summary.failed > 0:
            console.print()
            console.print("[bold red]Failed documents:[/bold red]")
            for result in summary.results:
                if result.status == IngestionStatus.FAILED:
                    console.print(f"  • {result.file_path.name}: {result.error}")

        return

    # Single file ingestion (existing logic)
    console.print(f"[bold blue]Ingesting document:[/bold blue] {path}")

    # Initialize duplicate tracking variables
    existing_doc_id = None
    existing_path = None
    existing_count = 0

    try:
        with ProgressType() as progress:
            task = progress.add_task("Processing...", total=100)

            # Load document
            progress.update(task, description="Loading document...", advance=10)
            document = load_document(path, format=format)
            progress.update(task, advance=10)

            # Check for duplicates
            progress.update(task, description="Checking for duplicates...", advance=5)
            vector_store = VectorStore()
            file_hash = document.metadata.file_hash
            existing = vector_store.get_documents_by_metadata(where={"file_hash": file_hash})

            if existing and existing.get("ids"):
                # Document already exists
                existing_count = len(existing["ids"])
                existing_doc_id = existing["metadatas"][0].get("document_id", "unknown")
                existing_path = existing["metadatas"][0].get("document_path", "unknown")

                # Exit progress context to show prompt
                progress.update(task, completed=100)

        # Handle duplicate if found
        if existing_doc_id is not None:
            # Show duplicate warning outside progress context
            console.print()
            console.print(f"[yellow]⚠ Document already exists:[/yellow]")
            console.print(f"  Document ID: {existing_doc_id}")
            console.print(f"  Existing path: {existing_path}")
            console.print(f"  Current path:  {path}")
            console.print(f"  Chunks: {existing_count}")
            console.print()

            # Interactive confirmation
            overwrite = click.confirm("Document already exists. Overwrite?", default=False)

            if not overwrite:
                console.print("[yellow]Cancelled. No changes made.[/yellow]")
                return

            # Delete old chunks
            console.print(f"[yellow]Removing {existing_count} old chunks...[/yellow]")
            vector_store.delete(ids=existing["ids"])
            console.print(f"[green]✓[/green] Removed old chunks")
            console.print()

            # Preserve document_id for continuity
            document.document_id = existing_doc_id

        # Continue with chunking and storing (for both new documents and overwrites)
        with ProgressType() as progress:
            task = progress.add_task("Processing...", total=80, completed=20)

            # Chunk document
            progress.update(task, description="Chunking document...", advance=10)
            document = chunk_document(document)
            progress.update(task, advance=20)

            # Generate embeddings
            progress.update(task, description="Generating embeddings...", advance=10)
            embedder = get_embedder()
            chunk_texts = [chunk.text for chunk in document.chunks]
            embeddings = embedder.embed_batch(chunk_texts)
            progress.update(task, advance=20)

            # Store in vector database
            progress.update(task, description="Storing in database...", advance=10)

            ids = [chunk.chunk_id for chunk in document.chunks]
            # Serialize Path objects to strings for ChromaDB
            metadatas = []
            for chunk in document.chunks:
                metadata = chunk.metadata.model_dump()
                # Convert Path to string if present
                if "document_path" in metadata and hasattr(metadata["document_path"], "__fspath__"):
                    metadata["document_path"] = str(metadata["document_path"])

                # Remove None values - ChromaDB only supports str, int, float, bool
                metadata = {k: v for k, v in metadata.items() if v is not None}

                metadatas.append(metadata)

            vector_store.add(
                ids=ids,
                embeddings=embeddings,
                documents=chunk_texts,
                metadatas=metadatas,
            )
            progress.update(task, advance=10)

        console.print(f"[bold green]✓[/bold green] Document ingested: {document.document_id}")
        console.print(f"  Chunks: {len(document.chunks)}")
        console.print(f"  Path: {path}")

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


@cli.command("list")
def list_docs() -> None:
    """
    List all ingested documents.
    """
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

    table = TableType(title="Configuration")
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


@config.command("set-model")
@click.argument("model_name", required=False)
@click.option("--auto", is_flag=True, help="Automatically select recommended model")
def config_set_model(model_name: Optional[str], auto: bool) -> None:
    """
    Set the LLM model to use for generation.

    If no model specified, shows interactive selection menu.
    Use --auto to automatically select the recommended model.
    """
    from src.config.model_manager import ModelManager
    from src.config.settings import get_settings
    import yaml  # type: ignore[import-untyped]

    settings = get_settings()
    manager = ModelManager(settings.ollama_url)

    # Auto mode
    if auto:
        recommended = manager.get_recommended_model()
        if not recommended:
            console.print("[red]✗[/red] No models available. Install with: ollama pull llama3.2:latest")
            sys.exit(1)
        model_name = recommended
        console.print(f"[green]✓[/green] Auto-selected: {model_name}")

    # If model specified directly
    elif model_name:
        if not manager.verify_model(model_name):
            console.print(f"[red]✗[/red] Model '{model_name}' not found.")
            console.print("\nRun 'ragged config list-models' to see available models")
            sys.exit(1)

    # Interactive mode
    else:
        models = manager.list_available_models()

        if not models:
            console.print("[red]✗[/red] No models available.")
            console.print("\nInstall a model with:")
            console.print("  ollama pull llama3.2:latest")
            sys.exit(1)

        # Display selection table
        table = TableType(title="Available Models")
        table.add_column("#", style="cyan")
        table.add_column("Model", style="magenta")
        table.add_column("Context", style="yellow")
        table.add_column("Suitability", style="green")

        for i, m in enumerate(models[:10], 1):  # Show top 10
            score_bar = "█" * (m.suitability_score // 10)
            context_str = f"{m.context_length // 1000}k"
            table.add_row(str(i), m.name, context_str, f"{score_bar} ({m.suitability_score})")

        console.print(table)
        console.print()

        # Get selection
        while True:
            choice = click.prompt(f"Select model [1-{min(10, len(models))}]", type=int, default=1)
            if 1 <= choice <= min(10, len(models)):
                model_name = models[choice - 1].name
                break
            console.print("[red]Invalid selection[/red]")

    # Save to config file (ensure directory exists first)
    data_dir = settings.ensure_data_dir()
    config_file = data_dir / "config.yml"
    config: Dict[str, Any] = {}

    if config_file.exists():
        with open(config_file, "r") as f:
            config = yaml.safe_load(f) or {}

    config["llm_model"] = model_name

    with open(config_file, "w") as f:
        yaml.dump(config, f)

    console.print(f"[green]✓[/green] Model set to: {model_name}")
    console.print(f"  Config: {config_file}")
    console.print("\nNote: Set RAGGED_LLM_MODEL in .env for persistent configuration")


@config.command("list-models")
def config_list_models() -> None:
    """List all available Ollama models with RAG suitability scores."""
    from src.config.model_manager import ModelManager
    from src.config.settings import get_settings

    settings = get_settings()
    manager = ModelManager(settings.ollama_url)

    try:
        models = manager.list_available_models()

        if not models:
            console.print("[yellow]No models available.[/yellow]")
            console.print("\nInstall a model with:")
            console.print("  ollama pull llama3.2:latest")
            return

        table = TableType(title="Available Ollama Models")
        table.add_column("Model", style="cyan")
        table.add_column("Family", style="magenta")
        table.add_column("Context", style="yellow")
        table.add_column("RAG Suitability", style="green")
        table.add_column("Status", style="blue")

        current_model = settings.llm_model

        for m in models:
            score_bar = "█" * (m.suitability_score // 10)
            context_str = f"{m.context_length // 1000}k tokens"
            status = "✓ Current" if m.name == current_model else ""

            table.add_row(m.name, m.family, context_str, f"{score_bar} {m.suitability_score}/100", status)

        console.print(table)
        console.print()
        console.print(f"Current model: [bold]{current_model}[/bold]")
        console.print(f"\nChange model with: ragged config set-model")

    except Exception as e:
        console.print(f"[red]✗[/red] Failed to list models: {e}")
        sys.exit(1)


# Import commands from modules
from src.cli.commands.health import health

# Register commands
cli.add_command(health)


def main() -> None:
    """Main entry point."""
    if click is None:
        print("Error: click and rich required. Install with: pip install click rich")
        sys.exit(1)
    cli()


if __name__ == "__main__":
    main()
