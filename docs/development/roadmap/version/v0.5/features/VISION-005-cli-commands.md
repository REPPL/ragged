# VISION-005: Multi-Modal CLI Commands

**Feature:** Comprehensive CLI for Vision-Enabled RAG
**Category:** User Interface
**Estimated Effort:** 16-22 hours
**Dependencies:** VISION-001, VISION-002, VISION-003, VISION-004
**Status:** Planned

---

## Overview

Extend ragged's CLI to expose all v0.5 multi-modal features through intuitive command-line interface. This includes ingestion with vision embeddings, multi-modal queries, GPU management, and system introspection.

**Design Principles:**
1. **Consistency:** Follow existing CLI patterns from v0.4.x
2. **Discoverability:** Helpful `--help` text and examples
3. **Flexibility:** Support both interactive and scripted usage
4. **Feedback:** Progress indicators for long-running operations
5. **Safety:** Confirmation prompts for destructive operations

---

## Command Structure

```
ragged/
├── ingest              # Document ingestion
│   ├── pdf             # PDF with optional vision embeddings
│   ├── batch           # Batch ingestion from directory
│   └── status          # Check ingestion progress
│
├── query               # Multi-modal queries
│   ├── text            # Text-only query (existing + visual boosting)
│   ├── image           # Image-only query (new)
│   ├── hybrid          # Text + image query (new)
│   └── interactive     # Interactive query mode (new)
│
├── gpu                 # GPU management
│   ├── list            # List available devices
│   ├── info            # Show device information
│   ├── stats           # Real-time memory statistics
│   └── benchmark       # Benchmark embedding generation
│
├── storage             # Storage management
│   ├── info            # Show storage statistics
│   ├── migrate         # Migrate v0.4 to v0.5 schema
│   └── vacuum          # Clean up orphaned embeddings
│
└── config              # Configuration management
    ├── show            # Display current configuration
    ├── set             # Set configuration value
    └── reset           # Reset to defaults
```

---

## Implementation Plan

### Phase 1: Ingestion Commands (5-7 hours)

#### Session 1.1: Enhanced PDF Ingestion (3-4h)

**Task:** Extend `ingest pdf` command with vision embedding options

**Implementation:**

```python
# src/cli/ingest.py

import click
from pathlib import Path
from typing import Optional
from loguru import logger

from ragged.ingestion.processor import DocumentProcessor
from ragged.embeddings.text_embedder import TextEmbedder
from ragged.embeddings.colpali_embedder import ColPaliEmbedder
from ragged.storage.dual_store import DualEmbeddingStore


@click.group()
def ingest():
    """Document ingestion commands."""
    pass


@ingest.command("pdf")
@click.argument("pdf_path", type=click.Path(exists=True))
@click.option(
    "--vision/--no-vision",
    default=False,
    help="Enable vision embeddings (requires GPU)"
)
@click.option(
    "--device",
    type=click.Choice(["cuda", "mps", "cpu", "auto"]),
    default="auto",
    help="Compute device for vision embeddings"
)
@click.option(
    "--batch-size",
    type=int,
    default=None,
    help="Batch size for vision embeddings (default: adaptive)"
)
@click.option(
    "--chunking",
    type=click.Choice(["fixed", "semantic", "hierarchical"]),
    default="fixed",
    help="Chunking strategy for text"
)
@click.option(
    "--collection",
    default="documents",
    help="ChromaDB collection name"
)
@click.option(
    "-v", "--verbose",
    is_flag=True,
    help="Enable verbose logging"
)
def pdf(
    pdf_path: str,
    vision: bool,
    device: str,
    batch_size: Optional[int],
    chunking: str,
    collection: str,
    verbose: bool
):
    """
    Ingest PDF document with optional vision embeddings.

    Examples:

        # Text-only ingestion (v0.4.x compatible)
        ragged ingest pdf document.pdf

        # Vision-enabled ingestion (GPU required)
        ragged ingest pdf document.pdf --vision

        # Vision with specific GPU
        ragged ingest pdf document.pdf --vision --device cuda:1

        # Custom chunking strategy
        ragged ingest pdf document.pdf --chunking semantic
    """
    if verbose:
        logger.enable("ragged")
    else:
        logger.disable("ragged")

    click.echo(f"Ingesting: {pdf_path}")

    # Initialise embedders
    text_embedder = TextEmbedder()

    vision_embedder = None
    if vision:
        click.echo(f"Initialising vision embedder on device: {device}")

        try:
            vision_embedder = ColPaliEmbedder(
                device=device if device != "auto" else None,
                batch_size=batch_size
            )
            click.echo(f"✓ Vision embedder ready: {vision_embedder.device_info}")

        except RuntimeError as e:
            click.echo(f"✗ Failed to initialise vision embedder: {e}", err=True)
            click.echo("Falling back to text-only ingestion.", err=True)
            vision_embedder = None

    # Initialise storage
    store = DualEmbeddingStore(collection_name=collection)

    # Create processor
    processor = DocumentProcessor(
        text_embedder=text_embedder,
        vision_embedder=vision_embedder,
        store=store,
        chunking_strategy=chunking
    )

    # Process document with progress indicator
    with click.progressbar(
        length=100,
        label="Processing document"
    ) as bar:
        try:
            doc_id = processor.process_document(
                Path(pdf_path),
                enable_vision=vision,
                progress_callback=lambda pct: bar.update(int(pct))
            )

            bar.update(100)  # Complete

        except Exception as e:
            click.echo(f"\n✗ Ingestion failed: {e}", err=True)
            return 1

    # Report results
    stats = store.get_by_document(doc_id)
    text_count = sum(
        1 for m in stats["metadatas"] if m["embedding_type"] == "text"
    )
    vision_count = sum(
        1 for m in stats["metadatas"] if m["embedding_type"] == "vision"
    )

    click.echo(f"\n✓ Document ingested: {doc_id}")
    click.echo(f"  Text embeddings: {text_count}")
    click.echo(f"  Vision embeddings: {vision_count}")

    return 0


@ingest.command("batch")
@click.argument("directory", type=click.Path(exists=True, file_okay=False))
@click.option(
    "--vision/--no-vision",
    default=False,
    help="Enable vision embeddings for all PDFs"
)
@click.option(
    "--device",
    type=click.Choice(["cuda", "mps", "cpu", "auto"]),
    default="auto",
    help="Compute device for vision embeddings"
)
@click.option(
    "--pattern",
    default="*.pdf",
    help="Glob pattern for file matching"
)
@click.option(
    "--recursive/--no-recursive",
    default=False,
    help="Recursively search subdirectories"
)
@click.option(
    "--collection",
    default="documents",
    help="ChromaDB collection name"
)
def batch(
    directory: str,
    vision: bool,
    device: str,
    pattern: str,
    recursive: bool,
    collection: str
):
    """
    Batch ingest all PDFs from a directory.

    Examples:

        # Ingest all PDFs from directory
        ragged ingest batch ./documents/

        # Recursive ingestion with vision
        ragged ingest batch ./documents/ --vision --recursive

        # Custom file pattern
        ragged ingest batch ./docs/ --pattern "report_*.pdf"
    """
    from glob import glob

    directory_path = Path(directory)

    # Find all matching files
    if recursive:
        pdf_files = list(directory_path.rglob(pattern))
    else:
        pdf_files = list(directory_path.glob(pattern))

    if not pdf_files:
        click.echo(f"No files matching '{pattern}' found in {directory}")
        return 1

    click.echo(f"Found {len(pdf_files)} files to ingest")

    # Confirm before proceeding
    if not click.confirm("Proceed with batch ingestion?"):
        click.echo("Aborted.")
        return 0

    # Initialise components (reuse across files)
    text_embedder = TextEmbedder()

    vision_embedder = None
    if vision:
        try:
            vision_embedder = ColPaliEmbedder(device=device if device != "auto" else None)
            click.echo(f"✓ Vision embedder initialised: {vision_embedder.device_info}")
        except RuntimeError as e:
            click.echo(f"✗ Vision embedder failed: {e}", err=True)
            return 1

    store = DualEmbeddingStore(collection_name=collection)
    processor = DocumentProcessor(
        text_embedder=text_embedder,
        vision_embedder=vision_embedder,
        store=store
    )

    # Process each file
    succeeded = 0
    failed = 0

    with click.progressbar(pdf_files, label="Ingesting PDFs") as files:
        for pdf_file in files:
            try:
                processor.process_document(pdf_file, enable_vision=vision)
                succeeded += 1

            except Exception as e:
                logger.error(f"Failed to process {pdf_file}: {e}")
                failed += 1

    # Summary
    click.echo(f"\n✓ Batch ingestion complete:")
    click.echo(f"  Succeeded: {succeeded}")
    click.echo(f"  Failed: {failed}")

    return 0 if failed == 0 else 1


@ingest.command("status")
@click.option(
    "--collection",
    default="documents",
    help="ChromaDB collection name"
)
def status(collection: str):
    """Show ingestion status and statistics."""
    from ragged.storage.dual_store import DualEmbeddingStore

    store = DualEmbeddingStore(collection_name=collection)

    # Get all embeddings
    all_results = store.collection.get()

    if not all_results["ids"]:
        click.echo(f"Collection '{collection}' is empty.")
        return 0

    # Count by type
    text_count = sum(
        1 for m in all_results["metadatas"] if m.get("embedding_type") == "text"
    )
    vision_count = sum(
        1 for m in all_results["metadatas"] if m.get("embedding_type") == "vision"
    )

    # Count unique documents
    unique_docs = set(m["document_id"] for m in all_results["metadatas"])

    click.echo(f"Collection: {collection}")
    click.echo(f"  Documents: {len(unique_docs)}")
    click.echo(f"  Text embeddings: {text_count}")
    click.echo(f"  Vision embeddings: {vision_count}")
    click.echo(f"  Total embeddings: {len(all_results['ids'])}")

    return 0
```

**Deliverables:**
- `src/cli/ingest.py` (~350 lines)
- Commands: `pdf`, `batch`, `status`
- Progress indicators and error handling

**Time:** 3-4 hours

---

#### Session 1.2: Testing Ingestion Commands (2-3h)

**Test Coverage:**
1. PDF ingestion with/without vision
2. Batch ingestion
3. Device selection and fallback
4. Error handling (invalid paths, GPU unavailable)
5. Progress callback integration

**Time:** 2-3 hours

---

### Phase 2: Query Commands (4-6 hours)

#### Session 2.1: Enhanced Query Commands (3-4h)

**Task:** Implement text, image, and hybrid query commands

**Implementation:**

```python
# src/cli/query.py

import click
from pathlib import Path
from typing import Optional
from PIL import Image

from ragged.retrieval.vision_retriever import VisionRetriever


@click.group()
def query():
    """Multi-modal query commands."""
    pass


@query.command("text")
@click.argument("query_text")
@click.option("-n", "--num-results", default=10, help="Number of results")
@click.option("--boost-diagrams", is_flag=True, help="Boost results with diagrams")
@click.option("--boost-tables", is_flag=True, help="Boost results with tables")
@click.option("--collection", default="documents", help="Collection to query")
@click.option("--show-metadata", is_flag=True, help="Show full metadata")
def text(
    query_text: str,
    num_results: int,
    boost_diagrams: bool,
    boost_tables: bool,
    collection: str,
    show_metadata: bool
):
    """
    Query documents by text.

    Examples:

        ragged query text "database architecture"

        ragged query text "authentication flow" --boost-diagrams

        ragged query text "API design" -n 20 --show-metadata
    """
    from ragged.storage.dual_store import DualEmbeddingStore

    store = DualEmbeddingStore(collection_name=collection)
    retriever = VisionRetriever(store=store)

    click.echo(f"Searching for: \"{query_text}\"")

    response = retriever.query(
        text=query_text,
        n_results=num_results,
        boost_diagrams=boost_diagrams,
        boost_tables=boost_tables
    )

    click.echo(
        f"\nFound {response.total_results} results "
        f"in {response.execution_time_ms:.2f}ms\n"
    )

    for result in response.results:
        click.echo(f"{result.rank}. {result.document_id}")
        click.echo(f"   Score: {result.score:.4f}")
        click.echo(f"   Type: {result.embedding_type}")

        if show_metadata:
            for key, value in result.metadata.items():
                if key not in ["document_id", "embedding_type"]:
                    click.echo(f"   {key}: {value}")

        click.echo()

    return 0


@query.command("image")
@click.argument("image_path", type=click.Path(exists=True))
@click.option("-n", "--num-results", default=10, help="Number of results")
@click.option("--collection", default="documents", help="Collection to query")
def image(image_path: str, num_results: int, collection: str):
    """
    Query documents by visual similarity.

    Upload an image (screenshot, diagram, chart) and find visually similar
    pages in your document collection.

    Examples:

        ragged query image diagram_sketch.png

        ragged query image screenshot.jpg -n 5
    """
    from ragged.storage.dual_store import DualEmbeddingStore

    store = DualEmbeddingStore(collection_name=collection)
    retriever = VisionRetriever(store=store)

    # Verify vision embeddings exist
    test_results = store.collection.get(limit=1, where={"embedding_type": "vision"})
    if not test_results["ids"]:
        click.echo(
            "⚠ No vision embeddings found in collection.\n"
            "Did you ingest documents with --vision flag?",
            err=True
        )
        return 1

    click.echo(f"Searching for images similar to: {image_path}")

    try:
        response = retriever.query(
            image=Path(image_path),
            n_results=num_results
        )

    except RuntimeError as e:
        click.echo(f"✗ Vision query failed: {e}", err=True)
        click.echo("Ensure GPU is available and vision embeddings are enabled.", err=True)
        return 1

    click.echo(
        f"\nFound {response.total_results} results "
        f"in {response.execution_time_ms:.2f}ms\n"
    )

    for result in response.results:
        click.echo(f"{result.rank}. {result.document_id}")
        click.echo(f"   Score: {result.score:.4f}")
        click.echo(f"   Page: {result.metadata.get('page_number', 'N/A')}")
        click.echo()

    return 0


@query.command("hybrid")
@click.argument("query_text")
@click.argument("image_path", type=click.Path(exists=True))
@click.option("-n", "--num-results", default=10, help="Number of results")
@click.option("--text-weight", default=0.5, type=float, help="Text score weight (0-1)")
@click.option("--vision-weight", default=0.5, type=float, help="Vision score weight (0-1)")
@click.option("--collection", default="documents", help="Collection to query")
def hybrid(
    query_text: str,
    image_path: str,
    num_results: int,
    text_weight: float,
    vision_weight: float,
    collection: str
):
    """
    Query documents with both text and image.

    Combine text and visual search for more precise results. Useful when you
    want content matching both semantic meaning and visual appearance.

    Examples:

        ragged query hybrid "network topology" diagram.png

        ragged query hybrid "API flow" sketch.jpg --text-weight 0.7 --vision-weight 0.3
    """
    from ragged.storage.dual_store import DualEmbeddingStore

    store = DualEmbeddingStore(collection_name=collection)
    retriever = VisionRetriever(store=store)

    click.echo(f"Searching for: \"{query_text}\" + {image_path}")
    click.echo(f"Weights: text={text_weight:.2f}, vision={vision_weight:.2f}\n")

    try:
        response = retriever.query(
            text=query_text,
            image=Path(image_path),
            n_results=num_results,
            text_weight=text_weight,
            vision_weight=vision_weight
        )

    except RuntimeError as e:
        click.echo(f"✗ Hybrid query failed: {e}", err=True)
        return 1

    click.echo(
        f"Found {response.total_results} results "
        f"in {response.execution_time_ms:.2f}ms\n"
    )

    for result in response.results:
        click.echo(f"{result.rank}. {result.document_id}")
        click.echo(f"   Combined score: {result.score:.4f}")
        click.echo(f"   Type: {result.embedding_type}")
        click.echo()

    return 0


@query.command("interactive")
@click.option("--collection", default="documents", help="Collection to query")
def interactive(collection: str):
    """
    Interactive query mode (REPL).

    Start an interactive session for rapid querying without re-typing
    the command prefix each time.

    Example:

        ragged query interactive

        > text: database design
        > image: diagram.png
        > hybrid: authentication flow, sketch.jpg
        > exit
    """
    from ragged.storage.dual_store import DualEmbeddingStore

    store = DualEmbeddingStore(collection_name=collection)
    retriever = VisionRetriever(store=store)

    click.echo("Interactive query mode (type 'help' for commands, 'exit' to quit)\n")

    while True:
        try:
            user_input = click.prompt("ragged>", type=str)

        except (EOFError, KeyboardInterrupt):
            click.echo("\nExiting.")
            break

        if not user_input.strip():
            continue

        command_parts = user_input.strip().split(":", 1)
        command = command_parts[0].strip().lower()

        if command == "exit" or command == "quit":
            break

        elif command == "help":
            click.echo("Commands:")
            click.echo("  text: <query>              - Text query")
            click.echo("  image: <path>              - Image query")
            click.echo("  hybrid: <query>, <path>    - Hybrid query")
            click.echo("  exit                       - Exit interactive mode")
            click.echo()

        elif command == "text":
            if len(command_parts) < 2:
                click.echo("Usage: text: <query>")
                continue

            query_text = command_parts[1].strip()
            _run_text_query(retriever, query_text)

        elif command == "image":
            if len(command_parts) < 2:
                click.echo("Usage: image: <path>")
                continue

            image_path = command_parts[1].strip()
            _run_image_query(retriever, image_path)

        elif command == "hybrid":
            if len(command_parts) < 2:
                click.echo("Usage: hybrid: <query>, <image_path>")
                continue

            parts = command_parts[1].split(",", 1)
            if len(parts) != 2:
                click.echo("Usage: hybrid: <query>, <image_path>")
                continue

            query_text = parts[0].strip()
            image_path = parts[1].strip()
            _run_hybrid_query(retriever, query_text, image_path)

        else:
            click.echo(f"Unknown command: {command}")
            click.echo("Type 'help' for available commands.")

    return 0


def _run_text_query(retriever, query_text: str):
    """Helper: Execute text query in interactive mode."""
    response = retriever.query(text=query_text, n_results=5)

    for result in response.results:
        click.echo(f"{result.rank}. {result.document_id} (score: {result.score:.4f})")

    click.echo()


def _run_image_query(retriever, image_path: str):
    """Helper: Execute image query in interactive mode."""
    try:
        response = retriever.query(image=Path(image_path), n_results=5)

        for result in response.results:
            click.echo(
                f"{result.rank}. {result.document_id} "
                f"(page: {result.metadata.get('page_number', 'N/A')}, "
                f"score: {result.score:.4f})"
            )

        click.echo()

    except Exception as e:
        click.echo(f"Error: {e}")


def _run_hybrid_query(retriever, query_text: str, image_path: str):
    """Helper: Execute hybrid query in interactive mode."""
    try:
        response = retriever.query(
            text=query_text,
            image=Path(image_path),
            n_results=5
        )

        for result in response.results:
            click.echo(f"{result.rank}. {result.document_id} (score: {result.score:.4f})")

        click.echo()

    except Exception as e:
        click.echo(f"Error: {e}")
```

**Deliverables:**
- `src/cli/query.py` (~400 lines)
- Commands: `text`, `image`, `hybrid`, `interactive`
- REPL mode for rapid querying

**Time:** 3-4 hours

---

#### Session 2.2: Testing Query Commands (1-2h)

**Test Coverage:**
1. Text query with visual boosting
2. Image query execution
3. Hybrid query with weight parameters
4. Interactive mode (basic flow)

**Time:** 1-2 hours

---

### Phase 3: GPU and Storage Management Commands (4-6 hours)

#### Session 3.1: GPU Management Commands (2-3h)

**Implementation:**

```python
# src/cli/gpu.py

import click
from ragged.gpu.device_manager import DeviceManager


@click.group()
def gpu():
    """GPU management and diagnostics."""
    pass


@gpu.command("list")
def list_devices():
    """List all available compute devices."""
    manager = DeviceManager()

    click.echo("Available devices:\n")

    for i, device in enumerate(manager._available_devices):
        click.echo(f"{i + 1}. {device}")

        if device.total_memory:
            mem_gb = device.total_memory / (1024**3)
            click.echo(f"   Memory: {mem_gb:.2f} GB")

        if device.compute_capability:
            click.echo(f"   Compute capability: {device.compute_capability}")

        click.echo()

    return 0


@gpu.command("info")
@click.option("--device", default=None, help="Device to inspect (e.g., 'cuda:0')")
def info(device: str):
    """Show detailed device information."""
    manager = DeviceManager()

    device_info = manager.get_optimal_device(device_hint=device)

    click.echo(f"Device: {device_info}\n")

    if device_info.total_memory:
        memory_info = manager.get_device_memory_info(device_info)

        total_gb = memory_info["total"] / (1024**3)
        allocated_gb = memory_info["allocated"] / (1024**3)
        free_gb = memory_info["free"] / (1024**3)

        click.echo("Memory:")
        click.echo(f"  Total: {total_gb:.2f} GB")
        click.echo(f"  Allocated: {allocated_gb:.2f} GB")
        click.echo(f"  Free: {free_gb:.2f} GB")

    return 0


@gpu.command("stats")
@click.option("--device", default=None, help="Device to monitor")
@click.option("--interval", default=1.0, type=float, help="Update interval (seconds)")
def stats(device: str, interval: float):
    """Show real-time GPU memory statistics."""
    import time

    manager = DeviceManager()
    device_info = manager.get_optimal_device(device_hint=device)

    click.echo(f"Monitoring {device_info} (Ctrl+C to stop)\n")

    try:
        while True:
            if device_info.total_memory:
                memory_info = manager.get_device_memory_info(device_info)

                allocated_gb = memory_info["allocated"] / (1024**3)
                free_gb = memory_info["free"] / (1024**3)
                util_pct = (memory_info["allocated"] / memory_info["total"]) * 100

                click.echo(
                    f"\r[{time.strftime('%H:%M:%S')}] "
                    f"Allocated: {allocated_gb:.2f} GB | "
                    f"Free: {free_gb:.2f} GB | "
                    f"Utilisation: {util_pct:.1f}%",
                    nl=False
                )

            time.sleep(interval)

    except KeyboardInterrupt:
        click.echo("\n\nStopped.")

    return 0


@gpu.command("benchmark")
@click.option("--device", default=None, help="Device to benchmark")
@click.option("--batch-size", default=4, type=int, help="Batch size")
def benchmark(device: str, batch_size: int):
    """Benchmark vision embedding generation performance."""
    import time
    import numpy as np
    from PIL import Image

    from ragged.embeddings.colpali_embedder import ColPaliEmbedder

    click.echo(f"Initialising ColPali on device: {device or 'auto'}")

    try:
        embedder = ColPaliEmbedder(
            device=device,
            batch_size=batch_size
        )

    except RuntimeError as e:
        click.echo(f"✗ Failed to initialise embedder: {e}", err=True)
        return 1

    click.echo(f"✓ Using device: {embedder.device_info}\n")

    # Create synthetic test images
    test_images = [
        Image.new("RGB", (800, 1200), color=(255, 255, 255))
        for _ in range(batch_size * 5)  # 5 batches
    ]

    click.echo(f"Benchmarking {len(test_images)} images (batch_size={batch_size})...")

    start_time = time.time()

    try:
        embeddings = embedder.embed_batch(test_images)

    except Exception as e:
        click.echo(f"✗ Benchmark failed: {e}", err=True)
        return 1

    elapsed = time.time() - start_time

    # Report metrics
    images_per_sec = len(test_images) / elapsed
    ms_per_image = (elapsed / len(test_images)) * 1000

    click.echo(f"\n✓ Benchmark complete:")
    click.echo(f"  Total time: {elapsed:.2f}s")
    click.echo(f"  Images/second: {images_per_sec:.2f}")
    click.echo(f"  ms/image: {ms_per_image:.2f}")

    return 0
```

**Deliverables:**
- `src/cli/gpu.py` (~200 lines)
- Commands: `list`, `info`, `stats`, `benchmark`

**Time:** 2-3 hours

---

#### Session 3.2: Storage Management Commands (2-3h)

**Implementation:**

```python
# src/cli/storage.py

import click
from ragged.storage.dual_store import DualEmbeddingStore
from ragged.storage.migration import StorageMigration


@click.group()
def storage():
    """Storage management commands."""
    pass


@storage.command("info")
@click.option("--collection", default="documents", help="Collection name")
def info(collection: str):
    """Show storage statistics."""
    store = DualEmbeddingStore(collection_name=collection)

    all_results = store.collection.get()

    if not all_results["ids"]:
        click.echo(f"Collection '{collection}' is empty.")
        return 0

    # Statistics
    text_count = sum(
        1 for m in all_results["metadatas"] if m.get("embedding_type") == "text"
    )
    vision_count = sum(
        1 for m in all_results["metadatas"] if m.get("embedding_type") == "vision"
    )

    unique_docs = set(m["document_id"] for m in all_results["metadatas"])

    click.echo(f"Collection: {collection}")
    click.echo(f"  Schema version: v0.5")
    click.echo(f"  Documents: {len(unique_docs)}")
    click.echo(f"  Text embeddings: {text_count}")
    click.echo(f"  Vision embeddings: {vision_count}")
    click.echo(f"  Total embeddings: {len(all_results['ids'])}")

    return 0


@storage.command("migrate")
@click.option("--collection", default="documents", help="Collection to migrate")
@click.option("--dry-run", is_flag=True, help="Preview changes without applying")
def migrate(collection: str, dry_run: bool):
    """Migrate v0.4 collection to v0.5 dual-embedding schema."""
    import chromadb

    client = chromadb.Client()
    migration = StorageMigration(client)

    # Detect schema version
    try:
        schema_version = migration.detect_schema_version(collection)

    except ValueError as e:
        click.echo(f"✗ {e}", err=True)
        return 1

    if schema_version == "v0.5":
        click.echo(f"Collection '{collection}' is already v0.5 schema.")
        return 0

    click.echo(f"Detected schema version: {schema_version}")
    click.echo(f"Migrating to: v0.5")

    if dry_run:
        click.echo("\n[DRY RUN - No changes will be made]")

    # Confirm before proceeding
    if not dry_run and not click.confirm("\nProceed with migration?"):
        click.echo("Aborted.")
        return 0

    # Run migration
    try:
        stats = migration.migrate_collection(
            collection_name=collection,
            dry_run=dry_run
        )

    except Exception as e:
        click.echo(f"\n✗ Migration failed: {e}", err=True)
        return 1

    # Report results
    click.echo(f"\n✓ Migration {'preview' if dry_run else 'complete'}:")
    click.echo(f"  Embeddings migrated: {stats['embeddings_migrated']}")
    click.echo(f"  IDs renamed: {stats['ids_renamed']}")
    click.echo(f"  Metadata updated: {stats['metadata_updated']}")

    return 0


@storage.command("vacuum")
@click.option("--collection", default="documents", help="Collection to clean")
def vacuum(collection: str):
    """Remove orphaned embeddings and optimize storage."""
    click.echo(f"Vacuuming collection: {collection}")
    click.echo("(Not yet implemented)")

    return 0
```

**Deliverables:**
- `src/cli/storage.py` (~150 lines)
- Commands: `info`, `migrate`, `vacuum` (stub)

**Time:** 2-3 hours

---

### Phase 4: Testing and Integration (3-4 hours)

#### Session 4.1: CLI Integration Tests (2-3h)

**Test Coverage:**
1. End-to-end ingestion via CLI
2. Query commands with actual data
3. GPU commands on available devices
4. Storage migration workflow

**Time:** 2-3 hours

---

#### Session 4.2: Documentation and Help Text (1h)

**Task:** Ensure all commands have complete help text and examples

**Time:** 1 hour

---

## Success Criteria

**Functional Requirements:**
- [ ] Ingestion: `pdf`, `batch`, `status`
- [ ] Query: `text`, `image`, `hybrid`, `interactive`
- [ ] GPU: `list`, `info`, `stats`, `benchmark`
- [ ] Storage: `info`, `migrate`, `vacuum`
- [ ] All commands have `--help` text with examples
- [ ] Progress indicators for long-running operations
- [ ] Confirmation prompts for destructive operations

**Quality Requirements:**
- [ ] 80%+ test coverage for CLI module
- [ ] Consistent error handling and messages
- [ ] British English in all user-facing text
- [ ] Examples in help text for each command

**User Experience:**
- [ ] Intuitive command structure
- [ ] Helpful error messages with suggestions
- [ ] Progress feedback for operations >2s
- [ ] Coloured output (optional, configurable)

---

## Dependencies

**Required:**
- click >= 8.0 (CLI framework)
- All VISION-001 through VISION-004 features

---

## Known Limitations

1. **Interactive Mode:** Basic REPL, no command history or autocomplete (future: use prompt_toolkit)
2. **Coloured Output:** Not implemented (future: use click.style for better UX)
3. **Vacuum Command:** Stub implementation (requires orphaned embedding detection logic)

---

## Future Enhancements (Post-v0.5)

1. **Rich CLI:** Use `rich` library for better formatting, tables, progress bars
2. **Command Aliases:** Short aliases for common commands (e.g., `rg q t` for `ragged query text`)
3. **Shell Completion:** Bash/Zsh completion scripts
4. **Export Results:** Export query results to JSON/CSV

---

**Status:** Planned
**Estimated Total Effort:** 16-22 hours
