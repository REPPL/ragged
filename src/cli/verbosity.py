"""Verbosity control utilities for CLI commands.

Provides helpers for commands to respect --verbose, --debug, and --quiet flags.
"""

from typing import Literal, Optional

import click
from rich.console import Console

VerbosityLevel = Literal["quiet", "normal", "verbose", "debug"]


def get_verbosity(ctx: Optional[click.Context] = None) -> VerbosityLevel:
    """Get current verbosity level from Click context.

    Args:
        ctx: Click context (auto-detected if None)

    Returns:
        Verbosity level: quiet, normal, verbose, or debug
    """
    if ctx is None:
        ctx = click.get_current_context(silent=True)

    if ctx and ctx.obj:
        return ctx.obj.get("verbosity", "normal")  # type: ignore

    return "normal"


def is_quiet(ctx: Optional[click.Context] = None) -> bool:
    """Check if quiet mode is enabled.

    Args:
        ctx: Click context (auto-detected if None)

    Returns:
        True if --quiet flag was used
    """
    if ctx is None:
        ctx = click.get_current_context(silent=True)

    if ctx and ctx.obj:
        return ctx.obj.get("quiet", False)

    return False


def is_verbose(ctx: Optional[click.Context] = None) -> bool:
    """Check if verbose mode is enabled.

    Args:
        ctx: Click context (auto-detected if None)

    Returns:
        True if --verbose flag was used
    """
    if ctx is None:
        ctx = click.get_current_context(silent=True)

    if ctx and ctx.obj:
        return ctx.obj.get("verbose", False)

    return False


def is_debug(ctx: Optional[click.Context] = None) -> bool:
    """Check if debug mode is enabled.

    Args:
        ctx: Click context (auto-detected if None)

    Returns:
        True if --debug flag was used
    """
    if ctx is None:
        ctx = click.get_current_context(silent=True)

    if ctx and ctx.obj:
        return ctx.obj.get("debug", False)

    return False


def vprint(
    message: str,
    console: Optional[Console] = None,
    min_verbosity: VerbosityLevel = "normal",
    ctx: Optional[click.Context] = None,
    **kwargs: any,
) -> None:
    """Print message only if verbosity level is sufficient.

    Args:
        message: Message to print
        console: Rich console (uses default if None)
        min_verbosity: Minimum verbosity level required to print
        ctx: Click context (auto-detected if None)
        **kwargs: Additional arguments passed to console.print()

    Example:
        vprint("Processing...", min_verbosity="verbose")
        # Only prints if --verbose or --debug is used
    """
    if console is None:
        console = Console()

    current = get_verbosity(ctx)

    # Verbosity hierarchy: quiet < normal < verbose < debug
    verbosity_order = {"quiet": 0, "normal": 1, "verbose": 2, "debug": 3}

    if verbosity_order[current] >= verbosity_order[min_verbosity]:
        console.print(message, **kwargs)


def vprint_debug(
    message: str,
    console: Optional[Console] = None,
    ctx: Optional[click.Context] = None,
) -> None:
    """Print debug message (only shown with --debug).

    Args:
        message: Debug message
        console: Rich console
        ctx: Click context
    """
    vprint(message, console, min_verbosity="debug", ctx=ctx, style="dim")


def vprint_verbose(
    message: str,
    console: Optional[Console] = None,
    ctx: Optional[click.Context] = None,
) -> None:
    """Print verbose message (only shown with --verbose or --debug).

    Args:
        message: Verbose message
        console: Rich console
        ctx: Click context
    """
    vprint(message, console, min_verbosity="verbose", ctx=ctx)


def vprint_info(
    message: str,
    console: Optional[Console] = None,
    ctx: Optional[click.Context] = None,
) -> None:
    """Print info message (shown in normal, verbose, and debug modes).

    Args:
        message: Info message
        console: Rich console
        ctx: Click context
    """
    vprint(message, console, min_verbosity="normal", ctx=ctx)


# Decorator for commands that should respect verbosity
def respects_verbosity(func: any) -> any:
    """Decorator to mark commands that respect verbosity settings.

    This decorator adds @click.pass_context to the command so it
    can access verbosity settings.

    Usage:
        @click.command()
        @respects_verbosity
        def my_command(ctx):
            if is_verbose(ctx):
                print("Verbose output")
    """
    return click.pass_context(func)
