"""
Logging configuration for ragged with privacy-safe structured logging.

This module provides structured JSON logging with privacy protections to ensure
no sensitive information (PII, file contents, API keys) is logged.
"""

import logging
import logging.handlers
import sys
from pathlib import Path
from typing import Any, Dict, Optional, Union

from pythonjsonlogger import json as jsonlogger

from src.config.settings import get_settings


class PrivacyFilter(logging.Filter):
    """
    Filter to remove or redact sensitive information from log records.

    Prevents logging of:
    - File contents
    - API keys and tokens
    - Potentially sensitive user data
    """

    SENSITIVE_KEYS = {
        "password",
        "token",
        "api_key",
        "secret",
        "auth",
        "credential",
        "content",  # Document content
        "text",  # Full text
    }

    def filter(self, record: logging.LogRecord) -> bool:
        """Filter and redact sensitive information from log records."""
        # Check message
        msg_lower = str(record.msg).lower()
        for key in self.SENSITIVE_KEYS:
            if key in msg_lower:
                # Don't completely block, but flag it
                record.msg = f"[REDACTED: potentially sensitive - {key}]"

        # Check extra fields if they exist
        if hasattr(record, "__dict__"):
            for key in list(record.__dict__.keys()):
                if any(sensitive in key.lower() for sensitive in self.SENSITIVE_KEYS):
                    record.__dict__[key] = "[REDACTED]"

        return True


class CustomJsonFormatter(jsonlogger.JsonFormatter):
    """Custom JSON formatter with additional metadata."""

    def add_fields(
        self,
        log_record: Dict[str, Any],
        record: logging.LogRecord,
        message_dict: Dict[str, Any],
    ) -> None:
        """Add custom fields to log records."""
        super().add_fields(log_record, record, message_dict)

        # Add standard fields
        log_record["level"] = record.levelname
        log_record["logger"] = record.name
        log_record["module"] = record.module
        log_record["function"] = record.funcName

        # Add timestamp in ISO format
        if not log_record.get("timestamp"):
            from datetime import datetime, timezone

            log_record["timestamp"] = datetime.now(timezone.utc).isoformat()


def setup_logging(
    log_level: Optional[str] = None,
    log_file: Optional[Path] = None,
    json_format: bool = True,
) -> None:
    """
    Configure application logging.

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL).
                   If None, uses value from settings.
        log_file: Path to log file. If None, logs only to console.
        json_format: Whether to use JSON formatting (True) or simple text (False).
    """
    settings = get_settings()
    level = log_level or settings.log_level

    # Get root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # Remove existing handlers
    root_logger.handlers = []

    # Privacy filter
    privacy_filter = PrivacyFilter()

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.addFilter(privacy_filter)

    console_formatter: Union[CustomJsonFormatter, logging.Formatter]
    if json_format:
        console_formatter = CustomJsonFormatter(
            "%(timestamp)s %(level)s %(logger)s %(message)s"
        )
    else:
        console_formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)

    # File handler (if specified)
    if log_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)

        # Use rotating file handler (max 10MB, keep 5 backups)
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5,
            encoding="utf-8",
        )
        file_handler.setLevel(level)
        file_handler.addFilter(privacy_filter)

        file_formatter: Union[CustomJsonFormatter, logging.Formatter]
        if json_format:
            file_formatter = CustomJsonFormatter(
                "%(timestamp)s %(level)s %(logger)s %(module)s %(function)s %(message)s"
            )
        else:
            file_formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(module)s:%(funcName)s - %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )

        file_handler.setFormatter(file_formatter)
        root_logger.addHandler(file_handler)


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance for the given name.

    Args:
        name: Logger name (typically __name__ of the module).

    Returns:
        Logger instance configured with application settings.
    """
    return logging.getLogger(name)
