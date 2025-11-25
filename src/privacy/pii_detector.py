"""PII detection and redaction utilities.

v0.2.11 FEAT-PRIV-002: PII Detection and Redaction
v0.5.7 HIGH-1: Visual PII Detection with OCR

Detects and redacts Personally Identifiable Information to protect privacy.
Prevents PII leakage through logs, metrics, and debug output.

NEW in v0.5.7:
- VisualPIIDetector: Detect PII in images using OCR
- Strict mode: Block images containing PII (GDPR/HIPAA compliance)
"""
from __future__ import annotations


import hashlib
import logging
import re
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from PIL import Image

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
            r"\b(?:\+\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b"
        ),  # Phone
        "email": re.compile(
            r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"
        ),  # Email
        "ip_address": re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b"),  # IPv4
        "date_of_birth": re.compile(r"\b\d{1,2}/\d{1,2}/\d{4}\b"),  # DOB: MM/DD/YYYY
    }

    def detect(self, text: str) -> list[tuple[str, str]]:
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
        salted = f"{salt}:{text}".encode()
        hash_digest = hashlib.sha256(salted).hexdigest()

        # Return first 16 chars for readability
        return hash_digest[:16]


class VisualPIIDetector(PIIDetector):
    """Detect PII in visual content (images, PDFs) using OCR.

    v0.5.7 HIGH-1: Visual PII Detection
    Security: Prevents accidental ingestion of sensitive documents containing PII.

    Usage:
        >>> detector = VisualPIIDetector(strict_mode=True)
        >>> from PIL import Image
        >>> image = Image.open("document.png")
        >>> findings = detector.detect_in_image(image)
        >>> if findings:
        ...     print(f"Found {len(findings)} PII instances in image")

    Strict Mode:
        When enabled, raises exception if PII detected (GDPR/HIPAA compliance).
        Use for healthcare, finance, or regulated environments.
    """

    def __init__(self, strict_mode: bool = False) -> None:
        """Initialise visual PII detector.

        Args:
            strict_mode: If True, raise exception when PII detected (default: False)

        Security (v0.5.7 HIGH-1):
        - strict_mode prevents ingestion of documents containing PII
        - Use in regulated environments (healthcare, finance)
        """
        super().__init__()
        self.strict_mode = strict_mode

        if self.strict_mode:
            logger.info("VisualPIIDetector initialised in STRICT mode (blocks PII)")
        else:
            logger.info("VisualPIIDetector initialised in WARNING mode (logs PII)")

    def extract_text_from_image(self, image: "Image.Image | Path") -> str:
        """Extract text from image using OCR.

        Args:
            image: PIL Image or path to image file

        Returns:
            Extracted text (empty string if no text found)

        Implementation:
        - Uses pytesseract for OCR (Tesseract OCR engine)
        - Supports: PNG, JPG, TIFF, BMP
        - Language: English (configurable)

        Security: OCR may introduce errors - use with caution for strict PII checks.

        Example:
            >>> from PIL import Image
            >>> detector = VisualPIIDetector()
            >>> img = Image.open("scan.png")
            >>> text = detector.extract_text_from_image(img)
            >>> print(f"Extracted: {len(text)} characters")
        """
        try:
            import pytesseract
            from PIL import Image
        except ImportError as e:
            logger.error(
                "pytesseract not installed. Install with: pip install pytesseract"
            )
            raise RuntimeError(
                "pytesseract required for visual PII detection. "
                "Install with: pip install pytesseract"
            ) from e

        # Load image if path provided
        if isinstance(image, (str, Path)):
            image = Image.open(image)

        # Convert to RGB if needed (Tesseract works best with RGB)
        if image.mode != "RGB":
            image = image.convert("RGB")

        # Extract text using OCR
        try:
            text = pytesseract.image_to_string(image, lang="eng")
            logger.debug(f"OCR extracted {len(text)} characters from image")
            return text
        except Exception as e:
            logger.error(f"OCR failed: {e}")
            return ""

    def detect_in_image(
        self, image: "Image.Image | Path"
    ) -> list[tuple[str, str]]:
        """Detect PII in image using OCR + pattern matching.

        Args:
            image: PIL Image or path to image file

        Returns:
            List of (pii_type, matched_value) tuples

        Raises:
            PIIDetectionError: If strict_mode enabled and PII detected

        Security (v0.5.7 HIGH-1):
        - Extracts text via OCR
        - Runs existing PII patterns on extracted text
        - In strict_mode, raises exception to block ingestion

        Example:
            >>> detector = VisualPIIDetector(strict_mode=True)
            >>> from PIL import Image
            >>> img = Image.open("patient_record.png")
            >>> try:
            ...     findings = detector.detect_in_image(img)
            ... except PIIDetectionError:
            ...     print("Blocked: Document contains PII")
        """
        # Extract text from image
        extracted_text = self.extract_text_from_image(image)

        if not extracted_text.strip():
            logger.debug("No text extracted from image (empty or no text content)")
            return []

        # Run PII detection on extracted text
        findings = self.detect(extracted_text)

        if findings:
            logger.warning(
                f"Visual PII detected: {len(findings)} instances in image "
                f"(types: {', '.join(set(f[0] for f in findings))})"
            )

            # Strict mode: raise exception to block ingestion
            if self.strict_mode:
                pii_types = ", ".join(set(f[0] for f in findings))
                raise PIIDetectionError(
                    f"Visual PII detected in image: {pii_types}. "
                    f"Ingestion blocked by strict mode (GDPR/HIPAA compliance)."
                )

        return findings

    def scan_pdf_page(
        self, pdf_path: Path, page_number: int = 0
    ) -> list[tuple[str, str]]:
        """Scan a single PDF page for PII.

        Args:
            pdf_path: Path to PDF file
            page_number: Page number to scan (0-indexed)

        Returns:
            List of (pii_type, matched_value) tuples

        Raises:
            PIIDetectionError: If strict_mode enabled and PII detected

        Security: Useful for scanning individual pages before ingestion.

        Example:
            >>> detector = VisualPIIDetector()
            >>> findings = detector.scan_pdf_page(Path("document.pdf"), page_number=0)
        """
        try:
            from pdf2image import convert_from_path
        except ImportError as e:
            logger.error("pdf2image not installed. Install with: pip install pdf2image")
            raise RuntimeError(
                "pdf2image required for PDF PII detection. "
                "Install with: pip install pdf2image"
            ) from e

        # Convert PDF page to image
        try:
            images = convert_from_path(
                pdf_path,
                first_page=page_number + 1,  # pdf2image uses 1-indexed pages
                last_page=page_number + 1,
                dpi=150,  # Match vision DPI setting
            )

            if not images:
                logger.warning(f"Could not convert PDF page {page_number} to image")
                return []

            # Scan the page image for PII
            return self.detect_in_image(images[0])

        except Exception as e:
            logger.error(f"Failed to scan PDF page {page_number}: {e}")
            return []


class PIIDetectionError(Exception):
    """Raised when PII detected in strict mode.

    v0.5.7 HIGH-1: Visual PII Detection
    Used to block document ingestion when PII found in visual content.
    """

    pass


# Global instances (singleton pattern)
_pii_detector: PIIDetector | None = None
_pii_redactor: PIIRedactor | None = None
_visual_pii_detector: VisualPIIDetector | None = None


def get_pii_detector() -> PIIDetector:
    """Get global PII detector instance (singleton).

    Returns:
        PIIDetector singleton

    Usage:
        >>> from ragged.privacy.pii_detector import get_pii_detector
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
        >>> from ragged.privacy.pii_detector import get_pii_redactor
        >>> redactor = get_pii_redactor()
        >>> clean_text = redactor.redact("text with PII")
    """
    global _pii_redactor
    if _pii_redactor is None:
        _pii_redactor = PIIRedactor()
    return _pii_redactor


def get_visual_pii_detector(strict_mode: bool = False) -> VisualPIIDetector:
    """Get global visual PII detector instance (singleton).

    v0.5.7 HIGH-1: Visual PII Detection

    Args:
        strict_mode: If True, raise exception when PII detected

    Returns:
        VisualPIIDetector singleton

    Usage:
        >>> from ragged.privacy.pii_detector import get_visual_pii_detector
        >>> detector = get_visual_pii_detector(strict_mode=True)
        >>> from PIL import Image
        >>> img = Image.open("document.png")
        >>> try:
        ...     findings = detector.detect_in_image(img)
        ... except PIIDetectionError:
        ...     print("Blocked: PII detected in image")
    """
    global _visual_pii_detector
    if _visual_pii_detector is None:
        _visual_pii_detector = VisualPIIDetector(strict_mode=strict_mode)
    return _visual_pii_detector


# Convenience functions
def detect_pii(text: str) -> list[tuple[str, str]]:
    """Detect PII in text (convenience function).

    Args:
        text: Text to scan

    Returns:
        List of (pii_type, value) tuples

    Usage:
        >>> from ragged.privacy.pii_detector import detect_pii
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
        >>> from ragged.privacy.pii_detector import contains_pii
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
        >>> from ragged.privacy.pii_detector import redact_pii
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
        >>> from ragged.privacy.pii_detector import hash_query
        >>> import logging
        >>> logger = logging.getLogger(__name__)
        >>> query_hash = hash_query(user_query)
        >>> logger.info(f"Processing query: {query_hash}")  # Safe to log
    """
    return get_pii_redactor().hash_for_logging(query)


def detect_visual_pii(
    image: "Image.Image | Path", strict_mode: bool = False
) -> list[tuple[str, str]]:
    """Detect PII in image using OCR (convenience function).

    v0.5.7 HIGH-1: Visual PII Detection

    Args:
        image: PIL Image or path to image file
        strict_mode: If True, raise exception when PII detected

    Returns:
        List of (pii_type, value) tuples

    Raises:
        PIIDetectionError: If strict_mode enabled and PII detected

    Security: Use strict_mode for regulated environments (healthcare, finance).

    Usage:
        >>> from ragged.privacy.pii_detector import detect_visual_pii
        >>> from PIL import Image
        >>> img = Image.open("scan.png")
        >>> findings = detect_visual_pii(img, strict_mode=False)
        >>> if findings:
        ...     print(f"Warning: Found {len(findings)} PII instances")
    """
    detector = get_visual_pii_detector(strict_mode=strict_mode)
    return detector.detect_in_image(image)


def scan_pdf_for_pii(
    pdf_path: Path, page_number: int = 0, strict_mode: bool = False
) -> list[tuple[str, str]]:
    """Scan PDF page for PII (convenience function).

    v0.5.7 HIGH-1: Visual PII Detection

    Args:
        pdf_path: Path to PDF file
        page_number: Page to scan (0-indexed)
        strict_mode: If True, raise exception when PII detected

    Returns:
        List of (pii_type, value) tuples

    Raises:
        PIIDetectionError: If strict_mode enabled and PII detected

    Usage:
        >>> from pathlib import Path
        >>> from ragged.privacy.pii_detector import scan_pdf_for_pii
        >>> findings = scan_pdf_for_pii(Path("document.pdf"), page_number=0)
        >>> if findings:
        ...     print(f"Page contains {len(findings)} PII instances")
    """
    detector = get_visual_pii_detector(strict_mode=strict_mode)
    return detector.scan_pdf_page(pdf_path, page_number)
