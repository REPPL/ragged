"""
Template CLI commands.

v0.3.11: CLI integration for query templates.
"""

from pathlib import Path

import click
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
from rich.table import Table

from src.templates import TemplateEngine, TemplateError
from src.utils.logging import get_logger

console = Console()
logger = get_logger(__name__)


@click.group()
def template():
    """Manage query templates for repeatable workflows."""
    pass


@template.command("render")
@click.argument("template_path", type=click.Path(exists=True, path_type=Path))
@click.option(
    "--var",
    "-v",
    multiple=True,
    help="Template variables (key=value format)",
)
@click.option(
    "--template-dir",
    "-d",
    type=click.Path(exists=True, file_okay=False, path_type=Path),
    help="Template directory (default: current directory)",
)
@click.option(
    "--output",
    "-o",
    type=click.Path(path_type=Path),
    help="Output file (default: stdout)",
)
def render_template(
    template_path: Path,
    var: tuple,
    template_dir: Path | None,
    output: Path | None,
):
    """
    Render a template file.

    TEMPLATE_PATH: Path to the template file (.j2)

    Example:
        ragged template render summary.j2 -v document=paper.pdf
    """
    try:
        # Parse variables
        variables = {}
        for v in var:
            if "=" not in v:
                console.print(f"[red]Invalid variable format: {v}[/red]")
                console.print("Use format: key=value")
                raise click.Abort()

            key, value = v.split("=", 1)
            variables[key] = value

        # Create template engine (no query functions for now)
        # Default template_dir to template's parent directory if not specified
        if template_dir is None:
            template_dir = template_path.parent
        engine = TemplateEngine(template_dir=template_dir)

        # Render template
        console.print(f"[cyan]Rendering template:[/cyan] {template_path}")

        result = engine.render_file(template_path, variables)

        # Output
        if output:
            output.write_text(result)
            console.print(f"[green]✓[/green] Output written to: {output}")
        else:
            console.print("\n[bold]Template Output:[/bold]")
            console.print(Panel(result, border_style="green"))

    except TemplateError as e:
        console.print(f"[red]Template error:[/red] {e}")
        raise click.Abort()
    except Exception as e:
        logger.exception("Template render failed")
        console.print(f"[red]Error:[/red] {e}")
        raise click.Abort()


@template.command("validate")
@click.argument("template_path", type=click.Path(exists=True, path_type=Path))
def validate_template(template_path: Path):
    """
    Validate template syntax.

    TEMPLATE_PATH: Path to the template file (.j2)

    Example:
        ragged template validate summary.j2
    """
    try:
        # Read template
        template_content = template_path.read_text()

        # Create engine and validate
        engine = TemplateEngine()
        result = engine.validate_template(template_content)

        if result["valid"]:
            console.print(f"[green]✓ Template is valid:[/green] {template_path}")
        else:
            console.print(f"[red]✗ Template has errors:[/red] {template_path}")
            console.print(f"\n[yellow]Error:[/yellow] {result['error']}")
            if "line" in result:
                console.print(f"[yellow]Line:[/yellow] {result['line']}")
            raise click.Abort()

    except Exception as e:
        logger.exception("Template validation failed")
        console.print(f"[red]Error:[/red] {e}")
        raise click.Abort()


@template.command("list")
@click.option(
    "--template-dir",
    "-d",
    type=click.Path(exists=True, file_okay=False, path_type=Path),
    default=Path("."),
    help="Template directory (default: current directory)",
)
def list_templates(template_dir: Path):
    """
    List available templates.

    Example:
        ragged template list
        ragged template list -d templates/
    """
    try:
        # Create engine
        engine = TemplateEngine(template_dir=template_dir)

        # Get templates
        templates = engine.list_templates()

        if not templates:
            console.print(f"[yellow]No templates found in:[/yellow] {template_dir}")
            console.print("\nTemplates should have .j2 extension")
            return

        # Display table
        table = Table(title=f"Templates in {template_dir}")
        table.add_column("Template", style="cyan")
        table.add_column("Path", style="dim")

        for template in templates:
            table.add_row(template.name, str(template))

        console.print(table)
        console.print(f"\n[green]{len(templates)} template(s) found[/green]")

    except Exception as e:
        logger.exception("Template list failed")
        console.print(f"[red]Error:[/red] {e}")
        raise click.Abort()


@template.command("show")
@click.argument("template_path", type=click.Path(exists=True, path_type=Path))
@click.option(
    "--syntax-highlight/--no-syntax-highlight",
    default=True,
    help="Enable syntax highlighting",
)
def show_template(template_path: Path, syntax_highlight: bool):
    """
    Show template contents.

    TEMPLATE_PATH: Path to the template file (.j2)

    Example:
        ragged template show summary.j2
    """
    try:
        # Read template
        content = template_path.read_text()

        console.print(f"\n[bold]Template:[/bold] {template_path}")

        if syntax_highlight:
            # Syntax highlighting for Jinja2
            syntax = Syntax(content, "jinja2", theme="monokai", line_numbers=True)
            console.print(syntax)
        else:
            console.print(Panel(content, border_style="cyan"))

    except Exception as e:
        logger.exception("Template show failed")
        console.print(f"[red]Error:[/red] {e}")
        raise click.Abort()


# Export
__all__ = ["template"]
