"""
Configuration Screen.

WIZARD-001: Screen for configuring ragged installation options.
"""

from pathlib import Path

from rich.panel import Panel
from rich.prompt import Confirm, Prompt
from rich.table import Table

from ragged.cli.wizard.framework import NavigationAction, WizardScreen


class ConfigurationScreen(WizardScreen):
    """Screen for configuring ragged."""

    @property
    def title(self) -> str:
        """Return screen title."""
        return "Configuration"

    @property
    def subtitle(self) -> str | None:
        """Return screen subtitle."""
        return "Customise your ragged installation"

    def render(self) -> None:
        """Render configuration options."""
        self.console.print(
            "Configure your ragged installation. Press Enter to accept defaults.\n"
        )

        # Get current/default values
        config = self.wizard.get_choice("config", {})

        # Storage location
        default_home = str(Path.home() / ".ragged")
        current_home = config.get("ragged_home", default_home)

        self.console.print("[bold]Storage Location[/bold]")
        self.console.print(
            "[dim]Where ragged stores documents, database, and configuration.[/dim]\n"
        )

        ragged_home = Prompt.ask(
            "ragged home directory",
            default=current_home,
        )
        config["ragged_home"] = ragged_home

        self.console.print()

        # Port configuration
        self.console.print("[bold]Network Ports[/bold]")
        self.console.print(
            "[dim]Ports for the API server and web interface.[/dim]\n"
        )

        api_port = Prompt.ask(
            "API server port",
            default=config.get("api_port", "8000"),
        )
        config["api_port"] = api_port

        webui_port = Prompt.ask(
            "Web UI port",
            default=config.get("webui_port", "5173"),
        )
        config["webui_port"] = webui_port

        self.console.print()

        # LLM configuration
        self.console.print("[bold]LLM Configuration[/bold]")
        self.console.print(
            "[dim]Configure the language model for answering questions.[/dim]\n"
        )

        default_model = config.get("llm_model", "llama3.2")
        llm_model = Prompt.ask(
            "Default LLM model",
            default=default_model,
        )
        config["llm_model"] = llm_model

        # Check if model should be pulled
        pull_model = Confirm.ask(
            f"Download {llm_model} model now?",
            default=True,
        )
        config["pull_model"] = pull_model

        self.console.print()

        # ChromaDB configuration
        self.console.print("[bold]Vector Database[/bold]")
        self.console.print(
            "[dim]Configure ChromaDB for document storage.[/dim]\n"
        )

        use_docker = Confirm.ask(
            "Use Docker for ChromaDB?",
            default=True,
        )
        config["use_docker_chromadb"] = use_docker

        if not use_docker:
            chromadb_path = Prompt.ask(
                "ChromaDB storage path",
                default=str(Path(ragged_home) / "chromadb"),
            )
            config["chromadb_path"] = chromadb_path

        self.console.print()

        # Security configuration
        self.console.print("[bold]Security[/bold]")
        self.console.print(
            "[dim]Configure security settings.[/dim]\n"
        )

        enable_auth = Confirm.ask(
            "Enable API authentication?",
            default=False,
        )
        config["enable_auth"] = enable_auth

        self.console.print()

        # Save configuration
        self.wizard.set_choice("config", config)

        # Display summary
        self._display_summary(config)

    def _display_summary(self, config: dict) -> None:
        """Display configuration summary."""
        table = Table(
            title="Configuration Summary",
            show_header=True,
            header_style="bold blue",
        )
        table.add_column("Setting", style="cyan")
        table.add_column("Value")

        table.add_row("ragged Home", config.get("ragged_home", "~/.ragged"))
        table.add_row("API Port", config.get("api_port", "8000"))
        table.add_row("Web UI Port", config.get("webui_port", "5173"))
        table.add_row("LLM Model", config.get("llm_model", "llama3.2"))
        table.add_row(
            "Pull Model",
            "Yes" if config.get("pull_model") else "No",
        )
        table.add_row(
            "Docker ChromaDB",
            "Yes" if config.get("use_docker_chromadb") else "No",
        )
        table.add_row(
            "Authentication",
            "Enabled" if config.get("enable_auth") else "Disabled",
        )

        self.console.print(table)
        self.console.print()

    def process(self) -> NavigationAction:
        """Process user navigation."""
        if Confirm.ask("Is this configuration correct?", default=True):
            return NavigationAction.NEXT

        # User wants to reconfigure
        return NavigationAction.RETRY
