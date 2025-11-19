"""
Smoke tests for ragged {VERSION}.

Quick sanity checks to verify basic functionality.
Estimated time: 5-10 minutes
"""

import pytest


@pytest.mark.smoke
@pytest.mark.version("{VERSION}")
def test_basic_functionality():
    """
    Test basic ragged functionality for {VERSION}.

    This test verifies that core operations work as expected.
    """
    # TODO: Implement smoke test
    # Example:
    # - Verify ragged can be imported
    # - Check configuration loads
    # - Test basic command execution
    # - Verify services are accessible

    assert True, "Placeholder - implement actual smoke test"


@pytest.mark.smoke
@pytest.mark.version("{VERSION}")
@pytest.mark.requires_ollama
@pytest.mark.requires_chromadb
def test_services_available():
    """
    Test that required services (Ollama, ChromaDB) are available.
    """
    from scripts.manual_tests.utils.helpers import check_service_health

    # Check Ollama
    ollama_health = check_service_health("ollama")
    assert ollama_health["status"] == "healthy", f"Ollama not available: {ollama_health['details']}"

    # Check ChromaDB
    chromadb_health = check_service_health("chromadb")
    assert chromadb_health["status"] == "healthy", f"ChromaDB not available: {chromadb_health['details']}"


@pytest.mark.smoke
@pytest.mark.version("{VERSION}")
def test_configuration_valid():
    """
    Test that configuration is valid for {VERSION}.
    """
    # TODO: Implement configuration validation test
    # Example:
    # - Load ragged configuration
    # - Verify required settings are present
    # - Check for any configuration errors

    assert True, "Placeholder - implement configuration test"


# Add more smoke tests as needed
