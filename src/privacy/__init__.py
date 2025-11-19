"""Privacy utilities for ragged.

v0.2.11 Privacy Infrastructure

Provides PII detection, data lifecycle management, and GDPR compliance utilities.
"""

from src.privacy.gdpr import GDPRToolkit, get_gdpr_toolkit
from src.privacy.lifecycle import DataLifecycleManager, get_lifecycle_manager
from src.privacy.pii_detector import (
    PIIDetector,
    PIIRedactor,
    contains_pii,
    detect_pii,
    get_pii_detector,
    get_pii_redactor,
    hash_query,
    redact_pii,
)

__all__ = [
    # PII Detection
    "PIIDetector",
    "PIIRedactor",
    "get_pii_detector",
    "get_pii_redactor",
    "detect_pii",
    "contains_pii",
    "redact_pii",
    "hash_query",
    # Data Lifecycle
    "DataLifecycleManager",
    "get_lifecycle_manager",
    # GDPR Compliance
    "GDPRToolkit",
    "get_gdpr_toolkit",
]
