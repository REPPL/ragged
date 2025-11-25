"""Persona management commands for ragged CLI.

v0.4.5: User persona management for context switching.
"""
from __future__ import annotations


import sys
from pathlib import Path
from typing import Any

import click

from ragged.cli.common import console
from ragged.cli.formatters import FORMAT_CHOICES, print_formatted
from ragged.memory.persona import PersonaManager
from ragged.utils.logging import get_logger

logger = get_logger(__name__)


@click.group()
def persona() -> None:
    """Manage user personas for context switching.

    Create, switch, and manage personas to organise your RAG interactions
    across different contexts (e.g., researcher, student, developer).

    All persona data is stored locally with full privacy.
    """
    pass


@persona.command("create")
@click.argument("name")
@click.option(
    "--description",
    "-d",
    help="Persona description",
)
@click.option(
    "--focus",
    "-f",
    multiple=True,
    help="Focus area/topic (can be specified multiple times)",
)
@click.option(
    "--project",
    "-p",
    multiple=True,
    help="Active project (can be specified multiple times)",
)
def create_persona(
    name: str,
    description: str | None,
    focus: tuple[str, ...],
    project: tuple[str, ...],
) -> None:
    """Create a new persona.

    \b
    Examples:
        ragged persona create researcher --description "ML researcher"
        ragged persona create researcher -f "RAG" -f "NLP" -p "thesis"
        ragged persona create student --focus "Learning Python"
    """
    try:
        manager = PersonaManager()

        persona_obj = manager.create(
            name=name,
            description=description or "",
            focus=list(focus) if focus else None,
            active_projects=list(project) if project else None,
        )

        console.print(f"\n[green]✓[/green] Created persona: [bold]{persona_obj.name}[/bold]")
        if persona_obj.description:
            console.print(f"Description: {persona_obj.description}")
        if persona_obj.focus_areas:
            console.print(f"Focus: {', '.join(persona_obj.focus_areas)}")
        if persona_obj.active_projects:
            console.print(f"Projects: {', '.join(persona_obj.active_projects)}")

        console.print(f"\n[dim]Use 'ragged persona switch {name}' to activate[/dim]\n")

    except ValueError as e:
        console.print(f"[bold red]✗[/bold red] {e}")
        sys.exit(1)
    except Exception as e:
        console.print(f"[bold red]✗[/bold red] Failed to create persona: {e}")
        logger.error(f"Create persona failed: {e}", exc_info=True)
        sys.exit(1)


@persona.command("switch")
@click.argument("name")
def switch_persona(name: str) -> None:
    """Switch to a different persona.

    \b
    Examples:
        ragged persona switch researcher
        ragged persona switch student
    """
    try:
        manager = PersonaManager()
        persona_obj = manager.switch(name)

        console.print(f"\n[green]✓[/green] Switched to persona: [bold]{persona_obj.name}[/bold]")
        if persona_obj.description:
            console.print(f"Description: {persona_obj.description}")
        if persona_obj.focus_areas:
            console.print(f"Focus: {', '.join(persona_obj.focus_areas)}")

        console.print(f"\n[dim]Usage: #{persona_obj.usage_count} times[/dim]\n")

    except KeyError as e:
        console.print(f"[bold red]✗[/bold red] {e}")
        console.print("\n[dim]Use 'ragged persona list' to see available personas[/dim]")
        sys.exit(1)
    except Exception as e:
        console.print(f"[bold red]✗[/bold red] Failed to switch persona: {e}")
        logger.error(f"Switch persona failed: {e}", exc_info=True)
        sys.exit(1)


@persona.command("list")
@click.option(
    "--format",
    "-f",
    "output_format",
    type=click.Choice(FORMAT_CHOICES + ["text"], case_sensitive=False),
    default="text",
    help="Output format",
)
def list_personas(output_format: str) -> None:
    """List all personas.

    \b
    Examples:
        ragged persona list
        ragged persona list --format json
        ragged persona list --format table
    """
    try:
        manager = PersonaManager()
        persona_names = manager.list()

        if not persona_names:
            console.print("\n[yellow]No personas created yet.[/yellow]")
            console.print("[dim]Use 'ragged persona create <name>' to create one[/dim]\n")
            return

        # Get detailed info for each persona
        personas_data = []
        active_persona = manager.active_persona

        for name in persona_names:
            persona_obj = manager.get(name)
            personas_data.append(
                {
                    "name": persona_obj.name,
                    "description": persona_obj.description or "-",
                    "focus_areas": ", ".join(persona_obj.focus_areas)
                    if persona_obj.focus_areas
                    else "-",
                    "usage_count": persona_obj.usage_count,
                    "active": "✓" if name == active_persona else "",
                }
            )

        if output_format == "text":
            console.print(f"\n[bold]Personas ({len(personas_data)})[/bold]\n")

            for p in personas_data:
                active_marker = " [green]●[/green]" if p["active"] else ""
                console.print(f"[bold]{p['name']}[/bold]{active_marker}")
                if p["description"] != "-":
                    console.print(f"  Description: {p['description']}")
                if p["focus_areas"] != "-":
                    console.print(f"  Focus: {p['focus_areas']}")
                console.print(f"  Usage: {p['usage_count']} times")
                console.print()

            if active_persona:
                console.print(f"[dim]Active: {active_persona}[/dim]\n")
        else:
            print_formatted(
                personas_data,
                format_type=output_format,  # type: ignore
                title="Personas",
                console=console,
            )

    except Exception as e:
        console.print(f"[bold red]✗[/bold red] Failed to list personas: {e}")
        logger.error(f"List personas failed: {e}", exc_info=True)
        sys.exit(1)


@persona.command("show")
@click.argument("name")
@click.option(
    "--format",
    "-f",
    "output_format",
    type=click.Choice(FORMAT_CHOICES + ["text"], case_sensitive=False),
    default="text",
    help="Output format",
)
def show_persona(name: str, output_format: str) -> None:
    """Show detailed information about a persona.

    \b
    Examples:
        ragged persona show researcher
        ragged persona show researcher --format json
    """
    try:
        manager = PersonaManager()
        persona_obj = manager.get(name)

        data = {
            "name": persona_obj.name,
            "description": persona_obj.description,
            "focus_areas": persona_obj.focus_areas,
            "active_projects": persona_obj.active_projects,
            "preferences": persona_obj.preferences,
            "created_at": persona_obj.created_at.isoformat(),
            "last_used": persona_obj.last_used.isoformat(),
            "usage_count": persona_obj.usage_count,
        }

        if output_format == "text":
            console.print(f"\n[bold]Persona: {persona_obj.name}[/bold]\n")
            if persona_obj.description:
                console.print(f"Description: {persona_obj.description}")
            if persona_obj.focus_areas:
                console.print(f"Focus Areas: {', '.join(persona_obj.focus_areas)}")
            if persona_obj.active_projects:
                console.print(f"Active Projects: {', '.join(persona_obj.active_projects)}")
            if persona_obj.preferences:
                console.print(f"Preferences: {persona_obj.preferences}")
            console.print(f"\nCreated: {persona_obj.created_at.strftime('%Y-%m-%d %H:%M')}")
            console.print(f"Last Used: {persona_obj.last_used.strftime('%Y-%m-%d %H:%M')}")
            console.print(f"Usage Count: {persona_obj.usage_count} times\n")
        else:
            print_formatted(
                [data],
                format_type=output_format,  # type: ignore
                title=f"Persona: {name}",
                console=console,
            )

    except KeyError as e:
        console.print(f"[bold red]✗[/bold red] {e}")
        sys.exit(1)
    except Exception as e:
        console.print(f"[bold red]✗[/bold red] Failed to show persona: {e}")
        logger.error(f"Show persona failed: {e}", exc_info=True)
        sys.exit(1)


@persona.command("delete")
@click.argument("name")
@click.option(
    "--yes",
    "-y",
    is_flag=True,
    help="Skip confirmation prompt",
)
def delete_persona(name: str, yes: bool) -> None:
    """Delete a persona.

    \b
    Examples:
        ragged persona delete old-persona
        ragged persona delete old-persona --yes
    """
    try:
        manager = PersonaManager()

        # Check if persona exists
        persona_obj = manager.get(name)

        # Confirm deletion
        if not yes:
            console.print(f"\n[yellow]About to delete persona:[/yellow] [bold]{name}[/bold]")
            if persona_obj.description:
                console.print(f"Description: {persona_obj.description}")
            console.print(f"Usage: {persona_obj.usage_count} times")
            console.print(
                "\n[dim]This will NOT delete associated interaction history.[/dim]"
            )
            console.print(
                "[dim]Use 'ragged memory clear --persona {name}' to delete interactions.[/dim]\n"
            )

            if not click.confirm("Continue?"):
                console.print("Cancelled.")
                return

        # Delete persona
        manager.delete(name, confirm=True)

        console.print(f"\n[green]✓[/green] Deleted persona: [bold]{name}[/bold]\n")

    except KeyError as e:
        console.print(f"[bold red]✗[/bold red] {e}")
        sys.exit(1)
    except Exception as e:
        console.print(f"[bold red]✗[/bold red] Failed to delete persona: {e}")
        logger.error(f"Delete persona failed: {e}", exc_info=True)
        sys.exit(1)


@persona.command("active")
def show_active() -> None:
    """Show currently active persona.

    \b
    Examples:
        ragged persona active
    """
    try:
        manager = PersonaManager()
        active = manager.get_active()

        if not active:
            console.print("\n[yellow]No active persona set.[/yellow]")
            console.print("[dim]Use 'ragged persona switch <name>' to activate one[/dim]\n")
            return

        console.print(f"\n[bold]Active Persona:[/bold] {active.name}")
        if active.description:
            console.print(f"Description: {active.description}")
        if active.focus_areas:
            console.print(f"Focus: {', '.join(active.focus_areas)}")
        console.print(f"Usage: {active.usage_count} times\n")

    except Exception as e:
        console.print(f"[bold red]✗[/bold red] Failed to get active persona: {e}")
        logger.error(f"Get active persona failed: {e}", exc_info=True)
        sys.exit(1)
