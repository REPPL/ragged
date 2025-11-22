"""Cache management commands for ragged CLI.

Manages caches, temporary files, and system cleanup.
"""

import shutil
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import click

from src.cli.common import console
from src.cli.formatters import FORMAT_CHOICES, print_formatted
from src.config.settings import get_settings
from src.utils.logging import get_logger

logger = get_logger(__name__)


def _format_size(size_bytes: int) -> str:
    """Format byte size in human-readable format."""
    for unit in ["B", "KB", "MB", "GB"]:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} TB"


def _get_directory_size(path: Path) -> int:
    """Get total size of directory in bytes."""
    total_size = 0
    try:
        for item in path.rglob("*"):
            if item.is_file():
                total_size += item.stat().st_size
    except (PermissionError, FileNotFoundError) as e:
        logger.warning(f"Could not access {path}: {e}")
    return total_size


def _get_cache_info() -> dict[str, Any]:
    """Get information about all caches and temporary files."""
    settings = get_settings()
    data_dir = Path(settings.data_dir)

    cache_info = {
        "data_directory": str(data_dir),
        "caches": [],
    }

    # Check for various cache directories
    cache_locations = [
        ("Query History", data_dir / "query_history.json"),
        ("Embeddings Cache", data_dir / "embeddings_cache"),
        ("Query Cache", data_dir / "query_cache"),
        ("Temporary Files", data_dir / "tmp"),
        ("Logs", data_dir / "logs"),
    ]

    for name, path in cache_locations:
        if path.exists():
            if path.is_file():
                size = path.stat().st_size
                count = 1
            else:
                size = _get_directory_size(path)
                count = len(list(path.rglob("*"))) if path.is_dir() else 0

            cache_info["caches"].append(
                {
                    "name": name,
                    "path": str(path),
                    "size": size,
                    "size_formatted": _format_size(size),
                    "exists": True,
                    "items": count,
                }
            )
        else:
            cache_info["caches"].append(
                {
                    "name": name,
                    "path": str(path),
                    "size": 0,
                    "size_formatted": "0 B",
                    "exists": False,
                    "items": 0,
                }
            )

    # Calculate total
    total_size = sum(c["size"] for c in cache_info["caches"])
    cache_info["total_size"] = total_size
    cache_info["total_size_formatted"] = _format_size(total_size)

    return cache_info


@click.group()
def cache() -> None:
    """Manage caches and temporary files.

    Inspect, clear, and optimise caches for better performance.
    """
    pass


@cache.command("info")
@click.option(
    "--format",
    "-f",
    "output_format",
    type=click.Choice(FORMAT_CHOICES + ["text"], case_sensitive=False),
    default="text",
    help="Output format",
)
def cache_info(output_format: str) -> None:
    """Show cache information and statistics.

    \\b
    Examples:
        ragged cache info
        ragged cache info --format json
    """
    try:
        cache_data = _get_cache_info()

        if output_format == "text":
            console.print("\n[bold]Cache Information[/bold]")
            console.print(f"Data Directory: {cache_data['data_directory']}")
            console.print(f"Total Size: {cache_data['total_size_formatted']}\n")

            console.print("[bold]Cache Components:[/bold]")
            for cache in cache_data["caches"]:
                status = "[green]✓[/green]" if cache["exists"] else "[dim]○[/dim]"
                console.print(f"\n{status} {cache['name']}")
                console.print(f"  Path: {cache['path']}")
                if cache["exists"]:
                    console.print(f"  Size: {cache['size_formatted']}")
                    console.print(f"  Items: {cache['items']}")
                else:
                    console.print("  [dim]Not created yet[/dim]")

            console.print()
        else:
            print_formatted(
                cache_data["caches"],
                format_type=output_format,  # type: ignore
                title="Cache Information",
                console=console,
            )

    except Exception as e:
        console.print(f"[bold red]✗[/bold red] Failed to get cache info: {e}")
        logger.error(f"Cache info failed: {e}", exc_info=True)
        sys.exit(1)


@cache.command("clear")
@click.option(
    "--type",
    "-t",
    "cache_type",
    type=click.Choice(
        ["history", "embeddings", "queries", "temp", "logs", "all"],
        case_sensitive=False,
    ),
    default="all",
    help="Type of cache to clear (default: all)",
)
@click.option(
    "--yes",
    "-y",
    is_flag=True,
    help="Skip confirmation prompt",
)
def clear_cache(cache_type: str, yes: bool) -> None:
    """Clear caches and temporary files.

    \\b
    Examples:
        ragged cache clear --type history
        ragged cache clear --type temp --yes
        ragged cache clear --type all
    """
    try:
        settings = get_settings()
        data_dir = Path(settings.data_dir)

        # Define what to clear
        cache_map = {
            "history": [data_dir / "query_history.json"],
            "embeddings": [data_dir / "embeddings_cache"],
            "queries": [data_dir / "query_cache"],
            "temp": [data_dir / "tmp"],
            "logs": [data_dir / "logs"],
        }

        if cache_type == "all":
            paths_to_clear = []
            for paths in cache_map.values():
                paths_to_clear.extend(paths)
        else:
            paths_to_clear = cache_map.get(cache_type, [])

        # Filter to only existing paths
        existing_paths = [p for p in paths_to_clear if p.exists()]

        if not existing_paths:
            console.print(f"[yellow]No {cache_type} cache found to clear.[/yellow]")
            return

        # Show what will be cleared
        total_size = sum(_get_directory_size(p) if p.is_dir() else p.stat().st_size for p in existing_paths)

        console.print(f"[yellow]About to clear {len(existing_paths)} cache location(s):[/yellow]")
        for path in existing_paths:
            if path.is_dir():
                size = _get_directory_size(path)
            else:
                size = path.stat().st_size
            console.print(f"  • {path.name}: {_format_size(size)}")

        console.print(f"\nTotal space to free: {_format_size(total_size)}")

        # Confirm
        if not yes:
            if not click.confirm("\nContinue?"):
                console.print("Cancelled.")
                return

        # Clear caches
        cleared_count = 0
        for path in existing_paths:
            try:
                if path.is_dir():
                    shutil.rmtree(path)
                else:
                    path.unlink()
                cleared_count += 1
                logger.info(f"Cleared: {path}")
            except (PermissionError, FileNotFoundError) as e:
                console.print(f"[yellow]Warning: Could not clear {path.name}: {e}[/yellow]")

        console.print(f"\n[green]✓[/green] Cleared {cleared_count} cache location(s)")
        console.print(f"Freed {_format_size(total_size)}")

    except Exception as e:
        console.print(f"[bold red]✗[/bold red] Failed to clear cache: {e}")
        logger.error(f"Clear cache failed: {e}", exc_info=True)
        sys.exit(1)


@cache.command("clean")
@click.option(
    "--older-than",
    "-o",
    type=int,
    default=7,
    help="Remove files older than N days (default: 7)",
)
@click.option(
    "--dry-run",
    "-n",
    is_flag=True,
    help="Show what would be deleted without actually deleting",
)
@click.option(
    "--yes",
    "-y",
    is_flag=True,
    help="Skip confirmation prompt",
)
def clean_cache(older_than: int, dry_run: bool, yes: bool) -> None:
    """Clean old cache files and temporary data.

    \\b
    Examples:
        ragged cache clean --older-than 7
        ragged cache clean --older-than 30 --dry-run
        ragged cache clean --older-than 1 --yes
    """
    try:
        settings = get_settings()
        data_dir = Path(settings.data_dir)

        cutoff_date = datetime.now() - timedelta(days=older_than)

        # Find old files
        old_files: list[Path] = []
        total_size = 0

        cache_dirs = [
            data_dir / "tmp",
            data_dir / "logs",
            data_dir / "embeddings_cache",
            data_dir / "query_cache",
        ]

        for cache_dir in cache_dirs:
            if not cache_dir.exists():
                continue

            for file_path in cache_dir.rglob("*"):
                if not file_path.is_file():
                    continue

                # Check modification time
                mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
                if mtime < cutoff_date:
                    old_files.append(file_path)
                    total_size += file_path.stat().st_size

        if not old_files:
            console.print(f"[green]✓[/green] No files older than {older_than} days found.")
            return

        # Show what will be cleaned
        console.print(f"\n[bold]Found {len(old_files)} file(s) older than {older_than} days[/bold]")
        console.print(f"Total size: {_format_size(total_size)}\n")

        if dry_run:
            console.print("[yellow]DRY RUN - No files will be deleted[/yellow]\n")

        # Group by directory
        by_dir: dict[str, list[Path]] = {}
        for file_path in old_files:
            parent = str(file_path.parent)
            if parent not in by_dir:
                by_dir[parent] = []
            by_dir[parent].append(file_path)

        for dir_path, files in sorted(by_dir.items()):
            dir_size = sum(f.stat().st_size for f in files)
            console.print(f"[cyan]{dir_path}[/cyan]: {len(files)} files ({_format_size(dir_size)})")

        if dry_run:
            console.print("\n[dim]Use without --dry-run to actually delete these files[/dim]")
            return

        # Confirm
        if not yes:
            console.print()
            if not click.confirm("Delete these files?"):
                console.print("Cancelled.")
                return

        # Delete files
        deleted_count = 0
        for file_path in old_files:
            try:
                file_path.unlink()
                deleted_count += 1
            except (PermissionError, FileNotFoundError) as e:
                console.print(f"[yellow]Warning: Could not delete {file_path.name}: {e}[/yellow]")

        console.print(f"\n[green]✓[/green] Deleted {deleted_count} file(s)")
        console.print(f"Freed {_format_size(total_size)}")

    except Exception as e:
        console.print(f"[bold red]✗[/bold red] Failed to clean cache: {e}")
        logger.error(f"Clean cache failed: {e}", exc_info=True)
        sys.exit(1)


@cache.command("stats")
@click.option(
    "--format",
    "-f",
    "output_format",
    type=click.Choice(FORMAT_CHOICES + ["text"], case_sensitive=False),
    default="text",
    help="Output format",
)
def cache_stats(output_format: str) -> None:
    """Show cache statistics and metrics.

    \\b
    Examples:
        ragged cache stats
        ragged cache stats --format json
    """
    try:
        cache_data = _get_cache_info()
        settings = get_settings()

        stats = {
            "total_size": cache_data["total_size_formatted"],
            "data_directory": cache_data["data_directory"],
            "cache_components": len([c for c in cache_data["caches"] if c["exists"]]),
            "total_items": sum(c["items"] for c in cache_data["caches"]),
        }

        # Add component breakdown
        components = []
        for cache in cache_data["caches"]:
            if cache["exists"]:
                components.append(
                    {
                        "name": cache["name"],
                        "size": cache["size_formatted"],
                        "items": cache["items"],
                        "percentage": (cache["size"] / cache_data["total_size"] * 100) if cache_data["total_size"] > 0 else 0,
                    }
                )

        if output_format == "text":
            console.print("\n[bold]Cache Statistics[/bold]\n")
            console.print(f"Total Cache Size: {stats['total_size']}")
            console.print(f"Active Components: {stats['cache_components']}")
            console.print(f"Total Items: {stats['total_items']}")

            if components:
                console.print("\n[bold]Breakdown by Component:[/bold]")
                for comp in sorted(components, key=lambda x: x["percentage"], reverse=True):
                    console.print(f"\n{comp['name']}")
                    console.print(f"  Size: {comp['size']} ({comp['percentage']:.1f}%)")
                    console.print(f"  Items: {comp['items']}")

            console.print()
        else:
            print_formatted(
                components,
                format_type=output_format,  # type: ignore
                title="Cache Statistics",
                console=console,
            )

    except Exception as e:
        console.print(f"[bold red]✗[/bold red] Failed to get cache stats: {e}")
        logger.error(f"Cache stats failed: {e}", exc_info=True)
        sys.exit(1)


@cache.command("embedders")
@click.option(
    "--format",
    "-f",
    "output_format",
    type=click.Choice(FORMAT_CHOICES + ["text"], case_sensitive=False),
    default="text",
    help="Output format",
)
def embedder_cache_stats(output_format: str) -> None:
    """Show embedder cache statistics (v0.2.9).

    \\b
    Examples:
        ragged cache embedders
        ragged cache embedders --format json
    """
    try:
        from src.embeddings.factory import get_cache_stats

        stats = get_cache_stats()

        if output_format == "text":
            console.print("\n[bold]Embedder Cache Statistics[/bold]\n")
            console.print(f"Caching Enabled: {'[green]Yes[/green]' if stats['enabled'] else '[red]No[/red]'}")
            console.print(f"Cached Models: {stats['size']}")

            if stats['models']:
                console.print("\n[bold]Cached Embedders:[/bold]")
                for model in stats['models']:
                    console.print(f"  • {model}")
            else:
                console.print("\n[dim]No models currently cached[/dim]")

            console.print()
        else:
            print_formatted(
                stats,
                format_type=output_format,  # type: ignore
                title="Embedder Cache Statistics",
                console=console,
            )

    except Exception as e:
        console.print(f"[bold red]✗[/bold red] Failed to get embedder cache stats: {e}")
        logger.error(f"Embedder cache stats failed: {e}", exc_info=True)
        sys.exit(1)


@cache.command("clear-embedders")
@click.option(
    "--yes",
    "-y",
    is_flag=True,
    help="Skip confirmation prompt",
)
def clear_embedder_cache_cmd(yes: bool) -> None:
    """Clear the embedder cache (v0.2.9).

    Forces embedders to be reloaded on next use. Useful for freeing memory
    or troubleshooting embedding issues.

    \\b
    Examples:
        ragged cache clear-embedders
        ragged cache clear-embedders --yes
    """
    try:
        from src.embeddings.factory import clear_embedder_cache, get_cache_stats

        # Get stats before clearing
        stats = get_cache_stats()

        if stats['size'] == 0:
            console.print("[yellow]Embedder cache is already empty.[/yellow]")
            return

        console.print(f"[yellow]About to clear {stats['size']} cached embedder(s):[/yellow]")
        for model in stats['models']:
            console.print(f"  • {model}")

        # Confirm
        if not yes:
            console.print()
            if not click.confirm("Continue?"):
                console.print("Cancelled.")
                return

        # Clear cache
        count = clear_embedder_cache()
        console.print(f"\n[green]✓[/green] Cleared {count} cached embedder(s)")
        console.print("[dim]Embedders will be reloaded on next use[/dim]")

    except Exception as e:
        console.print(f"[bold red]✗[/bold red] Failed to clear embedder cache: {e}")
        logger.error(f"Clear embedder cache failed: {e}", exc_info=True)
        sys.exit(1)
