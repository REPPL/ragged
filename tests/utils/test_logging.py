"""Tests for logging utilities."""

import json
import logging
from pathlib import Path

import pytest

from src.utils.logging import (
    CustomJsonFormatter,
    PrivacyFilter,
    get_logger,
    setup_logging,
)


class TestPrivacyFilter:
    """Test suite for PrivacyFilter."""

    def test_redacts_sensitive_keys(self) -> None:
        """Test that sensitive keys are redacted."""
        filter = PrivacyFilter()

        # Create a log record with sensitive information
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="This message contains a password",
            args=(),
            exc_info=None,
        )

        result = filter.filter(record)

        assert result is True
        assert "[REDACTED:" in record.msg
        assert "password" not in record.msg.lower() or "[REDACTED:" in record.msg

    def test_redacts_api_key(self) -> None:
        """Test that API keys are redacted."""
        filter = PrivacyFilter()

        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="API_KEY=secret123",
            args=(),
            exc_info=None,
        )

        result = filter.filter(record)

        assert result is True
        assert "[REDACTED:" in record.msg

    def test_allows_non_sensitive(self) -> None:
        """Test that non-sensitive messages pass through."""
        filter = PrivacyFilter()

        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="Processing document with 100 chunks",
            args=(),
            exc_info=None,
        )

        original_msg = record.msg
        result = filter.filter(record)

        assert result is True
        assert record.msg == original_msg


class TestCustomJsonFormatter:
    """Test suite for CustomJsonFormatter."""

    def test_formats_to_json(self) -> None:
        """Test that log records are formatted as valid JSON."""
        formatter = CustomJsonFormatter()

        record = logging.LogRecord(
            name="test.module",
            level=logging.INFO,
            pathname="/path/to/file.py",
            lineno=42,
            msg="Test message",
            args=(),
            exc_info=None,
        )
        record.module = "test_module"
        record.funcName = "test_function"

        formatted = formatter.format(record)

        # Should be valid JSON
        parsed = json.loads(formatted)
        assert parsed["message"] == "Test message"
        assert parsed["level"] == "INFO"
        assert parsed["logger"] == "test.module"
        assert parsed["module"] == "test_module"
        assert parsed["function"] == "test_function"
        assert "timestamp" in parsed

    def test_includes_extra_fields(self) -> None:
        """Test that extra fields are included in JSON output."""
        formatter = CustomJsonFormatter()

        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="Test",
            args=(),
            exc_info=None,
        )
        record.module = "test"
        record.funcName = "test"
        record.custom_field = "custom_value"

        formatted = formatter.format(record)
        parsed = json.loads(formatted)

        assert parsed["custom_field"] == "custom_value"


class TestSetupLogging:
    """Test suite for setup_logging function."""

    def test_setup_with_defaults(self, temp_dir: Path) -> None:
        """Test logging setup with default parameters."""
        log_file = temp_dir / "test.log"

        setup_logging(log_level="INFO", log_file=log_file, json_format=True)

        logger = logging.getLogger("test")
        logger.info("Test message")

        # Check log file was created and contains message
        assert log_file.exists()
        content = log_file.read_text()
        assert "Test message" in content

    def test_setup_with_text_format(self, temp_dir: Path) -> None:
        """Test logging setup with text formatting."""
        log_file = temp_dir / "test.log"

        setup_logging(log_level="DEBUG", log_file=log_file, json_format=False)

        logger = logging.getLogger("test")
        logger.debug("Debug message")

        content = log_file.read_text()
        assert "Debug message" in content
        assert "DEBUG" in content

    def test_console_only_logging(self) -> None:
        """Test logging to console only (no file)."""
        import io
        import sys

        # Capture stdout
        captured_output = io.StringIO()
        old_stdout = sys.stdout
        sys.stdout = captured_output

        try:
            setup_logging(log_level="WARNING", json_format=False)

            logger = logging.getLogger("test")
            logger.warning("Warning message")

            # Restore stdout and get output
            sys.stdout = old_stdout
            output = captured_output.getvalue()

            assert "Warning message" in output or "[REDACTED:" in output
        finally:
            sys.stdout = old_stdout

    def test_log_file_rotation_creates_directory(self, temp_dir: Path) -> None:
        """Test that log file directory is created if it doesn't exist."""
        log_file = temp_dir / "logs" / "app" / "test.log"

        setup_logging(log_file=log_file)

        logger = logging.getLogger("test")
        logger.info("Test")

        assert log_file.parent.exists()
        assert log_file.exists()

    def test_privacy_filter_applied(self, temp_dir: Path) -> None:
        """Test that privacy filter is applied to logs."""
        log_file = temp_dir / "test.log"

        setup_logging(log_file=log_file, json_format=False)

        logger = logging.getLogger("test")
        logger.info("User password is: secret123")

        content = log_file.read_text()
        assert "[REDACTED:" in content


class TestGetLogger:
    """Test suite for get_logger function."""

    def test_returns_logger_instance(self) -> None:
        """Test that get_logger returns a Logger instance."""
        logger = get_logger("test.module")

        assert isinstance(logger, logging.Logger)
        assert logger.name == "test.module"

    def test_loggers_are_hierarchical(self) -> None:
        """Test that loggers follow Python's hierarchical naming."""
        parent = get_logger("parent")
        child = get_logger("parent.child")

        assert child.parent == parent
