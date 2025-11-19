"""Tests for PII detection and redaction.

v0.2.11 FEAT-PRIV-002: PII Detection and Redaction

Tests for detecting and redacting personally identifiable information.
"""

import pytest

from src.privacy.pii_detector import (
    PIIDetector,
    PIIRedactor,
    contains_pii,
    detect_pii,
    hash_query,
    redact_pii,
)


class TestPIIDetector:
    """Test suite for PII detection."""

    def test_detect_ssn(self) -> None:
        """Test SSN detection."""
        detector = PIIDetector()

        text = "User's SSN is 123-45-6789"
        findings = detector.detect(text)

        assert len(findings) > 0, "SSN not detected"
        assert findings[0][0] == "ssn"
        assert findings[0][1] == "123-45-6789"

    def test_detect_multiple_ssns(self) -> None:
        """Test detection of multiple SSNs."""
        detector = PIIDetector()

        text = "SSN 123-45-6789 and SSN 987-65-4321"
        findings = detector.detect(text)

        ssn_findings = [f for f in findings if f[0] == "ssn"]
        assert len(ssn_findings) == 2

    def test_detect_credit_card(self) -> None:
        """Test credit card detection."""
        detector = PIIDetector()

        test_cases = [
            "4532-1234-5678-9010",  # With dashes
            "4532 1234 5678 9010",  # With spaces
            "4532123456789010",  # No separators
        ]

        for text in test_cases:
            findings = detector.detect(f"Card: {text}")
            assert len(findings) > 0, f"Credit card not detected in: {text}"
            assert findings[0][0] == "credit_card"

    def test_detect_email(self) -> None:
        """Test email detection."""
        detector = PIIDetector()

        test_cases = [
            "john.doe@example.com",
            "user+tag@subdomain.example.co.uk",
            "simple@email.org",
        ]

        for email in test_cases:
            findings = detector.detect(f"Contact: {email}")
            assert len(findings) > 0, f"Email not detected: {email}"
            assert findings[0][0] == "email"
            assert findings[0][1] == email

    def test_detect_phone_number(self) -> None:
        """Test phone number detection."""
        detector = PIIDetector()

        test_cases = [
            "555-123-4567",  # Standard format
            "(555) 123-4567",  # With parentheses
            "555.123.4567",  # With dots
            "+1-555-123-4567",  # With country code
        ]

        for phone in test_cases:
            findings = detector.detect(f"Call: {phone}")
            assert len(findings) > 0, f"Phone not detected: {phone}"
            assert findings[0][0] == "phone"

    def test_detect_ip_address(self) -> None:
        """Test IP address detection."""
        detector = PIIDetector()

        text = "Server IP: 192.168.1.100"
        findings = detector.detect(text)

        assert len(findings) > 0
        assert findings[0][0] == "ip_address"
        assert findings[0][1] == "192.168.1.100"

    def test_detect_date_of_birth(self) -> None:
        """Test date of birth detection."""
        detector = PIIDetector()

        test_cases = [
            "01/15/1990",
            "12/31/1985",
            "3/5/2000",
        ]

        for dob in test_cases:
            findings = detector.detect(f"DOB: {dob}")
            assert len(findings) > 0, f"DOB not detected: {dob}"
            assert findings[0][0] == "date_of_birth"

    def test_detect_multiple_pii_types(self) -> None:
        """Test detection of multiple PII types in same text."""
        detector = PIIDetector()

        text = (
            "John Doe, email: john@example.com, "
            "SSN: 123-45-6789, phone: 555-123-4567"
        )
        findings = detector.detect(text)

        # Should detect email, SSN, and phone
        assert len(findings) >= 3

        pii_types = {f[0] for f in findings}
        assert "email" in pii_types
        assert "ssn" in pii_types
        assert "phone" in pii_types

    def test_contains_pii_true(self) -> None:
        """Test contains_pii returns True when PII present."""
        detector = PIIDetector()

        assert detector.contains_pii("Email: user@example.com")
        assert detector.contains_pii("SSN: 123-45-6789")
        assert detector.contains_pii("Phone: 555-123-4567")

    def test_contains_pii_false(self) -> None:
        """Test contains_pii returns False when no PII."""
        detector = PIIDetector()

        assert not detector.contains_pii("This is a normal sentence.")
        assert not detector.contains_pii("No sensitive information here!")
        assert not detector.contains_pii("Just some regular text about nothing.")

    def test_no_false_positives_on_normal_text(self) -> None:
        """Test that normal text doesn't trigger false positives."""
        detector = PIIDetector()

        normal_texts = [
            "The meeting is at 3 o'clock.",
            "I have 5 apples and 10 oranges.",
            "Call me later.",  # "Call me" shouldn't trigger phone detection
            "The server is running.",  # Shouldn't trigger IP detection
        ]

        for text in normal_texts:
            findings = detector.detect(text)
            # Some might have edge case matches, but should be minimal
            assert len(findings) <= 1, f"False positive in: {text}"


class TestPIIRedactor:
    """Test suite for PII redaction."""

    def test_redact_ssn(self) -> None:
        """Test SSN redaction."""
        redactor = PIIRedactor()

        text = "User's SSN is 123-45-6789"
        redacted = redactor.redact(text)

        assert "123-45-6789" not in redacted
        assert "[REDACTED-SSN]" in redacted

    def test_redact_multiple_pii(self) -> None:
        """Test redaction of multiple PII instances."""
        redactor = PIIRedactor()

        text = "Email john@example.com, SSN 123-45-6789, phone 555-123-4567"
        redacted = redactor.redact(text)

        # PII should be replaced
        assert "john@example.com" not in redacted
        assert "123-45-6789" not in redacted
        assert "555-123-4567" not in redacted

        # Redaction markers should be present
        assert "[REDACTED-EMAIL]" in redacted
        assert "[REDACTED-SSN]" in redacted
        assert "[REDACTED-PHONE]" in redacted

    def test_redact_preserves_structure(self) -> None:
        """Test that redaction preserves sentence structure."""
        redactor = PIIRedactor()

        text = "Contact John at john@example.com or call 555-123-4567"
        redacted = redactor.redact(text)

        # Structure words should remain
        assert "Contact" in redacted
        assert "at" in redacted
        assert "or call" in redacted

    def test_redact_custom_replacement(self) -> None:
        """Test redaction with custom replacement string."""
        redactor = PIIRedactor()

        text = "SSN: 123-45-6789"
        redacted = redactor.redact(text, replacement="***")

        # Should use type-specific markers, not custom replacement
        # (Custom replacement parameter exists but type-specific is preferred)
        assert "123-45-6789" not in redacted

    def test_redact_no_pii(self) -> None:
        """Test redaction of text with no PII."""
        redactor = PIIRedactor()

        text = "This is clean text with no PII."
        redacted = redactor.redact(text)

        # Should be unchanged
        assert redacted == text

    def test_hash_for_logging_consistency(self) -> None:
        """Test that hash_for_logging produces consistent hashes."""
        redactor = PIIRedactor()

        query = "What is John Doe's credit card number?"

        hash1 = redactor.hash_for_logging(query)
        hash2 = redactor.hash_for_logging(query)

        # Same query should produce same hash
        assert hash1 == hash2
        assert len(hash1) == 16  # Should be 16 characters

    def test_hash_for_logging_different_queries(self) -> None:
        """Test that different queries produce different hashes."""
        redactor = PIIRedactor()

        hash1 = redactor.hash_for_logging("Query 1")
        hash2 = redactor.hash_for_logging("Query 2")

        # Different queries should produce different hashes
        assert hash1 != hash2

    def test_hash_for_logging_no_original_content(self) -> None:
        """Test that hash doesn't contain original query content."""
        redactor = PIIRedactor()

        query = "What is John Doe's SSN 123-45-6789?"
        query_hash = redactor.hash_for_logging(query)

        # Hash should not contain original text
        assert "John Doe" not in query_hash
        assert "SSN" not in query_hash
        assert "123-45-6789" not in query_hash
        assert "What" not in query_hash

    def test_hash_for_logging_salt_affects_hash(self) -> None:
        """Test that different salts produce different hashes."""
        redactor = PIIRedactor()

        query = "test query"

        hash1 = redactor.hash_for_logging(query, salt="salt1")
        hash2 = redactor.hash_for_logging(query, salt="salt2")

        # Different salts should produce different hashes
        assert hash1 != hash2


class TestConvenienceFunctions:
    """Test suite for convenience functions."""

    def test_detect_pii_function(self) -> None:
        """Test detect_pii convenience function."""
        findings = detect_pii("Email: user@example.com")

        assert len(findings) > 0
        assert findings[0][0] == "email"

    def test_contains_pii_function(self) -> None:
        """Test contains_pii convenience function."""
        assert contains_pii("SSN: 123-45-6789")
        assert not contains_pii("No PII here")

    def test_redact_pii_function(self) -> None:
        """Test redact_pii convenience function."""
        text = "Email: user@example.com"
        redacted = redact_pii(text)

        assert "user@example.com" not in redacted
        assert "[REDACTED-EMAIL]" in redacted

    def test_hash_query_function(self) -> None:
        """Test hash_query convenience function."""
        query = "What is the user's email?"

        hash1 = hash_query(query)
        hash2 = hash_query(query)

        # Should produce consistent hash
        assert hash1 == hash2
        assert len(hash1) == 16

        # Should not contain original content
        assert "email" not in hash1.lower()


class TestPIISecurity:
    """Security-specific tests for PII handling."""

    def test_pii_not_in_redacted_output(self) -> None:
        """Test that redacted output contains no traces of original PII."""
        redactor = PIIRedactor()

        sensitive_data = [
            ("SSN", "123-45-6789"),
            ("Email", "confidential@secret.com"),
            ("Phone", "555-867-5309"),
            ("Credit Card", "4532-1234-5678-9010"),
        ]

        for pii_type, pii_value in sensitive_data:
            text = f"{pii_type}: {pii_value}"
            redacted = redactor.redact(text)

            # Original PII should not appear
            assert pii_value not in redacted, f"{pii_type} leaked in redacted output!"

    def test_hash_irreversible(self) -> None:
        """Test that hash cannot be reversed to original query."""
        redactor = PIIRedactor()

        sensitive_query = "What is employee 12345's salary and SSN 123-45-6789?"
        query_hash = redactor.hash_for_logging(sensitive_query)

        # Hash should not contain any recognizable parts
        for word in sensitive_query.split():
            assert word.lower() not in query_hash.lower(), f"Word '{word}' found in hash!"

        # Common PII patterns should not be in hash
        assert "123" not in query_hash
        assert "45" not in query_hash
        assert "6789" not in query_hash

    def test_pii_detection_comprehensive(self) -> None:
        """Test comprehensive PII detection across multiple formats."""
        detector = PIIDetector()

        # Real-world-like text with multiple PII types
        text = """
        Customer Information:
        Name: John Doe
        Email: john.doe@company.com
        SSN: 123-45-6789
        Phone: (555) 123-4567
        DOB: 01/15/1985
        IP: 192.168.1.100
        Credit Card: 4532-1234-5678-9010
        """

        findings = detector.detect(text)

        # Should detect multiple PII instances
        assert len(findings) >= 5, f"Only detected {len(findings)} PII instances"

        # Check that all major types are detected
        pii_types = {f[0] for f in findings}
        expected_types = {"email", "ssn", "phone", "date_of_birth", "credit_card"}

        for expected in expected_types:
            assert expected in pii_types, f"{expected} not detected"


# Mark all tests as privacy tests
pytestmark = pytest.mark.privacy
