"""
Installation Test Configuration.

INSTALL-TEST: Shared fixtures and configuration for installation tests.
"""

import os
import shutil
from pathlib import Path
from typing import Generator

import pytest


@pytest.fixture
def ragged_home(tmp_path: Path) -> Generator[Path, None, None]:
    """Create a temporary ragged home directory.

    This fixture creates a clean temporary directory for testing
    installation operations. The directory is automatically cleaned
    up after the test completes.

    Yields:
        Path to temporary ragged home directory.
    """
    home = tmp_path / ".ragged"
    home.mkdir(parents=True)
    yield home
    # Cleanup is handled by tmp_path fixture


@pytest.fixture
def env_with_home(ragged_home: Path) -> dict[str, str]:
    """Create environment with custom ragged home.

    This fixture provides an environment dictionary with RAGGED_HOME
    set to the temporary directory, suitable for subprocess testing.

    Args:
        ragged_home: Path to temporary home directory.

    Returns:
        Environment dictionary with RAGGED_HOME set.
    """
    env = os.environ.copy()
    env["RAGGED_HOME"] = str(ragged_home)
    return env


@pytest.fixture
def populated_home(ragged_home: Path) -> Path:
    """Create a populated ragged home with standard structure.

    This fixture creates the standard directory structure and some
    sample files for testing upgrade/recovery scenarios.

    Args:
        ragged_home: Path to temporary home directory.

    Returns:
        Path to populated home directory.
    """
    # Create standard directories
    for dirname in ["documents", "cache", "logs", "data"]:
        (ragged_home / dirname).mkdir()

    # Create sample documents
    docs = ragged_home / "documents"
    for i in range(5):
        (docs / f"sample_{i}.txt").write_text(f"Sample content {i}")

    # Create sample cache
    cache = ragged_home / "cache"
    (cache / "embeddings.cache").write_bytes(b"\x00" * 100)

    # Create sample logs
    logs = ragged_home / "logs"
    (logs / "ragged.log").write_text("Sample log entry\n")

    # Create sample data
    data = ragged_home / "data"
    chromadb = data / "chromadb"
    chromadb.mkdir()
    (chromadb / "chroma.db").write_text("database")

    return ragged_home


@pytest.fixture
def clean_env() -> Generator[dict[str, str], None, None]:
    """Create a clean environment without ragged-related variables.

    This fixture provides an environment with all RAGGED_* variables
    removed, useful for testing default behaviour.

    Yields:
        Clean environment dictionary.
    """
    env = os.environ.copy()

    # Remove all ragged-related variables
    ragged_vars = [k for k in env if k.startswith("RAGGED_")]
    for var in ragged_vars:
        del env[var]

    yield env


@pytest.fixture
def mock_docker_unavailable(monkeypatch: pytest.MonkeyPatch) -> None:
    """Mock Docker as unavailable.

    This fixture patches subprocess calls to simulate Docker
    not being installed or not running.
    """
    import subprocess

    original_run = subprocess.run

    def mock_run(*args, **kwargs):
        cmd = args[0] if args else kwargs.get("args", [])
        if isinstance(cmd, list) and "docker" in cmd[0]:
            raise FileNotFoundError("docker not found")
        return original_run(*args, **kwargs)

    monkeypatch.setattr(subprocess, "run", mock_run)


@pytest.fixture
def mock_ollama_unavailable(monkeypatch: pytest.MonkeyPatch) -> None:
    """Mock Ollama as unavailable.

    This fixture patches subprocess calls to simulate Ollama
    not being installed.
    """
    import subprocess

    original_run = subprocess.run

    def mock_run(*args, **kwargs):
        cmd = args[0] if args else kwargs.get("args", [])
        if isinstance(cmd, list) and "ollama" in str(cmd):
            raise FileNotFoundError("ollama not found")
        return original_run(*args, **kwargs)

    monkeypatch.setattr(subprocess, "run", mock_run)


# Test markers
def pytest_configure(config: pytest.Config) -> None:
    """Configure custom pytest markers."""
    config.addinivalue_line(
        "markers",
        "slow: marks tests as slow (deselect with '-m \"not slow\"')",
    )
    config.addinivalue_line(
        "markers",
        "integration: marks tests as integration tests",
    )
    config.addinivalue_line(
        "markers",
        "requires_docker: marks tests that require Docker",
    )
    config.addinivalue_line(
        "markers",
        "requires_ollama: marks tests that require Ollama",
    )
    config.addinivalue_line(
        "markers",
        "requires_network: marks tests that require network access",
    )


# Skip conditions
requires_docker = pytest.mark.skipif(
    shutil.which("docker") is None,
    reason="Docker not available",
)

requires_ollama = pytest.mark.skipif(
    shutil.which("ollama") is None,
    reason="Ollama not available",
)
