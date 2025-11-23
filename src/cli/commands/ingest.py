"""Multi-modal document ingestion commands for ragged CLI.

v0.5.3: Enhanced ingestion with vision embeddings, batch processing, and GPU management.
"""

import asyncio
import sys
from pathlib import Path
from typing import Optional

import click

from src.cli.common import ProgressType, console
from src.utils.logging import get_logger

logger = get_logger(__name__)


@click.group()
def ingest() -> None:
    """Ingest documents with optional vision embeddings.

    \b
    Commands:
        pdf     - Ingest PDF with optional vision embeddings
        batch   - Batch ingest PDFs from directory
        status  - Check ingestion progress

    \b
    Examples:
        ragged ingest pdf document.pdf --vision
        ragged ingest batch ./docs --vision --recursive
        ragged ingest status
    """
    pass


@ingest.command()
@click.argument("path", type=click.Path(exists=True, path_type=Path))
@click.option("--format", "-f", type=str, help="Force document format (pdf, txt, md, html)")
@click.option(
    "--chunking",
    type=click.Choice(["fixed", "semantic", "hierarchical"], case_sensitive=False),
    help="Text chunking strategy (default: fixed)",
)
@click.option(
    "--auto-correct/--no-auto-correct",
    default=True,
    help="Auto-detect and correct PDF issues (default: enabled)",
)
@click.option(
    "--vision/--no-vision",
    default=False,
    help="Enable vision embeddings (requires GPU)",
)
@click.option(
    "--device",
    type=click.Choice(["auto", "cuda", "mps", "cpu"], case_sensitive=False),
    default="auto",
    help="Device for vision processing (default: auto)",
)
@click.option(
    "--batch-size",
    type=int,
    help="Vision embedding batch size (default: adaptive)",
)
@click.option(
    "--overwrite",
    is_flag=True,
    help="Overwrite existing document without confirmation",
)
def pdf(
    path: Path,
    format: Optional[str],
    chunking: Optional[str],
    auto_correct: bool,
    vision: bool,
    device: str,
    batch_size: Optional[int],
    overwrite: bool,
) -> None:
    """Ingest PDF with optional vision embeddings.

    \b
    Vision Mode:
    When --vision is enabled, the system generates both text and vision embeddings
    for multi-modal retrieval. This requires a GPU (CUDA or MPS).

    \b
    Device Selection:
    - auto: Automatically select best device (CUDA > MPS > CPU)
    - cuda: Force NVIDIA GPU
    - mps: Force Apple Silicon GPU
    - cpu: Force CPU (not recommended for vision)

    \b
    Examples:
        ragged ingest pdf document.pdf
        ragged ingest pdf document.pdf --vision
        ragged ingest pdf document.pdf --vision --device cuda:0
        ragged ingest pdf document.pdf --vision --batch-size 8
    """
    from src.chunking.splitters import chunk_document
    from src.embeddings.factory import get_embedder
    from src.ingestion.loaders import load_document
    from src.storage.vector_store import VectorStore

    console.print(f"[bold blue]Ingesting PDF:[/bold blue] {path}")

    # PDF correction variables
    pdf_corrected = False
    pdf_analysis = None
    corrected_pdf_path = None

    try:
        # PDF Correction: Analyze and correct PDFs before processing
        if auto_correct and path.suffix.lower() == ".pdf":
            from src.correction import CorrectionPipeline

            console.print("[dim]Analysing PDF quality...[/dim]")

            with ProgressType() as progress:
                task = progress.add_task("Analysing PDF...", total=100)

                pipeline = CorrectionPipeline()

                progress.update(task, description="Detecting issues...", advance=30)
                corrected_pdf_path = path.parent / f".corrected_{path.name}"

                # Run async analysis and correction
                pdf_analysis, pdf_correction = asyncio.run(
                    pipeline.analyze_and_correct(path, corrected_pdf_path)
                )

                progress.update(task, advance=70)

            # Display quality summary
            summary = pipeline.format_analysis_summary(pdf_analysis)
            quality_display = f"[{summary['quality_color']}]{summary['quality_icon']} Quality: {summary['quality_score']} ({summary['quality_grade']})[/{summary['quality_color']}]"
            console.print(f"  {quality_display}")

            if pdf_analysis.requires_correction and pdf_correction:
                successful = len([a for a in pdf_correction.actions if a.success])
                total = len(pdf_correction.actions)
                console.print(
                    f"  [yellow]⚡ Auto-corrected:[/yellow] {successful}/{total} issues"
                )

                if summary["issue_summary"] != "none":
                    console.print(f"  [dim]Issues: {summary['issue_summary']}[/dim]")

                # Use corrected PDF for processing
                path = corrected_pdf_path
                pdf_corrected = True
            elif pdf_analysis.issues:
                console.print(
                    f"  [dim]Issues detected but not corrected: {summary['issue_summary']}[/dim]"
                )

        # Process document
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

            existing_doc_id = None
            if existing and existing.get("ids"):
                existing_count = len(existing["ids"])
                existing_doc_id = existing["metadatas"][0].get("document_id", "unknown")
                existing_path = existing["metadatas"][0].get("document_path", "unknown")

                progress.update(task, completed=100)

        # Handle duplicate if found
        if existing_doc_id is not None:
            console.print()
            console.print("[yellow]⚠ Document already exists:[/yellow]")
            console.print(f"  Document ID: {existing_doc_id}")
            console.print(f"  Existing path: {existing_path}")
            console.print(f"  Current path:  {path}")
            console.print(f"  Chunks: {existing_count}")
            console.print()

            # Check for overwrite confirmation
            if not overwrite:
                overwrite_confirmed = click.confirm(
                    "Document already exists. Overwrite?", default=False
                )
                if not overwrite_confirmed:
                    console.print("[yellow]Cancelled. No changes made.[/yellow]")
                    return

            # Delete old chunks
            console.print(f"[yellow]Removing {existing_count} old chunks...[/yellow]")
            vector_store.delete(ids=existing["ids"])
            console.print("[green]✓[/green] Removed old chunks")
            console.print()

            # Preserve document_id for continuity
            document.document_id = existing_doc_id

        # Continue with processing
        with ProgressType() as progress:
            task = progress.add_task("Processing...", total=100)

            # Chunk document
            progress.update(task, description="Chunking document...", advance=10)
            document = chunk_document(document, strategy=chunking)
            progress.update(task, advance=20)

            # Generate text embeddings
            progress.update(task, description="Generating text embeddings...", advance=10)
            embedder = get_embedder()
            chunk_texts = [chunk.text for chunk in document.chunks]
            text_embeddings = embedder.embed_batch(chunk_texts)
            progress.update(task, advance=20)

            # Store text embeddings
            progress.update(task, description="Storing text embeddings...", advance=10)
            ids = [chunk.chunk_id for chunk in document.chunks]
            metadatas = []
            for chunk in document.chunks:
                metadata = chunk.metadata.model_dump()
                # Convert Path to string if present
                if "document_path" in metadata and hasattr(
                    metadata["document_path"], "__fspath__"
                ):
                    metadata["document_path"] = str(metadata["document_path"])

                # Remove None values
                metadata = {k: v for k, v in metadata.items() if v is not None}
                metadatas.append(metadata)

            vector_store.add(
                ids=ids,
                embeddings=text_embeddings,
                documents=chunk_texts,
                metadatas=metadatas,
            )
            progress.update(task, advance=20)

            # Generate vision embeddings if enabled
            if vision:
                progress.update(task, description="Generating vision embeddings...", advance=0)

                # Import vision components
                from src.embeddings.colpali_embedder import ColPaliEmbedder
                from src.storage.dual_storage import DualVectorStore

                # Initialize vision embedder with GPU management
                vision_embedder = ColPaliEmbedder(
                    device=None if device == "auto" else device,
                    batch_size=batch_size,
                    enable_adaptive_batching=batch_size is None,
                    enable_memory_monitoring=True,
                    enable_oom_recovery=True,
                )

                console.print(
                    f"  [dim]Vision device: {vision_embedder.device_info.device_type.value}[/dim]"
                )
                console.print(f"  [dim]Batch size: {vision_embedder.batch_size}[/dim]")

                # Load PDF as images
                from pdf2image import convert_from_path

                images = convert_from_path(str(path))
                console.print(f"  [dim]Pages: {len(images)}[/dim]")

                # Generate vision embeddings
                vision_embeddings = vision_embedder.embed_batch_images(images)

                # Store vision embeddings
                dual_store = DualVectorStore()
                dual_store.add_vision_embeddings(
                    document_id=document.document_id,
                    page_embeddings=vision_embeddings,
                    document_path=path,
                )

                progress.update(task, advance=10)

        console.print(f"[bold green]✓[/bold green] Document ingested: {document.document_id}")
        console.print(f"  Chunks: {len(document.chunks)}")
        console.print(f"  Path: {path}")
        if vision:
            console.print(f"  Vision embeddings: {len(vision_embeddings)} pages")

        # Generate PDF correction metadata
        if pdf_analysis is not None:
            try:
                from src.correction import MetadataGenerator

                metadata_dir = Path("data/documents/.ragged") / document.document_id
                metadata_dir.mkdir(parents=True, exist_ok=True)

                generator = MetadataGenerator(metadata_dir)
                metadata_files = generator.generate_all(
                    pdf_analysis, pdf_correction if pdf_corrected else None
                )

                console.print(f"  [dim]Metadata: {len(metadata_files)} files generated[/dim]")
            except Exception as e:
                logger.warning(f"Failed to generate PDF metadata: {e}")

    except Exception as e:
        console.print(f"[bold red]✗[/bold red] Failed to ingest PDF: {e}")
        logger.error(f"Ingestion failed: {e}", exc_info=True)
        sys.exit(1)

    finally:
        # Cleanup temporary corrected PDF
        if pdf_corrected and corrected_pdf_path and corrected_pdf_path.exists():
            try:
                corrected_pdf_path.unlink()
                logger.debug(f"Cleaned up temporary corrected PDF: {corrected_pdf_path}")
            except Exception as e:
                logger.warning(f"Failed to cleanup corrected PDF: {e}")


@ingest.command()
@click.argument("directory", type=click.Path(exists=True, file_okay=False, path_type=Path))
@click.option(
    "--pattern",
    default="*.pdf",
    help="File pattern to match (default: *.pdf)",
)
@click.option(
    "--recursive/--no-recursive",
    default=True,
    help="Recursively scan subdirectories (default: True)",
)
@click.option(
    "--max-depth",
    type=int,
    help="Maximum directory depth (unlimited by default)",
)
@click.option(
    "--vision/--no-vision",
    default=False,
    help="Enable vision embeddings (requires GPU)",
)
@click.option(
    "--device",
    type=click.Choice(["auto", "cuda", "mps", "cpu"], case_sensitive=False),
    default="auto",
    help="Device for vision processing (default: auto)",
)
@click.option(
    "--batch-size",
    type=int,
    help="Vision embedding batch size (default: adaptive)",
)
@click.option(
    "--fail-fast",
    is_flag=True,
    help="Stop on first error instead of continuing",
)
@click.option(
    "--skip-duplicates",
    is_flag=True,
    default=True,
    help="Automatically skip duplicate documents (default: True)",
)
def batch(
    directory: Path,
    pattern: str,
    recursive: bool,
    max_depth: Optional[int],
    vision: bool,
    device: str,
    batch_size: Optional[int],
    fail_fast: bool,
    skip_duplicates: bool,
) -> None:
    """Batch ingest PDFs from directory.

    \b
    Batch Mode Features:
    - Automatic duplicate detection and skipping
    - Progress tracking across multiple files
    - Error handling with continue-on-error option
    - Summary statistics at completion

    \b
    Examples:
        ragged ingest batch ./docs
        ragged ingest batch ./docs --vision --recursive
        ragged ingest batch ./docs --pattern "*.pdf" --max-depth 2
        ragged ingest batch ./docs --vision --fail-fast
    """
    from src.ingestion.batch import BatchIngester
    from src.ingestion.scanner import DocumentScanner

    console.print(f"[bold blue]Scanning:[/bold blue] {directory}")

    # Scan for documents
    scanner = DocumentScanner(
        follow_symlinks=False,
        max_depth=max_depth if not recursive else None,
    )

    # Use glob pattern for scanning
    if recursive:
        file_paths = list(directory.rglob(pattern))
    else:
        file_paths = list(directory.glob(pattern))

    if not file_paths:
        console.print(f"[yellow]No files matching '{pattern}' found.[/yellow]")
        return

    console.print(f"Found {len(file_paths)} documents")

    # Initialize vision embedder if needed
    vision_embedder = None
    if vision:
        from src.embeddings.colpali_embedder import ColPaliEmbedder

        vision_embedder = ColPaliEmbedder(
            device=None if device == "auto" else device,
            batch_size=batch_size,
            enable_adaptive_batching=batch_size is None,
            enable_memory_monitoring=True,
            enable_oom_recovery=True,
        )

        console.print(
            f"[dim]Vision device: {vision_embedder.device_info.device_type.value}[/dim]"
        )
        console.print(f"[dim]Batch size: {vision_embedder.batch_size}[/dim]")

    # Batch ingestion
    batch_ingester = BatchIngester(
        console=console,
        continue_on_error=not fail_fast,
        skip_duplicates=skip_duplicates,
    )

    with ProgressType() as progress:
        # Process each file
        results = []
        task = progress.add_task("Ingesting...", total=len(file_paths))

        for file_path in file_paths:
            try:
                progress.update(task, description=f"Processing {file_path.name}...")

                # Use the pdf command logic for each file
                # (simplified version without interactive prompts)
                from src.chunking.splitters import chunk_document
                from src.embeddings.factory import get_embedder
                from src.ingestion.loaders import load_document
                from src.storage.vector_store import VectorStore

                # Load and chunk
                document = load_document(file_path)
                document = chunk_document(document)

                # Check for duplicates
                vector_store = VectorStore()
                file_hash = document.metadata.file_hash
                existing = vector_store.get_documents_by_metadata(
                    where={"file_hash": file_hash}
                )

                if existing and existing.get("ids") and skip_duplicates:
                    # Skip duplicate
                    progress.update(task, advance=1)
                    continue

                # Generate text embeddings
                embedder = get_embedder()
                chunk_texts = [chunk.text for chunk in document.chunks]
                text_embeddings = embedder.embed_batch(chunk_texts)

                # Store text embeddings
                ids = [chunk.chunk_id for chunk in document.chunks]
                metadatas = []
                for chunk in document.chunks:
                    metadata = chunk.metadata.model_dump()
                    if "document_path" in metadata and hasattr(
                        metadata["document_path"], "__fspath__"
                    ):
                        metadata["document_path"] = str(metadata["document_path"])
                    metadata = {k: v for k, v in metadata.items() if v is not None}
                    metadatas.append(metadata)

                vector_store.add(
                    ids=ids,
                    embeddings=text_embeddings,
                    documents=chunk_texts,
                    metadatas=metadatas,
                )

                # Generate vision embeddings if enabled
                if vision and vision_embedder:
                    from pdf2image import convert_from_path

                    from src.storage.dual_storage import DualVectorStore

                    images = convert_from_path(str(file_path))
                    vision_embeddings = vision_embedder.embed_batch_images(images)

                    dual_store = DualVectorStore()
                    dual_store.add_vision_embeddings(
                        document_id=document.document_id,
                        page_embeddings=vision_embeddings,
                        document_path=file_path,
                    )

                progress.update(task, advance=1)

            except Exception as e:
                logger.error(f"Failed to process {file_path}: {e}")
                if fail_fast:
                    console.print(f"[bold red]✗[/bold red] Failed: {e}")
                    sys.exit(1)
                progress.update(task, advance=1)
                continue

    console.print("[bold green]✓[/bold green] Batch ingestion complete")
    console.print(f"  Processed: {len(file_paths)} documents")


@ingest.command()
def status() -> None:
    """Check ingestion status and statistics.

    \b
    Displays:
    - Total documents ingested
    - Total text chunks
    - Total vision embeddings (if any)
    - Storage size
    - Collection statistics

    \b
    Examples:
        ragged ingest status
    """
    from src.storage.dual_storage import DualVectorStore
    from src.storage.vector_store import VectorStore

    console.print("[bold blue]Ingestion Status:[/bold blue]")
    console.print()

    try:
        # Text collection statistics
        vector_store = VectorStore()
        text_count = vector_store.count()

        console.print("[bold]Text Collection:[/bold]")
        console.print(f"  Total chunks: {text_count}")

        # Get unique document count
        all_docs = vector_store.get_all_documents()
        if all_docs and all_docs.get("metadatas"):
            unique_docs = set(
                meta.get("document_id", "unknown") for meta in all_docs["metadatas"]
            )
            console.print(f"  Unique documents: {len(unique_docs)}")

        # Vision collection statistics (if exists)
        try:
            dual_store = DualVectorStore()
            vision_count = dual_store.count_vision_embeddings()

            if vision_count > 0:
                console.print()
                console.print("[bold]Vision Collection:[/bold]")
                console.print(f"  Total page embeddings: {vision_count}")

                # Get unique vision documents
                vision_docs = dual_store.get_all_vision_documents()
                if vision_docs and vision_docs.get("metadatas"):
                    unique_vision_docs = set(
                        meta.get("document_id", "unknown")
                        for meta in vision_docs["metadatas"]
                    )
                    console.print(f"  Unique documents: {len(unique_vision_docs)}")
        except Exception:
            # Vision collection might not exist yet
            pass

        # Storage information
        console.print()
        console.print("[bold]Storage:[/bold]")

        data_dir = Path("data")
        if data_dir.exists():
            # Calculate storage size
            total_size = sum(
                f.stat().st_size for f in data_dir.rglob("*") if f.is_file()
            )
            size_mb = total_size / (1024 * 1024)
            console.print(f"  Data directory: {data_dir}")
            console.print(f"  Size: {size_mb:.2f} MB")

    except Exception as e:
        console.print(f"[bold red]✗[/bold red] Failed to get status: {e}")
        logger.error(f"Status check failed: {e}", exc_info=True)
        sys.exit(1)
