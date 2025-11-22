"""Document ingestion command for ragged CLI."""

import sys
from pathlib import Path
from typing import Optional

import click

from src.cli.common import console, ProgressType
from src.utils.logging import get_logger

logger = get_logger(__name__)


@click.command()
@click.argument("path", type=click.Path(exists=True, path_type=Path))
@click.option("--format", "-f", type=str, help="Force document format (pdf, txt, md, html)")
@click.option("--recursive/--no-recursive", default=True, help="Scan subdirectories (default: True)")
@click.option("--max-depth", type=int, help="Maximum directory depth (unlimited by default)")
@click.option("--fail-fast", is_flag=True, help="Stop on first error instead of continuing")
@click.option(
    "--chunking-strategy",
    type=click.Choice(["fixed", "semantic", "hierarchical"], case_sensitive=False),
    help="Chunking strategy: 'fixed' (default, fast), 'semantic' (topic boundaries), or 'hierarchical' (parent-child)"
)
@click.option(
    "--auto-correct-pdf/--no-auto-correct-pdf",
    default=True,
    help="Automatically detect and correct PDF issues (rotation, duplicates, ordering) (default: enabled)"
)
def add(
    path: Path,
    format: Optional[str],
    recursive: bool,
    max_depth: Optional[int],
    fail_fast: bool,
    chunking_strategy: Optional[str],
    auto_correct_pdf: bool,
) -> None:
    """Ingest document(s) into the system.

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

    # PDF correction variables
    pdf_corrected = False
    pdf_analysis = None
    corrected_pdf_path = None

    try:
        # PDF Correction (v0.3.5): Analyze and correct PDFs before processing
        if auto_correct_pdf and path.suffix.lower() == ".pdf":
            import asyncio
            from src.correction import CorrectionPipeline, MetadataGenerator

            console.print("[dim]Analyzing PDF quality...[/dim]")

            with ProgressType() as progress:
                task = progress.add_task("Analyzing PDF...", total=100)

                # Create correction pipeline
                pipeline = CorrectionPipeline()

                # Analyze and correct PDF
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
                console.print(f"  [yellow]⚡ Auto-corrected:[/yellow] {successful}/{total} issues")

                if summary['issue_summary'] != "none":
                    console.print(f"  [dim]Issues: {summary['issue_summary']}[/dim]")

                # Use corrected PDF for processing
                path = corrected_pdf_path
                pdf_corrected = True
            elif pdf_analysis.issues:
                console.print(f"  [dim]Issues detected but not corrected: {summary['issue_summary']}[/dim]")

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

            # Chunk document (v0.3.3: support intelligent chunking strategies)
            progress.update(task, description="Chunking document...", advance=10)
            document = chunk_document(document, strategy=chunking_strategy)
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
            # Serialise Path objects to strings for ChromaDB
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

        # Generate PDF correction metadata (v0.3.5)
        if pdf_analysis is not None:
            try:
                from src.correction import MetadataGenerator

                # Create metadata directory
                metadata_dir = Path("data/documents/.ragged") / document.document_id
                metadata_dir.mkdir(parents=True, exist_ok=True)

                # Generate metadata files
                generator = MetadataGenerator(metadata_dir)
                metadata_files = generator.generate_all(pdf_analysis, pdf_correction if pdf_corrected else None)

                console.print(f"  [dim]Metadata: {len(metadata_files)} files generated[/dim]")
            except Exception as e:
                logger.warning(f"Failed to generate PDF metadata: {e}")

    except Exception as e:
        console.print(f"[bold red]✗[/bold red] Failed to ingest document: {e}")
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
