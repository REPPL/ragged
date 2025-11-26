"""
Uninstall Functionality.

PREREQ-005: Provides uninstall capability to cleanly remove ragged
installation including Docker services and data.
"""

import logging
import shutil
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class UninstallResult:
    """Result of uninstall operation."""

    success: bool
    steps_completed: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    data_preserved: bool = False


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
