"""Pytest configuration and shared fixtures."""

import os
import tempfile
from pathlib import Path
from typing import Generator

import pytest


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """Create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture(autouse=True)
def clean_env() -> Generator[None, None, None]:
    """Clean up RAGGED_ environment variables before and after each test."""
    # Clean before test
    for key in list(os.environ.keys()):
        if key.startswith("RAGGED_"):
            del os.environ[key]

    # Import here to avoid circular dependency
    from src.config.settings import get_settings

    get_settings.cache_clear()

    yield

    # Clean after test
    for key in list(os.environ.keys()):
        if key.startswith("RAGGED_"):
            del os.environ[key]

    get_settings.cache_clear()


@pytest.fixture
def temp_env_file(temp_dir: Path) -> Generator[Path, None, None]:
    """Create a temporary .env file for testing."""
    env_file = temp_dir / ".env"
    yield env_file


@pytest.fixture
def sample_pdf_path(temp_dir: Path) -> Path:
    """Path for a sample PDF file (to be created in tests)."""
    return temp_dir / "sample.pdf"


@pytest.fixture
def sample_txt_path(temp_dir: Path) -> Path:
    """Path for a sample text file."""
    txt_file = temp_dir / "sample.txt"
    txt_file.write_text("This is a sample text file for testing.\n" * 10)
    return txt_file


@pytest.fixture
def sample_md_path(temp_dir: Path) -> Path:
    """Path for a sample markdown file."""
    md_file = temp_dir / "sample.md"
    md_file.write_text(
        "# Sample Markdown\n\n"
        "This is a sample markdown file.\n\n"
        "## Section 1\n\n"
        "Content here.\n"
    )
    return md_file
