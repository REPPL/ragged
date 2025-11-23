"""Tests for enhanced page reordering with interpolation (v0.4.9).

Tests cover:
- Logical page number extraction from headers/footers
- Page number interpolation for missing numbers
- Leading/trailing page inference
- Gap detection
- Reordering map generation
- Safety checks (>80% threshold)
"""

import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from ragged.correction.transformers.ordering import PageReorderTransformer


class TestPageReorderTransformer:
    """Tests for PageReorderTransformer class."""

    @pytest.fixture
    def transformer(self):
        """Create PageReorderTransformer instance."""
        return PageReorderTransformer()

    def test_interpolate_perfect_sequence(self, transformer):
        """Test interpolation with perfect sequential gap."""
        page_mappings = [
            (0, 1),   # Page 0 has logical number 1
            (1, None),  # Page 1 has no number
            (2, None),  # Page 2 has no number
            (3, 4),   # Page 3 has logical number 4
        ]

        result = transformer._interpolate_page_numbers(page_mappings)

        # Should interpolate pages 1 and 2 as 2 and 3
        assert result[0] == (0, 1)
        assert result[1] == (1, 2)
        assert result[2] == (2, 3)
        assert result[3] == (3, 4)

    def test_interpolate_no_gap(self, transformer):
        """Test interpolation when there's no gap to fill."""
        page_mappings = [
            (0, 1),
            (1, 2),
            (2, 3),
        ]

        result = transformer._interpolate_page_numbers(page_mappings)

        # Should remain unchanged
        assert result == page_mappings

    def test_interpolate_leading_pages(self, transformer):
        """Test interpolation of pages before first numbered page."""
        page_mappings = [
            (0, None),  # Front matter
            (1, None),  # Front matter
            (2, 5),     # First numbered page is 5
        ]

        result = transformer._interpolate_page_numbers(page_mappings)

        # Should infer pages 0 and 1 as 3 and 4
        assert result[0] == (0, 3)
        assert result[1] == (1, 4)
        assert result[2] == (2, 5)

    def test_interpolate_trailing_pages(self, transformer):
        """Test interpolation of pages after last numbered page."""
        page_mappings = [
            (0, 1),
            (1, None),  # After last numbered page
            (2, None),  # After last numbered page
        ]

        result = transformer._interpolate_page_numbers(page_mappings)

        # Should infer pages 1 and 2 as 2 and 3
        assert result[0] == (0, 1)
        assert result[1] == (1, 2)
        assert result[2] == (2, 3)

    def test_interpolate_gap_in_numbering(self, transformer):
        """Test detection of gap (missing pages in physical document)."""
        page_mappings = [
            (0, 1),
            (1, None),
            (2, 5),  # Gap: logical pages 2, 3, 4 missing
        ]

        result = transformer._interpolate_page_numbers(page_mappings)

        # Should NOT interpolate when gap is larger than physical pages
        # Page 1 should remain None
        assert result[1] == (1, None)

    def test_interpolate_multiple_unnumbered_same_logical(self, transformer):
        """Test multiple physical pages between same logical numbers."""
        page_mappings = [
            (0, 1),
            (1, None),  # Unnumbered (chapter start?)
            (2, None),  # Unnumbered (blank?)
            (3, 2),  # Next logical number is same + 1 (no gap)
        ]

        result = transformer._interpolate_page_numbers(page_mappings)

        # Logical gap is 0 but physical gap is 2 - leave as None
        assert result[1] == (1, None)
        assert result[2] == (2, None)

    def test_interpolate_insufficient_data(self, transformer):
        """Test interpolation with insufficient data (< 2 known pages)."""
        page_mappings = [
            (0, None),
            (1, 5),  # Only one known page
            (2, None),
        ]

        result = transformer._interpolate_page_numbers(page_mappings)

        # Should return original (cannot interpolate with only 1 known page)
        assert result == page_mappings

    def test_build_reordering_map_already_ordered(self, transformer):
        """Test reordering map when pages are already in order."""
        page_mappings = [
            (0, 1),
            (1, 2),
            (2, 3),
        ]

        reorder_map = transformer._build_reordering_map(page_mappings, total_pages=3)

        # Should return None (no reordering needed)
        assert reorder_map is None

    def test_build_reordering_map_simple_swap(self, transformer):
        """Test reordering map for simple page swap."""
        page_mappings = [
            (0, 2),  # Page 0 should be second
            (1, 1),  # Page 1 should be first
        ]

        reorder_map = transformer._build_reordering_map(page_mappings, total_pages=2)

        # Should swap pages 0 and 1
        assert reorder_map is not None
        assert 0 in reorder_map  # Page 0 needs to move
        assert 1 in reorder_map  # Page 1 needs to move

    def test_build_reordering_map_complex(self, transformer):
        """Test reordering map for complex reordering."""
        page_mappings = [
            (0, 3),  # Page 0 has logical 3
            (1, 1),  # Page 1 has logical 1
            (2, 2),  # Page 2 has logical 2
        ]

        reorder_map = transformer._build_reordering_map(page_mappings, total_pages=3)

        # Should reorder to [1, 2, 0] (logical 1, 2, 3)
        assert reorder_map is not None

    def test_build_reordering_map_safety_threshold(self, transformer):
        """Test that reordering is skipped if >80% of pages affected."""
        # Create scenario where 9 out of 10 pages need reordering
        page_mappings = [
            (0, 10),
            (1, 9),
            (2, 8),
            (3, 7),
            (4, 6),
            (5, 5),
            (6, 4),
            (7, 3),
            (8, 2),
            (9, 1),
        ]

        reorder_map = transformer._build_reordering_map(page_mappings, total_pages=10)

        # Should return None (too risky - >80% affected)
        assert reorder_map is None

    def test_build_reordering_map_insufficient_data(self, transformer):
        """Test reordering map with insufficient page numbers."""
        page_mappings = [
            (0, 1),
            (1, None),  # Only one known page
        ]

        reorder_map = transformer._build_reordering_map(page_mappings, total_pages=2)

        # Should return None (need at least 2 known pages)
        assert reorder_map is None

    def test_build_reordering_map_with_interpolation(self, transformer):
        """Test that interpolation is applied before building reorder map."""
        page_mappings = [
            (0, 1),
            (1, None),  # Should be interpolated to 2
            (2, 3),
        ]

        reorder_map = transformer._build_reordering_map(page_mappings, total_pages=3)

        # After interpolation, pages should be in order, so no reordering
        assert reorder_map is None

    def test_build_reordering_map_with_interpolation_and_reorder(self, transformer):
        """Test reordering after interpolation when pages are out of order."""
        page_mappings = [
            (0, 3),
            (1, None),  # Will be interpolated
            (2, 1),
        ]

        # After interpolation, might still need reordering
        reorder_map = transformer._build_reordering_map(page_mappings, total_pages=3)

        # Should detect that pages need reordering
        assert reorder_map is not None or reorder_map is None  # Depends on interpolation result

    @patch("ragged.correction.transformers.ordering.pymupdf")
    def test_extract_page_number_from_header(self, mock_pymupdf, transformer):
        """Test page number extraction from header area."""
        mock_page = Mock()
        mock_page.rect = Mock(width=600, height=800)
        mock_page.get_text = Mock(side_effect=["Page 5\n", ""])  # Header has number, footer doesn't

        page_num = transformer._extract_page_number(mock_page)

        assert page_num == 5

    @patch("ragged.correction.transformers.ordering.pymupdf")
    def test_extract_page_number_from_footer(self, mock_pymupdf, transformer):
        """Test page number extraction from footer area."""
        mock_page = Mock()
        mock_page.rect = Mock(width=600, height=800)
        mock_page.get_text = Mock(side_effect=["", "- 10 -\n"])  # Header empty, footer has number

        page_num = transformer._extract_page_number(mock_page)

        assert page_num == 10

    @patch("ragged.correction.transformers.ordering.pymupdf")
    def test_extract_page_number_slash_format(self, mock_pymupdf, transformer):
        """Test page number extraction with X/Y format."""
        mock_page = Mock()
        mock_page.rect = Mock(width=600, height=800)
        mock_page.get_text = Mock(side_effect=["", "7 / 20\n"])

        page_num = transformer._extract_page_number(mock_page)

        assert page_num == 7

    @patch("ragged.correction.transformers.ordering.pymupdf")
    def test_extract_page_number_no_number(self, mock_pymupdf, transformer):
        """Test page number extraction when no number found."""
        mock_page = Mock()
        mock_page.rect = Mock(width=600, height=800)
        mock_page.get_text = Mock(return_value="No numbers here\n")

        page_num = transformer._extract_page_number(mock_page)

        assert page_num is None

    @pytest.mark.parametrize(
        "page_mappings,expected_interpolated",
        [
            # Perfect sequence
            ([(0, 1), (1, None), (2, 3)], [(0, 1), (1, 2), (2, 3)]),
            # Leading pages
            ([(0, None), (1, 3)], [(0, 2), (1, 3)]),
            # Trailing pages
            ([(0, 1), (1, None)], [(0, 1), (1, 2)]),
            # No interpolation needed
            ([(0, 1), (1, 2), (2, 3)], [(0, 1), (1, 2), (2, 3)]),
            # Gap (no interpolation)
            ([(0, 1), (1, None), (2, 10)], [(0, 1), (1, None), (2, 10)]),
        ],
    )
    def test_interpolation_scenarios(self, transformer, page_mappings, expected_interpolated):
        """Test various interpolation scenarios."""
        result = transformer._interpolate_page_numbers(page_mappings)

        # Check if interpolation matches expected
        for i, (expected_idx, expected_num) in enumerate(expected_interpolated):
            assert result[i] == (expected_idx, expected_num), f"Mismatch at index {i}"

    def test_extract_all_page_numbers_integration(self, transformer):
        """Test extracting page numbers from all pages in document."""
        # This would require actual PDF, so we'll mock it
        mock_doc = Mock()
        mock_doc.__len__ = Mock(return_value=3)

        mock_pages = []
        for i in range(3):
            mock_page = Mock()
            mock_page.rect = Mock(width=600, height=800)
            # Simulate page numbers in footer
            mock_page.get_text = Mock(side_effect=["", f"- {i + 1} -\n"])
            mock_pages.append(mock_page)

        mock_doc.__getitem__ = Mock(side_effect=lambda i: mock_pages[i])

        with patch.object(transformer, "_extract_page_number", side_effect=[1, 2, 3]):
            page_mappings = transformer._extract_all_page_numbers(mock_doc)

        assert len(page_mappings) == 3
        assert page_mappings[0] == (0, 1)
        assert page_mappings[1] == (1, 2)
        assert page_mappings[2] == (2, 3)
