"""Streaming output formatter for CLI.

Provides progressive terminal output with ANSI formatting, interrupt handling,
and progress indication for streaming LLM responses.

v0.6.5 OPTIMISE-005 Phase 2: CLI Integration
"""

from __future__ import annotations

import sys
from typing import Iterator

from rich.console import Console
from rich.live import Live
from rich.markdown import Markdown
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

from ragged.generation.streaming import StreamGenerator, StreamState, StreamToken


class StreamingFormatter:
    """Format streaming output for terminal display.

    Handles progressive output with ANSI formatting, live updates,
    and interrupt handling.
    """

    def __init__(self, console: Console | None = None):
        """Initialise streaming formatter.

        Args:
            console: Rich console for output (creates default if None)
        """
        self.console = console or Console()
        self.generator = StreamGenerator()

    def stream_response(
        self,
        tokens: Iterator[str],
        show_progress: bool = True,
        markdown: bool = False,
    ) -> str:
        """Stream response to terminal with live updates.

        Args:
            tokens: Iterator of token strings
            show_progress: Show progress spinner
            markdown: Render output as markdown

        Returns:
            Complete response text

        Raises:
            KeyboardInterrupt: User interrupted streaming
        """
        collected_text = []

        try:
            if show_progress:
                with Progress(
                    SpinnerColumn(),
                    TextColumn("[progress.description]{task.description}"),
                    console=self.console,
                ) as progress:
                    task = progress.add_task("Generating response...", total=None)

                    for stream_token in self.generator.stream_tokens(tokens):
                        collected_text.append(stream_token.token)
                        progress.update(task, description=f"Generated {len(collected_text)} tokens")

                    progress.update(task, description="✓ Complete")
            else:
                # Simple streaming without progress
                for stream_token in self.generator.stream_tokens(tokens):
                    collected_text.append(stream_token.token)
                    self.console.print(stream_token.token, end="", highlight=False)

                self.console.print()  # Newline at end

            full_text = "".join(collected_text)

            # Render markdown if requested
            if markdown and full_text:
                self.console.print(Markdown(full_text))

            return full_text

        except KeyboardInterrupt:
            self.console.print("\n[yellow]Stream interrupted by user[/yellow]")
            return "".join(collected_text)

    def stream_response_live(
        self,
        tokens: Iterator[str],
        title: str = "Response",
    ) -> str:
        """Stream response with live updating panel.

        Args:
            tokens: Iterator of token strings
            title: Panel title

        Returns:
            Complete response text
        """
        collected_text = []

        try:
            with Live(
                Panel("", title=title, border_style="cyan"),
                console=self.console,
                refresh_per_second=10,
            ) as live:
                for stream_token in self.generator.stream_tokens(tokens):
                    collected_text.append(stream_token.token)
                    current_text = "".join(collected_text)

                    # Update live panel
                    live.update(
                        Panel(
                            Markdown(current_text) if current_text else "Generating...",
                            title=f"{title} ({len(collected_text)} tokens)",
                            border_style="cyan",
                        )
                    )

                # Final update with completion indicator
                full_text = "".join(collected_text)
                live.update(
                    Panel(
                        Markdown(full_text) if full_text else "No response",
                        title=f"{title} ✓ Complete",
                        border_style="green",
                    )
                )

            return full_text

        except KeyboardInterrupt:
            self.console.print("\n[yellow]Stream interrupted by user[/yellow]")
            return "".join(collected_text)

    def get_metrics(self) -> dict:
        """Get streaming metrics.

        Returns:
            Metrics dictionary
        """
        return self.generator.get_metrics()


def stream_to_console(
    tokens: Iterator[str],
    console: Console | None = None,
    show_progress: bool = True,
) -> str:
    """Convenience function to stream tokens to console.

    Args:
        tokens: Iterator of token strings
        console: Optional Rich console
        show_progress: Show progress indicator

    Returns:
        Complete response text
    """
    formatter = StreamingFormatter(console)
    return formatter.stream_response(tokens, show_progress=show_progress)
