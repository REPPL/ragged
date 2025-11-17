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
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose logging (INFO level)")
@click.option("--debug", is_flag=True, help="Enable debug logging (DEBUG level)")
@click.option("--quiet", "-q", is_flag=True, help="Suppress all non-essential output")
@click.pass_context
def cli(ctx: click.Context, verbose: bool, debug: bool, quiet: bool) -> None:
    """ragged - Privacy-first local RAG system.

    \b
    Examples:
        ragged add document.pdf          # Normal output
        ragged add document.pdf -v       # Verbose output
        ragged add document.pdf --debug  # Debug output
        ragged add document.pdf --quiet  # Minimal output
    """
    if click is None:
        print("Error: click and rich required. Install with: pip install click rich")
        sys.exit(1)

    # Determine log level and verbosity
    if debug:
        log_level = "DEBUG"
        verbosity = "debug"
    elif verbose:
        log_level = "INFO"
        verbosity = "verbose"
    elif quiet:
        log_level = "ERROR"
        verbosity = "quiet"
    else:
        log_level = "WARNING"
        verbosity = "normal"

    # Store verbosity in context for commands to access
    ctx.ensure_object(dict)
    ctx.obj["verbosity"] = verbosity
    ctx.obj["quiet"] = quiet
    ctx.obj["verbose"] = verbose
    ctx.obj["debug"] = debug

    setup_logging(log_level=log_level, json_format=False)


# All CLI commands extracted to cli/commands/


# Import commands from modules
from src.cli.commands.add import add
from src.cli.commands.query import query
from src.cli.commands.health import health
from src.cli.commands.docs import list_docs, clear
from src.cli.commands.config import config
from src.cli.commands.completion import completion
from src.cli.commands.validate import validate
from src.cli.commands.envinfo import env_info
from src.cli.commands.metadata import metadata
from src.cli.commands.search import search
from src.cli.commands.history import history
from src.cli.commands.exportimport import export
from src.cli.commands.cache import cache

# Register commands
cli.add_command(add)
cli.add_command(query)
cli.add_command(health)
cli.add_command(list_docs)
cli.add_command(clear)
cli.add_command(config)
cli.add_command(completion)
cli.add_command(validate)
cli.add_command(env_info)
cli.add_command(metadata)
cli.add_command(search)
cli.add_command(history)
cli.add_command(export)
cli.add_command(cache)


def main() -> None:
    """Main entry point."""
    if click is None:
        print("Error: click and rich required. Install with: pip install click rich")
        sys.exit(1)
    cli()


if __name__ == "__main__":
    main()
