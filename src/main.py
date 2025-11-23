"""
Command-line interface for ragged.

Provides CLI commands for document ingestion, querying, and management.
"""

import sys

from ragged import __version__
from ragged.cli.common import click
from ragged.utils.logging import get_logger, setup_logging

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
        ragged ingest pdf document.pdf           # Normal output
        ragged ingest pdf document.pdf -v        # Verbose output
        ragged ingest pdf document.pdf --debug   # Debug output
        ragged ingest pdf document.pdf --quiet   # Minimal output
        ragged query text "your question"        # Multi-modal query
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

    # v0.2.9: Warm up embedder cache in background (if enabled)
    from ragged.embeddings.factory import warmup_embedder_cache
    warmup_embedder_cache()


# All CLI commands extracted to cli/commands/


# Import commands from modules
from ragged.cli.commands.benchmark import benchmark
from ragged.cli.commands.cache import cache
from ragged.cli.commands.completion import completion
from ragged.cli.commands.config import config
from ragged.cli.commands.docs import clear, list_docs
from ragged.cli.commands.envinfo import env_info
from ragged.cli.commands.explain import explain
from ragged.cli.commands.exportimport import export
from ragged.cli.commands.feature_flags import feature_flags_group
from ragged.cli.commands.gpu import gpu  # v0.5.3: GPU management
from ragged.cli.commands.health import health
from ragged.cli.commands.history import history
from ragged.cli.commands.ingest import ingest  # v0.5.3: Multi-modal ingestion
from ragged.cli.commands.memory import memory  # v0.4.5: Memory/interaction management
from ragged.cli.commands.metadata import metadata
from ragged.cli.commands.monitor import monitor
from ragged.cli.commands.persona import persona  # v0.4.5: Persona management
from ragged.cli.commands.query_multimodal import query_group  # v0.5.3: Multi-modal query
from ragged.cli.commands.search import search
from ragged.cli.commands.serve import serve  # v0.3.12: API server
from ragged.cli.commands.show import show  # v0.3.5: PDF correction metadata viewer
from ragged.cli.commands.storage import storage  # v0.5.3: Storage management
from ragged.cli.commands.template import template  # v0.3.11: Template commands
from ragged.cli.commands.test import test  # v0.3.11: Testing commands
from ragged.cli.commands.validate import validate
from ragged.cli.commands.versions import versions  # v0.3.7a: Document version tracking

# Register commands
cli.add_command(query_group)  # v0.5.3: Multi-modal query group
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
cli.add_command(feature_flags_group)
cli.add_command(monitor)
cli.add_command(benchmark)
cli.add_command(explain)
cli.add_command(show)  # v0.3.5: PDF correction metadata viewer
cli.add_command(versions)  # v0.3.7a: Document version tracking
cli.add_command(template)  # v0.3.11: Template commands
cli.add_command(test)  # v0.3.11: Testing commands
cli.add_command(serve)  # v0.3.12: API server
cli.add_command(persona)  # v0.4.5: Persona management
cli.add_command(memory)  # v0.4.5: Memory/interaction management
cli.add_command(ingest)  # v0.5.3: Multi-modal ingestion
cli.add_command(gpu)  # v0.5.3: GPU management
cli.add_command(storage)  # v0.5.3: Storage management


def main() -> None:
    """Main entry point."""
    if click is None:
        print("Error: click and rich required. Install with: pip install click rich")
        sys.exit(1)
    cli()


if __name__ == "__main__":
    main()
