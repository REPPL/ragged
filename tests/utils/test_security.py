"""Tests for security utilities.

v0.2.9: Comprehensive tests for security validation functions.
"""

import pytest
import tempfile
from pathlib import Path
from unittest.mock import patch, Mock

from src.utils.security import (
    SecurityError,
    validate_file_path,
    validate_file_size,
    validate_mime_type,
    sanitize_filename,
    is_safe_content,
)


@pytest.fixture
def temp_dir():
    """Create temporary directory for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def temp_file(temp_dir):
    """Create temporary file for testing."""
    file_path = temp_dir / "test.txt"
    file_path.write_text("test content")
    return file_path


@pytest.fixture
def temp_pdf(temp_dir):
    """Create temporary PDF file for testing."""
    file_path = temp_dir / "test.pdf"
    # Write PDF magic bytes
    file_path.write_bytes(b"%PDF-1.4\ntest pdf content")
    return file_path


class TestValidateFilePath:
    """Tests for validate_file_path function."""

    def test_valid_file_path(self, temp_file):
        """Test validating a valid file path."""
        result = validate_file_path(temp_file)
        assert result == temp_file.resolve()
        assert result.is_absolute()

    def test_nonexistent_file(self, temp_dir):
        """Test validation fails for nonexistent file."""
        nonexistent = temp_dir / "nonexistent.txt"
        with pytest.raises(FileNotFoundError):
            validate_file_path(nonexistent)

    def test_directory_not_file(self, temp_dir):
        """Test validation fails for directory."""
        with pytest.raises(SecurityError, match="not a regular file"):
            validate_file_path(temp_dir)

    def test_path_within_allowed_base(self, temp_file, temp_dir):
        """Test validation succeeds when path is within allowed base."""
        result = validate_file_path(temp_file, allowed_base=temp_dir)
        assert result == temp_file.resolve()

    def test_path_outside_allowed_base(self, temp_file, temp_dir):
        """Test validation fails when path is outside allowed base."""
        other_dir = temp_dir.parent / "other"
        with pytest.raises(SecurityError, match="outside allowed directory"):
            validate_file_path(temp_file, allowed_base=other_dir)

    def test_relative_path_resolved(self, temp_file):
        """Test that relative paths are resolved to absolute."""
        # Use relative path
        relative = Path(temp_file.name)
        with pytest.raises(FileNotFoundError):  # Won't exist from current dir
            validate_file_path(relative)

    def test_symlink_to_file(self, temp_file, temp_dir):
        """Test symlink to file is treated as file."""
        symlink = temp_dir / "symlink.txt"
        symlink.symlink_to(temp_file)

        result = validate_file_path(symlink)
        # Should resolve to target
        assert result.resolve() == temp_file.resolve()

    def test_symlink_to_directory(self, temp_dir):
        """Test symlink to directory fails."""
        subdir = temp_dir / "subdir"
        subdir.mkdir()
        symlink = temp_dir / "dirlink"
        symlink.symlink_to(subdir)

        with pytest.raises(SecurityError, match="not a regular file"):
            validate_file_path(symlink)


class TestValidateFileSize:
    """Tests for validate_file_size function."""

    def test_file_within_size_limit(self, temp_file):
        """Test file within size limit."""
        size = validate_file_size(temp_file, max_size_mb=1)
        assert size == len(b"test content")
        assert size > 0

    def test_file_exceeds_size_limit(self, temp_dir):
        """Test file exceeding size limit."""
        large_file = temp_dir / "large.txt"
        large_file.write_bytes(b"a" * (2 * 1024 * 1024))  # 2 MB

        with pytest.raises(SecurityError, match="exceeds maximum allowed size"):
            validate_file_size(large_file, max_size_mb=1)

    def test_file_exactly_at_limit(self, temp_dir):
        """Test file exactly at size limit."""
        file_path = temp_dir / "exact.txt"
        file_path.write_bytes(b"a" * (1024 * 1024))  # Exactly 1 MB

        size = validate_file_size(file_path, max_size_mb=1)
        assert size == 1024 * 1024

    def test_nonexistent_file(self, temp_dir):
        """Test validation fails for nonexistent file."""
        nonexistent = temp_dir / "nonexistent.txt"
        with pytest.raises(FileNotFoundError):
            validate_file_size(nonexistent, max_size_mb=1)

    def test_default_max_size_from_config(self, temp_file):
        """Test using default max size from config."""
        with patch("src.utils.security.get_settings") as mock_settings:
            mock_settings.return_value = Mock(max_file_size_mb=10)
            size = validate_file_size(temp_file)
            assert size > 0

    def test_empty_file(self, temp_dir):
        """Test empty file validation."""
        empty_file = temp_dir / "empty.txt"
        empty_file.touch()

        size = validate_file_size(empty_file, max_size_mb=1)
        assert size == 0

    def test_very_large_limit(self, temp_file):
        """Test file with very large limit."""
        size = validate_file_size(temp_file, max_size_mb=10000)
        assert size > 0


class TestValidateMimeType:
    """Tests for validate_mime_type function."""

    def test_detect_pdf(self, temp_pdf):
        """Test PDF detection."""
        mime_type = validate_mime_type(temp_pdf)
        assert mime_type == "application/pdf"

    def test_detect_text_file(self, temp_file):
        """Test text file detection."""
        mime_type = validate_mime_type(temp_file)
        assert mime_type == "text/plain"

    def test_detect_png(self, temp_dir):
        """Test PNG detection."""
        png_file = temp_dir / "test.png"
        png_file.write_bytes(b"\x89PNG\r\n\x1a\n" + b"fake png data")
        mime_type = validate_mime_type(png_file)
        assert mime_type == "image/png"

    def test_detect_jpeg(self, temp_dir):
        """Test JPEG detection."""
        jpeg_file = temp_dir / "test.jpg"
        jpeg_file.write_bytes(b"\xFF\xD8\xFF" + b"fake jpeg data")
        mime_type = validate_mime_type(jpeg_file)
        assert mime_type == "image/jpeg"

    def test_detect_html(self, temp_dir):
        """Test HTML detection."""
        html_file = temp_dir / "test.html"
        html_file.write_text("<!DOCTYPE html><html></html>")
        mime_type = validate_mime_type(html_file)
        assert mime_type == "text/html"

    def test_detect_zip(self, temp_dir):
        """Test ZIP detection."""
        zip_file = temp_dir / "test.zip"
        zip_file.write_bytes(b"PK\x03\x04" + b"fake zip data")
        mime_type = validate_mime_type(zip_file)
        assert mime_type == "application/zip"

    def test_validate_expected_type_match(self, temp_pdf):
        """Test validation succeeds when type matches."""
        mime_type = validate_mime_type(temp_pdf, expected_types=["application/pdf"])
        assert mime_type == "application/pdf"

    def test_validate_expected_type_mismatch(self, temp_file):
        """Test validation fails when type doesn't match."""
        with pytest.raises(SecurityError, match="not in allowed types"):
            validate_mime_type(temp_file, expected_types=["application/pdf"])

    def test_validate_multiple_expected_types(self, temp_file):
        """Test validation with multiple allowed types."""
        mime_type = validate_mime_type(
            temp_file,
            expected_types=["text/plain", "application/pdf", "text/html"]
        )
        assert mime_type == "text/plain"

    def test_nonexistent_file(self, temp_dir):
        """Test validation fails for nonexistent file."""
        nonexistent = temp_dir / "nonexistent.txt"
        with pytest.raises(FileNotFoundError):
            validate_mime_type(nonexistent)

    def test_binary_file_not_text(self, temp_dir):
        """Test binary file not detected as text."""
        binary_file = temp_dir / "binary.bin"
        binary_file.write_bytes(b"\x00\x01\x02\xFF\xFE")
        mime_type = validate_mime_type(binary_file)
        assert mime_type == "application/octet-stream"

    def test_unicode_text_file(self, temp_dir):
        """Test unicode text file detection."""
        text_file = temp_dir / "unicode.txt"
        text_file.write_text("Hello 世界 🌍", encoding="utf-8")
        mime_type = validate_mime_type(text_file)
        assert mime_type == "text/plain"

    def test_empty_file(self, temp_dir):
        """Test empty file detection."""
        empty_file = temp_dir / "empty.txt"
        empty_file.touch()
        mime_type = validate_mime_type(empty_file)
        # Empty file should default to octet-stream
        assert mime_type == "application/octet-stream"


class TestSanitizeFilename:
    """Tests for sanitize_filename function."""

    def test_simple_filename(self):
        """Test sanitizing simple filename."""
        result = sanitize_filename("test.txt")
        assert result == "test.txt"

    def test_remove_path_traversal(self):
        """Test removing path traversal attempts."""
        result = sanitize_filename("../../../etc/passwd")
        assert ".." not in result
        assert "/" not in result
        assert result == "etcpasswd"

    def test_remove_directory_separators(self):
        """Test removing directory separators."""
        result = sanitize_filename("path/to/file.txt")
        assert "/" not in result
        assert "\\" not in result

    def test_remove_null_bytes(self):
        """Test removing null bytes."""
        result = sanitize_filename("file\x00name.txt")
        assert "\x00" not in result

    def test_remove_control_characters(self):
        """Test removing control characters."""
        result = sanitize_filename("file\x01\x02name.txt")
        assert result == "filename.txt"

    def test_truncate_long_filename(self):
        """Test truncating very long filenames."""
        long_name = "a" * 300 + ".txt"
        result = sanitize_filename(long_name, max_length=255)
        assert len(result) <= 255
        assert result.endswith(".txt")  # Preserve extension

    def test_preserve_extension_on_truncate(self):
        """Test extension is preserved when truncating."""
        long_name = "a" * 300 + ".pdf"
        result = sanitize_filename(long_name, max_length=100)
        assert len(result) <= 100
        assert result.endswith(".pdf")

    def test_empty_after_sanitization(self):
        """Test error when filename is empty after sanitization."""
        with pytest.raises(SecurityError, match="empty after sanitization"):
            sanitize_filename("../../")

    def test_unicode_filename(self):
        """Test unicode filename is preserved."""
        result = sanitize_filename("文档.txt")
        assert "文档" in result
        assert result.endswith(".txt")

    def test_spaces_preserved(self):
        """Test spaces in filename are preserved."""
        result = sanitize_filename("my document.txt")
        assert result == "my document.txt"

    def test_special_characters_preserved(self):
        """Test safe special characters are preserved."""
        result = sanitize_filename("file-name_2024.txt")
        assert result == "file-name_2024.txt"

    def test_windows_path_separator(self):
        """Test Windows path separators are removed."""
        result = sanitize_filename("C:\\Users\\file.txt")
        assert "\\" not in result
        assert result == "C:Usersfile.txt"

    def test_basename_extraction(self):
        """Test that only basename is used."""
        result = sanitize_filename("/path/to/file.txt")
        assert result == "file.txt"


class TestIsSafeContent:
    """Tests for is_safe_content function."""

    def test_safe_short_content(self):
        """Test short content is safe."""
        result = is_safe_content("short content")
        assert result is True

    def test_safe_medium_content(self):
        """Test medium-length content is safe."""
        content = "a" * 10000
        result = is_safe_content(content)
        assert result is True

    def test_safe_long_content(self):
        """Test long content within limit is safe."""
        content = "a" * 1_000_000
        result = is_safe_content(content, max_length=2_000_000)
        assert result is True

    def test_unsafe_exceeds_length(self):
        """Test content exceeding limit raises error."""
        content = "a" * 200
        with pytest.raises(SecurityError, match="exceeds maximum"):
            is_safe_content(content, max_length=100)

    def test_exactly_at_limit(self):
        """Test content exactly at limit is safe."""
        content = "a" * 1000
        result = is_safe_content(content, max_length=1000)
        assert result is True

    def test_empty_content(self):
        """Test empty content is safe."""
        result = is_safe_content("")
        assert result is True

    def test_unicode_content(self):
        """Test unicode content length is counted correctly."""
        content = "世界" * 1000
        result = is_safe_content(content, max_length=10000)
        assert result is True

    def test_default_max_length(self):
        """Test default max length is very large."""
        # Should allow very large content by default
        content = "a" * 1_000_000
        result = is_safe_content(content)  # Default is 100M
        assert result is True


class TestIntegrationScenarios:
    """Integration tests for realistic security scenarios."""

    def test_secure_file_upload_validation(self, temp_pdf, temp_dir):
        """Test complete file upload validation workflow."""
        # 1. Validate path
        validated_path = validate_file_path(temp_pdf, allowed_base=temp_dir)
        assert validated_path.exists()

        # 2. Validate size
        size = validate_file_size(validated_path, max_size_mb=10)
        assert size > 0

        # 3. Validate MIME type
        mime_type = validate_mime_type(validated_path, expected_types=["application/pdf"])
        assert mime_type == "application/pdf"

        # All validations passed
        assert True

    def test_reject_malicious_upload(self, temp_dir):
        """Test rejecting potentially malicious file."""
        # Create file with misleading extension
        malicious = temp_dir / "innocent.pdf"
        malicious.write_text("#!/bin/bash\nrm -rf /")  # Not actually a PDF

        # Validate path (OK)
        validated_path = validate_file_path(malicious)

        # But MIME type validation should fail
        with pytest.raises(SecurityError):
            validate_mime_type(validated_path, expected_types=["application/pdf"])

    def test_path_traversal_attack_prevention(self, temp_dir):
        """Test preventing path traversal attack."""
        # Attacker tries to access file outside allowed directory
        attack_path = temp_dir / ".." / ".." / "etc" / "passwd"

        # Create a decoy file (won't actually be /etc/passwd)
        parent_dir = temp_dir.parent
        etc_dir = parent_dir / "etc"
        etc_dir.mkdir(exist_ok=True)
        passwd_file = etc_dir / "passwd"
        passwd_file.write_text("fake passwd file")

        try:
            # Validation should fail
            with pytest.raises(SecurityError, match="outside allowed directory"):
                validate_file_path(attack_path.resolve(), allowed_base=temp_dir)
        finally:
            # Cleanup
            if passwd_file.exists():
                passwd_file.unlink()
            if etc_dir.exists():
                etc_dir.rmdir()

    def test_filename_sanitization_workflow(self):
        """Test complete filename sanitization workflow."""
        dangerous_filenames = [
            "../../../etc/passwd",
            "file\x00name.txt",
            "very" * 100 + ".pdf",  # Very long
            "path/to/file.txt",
        ]

        for dangerous in dangerous_filenames:
            safe = sanitize_filename(dangerous)

            # Safe filename should have no path components
            assert "/" not in safe
            assert "\\" not in safe
            assert ".." not in safe

            # Should not be empty
            assert len(safe) > 0

            # Should be within length limit
            assert len(safe) <= 255

    def test_content_size_limits(self):
        """Test enforcing content size limits."""
        # Simulate processing user-uploaded content
        small_content = "small"
        medium_content = "a" * 10000
        huge_content = "a" * 200_000_000  # 200 MB

        # Small and medium should be fine
        assert is_safe_content(small_content, max_length=100_000_000)
        assert is_safe_content(medium_content, max_length=100_000_000)

        # Huge content should be rejected
        with pytest.raises(SecurityError):
            is_safe_content(huge_content, max_length=100_000_000)

    def test_defense_in_depth(self, temp_dir):
        """Test multiple layers of security validation."""
        # Create suspicious file
        suspicious = temp_dir / "script.pdf"  # Claims to be PDF
        suspicious.write_text("#!/bin/bash\nmalicious code")

        # Layer 1: Path validation (passes - file exists)
        validated_path = validate_file_path(suspicious, allowed_base=temp_dir)

        # Layer 2: Size validation (passes - small file)
        size = validate_file_size(validated_path, max_size_mb=1)

        # Layer 3: MIME type validation (FAILS - not a PDF)
        with pytest.raises(SecurityError):
            validate_mime_type(validated_path, expected_types=["application/pdf"])

        # Defense in depth caught the attack at layer 3
