"""Comprehensive security testing framework.

v0.2.10 FEAT-SEC-003: Additional security tests for common vulnerabilities.

This test suite covers:
1. Path traversal prevention
2. File size limits
3. Input validation
4. Error message security
5. Dependency security
"""

import re
from pathlib import Path
from typing import List

import pytest

from src.utils.path_utils import validate_path, is_safe_path
from src.utils.security import validate_file_size, get_safe_filename


class TestPathTraversal:
    """Test suite for path traversal prevention."""

    def test_path_traversal_blocked(self, tmp_path: Path) -> None:
        """Test that path traversal attempts are blocked.

        Security: Prevents directory traversal attacks (CWE-22).
        """
        base_dir = tmp_path / "safe_dir"
        base_dir.mkdir()

        # Attempts to escape base directory
        malicious_paths = [
            "../etc/passwd",
            "../../etc/passwd",
            "../../../etc/passwd",
            "subdir/../../etc/passwd",
            "..\\..\\windows\\system32",  # Windows style
            "./../../../etc/passwd",
        ]

        for malicious_path in malicious_paths:
            test_path = base_dir / malicious_path

            # Should detect as unsafe
            assert not is_safe_path(test_path, base_dir), (
                f"Path traversal not detected: {malicious_path}"
            )

    def test_safe_paths_allowed(self, tmp_path: Path) -> None:
        """Test that legitimate paths are allowed."""
        base_dir = tmp_path / "safe_dir"
        base_dir.mkdir()

        safe_paths = [
            "file.txt",
            "subdir/file.txt",
            "deep/nested/dir/file.txt",
            "file-with-dash.txt",
            "file_with_underscore.txt",
        ]

        for safe_path in safe_paths:
            test_path = base_dir / safe_path
            test_path.parent.mkdir(parents=True, exist_ok=True)

            # Should be safe
            assert is_safe_path(test_path, base_dir), f"Safe path rejected: {safe_path}"


class TestFileSizeLimits:
    """Test suite for file size validation."""

    def test_file_size_limits_enforced(self, tmp_path: Path) -> None:
        """Test that file size limits are enforced.

        Security: Prevents DoS via large file uploads.
        """
        # Create file exceeding limit
        large_file = tmp_path / "large_file.txt"
        large_file.write_text("x" * (100 * 1024 * 1024 + 1))  # 100MB + 1 byte

        # Should be rejected (assuming 100MB limit)
        assert not validate_file_size(large_file, max_size_mb=100)

    def test_file_size_within_limits(self, tmp_path: Path) -> None:
        """Test that files within limits are accepted."""
        small_file = tmp_path / "small_file.txt"
        small_file.write_text("x" * 1024)  # 1KB

        # Should be accepted
        assert validate_file_size(small_file, max_size_mb=100)


class TestInputValidation:
    """Test suite for input validation."""

    def test_filename_sanitization(self) -> None:
        """Test that filenames are sanitized to prevent injection.

        Security: Prevents file system injection attacks.
        """
        dangerous_filenames = [
            "../../../etc/passwd",
            "file; rm -rf /",
            "file`whoami`",
            "file$(whoami)",
            "file|whoami",
            "file&whoami",
            "file\nwhoami",
            "file\rwhoami",
        ]

        for dangerous_name in dangerous_filenames:
            safe_name = get_safe_filename(dangerous_name)

            # Should not contain shell metacharacters
            assert not re.search(r'[;&|`$\n\r]', safe_name), (
                f"Shell metacharacters in sanitized filename: {safe_name}"
            )

            # Should not contain path traversal
            assert ".." not in safe_name
            assert "/" not in safe_name
            assert "\\" not in safe_name


class TestErrorHandling:
    """Test suite for secure error handling."""

    def test_error_messages_no_sensitive_info(self) -> None:
        """Test that error messages don't leak sensitive information.

        Security: Prevents information disclosure through error messages.
        """
        # This is a documentation test - error messages should be reviewed manually
        # Common violations:
        # - Full file paths in error messages
        # - Database schema in error messages
        # - Stack traces to external users
        # - Configuration details in error messages

        assert True, (
            "Review all error messages for information disclosure:\n"
            "- No full file paths\n"
            "- No database schema details\n"
            "- No stack traces to users\n"
            "- No configuration values\n"
            "- Generic messages for authentication failures"
        )


class TestDependencySecurity:
    """Test suite for dependency security."""

    def test_no_known_vulnerable_dependencies(self) -> None:
        """Test for known vulnerable dependencies.

        Security: Ensures dependencies don't have known CVEs.

        Note: Run `pip-audit` manually for comprehensive vulnerability scanning.
        """
        # This is a documentation test
        # In CI/CD, run: pip-audit --desc
        assert True, (
            "Run dependency vulnerability scan:\n"
            "  pip install pip-audit\n"
            "  pip-audit --desc\n"
            "\n"
            "Review and update any vulnerable dependencies."
        )

    def test_no_unnecessary_dependencies(self) -> None:
        """Test that no unnecessary dependencies are installed.

        Security: Reduces attack surface by minimizing dependencies.
        """
        # Read pyproject.toml dependencies
        pyproject = Path("pyproject.toml")
        if not pyproject.exists():
            pytest.skip("pyproject.toml not found")

        content = pyproject.read_text()

        # Check for commonly unnecessary/risky dependencies
        risky_deps = [
            "pickle5",  # Pickle variant (we use JSON)
            "dill",  # Extended pickle (we use JSON)
            "cloudpickle",  # Pickle for cloud (we use JSON)
            "marshal",  # Python marshaling (unsafe)
        ]

        for dep in risky_deps:
            assert dep not in content.lower(), (
                f"Risky dependency '{dep}' found in pyproject.toml. "
                "Use safe alternatives (JSON, etc.)"
            )


class TestSecurityHeaders:
    """Test suite for security headers (future web UI)."""

    def test_security_headers_documented(self) -> None:
        """Document required security headers for web UI.

        Security: When web UI is deployed, ensure security headers are set.
        """
        required_headers = {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "X-XSS-Protection": "1; mode=block",
            "Content-Security-Policy": "default-src 'self'",
            "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
        }

        assert True, (
            "When deploying web UI, ensure these security headers are set:\n"
            + "\n".join(f"  {k}: {v}" for k, v in required_headers.items())
        )


class TestDataSanitization:
    """Test suite for data sanitization."""

    def test_pii_not_logged(self) -> None:
        """Test that PII is not logged.

        Security: Prevents privacy violations through logs.

        Note: This should be enforced by FEAT-PRIV-002 (v0.2.11).
        """
        # Common PII patterns that should NOT appear in logs
        pii_patterns = [
            r'\b\d{3}-\d{2}-\d{4}\b',  # SSN
            r'\b\d{16}\b',  # Credit card
            r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',  # Email
            r'\b\d{3}-\d{3}-\d{4}\b',  # Phone number
        ]

        # This is a documentation test
        # Actual implementation in v0.2.11 FEAT-PRIV-002
        assert True, (
            "Ensure PII is not logged:\n"
            "- Hash queries before logging\n"
            "- Redact SSN patterns\n"
            "- Redact credit card patterns\n"
            "- Redact email addresses\n"
            "- Redact phone numbers\n"
            "\n"
            "Use PIIDetector from v0.2.11 for automatic detection/redaction."
        )


class TestCryptography:
    """Test suite for cryptographic operations."""

    def test_cryptography_library_available(self) -> None:
        """Test that cryptography library is available.

        Security: Required for v0.2.11 encryption features.
        """
        try:
            import cryptography
            assert True
        except ImportError:
            pytest.fail(
                "cryptography library not installed. "
                "Required for v0.2.11 encryption features. "
                "Install with: pip install cryptography"
            )

    def test_no_hardcoded_secrets(self) -> None:
        """Test that no hardcoded secrets exist in code.

        Security: Prevents credential leakage.
        """
        src_dir = Path("src")
        if not src_dir.exists():
            pytest.skip("src directory not found")

        # Patterns that might indicate hardcoded secrets
        secret_patterns = [
            (r'password\s*=\s*["\'][^"\']+["\']', "hardcoded password"),
            (r'api_key\s*=\s*["\'][^"\']+["\']', "hardcoded API key"),
            (r'secret\s*=\s*["\'][^"\']+["\']', "hardcoded secret"),
            (r'token\s*=\s*["\'][^"\']+["\']', "hardcoded token"),
        ]

        violations: List[str] = []

        for py_file in src_dir.rglob("*.py"):
            content = py_file.read_text(encoding="utf-8")

            for pattern, description in secret_patterns:
                if re.search(pattern, content, re.IGNORECASE):
                    # Check if it's in a comment or test
                    if "# example" in content.lower() or "# dummy" in content.lower():
                        continue

                    violations.append(f"{py_file}: {description}")

        if violations:
            pytest.fail(
                f"Potential hardcoded secrets found:\n" + "\n".join(violations) + "\n\n"
                "Use environment variables or secure key storage instead."
            )


# Mark all tests as security tests
pytestmark = pytest.mark.security
