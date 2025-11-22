"""Show command for viewing PDF correction metadata.

v0.3.5: Display quality reports, corrections, and uncertainties for processed PDFs.
"""

import json
from pathlib import Path

import click
from rich.table import Table
from rich.panel import Panel

from src.cli.common import console
from src.utils.logging import get_logger

logger = get_logger(__name__)


@click.group()
def show():
    """View PDF correction metadata and quality reports."""
    pass


@show.command()
@click.argument("document_id", type=str)
def quality(document_id: str) -> None:
    """Display quality report for a document.

    DOCUMENT_ID is the document identifier (e.g., from 'ragged add').

    Example:
        ragged show quality doc_abc123
    """
    metadata_dir = Path("data/documents/.ragged") / document_id

    if not metadata_dir.exists():
        console.print(f"[red]✗[/red] No metadata found for document: {document_id}")
        console.print(f"[dim]Expected directory: {metadata_dir}[/dim]")
        return

    quality_file = metadata_dir / "quality_report.json"
    if not quality_file.exists():
        console.print(f"[red]✗[/red] No quality report found for document: {document_id}")
        return

    try:
        with open(quality_file, encoding="utf-8") as f:
            report = json.load(f)

        # Display quality summary
        overall = report["overall_quality"]
        grade = overall["grade"].capitalize()
        score = overall["score"]

        # Color based on grade
        if grade == "Excellent":
            color = "green"
            icon = "✓"
        elif grade == "Good":
            color = "yellow"
            icon = "✓"
        elif grade == "Fair":
            color = "yellow"
            icon = "⚠"
        else:
            color = "red"
            icon = "⚠"

        console.print()
        console.print(Panel(
            f"[{color}]{icon} Quality: {score:.0%} ({grade})[/{color}]\n\n"
            f"Document: {report['document_path']}\n"
            f"Pages: {report['total_pages']}\n"
            f"Analyzed: {report['analysed_at']}\n"
            f"Duration: {report['analysis_duration']:.2f}s",
            title=f"Quality Report: {document_id}",
            border_style=color,
        ))

        # Display issues if any
        if report['issues_detected'] > 0:
            console.print()
            console.print(f"[bold]Issues Detected:[/bold] {report['issues_detected']}")

            # Create issues table
            table = Table(show_header=True, header_style="bold")
            table.add_column("Type")
            table.add_column("Count", justify="right")

            for issue_type, count in report['issues_by_type'].items():
                table.add_row(issue_type.capitalize(), str(count))

            console.print(table)

            if report['affected_pages']:
                console.print(f"\n[dim]Affected pages: {', '.join(map(str, report['affected_pages'][:10]))}")
                if len(report['affected_pages']) > 10:
                    console.print(f"  ... and {len(report['affected_pages']) - 10} more[/dim]")

        else:
            console.print()
            console.print("[green]✓ No issues detected[/green]")

        # Display flags
        if report.get('critical_issues'):
            console.print("\n[red]⚠ Document has critical issues[/red]")
        elif report.get('high_severity_issues'):
            console.print("\n[yellow]⚠ Document has high severity issues[/yellow]")

        console.print()

    except Exception as e:
        console.print(f"[red]✗[/red] Failed to read quality report: {e}")
        logger.error(f"Error reading quality report: {e}", exc_info=True)


@show.command()
@click.argument("document_id", type=str)
def corrections(document_id: str) -> None:
    """Display corrections applied to a document.

    DOCUMENT_ID is the document identifier.

    Example:
        ragged show corrections doc_abc123
    """
    metadata_dir = Path("data/documents/.ragged") / document_id

    if not metadata_dir.exists():
        console.print(f"[red]✗[/red] No metadata found for document: {document_id}")
        return

    corrections_file = metadata_dir / "corrections.json"
    if not corrections_file.exists():
        console.print(f"[yellow]ℹ[/yellow] No corrections were applied to this document")
        console.print(f"[dim]Document may not have required corrections[/dim]")
        return

    try:
        with open(corrections_file, encoding="utf-8") as f:
            corrections = json.load(f)

        # Display corrections summary
        console.print()
        console.print(Panel(
            f"Original: {corrections['original_path']}\n"
            f"Corrected: {corrections['corrected_path']}\n"
            f"Applied: {corrections['corrected_at']}\n"
            f"Duration: {corrections['total_duration']:.2f}s",
            title=f"Corrections: {document_id}",
            border_style="blue",
        ))

        # Quality improvement
        qual = corrections['quality_improvement']
        improvement = qual['improvement']
        if improvement > 0:
            color = "green"
            arrow = "↑"
        elif improvement < 0:
            color = "red"
            arrow = "↓"
        else:
            color = "yellow"
            arrow = "→"

        console.print()
        console.print(f"[bold]Quality Improvement:[/bold]")
        console.print(
            f"  Before:  {qual['before']:.0%}\n"
            f"  After:   {qual['after']:.0%}\n"
            f"  Change:  [{color}]{arrow} {abs(improvement):.1%}[/{color}]"
        )

        # Corrections table
        console.print()
        console.print(f"[bold]Corrections Applied:[/bold] {corrections['successful_corrections']}/{corrections['corrections_applied']}")

        if corrections['actions']:
            table = Table(show_header=True, header_style="bold")
            table.add_column("Type")
            table.add_column("Pages")
            table.add_column("Status")
            table.add_column("Details")

            for action in corrections['actions']:
                status = "[green]✓[/green]" if action['success'] else "[red]✗[/red]"
                pages = ", ".join(map(str, action['pages_affected'][:5]))
                if len(action['pages_affected']) > 5:
                    pages += f" +{len(action['pages_affected']) - 5}"

                table.add_row(
                    action['action_type'].capitalize(),
                    pages,
                    status,
                    action['issue']['details'][:50] + "..." if len(action['issue']['details']) > 50 else action['issue']['details']
                )

            console.print(table)

        console.print()

    except Exception as e:
        console.print(f"[red]✗[/red] Failed to read corrections: {e}")
        logger.error(f"Error reading corrections: {e}", exc_info=True)


@show.command()
@click.argument("document_id", type=str)
def uncertainties(document_id: str) -> None:
    """Display low-confidence sections in a document.

    DOCUMENT_ID is the document identifier.

    Example:
        ragged show uncertainties doc_abc123
    """
    metadata_dir = Path("data/documents/.ragged") / document_id

    if not metadata_dir.exists():
        console.print(f"[red]✗[/red] No metadata found for document: {document_id}")
        return

    uncertainties_file = metadata_dir / "uncertainties.json"
    if not uncertainties_file.exists():
        console.print(f"[green]✓[/green] No uncertainties detected in this document")
        console.print(f"[dim]Document quality is good[/dim]")
        return

    try:
        with open(uncertainties_file, encoding="utf-8") as f:
            data = json.load(f)

        console.print()
        console.print(Panel(
            f"Uncertain pages: {data['total_uncertain_pages']}\n"
            f"Generated: {data['generated_at']}",
            title=f"Uncertainties: {document_id}",
            border_style="yellow",
        ))

        if data['pages']:
            console.print()
            console.print("[bold]Low-confidence pages:[/bold]")

            table = Table(show_header=True, header_style="bold")
            table.add_column("Page", justify="right")
            table.add_column("Confidence", justify="right")
            table.add_column("Severity")
            table.add_column("Details")

            for page_info in data['pages']:
                conf_color = "green" if page_info['confidence'] >= 0.7 else "yellow" if page_info['confidence'] >= 0.5 else "red"

                table.add_row(
                    str(page_info['page_number']),
                    f"[{conf_color}]{page_info['confidence']:.0%}[/{conf_color}]",
                    page_info['severity'],
                    page_info['details'][:60] + "..." if len(page_info['details']) > 60 else page_info['details']
                )

            console.print(table)

        console.print()
        console.print("[dim]Tip: Review these pages for OCR errors or scanning issues[/dim]")
        console.print()

    except Exception as e:
        console.print(f"[red]✗[/red] Failed to read uncertainties: {e}")
        logger.error(f"Error reading uncertainties: {e}", exc_info=True)
