"""PDF page reordering transformer.

v0.3.5: Reorders pages based on detected ordering issues.
v0.4.9: Enhanced automatic reordering based on logical page numbers.
"""
from __future__ import annotations


import re
from pathlib import Path

import pymupdf

from ragged.correction.schemas import IssueReport, IssueType
from ragged.utils.logging import get_logger

logger = get_logger(__name__)


class PageReorderTransformer:
    """Reorders PDF pages based on detected ordering issues.

    v0.4.9: Implements automatic reordering using logical page numbers
    extracted from page headers/footers. Automatically sorts pages by
    their printed page numbers.
    """

    # Common page number patterns (same as detector)
    PAGE_NUMBER_PATTERNS = [
        r'(?:Page|page|PAGE)\s+(\d+)',  # "Page 5"
        r'(\d+)\s*/\s*\d+',  # "5/10" or "5 / 10"
        r'-\s*(\d+)\s*-',  # "- 5 -"
        r'^\s*(\d+)\s*$',  # Just a number (in header/footer area)
    ]

    def __init__(self):
        """Initialise page reorder transformer."""
        pass

    def transform(self, pdf_path: Path, issues: list[IssueReport], output_path: Path) -> bool:
        """Apply page reordering to PDF.

        v0.4.9: Automatically reorders pages based on extracted logical page numbers.

        Args:
            pdf_path: Path to input PDF file.
            issues: List of ordering issues.
            output_path: Path to write corrected PDF.

        Returns:
            True if corrections applied successfully, False otherwise.

        Raises:
            FileNotFoundError: If PDF file not found.
        """
        # Validate input
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")

        # Filter to ordering issues only
        ordering_issues = [
            issue for issue in issues if issue.issue_type == IssueType.ORDERING
        ]

        if not ordering_issues:
            logger.debug("No ordering issues to correct")
            # No issues, just copy the file
            doc = pymupdf.open(pdf_path)
            doc.save(output_path)
            doc.close()
            return True

        logger.info(f"Found {len(ordering_issues)} ordering issues - applying automatic reordering")

        try:
            # Read PDF
            doc = pymupdf.open(pdf_path)
            total_pages = len(doc)

            # Extract logical page numbers from all pages
            page_mappings = self._extract_all_page_numbers(doc)

            # Build reordering map
            reorder_map = self._build_reordering_map(page_mappings, total_pages)

            if reorder_map:
                # Apply reordering
                logger.info(f"Reordering {len(reorder_map)} pages based on logical page numbers")
                self._apply_reordering(doc, reorder_map, output_path)
                logger.info("Automatic page reordering applied successfully")
            else:
                # No clear reordering possible, keep original order
                logger.warning("Could not determine clear reordering - keeping original order")
                doc.save(output_path)

            doc.close()
            return True

        except Exception as e:
            logger.error(f"Page ordering correction failed: {e}", exc_info=True)
            return False

    def can_correct(self, issue: IssueReport) -> bool:
        """Check if this transformer can correct the given issue.

        Args:
            issue: Issue to check.

        Returns:
            True if this is an ordering issue, False otherwise.
        """
        return issue.issue_type == IssueType.ORDERING

    def _extract_all_page_numbers(self, doc: pymupdf.Document) -> list[tuple[int, int | None]]:
        """Extract logical page numbers from all pages.

        Args:
            doc: PyMuPDF document.

        Returns:
            List of (physical_page_index, logical_page_number) tuples.
            Physical page index is 0-based, logical page number is 1-based.
        """
        page_mappings = []

        for page_idx in range(len(doc)):
            page = doc[page_idx]
            logical_page_num = self._extract_page_number(page)
            page_mappings.append((page_idx, logical_page_num))
            logger.debug(
                f"Page {page_idx + 1} (physical) has logical page number: {logical_page_num}"
            )

        return page_mappings

    def _extract_page_number(self, page: pymupdf.Page) -> int | None:
        """Extract logical page number from header/footer areas.

        Args:
            page: PyMuPDF page object.

        Returns:
            Extracted page number or None if not found.
        """
        # Get page dimensions
        rect = page.rect
        height = rect.height

        # Define header and footer regions (top 10% and bottom 10% of page)
        header_rect = pymupdf.Rect(0, 0, rect.width, height * 0.1)
        footer_rect = pymupdf.Rect(0, height * 0.9, rect.width, height)

        # Extract text from header and footer
        header_text = page.get_text(clip=header_rect)
        footer_text = page.get_text(clip=footer_rect)
        combined_text = header_text + "\n" + footer_text

        # Try each pattern
        for pattern in self.PAGE_NUMBER_PATTERNS:
            match = re.search(pattern, combined_text, re.MULTILINE)
            if match:
                try:
                    return int(match.group(1))
                except (ValueError, IndexError):
                    continue

        return None

    def _build_reordering_map(
        self, page_mappings: list[tuple[int, int | None]], total_pages: int
    ) -> dict[int, int] | None:
        """Build a reordering map from page number mappings.

        v0.4.9: Implements automatic reordering based on logical page numbers.
        Handles missing page numbers through interpolation.

        Args:
            page_mappings: List of (physical_index, logical_page_num) tuples.
            total_pages: Total number of pages in PDF.

        Returns:
            Dictionary mapping original page indices to new positions,
            or None if reordering cannot be determined.
        """
        # Step 1: Interpolate missing page numbers
        interpolated_mappings = self._interpolate_page_numbers(page_mappings)

        # Filter out pages still without logical page numbers after interpolation
        valid_mappings = [
            (physical_idx, logical_num)
            for physical_idx, logical_num in interpolated_mappings
            if logical_num is not None
        ]

        if len(valid_mappings) < 2:
            # Not enough information to reorder
            logger.debug("Not enough pages with logical page numbers for reordering")
            return None

        # Check if pages are already in order
        is_ordered = all(
            valid_mappings[i][1] < valid_mappings[i + 1][1]
            for i in range(len(valid_mappings) - 1)
        )

        if is_ordered:
            logger.debug("Pages already in correct order")
            return None

        # Sort pages by logical page number
        sorted_mappings = sorted(valid_mappings, key=lambda x: x[1])

        # Build reordering map
        reorder_map = {}
        for new_position, (original_physical_idx, logical_num) in enumerate(sorted_mappings):
            if original_physical_idx != new_position:
                # This page needs to be moved
                reorder_map[original_physical_idx] = new_position
                logger.debug(
                    f"Reorder: Physical page {original_physical_idx + 1} "
                    f"(logical {logical_num}) → position {new_position + 1}"
                )

        # Sanity check: ensure we're not reordering too many pages
        # For small documents (< 5 pages), allow any reordering
        # For larger documents, limit to 80% to avoid catastrophic mistakes
        if total_pages >= 5 and len(reorder_map) > total_pages * 0.8:
            logger.warning(
                f"Reordering would affect {len(reorder_map)}/{total_pages} pages - "
                "may be too risky, skipping"
            )
            return None

        return reorder_map if reorder_map else None

    def _interpolate_page_numbers(
        self, page_mappings: list[tuple[int, int | None]]
    ) -> list[tuple[int, int | None]]:
        """Interpolate missing page numbers between known page numbers.

        Common scenarios:
        - Chapter start pages (often no page number)
        - Blank pages
        - Title pages
        - Some books only number odd or even pages

        Strategy:
        1. Find gaps between known page numbers
        2. Interpolate sequential numbers for gap pages
        3. Handle edge cases (beginning/end of document)

        Args:
            page_mappings: List of (physical_index, logical_page_num) tuples.

        Returns:
            List with interpolated page numbers filled in where possible.
        """
        result = list(page_mappings)  # Copy

        # Find all pages with known page numbers
        known_pages = [
            (idx, physical_idx, logical_num)
            for idx, (physical_idx, logical_num) in enumerate(page_mappings)
            if logical_num is not None
        ]

        # Interpolate gaps between known pages (requires at least 2 known pages)
        if len(known_pages) >= 2:
            for i in range(len(known_pages) - 1):
                current_idx, current_physical, current_logical = known_pages[i]
                next_idx, next_physical, next_logical = known_pages[i + 1]

                # Check if there's a gap to fill
                gap_size = next_idx - current_idx - 1
                logical_gap = next_logical - current_logical - 1

                if gap_size > 0 and logical_gap >= 0:
                    # Interpolate: assume sequential page numbers
                    if logical_gap == gap_size:
                        # Perfect match: fill in sequential numbers
                        for j in range(1, gap_size + 1):
                            interpolated_logical = current_logical + j
                            gap_idx = current_idx + j
                            gap_physical_idx = result[gap_idx][0]
                            result[gap_idx] = (gap_physical_idx, interpolated_logical)
                            logger.debug(
                                f"Interpolated: Page {gap_physical_idx + 1} → logical page {interpolated_logical}"
                            )
                    elif logical_gap > gap_size:
                        # Missing pages in physical document (gap in numbering)
                        logger.debug(
                            f"Gap detected: {gap_size} physical pages but {logical_gap} logical pages "
                            f"between {current_logical} and {next_logical} - some pages missing"
                        )
                        # Don't interpolate - could be intentional gaps
                    elif logical_gap == 0 and gap_size > 0:
                        # Multiple physical pages with same logical number
                        # (e.g., all blank pages, all chapter starts)
                        logger.debug(
                            f"Found {gap_size} unnumbered pages between logical {current_logical} and {next_logical}"
                        )
                        # Assign same number as previous (or don't assign)
                        # For now, leave as None to avoid confusion

        # Handle leading/trailing pages (requires at least 2 known pages for confidence)
        # With only 1 known page, we can't reliably infer sequence direction
        if len(known_pages) >= 2:
            # Handle leading pages (before first known page number)
            first_known_idx, first_physical, first_logical = known_pages[0]
            if first_known_idx > 0 and first_logical > 1:
                # There are pages before first numbered page, and first number > 1
                # Assume these are front matter with sequential numbering
                for i in range(first_known_idx):
                    inferred_logical = first_logical - (first_known_idx - i)
                    if inferred_logical > 0:
                        physical_idx = result[i][0]
                        result[i] = (physical_idx, inferred_logical)
                        logger.debug(
                            f"Inferred leading: Page {physical_idx + 1} → logical page {inferred_logical}"
                        )

            # Handle trailing pages (after last known page number)
            last_known_idx, last_physical, last_logical = known_pages[-1]
            if last_known_idx < len(result) - 1:
                # There are pages after last numbered page
                # Assume sequential continuation
                for i in range(last_known_idx + 1, len(result)):
                    offset = i - last_known_idx
                    inferred_logical = last_logical + offset
                    physical_idx = result[i][0]
                    result[i] = (physical_idx, inferred_logical)
                    logger.debug(
                        f"Inferred trailing: Page {physical_idx + 1} → logical page {inferred_logical}"
                    )

        return result

    def _apply_reordering(
        self, doc: pymupdf.Document, reorder_map: dict[int, int], output_path: Path
    ) -> None:
        """Apply page reordering to document.

        Args:
            doc: PyMuPDF document to reorder.
            reorder_map: Mapping of original indices to new positions.
            output_path: Output path for reordered PDF.
        """
        # Build complete page order (including unmapped pages)
        total_pages = len(doc)
        new_order = list(range(total_pages))

        # Apply reordering map
        # We need to be careful here: the map tells us where pages should go,
        # but we need to construct the final order
        for original_idx, new_position in reorder_map.items():
            new_order[new_position] = original_idx

        # Create new PDF with reordered pages
        new_doc = pymupdf.open()
        for page_idx in new_order:
            new_doc.insert_pdf(doc, from_page=page_idx, to_page=page_idx)

        # Save reordered PDF
        new_doc.save(output_path)
        new_doc.close()

        logger.info(f"Applied reordering: {len(reorder_map)} pages repositioned")
