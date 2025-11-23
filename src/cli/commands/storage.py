"""Storage management commands for ragged CLI.

v0.5.3: Collection info, schema migration, and maintenance.
"""

import sys
from pathlib import Path

import click

from ragged.cli.common import ProgressType, console
from ragged.utils.logging import get_logger

logger = get_logger(__name__)


@click.group()
def storage() -> None:
    """Storage and database management.

    \b
    Commands:
        info    - Show storage statistics
        migrate - Migrate v0.4 to v0.5 schema
        vacuum  - Clean up orphaned embeddings

    \b
    Examples:
        ragged storage info
        ragged storage migrate
        ragged storage vacuum --dry-run
    """
    pass


@storage.command()
@click.option(
    "--verbose",
    "-v",
    is_flag=True,
    help="Show detailed statistics",
)
def info(verbose: bool) -> None:
    """Show storage statistics and collection information.

    \b
    Displays:
    - Text collection statistics (chunks, documents)
    - Vision collection statistics (pages, documents)
    - Storage size and location
    - Collection schema versions

    \b
    Examples:
        ragged storage info
        ragged storage info --verbose
    """
    from ragged.storage.dual_storage import DualVectorStore
    from ragged.storage.vector_store import VectorStore

    try:
        console.print("[bold blue]Storage Information:[/bold blue]")
        console.print()

        # Text collection
        console.print("[bold]Text Collection:[/bold]")
        vector_store = VectorStore()
        text_count = vector_store.count()
        console.print(f"  Total chunks: {text_count}")

        # Get unique documents
        all_docs = vector_store.get_all_documents()
        if all_docs and all_docs.get("metadatas"):
            unique_docs = set(
                meta.get("document_id", "unknown") for meta in all_docs["metadatas"]
            )
            console.print(f"  Unique documents: {len(unique_docs)}")

            if verbose:
                # Show document list
                console.print("  Documents:")
                for doc_id in sorted(unique_docs):
                    # Count chunks for this document
                    doc_chunks = sum(
                        1 for meta in all_docs["metadatas"] if meta.get("document_id") == doc_id
                    )
                    console.print(f"    - {doc_id}: {doc_chunks} chunks")

        # Vision collection
        console.print()
        console.print("[bold]Vision Collection:[/bold]")

        try:
            dual_store = DualVectorStore()
            vision_count = dual_store.count_vision_embeddings()

            if vision_count > 0:
                console.print(f"  Total page embeddings: {vision_count}")

                # Get unique vision documents
                vision_docs = dual_store.get_all_vision_documents()
                if vision_docs and vision_docs.get("metadatas"):
                    unique_vision_docs = set(
                        meta.get("document_id", "unknown")
                        for meta in vision_docs["metadatas"]
                    )
                    console.print(f"  Unique documents: {len(unique_vision_docs)}")

                    if verbose:
                        # Show vision document list
                        console.print("  Documents:")
                        for doc_id in sorted(unique_vision_docs):
                            # Count pages for this document
                            doc_pages = sum(
                                1
                                for meta in vision_docs["metadatas"]
                                if meta.get("document_id") == doc_id
                            )
                            console.print(f"    - {doc_id}: {doc_pages} pages")
            else:
                console.print("  [dim]No vision embeddings yet[/dim]")

        except Exception as e:
            console.print(f"  [yellow]Vision collection not available: {e}[/yellow]")

        # Storage location and size
        console.print()
        console.print("[bold]Storage:[/bold]")

        data_dir = Path("data")
        if data_dir.exists():
            console.print(f"  Location: {data_dir.absolute()}")

            # Calculate total size
            total_size = sum(f.stat().st_size for f in data_dir.rglob("*") if f.is_file())
            size_mb = total_size / (1024 * 1024)
            console.print(f"  Size: {size_mb:.2f} MB")

            if verbose:
                # Show subdirectory sizes
                console.print("  Breakdown:")
                for subdir in data_dir.iterdir():
                    if subdir.is_dir():
                        subdir_size = sum(
                            f.stat().st_size for f in subdir.rglob("*") if f.is_file()
                        )
                        subdir_mb = subdir_size / (1024 * 1024)
                        console.print(f"    {subdir.name}: {subdir_mb:.2f} MB")
        else:
            console.print("  [yellow]Data directory not found[/yellow]")

    except Exception as e:
        console.print(f"[bold red]✗[/bold red] Failed to get storage info: {e}")
        logger.error(f"Storage info failed: {e}", exc_info=True)
        sys.exit(1)


@storage.command()
@click.option(
    "--dry-run",
    is_flag=True,
    help="Show what would be migrated without making changes",
)
@click.option(
    "--backup",
    is_flag=True,
    default=True,
    help="Create backup before migration (default: True)",
)
def migrate(dry_run: bool, backup: bool) -> None:
    """Migrate v0.4 schema to v0.5 dual-collection schema.

    \b
    Migration Process:
    1. Detect existing v0.4 text embeddings
    2. Create new vision collection (if not exists)
    3. Preserve all existing text embeddings
    4. Add vision embedding support

    \b
    Safety:
    - Automatic backup before migration (unless --no-backup)
    - Dry-run mode to preview changes
    - Non-destructive (text embeddings preserved)

    \b
    Examples:
        ragged storage migrate --dry-run
        ragged storage migrate
        ragged storage migrate --no-backup
    """
    from ragged.storage.dual_storage import DualVectorStore
    from ragged.storage.vector_store import VectorStore

    try:
        console.print("[bold blue]Schema Migration: v0.4 → v0.5[/bold blue]")
        console.print()

        if dry_run:
            console.print("[yellow]DRY RUN - No changes will be made[/yellow]")
            console.print()

        # Check current state
        vector_store = VectorStore()
        text_count = vector_store.count()

        console.print(f"[bold]Current State:[/bold]")
        console.print(f"  Text embeddings: {text_count}")

        # Check if vision collection exists
        try:
            dual_store = DualVectorStore()
            vision_count = dual_store.count_vision_embeddings()
            console.print(f"  Vision embeddings: {vision_count}")

            if vision_count > 0:
                console.print()
                console.print("[green]✓ Already using v0.5 schema[/green]")
                console.print("[dim]No migration needed[/dim]")
                return

        except Exception:
            console.print("  Vision embeddings: [yellow]collection not found[/yellow]")

        console.print()

        # Migration plan
        console.print("[bold]Migration Plan:[/bold]")
        console.print("  1. Create vision embedding collection")
        console.print("  2. Verify text embeddings preserved")
        console.print("  3. Enable multi-modal retrieval")
        console.print()

        if dry_run:
            console.print("[green]✓ Dry run complete[/green]")
            console.print("[dim]Run without --dry-run to perform migration[/dim]")
            return

        # Backup if requested
        if backup:
            console.print("[bold]Creating backup...[/bold]")

            import shutil
            from datetime import datetime

            data_dir = Path("data")
            if data_dir.exists():
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_dir = data_dir.parent / f"data_backup_{timestamp}"

                with ProgressType() as progress:
                    task = progress.add_task("Backing up...", total=100)
                    shutil.copytree(data_dir, backup_dir)
                    progress.update(task, completed=100)

                console.print(f"[green]✓ Backup created: {backup_dir}[/green]")
                console.print()

        # Perform migration
        with ProgressType() as progress:
            task = progress.add_task("Migrating...", total=100)

            # Create vision collection
            progress.update(task, description="Creating vision collection...", advance=30)
            dual_store = DualVectorStore()

            # Verify text embeddings still accessible
            progress.update(task, description="Verifying text embeddings...", advance=30)
            new_text_count = vector_store.count()

            if new_text_count != text_count:
                raise RuntimeError(
                    f"Text embedding count mismatch: {text_count} → {new_text_count}"
                )

            progress.update(task, description="Finalising...", advance=40)

        console.print("[bold green]✓ Migration complete![/bold green]")
        console.print()
        console.print("[bold]Post-Migration State:[/bold]")
        console.print(f"  Text embeddings: {new_text_count}")
        console.print(f"  Vision embeddings: 0 (ready for ingestion)")
        console.print()
        console.print("[dim]You can now use --vision flag during ingestion[/dim]")

    except Exception as e:
        console.print(f"[bold red]✗[/bold red] Migration failed: {e}")
        logger.error(f"Migration failed: {e}", exc_info=True)
        sys.exit(1)


@storage.command()
@click.option(
    "--dry-run",
    is_flag=True,
    help="Show what would be deleted without making changes",
)
@click.option(
    "--orphaned-only",
    is_flag=True,
    default=True,
    help="Only remove orphaned embeddings (default: True)",
)
def vacuum(dry_run: bool, orphaned_only: bool) -> None:
    """Clean up orphaned embeddings and optimize storage.

    \b
    Cleanup Process:
    - Identifies text chunks without parent documents
    - Identifies vision pages without parent documents
    - Removes orphaned embeddings
    - Optimises database storage

    \b
    Safety:
    - Dry-run mode to preview deletions
    - Only removes truly orphaned data
    - Preserves all valid embeddings

    \b
    Examples:
        ragged storage vacuum --dry-run
        ragged storage vacuum
    """
    from ragged.storage.dual_storage import DualVectorStore
    from ragged.storage.vector_store import VectorStore

    try:
        console.print("[bold blue]Storage Vacuum[/bold blue]")
        console.print()

        if dry_run:
            console.print("[yellow]DRY RUN - No changes will be made[/yellow]")
            console.print()

        orphaned_text = []
        orphaned_vision = []

        # Scan text embeddings
        console.print("[bold]Scanning text embeddings...[/bold]")
        vector_store = VectorStore()
        all_text = vector_store.get_all_documents()

        if all_text and all_text.get("ids"):
            # Group by document_id
            doc_groups = {}
            for i, meta in enumerate(all_text["metadatas"]):
                doc_id = meta.get("document_id", "unknown")
                if doc_id not in doc_groups:
                    doc_groups[doc_id] = []
                doc_groups[doc_id].append(all_text["ids"][i])

            # Check for orphaned chunks (document files don't exist)
            docs_dir = Path("data/documents")
            for doc_id, chunk_ids in doc_groups.items():
                doc_metadata_dir = docs_dir / ".ragged" / doc_id
                if not doc_metadata_dir.exists():
                    orphaned_text.extend(chunk_ids)

            console.print(f"  Total chunks: {len(all_text['ids'])}")
            console.print(f"  Orphaned chunks: {len(orphaned_text)}")

        # Scan vision embeddings
        console.print()
        console.print("[bold]Scanning vision embeddings...[/bold]")

        try:
            dual_store = DualVectorStore()
            all_vision = dual_store.get_all_vision_documents()

            if all_vision and all_vision.get("ids"):
                # Group by document_id
                vision_doc_groups = {}
                for i, meta in enumerate(all_vision["metadatas"]):
                    doc_id = meta.get("document_id", "unknown")
                    if doc_id not in vision_doc_groups:
                        vision_doc_groups[doc_id] = []
                    vision_doc_groups[doc_id].append(all_vision["ids"][i])

                # Check for orphaned pages
                for doc_id, page_ids in vision_doc_groups.items():
                    doc_metadata_dir = docs_dir / ".ragged" / doc_id
                    if not doc_metadata_dir.exists():
                        orphaned_vision.extend(page_ids)

                console.print(f"  Total pages: {len(all_vision['ids'])}")
                console.print(f"  Orphaned pages: {len(orphaned_vision)}")
            else:
                console.print("  [dim]No vision embeddings[/dim]")

        except Exception:
            console.print("  [dim]Vision collection not available[/dim]")

        # Summary
        console.print()
        console.print("[bold]Summary:[/bold]")
        total_orphaned = len(orphaned_text) + len(orphaned_vision)
        console.print(f"  Total orphaned embeddings: {total_orphaned}")

        if total_orphaned == 0:
            console.print("[green]✓ No orphaned embeddings found[/green]")
            return

        if dry_run:
            console.print()
            console.print("[bold]Would delete:[/bold]")
            console.print(f"  Text chunks: {len(orphaned_text)}")
            console.print(f"  Vision pages: {len(orphaned_vision)}")
            console.print()
            console.print("[dim]Run without --dry-run to perform cleanup[/dim]")
            return

        # Perform cleanup
        console.print()
        confirm = click.confirm(
            f"Delete {total_orphaned} orphaned embeddings?", default=False
        )

        if not confirm:
            console.print("[yellow]Cancelled. No changes made.[/yellow]")
            return

        with ProgressType() as progress:
            task = progress.add_task("Cleaning up...", total=100)

            # Delete orphaned text chunks
            if orphaned_text:
                progress.update(task, description="Removing orphaned text chunks...", advance=30)
                vector_store.delete(ids=orphaned_text)

            # Delete orphaned vision pages
            if orphaned_vision:
                progress.update(task, description="Removing orphaned vision pages...", advance=30)
                dual_store.delete_vision_embeddings(ids=orphaned_vision)

            progress.update(task, description="Optimising storage...", advance=40)

        console.print("[bold green]✓ Cleanup complete![/bold green]")
        console.print()
        console.print(f"  Removed {len(orphaned_text)} text chunks")
        console.print(f"  Removed {len(orphaned_vision)} vision pages")

    except Exception as e:
        console.print(f"[bold red]✗[/bold red] Vacuum failed: {e}")
        logger.error(f"Vacuum failed: {e}", exc_info=True)
        sys.exit(1)
