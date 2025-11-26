"""
Uninstall Functionality.

PREREQ-005: Provides uninstall capability to cleanly remove ragged
installation including Docker services and data.

REFINE-005: Enhanced with interactive mode, data export, and
integration with diagnostic/recovery systems.
"""

import json
import logging
import shutil
import subprocess
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Callable

logger = logging.getLogger(__name__)


class UninstallMode(Enum):
    """Uninstall modes."""

    FULL = "full"  # Remove everything
    KEEP_DATA = "keep_data"  # Keep user data
    KEEP_CONFIG = "keep_config"  # Keep config files
    MINIMAL = "minimal"  # Only remove package


@dataclass
class UninstallResult:
    """Result of uninstall operation."""

    success: bool
    steps_completed: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    data_preserved: bool = False
    config_preserved: bool = False
    export_path: Path | None = None
    mode: UninstallMode = UninstallMode.KEEP_DATA


def uninstall_ragged(
    ragged_home: Path | None = None,
    remove_data: bool = False,
    remove_docker: bool = True,
    remove_package: bool = False,
    dry_run: bool = False,
) -> UninstallResult:
    """
    Uninstall ragged.

    Args:
        ragged_home: Path to ragged home directory.
        remove_data: Whether to remove user data (documents, database).
        remove_docker: Whether to remove Docker containers and volumes.
        remove_package: Whether to uninstall the ragged Python package.
        dry_run: If True, only report what would be done.

    Returns:
        UninstallResult with operation details.
    """
    import os

    if ragged_home is None:
        ragged_home = Path(os.environ.get("RAGGED_HOME", Path.home() / ".ragged"))

    result = UninstallResult(success=True)

    logger.info(f"Starting uninstall (dry_run={dry_run})")
    logger.info(f"ragged home: {ragged_home}")

    # Step 1: Stop services
    _stop_services(ragged_home, result, dry_run)

    # Step 2: Remove Docker containers and volumes
    if remove_docker:
        _remove_docker_resources(ragged_home, result, dry_run)

    # Step 3: Remove data directory
    if remove_data:
        _remove_data_directory(ragged_home, result, dry_run)
    else:
        result.data_preserved = True
        result.warnings.append(f"User data preserved at: {ragged_home}")

    # Step 4: Uninstall Python package
    if remove_package:
        _uninstall_package(result, dry_run)

    # Step 5: Clean up any remaining files
    _cleanup_remaining(ragged_home, result, dry_run, remove_data)

    return result


def _stop_services(
    ragged_home: Path,
    result: UninstallResult,
    dry_run: bool,
) -> None:
    """Stop all ragged services."""
    compose_file = ragged_home / "docker-compose.yml"

    if compose_file.exists():
        logger.info("Stopping Docker services...")

        if not dry_run:
            try:
                subprocess.run(
                    ["docker", "compose", "-f", str(compose_file), "down"],
                    capture_output=True,
                    timeout=60,
                    check=False,
                )
            except (subprocess.TimeoutExpired, FileNotFoundError):
                # Try v1
                try:
                    subprocess.run(
                        ["docker-compose", "-f", str(compose_file), "down"],
                        capture_output=True,
                        timeout=60,
                        check=False,
                    )
                except (subprocess.TimeoutExpired, FileNotFoundError):
                    pass

        result.steps_completed.append("Stopped Docker services")
    else:
        logger.info("No docker-compose.yml found, skipping service stop")


def _remove_docker_resources(
    ragged_home: Path,
    result: UninstallResult,
    dry_run: bool,
) -> None:
    """Remove Docker containers and volumes."""
    compose_file = ragged_home / "docker-compose.yml"

    if compose_file.exists():
        logger.info("Removing Docker containers and volumes...")

        if not dry_run:
            try:
                # Remove containers and volumes
                subprocess.run(
                    ["docker", "compose", "-f", str(compose_file), "down", "-v"],
                    capture_output=True,
                    timeout=60,
                    check=False,
                )
            except (subprocess.TimeoutExpired, FileNotFoundError):
                try:
                    subprocess.run(
                        ["docker-compose", "-f", str(compose_file), "down", "-v"],
                        capture_output=True,
                        timeout=60,
                        check=False,
                    )
                except (subprocess.TimeoutExpired, FileNotFoundError):
                    result.warnings.append("Could not remove Docker resources")

        result.steps_completed.append("Removed Docker containers and volumes")

    # Try to remove specific ragged containers/volumes
    if not dry_run:
        try:
            # Remove ragged_chromadb container
            subprocess.run(
                ["docker", "rm", "-f", "ragged_chromadb"],
                capture_output=True,
                timeout=30,
                check=False,
            )

            # Remove ragged_chromadb_data volume
            subprocess.run(
                ["docker", "volume", "rm", "ragged_chromadb_data"],
                capture_output=True,
                timeout=30,
                check=False,
            )

            # Remove network
            subprocess.run(
                ["docker", "network", "rm", "ragged_network"],
                capture_output=True,
                timeout=30,
                check=False,
            )

        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass


def _remove_data_directory(
    ragged_home: Path,
    result: UninstallResult,
    dry_run: bool,
) -> None:
    """Remove the ragged data directory."""
    if ragged_home.exists():
        logger.info(f"Removing data directory: {ragged_home}")

        if not dry_run:
            try:
                shutil.rmtree(ragged_home)
                result.steps_completed.append(f"Removed data directory: {ragged_home}")
            except OSError as e:
                result.errors.append(f"Failed to remove {ragged_home}: {e}")
                result.success = False
        else:
            result.steps_completed.append(f"Would remove: {ragged_home}")
    else:
        logger.info(f"Data directory does not exist: {ragged_home}")


def _uninstall_package(result: UninstallResult, dry_run: bool) -> None:
    """Uninstall the ragged Python package."""
    logger.info("Uninstalling ragged Python package...")

    if not dry_run:
        try:
            proc = subprocess.run(
                ["pip", "uninstall", "-y", "ragged"],
                capture_output=True,
                text=True,
                timeout=60,
                check=False,
            )

            if proc.returncode == 0:
                result.steps_completed.append("Uninstalled ragged Python package")
            else:
                result.warnings.append(f"pip uninstall returned: {proc.returncode}")

        except subprocess.TimeoutExpired:
            result.errors.append("pip uninstall timed out")
        except FileNotFoundError:
            result.warnings.append("pip not found, skipping package uninstall")
    else:
        result.steps_completed.append("Would uninstall ragged Python package")


def _cleanup_remaining(
    ragged_home: Path,
    result: UninstallResult,
    dry_run: bool,
    remove_data: bool,
) -> None:
    """Clean up any remaining configuration files."""
    # Remove compose file if data was removed but file remains
    compose_file = ragged_home / "docker-compose.yml"
    if remove_data and compose_file.exists() and not dry_run:
        try:
            compose_file.unlink()
        except OSError:
            pass

    # Check for leftover config in common locations
    config_locations = [
        Path.home() / ".config" / "ragged",
        Path.home() / ".local" / "share" / "ragged",
    ]

    for location in config_locations:
        if location.exists():
            if remove_data:
                if not dry_run:
                    try:
                        shutil.rmtree(location)
                        result.steps_completed.append(f"Removed: {location}")
                    except OSError:
                        result.warnings.append(f"Could not remove: {location}")
            else:
                result.warnings.append(f"Additional config found at: {location}")


def format_uninstall_report(result: UninstallResult) -> str:
    """
    Format uninstall result as human-readable report.

    Args:
        result: UninstallResult to format.

    Returns:
        Formatted report string.
    """
    lines = []

    # Header
    status = "✅ SUCCESS" if result.success else "❌ FAILED"
    lines.append("=" * 60)
    lines.append(f"  UNINSTALL: {status}")
    lines.append("=" * 60)
    lines.append("")

    # Steps completed
    if result.steps_completed:
        lines.append("--- COMPLETED STEPS ---")
        for step in result.steps_completed:
            lines.append(f"✅ {step}")
        lines.append("")

    # Errors
    if result.errors:
        lines.append("--- ERRORS ---")
        for error in result.errors:
            lines.append(f"❌ {error}")
        lines.append("")

    # Warnings
    if result.warnings:
        lines.append("--- WARNINGS ---")
        for warning in result.warnings:
            lines.append(f"⚠️  {warning}")
        lines.append("")

    # Data preservation notice
    if result.data_preserved:
        lines.append("--- DATA PRESERVED ---")
        lines.append("Your data has been preserved. To remove it completely, run:")
        lines.append("  ragged uninstall --remove-data")
        lines.append("")

    lines.append("=" * 60)

    return "\n".join(lines)


class UninstallWizard:
    """
    Interactive uninstall wizard.

    REFINE-005: Guides user through uninstall with confirmations.
    """

    def __init__(
        self,
        ragged_home: Path | None = None,
        callback: Callable[[str], None] | None = None,
    ) -> None:
        """
        Initialise uninstall wizard.

        Args:
            ragged_home: Path to ragged home.
            callback: Progress callback.
        """
        import os

        self.ragged_home = ragged_home or Path(
            os.environ.get("RAGGED_HOME", Path.home() / ".ragged")
        )
        self.callback = callback or (lambda x: None)

    def get_installation_info(self) -> dict[str, Any]:
        """
        Get information about current installation.

        Returns:
            Dictionary with installation details.
        """
        info: dict[str, Any] = {
            "home_exists": self.ragged_home.exists(),
            "home_path": str(self.ragged_home),
            "components": [],
            "data_size": 0,
            "config_files": [],
        }

        if not self.ragged_home.exists():
            return info

        # Check components
        components = {
            "config": self.ragged_home / "config.yaml",
            "docker_compose": self.ragged_home / "docker-compose.yml",
            "documents": self.ragged_home / "documents",
            "database": self.ragged_home / "data",
            "cache": self.ragged_home / "cache",
            "logs": self.ragged_home / "logs",
        }

        for name, path in components.items():
            if path.exists():
                info["components"].append(name)

        # Calculate data size
        try:
            total_size = sum(
                f.stat().st_size
                for f in self.ragged_home.rglob("*")
                if f.is_file()
            )
            info["data_size"] = total_size
            info["data_size_human"] = self._format_size(total_size)
        except OSError:
            info["data_size_human"] = "Unknown"

        # Find config files
        config_patterns = ["*.yaml", "*.yml", "*.json", "*.conf"]
        for pattern in config_patterns:
            for f in self.ragged_home.glob(pattern):
                info["config_files"].append(str(f.name))

        return info

    def _format_size(self, size: int) -> str:
        """Format byte size as human readable."""
        for unit in ["B", "KB", "MB", "GB"]:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size //= 1024
        return f"{size:.1f} TB"

    def export_data(self, export_path: Path | None = None) -> Path | None:
        """
        Export user data before uninstall.

        Args:
            export_path: Where to export data.

        Returns:
            Path to export archive or None if failed.
        """
        if not self.ragged_home.exists():
            return None

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        if export_path is None:
            export_path = Path.home() / f"ragged_export_{timestamp}"

        self.callback(f"Exporting data to {export_path}...")

        try:
            export_path.mkdir(parents=True, exist_ok=True)

            # Export documents
            docs_src = self.ragged_home / "documents"
            if docs_src.exists():
                docs_dst = export_path / "documents"
                shutil.copytree(docs_src, docs_dst)
                self.callback("Exported documents")

            # Export config
            config_src = self.ragged_home / "config.yaml"
            if config_src.exists():
                shutil.copy2(config_src, export_path / "config.yaml")
                self.callback("Exported configuration")

            # Export manifest
            manifest = {
                "exported_at": datetime.now().isoformat(),
                "source": str(self.ragged_home),
                "ragged_version": self._get_version(),
            }
            with open(export_path / "manifest.json", "w") as f:
                json.dump(manifest, f, indent=2)

            self.callback(f"Export complete: {export_path}")
            return export_path

        except Exception as e:
            logger.error(f"Export failed: {e}")
            return None

    def _get_version(self) -> str:
        """Get installed ragged version."""
        try:
            result = subprocess.run(
                ["pip", "show", "ragged"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            for line in result.stdout.split("\n"):
                if line.startswith("Version:"):
                    return line.split(":")[1].strip()
        except Exception:
            pass
        return "unknown"

    def run_interactive(self) -> UninstallResult:
        """
        Run interactive uninstall.

        Returns:
            UninstallResult.
        """
        from rich.console import Console
        from rich.panel import Panel
        from rich.prompt import Confirm, Prompt

        console = Console()

        # Show installation info
        info = self.get_installation_info()

        console.print()
        console.print(Panel(
            f"[bold]ragged Installation[/bold]\n\n"
            f"Location: {info['home_path']}\n"
            f"Size: {info.get('data_size_human', 'Unknown')}\n"
            f"Components: {', '.join(info['components']) or 'None'}",
            title="Uninstall ragged",
        ))

        if not info["home_exists"]:
            console.print("[yellow]No installation found.[/yellow]")
            return UninstallResult(
                success=True,
                warnings=["No installation found"],
            )

        # Ask about data export
        export_path = None
        if info["components"]:
            if Confirm.ask("Export your data before uninstalling?", default=True):
                export_path = self.export_data()

        # Ask about removal mode
        console.print("\n[bold]What would you like to remove?[/bold]")
        console.print("1. Everything (full uninstall)")
        console.print("2. Keep user data (documents)")
        console.print("3. Keep configuration")
        console.print("4. Cancel")

        choice = Prompt.ask("Choice", choices=["1", "2", "3", "4"], default="2")

        if choice == "4":
            console.print("[yellow]Cancelled[/yellow]")
            return UninstallResult(
                success=True,
                warnings=["Uninstall cancelled by user"],
            )

        mode_map = {
            "1": UninstallMode.FULL,
            "2": UninstallMode.KEEP_DATA,
            "3": UninstallMode.KEEP_CONFIG,
        }
        mode = mode_map[choice]

        # Final confirmation
        if mode == UninstallMode.FULL:
            if not Confirm.ask(
                "[red]This will delete ALL data. Are you sure?[/red]",
                default=False,
            ):
                return UninstallResult(
                    success=True,
                    warnings=["Uninstall cancelled by user"],
                )

        # Perform uninstall
        console.print("\n[bold]Uninstalling...[/bold]")

        result = uninstall_ragged(
            ragged_home=self.ragged_home,
            remove_data=(mode == UninstallMode.FULL),
            remove_docker=True,
            remove_package=False,
            dry_run=False,
        )

        result.mode = mode
        result.export_path = export_path

        # Show result
        console.print()
        console.print(format_uninstall_report(result))

        return result


def interactive_uninstall(
    ragged_home: Path | None = None,
) -> UninstallResult:
    """
    Run interactive uninstall wizard.

    Args:
        ragged_home: Path to ragged home.

    Returns:
        UninstallResult.
    """
    wizard = UninstallWizard(ragged_home)
    return wizard.run_interactive()


def get_uninstall_preview(
    ragged_home: Path | None = None,
) -> dict[str, Any]:
    """
    Get preview of what would be uninstalled.

    Args:
        ragged_home: Path to ragged home.

    Returns:
        Dictionary with uninstall preview.
    """
    wizard = UninstallWizard(ragged_home)
    return wizard.get_installation_info()
