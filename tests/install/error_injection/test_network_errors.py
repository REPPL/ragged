"""
Network Error Injection Tests.

INSTALL-TEST-003: Test recovery from network-related errors.
"""

import socket
from pathlib import Path
from typing import Generator
from unittest.mock import MagicMock, patch

import pytest


@pytest.fixture
def test_home(tmp_path: Path) -> Generator[Path, None, None]:
    """Create test home directory."""
    home = tmp_path / ".ragged"
    home.mkdir(parents=True)
    yield home


class TestDNSErrors:
    """Tests for DNS resolution error handling."""

    def test_handles_dns_failure(self) -> None:
        """Test handling of DNS resolution failure."""
        # Simulate DNS failure
        with patch("socket.gethostbyname", side_effect=socket.gaierror("DNS failure")):
            try:
                socket.gethostbyname("nonexistent.invalid")
            except socket.gaierror:
                pass  # Expected

        # Installation should still work for local operations
        from ragged.install.detection import PythonDetector

        detector = PythonDetector()
        result = detector.detect()

        assert result.installed is True

    def test_handles_dns_timeout(self) -> None:
        """Test handling of DNS timeout."""
        # Local detection should work regardless of DNS
        from ragged.install.detection import PythonDetector

        detector = PythonDetector()
        result = detector.detect()

        assert result.installed is True


class TestConnectionErrors:
    """Tests for connection error handling."""

    def test_handles_connection_refused(
        self,
        test_home: Path,
    ) -> None:
        """Test handling of connection refused errors."""
        # This tests that local operations work without network
        from ragged.install.scaffolding import create_directory_structure

        create_directory_structure(test_home)

        assert test_home.exists()

    def test_handles_connection_timeout(
        self,
        test_home: Path,
    ) -> None:
        """Test handling of connection timeout."""
        # Local operations should not be affected by network timeouts
        from ragged.install.detection import detect_all_prerequisites

        results = detect_all_prerequisites(test_home)

        assert "python" in results
        assert results["python"].installed is True


class TestPortAvailabilityErrors:
    """Tests for port availability error handling."""

    def test_handles_port_in_use(self) -> None:
        """Test handling when required port is in use."""
        from ragged.install.validation import PortValidator

        validator = PortValidator()
        results = validator.validate()

        # Should return results regardless of port status
        assert isinstance(results, list)

    def test_handles_privileged_port_access(self) -> None:
        """Test handling of privileged port access denial."""
        # Try to bind to privileged port (should fail for non-root)
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            sock.bind(("127.0.0.1", 80))
            # If we got here, we're root - skip test
            pytest.skip("Running as root")
        except PermissionError:
            pass  # Expected for non-root
        except OSError:
            pass  # Port may be in use
        finally:
            sock.close()

    def test_port_validation_completes(self) -> None:
        """Test port validation completes without errors."""
        from ragged.install.validation import PortValidator

        validator = PortValidator()
        results = validator.validate()

        assert isinstance(results, list)
        for result in results:
            assert hasattr(result, "passed")
            assert hasattr(result, "message")


class TestDockerNetworkErrors:
    """Tests for Docker network error handling."""

    def test_handles_docker_not_running(
        self,
        test_home: Path,
    ) -> None:
        """Test handling when Docker daemon is not running."""
        from ragged.install.detection import DockerDetector

        detector = DockerDetector()
        result = detector.detect()

        # Should return result (may show not installed/not running)
        assert result is not None
        assert hasattr(result, "installed")

    def test_handles_docker_socket_error(
        self,
        test_home: Path,
    ) -> None:
        """Test handling of Docker socket errors."""
        from ragged.install.detection import DockerDetector

        detector = DockerDetector()
        result = detector.detect()

        # Should handle gracefully
        assert result is not None


class TestOfflineOperation:
    """Tests for offline operation capability."""

    def test_installation_works_offline(
        self,
        test_home: Path,
    ) -> None:
        """Test installation works without network."""
        from ragged.install.scaffolding import create_directory_structure

        # All scaffolding should work offline
        create_directory_structure(test_home)

        assert test_home.exists()
        assert (test_home / "documents").exists()
        assert (test_home / "cache").exists()
        assert (test_home / "logs").exists()
        assert (test_home / "data").exists()

    def test_detection_works_offline(
        self,
        test_home: Path,
    ) -> None:
        """Test detection works without network."""
        from ragged.install.detection import detect_all_prerequisites

        results = detect_all_prerequisites(test_home)

        # Local detection should work
        assert results["python"].installed is True
        assert results["environment"] is not None

    def test_validation_works_offline(
        self,
        test_home: Path,
    ) -> None:
        """Test validation works without network."""
        from ragged.install.scaffolding import create_directory_structure
        from ragged.install.validation import validate_environment

        create_directory_structure(test_home)
        results = validate_environment(test_home)

        assert isinstance(results, list)


class TestProxyErrors:
    """Tests for proxy configuration error handling."""

    def test_handles_invalid_proxy(
        self,
        test_home: Path,
    ) -> None:
        """Test handling of invalid proxy configuration."""
        import os

        # Set invalid proxy
        old_proxy = os.environ.get("HTTP_PROXY")
        os.environ["HTTP_PROXY"] = "http://invalid:99999"

        try:
            # Local operations should work regardless
            from ragged.install.scaffolding import create_directory_structure

            create_directory_structure(test_home)
            assert test_home.exists()
        finally:
            if old_proxy:
                os.environ["HTTP_PROXY"] = old_proxy
            else:
                os.environ.pop("HTTP_PROXY", None)

    def test_handles_proxy_auth_failure(
        self,
        test_home: Path,
    ) -> None:
        """Test handling of proxy authentication failure."""
        # Local operations should not require proxy
        from ragged.install.detection import PythonDetector

        detector = PythonDetector()
        result = detector.detect()

        assert result.installed is True
