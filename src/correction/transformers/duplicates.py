"""PDF duplicate page remover transformer.

v0.3.5: Removes duplicate pages from PDFs.
"""

from pathlib import Path

import pymupdf

from src.correction.schemas import IssueReport, IssueType
from src.utils.logging import get_logger

logger = get_logger(__name__)


class DuplicateRemover:
    """Removes duplicate pages from PDFs.

    Removes pages identified as duplicates while preserving the original
    (first occurrence) of each duplicate group.
    """

    def __init__(self):
        """Initialize duplicate remover."""
        pass

    def transform(self, pdf_path: Path, issues: list[IssueReport], output_path: Path) -> bool:
        """Remove duplicate pages from PDF.

        Args:
            pdf_path: Path to input PDF file.
            issues: List of duplicate issues.
            output_path: Path to write corrected PDF.

        Returns:
            True if corrections applied successfully, False otherwise.

        Raises:
            FileNotFoundError: If PDF file not found.
        """
        # Validate input
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")

        # Filter to duplicate issues only
        duplicate_issues = [
            issue for issue in issues if issue.issue_type == IssueType.DUPLICATE
        ]

        if not duplicate_issues:
            logger.debug("No duplicate issues to correct")
            return True

        logger.info(f"Removing duplicates from {len(duplicate_issues)} duplicate groups")

        try:
            # Read PDF
            doc = pymupdf.open(pdf_path)

            # Build set of pages to remove (convert to 0-indexed)
            pages_to_remove = set()
            for issue in duplicate_issues:
                # Issue.page_numbers contains the duplicate pages (1-indexed)
                # Original is stored in metadata
                pages_to_remove.update(issue.page_numbers)

            logger.debug(f"Removing {len(pages_to_remove)} duplicate pages: {sorted(pages_to_remove)}")

            # Delete pages in reverse order to avoid index shifting
            pages_to_remove_sorted = sorted(pages_to_remove, reverse=True)
            for page_number in pages_to_remove_sorted:
                page_index = page_number - 1  # Convert to 0-indexed
                if 0 <= page_index < len(doc):
                    logger.debug(f"Removing duplicate page {page_number}")
                    doc.delete_page(page_index)

            pages_kept = len(doc)

            # Write corrected PDF
            doc.save(output_path)
            doc.close()

            logger.info(
                f"Duplicate removal complete: kept {pages_kept} pages, "
                f"removed {len(pages_to_remove)} duplicates"
            )
            return True

        except Exception as e:
            logger.error(f"Duplicate removal failed: {e}", exc_info=True)
            return False

    def can_correct(self, issue: IssueReport) -> bool:
        """Check if this transformer can correct the given issue.

        Args:
            issue: Issue to check.

        Returns:
            True if this is a duplicate issue, False otherwise.
        """
        return issue.issue_type == IssueType.DUPLICATE
