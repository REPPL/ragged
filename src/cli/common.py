"""Common imports and utilities for CLI commands."""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import click
    from rich.console import Console as ConsoleType
    from rich.progress import Progress as ProgressType
    from rich.table import Table as TableType
else:
    try:
        import click
        from rich.console import Console as ConsoleType
        from rich.progress import Progress as ProgressType
        from rich.table import Table as TableType
    except ImportError:
        click = None  # type: ignore[assignment]
        ConsoleType = None  # type: ignore[assignment, misc]
        ProgressType = None  # type: ignore[assignment, misc]
        TableType = None  # type: ignore[assignment, misc]

# Shared console instance
console = ConsoleType() if ConsoleType is not None else None
