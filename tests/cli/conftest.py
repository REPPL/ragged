"""Pytest fixtures for CLI tests."""

import tempfile
from pathlib import Path
from typing import Generator
from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner


@pytest.fixture
def cli_runner() -> CliRunner:
    """Provide a Click CLI test runner."""
    return CliRunner()


@pytest.fixture
def temp_data_dir(tmp_path: Path) -> Generator[Path, None, None]:
    """Provide a temporary data directory."""
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    yield data_dir


@pytest.fixture
def mock_vector_store():
    """Mock VectorStore for CLI tests."""
    with patch("src.cli.commands.add.VectorStore") as mock:
        store_instance = MagicMock()
        mock.return_value = store_instance

        # Default empty results
        store_instance.collection.get.return_value = {
            "ids": [],
            "documents": [],
            "metadatas": [],
        }
        store_instance.count.return_value = 0
        store_instance.health_check.return_value = True

        yield store_instance


@pytest.fixture
def mock_ollama_client():
    """Mock OllamaClient for CLI tests."""
    with patch("src.cli.commands.query.OllamaClient") as mock:
        client_instance = MagicMock()
        mock.return_value = client_instance

        # Default response
        client_instance.generate.return_value = "This is a test answer."

        yield client_instance


@pytest.fixture
def mock_retriever():
    """Mock Retriever for CLI tests."""
    with patch("src.cli.commands.query.Retriever") as mock:
        retriever_instance = MagicMock()
        mock.return_value = retriever_instance

        # Default no chunks
        retriever_instance.retrieve.return_value = []

        yield retriever_instance


@pytest.fixture
def mock_settings(temp_data_dir: Path):
    """Mock settings with temporary directory."""
    with patch("src.cli.commands.add.get_settings") as mock:
        settings = MagicMock()
        settings.data_dir = str(temp_data_dir)
        settings.chunk_size = 1000
        settings.chunk_overlap = 200
        settings.embedding_model = "nomic-embed-text"
        settings.llm_model = "llama2"
        settings.retrieval_method = "hybrid"
        settings.chroma_url = "http://localhost:8001"
        mock.return_value = settings
        yield settings


@pytest.fixture
def sample_document_path(tmp_path: Path) -> Path:
    """Create a sample text document for testing."""
    doc_path = tmp_path / "sample.txt"
    doc_path.write_text("This is a test document.\nIt has multiple lines.\n")
    return doc_path


@pytest.fixture
def sample_pdf_path(tmp_path: Path) -> Path:
    """Create a sample PDF document for testing (mock)."""
    pdf_path = tmp_path / "sample.pdf"
    # Just create a file, actual PDF parsing will be mocked
    pdf_path.write_bytes(b"%PDF-1.4\nfake pdf content")
    return pdf_path
