"""Export and import utilities for ragged CLI.

Enables data backup, migration, and portability.
"""

import json
import shutil
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import click

from src import __version__
from src.cli.common import console
from src.config.settings import get_settings
from src.utils.logging import get_logger

logger = get_logger(__name__)


@click.group()
def export() -> None:
    """Export and import data for backup and migration.

    Backup your documents, embeddings, and configuration for safekeeping
    or migration to another system.
    """
    pass


@export.command("backup")
@click.option(
    "--output",
    "-o",
    "output_file",
    type=click.Path(),
    help="Output file path (default: auto-generated timestamp)",
)
@click.option(
    "--include-embeddings",
    is_flag=True,
    default=True,
    help="Include embeddings in export (default: yes)",
)
@click.option(
    "--include-config",
    is_flag=True,
    default=True,
    help="Include configuration in export (default: yes)",
)
@click.option(
    "--compress",
    "-z",
    is_flag=True,
    help="Compress output with gzip",
)
def backup_command(
    output_file: Optional[str],
    include_embeddings: bool,
    include_config: bool,
    compress: bool,
) -> None:
    """Create a backup of all data.

    \\b
    Examples:
        ragged export backup
        ragged export backup --output backup.json
        ragged export backup --compress
        ragged export backup --output backup.json.gz --compress
    """
    try:
        from src.storage.vector_store import VectorStore

        # Generate output filename if not provided
        if output_file is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            extension = ".json.gz" if compress else ".json"
            output_file = f"ragged_backup_{timestamp}{extension}"

        output_path = Path(output_file)

        console.print(f"[bold]Creating backup...[/bold]")
        console.print(f"Output: {output_path}")

        # Initialize vector store
        vector_store = VectorStore()

        # Get all data from vector store
        console.print("Retrieving data from vector store...")
        results = vector_store.collection.get(
            include=["documents", "metadatas", "embeddings"] if include_embeddings else ["documents", "metadatas"]
        )

        if not results or not results.get("ids"):
            console.print("[yellow]No data to export.[/yellow]")
            return

        # Build export data structure
        export_data: Dict[str, Any] = {
            "version": __version__,
            "export_timestamp": datetime.now().isoformat(),
            "ragged_version": __version__,
            "collection_name": vector_store._collection_name,
            "total_chunks": len(results["ids"]),
            "include_embeddings": include_embeddings,
        }

        # Add chunks
        console.print(f"Exporting {len(results['ids'])} chunks...")
        chunks = []
        for i, chunk_id in enumerate(results["ids"]):
            chunk_data = {
                "id": chunk_id,
                "document": results["documents"][i] if results.get("documents") else None,  # type: ignore
                "metadata": results["metadatas"][i] if results.get("metadatas") else None,  # type: ignore
            }
            if include_embeddings and results.get("embeddings"):
                chunk_data["embedding"] = results["embeddings"][i]  # type: ignore

            chunks.append(chunk_data)

        export_data["chunks"] = chunks

        # Add configuration if requested
        if include_config:
            console.print("Including configuration...")
            settings = get_settings()
            export_data["config"] = {
                "embedding_model": settings.embedding_model,
                "llm_model": settings.llm_model,
                "retrieval_method": settings.retrieval_method,
                "chunk_size": settings.chunk_size,
                "chunk_overlap": settings.chunk_overlap,
            }

        # Write to file
        console.print(f"Writing to {output_path}...")
        if compress:
            import gzip

            with gzip.open(output_path, "wt", encoding="utf-8") as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
        else:
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)

        # Get file size
        file_size = output_path.stat().st_size
        size_mb = file_size / (1024 * 1024)

        console.print(f"\n[green]✓[/green] Backup created successfully")
        console.print(f"  File: {output_path}")
        console.print(f"  Size: {size_mb:.2f} MB")
        console.print(f"  Chunks: {len(chunks)}")
        console.print(f"  Embeddings: {'included' if include_embeddings else 'excluded'}")

    except Exception as e:
        console.print(f"[bold red]✗[/bold red] Backup failed: {e}")
        logger.error(f"Backup failed: {e}", exc_info=True)
        sys.exit(1)


@export.command("restore")
@click.argument("backup_file", type=click.Path(exists=True))
@click.option(
    "--clear-existing",
    is_flag=True,
    help="Clear existing data before restore",
)
@click.option(
    "--skip-duplicates",
    is_flag=True,
    default=True,
    help="Skip chunks that already exist (default: yes)",
)
@click.option(
    "--yes",
    "-y",
    is_flag=True,
    help="Skip confirmation prompt",
)
def restore_command(
    backup_file: str,
    clear_existing: bool,
    skip_duplicates: bool,
    yes: bool,
) -> None:
    """Restore data from a backup.

    \\b
    Examples:
        ragged export restore backup.json
        ragged export restore backup.json --clear-existing
        ragged export restore backup.json.gz
    """
    try:
        from src.storage.vector_store import VectorStore
        import numpy as np

        backup_path = Path(backup_file)

        console.print(f"[bold]Restoring from backup...[/bold]")
        console.print(f"File: {backup_path}")

        # Read backup file
        console.print("Reading backup file...")
        if backup_path.suffix == ".gz":
            import gzip

            with gzip.open(backup_path, "rt", encoding="utf-8") as f:
                backup_data = json.load(f)
        else:
            with open(backup_path, "r", encoding="utf-8") as f:
                backup_data = json.load(f)

        # Validate backup data
        if "version" not in backup_data or "chunks" not in backup_data:
            console.print("[red]Invalid backup file format.[/red]")
            sys.exit(1)

        backup_version = backup_data["version"]
        total_chunks = len(backup_data["chunks"])
        has_embeddings = backup_data.get("include_embeddings", False)

        console.print(f"\nBackup information:")
        console.print(f"  Version: {backup_version}")
        console.print(f"  Timestamp: {backup_data.get('export_timestamp', 'unknown')}")
        console.print(f"  Chunks: {total_chunks}")
        console.print(f"  Embeddings: {'included' if has_embeddings else 'not included'}")

        if not has_embeddings:
            console.print("\n[yellow]Warning: This backup does not include embeddings.[/yellow]")
            console.print("Documents will need to be re-embedded after restore.")

        # Confirm action
        if not yes:
            if clear_existing:
                console.print("\n[yellow]⚠ This will DELETE all existing data![/yellow]")
            if not click.confirm("\nContinue with restore?"):
                console.print("Cancelled.")
                return

        # Initialize vector store
        vector_store = VectorStore()

        # Clear existing data if requested
        if clear_existing:
            console.print("\nClearing existing data...")
            vector_store.clear()
            console.print("[green]✓[/green] Existing data cleared")

        # Get existing IDs if skipping duplicates
        existing_ids = set()
        if skip_duplicates and not clear_existing:
            console.print("Checking for existing data...")
            existing_results = vector_store.collection.get()
            if existing_results and existing_results.get("ids"):
                existing_ids = set(existing_results["ids"])
                console.print(f"Found {len(existing_ids)} existing chunks")

        # Restore chunks
        console.print(f"\nRestoring {total_chunks} chunks...")

        ids_to_add = []
        embeddings_to_add = []
        documents_to_add = []
        metadatas_to_add = []
        skipped = 0

        for chunk in backup_data["chunks"]:
            chunk_id = chunk["id"]

            # Skip if already exists
            if skip_duplicates and chunk_id in existing_ids:
                skipped += 1
                continue

            ids_to_add.append(chunk_id)
            documents_to_add.append(chunk.get("document", ""))
            metadatas_to_add.append(chunk.get("metadata", {}))

            if has_embeddings and chunk.get("embedding"):
                embeddings_to_add.append(chunk["embedding"])

        # Add to vector store in batches
        if ids_to_add:
            batch_size = 100
            for i in range(0, len(ids_to_add), batch_size):
                end_idx = min(i + batch_size, len(ids_to_add))

                if has_embeddings and embeddings_to_add:
                    embeddings_batch = np.array(embeddings_to_add[i:end_idx])
                else:
                    # If no embeddings in backup, we need to generate them
                    console.print("\n[yellow]Embeddings not found in backup. Generating embeddings...[/yellow]")
                    from src.embedding.embedder import Embedder

                    embedder = Embedder()
                    embeddings_batch = embedder.embed_batch(documents_to_add[i:end_idx])

                vector_store.add(
                    ids=ids_to_add[i:end_idx],
                    embeddings=embeddings_batch,
                    documents=documents_to_add[i:end_idx],
                    metadatas=metadatas_to_add[i:end_idx],
                )

                progress = ((i + len(ids_to_add[i:end_idx])) / len(ids_to_add)) * 100
                console.print(f"Progress: {progress:.1f}%")

        console.print(f"\n[green]✓[/green] Restore completed successfully")
        console.print(f"  Restored: {len(ids_to_add)} chunks")
        if skipped > 0:
            console.print(f"  Skipped: {skipped} existing chunks")

        # Show configuration diff if available
        if backup_data.get("config"):
            console.print("\n[bold]Configuration in backup:[/bold]")
            for key, value in backup_data["config"].items():
                console.print(f"  {key}: {value}")
            console.print("\n[dim]Note: Restore does not change your current configuration.[/dim]")

    except Exception as e:
        console.print(f"[bold red]✗[/bold red] Restore failed: {e}")
        logger.error(f"Restore failed: {e}", exc_info=True)
        sys.exit(1)


@export.command("info")
@click.argument("backup_file", type=click.Path(exists=True))
def info_command(backup_file: str) -> None:
    """Show information about a backup file.

    \\b
    Examples:
        ragged export info backup.json
        ragged export info backup.json.gz
    """
    try:
        backup_path = Path(backup_file)

        # Read backup file
        if backup_path.suffix == ".gz":
            import gzip

            with gzip.open(backup_path, "rt", encoding="utf-8") as f:
                backup_data = json.load(f)
        else:
            with open(backup_path, "r", encoding="utf-8") as f:
                backup_data = json.load(f)

        # Display information
        console.print(f"\n[bold]Backup Information[/bold]")
        console.print(f"File: {backup_path}")
        console.print(f"Size: {backup_path.stat().st_size / (1024 * 1024):.2f} MB")
        console.print()

        console.print(f"[bold]Content:[/bold]")
        console.print(f"  Ragged Version: {backup_data.get('ragged_version', 'unknown')}")
        console.print(f"  Export Timestamp: {backup_data.get('export_timestamp', 'unknown')}")
        console.print(f"  Collection Name: {backup_data.get('collection_name', 'unknown')}")
        console.print(f"  Total Chunks: {backup_data.get('total_chunks', len(backup_data.get('chunks', [])))}")
        console.print(f"  Embeddings Included: {backup_data.get('include_embeddings', False)}")

        if backup_data.get("config"):
            console.print(f"\n[bold]Configuration:[/bold]")
            for key, value in backup_data["config"].items():
                console.print(f"  {key}: {value}")

        # Analyze document distribution
        if backup_data.get("chunks"):
            console.print(f"\n[bold]Document Distribution:[/bold]")
            doc_counts: Dict[str, int] = {}
            for chunk in backup_data["chunks"]:
                metadata = chunk.get("metadata", {})
                doc_path = metadata.get("document_path", "Unknown")
                doc_counts[doc_path] = doc_counts.get(doc_path, 0) + 1

            # Show top 10 documents
            sorted_docs = sorted(doc_counts.items(), key=lambda x: x[1], reverse=True)
            for doc, count in sorted_docs[:10]:
                console.print(f"  {doc}: {count} chunks")

            if len(sorted_docs) > 10:
                console.print(f"  ... and {len(sorted_docs) - 10} more documents")

        console.print()

    except Exception as e:
        console.print(f"[bold red]✗[/bold red] Failed to read backup: {e}")
        logger.error(f"Failed to read backup: {e}", exc_info=True)
        sys.exit(1)


@export.command("list")
@click.option(
    "--directory",
    "-d",
    type=click.Path(exists=True),
    default=".",
    help="Directory to search for backups (default: current directory)",
)
def list_backups(directory: str) -> None:
    """List available backup files.

    \\b
    Examples:
        ragged export list
        ragged export list --directory ~/backups
    """
    try:
        dir_path = Path(directory)

        # Find backup files
        backup_files = list(dir_path.glob("ragged_backup_*.json"))
        backup_files.extend(dir_path.glob("ragged_backup_*.json.gz"))
        backup_files.extend(dir_path.glob("*.ragged.json"))
        backup_files.extend(dir_path.glob("*.ragged.json.gz"))

        if not backup_files:
            console.print(f"[yellow]No backup files found in {directory}[/yellow]")
            return

        console.print(f"\n[bold]Found {len(backup_files)} backup file(s)[/bold]\n")

        for backup_file in sorted(backup_files, key=lambda x: x.stat().st_mtime, reverse=True):
            size_mb = backup_file.stat().st_size / (1024 * 1024)
            mtime = datetime.fromtimestamp(backup_file.stat().st_mtime)

            console.print(f"[cyan]{backup_file.name}[/cyan]")
            console.print(f"  Size: {size_mb:.2f} MB")
            console.print(f"  Modified: {mtime.strftime('%Y-%m-%d %H:%M:%S')}")
            console.print()

    except Exception as e:
        console.print(f"[bold red]✗[/bold red] Failed to list backups: {e}")
        logger.error(f"Failed to list backups: {e}", exc_info=True)
        sys.exit(1)
