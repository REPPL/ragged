"""CLI commands for managing v0.2.9 feature flags."""

import click
from rich.console import Console
from rich.table import Table
from pathlib import Path
import yaml

from src.config import get_settings


console = Console()


@click.group(name="feature-flags")
def feature_flags_group():
    """Manage v0.2.9 feature flags (runtime toggles)."""
    pass


@feature_flags_group.command("list")
@click.option("--phase", type=click.INT, help="Filter by phase (1, 2, or 3)")
@click.option("--enabled-only", is_flag=True, help="Show only enabled features")
def list_flags(phase: int | None, enabled_only: bool):
    """List all feature flags and their current status.

    Example:
        ragged feature-flags list
        ragged feature-flags list --phase 1
        ragged feature-flags list --enabled-only
    """
    settings = get_settings()
    flags = settings.feature_flags

    # Create table
    table = Table(title="v0.2.9 Feature Flags", show_header=True, header_style="bold magenta")
    table.add_column("Feature", style="cyan", no_wrap=True)
    table.add_column("Phase", justify="center", style="yellow")
    table.add_column("Status", justify="center")
    table.add_column("Description", style="dim")

    all_flags = flags.get_all_flags()

    for flag_name, is_enabled in all_flags.items():
        feature_name = flag_name.replace("enable_", "")

        # Apply filters
        try:
            feature_phase = flags.get_phase(feature_name)
        except AttributeError:
            continue  # Skip unknown features

        if phase is not None and feature_phase != phase:
            continue

        if enabled_only and not is_enabled:
            continue

        # Determine status display
        status = "✅ Enabled" if is_enabled else "❌ Disabled"
        status_style = "green" if is_enabled else "red"

        # Get description from field
        field_info = flags.model_fields[flag_name]
        description = field_info.description or "No description"

        table.add_row(
            feature_name,
            str(feature_phase),
            f"[{status_style}]{status}[/{status_style}]",
            description
        )

    console.print(table)

    # Summary
    enabled_count = len(flags.get_enabled_features())
    total_count = len(all_flags)
    console.print(f"\n[bold]Summary:[/bold] {enabled_count}/{total_count} features enabled")


@feature_flags_group.command("enable")
@click.argument("feature", type=str)
def enable_flag(feature: str):
    """Enable a feature flag.

    FEATURE should be the feature name without 'enable_' prefix.

    Example:
        ragged feature-flags enable embedder_caching
        ragged feature-flags enable batch_auto_tuning
    """
    settings = get_settings()
    flags = settings.feature_flags

    try:
        # Check if feature exists and get current status
        current_status = flags.is_enabled(feature)

        if current_status:
            console.print(f"[yellow]Feature '{feature}' is already enabled[/yellow]")
            return

        # Enable the feature
        flags.enable(feature)

        # Save to config file
        _save_flags_to_config(flags)

        console.print(f"[green]✓[/green] Enabled feature: [bold]{feature}[/bold]")

        # Show phase info
        phase = flags.get_phase(feature)
        console.print(f"  Phase: {phase}")

        # Warn about restart if needed
        console.print("\n[yellow]Note:[/yellow] Some features may require restarting ragged to take effect.")

    except AttributeError as e:
        console.print(f"[red]Error:[/red] {e}")
        console.print("\n[dim]Available features:[/dim]")
        _list_available_features()


@feature_flags_group.command("disable")
@click.argument("feature", type=str)
def disable_flag(feature: str):
    """Disable a feature flag.

    FEATURE should be the feature name without 'enable_' prefix.

    Example:
        ragged feature-flags disable embedder_caching
    """
    settings = get_settings()
    flags = settings.feature_flags

    try:
        # Check if feature exists and get current status
        current_status = flags.is_enabled(feature)

        if not current_status:
            console.print(f"[yellow]Feature '{feature}' is already disabled[/yellow]")
            return

        # Disable the feature
        flags.disable(feature)

        # Save to config file
        _save_flags_to_config(flags)

        console.print(f"[green]✓[/green] Disabled feature: [bold]{feature}[/bold]")

        # Warn about restart
        console.print("\n[yellow]Note:[/yellow] Restart ragged for changes to take effect.")

    except AttributeError as e:
        console.print(f"[red]Error:[/red] {e}")
        console.print("\n[dim]Available features:[/dim]")
        _list_available_features()


@feature_flags_group.command("enable-phase")
@click.argument("phase", type=click.INT)
def enable_phase(phase: int):
    """Enable all features in a specific phase.

    PHASE should be 1, 2, or 3.

    Example:
        ragged feature-flags enable-phase 1  # Enable all Phase 1 features
    """
    if phase not in [1, 2, 3]:
        console.print("[red]Error:[/red] Phase must be 1, 2, or 3")
        return

    settings = get_settings()
    flags = settings.feature_flags

    # Get all features in this phase
    features_in_phase = []
    for flag_name in flags.get_all_flags().keys():
        feature_name = flag_name.replace("enable_", "")
        try:
            if flags.get_phase(feature_name) == phase:
                features_in_phase.append(feature_name)
        except AttributeError:
            continue

    if not features_in_phase:
        console.print(f"[yellow]No features found in phase {phase}[/yellow]")
        return

    # Enable all features in phase
    for feature in features_in_phase:
        flags.enable(feature)

    # Save to config
    _save_flags_to_config(flags)

    console.print(f"[green]✓[/green] Enabled {len(features_in_phase)} features in Phase {phase}:")
    for feature in features_in_phase:
        console.print(f"  • {feature}")

    console.print("\n[yellow]Note:[/yellow] Restart ragged for changes to take effect.")


def _save_flags_to_config(flags):
    """Save feature flags to user config file."""
    settings = get_settings()
    config_file = settings.data_dir / "config.yml"

    # Ensure data directory exists
    settings.ensure_data_dir()

    # Load existing config or create new
    if config_file.exists():
        with open(config_file, "r") as f:
            config = yaml.safe_load(f) or {}
    else:
        config = {}

    # Update feature_flags section
    config["feature_flags"] = flags.get_all_flags()

    # Write back to file
    with open(config_file, "w") as f:
        yaml.dump(config, f, default_flow_style=False, sort_keys=False)


def _list_available_features():
    """List all available feature names."""
    settings = get_settings()
    flags = settings.feature_flags

    for flag_name in flags.get_all_flags().keys():
        feature_name = flag_name.replace("enable_", "")
        console.print(f"  • {feature_name}")
