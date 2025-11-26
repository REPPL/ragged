"""
Wizard Runner.

WIZARD-001: Main entry point for running the installation wizard.
"""

import logging
from pathlib import Path

from rich.console import Console
from rich.panel import Panel

from ragged.cli.wizard.framework import Wizard, WizardState
from ragged.cli.wizard.screens import (
    WelcomeScreen,
    PrerequisitesScreen,
    InstallationScreen,
    ConfigurationScreen,
    VerificationScreen,
    SuccessScreen,
)


logger = logging.getLogger(__name__)


def run_installation_wizard(
    resume: bool = False,
    state_path: Path | None = None,
    console: Console | None = None,
) -> bool:
    """
    Run the interactive installation wizard.

    Args:
        resume: Whether to resume from saved state.
        state_path: Path for state persistence.
        console: Rich console for output.

    Returns:
        True if wizard completed successfully.
    """
    console = console or Console()

    # Display banner
    _display_banner(console)

    # Check for existing state if not explicitly resuming
    if not resume and state_path:
        state = WizardState.load(state_path)
        if state.current_screen > 0:
            from rich.prompt import Confirm

            console.print(
                Panel(
                    f"[yellow]Found previous installation progress at step {state.current_screen + 1}.[/yellow]",
                    border_style="yellow",
                )
            )
            if Confirm.ask("Resume from where you left off?", default=True):
                resume = True

    # Create wizard
    wizard = Wizard(
        state_path=state_path,
        console=console,
    )

    # Add screens
    wizard.add_screen(WelcomeScreen(wizard))
    wizard.add_screen(PrerequisitesScreen(wizard))
    wizard.add_screen(InstallationScreen(wizard))
    wizard.add_screen(ConfigurationScreen(wizard))
    wizard.add_screen(VerificationScreen(wizard))
    wizard.add_screen(SuccessScreen(wizard))

    # Mark as resumed if applicable
    if resume:
        wizard.set_choice("resumed", True)

    # Run wizard
    try:
        success = wizard.run(resume=resume)

        if success:
            logger.info("Installation wizard completed successfully")
        else:
            logger.info("Installation wizard was aborted")

        return success

    except KeyboardInterrupt:
        console.print("\n")
        console.print(
            Panel(
                "[yellow]Installation interrupted.[/yellow]\n\n"
                "Your progress has been saved. Run:\n"
                "[bold]ragged install --resume[/bold]",
                border_style="yellow",
            )
        )
        return False

    except Exception as e:
        logger.exception("Installation wizard failed")
        console.print(
            Panel(
                f"[red]Installation failed: {e}[/red]\n\n"
                "Please check the logs and try again.",
                border_style="red",
            )
        )
        return False


def _display_banner(console: Console) -> None:
    """Display the ragged banner."""
    banner = """
                                    ██
 ██████╗  █████╗  ██████╗  ██████╗ ███████╗██████╗
 ██╔══██╗██╔══██╗██╔════╝ ██╔════╝ ██╔════╝██╔══██╗
 ██████╔╝███████║██║  ███╗██║  ███╗█████╗  ██║  ██║
 ██╔══██╗██╔══██║██║   ██║██║   ██║██╔══╝  ██║  ██║
 ██║  ██║██║  ██║╚██████╔╝╚██████╔╝███████╗██████╔╝
 ╚═╝  ╚═╝╚═╝  ╚═╝ ╚═════╝  ╚═════╝ ╚══════╝╚═════╝

    Privacy-first Retrieval-Augmented Generation
"""
    console.print(Panel(banner, border_style="blue", padding=(0, 2)))
    console.print()
