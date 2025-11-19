"""
Shared pytest fixtures for manual tests.

This conftest.py provides common fixtures used across all manual test types:
- Version-specific tests (version/)
- Regression tests (regression/)
- Workflow tests (workflows/)
- Performance tests (performance/)
"""

import json
import os
import shutil
import tempfile
from pathlib import Path
from typing import Dict, List, Optional

import pytest


# ============================================================================
# Path Fixtures
# ============================================================================

@pytest.fixture(scope="session")
def project_root() -> Path:
    """Return the project root directory."""
    return Path(__file__).parent.parent.parent


@pytest.fixture(scope="session")
def test_data_dir(project_root) -> Path:
    """Return the test data directory."""
    return project_root / "scripts" / "manual_tests" / "test_data"


@pytest.fixture(scope="session")
def reports_dir(project_root) -> Path:
    """Return the reports directory."""
    return project_root / "scripts" / "manual_tests" / "reports"


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files."""
    temp_path = tempfile.mkdtemp(prefix="ragged_test_")
    yield Path(temp_path)
    # Cleanup
    if os.path.exists(temp_path):
        shutil.rmtree(temp_path)


# ============================================================================
# Service Availability Fixtures
# ============================================================================

@pytest.fixture(scope="session")
def ollama_available() -> bool:
    """Check if Ollama service is available."""
    import requests
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        return response.status_code == 200
    except requests.exceptions.RequestException:
        return False


@pytest.fixture(scope="session")
def chromadb_available() -> bool:
    """Check if ChromaDB service is available."""
    try:
        import chromadb
        client = chromadb.HttpClient(host="localhost", port=8001)
        client.heartbeat()
        return True
    except Exception:
        return False


@pytest.fixture(autouse=True)
def skip_if_services_unavailable(request, ollama_available, chromadb_available):
    """Skip tests requiring unavailable services."""
    if request.node.get_closest_marker("requires_ollama") and not ollama_available:
        pytest.skip("Ollama service not available")
    if request.node.get_closest_marker("requires_chromadb") and not chromadb_available:
        pytest.skip("ChromaDB service not available")


# ============================================================================
# Test Configuration Fixtures
# ============================================================================

@pytest.fixture
def test_config(temp_dir) -> Dict:
    """Create test configuration."""
    return {
        "data_dir": str(temp_dir / "data"),
        "chroma_host": "localhost",
        "chroma_port": 8001,
        "ollama_host": "localhost",
        "ollama_port": 11434,
        "embedding_model": "all-MiniLM-L6-v2",
        "llm_model": "llama2",
        "chunk_size": 500,
        "chunk_overlap": 50,
    }


# ============================================================================
# Sample Data Fixtures
# ============================================================================

@pytest.fixture
def sample_text_content() -> str:
    """Generate sample text content for testing."""
    return """
# Introduction to Retrieval-Augmented Generation

Retrieval-Augmented Generation (RAG) is a technique that combines information
retrieval with large language models. The system first retrieves relevant documents
from a knowledge base, then uses those documents as context for generating responses.

## Key Benefits

1. Reduced hallucinations
2. Up-to-date information
3. Source attribution
4. Domain-specific knowledge

## Implementation

RAG systems typically consist of:
- Document ingestion pipeline
- Vector embeddings for semantic search
- Retrieval mechanisms (vector, BM25, hybrid)
- Generation with retrieved context
"""


@pytest.fixture
def sample_documents(temp_dir, sample_text_content) -> List[Path]:
    """Create sample documents for testing."""
    docs = []

    # Create sample text file
    txt_file = temp_dir / "sample.txt"
    txt_file.write_text(sample_text_content)
    docs.append(txt_file)

    # Create sample markdown file
    md_file = temp_dir / "sample.md"
    md_file.write_text(f"# Sample Document\n\n{sample_text_content}")
    docs.append(md_file)

    # Create sample HTML file
    html_file = temp_dir / "sample.html"
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head><title>Sample Document</title></head>
    <body>
    <h1>Sample Document</h1>
    <p>{sample_text_content}</p>
    </body>
    </html>
    """
    html_file.write_text(html_content)
    docs.append(html_file)

    return docs


@pytest.fixture
def sample_folder(temp_dir, sample_text_content) -> Path:
    """Create a sample folder structure with multiple documents."""
    folder = temp_dir / "sample_folder"
    folder.mkdir()

    # Create multiple files
    for i in range(5):
        txt_file = folder / f"document_{i}.txt"
        txt_file.write_text(f"Document {i}\n\n{sample_text_content}")

    # Create nested folder
    nested = folder / "nested"
    nested.mkdir()
    for i in range(3):
        md_file = nested / f"nested_doc_{i}.md"
        md_file.write_text(f"# Nested Document {i}\n\n{sample_text_content}")

    return folder


# ============================================================================
# Performance Baseline Fixtures
# ============================================================================

@pytest.fixture(scope="session")
def performance_baselines(project_root) -> Dict:
    """Load performance baselines for all versions."""
    baselines_dir = project_root / "scripts" / "manual_tests" / "performance" / "baselines"
    baselines = {}

    if baselines_dir.exists():
        for baseline_file in baselines_dir.glob("*.json"):
            version = baseline_file.stem
            with open(baseline_file) as f:
                baselines[version] = json.load(f)

    return baselines


@pytest.fixture
def current_version_baseline(performance_baselines) -> Optional[Dict]:
    """Get baseline for current version (v0.2.9 by default)."""
    return performance_baselines.get("v0.2.9")


# ============================================================================
# Ragged Instance Fixtures (to be implemented when ragged is available)
# ============================================================================

# Note: These fixtures assume ragged can be imported and instantiated
# Uncomment and adapt when ready to use

# @pytest.fixture
# def ragged_instance(test_config, temp_dir):
#     """Create a fresh ragged instance for testing."""
#     from ragged import Ragged
#
#     instance = Ragged(
#         data_dir=test_config["data_dir"],
#         chroma_host=test_config["chroma_host"],
#         chroma_port=test_config["chroma_port"],
#     )
#
#     yield instance
#
#     # Cleanup
#     instance.clear()


# ============================================================================
# Test Result Collection
# ============================================================================

@pytest.fixture(scope="session")
def test_results():
    """Collect test results for reporting."""
    results = {
        "passed": [],
        "failed": [],
        "skipped": [],
    }
    return results


# ============================================================================
# Markers
# ============================================================================

def pytest_configure(config):
    """Register custom pytest markers."""
    config.addinivalue_line(
        "markers", "smoke: Quick sanity checks (5-10 min)"
    )
    config.addinivalue_line(
        "markers", "feature(name): Tests for specific feature"
    )
    config.addinivalue_line(
        "markers", "version(v): Tests for specific version"
    )
    config.addinivalue_line(
        "markers", "regression: Cross-version critical paths"
    )
    config.addinivalue_line(
        "markers", "workflow: End-to-end user workflows"
    )
    config.addinivalue_line(
        "markers", "performance: Performance benchmarks"
    )
    config.addinivalue_line(
        "markers", "interactive: Manual checklists"
    )
    config.addinivalue_line(
        "markers", "requires_ollama: Test requires Ollama service"
    )
    config.addinivalue_line(
        "markers", "requires_chromadb: Test requires ChromaDB service"
    )
    config.addinivalue_line(
        "markers", "slow: Slow-running tests"
    )
