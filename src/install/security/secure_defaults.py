"""
Secure Configuration Defaults.

INSTALL-SEC-002: Security-by-default configuration.
"""

import logging
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class SecurityLevel(Enum):
    """Security level for configuration."""

    STRICT = "strict"  # Maximum security, may require adjustments
    STANDARD = "standard"  # Secure defaults, balanced usability
    RELAXED = "relaxed"  # Less secure, for development


@dataclass
class SecurityWarning:
    """Security warning for configuration issues."""

    category: str
    severity: str  # critical, high, medium, low
    message: str
    recommendation: str
    config_key: str | None = None


@dataclass
class SecureDefaults:
    """Secure configuration defaults."""

    # Authentication
    authentication_enabled: bool = True
    session_timeout_minutes: int = 60
    max_login_attempts: int = 5
    lockout_duration_minutes: int = 15

    # Network
    bind_host: str = "127.0.0.1"  # localhost only
    enable_https: bool = True
    hsts_enabled: bool = True
    cors_allow_origins: list[str] = field(default_factory=lambda: [
        "http://localhost:5173",
        "https://localhost:5173",
    ])

    # File Permissions
    secrets_permission: int = 0o600  # user-only read/write
    config_permission: int = 0o600  # user-only read/write
    data_permission: int = 0o700  # user-only full access
    log_permission: int = 0o644  # readable by all

    # Debug
    debug_mode: bool = False
    expose_stack_traces: bool = False
    verbose_logging: bool = False

    # API
    rate_limiting_enabled: bool = True
    max_requests_per_minute: int = 100
    max_upload_size_mb: int = 50


def apply_secure_defaults(
    config: dict[str, Any],
    security_level: SecurityLevel = SecurityLevel.STANDARD,
) -> dict[str, Any]:
    """
    Apply secure defaults to configuration.

    Args:
        config: Configuration dictionary.
        security_level: Security level to apply.

    Returns:
        Configuration with secure defaults applied.
    """
    defaults = SecureDefaults()

    # Apply defaults based on security level
    if security_level == SecurityLevel.STRICT:
        defaults.session_timeout_minutes = 30
        defaults.max_login_attempts = 3
        defaults.max_requests_per_minute = 60

    # Server configuration
    if "server" not in config:
        config["server"] = {}

    server = config["server"]
    server.setdefault("host", defaults.bind_host)
    server.setdefault("https_enabled", defaults.enable_https)
    server.setdefault("hsts_enabled", defaults.hsts_enabled)

    # Security configuration
    if "security" not in config:
        config["security"] = {}

    security = config["security"]
    security.setdefault("authentication_enabled", defaults.authentication_enabled)
    security.setdefault("session_timeout_minutes", defaults.session_timeout_minutes)
    security.setdefault("max_login_attempts", defaults.max_login_attempts)
    security.setdefault("lockout_duration_minutes", defaults.lockout_duration_minutes)
    security.setdefault("rate_limiting_enabled", defaults.rate_limiting_enabled)
    security.setdefault("max_requests_per_minute", defaults.max_requests_per_minute)

    # CORS configuration
    if "cors" not in config:
        config["cors"] = {}

    cors = config["cors"]
    cors.setdefault("allow_origins", defaults.cors_allow_origins)
    cors.setdefault("allow_credentials", True)
    cors.setdefault("allow_methods", ["GET", "POST", "PUT", "DELETE"])

    # Debug settings
    if "debug" not in config:
        config["debug"] = {}

    debug = config["debug"]
    debug.setdefault("enabled", defaults.debug_mode)
    debug.setdefault("expose_stack_traces", defaults.expose_stack_traces)
    debug.setdefault("verbose_logging", defaults.verbose_logging)

    # Upload limits
    if "upload" not in config:
        config["upload"] = {}

    upload = config["upload"]
    upload.setdefault("max_size_mb", defaults.max_upload_size_mb)

    return config


def validate_security_config(
    config: dict[str, Any],
) -> list[SecurityWarning]:
    """
    Validate configuration for security issues.

    Args:
        config: Configuration to validate.

    Returns:
        List of security warnings.
    """
    warnings: list[SecurityWarning] = []

    # Check authentication
    security = config.get("security", {})
    if not security.get("authentication_enabled", True):
        warnings.append(SecurityWarning(
            category="authentication",
            severity="critical",
            message="Authentication is disabled",
            recommendation="Enable authentication to protect your data",
            config_key="security.authentication_enabled",
        ))

    # Check binding
    server = config.get("server", {})
    host = server.get("host", "127.0.0.1")
    if host in ("0.0.0.0", "::"):
        warnings.append(SecurityWarning(
            category="network",
            severity="high",
            message=f"Server binding to {host} (all interfaces)",
            recommendation="Bind to localhost (127.0.0.1) unless external access required",
            config_key="server.host",
        ))

    # Check HTTPS
    if not server.get("https_enabled", True):
        warnings.append(SecurityWarning(
            category="network",
            severity="high",
            message="HTTPS is disabled",
            recommendation="Enable HTTPS for encrypted communication",
            config_key="server.https_enabled",
        ))

    # Check debug mode
    debug = config.get("debug", {})
    if debug.get("enabled", False):
        warnings.append(SecurityWarning(
            category="debug",
            severity="medium",
            message="Debug mode is enabled",
            recommendation="Disable debug mode in production",
            config_key="debug.enabled",
        ))

    if debug.get("expose_stack_traces", False):
        warnings.append(SecurityWarning(
            category="debug",
            severity="high",
            message="Stack traces exposed in errors",
            recommendation="Disable stack trace exposure in production",
            config_key="debug.expose_stack_traces",
        ))

    # Check CORS
    cors = config.get("cors", {})
    origins = cors.get("allow_origins", [])
    if "*" in origins:
        warnings.append(SecurityWarning(
            category="cors",
            severity="high",
            message="CORS allows all origins (*)",
            recommendation="Restrict CORS to specific trusted origins",
            config_key="cors.allow_origins",
        ))

    # Check rate limiting
    if not security.get("rate_limiting_enabled", True):
        warnings.append(SecurityWarning(
            category="security",
            severity="medium",
            message="Rate limiting is disabled",
            recommendation="Enable rate limiting to prevent abuse",
            config_key="security.rate_limiting_enabled",
        ))

    # Check session timeout
    timeout = security.get("session_timeout_minutes", 60)
    if timeout > 480:  # 8 hours
        warnings.append(SecurityWarning(
            category="authentication",
            severity="low",
            message=f"Long session timeout ({timeout} minutes)",
            recommendation="Consider reducing session timeout for better security",
            config_key="security.session_timeout_minutes",
        ))

    return warnings


def format_security_warnings(
    warnings: list[SecurityWarning],
) -> str:
    """
    Format security warnings for display.

    Args:
        warnings: List of warnings.

    Returns:
        Formatted string.
    """
    if not warnings:
        return "No security warnings"

    lines = ["Security Warnings:", ""]

    severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    sorted_warnings = sorted(warnings, key=lambda w: severity_order.get(w.severity, 4))

    severity_icons = {
        "critical": "[!]",
        "high": "[H]",
        "medium": "[M]",
        "low": "[L]",
    }

    for warning in sorted_warnings:
        icon = severity_icons.get(warning.severity, "[?]")
        lines.append(f"{icon} {warning.message}")
        lines.append(f"    Recommendation: {warning.recommendation}")
        if warning.config_key:
            lines.append(f"    Config: {warning.config_key}")
        lines.append("")

    return "\n".join(lines)


def is_config_secure(config: dict[str, Any]) -> bool:
    """
    Check if configuration is secure.

    Args:
        config: Configuration to check.

    Returns:
        True if no critical or high severity warnings.
    """
    warnings = validate_security_config(config)
    return not any(
        w.severity in ("critical", "high")
        for w in warnings
    )


def generate_secure_config(
    base_config: dict[str, Any] | None = None,
    security_level: SecurityLevel = SecurityLevel.STANDARD,
) -> dict[str, Any]:
    """
    Generate a secure configuration.

    Args:
        base_config: Base configuration to extend.
        security_level: Security level.

    Returns:
        Secure configuration dictionary.
    """
    config = base_config.copy() if base_config else {}
    return apply_secure_defaults(config, security_level)
