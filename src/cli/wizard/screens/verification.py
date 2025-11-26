"""
Verification Screen.

WIZARD-001: Screen for verifying the installation and running setup.
"""

from pathlib import Path

from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from ragged.cli.wizard.framework import NavigationAction, WizardScreen


class VerificationScreen(WizardScreen):
    """Screen for verifying installation."""

    @property
    def title(self) -> str:
        """Return screen title."""
        return "Setup & Verification"

    @property
    def subtitle(self) -> str | None:
        """Return screen subtitle."""
        return "Setting up ragged and verifying installation"

    def render(self) -> None:
        """Render verification screen."""
        if not self.wizard.get_result("setup_complete"):
            self._run_setup()

        if not self.wizard.get_result("verification_complete"):
            self._run_verification()

        self._display_results()

    def _run_setup(self) -> None:
        """Run installation setup."""
        config = self.wizard.get_choice("config", {})
        ragged_home = Path(config.get("ragged_home", Path.home() / ".ragged"))

        setup_results = {}

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console,
        ) as progress:
            # Create directory structure
            task = progress.add_task("Creating directories...", total=None)
            try:
                from ragged.install.scaffolding import create_directory_structure

                create_directory_structure(ragged_home)
                setup_results["directories"] = {"success": True, "message": "Created"}
            except Exception as e:
                setup_results["directories"] = {"success": False, "message": str(e)}
            progress.remove_task(task)

            # Generate configuration files
            task = progress.add_task("Generating configuration...", total=None)
            try:
                from ragged.install.config_manager import ConfigManager

                manager = ConfigManager(ragged_home)
                manager.generate_config(
                    server_port=int(config.get("api_port", 8000)),
                    webui_port=int(config.get("webui_port", 5173)),
                    llm_model=config.get("llm_model", "llama3.2"),
                    enable_auth=config.get("enable_auth", False),
                )
                manager.save()
                setup_results["config"] = {"success": True, "message": "Generated"}
            except Exception as e:
                setup_results["config"] = {"success": False, "message": str(e)}
            progress.remove_task(task)

            # Setup Docker services if needed
            if config.get("use_docker_chromadb", True):
                task = progress.add_task("Setting up Docker services...", total=None)
                try:
                    from ragged.install.scaffolding import setup_docker_services

                    setup_docker_services(ragged_home)
                    setup_results["docker"] = {"success": True, "message": "Configured"}
                except Exception as e:
                    setup_results["docker"] = {"success": False, "message": str(e)}
                progress.remove_task(task)

            # Pull LLM model if requested
            if config.get("pull_model", True):
                model = config.get("llm_model", "llama3.2")
                task = progress.add_task(f"Pulling {model} model...", total=None)
                try:
                    import subprocess

                    result = subprocess.run(
                        ["ollama", "pull", model],
                        capture_output=True,
                        text=True,
                        timeout=600,  # 10 minute timeout
                    )
                    if result.returncode == 0:
                        setup_results["model"] = {"success": True, "message": f"Pulled {model}"}
                    else:
                        setup_results["model"] = {
                            "success": False,
                            "message": result.stderr or "Failed to pull model",
                        }
                except subprocess.TimeoutExpired:
                    setup_results["model"] = {
                        "success": False,
                        "message": "Model pull timed out",
                    }
                except FileNotFoundError:
                    setup_results["model"] = {
                        "success": False,
                        "message": "Ollama not found",
                    }
                except Exception as e:
                    setup_results["model"] = {"success": False, "message": str(e)}
                progress.remove_task(task)

        self.wizard.set_result("setup_results", setup_results)
        self.wizard.set_result("setup_complete", True)

    def _run_verification(self) -> None:
        """Run installation verification."""
        config = self.wizard.get_choice("config", {})
        ragged_home = Path(config.get("ragged_home", Path.home() / ".ragged"))

        verification_results = {}

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console,
        ) as progress:
            # Verify directory structure
            task = progress.add_task("Verifying directories...", total=None)
            required_dirs = ["documents", "logs", "config"]
            dirs_ok = all((ragged_home / d).exists() for d in required_dirs)
            verification_results["directories"] = {
                "passed": dirs_ok,
                "message": "All directories exist" if dirs_ok else "Missing directories",
            }
            progress.remove_task(task)

            # Verify configuration
            task = progress.add_task("Verifying configuration...", total=None)
            config_file = ragged_home / "config" / "ragged.yml"
            config_ok = config_file.exists()
            verification_results["config"] = {
                "passed": config_ok,
                "message": "Configuration valid" if config_ok else "Configuration missing",
            }
            progress.remove_task(task)

            # Verify Docker (if used)
            if config.get("use_docker_chromadb", True):
                task = progress.add_task("Verifying Docker...", total=None)
                try:
                    import subprocess

                    result = subprocess.run(
                        ["docker", "info"],
                        capture_output=True,
                        timeout=10,
                    )
                    docker_ok = result.returncode == 0
                    verification_results["docker"] = {
                        "passed": docker_ok,
                        "message": "Docker running" if docker_ok else "Docker not running",
                    }
                except Exception:
                    verification_results["docker"] = {
                        "passed": False,
                        "message": "Docker check failed",
                    }
                progress.remove_task(task)

            # Verify Ollama
            task = progress.add_task("Verifying Ollama...", total=None)
            try:
                import subprocess

                result = subprocess.run(
                    ["ollama", "list"],
                    capture_output=True,
                    text=True,
                    timeout=10,
                )
                ollama_ok = result.returncode == 0
                model = config.get("llm_model", "llama3.2")
                has_model = model in result.stdout if ollama_ok else False
                verification_results["ollama"] = {
                    "passed": ollama_ok and has_model,
                    "message": f"Ollama ready with {model}" if has_model else "Model not found",
                }
            except Exception:
                verification_results["ollama"] = {
                    "passed": False,
                    "message": "Ollama check failed",
                }
            progress.remove_task(task)

        self.wizard.set_result("verification_results", verification_results)
        self.wizard.set_result("verification_complete", True)

    def _display_results(self) -> None:
        """Display setup and verification results."""
        setup_results = self.wizard.get_result("setup_results", {})
        verification_results = self.wizard.get_result("verification_results", {})

        # Setup results table
        if setup_results:
            table = Table(
                title="Setup Results",
                show_header=True,
                header_style="bold blue",
            )
            table.add_column("Step", style="cyan")
            table.add_column("Status", justify="center")
            table.add_column("Details")

            for step, result in setup_results.items():
                status = "[green]Done[/green]" if result["success"] else "[red]Failed[/red]"
                table.add_row(step.title(), status, result["message"])

            self.console.print(table)
            self.console.print()

        # Verification results table
        if verification_results:
            table = Table(
                title="Verification Results",
                show_header=True,
                header_style="bold blue",
            )
            table.add_column("Check", style="cyan")
            table.add_column("Status", justify="center")
            table.add_column("Details")

            all_passed = True
            for check, result in verification_results.items():
                if result["passed"]:
                    status = "[green]Pass[/green]"
                else:
                    status = "[red]Fail[/red]"
                    all_passed = False
                table.add_row(check.title(), status, result["message"])

            self.console.print(table)
            self.console.print()

            if all_passed:
                self.console.print(
                    Panel(
                        "[green]All verification checks passed![/green]",
                        border_style="green",
                    )
                )
            else:
                self.console.print(
                    Panel(
                        "[yellow]Some verification checks failed. "
                        "You may need to complete setup manually.[/yellow]",
                        border_style="yellow",
                    )
                )

            self.wizard.set_choice("verification_passed", all_passed)

    def process(self) -> NavigationAction:
        """Process user navigation."""
        return self.prompt_navigation()
