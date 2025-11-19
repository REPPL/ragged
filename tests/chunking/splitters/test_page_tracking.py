"""Tests for page tracking and mapping functionality.

v0.2.9: Tests for page position mapping and chunk-to-page assignment.
"""

import pytest
from src.chunking.splitters.page_tracking import (
    build_page_position_map,
    get_page_for_position,
    build_clean_to_orig_map,
    map_chunks_to_pages,
    estimate_page_from_position,
)


class TestBuildPagePositionMap:
    """Tests for build_page_position_map function."""

    def test_single_page_marker(self):
        """Test extracting single page marker."""
        content = "Some text\n<!-- PAGE 1 -->\nPage 1 content"
        positions = build_page_position_map(content)

        assert len(positions) == 1
        assert positions[0][0] == 1  # Page number
        assert positions[0][1] == 10  # Position after "Some text\n"

    def test_multiple_page_markers(self):
        """Test extracting multiple page markers."""
        content = "<!-- PAGE 1 -->\nPage 1\n<!-- PAGE 2 -->\nPage 2\n<!-- PAGE 3 -->\nPage 3"
        positions = build_page_position_map(content)

        assert len(positions) == 3
        assert positions[0] == (1, 0)
        assert positions[1][0] == 2
        assert positions[2][0] == 3

    def test_no_page_markers(self):
        """Test content without page markers."""
        content = "Just some plain text without any markers"
        positions = build_page_position_map(content)

        assert len(positions) == 0

    def test_empty_content(self):
        """Test empty content."""
        content = ""
        positions = build_page_position_map(content)

        assert len(positions) == 0

    def test_markers_only(self):
        """Test content with only markers."""
        content = "<!-- PAGE 1 --><!-- PAGE 2 --><!-- PAGE 3 -->"
        positions = build_page_position_map(content)

        assert len(positions) == 3

    def test_multidigit_page_numbers(self):
        """Test markers with multi-digit page numbers."""
        content = "<!-- PAGE 10 -->\nPage 10\n<!-- PAGE 99 -->\nPage 99\n<!-- PAGE 100 -->\nPage 100"
        positions = build_page_position_map(content)

        assert len(positions) == 3
        assert positions[0][0] == 10
        assert positions[1][0] == 99
        assert positions[2][0] == 100

    def test_position_ordering(self):
        """Test that positions are in order."""
        content = "<!-- PAGE 1 -->\nContent\n<!-- PAGE 2 -->\nMore content\n<!-- PAGE 3 -->\nEven more"
        positions = build_page_position_map(content)

        for i in range(len(positions) - 1):
            assert positions[i][1] < positions[i + 1][1]


class TestGetPageForPosition:
    """Tests for get_page_for_position function."""

    def test_position_on_first_page(self):
        """Test position on first page."""
        page_positions = [(1, 0), (2, 100), (3, 200)]
        page = get_page_for_position(50, page_positions)
        assert page == 1

    def test_position_on_middle_page(self):
        """Test position on middle page."""
        page_positions = [(1, 0), (2, 100), (3, 200)]
        page = get_page_for_position(150, page_positions)
        assert page == 2

    def test_position_on_last_page(self):
        """Test position on last page."""
        page_positions = [(1, 0), (2, 100), (3, 200)]
        page = get_page_for_position(250, page_positions)
        assert page == 3

    def test_position_at_page_boundary(self):
        """Test position exactly at page marker."""
        page_positions = [(1, 0), (2, 100), (3, 200)]
        page = get_page_for_position(100, page_positions)
        assert page == 2  # At boundary, belongs to new page

    def test_no_page_positions(self):
        """Test with empty page positions."""
        page = get_page_for_position(50, [])
        assert page == 1  # Default to page 1

    def test_position_before_first_marker(self):
        """Test position before first page marker."""
        page_positions = [(1, 100), (2, 200)]
        page = get_page_for_position(50, page_positions)
        assert page == 1

    def test_position_after_last_marker(self):
        """Test position after last page marker."""
        page_positions = [(1, 0), (2, 100), (3, 200)]
        page = get_page_for_position(300, page_positions)
        assert page == 3


class TestBuildCleanToOrigMap:
    """Tests for build_clean_to_orig_map function."""

    def test_no_markers(self):
        """Test mapping with no page markers."""
        original = "Plain text without markers"
        mapping = build_clean_to_orig_map(original)

        # Should be 1:1 mapping
        assert len(mapping) == len(original)
        for i in range(len(original)):
            assert mapping[i] == i

    def test_single_marker(self):
        """Test mapping with single page marker."""
        original = "Before<!-- PAGE 1 -->\nAfter"
        mapping = build_clean_to_orig_map(original)

        # "Before" maps normally (0-5)
        for i in range(6):
            assert mapping[i] == i

        # After marker, positions skip the marker length
        marker_len = len("<!-- PAGE 1 -->\n")
        assert mapping[6] == 6 + marker_len  # 'A' after marker

    def test_multiple_markers(self):
        """Test mapping with multiple page markers."""
        original = "A<!-- PAGE 1 -->B<!-- PAGE 2 -->C"
        mapping = build_clean_to_orig_map(original)

        # 'A' at position 0 in both
        assert mapping[0] == 0

        # 'B' skips first marker
        marker1_len = len("<!-- PAGE 1 -->")
        assert mapping[1] == 1 + marker1_len

        # 'C' skips both markers
        marker2_len = len("<!-- PAGE 2 -->")
        assert mapping[2] == 2 + marker1_len + marker2_len

    def test_empty_content(self):
        """Test mapping with empty content."""
        original = ""
        mapping = build_clean_to_orig_map(original)
        assert len(mapping) == 0

    def test_markers_with_newlines(self):
        """Test markers with newlines."""
        original = "Text\n<!-- PAGE 1 -->\nMore text"
        mapping = build_clean_to_orig_map(original)

        # Should correctly skip marker with newline
        assert len(mapping) == len("TextMore text")


class TestMapChunksToPages:
    """Tests for map_chunks_to_pages function."""

    def test_single_page_chunks(self):
        """Test chunks all on one page."""
        text_chunks = ["Chunk 1", "Chunk 2", "Chunk 3"]
        clean_content = "Chunk 1 Chunk 2 Chunk 3"
        original_content = "<!-- PAGE 1 -->\nChunk 1 Chunk 2 Chunk 3"
        page_positions = [(1, 0)]

        result = map_chunks_to_pages(text_chunks, clean_content, original_content, page_positions)

        assert len(result) == 3
        for page_num, page_range in result:
            assert page_num == 1
            assert page_range is None  # Single page

    def test_chunks_across_pages(self):
        """Test chunks spanning multiple pages."""
        text_chunks = ["Chunk on page 1", "Chunk spanning", "Chunk on page 3"]
        clean_content = "Chunk on page 1 Chunk spanning Chunk on page 3"
        original_content = (
            "<!-- PAGE 1 -->\nChunk on page 1 <!-- PAGE 2 -->\nChunk spanning "
            "<!-- PAGE 3 -->\nChunk on page 3"
        )
        page_positions = [(1, 0), (2, 33), (3, 65)]

        result = map_chunks_to_pages(text_chunks, clean_content, original_content, page_positions)

        assert result[0][0] == 1  # First chunk on page 1
        # Middle chunk might span pages
        assert result[2][0] == 3  # Last chunk on page 3

    def test_no_page_markers(self):
        """Test chunks without page markers."""
        text_chunks = ["Chunk 1", "Chunk 2"]
        clean_content = "Chunk 1 Chunk 2"
        original_content = "Chunk 1 Chunk 2"
        page_positions = []

        result = map_chunks_to_pages(text_chunks, clean_content, original_content, page_positions)

        assert len(result) == 2
        for page_num, page_range in result:
            assert page_num is None
            assert page_range is None

    def test_multi_page_chunk(self):
        """Test chunk spanning multiple pages."""
        text_chunks = ["Long chunk spanning two pages"]
        clean_content = "Long chunk spanning two pages"
        original_content = (
            "<!-- PAGE 1 -->\nLong chunk spanning "
            "<!-- PAGE 2 -->\ntwo pages"
        )
        page_positions = [(1, 0), (2, 37)]

        result = map_chunks_to_pages(text_chunks, clean_content, original_content, page_positions)

        assert len(result) == 1
        page_num, page_range = result[0]
        assert page_num == 1
        assert page_range == "1-2"

    def test_chunk_not_found(self):
        """Test graceful handling when chunk not found."""
        text_chunks = ["Nonexistent chunk"]
        clean_content = "Different content"
        original_content = "<!-- PAGE 1 -->\nDifferent content"
        page_positions = [(1, 0)]

        result = map_chunks_to_pages(text_chunks, clean_content, original_content, page_positions)

        assert len(result) == 1
        page_num, page_range = result[0]
        assert page_num is None
        assert page_range is None

    def test_empty_chunks(self):
        """Test with empty chunks list."""
        text_chunks = []
        clean_content = "Content"
        original_content = "<!-- PAGE 1 -->\nContent"
        page_positions = [(1, 0)]

        result = map_chunks_to_pages(text_chunks, clean_content, original_content, page_positions)

        assert len(result) == 0


class TestEstimatePageFromPosition:
    """Tests for estimate_page_from_position function."""

    def test_first_chunk(self):
        """Test estimation for first chunk."""
        page = estimate_page_from_position(0, 10, 5)
        assert page == 1

    def test_last_chunk(self):
        """Test estimation for last chunk."""
        page = estimate_page_from_position(9, 10, 5)
        assert page == 5

    def test_middle_chunk(self):
        """Test estimation for middle chunk."""
        page = estimate_page_from_position(5, 10, 5)
        # Should be around page 3
        assert 2 <= page <= 4

    def test_single_page_document(self):
        """Test estimation for single-page document."""
        for chunk_pos in range(5):
            page = estimate_page_from_position(chunk_pos, 5, 1)
            assert page == 1

    def test_zero_total_pages(self):
        """Test with zero total pages."""
        page = estimate_page_from_position(0, 10, 0)
        assert page == 1  # Should not crash, return 1

    def test_single_chunk(self):
        """Test with single chunk."""
        page = estimate_page_from_position(0, 1, 5)
        assert page == 1

    def test_bounds_checking(self):
        """Test that result is within valid page range."""
        for chunk_pos in range(20):
            page = estimate_page_from_position(chunk_pos, 20, 10)
            assert 1 <= page <= 10

    def test_linear_distribution(self):
        """Test linear distribution of chunks across pages."""
        # 100 chunks across 10 pages
        total_chunks = 100
        total_pages = 10

        prev_page = 0
        for i in range(0, total_chunks, 10):
            page = estimate_page_from_position(i, total_chunks, total_pages)
            # Pages should increase monotonically
            assert page >= prev_page
            prev_page = page


class TestIntegrationScenarios:
    """Integration tests for page tracking workflows."""

    def test_pdf_page_tracking_workflow(self):
        """Test complete workflow for PDF with page markers."""
        # Simulate PDF content with markers
        original_content = (
            "<!-- PAGE 1 -->\nFirst page content here.\n"
            "<!-- PAGE 2 -->\nSecond page content here.\n"
            "<!-- PAGE 3 -->\nThird page content here."
        )

        # Build page map
        page_positions = build_page_position_map(original_content)
        assert len(page_positions) == 3

        # Clean content for chunking
        import re
        clean_content = re.sub(r'<!-- PAGE \d+ -->\n?', '', original_content)

        # Simulate chunks
        text_chunks = [
            "First page content here.",
            "Second page content here.",
            "Third page content here.",
        ]

        # Map chunks to pages
        chunk_pages = map_chunks_to_pages(text_chunks, clean_content, original_content, page_positions)

        # Verify page assignments
        assert chunk_pages[0][0] == 1
        assert chunk_pages[1][0] == 2
        assert chunk_pages[2][0] == 3

    def test_text_file_no_pages(self):
        """Test workflow for text file without pages."""
        content = "Just plain text with no page markers"

        page_positions = build_page_position_map(content)
        assert len(page_positions) == 0

        text_chunks = ["Just plain text", "with no page markers"]
        chunk_pages = map_chunks_to_pages(text_chunks, content, content, page_positions)

        # All should have None for pages
        for page_num, page_range in chunk_pages:
            assert page_num is None
            assert page_range is None

    def test_chunk_spanning_multiple_pages(self):
        """Test chunk that spans 3+ pages."""
        original_content = (
            "<!-- PAGE 1 -->\nStart of long chunk "
            "<!-- PAGE 2 -->\ncontinues here "
            "<!-- PAGE 3 -->\nand ends here."
        )

        clean_content = re.sub(r'<!-- PAGE \d+ -->\n?', '', original_content)
        page_positions = build_page_position_map(original_content)

        text_chunks = ["Start of long chunk continues here and ends here."]
        chunk_pages = map_chunks_to_pages(text_chunks, clean_content, original_content, page_positions)

        page_num, page_range = chunk_pages[0]
        assert page_num == 1
        assert page_range == "1-3"

    def test_fallback_estimation(self):
        """Test fallback to estimation when page tracking fails."""
        # Scenario: page positions exist but chunk not found in content
        total_chunks = 10
        total_pages = 5

        # Use estimation for all chunks
        for i in range(total_chunks):
            page = estimate_page_from_position(i, total_chunks, total_pages)
            assert 1 <= page <= total_pages
