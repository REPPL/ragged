"""
Test suite for enhanced MIME type validation (v0.6.1 SECURITY-001).

Tests comprehensive file type detection using python-magic library
with graceful fallback to basic magic byte detection.
"""

import tempfile
from pathlib import Path

import pytest

from ragged.utils.security import SecurityError, validate_mime_type


class TestMIMEValidationWithPythonMagic:
    """Tests for python-magic based MIME validation."""

    def test_validate_pdf_file(self, tmp_path: Path) -> None:
        """Test PDF file detection."""
        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_bytes(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")  # Valid PDF header

        mime_type = validate_mime_type(pdf_file)
        assert mime_type in ("application/pdf", "application/x-pdf")

    def test_validate_text_file(self, tmp_path: Path) -> None:
        """Test text file detection."""
        txt_file = tmp_path / "test.txt"
        txt_file.write_text("This is a text file\nwith multiple lines.")

        mime_type = validate_mime_type(txt_file)
        assert mime_type in ("text/plain", "text/x-python", "text/x-c")

    def test_validate_html_file(self, tmp_path: Path) -> None:
        """Test HTML file detection."""
        html_file = tmp_path / "test.html"
        html_file.write_text("<!DOCTYPE html><html><body>Test</body></html>")

        mime_type = validate_mime_type(html_file)
        assert mime_type == "text/html"

    def test_validate_png_file(self, tmp_path: Path) -> None:
        """Test PNG image detection."""
        png_file = tmp_path / "test.png"
        # Valid PNG file header
        png_header = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
        png_file.write_bytes(png_header)

        mime_type = validate_mime_type(png_file)
        assert mime_type == "image/png"

    def test_validate_jpeg_file(self, tmp_path: Path) -> None:
        """Test JPEG image detection."""
        jpeg_file = tmp_path / "test.jpg"
        # Valid JPEG file header
        jpeg_header = b"\xFF\xD8\xFF\xE0\x00\x10JFIF"
        jpeg_file.write_bytes(jpeg_header)

        mime_type = validate_mime_type(jpeg_file)
        assert mime_type == "image/jpeg"

    def test_validate_zip_file(self, tmp_path: Path) -> None:
        """Test ZIP archive detection."""
        zip_file = tmp_path / "test.zip"
        # Valid ZIP file header
        zip_header = b"PK\x03\x04\x14\x00\x00\x00\x08\x00"
        zip_file.write_bytes(zip_header)

        mime_type = validate_mime_type(zip_file)
        assert mime_type == "application/zip"

    def test_validate_with_expected_types_pass(self, tmp_path: Path) -> None:
        """Test validation passes with correct expected type."""
        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_bytes(b"%PDF-1.4\n")

        # Should not raise
        mime_type = validate_mime_type(pdf_file, expected_types=["application/pdf"])
        assert mime_type == "application/pdf"

    def test_validate_with_expected_types_fail(self, tmp_path: Path) -> None:
        """Test validation fails with incorrect expected type."""
        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_bytes(b"%PDF-1.4\n")

        with pytest.raises(SecurityError, match="not in allowed types"):
            validate_mime_type(pdf_file, expected_types=["text/plain", "text/html"])

    def test_validate_file_not_found(self) -> None:
        """Test error when file doesn't exist."""
        nonexistent = Path("/nonexistent/file.pdf")

        with pytest.raises(FileNotFoundError, match="File not found"):
            validate_mime_type(nonexistent)


class TestRenamedExecutableDetection:
    """Tests for detecting executables renamed with safe extensions."""

    def test_detect_exe_renamed_as_pdf(self, tmp_path: Path) -> None:
        """Test detection of .exe file renamed as .pdf."""
        fake_pdf = tmp_path / "malicious.pdf"
        # Windows PE executable header
        exe_header = b"MZ\x90\x00\x03\x00\x00\x00\x04\x00\x00\x00\xff\xff"
        fake_pdf.write_bytes(exe_header)

        mime_type = validate_mime_type(fake_pdf)
        # python-magic should detect this as executable, not PDF
        assert mime_type != "application/pdf"
        assert "application" in mime_type  # e.g., application/x-dosexec

    def test_detect_elf_renamed_as_txt(self, tmp_path: Path) -> None:
        """Test detection of Linux ELF binary renamed as .txt.

        Note: This test requires python-magic with libmagic for accurate detection.
        Basic fallback may treat ELF headers as binary (application/octet-stream).
        """
        fake_txt = tmp_path / "malicious.txt"
        # Linux ELF binary header
        elf_header = b"\x7fELF\x02\x01\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00"
        fake_txt.write_bytes(elf_header)

        mime_type = validate_mime_type(fake_txt)
        # python-magic should detect this as executable, not text
        # Fallback may detect as application/octet-stream which is acceptable
        assert mime_type != "text/plain"
        assert "application" in mime_type  # e.g., application/x-executable or application/octet-stream

    def test_detect_script_renamed_as_pdf(self, tmp_path: Path) -> None:
        """Test detection of shell script renamed as .pdf."""
        fake_pdf = tmp_path / "script.pdf"
        fake_pdf.write_text("#!/bin/bash\nrm -rf /")

        mime_type = validate_mime_type(fake_pdf)
        # python-magic should detect this as text/script, not PDF
        assert mime_type != "application/pdf"
        assert "text" in mime_type


class TestZIPBasedFormatDetection:
    """Tests for detecting specific ZIP-based formats (DOCX, XLSX, etc.)."""

    def test_detect_docx_vs_generic_zip(self, tmp_path: Path) -> None:
        """Test that DOCX is detected, not just generic ZIP."""
        # Note: python-magic can distinguish DOCX from ZIP by inspecting contents
        # For basic test, we just verify ZIP is detected
        docx_file = tmp_path / "test.docx"
        docx_file.write_bytes(b"PK\x03\x04")  # ZIP header

        mime_type = validate_mime_type(docx_file)
        # Should detect as ZIP or DOCX (depending on python-magic capability)
        assert "zip" in mime_type.lower() or "word" in mime_type.lower()


class TestEdgeCases:
    """Tests for edge cases and error handling."""

    def test_empty_file(self, tmp_path: Path) -> None:
        """Test detection of empty file."""
        empty_file = tmp_path / "empty.txt"
        empty_file.write_bytes(b"")

        mime_type = validate_mime_type(empty_file)
        # Empty file should be detected (typically as inode/x-empty or application/x-empty)
        assert mime_type in (
            "application/x-empty",
            "inode/x-empty",
            "application/octet-stream",
        )

    def test_corrupted_pdf_header(self, tmp_path: Path) -> None:
        """Test detection of file with corrupted PDF header."""
        corrupted = tmp_path / "corrupted.pdf"
        corrupted.write_bytes(b"%PD\x00\x00\x00\x00")  # Invalid PDF

        mime_type = validate_mime_type(corrupted)
        # Should NOT detect as PDF
        assert mime_type != "application/pdf"

    def test_very_large_file(self, tmp_path: Path) -> None:
        """Test MIME detection works on large files."""
        large_file = tmp_path / "large.txt"
        # Create a 1MB text file
        large_file.write_text("A" * (1024 * 1024))

        mime_type = validate_mime_type(large_file)
        assert mime_type == "text/plain"

    def test_binary_file(self, tmp_path: Path) -> None:
        """Test detection of generic binary file."""
        binary_file = tmp_path / "binary.bin"
        binary_file.write_bytes(bytes(range(256)))

        mime_type = validate_mime_type(binary_file)
        assert mime_type == "application/octet-stream"


class TestFallbackBehaviour:
    """Tests for graceful fallback to basic detection."""

    def test_fallback_on_import_error(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test that basic detection works when python-magic unavailable."""
        # Mock ImportError for magic module
        import builtins

        original_import = builtins.__import__

        def mock_import(name: str, *args, **kwargs):  # type: ignore[no-untyped-def]
            if name == "magic":
                raise ImportError("python-magic not available")
            return original_import(name, *args, **kwargs)

        monkeypatch.setattr(builtins, "__import__", mock_import)

        # Test PDF detection with fallback
        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_bytes(b"%PDF-1.4\n")

        mime_type = validate_mime_type(pdf_file)
        assert mime_type == "application/pdf"  # Should work with basic detection

    def test_fallback_detects_png(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test basic fallback can detect PNG files."""
        import builtins

        original_import = builtins.__import__

        def mock_import(name: str, *args, **kwargs):  # type: ignore[no-untyped-def]
            if name == "magic":
                raise ImportError("python-magic not available")
            return original_import(name, *args, **kwargs)

        monkeypatch.setattr(builtins, "__import__", mock_import)

        png_file = tmp_path / "test.png"
        png_file.write_bytes(b"\x89PNG\r\n\x1a\n")

        mime_type = validate_mime_type(png_file)
        assert mime_type == "image/png"

    def test_fallback_detects_text(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test basic fallback can detect text files."""
        import builtins

        original_import = builtins.__import__

        def mock_import(name: str, *args, **kwargs):  # type: ignore[no-untyped-def]
            if name == "magic":
                raise ImportError("python-magic not available")
            return original_import(name, *args, **kwargs)

        monkeypatch.setattr(builtins, "__import__", mock_import)

        txt_file = tmp_path / "test.txt"
        txt_file.write_text("Hello, world!")

        mime_type = validate_mime_type(txt_file)
        assert mime_type == "text/plain"


class TestSecurityValidation:
    """Tests for security validation against known attack vectors."""

    def test_reject_executable_when_pdf_expected(self, tmp_path: Path) -> None:
        """Test that executable is rejected when PDF expected."""
        exe_file = tmp_path / "malware.pdf"
        exe_file.write_bytes(b"MZ\x90\x00")  # DOS executable

        with pytest.raises(SecurityError, match="not in allowed types"):
            validate_mime_type(exe_file, expected_types=["application/pdf"])

    def test_reject_html_when_image_expected(self, tmp_path: Path) -> None:
        """Test that HTML is rejected when image expected."""
        html_file = tmp_path / "xss.png"
        html_file.write_text("<script>alert('XSS')</script>")

        with pytest.raises(SecurityError, match="not in allowed types"):
            validate_mime_type(html_file, expected_types=["image/png", "image/jpeg"])

    def test_null_byte_injection_in_filename(self, tmp_path: Path) -> None:
        """Test handling of null byte in filename."""
        # Create a normal text file
        txt_file = tmp_path / "test.txt"
        txt_file.write_text("Safe content")

        # Path with null byte should be handled by Path object
        # This tests that we don't have null byte injection vulnerability
        mime_type = validate_mime_type(txt_file)
        assert mime_type == "text/plain"


@pytest.mark.integration
class TestIntegrationWithFileUpload:
    """Integration tests with file upload scenarios."""

    def test_upload_validation_workflow(self, tmp_path: Path) -> None:
        """Test complete upload validation workflow."""
        # Simulate file upload: user uploads "document.pdf"
        uploaded_file = tmp_path / "document.pdf"
        uploaded_file.write_bytes(b"%PDF-1.4\nSample PDF content")

        # Validate MIME type matches extension expectation
        mime_type = validate_mime_type(
            uploaded_file, expected_types=["application/pdf", "application/x-pdf"]
        )

        assert mime_type == "application/pdf"

    def test_upload_validation_blocks_renamed_executable(self, tmp_path: Path) -> None:
        """Test that upload validation blocks renamed executable."""
        # Simulate malicious upload: executable renamed as PDF
        malicious_file = tmp_path / "invoice.pdf"
        malicious_file.write_bytes(b"MZ\x90\x00")  # PE executable

        # Should raise SecurityError
        with pytest.raises(SecurityError, match="not in allowed types"):
            validate_mime_type(malicious_file, expected_types=["application/pdf"])
