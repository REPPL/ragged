"""
Configuration Wizard.

WIZARD-004: Interactive configuration file generation with validation.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, IntPrompt, Prompt
from rich.table import Table

from ragged.install.config_manager import (
    ConfigManager,
    ConfigProfile,
    RaggedConfig,
)


@dataclass
class ConfigWizardOptions:
    """Options for configuration wizard."""

    ragged_home: Path = field(default_factory=lambda: Path.home() / ".ragged")
    profile: ConfigProfile = ConfigProfile.DEFAULT
    interactive: bool = True
    generate_env: bool = True
    backup_existing: bool = True


class ConfigWizard:
    """
    Interactive configuration wizard.

    Guides users through configuration options with validation.
    """

    def __init__(
        self,
        options: ConfigWizardOptions | None = None,
        console: Console | None = None,
    ) -> None:
        """
        Initialise configuration wizard.

        Args:
            options: Wizard options.
            console: Rich console for output.
        """
        self.options = options or ConfigWizardOptions()
        self.console = console or Console()
        self.manager = ConfigManager(self.options.ragged_home)

    def run(self) -> RaggedConfig:
        """
        Run the configuration wizard.

        Returns:
            Generated configuration.
        """
        self.console.print(
            Panel(
                "[bold]Configuration Wizard[/bold]\n\n"
                "This wizard will help you configure ragged.\n"
                "Press Enter to accept default values.",
                border_style="blue",
            )
        )
        self.console.print()

        # Backup existing config if present
        if self.options.backup_existing and self.manager.config_exists():
            backup_path = self.manager.backup_config()
            if backup_path:
                self.console.print(
                    f"[dim]Existing configuration backed up to: {backup_path}[/dim]\n"
                )

        # Start with profile-based config
        config = self.manager.generate_config(profile=self.options.profile)

        if self.options.interactive:
            config = self._interactive_configure(config)
        else:
            self.console.print("[dim]Using default configuration.[/dim]")

        # Validate configuration
        errors = self.manager.validate_config(config)
        if errors:
            self.console.print("[red]Configuration validation errors:[/red]")
            for error in errors:
                self.console.print(f"  [red]- {error}[/red]")
            self.console.print()

            if not Confirm.ask("Save configuration anyway?", default=False):
                raise ValueError("Configuration validation failed")

        # Save configuration
        self.manager.save_config(config)
        self.console.print(f"[green]Configuration saved to: {self.manager.config_path}[/green]")

        # Generate .env file if requested
        if self.options.generate_env:
            self.manager.save_env_file()
            self.console.print(f"[green]Environment file saved to: {self.manager.env_path}[/green]")

        return config

    def _interactive_configure(self, config: RaggedConfig) -> RaggedConfig:
        """Run interactive configuration."""
        # Server settings
        self.console.print("[bold blue]Server Settings[/bold blue]")
        self.console.print()

        config.server.host = Prompt.ask(
            "  Bind address",
            default=config.server.host,
        )

        config.server.port = IntPrompt.ask(
            "  API port",
            default=config.server.port,
        )

        config.server.workers = IntPrompt.ask(
            "  Worker processes",
            default=config.server.workers,
        )

        self.console.print()

        # Database settings
        self.console.print("[bold blue]Database Settings[/bold blue]")
        self.console.print()

        config.database.chromadb_host = Prompt.ask(
            "  ChromaDB host",
            default=config.database.chromadb_host,
        )

        config.database.chromadb_port = IntPrompt.ask(
            "  ChromaDB port",
            default=config.database.chromadb_port,
        )

        config.database.persist_directory = Prompt.ask(
            "  Persist directory",
            default=config.database.persist_directory,
        )

        self.console.print()

        # LLM settings
        self.console.print("[bold blue]LLM Settings[/bold blue]")
        self.console.print()

        config.llm.ollama_host = Prompt.ask(
            "  Ollama host URL",
            default=config.llm.ollama_host,
        )

        config.llm.default_model = Prompt.ask(
            "  Default model",
            default=config.llm.default_model,
        )

        config.llm.embedding_model = Prompt.ask(
            "  Embedding model",
            default=config.llm.embedding_model,
        )

        self.console.print()

        # Storage settings
        self.console.print("[bold blue]Storage Settings[/bold blue]")
        self.console.print()

        config.storage.documents_path = Prompt.ask(
            "  Documents path",
            default=config.storage.documents_path,
        )

        config.storage.cache_path = Prompt.ask(
            "  Cache path",
            default=config.storage.cache_path,
        )

        config.storage.logs_path = Prompt.ask(
            "  Logs path",
            default=config.storage.logs_path,
        )

        self.console.print()

        # Security settings
        self.console.print("[bold blue]Security Settings[/bold blue]")
        self.console.print()

        config.security.authentication_enabled = Confirm.ask(
            "  Enable authentication?",
            default=config.security.authentication_enabled,
        )

        if config.security.authentication_enabled:
            config.security.jwt_expiry_hours = IntPrompt.ask(
                "  JWT token expiry (hours)",
                default=config.security.jwt_expiry_hours,
            )

            config.security.session_timeout_minutes = IntPrompt.ask(
                "  Session timeout (minutes)",
                default=config.security.session_timeout_minutes,
            )

        self.console.print()

        # WebUI settings
        self.console.print("[bold blue]WebUI Settings[/bold blue]")
        self.console.print()

        config.webui.enabled = Confirm.ask(
            "  Enable WebUI?",
            default=config.webui.enabled,
        )

        if config.webui.enabled:
            config.webui.port = IntPrompt.ask(
                "  WebUI port",
                default=config.webui.port,
            )

            config.webui.theme = Prompt.ask(
                "  Theme (system/light/dark)",
                default=config.webui.theme,
                choices=["system", "light", "dark"],
            )

        self.console.print()

        # Show summary
        self._show_summary(config)

        # Confirm
        if not Confirm.ask("Is this configuration correct?", default=True):
            self.console.print("[yellow]Restarting configuration...[/yellow]\n")
            return self._interactive_configure(config)

        return config

    def _show_summary(self, config: RaggedConfig) -> None:
        """Display configuration summary."""
        table = Table(
            title="Configuration Summary",
            show_header=True,
            header_style="bold blue",
        )
        table.add_column("Setting", style="cyan")
        table.add_column("Value")

        # Server
        table.add_row("Server Host", config.server.host)
        table.add_row("Server Port", str(config.server.port))
        table.add_row("Workers", str(config.server.workers))

        # Database
        table.add_row("ChromaDB Host", config.database.chromadb_host)
        table.add_row("ChromaDB Port", str(config.database.chromadb_port))

        # LLM
        table.add_row("Ollama Host", config.llm.ollama_host)
        table.add_row("Default Model", config.llm.default_model)

        # Storage
        table.add_row("Documents Path", config.storage.documents_path)

        # Security
        table.add_row(
            "Authentication",
            "Enabled" if config.security.authentication_enabled else "Disabled",
        )

        # WebUI
        table.add_row(
            "WebUI",
            f"Enabled on port {config.webui.port}" if config.webui.enabled else "Disabled",
        )

        self.console.print(table)
        self.console.print()


def generate_config_from_dict(
    options: dict[str, Any],
    ragged_home: Path | None = None,
) -> RaggedConfig:
    """
    Generate configuration from dictionary of options.

    Args:
        options: Configuration options from wizard screens.
        ragged_home: Path to ragged home directory.

    Returns:
        Generated configuration.
    """
    ragged_home = ragged_home or Path(options.get("ragged_home", "~/.ragged"))
    ragged_home = Path(str(ragged_home).replace("~", str(Path.home())))

    manager = ConfigManager(ragged_home)
    config = manager.generate_config()

    # Apply wizard options
    if "api_port" in options:
        config.server.port = int(options["api_port"])

    if "webui_port" in options:
        config.webui.port = int(options["webui_port"])

    if "llm_model" in options:
        config.llm.default_model = options["llm_model"]

    if "enable_auth" in options:
        config.security.authentication_enabled = options["enable_auth"]

    if "use_docker_chromadb" in options:
        if options["use_docker_chromadb"]:
            config.database.chromadb_host = "localhost"
        elif "chromadb_path" in options:
            config.database.persist_directory = options["chromadb_path"]

    # Set paths relative to ragged home
    config.storage.documents_path = str(ragged_home / "documents")
    config.storage.cache_path = str(ragged_home / "cache")
    config.storage.logs_path = str(ragged_home / "logs")
    config.database.persist_directory = str(ragged_home / "data" / "chromadb")

    return config


def quick_configure(
    ragged_home: Path | None = None,
    profile: ConfigProfile = ConfigProfile.DEFAULT,
) -> RaggedConfig:
    """
    Quick non-interactive configuration.

    Args:
        ragged_home: Path to ragged home directory.
        profile: Configuration profile to use.

    Returns:
        Generated and saved configuration.
    """
    ragged_home = ragged_home or Path.home() / ".ragged"
    manager = ConfigManager(ragged_home)

    # Generate config
    config = manager.generate_config(profile=profile)

    # Save config and env
    manager.save_config(config)
    manager.save_env_file()

    return config
