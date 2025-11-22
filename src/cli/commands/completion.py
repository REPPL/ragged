"""Shell completion command for ragged CLI.

Provides shell completion installation for bash, zsh, and fish shells.
Uses Click's built-in shell completion support (Click 8.0+).
"""

import os
import sys
from pathlib import Path
from typing import Literal

from src.cli.common import click, console

ShellType = Literal["bash", "zsh", "fish"]


@click.command()
@click.option(
    "--shell",
    "-s",
    type=click.Choice(["bash", "zsh", "fish"], case_sensitive=False),
    help="Shell type (auto-detected if not specified)",
)
@click.option(
    "--install",
    "-i",
    is_flag=True,
    help="Automatically install completion (modifies shell config)",
)
@click.option(
    "--show",
    is_flag=True,
    help="Show completion script without installing",
)
def completion(shell: str | None, install: bool, show: bool) -> None:
    """Install shell completion for ragged CLI.

    Supports bash, zsh, and fish shells. Auto-detects your shell if not specified.

    \b
    Examples:
        # Show installation instructions
        ragged completion

        # Generate completion script for bash
        ragged completion --shell bash --show

        # Auto-install for your current shell
        ragged completion --install

    \b
    Manual Installation:
        Bash:
            ragged completion --shell bash --show >> ~/.bashrc
            source ~/.bashrc

        Zsh:
            ragged completion --shell zsh --show >> ~/.zshrc
            source ~/.zshrc

        Fish:
            ragged completion --shell fish --show > ~/.config/fish/completions/ragged.fish
    """
    # Auto-detect shell if not specified
    if shell is None:
        shell = _detect_shell()
        if shell is None:
            console.print(
                "[red]Could not auto-detect shell. Please specify with --shell[/red]"
            )
            console.print("\nAvailable shells: bash, zsh, fish")
            sys.exit(1)

    shell = shell.lower()  # type: ignore

    # Show completion script
    if show:
        script = _get_completion_script(shell)  # type: ignore
        print(script)
        return

    # Install completion
    if install:
        _install_completion(shell)  # type: ignore
        return

    # Default: show installation instructions
    _show_instructions(shell)  # type: ignore


def _detect_shell() -> ShellType | None:
    """Auto-detect the current shell."""
    # Try SHELL environment variable
    shell_path = os.environ.get("SHELL", "")
    if shell_path:
        shell_name = Path(shell_path).name
        if shell_name in ("bash", "zsh", "fish"):
            return shell_name  # type: ignore

    # Try parent process (works on Linux/macOS)
    try:
        import psutil

        parent = psutil.Process().parent()
        if parent:
            parent_name = parent.name()
            if parent_name in ("bash", "zsh", "fish"):
                return parent_name  # type: ignore
    except (ImportError, Exception):
        pass

    return None


def _get_completion_script(shell: ShellType) -> str:
    """Generate the completion script for the specified shell."""
    if shell == "bash":
        return """# ragged completion for bash
# Add this to your ~/.bashrc

eval "$(_RAGGED_COMPLETE=bash_source ragged)"
"""
    elif shell == "zsh":
        return """# ragged completion for zsh
# Add this to your ~/.zshrc

eval "$(_RAGGED_COMPLETE=zsh_source ragged)"
"""
    elif shell == "fish":
        return """# ragged completion for fish
# Save this as ~/.config/fish/completions/ragged.fish

eval (env _RAGGED_COMPLETE=fish_source ragged)
"""
    else:
        return f"# Unsupported shell: {shell}"


def _get_config_file(shell: ShellType) -> Path:
    """Get the shell configuration file path."""
    home = Path.home()

    if shell == "bash":
        # Try .bashrc first, fall back to .bash_profile
        bashrc = home / ".bashrc"
        if bashrc.exists() or sys.platform == "linux":
            return bashrc
        return home / ".bash_profile"

    elif shell == "zsh":
        return home / ".zshrc"

    elif shell == "fish":
        config_dir = home / ".config" / "fish" / "completions"
        config_dir.mkdir(parents=True, exist_ok=True)
        return config_dir / "ragged.fish"

    else:
        raise ValueError(f"Unsupported shell: {shell}")


def _install_completion(shell: ShellType) -> None:
    """Automatically install shell completion."""
    config_file = _get_config_file(shell)
    completion_script = _get_completion_script(shell)

    # Check if already installed
    if config_file.exists():
        content = config_file.read_text()
        if "_RAGGED_COMPLETE" in content or "ragged completion" in content.lower():
            console.print(
                f"[yellow]Completion already installed in {config_file}[/yellow]"
            )
            console.print("\nTo reinstall, remove the existing completion lines first.")
            return

    # Install completion
    try:
        with config_file.open("a") as f:
            f.write("\n# ragged CLI completion (added by ragged completion --install)\n")
            f.write(completion_script)

        console.print(f"[green]✓[/green] Completion installed to {config_file}")
        console.print(
            f"\n[yellow]Restart your shell or run:[/yellow] source {config_file}"
        )

    except (OSError, PermissionError) as e:
        console.print(f"[red]Error installing completion: {e}[/red]")
        console.print(f"\nTry manual installation with: ragged completion --shell {shell} --show")
        sys.exit(1)


def _show_instructions(shell: ShellType) -> None:
    """Show installation instructions for the shell."""
    config_file = _get_config_file(shell)

    console.print(f"[bold]Shell Completion for {shell.upper()}[/bold]\n")

    console.print("[bold green]Automatic Installation:[/bold green]")
    console.print(f"  ragged completion --shell {shell} --install\n")

    console.print("[bold blue]Manual Installation:[/bold blue]")

    if shell in ("bash", "zsh"):
        console.print(f"  1. Add to your {config_file}:")
        console.print(f"     ragged completion --shell {shell} --show >> {config_file}")
        console.print("\n  2. Reload your shell:")
        console.print(f"     source {config_file}")
    else:  # fish
        console.print("  1. Save completion script:")
        console.print(f"     ragged completion --shell {shell} --show > {config_file}")
        console.print("\n  2. Restart your shell or reload config")

    console.print(
        "\n[bold yellow]Current Detection:[/bold yellow]"
        f" {shell} (auto-detected)"
        if os.environ.get("SHELL", "").endswith(shell)
        else " " + shell
    )

    console.print("\n[dim]After installation, try typing:[/dim]")
    console.print("  [dim]ragged <TAB>          # Show available commands[/dim]")
    console.print("  [dim]ragged add <TAB>      # Show add command options[/dim]")
