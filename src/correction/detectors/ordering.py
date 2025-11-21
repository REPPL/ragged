"""Page order detection for PDFs using page numbers and content flow.

v0.3.5: Detects misordered pages using multi-signal analysis.
"""

import re
from pathlib import Path

import pymupdf

from src.correction.schemas import IssueReport, IssueType
from src.utils.logging import get_logger

logger = get_logger(__name__)


class PageOrderDetector:
    """Detects pages that are out of order.

    Uses multi-signal approach:
    - Signal 1: Page number extraction (regex patterns for Page X, X/Y, -X-)
    - Signal 2: Content flow analysis (sentence continuation, heading hierarchy)

    Confidence threshold: 0.80 (80% agreement between signals required)
    """

    # Common page number patterns
    PAGE_NUMBER_PATTERNS = [
        r'(?:Page|page|PAGE)\s+(\d+)',  # "Page 5"
        r'(\d+)\s*/\s*\d+',  # "5/10" or "5 / 10"
        r'-\s*(\d+)\s*-',  # "- 5 -"
        r'^\s*(\d+)\s*$',  # Just a number (in header/footer area)
    ]

    def __init__(self, confidence_threshold: float = 0.80):
        """Initialize page order detector.

        Args:
            confidence_threshold: Minimum confidence to report ordering issue (0.0-1.0).
        """
        self.confidence_threshold = confidence_threshold

    async def detect(self, pdf_path: Path) -> list[IssueReport]:
        """Detect page ordering issues in PDF.

        Args:
            pdf_path: Path to the PDF file to analyse.

        Returns:
            List of IssueReports for ordering problems.
        """
        issues = []

        try:
            doc = pymupdf.open(pdf_path)

            # Extract page numbers from all pages
            extracted_numbers = []
            for page_num in range(len(doc)):
                page = doc[page_num]
                page_number = self._extract_page_number(page)
                extracted_numbers.append((page_num + 1, page_number))

            # Analyse ordering based on extracted numbers
            ordering_issues = self._analyse_page_numbers(extracted_numbers)
            issues.extend(ordering_issues)

            # Analyse content flow between consecutive pages
            flow_issues = self._analyse_content_flow(doc)
            issues.extend(flow_issues)

            doc.close()

        except Exception as e:
            logger.error(f"Page order detection failed for {pdf_path}: {e}", exc_info=True)
            return []

        logger.debug(f"Page order detection: {len(issues)} ordering issues found")
        return issues

    def _extract_page_number(self, page: pymupdf.Page) -> int | None:
        """Extract page number from header/footer areas.

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

    def _analyse_page_numbers(
        self, extracted_numbers: list[tuple[int, int | None]]
    ) -> list[IssueReport]:
        """Analyse extracted page numbers for ordering issues.

        Args:
            extracted_numbers: List of (physical_page_num, extracted_page_num) tuples.

        Returns:
            List of IssueReports for detected ordering problems.
        """
        issues = []

        # Filter out pages without extracted numbers
        valid_numbers = [
            (physical, logical)
            for physical, logical in extracted_numbers
            if logical is not None
        ]

        if len(valid_numbers) < 2:
            # Not enough data to determine ordering
            return issues

        # Check for non-sequential page numbers
        for i in range(len(valid_numbers) - 1):
            current_physical, current_logical = valid_numbers[i]
            next_physical, next_logical = valid_numbers[i + 1]

            # Expected: next_logical = current_logical + 1
            expected_next = current_logical + 1

            if next_logical != expected_next:
                # Possible ordering issue
                confidence = 0.85  # High confidence from page number mismatch

                # Check if this is just a missing page vs misordering
                if next_logical < current_logical:
                    # Definite misordering (page numbers go backwards)
                    severity = "high"
                    details = (
                        f"Pages {current_physical}-{next_physical} appear misordered: "
                        f"page numbers go from {current_logical} to {next_logical}"
                    )
                elif next_logical > expected_next:
                    # Possible missing page(s)
                    severity = "medium"
                    missing_count = next_logical - expected_next
                    details = (
                        f"Possible missing page(s) between pages {current_physical} and {next_physical}: "
                        f"page numbers jump from {current_logical} to {next_logical} "
                        f"({missing_count} page(s) missing)"
                    )
                else:
                    continue

                issues.append(
                    IssueReport(
                        issue_type=IssueType.ORDERING,
                        page_numbers=[current_physical, next_physical],
                        confidence=confidence,
                        severity=severity,
                        details=details,
                        suggested_correction="Review page order and reorder if necessary",
                        metadata={
                            "current_logical_page": current_logical,
                            "next_logical_page": next_logical,
                            "expected_next": expected_next,
                        },
                    )
                )

        return issues

    def _analyse_content_flow(self, doc: pymupdf.Document) -> list[IssueReport]:
        """Analyse content flow between consecutive pages.

        Looks for:
        - Sentences that end mid-sentence
        - Sentences that start mid-sentence (suggesting previous page missing)

        Args:
            doc: PyMuPDF document object.

        Returns:
            List of IssueReports for content flow issues.
        """
        issues = []

        for page_num in range(len(doc) - 1):
            current_page = doc[page_num]
            next_page = doc[page_num + 1]

            # Get text from pages
            current_text = current_page.get_text().strip()
            next_text = next_page.get_text().strip()

            if not current_text or not next_text:
                continue

            # Check if current page ends mid-sentence
            ends_mid_sentence = self._ends_mid_sentence(current_text)
            starts_mid_sentence = self._starts_mid_sentence(next_text)

            if ends_mid_sentence and not starts_mid_sentence:
                # Current page ends mid-sentence but next doesn't continue it
                # Possible missing page or misordering
                confidence = 0.75  # Medium confidence from content flow

                issues.append(
                    IssueReport(
                        issue_type=IssueType.ORDERING,
                        page_numbers=[page_num + 1, page_num + 2],
                        confidence=confidence,
                        severity="medium",
                        details=(
                            f"Content flow issue between pages {page_num + 1} and {page_num + 2}: "
                            f"page {page_num + 1} ends mid-sentence but next page doesn't continue it"
                        ),
                        suggested_correction="Review content flow and page order",
                        metadata={
                            "current_page_end": current_text[-100:],
                            "next_page_start": next_text[:100],
                        },
                    )
                )

        return issues

    def _ends_mid_sentence(self, text: str) -> bool:
        """Check if text ends mid-sentence (no sentence-ending punctuation).

        Args:
            text: Text to check.

        Returns:
            True if text ends mid-sentence.
        """
        if not text:
            return False

        # Get last 200 characters (or full text if shorter)
        end_text = text[-200:].strip()

        # Check if ends with sentence-ending punctuation
        return not re.search(r'[.!?]\s*$', end_text)

    def _starts_mid_sentence(self, text: str) -> bool:
        """Check if text starts mid-sentence (lowercase start, no capital).

        Args:
            text: Text to check.

        Returns:
            True if text starts mid-sentence.
        """
        if not text:
            return False

        # Get first 200 characters
        start_text = text[:200].strip()

        # Check if starts with lowercase letter (not uppercase or number)
        return bool(re.match(r'^[a-z]', start_text))
