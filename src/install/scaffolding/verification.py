"""
Installation Verification.

PREREQ-005: Verifies that installation completed successfully by
checking all services and running a test query.
"""

import logging
import subprocess
import socket
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class VerificationResult:
    """Result of installation verification."""

    success: bool
    checks_passed: int
    checks_total: int
    details: dict[str, Any] = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def add_check(self, name: str, passed: bool, message: str = "") -> None:
        """Add a check result."""
        self.details[name] = {"passed": passed, "message": message}
        self.checks_total += 1
        if passed:
            self.checks_passed += 1


def verify_installation(
    ragged_home: Path | None = None,
    run_test_query: bool = True,
) -> VerificationResult:
    """
    Verify that ragged installation is complete and working.

    Args:
        ragged_home: Path to ragged home directory.
        run_test_query: Whether to run a test query.

    Returns:
        VerificationResult with check details.
    """
    import os

    if ragged_home is None:
        ragged_home = Path(os.environ.get("RAGGED_HOME", Path.home() / ".ragged"))

    result = VerificationResult(
        success=True,
        checks_passed=0,
        checks_total=0,
    )

    # Check 1: Directory structure
    _verify_directories(ragged_home, result)

    # Check 2: Configuration files
    _verify_config_files(ragged_home, result)

    # Check 3: Ollama service
    _verify_ollama(result)

    # Check 4: ChromaDB service
    _verify_chromadb(result)

    # Check 5: Ollama models
    _verify_ollama_models(result)

    # Check 6: Test query (optional)
    if run_test_query:
        _verify_test_query(result)

    # Determine overall success
    result.success = result.checks_passed == result.checks_total

    return result


def _verify_directories(ragged_home: Path, result: VerificationResult) -> None:
    """Verify directory structure exists."""
    required_dirs = [
        "documents",
        "chromadb",
        "cache",
        "logs",
    ]

    all_exist = True
    missing = []

    if not ragged_home.exists():
        result.add_check(
            "directories",
            False,
            f"ragged home directory does not exist: {ragged_home}",
        )
        result.errors.append(f"Missing ragged home: {ragged_home}")
        return

    for dirname in required_dirs:
        dir_path = ragged_home / dirname
        if not dir_path.exists():
            all_exist = False
            missing.append(dirname)

    if all_exist:
        result.add_check("directories", True, "All required directories exist")
    else:
        result.add_check(
            "directories",
            False,
            f"Missing directories: {', '.join(missing)}",
        )
        result.errors.append(f"Missing directories: {', '.join(missing)}")


def _verify_config_files(ragged_home: Path, result: VerificationResult) -> None:
    """Verify configuration files exist."""
    config_path = ragged_home / "config.yaml"
    env_path = ragged_home / ".env"

    if config_path.exists():
        result.add_check("config_file", True, f"Config file exists: {config_path}")
    else:
        result.add_check("config_file", False, f"Config file missing: {config_path}")
        result.warnings.append(f"Missing config file: {config_path}")

    if env_path.exists():
        result.add_check("env_file", True, f".env file exists: {env_path}")

        # Check permissions
        mode = env_path.stat().st_mode & 0o777
        if mode > 0o600:
            result.warnings.append(f".env file has loose permissions: {oct(mode)}")
    else:
        result.add_check("env_file", False, f".env file missing: {env_path}")
        result.warnings.append(f"Missing .env file: {env_path}")


def _verify_ollama(result: VerificationResult) -> None:
    """Verify Ollama service is running."""
    try:
        with socket.create_connection(("localhost", 11434), timeout=5):
            result.add_check("ollama_service", True, "Ollama service is running")
    except (socket.error, socket.timeout):
        result.add_check("ollama_service", False, "Ollama service is not running")
        result.errors.append("Ollama service not running on port 11434")


def _verify_chromadb(result: VerificationResult) -> None:
    """Verify ChromaDB service is running."""
    try:
        import urllib.request
        import urllib.error

        with urllib.request.urlopen(
            "http://localhost:8001/api/v1/heartbeat",
            timeout=5,
        ) as response:
            if response.status == 200:
                result.add_check("chromadb_service", True, "ChromaDB service is running")
            else:
                result.add_check(
                    "chromadb_service",
                    False,
                    f"ChromaDB returned status {response.status}",
                )
    except urllib.error.URLError:
        result.add_check("chromadb_service", False, "ChromaDB service is not running")
        result.errors.append("ChromaDB service not running on port 8001")
    except Exception as e:
        result.add_check("chromadb_service", False, f"ChromaDB check failed: {e}")


def _verify_ollama_models(result: VerificationResult) -> None:
    """Verify Ollama has models installed."""
    try:
        proc = subprocess.run(
            ["ollama", "list"],
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )

        if proc.returncode == 0:
            lines = proc.stdout.strip().split("\n")
            # First line is header, count remaining
            model_count = len(lines) - 1 if len(lines) > 1 else 0

            if model_count > 0:
                result.add_check(
                    "ollama_models",
                    True,
                    f"Ollama has {model_count} model(s) installed",
                )
            else:
                result.add_check(
                    "ollama_models",
                    False,
                    "No Ollama models installed",
                )
                result.warnings.append("No Ollama models found. Run: ollama pull llama3.2:3b")
        else:
            result.add_check("ollama_models", False, "Could not list Ollama models")

    except subprocess.TimeoutExpired:
        result.add_check("ollama_models", False, "Ollama list command timed out")
    except FileNotFoundError:
        result.add_check("ollama_models", False, "Ollama command not found")


def _verify_test_query(result: VerificationResult) -> None:
    """Run a test query to verify end-to-end functionality."""
    try:
        import urllib.request
        import urllib.error
        import json

        # Simple API health check
        with urllib.request.urlopen(
            "http://localhost:8000/health",
            timeout=10,
        ) as response:
            if response.status == 200:
                result.add_check("api_health", True, "API health check passed")
            else:
                result.add_check(
                    "api_health",
                    False,
                    f"API health returned status {response.status}",
                )

    except urllib.error.URLError:
        result.add_check(
            "api_health",
            False,
            "API not responding (ragged server may not be running)",
        )
        result.warnings.append("Start ragged server with: ragged serve")
    except Exception as e:
        result.add_check("api_health", False, f"API check failed: {e}")


def format_verification_report(result: VerificationResult) -> str:
    """
    Format verification result as human-readable report.

    Args:
        result: VerificationResult to format.

    Returns:
        Formatted report string.
    """
    lines = []

    # Header
    status = "✅ PASSED" if result.success else "❌ FAILED"
    lines.append("=" * 60)
    lines.append(f"  INSTALLATION VERIFICATION: {status}")
    lines.append("=" * 60)
    lines.append("")

    # Summary
    lines.append(f"Checks: {result.checks_passed}/{result.checks_total} passed")
    lines.append("")

    # Details
    lines.append("--- CHECK DETAILS ---")
    for name, info in result.details.items():
        icon = "✅" if info["passed"] else "❌"
        lines.append(f"{icon} {name}: {info['message']}")
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

    lines.append("=" * 60)

    return "\n".join(lines)
