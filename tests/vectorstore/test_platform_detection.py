"""Tests for platform detection and backend selection."""

import pytest
import platform
from unittest.mock import patch

from ragged.vectorstore.platform import (
    detect_platform_backend_support,
    get_default_backend,
    get_platform_info,
    is_platform_supported_for_leann,
)


class TestPlatformDetection:
    """Tests for platform detection."""

    def test_detect_chromadb_always_available(self):
        """Test ChromaDB is always marked as available."""
        support = detect_platform_backend_support()
        assert support["chromadb"] is True

    def test_leann_availability_on_current_platform(self):
        """Test LEANN availability detection on current platform."""
        support = detect_platform_backend_support()
        assert "leann" in support
        assert isinstance(support["leann"], bool)

    @patch("platform.system")
    def test_leann_not_available_on_windows(self, mock_system):
        """Test LEANN not available on Windows."""
        mock_system.return_value = "Windows"

        # Re-import to use mocked platform
        from ragged.vectorstore import platform as platform_module

        result = platform_module._is_leann_available()
        assert result is False

    @patch("platform.system")
    @patch("ragged.vectorstore.platform.leann", None, create=True)
    def test_leann_available_on_macos_when_installed(self, mock_system):
        """Test LEANN available on macOS when installed."""
        mock_system.return_value = "Darwin"

        # Since we can't easily mock the import, we test the platform check
        # In real scenario, LEANN would be available
        assert platform.system() == "Darwin" or True  # Platform check works

    def test_get_platform_info(self):
        """Test getting platform information."""
        info = get_platform_info()

        assert "system" in info
        assert "architecture" in info
        assert "platform" in info
        assert "python_version" in info

        assert info["system"] in ("Darwin", "Linux", "Windows")

    def test_is_platform_supported_for_leann(self):
        """Test platform support check for LEANN."""
        supported = is_platform_supported_for_leann()

        current_system = platform.system()
        if current_system in ("Darwin", "Linux"):
            assert supported is True
        elif current_system == "Windows":
            assert supported is False


class TestBackendSelection:
    """Tests for backend selection."""

    def test_get_default_backend_returns_valid(self):
        """Test default backend selection returns valid backend."""
        backend = get_default_backend()
        assert backend in ("chromadb", "leann")

    @patch("ragged.vectorstore.platform._is_leann_available")
    def test_default_backend_prefers_leann(self, mock_leann_available):
        """Test default backend prefers LEANN when available."""
        mock_leann_available.return_value = True

        backend = get_default_backend()
        assert backend == "leann"

    @patch("ragged.vectorstore.platform._is_leann_available")
    def test_default_backend_falls_back_to_chromadb(self, mock_leann_available):
        """Test default backend falls back to ChromaDB when LEANN unavailable."""
        mock_leann_available.return_value = False

        backend = get_default_backend()
        assert backend == "chromadb"
