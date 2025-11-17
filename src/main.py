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
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose logging")
@click.option("--debug", is_flag=True, help="Enable debug logging")
def cli(verbose: bool, debug: bool) -> None:
    """ragged - Privacy-first local RAG system."""
    if click is None:
        print("Error: click and rich required. Install with: pip install click rich")
        sys.exit(1)
    log_level = "DEBUG" if debug else ("INFO" if verbose else "WARNING")
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

# Register commands
cli.add_command(add)
cli.add_command(query)
cli.add_command(health)
cli.add_command(list_docs)
cli.add_command(clear)
cli.add_command(config)
cli.add_command(completion)
cli.add_command(validate)


def main() -> None:
    """Main entry point."""
    if click is None:
        print("Error: click and rich required. Install with: pip install click rich")
        sys.exit(1)
    cli()


if __name__ == "__main__":
    main()
