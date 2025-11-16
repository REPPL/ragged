"""Tests for document scanner."""

import pytest
from pathlib import Path
from src.ingestion.scanner import DocumentScanner, SUPPORTED_EXTENSIONS, DEFAULT_IGNORE_PATTERNS


class TestDocumentScannerInit:
    """Tests for DocumentScanner initialization."""

    def test_default_initialization(self):
        """Test scanner with default parameters."""
        scanner = DocumentScanner()

        assert scanner.follow_symlinks is False
        assert scanner.max_depth is None
        assert scanner.ignore_patterns == DEFAULT_IGNORE_PATTERNS

    def test_custom_initialization(self):
        """Test scanner with custom parameters."""
        custom_patterns = {"*.tmp", "test_*"}
        scanner = DocumentScanner(
            follow_symlinks=True,
            max_depth=2,
            ignore_patterns=custom_patterns
        )

        assert scanner.follow_symlinks is True
        assert scanner.max_depth == 2
        assert scanner.ignore_patterns == custom_patterns


class TestSingleFileScanning:
    """Tests for scanning single files."""

    def test_scan_supported_file(self, temp_dir):
        """Test scanning a supported file type."""
        # Create a supported file
        pdf_file = temp_dir / "document.pdf"
        pdf_file.write_text("PDF content")

        scanner = DocumentScanner()
        results = scanner.scan(pdf_file)

        assert len(results) == 1
        assert results[0] == pdf_file.resolve()

    def test_scan_supported_txt_file(self, sample_txt_path):
        """Test scanning a TXT file."""
        scanner = DocumentScanner()
        results = scanner.scan(sample_txt_path)

        assert len(results) == 1
        assert results[0] == sample_txt_path.resolve()

    def test_scan_supported_md_file(self, sample_md_path):
        """Test scanning a Markdown file."""
        scanner = DocumentScanner()
        results = scanner.scan(sample_md_path)

        assert len(results) == 1
        assert results[0] == sample_md_path.resolve()

    def test_scan_unsupported_file(self, temp_dir):
        """Test scanning an unsupported file type."""
        unsupported_file = temp_dir / "document.xyz"
        unsupported_file.write_text("Unsupported content")

        scanner = DocumentScanner()
        results = scanner.scan(unsupported_file)

        assert len(results) == 0

    def test_scan_all_supported_extensions(self, temp_dir):
        """Test that all supported extensions are recognized."""
        scanner = DocumentScanner()

        for ext in SUPPORTED_EXTENSIONS:
            test_file = temp_dir / f"test{ext}"
            test_file.write_text("content")
            results = scanner.scan(test_file)
            assert len(results) == 1, f"Extension {ext} should be supported"
            test_file.unlink()  # Clean up

    def test_scan_nonexistent_file(self, temp_dir):
        """Test scanning a non-existent file."""
        nonexistent = temp_dir / "nonexistent.pdf"

        scanner = DocumentScanner()
        with pytest.raises(ValueError, match="not a file or directory"):
            scanner.scan(nonexistent)


class TestDirectoryScanning:
    """Tests for scanning directories."""

    def test_scan_empty_directory(self, temp_dir):
        """Test scanning an empty directory."""
        scanner = DocumentScanner()
        results = scanner.scan(temp_dir)

        assert results == []

    def test_scan_directory_with_single_file(self, temp_dir):
        """Test scanning directory with one supported file."""
        doc = temp_dir / "document.pdf"
        doc.write_text("PDF content")

        scanner = DocumentScanner()
        results = scanner.scan(temp_dir)

        assert len(results) == 1
        assert results[0] == doc.resolve()

    def test_scan_directory_with_multiple_files(self, temp_dir):
        """Test scanning directory with multiple supported files."""
        # Create multiple files
        pdf1 = temp_dir / "doc1.pdf"
        pdf2 = temp_dir / "doc2.pdf"
        txt1 = temp_dir / "doc3.txt"
        md1 = temp_dir / "doc4.md"

        for f in [pdf1, pdf2, txt1, md1]:
            f.write_text("content")

        scanner = DocumentScanner()
        results = scanner.scan(temp_dir)

        assert len(results) == 4
        assert pdf1.resolve() in results
        assert pdf2.resolve() in results
        assert txt1.resolve() in results
        assert md1.resolve() in results

    def test_scan_directory_mixed_files(self, temp_dir):
        """Test scanning directory with supported and unsupported files."""
        # Supported
        pdf = temp_dir / "doc.pdf"
        txt = temp_dir / "doc.txt"

        # Unsupported
        exe = temp_dir / "app.exe"
        img = temp_dir / "image.jpg"

        for f in [pdf, txt, exe, img]:
            f.write_text("content")

        scanner = DocumentScanner()
        results = scanner.scan(temp_dir)

        assert len(results) == 2
        assert pdf.resolve() in results
        assert txt.resolve() in results
        assert exe.resolve() not in results
        assert img.resolve() not in results

    def test_scan_results_sorted(self, temp_dir):
        """Test that scan results are returned in sorted order."""
        # Create files in non-alphabetical order
        files = ["zebra.txt", "apple.md", "monkey.pdf", "banana.html"]
        for fname in files:
            (temp_dir / fname).write_text("content")

        scanner = DocumentScanner()
        results = scanner.scan(temp_dir)

        # Results should be sorted alphabetically
        result_names = [r.name for r in results]
        assert result_names == sorted(result_names)


class TestRecursiveScanning:
    """Tests for recursive directory scanning."""

    def test_scan_nested_directories(self, temp_dir):
        """Test scanning nested directory structure."""
        # Create nested structure
        (temp_dir / "level1").mkdir()
        (temp_dir / "level1" / "level2").mkdir()
        (temp_dir / "level1" / "level2" / "level3").mkdir()

        # Add files at each level
        doc1 = temp_dir / "doc1.pdf"
        doc2 = temp_dir / "level1" / "doc2.txt"
        doc3 = temp_dir / "level1" / "level2" / "doc3.md"
        doc4 = temp_dir / "level1" / "level2" / "level3" / "doc4.html"

        for doc in [doc1, doc2, doc3, doc4]:
            doc.write_text("content")

        scanner = DocumentScanner()
        results = scanner.scan(temp_dir)

        assert len(results) == 4
        assert doc1.resolve() in results
        assert doc2.resolve() in results
        assert doc3.resolve() in results
        assert doc4.resolve() in results

    def test_scan_max_depth_0(self, temp_dir):
        """Test scanning with max depth of 0 (only root directory)."""
        # Create nested structure
        (temp_dir / "subdir").mkdir()

        root_doc = temp_dir / "root.pdf"
        sub_doc = temp_dir / "subdir" / "sub.pdf"

        root_doc.write_text("content")
        sub_doc.write_text("content")

        scanner = DocumentScanner(max_depth=0)
        results = scanner.scan(temp_dir)

        # Should only find root file
        assert len(results) == 1
        assert root_doc.resolve() in results
        assert sub_doc.resolve() not in results

    def test_scan_max_depth_1(self, temp_dir):
        """Test scanning with max depth of 1."""
        # Create nested structure
        (temp_dir / "level1").mkdir()
        (temp_dir / "level1" / "level2").mkdir()

        doc0 = temp_dir / "doc0.pdf"
        doc1 = temp_dir / "level1" / "doc1.pdf"
        doc2 = temp_dir / "level1" / "level2" / "doc2.pdf"

        for doc in [doc0, doc1, doc2]:
            doc.write_text("content")

        scanner = DocumentScanner(max_depth=1)
        results = scanner.scan(temp_dir)

        # Should find doc0 and doc1, but not doc2
        assert len(results) == 2
        assert doc0.resolve() in results
        assert doc1.resolve() in results
        assert doc2.resolve() not in results

    def test_scan_multiple_subdirectories(self, temp_dir):
        """Test scanning directory with multiple subdirectories."""
        # Create parallel directories
        (temp_dir / "dir_a").mkdir()
        (temp_dir / "dir_b").mkdir()
        (temp_dir / "dir_c").mkdir()

        # Add files to each
        doc_a = temp_dir / "dir_a" / "doc.pdf"
        doc_b = temp_dir / "dir_b" / "doc.txt"
        doc_c = temp_dir / "dir_c" / "doc.md"

        for doc in [doc_a, doc_b, doc_c]:
            doc.write_text("content")

        scanner = DocumentScanner()
        results = scanner.scan(temp_dir)

        assert len(results) == 3
        assert doc_a.resolve() in results
        assert doc_b.resolve() in results
        assert doc_c.resolve() in results


class TestSymlinkHandling:
    """Tests for symlink handling."""

    def test_scan_symlink_file_not_followed(self, temp_dir):
        """Test that symlinked files are not followed by default."""
        # Create real file
        real_file = temp_dir / "real.pdf"
        real_file.write_text("content")

        # Create symlink
        symlink = temp_dir / "link.pdf"
        try:
            symlink.symlink_to(real_file)
        except OSError:
            pytest.skip("Symlinks not supported on this system")

        scanner = DocumentScanner(follow_symlinks=False)
        results = scanner.scan(temp_dir)

        # Should only find the real file, not the symlink
        assert len(results) == 1
        assert real_file.resolve() in results

    def test_scan_symlink_file_followed(self, temp_dir):
        """Test that symlinked files are followed when enabled."""
        # Create real file
        real_file = temp_dir / "real.pdf"
        real_file.write_text("content")

        # Create symlink in different location
        symlink_dir = temp_dir / "links"
        symlink_dir.mkdir()
        symlink = symlink_dir / "link.pdf"

        try:
            symlink.symlink_to(real_file)
        except OSError:
            pytest.skip("Symlinks not supported on this system")

        scanner = DocumentScanner(follow_symlinks=True)
        results = scanner.scan(temp_dir)

        # Should find both real file and symlink
        assert len(results) == 2

    def test_scan_symlink_directory_not_followed(self, temp_dir):
        """Test that symlinked directories are not followed by default."""
        # Create real directory with file
        real_dir = temp_dir / "real_dir"
        real_dir.mkdir()
        real_file = real_dir / "doc.pdf"
        real_file.write_text("content")

        # Create symlink to directory
        symlink_dir = temp_dir / "link_dir"
        try:
            symlink_dir.symlink_to(real_dir)
        except OSError:
            pytest.skip("Symlinks not supported on this system")

        scanner = DocumentScanner(follow_symlinks=False)
        results = scanner.scan(temp_dir)

        # Should only find file in real directory
        assert len(results) == 1

    def test_scan_symlink_directory_followed(self, temp_dir):
        """Test that symlinked directories are followed when enabled."""
        # Create real directory with file
        real_dir = temp_dir / "real_dir"
        real_dir.mkdir()
        real_file = real_dir / "doc.pdf"
        real_file.write_text("content")

        # Create symlink to directory
        symlink_dir = temp_dir / "link_dir"
        try:
            symlink_dir.symlink_to(real_dir)
        except OSError:
            pytest.skip("Symlinks not supported on this system")

        scanner = DocumentScanner(follow_symlinks=True)
        results = scanner.scan(temp_dir)

        # Should find file twice (once in real dir, once through symlink)
        assert len(results) == 2


class TestIgnorePatterns:
    """Tests for ignore patterns."""

    def test_scan_ignores_hidden_files_by_default(self, temp_dir):
        """Test that hidden files (starting with .) are ignored by default."""
        visible = temp_dir / "visible.pdf"
        hidden = temp_dir / ".hidden.pdf"

        visible.write_text("content")
        hidden.write_text("content")

        scanner = DocumentScanner()
        results = scanner.scan(temp_dir)

        assert len(results) == 1
        assert visible.resolve() in results
        assert hidden.resolve() not in results

    def test_scan_ignores_hidden_directories_by_default(self, temp_dir):
        """Test that hidden directories are ignored by default."""
        visible_dir = temp_dir / "visible"
        hidden_dir = temp_dir / ".hidden"

        visible_dir.mkdir()
        hidden_dir.mkdir()

        visible_doc = visible_dir / "doc.pdf"
        hidden_doc = hidden_dir / "doc.pdf"

        visible_doc.write_text("content")
        hidden_doc.write_text("content")

        scanner = DocumentScanner()
        results = scanner.scan(temp_dir)

        assert len(results) == 1
        assert visible_doc.resolve() in results
        assert hidden_doc.resolve() not in results

    def test_scan_custom_ignore_patterns(self, temp_dir):
        """Test custom ignore patterns."""
        # Create files matching custom pattern
        keep1 = temp_dir / "keep.pdf"
        keep2 = temp_dir / "document.txt"
        ignore1 = temp_dir / "temp_file.md"
        ignore2 = temp_dir / "test_doc.pdf"

        for f in [keep1, keep2, ignore1, ignore2]:
            f.write_text("content")

        # Custom patterns: ignore files starting with temp_ or test_
        custom_patterns = {"temp_*", "test_*"}
        scanner = DocumentScanner(ignore_patterns=custom_patterns)
        results = scanner.scan(temp_dir)

        assert len(results) == 2
        assert keep1.resolve() in results
        assert keep2.resolve() in results

    def test_scan_ignores_pycache_by_default(self, temp_dir):
        """Test that __pycache__ directories are ignored."""
        normal_dir = temp_dir / "normal"
        pycache_dir = temp_dir / "__pycache__"

        normal_dir.mkdir()
        pycache_dir.mkdir()

        normal_doc = normal_dir / "doc.pdf"
        pycache_doc = pycache_dir / "cached.pdf"

        normal_doc.write_text("content")
        pycache_doc.write_text("content")

        scanner = DocumentScanner()
        results = scanner.scan(temp_dir)

        assert len(results) == 1
        assert normal_doc.resolve() in results

    def test_scan_ignores_node_modules(self, temp_dir):
        """Test that node_modules directories are ignored."""
        normal_dir = temp_dir / "src"
        node_modules = temp_dir / "node_modules"

        normal_dir.mkdir()
        node_modules.mkdir()

        normal_doc = normal_dir / "doc.md"
        node_doc = node_modules / "readme.md"

        normal_doc.write_text("content")
        node_doc.write_text("content")

        scanner = DocumentScanner()
        results = scanner.scan(temp_dir)

        assert len(results) == 1
        assert normal_doc.resolve() in results

    def test_scan_ignores_git_directory(self, temp_dir):
        """Test that .git directories are ignored."""
        src_dir = temp_dir / "src"
        git_dir = temp_dir / ".git"

        src_dir.mkdir()
        git_dir.mkdir()

        src_doc = src_dir / "doc.txt"
        git_doc = git_dir / "config.txt"

        src_doc.write_text("content")
        git_doc.write_text("content")

        scanner = DocumentScanner()
        results = scanner.scan(temp_dir)

        assert len(results) == 1
        assert src_doc.resolve() in results


class TestEdgeCases:
    """Tests for edge cases and error handling."""

    def test_scan_directory_with_special_characters(self, temp_dir):
        """Test scanning directory with special characters in name."""
        special_dir = temp_dir / "dir with spaces & (parens)"
        special_dir.mkdir()

        doc = special_dir / "document.pdf"
        doc.write_text("content")

        scanner = DocumentScanner()
        results = scanner.scan(temp_dir)

        assert len(results) == 1
        assert doc.resolve() in results

    def test_scan_file_with_uppercase_extension(self, temp_dir):
        """Test that uppercase extensions are supported."""
        pdf_upper = temp_dir / "doc.PDF"
        txt_upper = temp_dir / "doc.TXT"

        pdf_upper.write_text("content")
        txt_upper.write_text("content")

        scanner = DocumentScanner()
        results = scanner.scan(temp_dir)

        assert len(results) == 2

    def test_scan_file_with_mixed_case_extension(self, temp_dir):
        """Test that mixed case extensions are supported."""
        mixed = temp_dir / "doc.Pdf"
        mixed.write_text("content")

        scanner = DocumentScanner()
        results = scanner.scan(temp_dir)

        assert len(results) == 1

    def test_scan_markdown_file_with_markdown_extension(self, temp_dir):
        """Test that .markdown extension is supported."""
        markdown = temp_dir / "doc.markdown"
        markdown.write_text("# Markdown")

        scanner = DocumentScanner()
        results = scanner.scan(temp_dir)

        assert len(results) == 1

    def test_scan_html_with_htm_extension(self, temp_dir):
        """Test that .htm extension is supported."""
        htm = temp_dir / "doc.htm"
        htm.write_text("<html></html>")

        scanner = DocumentScanner()
        results = scanner.scan(temp_dir)

        assert len(results) == 1

    def test_scan_returns_absolute_paths(self, temp_dir):
        """Test that scan returns absolute paths."""
        doc = temp_dir / "doc.pdf"
        doc.write_text("content")

        scanner = DocumentScanner()
        results = scanner.scan(doc)

        assert len(results) == 1
        assert results[0].is_absolute()

    def test_scan_empty_directory_returns_empty_list(self, temp_dir):
        """Test that scanning empty directory returns empty list."""
        empty_dir = temp_dir / "empty"
        empty_dir.mkdir()

        scanner = DocumentScanner()
        results = scanner.scan(empty_dir)

        assert results == []
        assert isinstance(results, list)

    def test_scan_deeply_nested_structure(self, temp_dir):
        """Test scanning a deeply nested directory structure."""
        # Create 10-level deep structure
        current_dir = temp_dir
        for i in range(10):
            current_dir = current_dir / f"level{i}"
            current_dir.mkdir()

        # Add file at deepest level
        deep_doc = current_dir / "deep.pdf"
        deep_doc.write_text("content")

        scanner = DocumentScanner()
        results = scanner.scan(temp_dir)

        assert len(results) == 1
        assert deep_doc.resolve() in results

    def test_scan_max_depth_none_unlimited(self, temp_dir):
        """Test that max_depth=None allows unlimited depth."""
        # Create deep structure
        current_dir = temp_dir
        for i in range(10):
            current_dir = current_dir / f"level{i}"
            current_dir.mkdir()
            doc = current_dir / f"doc{i}.pdf"
            doc.write_text("content")

        scanner = DocumentScanner(max_depth=None)
        results = scanner.scan(temp_dir)

        # Should find all 10 documents
        assert len(results) == 10


@pytest.mark.unit
class TestHelperMethods:
    """Tests for internal helper methods."""

    def test_is_supported_format_pdf(self, temp_dir):
        """Test _is_supported_format with PDF."""
        scanner = DocumentScanner()
        pdf_path = temp_dir / "doc.pdf"

        assert scanner._is_supported_format(pdf_path) is True

    def test_is_supported_format_unsupported(self, temp_dir):
        """Test _is_supported_format with unsupported extension."""
        scanner = DocumentScanner()
        exe_path = temp_dir / "app.exe"

        assert scanner._is_supported_format(exe_path) is False

    def test_should_ignore_hidden_file(self, temp_dir):
        """Test _should_ignore with hidden file."""
        scanner = DocumentScanner()
        hidden = temp_dir / ".hidden"

        assert scanner._should_ignore(hidden) is True

    def test_should_ignore_normal_file(self, temp_dir):
        """Test _should_ignore with normal file."""
        scanner = DocumentScanner()
        normal = temp_dir / "normal.pdf"

        assert scanner._should_ignore(normal) is False

    def test_should_ignore_custom_pattern(self, temp_dir):
        """Test _should_ignore with custom pattern."""
        scanner = DocumentScanner(ignore_patterns={"test_*"})
        test_file = temp_dir / "test_file.pdf"
        normal_file = temp_dir / "file.pdf"

        assert scanner._should_ignore(test_file) is True
        assert scanner._should_ignore(normal_file) is False
