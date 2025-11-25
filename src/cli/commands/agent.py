"""Agent and workflow CLI commands for ragged.

Phase 2 CLI: Commands for running agents and workflows.
"""

import asyncio
import json
import sys
from pathlib import Path
from typing import Optional

import click

from ragged.cli.common import console
from ragged.utils.logging import get_logger

logger = get_logger(__name__)


@click.group()
def agent() -> None:
    """Run agents and workflows.

    \b
    Commands:
        run       - Execute a task with an agent
        workflow  - Run a workflow from file or template
        tools     - List available agent tools
        templates - List available workflow templates

    \b
    Examples:
        ragged agent run "Find documents about auth"
        ragged agent workflow search_and_summarise --input query="security"
        ragged agent tools
    """
    pass


@agent.command("run")
@click.argument("task")
@click.option(
    "--max-steps",
    type=int,
    default=10,
    help="Maximum execution steps (default: 10)",
)
@click.option(
    "--timeout",
    type=int,
    default=300,
    help="Timeout in seconds (default: 300)",
)
@click.option(
    "--verbose", "-v",
    is_flag=True,
    help="Show detailed execution steps",
)
@click.option(
    "--json",
    "output_json",
    is_flag=True,
    help="Output result as JSON",
)
def run_agent(
    task: str,
    max_steps: int,
    timeout: int,
    verbose: bool,
    output_json: bool,
) -> None:
    """Execute a task with an agent.

    The agent will plan and execute steps to complete the task using
    available RAG tools (search, ingest, query).

    \b
    Examples:
        ragged agent run "Find documents about authentication"
        ragged agent run "Summarise the security guidelines" --verbose
        ragged agent run "Search for API docs" --json
    """
    try:
        from ragged.agents import Agent, AgentConfig, ToolRegistry

        # Create registry with default tools
        registry = ToolRegistry()
        registry.register_defaults()

        # Configure agent
        config = AgentConfig(
            max_steps=max_steps,
            timeout_seconds=timeout,
            verbose=verbose,
        )

        # Create and run agent
        agent_instance = Agent(tool_registry=registry, config=config)

        if verbose and console:
            console.print(f"[bold]Running task:[/bold] {task}")
            console.print(f"[dim]Max steps: {max_steps}, Timeout: {timeout}s[/dim]")
            console.print()

        # Run async
        result = asyncio.run(agent_instance.run(task))

        if output_json:
            print(json.dumps(result.to_dict(), indent=2, default=str))
        else:
            _display_agent_result(result, verbose)

    except ImportError as e:
        if console:
            console.print(f"[red]Error:[/red] Missing dependency: {e}")
        else:
            print(f"Error: Missing dependency: {e}")
        sys.exit(1)

    except Exception as e:
        logger.exception(f"Agent execution failed: {e}")
        if console:
            console.print(f"[red]Error:[/red] {e}")
        else:
            print(f"Error: {e}")
        sys.exit(1)


@agent.command("workflow")
@click.argument("name_or_path")
@click.option(
    "--input", "-i",
    "inputs",
    multiple=True,
    help="Input values as key=value pairs",
)
@click.option(
    "--verbose", "-v",
    is_flag=True,
    help="Show detailed execution steps",
)
@click.option(
    "--json",
    "output_json",
    is_flag=True,
    help="Output result as JSON",
)
@click.option(
    "--dry-run",
    is_flag=True,
    help="Validate workflow without executing",
)
def run_workflow(
    name_or_path: str,
    inputs: tuple[str, ...],
    verbose: bool,
    output_json: bool,
    dry_run: bool,
) -> None:
    """Run a workflow from file or template.

    NAME_OR_PATH can be:
    - A template name (e.g., 'search_and_summarise')
    - A path to a workflow JSON file

    \b
    Examples:
        ragged agent workflow search_and_summarise --input query="auth"
        ragged agent workflow ./my_workflow.json --input path="/docs/readme.md"
        ragged agent workflow ingest_and_query -i path="doc.pdf" -i question="What?"
    """
    try:
        from ragged.agents import ToolRegistry
        from ragged.agents.workflows import (
            WorkflowExecutor,
            load_workflow,
            validate_workflow,
        )
        from ragged.agents.workflows.definition import WORKFLOW_TEMPLATES

        # Parse inputs
        input_dict = {}
        for inp in inputs:
            if "=" in inp:
                key, value = inp.split("=", 1)
                input_dict[key.strip()] = value.strip()
            else:
                if console:
                    console.print(f"[yellow]Warning:[/yellow] Ignoring invalid input: {inp}")

        # Load workflow
        path = Path(name_or_path)
        if path.exists() and path.suffix == ".json":
            workflow = load_workflow(path)
        elif name_or_path in WORKFLOW_TEMPLATES:
            workflow = WORKFLOW_TEMPLATES[name_or_path]
        else:
            if console:
                console.print(f"[red]Error:[/red] Workflow not found: {name_or_path}")
                console.print("[dim]Use 'ragged agent templates' to see available templates[/dim]")
            else:
                print(f"Error: Workflow not found: {name_or_path}")
            sys.exit(1)

        if verbose and console:
            console.print(f"[bold]Workflow:[/bold] {workflow.name}")
            console.print(f"[dim]{workflow.description}[/dim]")
            console.print(f"[dim]Steps: {len(workflow.steps)}[/dim]")
            console.print()

        # Create registry
        registry = ToolRegistry()
        registry.register_defaults()

        # Validate workflow
        errors = validate_workflow(workflow, [t.spec.name for t in registry.list_tools()])

        if errors:
            if console:
                console.print("[red]Workflow validation errors:[/red]")
                for error in errors:
                    console.print(f"  - {error}")
            else:
                print("Workflow validation errors:")
                for error in errors:
                    print(f"  - {error}")
            sys.exit(1)

        if dry_run:
            if console:
                console.print("[green]✓[/green] Workflow validated successfully")
            else:
                print("Workflow validated successfully")
            return

        # Execute workflow
        executor = WorkflowExecutor(registry)
        result = asyncio.run(executor.execute(workflow, inputs=input_dict))

        if output_json:
            print(json.dumps(result.to_dict(), indent=2, default=str))
        else:
            _display_workflow_result(result, verbose)

    except ImportError as e:
        if console:
            console.print(f"[red]Error:[/red] Missing dependency: {e}")
        else:
            print(f"Error: Missing dependency: {e}")
        sys.exit(1)

    except Exception as e:
        logger.exception(f"Workflow execution failed: {e}")
        if console:
            console.print(f"[red]Error:[/red] {e}")
        else:
            print(f"Error: {e}")
        sys.exit(1)


@agent.command("tools")
@click.option(
    "--category",
    type=click.Choice(["rag", "storage", "analysis", "external", "system"]),
    help="Filter by category",
)
@click.option(
    "--json",
    "output_json",
    is_flag=True,
    help="Output as JSON",
)
def list_tools(
    category: Optional[str],
    output_json: bool,
) -> None:
    """List available agent tools.

    \b
    Examples:
        ragged agent tools
        ragged agent tools --category rag
        ragged agent tools --json
    """
    try:
        from ragged.agents import ToolRegistry
        from ragged.agents.base import ToolCategory

        registry = ToolRegistry()
        registry.register_defaults()

        # Filter by category if specified
        filter_category = None
        if category:
            filter_category = ToolCategory(category)

        tools = registry.list_tools(category=filter_category)

        if output_json:
            print(json.dumps(registry.to_dict(), indent=2))
            return

        if not tools:
            if console:
                console.print("[yellow]No tools registered[/yellow]")
            else:
                print("No tools registered")
            return

        if console:
            from rich.table import Table

            table = Table(title="Available Tools")
            table.add_column("Name", style="cyan")
            table.add_column("Category", style="green")
            table.add_column("Description")
            table.add_column("Confirm", style="yellow")

            for tool in tools:
                spec = tool.spec
                table.add_row(
                    spec.name,
                    spec.category.value,
                    spec.description[:50] + "..." if len(spec.description) > 50 else spec.description,
                    "Yes" if spec.requires_confirmation else "No",
                )

            console.print(table)
        else:
            print("Available Tools:")
            for tool in tools:
                spec = tool.spec
                print(f"  {spec.name} ({spec.category.value}): {spec.description[:50]}...")

    except ImportError as e:
        if console:
            console.print(f"[red]Error:[/red] Missing dependency: {e}")
        else:
            print(f"Error: Missing dependency: {e}")
        sys.exit(1)


@agent.command("templates")
@click.option(
    "--json",
    "output_json",
    is_flag=True,
    help="Output as JSON",
)
def list_templates(output_json: bool) -> None:
    """List available workflow templates.

    \b
    Examples:
        ragged agent templates
        ragged agent templates --json
    """
    try:
        from ragged.agents.workflows.definition import WORKFLOW_TEMPLATES

        if output_json:
            templates_dict = {
                k: v.to_dict() for k, v in WORKFLOW_TEMPLATES.items()
            }
            print(json.dumps(templates_dict, indent=2))
            return

        if not WORKFLOW_TEMPLATES:
            if console:
                console.print("[yellow]No templates available[/yellow]")
            else:
                print("No templates available")
            return

        if console:
            from rich.table import Table

            table = Table(title="Workflow Templates")
            table.add_column("Name", style="cyan")
            table.add_column("Description")
            table.add_column("Steps", justify="right")
            table.add_column("Inputs")

            for name, workflow in WORKFLOW_TEMPLATES.items():
                inputs = ", ".join(workflow.inputs.keys()) if workflow.inputs else "-"
                table.add_row(
                    name,
                    workflow.description[:40] + "..." if len(workflow.description) > 40 else workflow.description,
                    str(len(workflow.steps)),
                    inputs,
                )

            console.print(table)
        else:
            print("Workflow Templates:")
            for name, workflow in WORKFLOW_TEMPLATES.items():
                print(f"  {name}: {workflow.description}")
                print(f"    Steps: {len(workflow.steps)}")
                if workflow.inputs:
                    print(f"    Inputs: {', '.join(workflow.inputs.keys())}")

    except ImportError as e:
        if console:
            console.print(f"[red]Error:[/red] Missing dependency: {e}")
        else:
            print(f"Error: Missing dependency: {e}")
        sys.exit(1)


def _display_agent_result(result, verbose: bool) -> None:
    """Display agent result in human-readable format."""
    from ragged.agents import AgentState

    if console:
        # Status
        if result.state == AgentState.COMPLETED:
            console.print("[green]✓ Task completed[/green]")
        else:
            console.print(f"[red]✗ Task failed: {result.state.value}[/red]")

        # Steps summary
        if verbose and result.steps:
            console.print()
            console.print(f"[bold]Steps executed:[/bold] {len(result.steps)}")
            for step in result.steps:
                status = "✓" if step.tool_result and step.tool_result.success else "✗"
                console.print(f"  {status} Step {step.step_number}: {step.reasoning[:50]}...")

        # Output
        if result.output:
            console.print()
            console.print("[bold]Result:[/bold]")
            if isinstance(result.output, dict):
                console.print_json(data=result.output)
            elif isinstance(result.output, list):
                for i, item in enumerate(result.output[:5]):  # Show first 5
                    if isinstance(item, dict):
                        text = item.get("text", str(item))[:100]
                        console.print(f"  {i+1}. {text}...")
                    else:
                        console.print(f"  {i+1}. {str(item)[:100]}...")
                if len(result.output) > 5:
                    console.print(f"  ... and {len(result.output) - 5} more")
            else:
                console.print(f"  {result.output}")

        # Error
        if result.error:
            console.print()
            console.print(f"[red]Error:[/red] {result.error}")

        # Duration
        console.print()
        console.print(f"[dim]Duration: {result.total_duration_ms:.0f}ms[/dim]")

    else:
        print(f"Status: {result.state.value}")
        if result.output:
            print(f"Result: {result.output}")
        if result.error:
            print(f"Error: {result.error}")
        print(f"Duration: {result.total_duration_ms:.0f}ms")


def _display_workflow_result(result, verbose: bool) -> None:
    """Display workflow result in human-readable format."""
    from ragged.agents.workflows import WorkflowState

    if console:
        # Status
        if result.state == WorkflowState.COMPLETED:
            console.print("[green]✓ Workflow completed[/green]")
        else:
            console.print(f"[red]✗ Workflow failed: {result.state.value}[/red]")

        # Steps summary
        if verbose and result.step_results:
            console.print()
            console.print(f"[bold]Steps executed:[/bold] {len(result.step_results)}")
            for step in result.step_results:
                status = "✓" if step.success else "✗"
                duration = f"{step.duration_ms:.0f}ms"
                console.print(f"  {status} {step.step_id} ({duration})")
                if not step.success and step.error:
                    console.print(f"    [red]{step.error}[/red]")

        # Outputs
        if result.outputs.get("result"):
            console.print()
            console.print("[bold]Result:[/bold]")
            output = result.outputs["result"]
            if isinstance(output, dict):
                console.print_json(data=output)
            else:
                console.print(f"  {output}")

        # Error
        if result.error:
            console.print()
            console.print(f"[red]Error:[/red] {result.error}")

        # Duration
        console.print()
        console.print(f"[dim]Duration: {result.duration_ms:.0f}ms[/dim]")

    else:
        print(f"Status: {result.state.value}")
        if result.outputs.get("result"):
            print(f"Result: {result.outputs['result']}")
        if result.error:
            print(f"Error: {result.error}")
        print(f"Duration: {result.duration_ms:.0f}ms")
