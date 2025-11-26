"""
Secrets Generation and Management.

INSTALL-SEC-003: Secure secret generation during installation.
"""

import logging
import math
import secrets
import string
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class SecretStrength(Enum):
    """Secret strength levels."""

    WEAK = "weak"
    MODERATE = "moderate"
    STRONG = "strong"
    VERY_STRONG = "very_strong"


@dataclass
class SecretValidation:
    """Result of secret strength validation."""

    strength: SecretStrength
    entropy_bits: float
    issues: list[str]
    recommendations: list[str]


def generate_jwt_secret(length: int = 32) -> str:
    """
    Generate cryptographically secure JWT secret.

    Args:
        length: Number of bytes (default 32 = 256 bits).

    Returns:
        URL-safe base64 encoded secret.
    """
    return secrets.token_urlsafe(length)


def generate_admin_password(
    length: int = 24,
    include_symbols: bool = True,
) -> str:
    """
    Generate strong admin password.

    Args:
        length: Password length (default 24).
        include_symbols: Include special characters.

    Returns:
        Secure random password.
    """
    alphabet = string.ascii_letters + string.digits
    if include_symbols:
        # Use safe symbols that work across platforms
        alphabet += "!@#$%^&*()-_=+"

    # Ensure password has at least one of each required type
    password_chars = [
        secrets.choice(string.ascii_lowercase),
        secrets.choice(string.ascii_uppercase),
        secrets.choice(string.digits),
    ]

    if include_symbols:
        password_chars.append(secrets.choice("!@#$%^&*()-_=+"))

    # Fill rest with random characters
    remaining_length = length - len(password_chars)
    password_chars.extend(
        secrets.choice(alphabet) for _ in range(remaining_length)
    )

    # Shuffle to avoid predictable patterns
    password_list = list(password_chars)
    # Use Fisher-Yates shuffle with secure random
    for i in range(len(password_list) - 1, 0, -1):
        j = secrets.randbelow(i + 1)
        password_list[i], password_list[j] = password_list[j], password_list[i]

    return "".join(password_list)


def generate_api_key(prefix: str = "ragged_") -> str:
    """
    Generate API key.

    Args:
        prefix: Key prefix for identification.

    Returns:
        API key with prefix.
    """
    key = secrets.token_urlsafe(32)
    return f"{prefix}{key}"


def generate_encryption_key(length: int = 32) -> bytes:
    """
    Generate encryption key for symmetric encryption.

    Args:
        length: Key length in bytes (default 32 = 256 bits).

    Returns:
        Random bytes suitable for encryption.
    """
    return secrets.token_bytes(length)


def generate_fernet_key() -> str:
    """
    Generate Fernet encryption key.

    Returns:
        Base64-encoded Fernet key.
    """
    from cryptography.fernet import Fernet

    return Fernet.generate_key().decode()


def calculate_entropy(secret: str) -> float:
    """
    Calculate entropy of a secret in bits.

    Args:
        secret: Secret string.

    Returns:
        Entropy in bits.
    """
    if not secret:
        return 0.0

    # Determine character set size
    charset_size = 0
    has_lower = any(c in string.ascii_lowercase for c in secret)
    has_upper = any(c in string.ascii_uppercase for c in secret)
    has_digit = any(c in string.digits for c in secret)
    has_symbol = any(c in string.punctuation for c in secret)

    if has_lower:
        charset_size += 26
    if has_upper:
        charset_size += 26
    if has_digit:
        charset_size += 10
    if has_symbol:
        charset_size += 32  # Common symbols

    if charset_size == 0:
        return 0.0

    # Entropy = length * log2(charset_size)
    return len(secret) * math.log2(charset_size)


def validate_secret_strength(
    secret: str,
    min_length: int = 16,
    require_mixed_case: bool = True,
    require_digits: bool = True,
    require_symbols: bool = False,
) -> SecretValidation:
    """
    Validate secret strength.

    Args:
        secret: Secret to validate.
        min_length: Minimum required length.
        require_mixed_case: Require upper and lower case.
        require_digits: Require numeric digits.
        require_symbols: Require special characters.

    Returns:
        SecretValidation with strength assessment.
    """
    issues: list[str] = []
    recommendations: list[str] = []

    # Check length
    if len(secret) < min_length:
        issues.append(f"Too short ({len(secret)} < {min_length})")
        recommendations.append(f"Use at least {min_length} characters")

    # Check character types
    has_lower = any(c in string.ascii_lowercase for c in secret)
    has_upper = any(c in string.ascii_uppercase for c in secret)
    has_digit = any(c in string.digits for c in secret)
    has_symbol = any(c in string.punctuation for c in secret)

    if require_mixed_case:
        if not has_lower:
            issues.append("No lowercase letters")
            recommendations.append("Add lowercase letters")
        if not has_upper:
            issues.append("No uppercase letters")
            recommendations.append("Add uppercase letters")

    if require_digits and not has_digit:
        issues.append("No digits")
        recommendations.append("Add numeric digits")

    if require_symbols and not has_symbol:
        issues.append("No special characters")
        recommendations.append("Add special characters")

    # Calculate entropy
    entropy = calculate_entropy(secret)

    # Determine strength
    if entropy < 40 or len(issues) > 2:
        strength = SecretStrength.WEAK
    elif entropy < 60 or len(issues) > 0:
        strength = SecretStrength.MODERATE
    elif entropy < 80:
        strength = SecretStrength.STRONG
    else:
        strength = SecretStrength.VERY_STRONG

    return SecretValidation(
        strength=strength,
        entropy_bits=entropy,
        issues=issues,
        recommendations=recommendations,
    )


class SecretStore:
    """
    Secure secret storage.

    Manages secrets in .env file with proper permissions.
    """

    def __init__(self, env_path: Path) -> None:
        """
        Initialise secret store.

        Args:
            env_path: Path to .env file.
        """
        self.env_path = env_path
        self._secrets: dict[str, str] = {}
        self._load()

    def _load(self) -> None:
        """Load secrets from .env file."""
        if not self.env_path.exists():
            return

        with open(self.env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    self._secrets[key.strip()] = value.strip()

    def get(self, key: str) -> str | None:
        """Get a secret."""
        return self._secrets.get(key)

    def set(self, key: str, value: str) -> None:
        """Set a secret."""
        self._secrets[key] = value

    def save(self) -> None:
        """Save secrets to .env file with secure permissions."""
        import os
        import stat

        # Ensure parent directory exists
        self.env_path.parent.mkdir(parents=True, exist_ok=True)

        # Write secrets
        with open(self.env_path, "w") as f:
            f.write("# ragged secrets - DO NOT COMMIT\n")
            f.write("# Generated automatically during installation\n\n")
            for key, value in self._secrets.items():
                f.write(f"{key}={value}\n")

        # Set restrictive permissions (user-only read/write)
        os.chmod(self.env_path, stat.S_IRUSR | stat.S_IWUSR)

    def generate_all(self) -> dict[str, str]:
        """
        Generate all required secrets.

        Returns:
            Dictionary of generated secrets.
        """
        generated = {
            "JWT_SECRET": generate_jwt_secret(),
            "ADMIN_PASSWORD": generate_admin_password(),
            "API_KEY": generate_api_key(),
            "ENCRYPTION_KEY": generate_fernet_key(),
        }

        for key, value in generated.items():
            self.set(key, value)

        return generated


def redact_secret(secret: str, show_chars: int = 4) -> str:
    """
    Redact a secret for display.

    Args:
        secret: Secret to redact.
        show_chars: Number of characters to show at end.

    Returns:
        Redacted secret string.
    """
    if len(secret) <= show_chars:
        return "*" * len(secret)

    hidden_length = len(secret) - show_chars
    return "*" * hidden_length + secret[-show_chars:]


def format_secret_for_display(key: str, value: str) -> str:
    """
    Format secret for display (redacted).

    Args:
        key: Secret key name.
        value: Secret value.

    Returns:
        Formatted string with redacted value.
    """
    return f"{key}: {redact_secret(value)}"
