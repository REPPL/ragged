"""PII detection and redaction utilities.

v0.2.11 FEAT-PRIV-002: PII Detection and Redaction

Detects and redacts Personally Identifiable Information to protect privacy.
Prevents PII leakage through logs, metrics, and debug output.
"""

import hashlib
import logging
import re
from typing import List, Optional, Tuple

logger = logging.getLogger(__name__)


class PIIDetector:
    """Detects PII patterns in text.

    Supports detection of:
    - Social Security Numbers (SSN)
    - Credit card numbers
    - Phone numbers
    - Email addresses
    - IP addresses
    - Dates of birth

    Usage:
        >>> detector = PIIDetector()
        >>> findings = detector.detect("My SSN is 123-45-6789")
        >>> print(findings)
        [('ssn', '123-45-6789')]
    """

    # Regex patterns for common PII types
    PATTERNS = {
        "ssn": re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),  # US SSN: 123-45-6789
        "credit_card": re.compile(
            r"\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b"
        ),  # Credit card
        "phone": re.compile(
            r"\b(\+\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b"
        ),  # Phone
        "email": re.compile(
            r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"
        ),  # Email
        "ip_address": re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b"),  # IPv4
        "date_of_birth": re.compile(r"\b\d{1,2}/\d{1,2}/\d{4}\b"),  # DOB: MM/DD/YYYY
    }

    def detect(self, text: str) -> List[Tuple[str, str]]:
        """Detect PII in text.

        Args:
            text: Text to scan for PII

        Returns:
            List of (pii_type, matched_value) tuples

        Privacy: Logs warning when PII detected (for monitoring).
        """
        findings = []

        for pii_type, pattern in self.PATTERNS.items():
            matches = pattern.findall(text)
            for match in matches:
                # Handle tuple matches (from capturing groups)
                matched_value = match if isinstance(match, str) else match[0]
                findings.append((pii_type, matched_value))

        if findings:
            logger.warning(f"Detected {len(findings)} PII instances in text")

        return findings

    def contains_pii(self, text: str) -> bool:
        """Check if text contains any PII.

        Args:
            text: Text to check

        Returns:
            True if PII detected

        Usage:
            >>> detector = PIIDetector()
            >>> detector.contains_pii("Contact me at john@example.com")
            True
        """
        return len(self.detect(text)) > 0


class PIIRedactor:
    """Redacts PII from text.

    Usage:
        >>> redactor = PIIRedactor()
        >>> text = "Email: john@example.com, SSN: 123-45-6789"
        >>> redacted = redactor.redact(text)
        >>> print(redacted)
        'Email: [REDACTED-EMAIL], SSN: [REDACTED-SSN]'
    """

    def __init__(self):
        """Initialise redactor with detector."""
        self.detector = PIIDetector()

    def redact(self, text: str, replacement: str = "[REDACTED]") -> str:
        """Redact PII from text.

        Args:
            text: Text to redact
            replacement: Replacement string for PII (default: [REDACTED])

        Returns:
            Text with PII redacted

        Privacy: Each PII type gets specific marker (e.g., [REDACTED-EMAIL]).
        """
        redacted = text

        findings = self.detector.detect(text)

        for pii_type, value in findings:
            # Replace with type-specific marker
            marker = f"[REDACTED-{pii_type.upper()}]"
            redacted = redacted.replace(value, marker)

            logger.debug(f"Redacted {pii_type}: {value[:4]}...")

        return redacted

    def hash_for_logging(self, text: str, salt: str = "ragged-logging") -> str:
        """Hash text for logging (one-way, cannot recover original).

        Args:
            text: Text to hash
            salt: Salt for hash (prevents rainbow table attacks)

        Returns:
            Hex digest of SHA-256 hash (first 16 characters)

        Security: One-way hash prevents recovery of original query.
        Consistent hash allows correlation across logs.

        Usage:
            >>> redactor = PIIRedactor()
            >>> hash1 = redactor.hash_for_logging("sensitive query")
            >>> hash2 = redactor.hash_for_logging("sensitive query")
            >>> assert hash1 == hash2  # Same query = same hash
        """
        salted = f"{salt}:{text}".encode("utf-8")
        hash_digest = hashlib.sha256(salted).hexdigest()

        # Return first 16 chars for readability
        return hash_digest[:16]


# Global instances (singleton pattern)
_pii_detector: Optional[PIIDetector] = None
_pii_redactor: Optional[PIIRedactor] = None


def get_pii_detector() -> PIIDetector:
    """Get global PII detector instance (singleton).

    Returns:
        PIIDetector singleton

    Usage:
        >>> from src.privacy.pii_detector import get_pii_detector
        >>> detector = get_pii_detector()
        >>> has_pii = detector.contains_pii("text to check")
    """
    global _pii_detector
    if _pii_detector is None:
        _pii_detector = PIIDetector()
    return _pii_detector


def get_pii_redactor() -> PIIRedactor:
    """Get global PII redactor instance (singleton).

    Returns:
        PIIRedactor singleton

    Usage:
        >>> from src.privacy.pii_detector import get_pii_redactor
        >>> redactor = get_pii_redactor()
        >>> clean_text = redactor.redact("text with PII")
    """
    global _pii_redactor
    if _pii_redactor is None:
        _pii_redactor = PIIRedactor()
    return _pii_redactor


# Convenience functions
def detect_pii(text: str) -> List[Tuple[str, str]]:
    """Detect PII in text (convenience function).

    Args:
        text: Text to scan

    Returns:
        List of (pii_type, value) tuples

    Usage:
        >>> from src.privacy.pii_detector import detect_pii
        >>> findings = detect_pii("My email is john@example.com")
    """
    return get_pii_detector().detect(text)


def contains_pii(text: str) -> bool:
    """Check if text contains PII (convenience function).

    Args:
        text: Text to check

    Returns:
        True if PII detected

    Usage:
        >>> from src.privacy.pii_detector import contains_pii
        >>> if contains_pii(user_input):
        ...     print("Warning: input contains PII")
    """
    return get_pii_detector().contains_pii(text)


def redact_pii(text: str) -> str:
    """Redact PII from text (convenience function).

    Args:
        text: Text to redact

    Returns:
        Text with PII redacted

    Usage:
        >>> from src.privacy.pii_detector import redact_pii
        >>> safe_text = redact_pii("My SSN is 123-45-6789")
        >>> print(safe_text)
        'My SSN is [REDACTED-SSN]'
    """
    return get_pii_redactor().redact(text)


def hash_query(query: str) -> str:
    """Hash query for logging (convenience function).

    Args:
        query: Query to hash

    Returns:
        16-character hash

    Security: One-way hash for privacy-preserving logging.

    Usage:
        >>> from src.privacy.pii_detector import hash_query
        >>> import logging
        >>> logger = logging.getLogger(__name__)
        >>> query_hash = hash_query(user_query)
        >>> logger.info(f"Processing query: {query_hash}")  # Safe to log
    """
    return get_pii_redactor().hash_for_logging(query)
