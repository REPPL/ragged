"""PDF page rotation transformer.

v0.3.5: Applies rotation corrections to PDF pages using PyMuPDF.
"""

from pathlib import Path

import pymupdf

from src.correction.schemas import IssueReport, IssueType
from src.utils.logging import get_logger

logger = get_logger(__name__)


class RotationTransformer:
    """Applies rotation corrections to PDF pages.

    Uses pypdf to rotate pages clockwise by specified degrees.
    Supports 90°, 180°, and 270° rotations.
    """

    def __init__(self):
        """Initialize rotation transformer."""
        pass

    def transform(self, pdf_path: Path, issues: list[IssueReport], output_path: Path) -> bool:
        """Apply rotation corrections to PDF.

        Args:
            pdf_path: Path to input PDF file.
            issues: List of rotation issues to correct.
            output_path: Path to write corrected PDF.

        Returns:
            True if corrections applied successfully, False otherwise.

        Raises:
            ValueError: If issues contain non-rotation types.
            FileNotFoundError: If PDF file not found.
        """
        # Validate input
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")

        # Filter to rotation issues only
        rotation_issues = [
            issue for issue in issues if issue.issue_type == IssueType.ROTATION
        ]

        if not rotation_issues:
            logger.debug("No rotation issues to correct")
            return True

        logger.info(f"Applying {len(rotation_issues)} rotation corrections")

        try:
            # Read PDF
            doc = pymupdf.open(pdf_path)

            # Build rotation map (page_number -> degrees)
            rotation_map = {}
            for issue in rotation_issues:
                # Get rotation from metadata
                rotation_needed = issue.metadata.get("rotation_needed", 0)

                for page_num in issue.page_numbers:
                    # Store rotation (will be applied once per page)
                    rotation_map[page_num] = rotation_needed

            # Process each page
            for page_num in range(len(doc)):
                page = doc[page_num]
                page_number = page_num + 1  # 1-indexed

                # Check if this page needs rotation
                if page_number in rotation_map:
                    rotation_degrees = rotation_map[page_number]
                    logger.debug(f"Rotating page {page_number} by {rotation_degrees}°")

                    # Rotate page clockwise (PyMuPDF uses positive angles for clockwise)
                    page.set_rotation(rotation_degrees)

            # Write corrected PDF
            doc.save(output_path)
            doc.close()

            logger.info(f"Rotation corrections written to {output_path}")
            return True

        except Exception as e:
            logger.error(f"Rotation correction failed: {e}", exc_info=True)
            return False

    def can_correct(self, issue: IssueReport) -> bool:
        """Check if this transformer can correct the given issue.

        Args:
            issue: Issue to check.

        Returns:
            True if this is a rotation issue, False otherwise.
        """
        return issue.issue_type == IssueType.ROTATION
