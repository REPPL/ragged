"""Version command for viewing document version history.

v0.3.7a: Document version tracking and querying.
"""

from pathlib import Path

import click
from rich.panel import Panel
from rich.table import Table

from src.cli.common import console
from src.storage import VersionTracker
from src.utils.logging import get_logger

logger = get_logger(__name__)


@click.group()
def versions():
    """View document version history and tracking."""
    pass


@versions.command()
@click.argument("file_path", type=click.Path(exists=True))
def list(file_path: str) -> None:
    """List all versions of a document.

    FILE_PATH is the path to the document file.

    Example:
        ragged versions list path/to/document.pdf
    """
    tracker = VersionTracker()
    file_path_abs = str(Path(file_path).absolute())

    # Find document
    doc_id = tracker.find_document_by_path(file_path_abs)

    if not doc_id:
        console.print(f"[red]✗[/red] No versions found for: {file_path}")
        console.print("[dim]Document has not been indexed yet.[/dim]")
        return

    # Get all versions
    versions_list = tracker.list_versions(doc_id)

    if not versions_list:
        console.print(f"[red]✗[/red] No versions found for document: {doc_id}")
        return

    # Display summary
    console.print()
    console.print(Panel(
        f"Document: {Path(file_path).name}\n"
        f"Document ID: {doc_id}\n"
        f"Total Versions: {len(versions_list)}",
        title="Version History",
        border_style="cyan",
    ))

    # Create versions table
    table = Table(show_header=True, header_style="bold cyan")
    table.add_column("Version", justify="right", style="cyan")
    table.add_column("Version ID", style="dim")
    table.add_column("Content Hash", style="yellow")
    table.add_column("Created At")
    table.add_column("Pages", justify="right")

    for version in versions_list:
        # Shorten hashes for display
        version_id_short = version.version_id[:12] + "..."
        content_hash_short = version.content_hash[:12] + "..."

        # Format timestamp
        created_at = version.created_at.strftime("%Y-%m-%d %H:%M:%S")

        # Page count
        page_count = str(len(version.page_hashes)) if version.page_hashes else "-"

        table.add_row(
            str(version.version_number),
            version_id_short,
            content_hash_short,
            created_at,
            page_count,
        )

    console.print()
    console.print(table)
    console.print()


@versions.command()
@click.option(
    "--version-id",
    type=str,
    help="Version ID to display",
)
@click.option(
    "--version-number",
    type=int,
    help="Version number to display",
)
@click.option(
    "--content-hash",
    type=str,
    help="Content hash to display",
)
@click.argument("identifier", type=str, required=False)
def show(
    version_id: str | None,
    version_number: int | None,
    content_hash: str | None,
    identifier: str | None,
) -> None:
    """Show details of a specific version.

    You can specify the version using one of these options:

    --version-id: Full version ID\n
    --version-number: Version number (requires doc_id as IDENTIFIER)\n
    --content-hash: Content hash\n

    Or provide version ID directly as IDENTIFIER.

    Examples:
        ragged versions show abc123def456...\n
        ragged versions show --version-id abc123def456...\n
        ragged versions show --version-number 2 doc_xyz789\n
        ragged versions show --content-hash 1a2b3c4d...
    """
    tracker = VersionTracker()
    version = None

    # Determine which lookup method to use
    if version_id:
        version = tracker.get_version_by_id(version_id)
    elif content_hash:
        version = tracker.get_version_by_hash(content_hash)
    elif version_number is not None:
        if not identifier:
            console.print("[red]✗[/red] --version-number requires a document ID as IDENTIFIER")
            console.print("\nExample: ragged versions show --version-number 2 doc_abc123")
            return
        version = tracker.get_version(identifier, version_number)
    elif identifier:
        # Try as version ID
        version = tracker.get_version_by_id(identifier)
    else:
        console.print("[red]✗[/red] Please specify a version using one of the options")
        console.print("\nSee: ragged versions show --help")
        return

    if not version:
        console.print("[red]✗[/red] Version not found")
        return

    # Display version details
    console.print()
    console.print(Panel(
        f"Version: {version.version_number}\n"
        f"Document ID: {version.doc_id}\n"
        f"Created: {version.created_at.strftime('%Y-%m-%d %H:%M:%S')}",
        title="Version Details",
        border_style="green",
    ))

    # Version identification
    console.print("\n[bold]Identification[/bold]")
    console.print(f"Version ID:    {version.version_id}")
    console.print(f"Content Hash:  {version.content_hash}")

    # File information
    console.print("\n[bold]File[/bold]")
    console.print(f"Path: {version.file_path}")

    # Page information
    if version.page_hashes:
        console.print("\n[bold]Pages[/bold]")
        console.print(f"Total Pages: {len(version.page_hashes)}")

        # Show first few page hashes
        console.print("\nPage Hashes:")
        for i, page_hash in enumerate(version.page_hashes[:5], 1):
            console.print(f"  Page {i}: {page_hash[:16]}...")

        if len(version.page_hashes) > 5:
            console.print(f"  ... and {len(version.page_hashes) - 5} more pages")

    # Metadata
    if version.metadata:
        console.print("\n[bold]Metadata[/bold]")
        for key, value in version.metadata.items():
            console.print(f"{key}: {value}")

    console.print()


@versions.command()
@click.argument("file_path", type=click.Path(exists=True))
def check(file_path: str) -> None:
    """Check if a document has changed since last indexing.

    FILE_PATH is the path to the document file.

    Example:
        ragged versions check path/to/document.pdf
    """
    tracker = VersionTracker()
    file_path_abs = str(Path(file_path).absolute())

    # Read file and calculate hash
    try:
        with open(file_path_abs, "rb") as f:
            content = f.read()

        content_hash, _ = tracker.calculate_content_hash(content)

        # Check if new version
        is_new = tracker.is_new_version(file_path_abs, content_hash)

        if is_new:
            console.print("[yellow]⚠[/yellow] Document has changed (new version detected)")
            console.print(f"[dim]Content hash: {content_hash[:16]}...[/dim]")

            # Check if document exists at all
            doc_id = tracker.find_document_by_path(file_path_abs)
            if doc_id:
                console.print("\n[dim]Re-index to create new version.[/dim]")
            else:
                console.print("\n[dim]Document not yet indexed.[/dim]")
        else:
            console.print("[green]✓[/green] Document unchanged (matches latest version)")
            console.print(f"[dim]Content hash: {content_hash[:16]}...[/dim]")

    except Exception as e:
        console.print(f"[red]✗[/red] Error checking document: {e}")
        logger.error(f"Error checking document version: {e}")


@versions.command()
@click.argument("doc_id", type=str)
@click.argument("version1", type=int)
@click.argument("version2", type=int)
def compare(doc_id: str, version1: int, version2: int) -> None:
    """Compare two versions of a document.

    DOC_ID is the document identifier\n
    VERSION1 and VERSION2 are version numbers to compare

    Example:
        ragged versions compare doc_abc123 1 2
    """
    tracker = VersionTracker()

    # Get both versions
    v1 = tracker.get_version(doc_id, version1)
    v2 = tracker.get_version(doc_id, version2)

    if not v1:
        console.print(f"[red]✗[/red] Version {version1} not found")
        return

    if not v2:
        console.print(f"[red]✗[/red] Version {version2} not found")
        return

    # Display comparison
    console.print()
    console.print(Panel(
        f"Comparing versions {version1} and {version2}\n"
        f"Document ID: {doc_id}",
        title="Version Comparison",
        border_style="magenta",
    ))

    # Create comparison table
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Property", style="cyan")
    table.add_column(f"Version {version1}", style="yellow")
    table.add_column(f"Version {version2}", style="green")
    table.add_column("Changed", justify="center")

    # Content hash
    content_changed = v1.content_hash != v2.content_hash
    table.add_row(
        "Content Hash",
        v1.content_hash[:16] + "...",
        v2.content_hash[:16] + "...",
        "✗" if content_changed else "✓"
    )

    # Created timestamp
    table.add_row(
        "Created",
        v1.created_at.strftime("%Y-%m-%d %H:%M:%S"),
        v2.created_at.strftime("%Y-%m-%d %H:%M:%S"),
        "-"
    )

    # Page count
    v1_pages = len(v1.page_hashes) if v1.page_hashes else 0
    v2_pages = len(v2.page_hashes) if v2.page_hashes else 0
    pages_changed = v1_pages != v2_pages

    table.add_row(
        "Page Count",
        str(v1_pages),
        str(v2_pages),
        "✗" if pages_changed else "✓"
    )

    # File path
    path_changed = v1.file_path != v2.file_path
    table.add_row(
        "File Path",
        str(Path(v1.file_path).name),
        str(Path(v2.file_path).name),
        "✗" if path_changed else "✓"
    )

    console.print()
    console.print(table)

    # Page-level changes
    if v1.page_hashes and v2.page_hashes:
        console.print("\n[bold]Page-Level Changes[/bold]")

        changed_pages = []
        for i in range(min(len(v1.page_hashes), len(v2.page_hashes))):
            if v1.page_hashes[i] != v2.page_hashes[i]:
                changed_pages.append(i + 1)

        if changed_pages:
            console.print(f"Changed pages: {', '.join(map(str, changed_pages[:10]))}")
            if len(changed_pages) > 10:
                console.print(f"  ... and {len(changed_pages) - 10} more")
        else:
            console.print("No page-level changes detected")

        # Pages added/removed
        if len(v2.page_hashes) > len(v1.page_hashes):
            added = len(v2.page_hashes) - len(v1.page_hashes)
            console.print(f"\n[green]+{added} pages added[/green]")
        elif len(v1.page_hashes) > len(v2.page_hashes):
            removed = len(v1.page_hashes) - len(v2.page_hashes)
            console.print(f"\n[red]-{removed} pages removed[/red]")

    console.print()
