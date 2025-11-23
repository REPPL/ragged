"""Scan processing CLI commands for ragged (v0.4.9).

Commands for processing messy scanned documents into perfect PDFs and markdown.

Commands:
    ragged scan process PATH [OPTIONS]  - Process messy scans

v0.4.9: Initial scan processing CLI
"""

import asyncio
import logging
from pathlib import Path

import click
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from ragged.config.settings import get_settings
from ragged.processing.metadata_extractor import MetadataExtractor
from ragged.processing.output_organizer import OutputOrganizer
from ragged.processing.scan_preprocessor import ScanPreprocessor
from ragged.utils.logging import get_logger
from ragged.validation.path_validator import PathTraversalError, PathValidator

logger = get_logger(__name__)
console = Console()


@click.group()
def scan():
    """Process messy scanned documents into perfect PDFs."""
    pass


@scan.command()
@click.argument("path", type=click.Path(exists=True, path_type=Path))
@click.option(
    "--output-dir",
    type=click.Path(path_type=Path),
    default=None,
    help="Output directory (default: ~/.ragged/documents)",
)
@click.option(
    "--ocr-engine",
    type=click.Choice(["auto", "easyocr", "paddleocr"]),
    default="auto",
    help="OCR engine to use (default: auto-select based on quality)",
)
@click.option(
    "--ocr-language",
    default="eng",
    help="OCR language (ISO 639-2/3 code, default: eng)",
)
@click.option(
    "--force-ocr/--no-force-ocr",
    default=False,
    help="Force full-page OCR even if text layer exists",
)
@click.option(
    "--reorder-pages/--no-reorder-pages",
    default=True,
    help="Automatically reorder pages (default: yes)",
)
@click.option(
    "--export-markdown/--no-export-markdown",
    default=True,
    help="Export to markdown (default: yes)",
)
@click.option(
    "--keep-original/--no-keep-original",
    default=True,
    help="Keep backup of original file (default: yes)",
)
@click.option(
    "--batch/--no-batch",
    default=False,
    help="Process entire directory recursively (default: no)",
)
@click.option(
    "--dry-run/--no-dry-run",
    default=False,
    help="Preview without processing (default: no)",
)
@click.option(
    "--gpu/--no-gpu",
    default=False,
    help="Prefer GPU for OCR if available (default: no)",
)
def process(
    path,
    output_dir,
    ocr_engine,
    ocr_language,
    force_ocr,
    reorder_pages,
    export_markdown,
    keep_original,
    batch,
    dry_run,
    gpu,
):
    """Process messy scans into perfect PDFs and markdown.

    PATH can be:
    - Single PDF file
    - Single image file (JPG, PNG, TIFF, BMP)
    - Folder containing images
    - Folder containing PDFs
    - Folder with mixed images and PDFs

    Examples:

        # Process single PDF
        ragged scan process ~/scans/book.pdf

        # Process folder of images
        ragged scan process ~/scans/book-folder/

        # Use PaddleOCR for difficult scans
        ragged scan process messy-scan.pdf --ocr-engine paddleocr

        # Preview without processing
        ragged scan process ~/scans/ --dry-run

        # Batch process entire directory
        ragged scan process ~/scans/ --batch
    """
    settings = get_settings()

    # v0.5.8 HIGH-5: Validate input path for security (prevent path traversal)
    try:
        validator = PathValidator(
            allowed_base=None,  # Allow scanning files anywhere
            allow_absolute=True,  # Users commonly use absolute paths
            allow_symlinks=False,  # Block symlinks for security
        )
        path = validator.validate(path)
    except PathTraversalError as e:
        console.print(f"[bold red]✗ Security Error:[/bold red] {e}")
        logger.error(f"Path validation failed: {e}")
        sys.exit(1)

    # v0.5.8 HIGH-5: Validate output directory if provided
    if output_dir:
        try:
            validator_output = PathValidator(
                allowed_base=None,  # Allow output anywhere
                allow_absolute=True,  # Users commonly use absolute paths
                allow_symlinks=False,  # Block symlinks for security
            )
            output_dir = validator_output.validate(output_dir, create_if_missing=True)
        except PathTraversalError as e:
            console.print(f"[bold red]✗ Security Error:[/bold red] {e}")
            logger.error(f"Output directory validation failed: {e}")
            sys.exit(1)

    if dry_run:
        console.print(f"[yellow]DRY RUN: Would process {path}[/yellow]")
        _preview_processing(path, batch)
        return

    console.print(f"[bold blue]Processing:[/bold blue] {path}")

    try:
        # Phase 1: Preprocess (OCR, merge, sort)
        console.print("\n[bold]Phase 1: Preprocessing[/bold]")
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Preprocessing scans...", total=None)

            preprocessor = ScanPreprocessor(
                apply_ocr=force_ocr or True,  # Always apply if needed
                preprocess_images=True,
                ocr_language=ocr_language,
                prefer_gpu=gpu,
            )

            # Determine output path for preprocessed file
            if output_dir:
                preprocessed_output = Path(output_dir) / "preprocessed.pdf"
            else:
                preprocessed_output = path.parent / f"{path.stem}_preprocessed.pdf"

            preprocess_result = preprocessor.preprocess(path, preprocessed_output)

            progress.update(task, completed=True)

        # Show preprocessing results
        _display_preprocess_results(preprocess_result)

        # Phase 2: Auto-correction (rotation, reordering, duplicates)
        console.print("\n[bold]Phase 2: Auto-Correction[/bold]")

        corrected_path = preprocess_result.output_path

        if reorder_pages:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
            ) as progress:
                task = progress.add_task("Applying corrections...", total=None)

                # Use existing correction pipeline
                from ragged.correction.pipeline import CorrectionPipeline

                pipeline = CorrectionPipeline()

                # Run async correction
                corrected_output = corrected_path.parent / f"{corrected_path.stem}_corrected.pdf"
                analysis, correction = asyncio.run(
                    pipeline.analyze_and_correct(corrected_path, corrected_output)
                )

                if correction.success:
                    corrected_path = correction.output_path
                    console.print(
                        f"[green]✓[/green] Applied corrections: "
                        f"{len(correction.corrections_applied)} changes"
                    )
                else:
                    console.print("[yellow]⚠[/yellow] Corrections failed, using preprocessed PDF")

                progress.update(task, completed=True)

        # Phase 3: Extract metadata
        console.print("\n[bold]Phase 3: Metadata Extraction[/bold]")
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Extracting metadata...", total=None)

            extractor = MetadataExtractor(
                titlepage_pages=3,
                ocr_language=ocr_language,
                use_vision=False,  # Not implemented yet
                prefer_gpu=gpu,
            )

            metadata_result = extractor.extract(corrected_path)

            progress.update(task, completed=True)

        # Show metadata results
        _display_metadata(metadata_result)

        # Phase 4: Export markdown (if enabled)
        markdown_path = None
        if export_markdown:
            console.print("\n[bold]Phase 4: Markdown Export[/bold]")
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
            ) as progress:
                task = progress.add_task("Exporting to markdown...", total=None)

                from ragged.processing.docling_processor import DoclingProcessor
                from ragged.processing.base import ProcessorConfig

                config = ProcessorConfig(
                    processor_type="docling",
                    enable_layout_analysis=True,
                    enable_table_extraction=True,
                )
                processor = DoclingProcessor(config)

                processed = processor.process(corrected_path)
                markdown_path = corrected_path.parent / f"{corrected_path.stem}.md"
                markdown_path.write_text(processed.content, encoding="utf-8")

                console.print(f"[green]✓[/green] Exported markdown: {markdown_path.name}")

                progress.update(task, completed=True)

        # Phase 5: Organize outputs
        console.print("\n[bold]Phase 5: Output Organization[/bold]")
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Organizing outputs...", total=None)

            organizer = OutputOrganizer(
                output_dir=output_dir,
                naming_convention="title-author-year",
                keep_originals=keep_original,
                track_lineage=True,
            )

            organized = organizer.organize(
                original=path,
                corrected=corrected_path,
                markdown=markdown_path,
                metadata={
                    "title": metadata_result.title,
                    "author": metadata_result.author,
                    "year": metadata_result.year,
                    "publisher": metadata_result.publisher,
                },
            )

            progress.update(task, completed=True)

        # Display final results
        console.print("\n[bold green]✓ Processing Complete[/bold green]")
        _display_final_results(organized)

    except Exception as e:
        logger.error(f"Scan processing failed: {e}")
        console.print(f"\n[bold red]✗ Error:[/bold red] {e}")
        raise click.ClickException(str(e))


def _preview_processing(path: Path, batch: bool) -> None:
    """Preview what would be processed (dry run).

    Args:
        path: Input path
        batch: Batch mode enabled
    """
    from ragged.processing.scan_preprocessor import ScanPreprocessor

    preprocessor = ScanPreprocessor()
    input_type = preprocessor._detect_input_type(path)

    table = Table(title="Processing Preview")
    table.add_column("Property", style="cyan")
    table.add_column("Value", style="white")

    table.add_row("Input Path", str(path))
    table.add_row("Input Type", input_type.value.replace("_", " ").title())

    if path.is_dir():
        # Count files
        from ragged.processing.scan_preprocessor import ScanPreprocessor

        images = [
            f
            for f in path.rglob("*")
            if f.suffix.lower() in ScanPreprocessor.IMAGE_EXTENSIONS
        ]
        pdfs = [f for f in path.rglob("*") if f.suffix.lower() == ScanPreprocessor.PDF_EXTENSION]

        table.add_row("Images Found", str(len(images)))
        table.add_row("PDFs Found", str(len(pdfs)))
        table.add_row("Total Files", str(len(images) + len(pdfs)))

    console.print(table)


def _display_preprocess_results(result) -> None:
    """Display preprocessing results.

    Args:
        result: PreprocessResult from ScanPreprocessor
    """
    table = Table(title="Preprocessing Results")
    table.add_column("Property", style="cyan")
    table.add_column("Value", style="white")

    table.add_row("Output PDF", str(result.output_path.name))
    table.add_row("Input Type", result.input_type.value.replace("_", " ").title())
    table.add_row("Files Processed", str(result.num_files_processed))
    table.add_row("OCR Applied", "Yes" if result.ocr_applied else "No")
    table.add_row("Image Preprocessing", "Yes" if result.preprocessing_applied else "No")
    table.add_row("Processing Time", f"{result.processing_time_seconds:.2f}s")

    if result.warnings:
        table.add_row("Warnings", str(len(result.warnings)))

    console.print(table)


def _display_metadata(metadata) -> None:
    """Display extracted metadata.

    Args:
        metadata: ExtractedMetadata from MetadataExtractor
    """
    table = Table(title="Extracted Metadata")
    table.add_column("Field", style="cyan")
    table.add_column("Value", style="white")

    table.add_row("Title", metadata.title)
    table.add_row("Author", metadata.author or "[dim]Unknown[/dim]")
    table.add_row("Year", str(metadata.year) if metadata.year else "[dim]Unknown[/dim]")
    table.add_row("Publisher", metadata.publisher or "[dim]Unknown[/dim]")
    table.add_row("Confidence", f"{metadata.confidence:.1%}")
    table.add_row("Method", metadata.method)

    console.print(table)


def _display_final_results(organized) -> None:
    """Display final organized output paths.

    Args:
        organized: OrganizedOutput from OutputOrganizer
    """
    table = Table(title="Final Output")
    table.add_column("Type", style="cyan")
    table.add_column("Path", style="white")

    table.add_row("Original Backup", str(organized.original_path))
    table.add_row("Corrected PDF", str(organized.corrected_path))

    if organized.markdown_path:
        table.add_row("Markdown", str(organized.markdown_path))

    table.add_row("Lineage ID", organized.lineage_id)

    console.print(table)
    console.print(
        f"\n[green]Your processed document is ready at:[/green]\n"
        f"[bold]{organized.corrected_path}[/bold]"
    )


if __name__ == "__main__":
    scan()
