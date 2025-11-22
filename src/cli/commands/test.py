"""
Testing CLI commands.

v0.3.11: CLI integration for configuration validation and testing.
"""

from pathlib import Path

import click
from rich.console import Console
from rich.table import Table

from src.testing import create_config_validator
from src.utils.logging import get_logger

console = Console()
logger = get_logger(__name__)


@click.group()
def test():
    """Run validation and quality tests."""
    pass


@test.command("config")
@click.argument("config_path", type=click.Path(exists=True, path_type=Path))
@click.option(
    "--strict",
    is_flag=True,
    help="Treat warnings as errors",
)
def test_config(config_path: Path, strict: bool):
    """
    Validate configuration file.

    CONFIG_PATH: Path to YAML configuration file

    Example:
        ragged test config config.yaml
        ragged test config config.yaml --strict
    """
    try:
        console.print(f"\n[cyan]Validating configuration:[/cyan] {config_path}\n")

        # Create validator
        validator = create_config_validator()

        # Validate
        result = validator.validate(config_path)

        # Display results
        _display_validation_results(result, strict)

        # Exit with appropriate code
        if not result.valid or (strict and result.warning_count > 0):
            raise click.Abort()

    except click.Abort:
        raise
    except Exception as e:
        logger.exception("Config validation failed")
        console.print(f"\n[red]Error:[/red] {e}")
        raise click.Abort()


def _display_validation_results(result, strict: bool):
    """Display validation results in a formatted manner."""

    # Summary
    if result.valid and result.warning_count == 0:
        console.print("[green]✓ Configuration is valid[/green]")
        console.print("  No errors or warnings found\n")
        return

    # Errors section
    if result.errors:
        console.print("[red bold]Errors:[/red bold]")
        for i, error in enumerate(result.errors, 1):
            field_str = f" ({error.field})" if error.field else ""
            console.print(
                f"  {i}. [{error.category}]{field_str} {error.message}", style="red"
            )
        console.print()

    # Warnings section
    if result.warnings:
        style = "red" if strict else "yellow"
        label = "Warnings (treated as errors):" if strict else "Warnings:"
        console.print(f"[{style} bold]{label}[/{style} bold]")
        for i, warning in enumerate(result.warnings, 1):
            field_str = f" ({warning.field})" if warning.field else ""
            console.print(
                f"  {i}. [{warning.category}]{field_str} {warning.message}",
                style=style,
            )
        console.print()

    # Summary table
    table = Table(title="Validation Summary", show_header=False)
    table.add_column("Category", style="bold")
    table.add_column("Count")

    table.add_row("Errors", f"[red]{result.error_count}[/red]")

    warning_style = "red" if strict else "yellow"
    warning_text = (
        f"[{warning_style}]{result.warning_count}[/{warning_style}]"
        if result.warning_count > 0
        else str(result.warning_count)
    )
    table.add_row("Warnings", warning_text)

    table.add_row(
        "Total Issues",
        f"[red]{result.total_issues}[/red]"
        if result.total_issues > 0
        else str(result.total_issues),
    )

    console.print(table)
    console.print()

    # Recommendation
    if result.valid and result.warning_count > 0:
        if strict:
            console.print(
                "[red]✗ Validation failed:[/red] Warnings treated as errors (--strict mode)"
            )
        else:
            console.print(
                "[yellow]⚠ Configuration valid with warnings[/yellow]"
            )
            console.print(
                "  Consider reviewing warnings for best practices"
            )
    elif not result.valid:
        console.print(
            f"[red]✗ Validation failed:[/red] Fix {result.error_count} error(s) before using this configuration"
        )


@test.command("config-string")
@click.argument("config_string")
@click.option(
    "--strict",
    is_flag=True,
    help="Treat warnings as errors",
)
def test_config_string(config_string: str, strict: bool):
    """
    Validate configuration from string.

    CONFIG_STRING: YAML configuration as string

    Example:
        ragged test config-string "chunking:\\n  chunk_size: 500"
    """
    try:
        console.print("\n[cyan]Validating configuration string[/cyan]\n")

        # Create validator
        validator = create_config_validator()

        # Validate
        result = validator.validate_string(config_string)

        # Display results
        _display_validation_results(result, strict)

        # Exit with appropriate code
        if not result.valid or (strict and result.warning_count > 0):
            raise click.Abort()

    except click.Abort:
        raise
    except Exception as e:
        logger.exception("Config validation failed")
        console.print(f"\n[red]Error:[/red] {e}")
        raise click.Abort()


# Export
__all__ = ["test"]
