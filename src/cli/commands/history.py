"""Query history management for ragged CLI.

Stores and manages query history for easy replay and analysis.

v0.2.11 FEAT-PRIV-001: Query history now encrypted at rest.
"""

import json
import os
import shutil
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

import click

from src.cli.common import console
from src.cli.formatters import FORMAT_CHOICES, print_formatted
from src.config.settings import get_settings
from src.security.encryption import get_encryption_manager
from src.utils.logging import get_logger

logger = get_logger(__name__)


class QueryHistory:
    """Manages query history storage and retrieval."""

    def __init__(self, history_file: Path | None = None):
        """Initialise query history manager.

        Args:
            history_file: Path to history file (defaults to data_dir/query_history.json)
        """
        if history_file is None:
            settings = get_settings()
            data_dir = Path(settings.data_dir)
            history_file = data_dir / "query_history.json"

        self.history_file = history_file
        self._ensure_history_file()

    def _ensure_history_file(self) -> None:
        """Ensure history file exists."""
        if not self.history_file.exists():
            self.history_file.parent.mkdir(parents=True, exist_ok=True)
            self._save_history([])

    def _load_history(self) -> list[dict[str, Any]]:
        """Load history from encrypted file.

        Returns:
            List of history entries

        Security: v0.2.11 FEAT-PRIV-001 - History loaded from encrypted file.
        """
        if not self.history_file.exists():
            return []

        encryption = get_encryption_manager()

        try:
            # Read encrypted file
            with open(self.history_file, "rb") as f:
                encrypted = f.read()

            # Decrypt
            decrypted = encryption.decrypt(encrypted)

            # Parse JSON
            history = json.loads(decrypted.decode("utf-8"))

            logger.debug(f"Loaded encrypted history: {len(history)} entries")
            return history

        except Exception as e:
            logger.warning(f"Failed to load encrypted history: {e}")
            # Try legacy plaintext migration
            return self._migrate_plaintext_history()

    def _save_history(self, history: list[dict[str, Any]]) -> None:
        """Save history to encrypted file.

        Args:
            history: List of history entries

        Security: v0.2.11 FEAT-PRIV-001 - History encrypted before writing to disk.
        """
        encryption = get_encryption_manager()

        # Serialise to JSON
        json_data = json.dumps(history, indent=2, ensure_ascii=False)

        # Encrypt
        encrypted = encryption.encrypt(json_data.encode("utf-8"))

        # Write encrypted file
        with open(self.history_file, "wb") as f:
            f.write(encrypted)

        # Set restrictive permissions
        os.chmod(self.history_file, 0o600)

        logger.debug(f"Saved encrypted history: {len(history)} entries")

    def _migrate_plaintext_history(self) -> list[dict[str, Any]]:
        """One-time migration from plaintext to encrypted history.

        Returns:
            List of history entries from legacy plaintext file

        Security: Automatically migrates existing plaintext history to encrypted format.
        """
        legacy_file = self.history_file.with_suffix(".json.legacy")

        # Check if file exists and might be plaintext
        if self.history_file.exists():
            try:
                # Try reading as plaintext
                with open(self.history_file, encoding="utf-8") as f:
                    history = json.load(f)

                logger.warning("Migrating plaintext history to encrypted format")

                # Backup plaintext
                shutil.copy(self.history_file, legacy_file)

                # Save encrypted
                self._save_history(history)

                logger.info(f"Migration complete. Legacy backup: {legacy_file}")
                return history

            except (json.JSONDecodeError, UnicodeDecodeError):
                # File already encrypted or corrupted
                logger.error("History file corrupted or already encrypted")
                return []

        return []

    def add_query(
        self,
        query: str,
        top_k: int = 5,
        answer: str | None = None,
        sources: list[str] | None = None,
    ) -> None:
        """Add a query to history.

        Args:
            query: The query text
            top_k: Number of results requested
            answer: The answer received (optional)
            sources: Source documents used (optional)
        """
        history = self._load_history()

        entry = {
            "id": len(history) + 1,
            "timestamp": datetime.now().isoformat(),
            "query": query,
            "top_k": top_k,
            "answer": answer,
            "sources": sources or [],
        }

        history.append(entry)
        self._save_history(history)
        logger.debug(f"Added query to history: {query[:50]}...")

    def get_history(
        self,
        limit: int | None = None,
        search: str | None = None,
    ) -> list[dict[str, Any]]:
        """Get query history with optional filtering.

        Args:
            limit: Maximum number of entries to return
            search: Search term to filter queries

        Returns:
            List of history entries
        """
        history = self._load_history()

        # Filter by search term if provided
        if search:
            search_lower = search.lower()
            history = [
                entry
                for entry in history
                if search_lower in entry["query"].lower()
                or (entry.get("answer") and search_lower in entry["answer"].lower())
            ]

        # Apply limit
        if limit:
            history = history[-limit:]

        return history

    def get_query_by_id(self, query_id: int) -> dict[str, Any] | None:
        """Get a specific query by ID.

        Args:
            query_id: The query ID

        Returns:
            Query entry or None if not found
        """
        history = self._load_history()
        for entry in history:
            if entry["id"] == query_id:
                return entry
        return None

    def clear_history(self) -> int:
        """Clear all history.

        Returns:
            Number of entries cleared
        """
        history = self._load_history()
        count = len(history)
        self._save_history([])
        return count

    def export_history(self, output_file: Path) -> int:
        """Export history to file.

        Args:
            output_file: Path to export file

        Returns:
            Number of entries exported
        """
        history = self._load_history()
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(history, f, indent=2, ensure_ascii=False)
        return len(history)


@click.group()
def history() -> None:
    """Manage query history.

    Store, search, and replay past queries.
    """
    pass


@history.command("list")
@click.option(
    "--limit",
    "-n",
    type=int,
    help="Maximum number of entries to show (default: all)",
)
@click.option(
    "--search",
    "-s",
    help="Search term to filter queries",
)
@click.option(
    "--format",
    "-f",
    "output_format",
    type=click.Choice(FORMAT_CHOICES + ["text"], case_sensitive=False),
    default="text",
    help="Output format",
)
def list_history(
    limit: int | None,
    search: str | None,
    output_format: str,
) -> None:
    """List query history.

    \\b
    Examples:
        ragged history list
        ragged history list --limit 10
        ragged history list --search "machine learning"
        ragged history list --format json
    """
    try:
        history_manager = QueryHistory()
        entries = history_manager.get_history(limit=limit, search=search)

        if not entries:
            if search:
                console.print(f"[yellow]No history entries matching '{search}'[/yellow]")
            else:
                console.print("[yellow]No query history found.[/yellow]")
                console.print("\nQueries will be automatically saved to history when you run:")
                console.print("  ragged query 'your question'")
            return

        if output_format == "text":
            _print_text_history(entries)
        else:
            # Prepare data for formatting
            data = [
                {
                    "id": entry["id"],
                    "timestamp": entry["timestamp"],
                    "query": entry["query"][:80] + "..."
                    if len(entry["query"]) > 80
                    else entry["query"],
                    "top_k": entry["top_k"],
                    "sources": len(entry.get("sources", [])),
                }
                for entry in entries
            ]
            print_formatted(
                data,
                format_type=output_format,  # type: ignore
                title=f"Query History ({len(entries)} entries)",
                console=console,
            )

    except Exception as e:
        console.print(f"[bold red]✗[/bold red] Failed to list history: {e}")
        logger.error(f"List history failed: {e}", exc_info=True)
        sys.exit(1)


def _print_text_history(entries: list[dict[str, Any]]) -> None:
    """Print history in text format."""
    console.print(f"\n[bold]Query History ({len(entries)} entries)[/bold]\n")

    for entry in entries:
        # Format timestamp
        timestamp = datetime.fromisoformat(entry["timestamp"])
        time_str = timestamp.strftime("%Y-%m-%d %H:%M:%S")

        # Header
        console.print(f"[bold cyan][{entry['id']}][/bold cyan] {time_str}")
        console.print(f"  Query: {entry['query']}")
        console.print(f"  Top K: {entry['top_k']}, Sources: {len(entry.get('sources', []))}")

        # Show answer preview if available
        if entry.get("answer"):
            answer = entry["answer"]
            preview = answer[:150] + "..." if len(answer) > 150 else answer
            console.print(f"  Answer: {preview}")

        console.print()


@history.command("show")
@click.argument("query_id", type=int)
@click.option(
    "--format",
    "-f",
    "output_format",
    type=click.Choice(["text", "json"], case_sensitive=False),
    default="text",
    help="Output format",
)
def show_history(query_id: int, output_format: str) -> None:
    """Show full details of a specific query.

    \\b
    Examples:
        ragged history show 5
        ragged history show 5 --format json
    """
    try:
        history_manager = QueryHistory()
        entry = history_manager.get_query_by_id(query_id)

        if not entry:
            console.print(f"[yellow]Query ID {query_id} not found in history.[/yellow]")
            sys.exit(1)

        if output_format == "json":
            print(json.dumps(entry, indent=2))
        else:
            # Format timestamp
            timestamp = datetime.fromisoformat(entry["timestamp"])
            time_str = timestamp.strftime("%Y-%m-%d %H:%M:%S")

            console.print(f"\n[bold]Query #{entry['id']}[/bold]")
            console.print(f"[dim]Timestamp: {time_str}[/dim]\n")

            console.print(f"[bold]Query:[/bold] {entry['query']}")
            console.print(f"[bold]Top K:[/bold] {entry['top_k']}")

            if entry.get("answer"):
                console.print(f"\n[bold]Answer:[/bold]\n{entry['answer']}")

            if entry.get("sources"):
                console.print(f"\n[bold]Sources ({len(entry['sources'])}):[/bold]")
                for i, source in enumerate(entry["sources"], 1):
                    console.print(f"  {i}. {source}")

            console.print()

    except Exception as e:
        console.print(f"[bold red]✗[/bold red] Failed to show history entry: {e}")
        logger.error(f"Show history failed: {e}", exc_info=True)
        sys.exit(1)


@history.command("replay")
@click.argument("query_id", type=int)
@click.option(
    "--top-k",
    "-k",
    type=int,
    help="Override number of results (uses original if not specified)",
)
def replay_query(query_id: int, top_k: int | None) -> None:
    """Replay a query from history.

    \\b
    Examples:
        ragged history replay 5
        ragged history replay 5 --top-k 10
    """
    try:
        history_manager = QueryHistory()
        entry = history_manager.get_query_by_id(query_id)

        if not entry:
            console.print(f"[yellow]Query ID {query_id} not found in history.[/yellow]")
            sys.exit(1)

        query_text = entry["query"]
        k = top_k if top_k is not None else entry["top_k"]

        console.print(f"[dim]Replaying query #{query_id}:[/dim]")
        console.print(f"[bold]{query_text}[/bold]\n")

        # Import and execute query
        from src.cli.commands.query import query as query_command

        # Create a new context and invoke the query command
        ctx = click.get_current_context()
        ctx.invoke(query_command, query=query_text, k=k, show_sources=True, output_format="text")

    except Exception as e:
        console.print(f"[bold red]✗[/bold red] Failed to replay query: {e}")
        logger.error(f"Replay query failed: {e}", exc_info=True)
        sys.exit(1)


@history.command("clear")
@click.option(
    "--yes",
    "-y",
    is_flag=True,
    help="Skip confirmation prompt",
)
def clear_history(yes: bool) -> None:
    """Clear all query history.

    \\b
    Examples:
        ragged history clear
        ragged history clear --yes
    """
    try:
        history_manager = QueryHistory()

        if not yes:
            entries = history_manager.get_history()
            if not entries:
                console.print("[yellow]No history to clear.[/yellow]")
                return

            console.print(f"[yellow]About to clear {len(entries)} history entries.[/yellow]")
            if not click.confirm("Are you sure?"):
                console.print("Cancelled.")
                return

        count = history_manager.clear_history()
        console.print(f"[green]✓[/green] Cleared {count} history entries")

    except Exception as e:
        console.print(f"[bold red]✗[/bold red] Failed to clear history: {e}")
        logger.error(f"Clear history failed: {e}", exc_info=True)
        sys.exit(1)


@history.command("export")
@click.argument("output_file", type=click.Path())
def export_history(output_file: str) -> None:
    """Export query history to JSON file.

    \\b
    Examples:
        ragged history export history.json
        ragged history export ~/Desktop/queries.json
    """
    try:
        history_manager = QueryHistory()
        output_path = Path(output_file)

        # Check if file exists
        if output_path.exists():
            if not click.confirm(f"File {output_file} exists. Overwrite?"):
                console.print("Cancelled.")
                return

        count = history_manager.export_history(output_path)
        console.print(f"[green]✓[/green] Exported {count} history entries to {output_file}")

    except Exception as e:
        console.print(f"[bold red]✗[/bold red] Failed to export history: {e}")
        logger.error(f"Export history failed: {e}", exc_info=True)
        sys.exit(1)
