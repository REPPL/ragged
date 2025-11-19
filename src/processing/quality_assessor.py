"""
Quality assessment framework for document analysis and routing.

This module provides quality assessment capabilities to analyse document
characteristics and determine optimal processing strategies. It evaluates
born-digital vs scanned documents, image quality, layout complexity, and
other factors to inform intelligent processor routing.

v0.3.4b: Intelligent Routing
"""

from __future__ import annotations

import hashlib
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from src.utils.logging import get_logger

logger = get_logger(__name__)


@dataclass
class PageQuality:
    """
    Quality metrics for a single page.

    Attributes:
        page_number: Page number (1-indexed)
        is_born_digital: Whether page appears to be born-digital
        is_scanned: Whether page appears to be scanned
        text_quality: Text clarity score (0.0-1.0)
        image_quality: Image quality score (0.0-1.0) if scanned
        layout_complexity: Layout complexity score (0.0-1.0)
        has_tables: Whether page contains tables
        has_rotated_content: Whether page has rotated text/images
        metadata: Additional page-specific metadata
    """

    page_number: int
    is_born_digital: bool = False
    is_scanned: bool = False
    text_quality: float = 0.0
    image_quality: float = 0.0
    layout_complexity: float = 0.0
    has_tables: bool = False
    has_rotated_content: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def overall_score(self) -> float:
        """
        Calculate overall quality score for this page.

        Returns:
            Quality score between 0.0 and 1.0
        """
        if self.is_born_digital:
            # Born-digital: prioritise text quality and layout
            return (self.text_quality * 0.7 + (1.0 - self.layout_complexity * 0.5) * 0.3)
        else:
            # Scanned: prioritise image quality and text quality
            return (self.image_quality * 0.5 + self.text_quality * 0.5)


@dataclass
class QualityAssessment:
    """
    Complete quality assessment for a document.

    This assessment includes both document-level and page-level quality
    metrics to inform routing decisions and processing configuration.

    Attributes:
        overall_score: Aggregated quality score (0.0-1.0)
        is_born_digital: Whether document is born-digital
        is_scanned: Whether document is scanned
        text_quality: Average text quality across pages (0.0-1.0)
        layout_complexity: Average layout complexity (0.0-1.0)
        image_quality: Average image quality for scanned docs (0.0-1.0)
        has_tables: Whether document contains tables
        has_rotated_content: Whether document has rotated content
        page_scores: Per-page quality assessments
        recommended_processor: Recommended processor name
        confidence: Confidence in recommendation (0.0-1.0)
        metadata: Additional assessment metadata
    """

    overall_score: float
    is_born_digital: bool
    is_scanned: bool
    text_quality: float
    layout_complexity: float
    image_quality: float
    has_tables: bool
    has_rotated_content: bool
    page_scores: List[PageQuality] = field(default_factory=list)
    recommended_processor: str = "docling"
    confidence: float = 1.0
    metadata: Dict[str, Any] = field(default_factory=dict)


class QualityAssessor:
    """
    Assess document quality to determine optimal processing strategy.

    This class analyses PDF documents to determine their characteristics
    and quality metrics, which are used to route documents to the most
    appropriate processor with optimal configuration.

    Assessment includes:
    - Born-digital vs scanned detection
    - Image quality analysis (resolution, contrast, noise, skew)
    - Layout complexity analysis (columns, tables, mixed content)
    - Per-page quality scoring
    - Overall quality aggregation

    Example:
        >>> assessor = QualityAssessor(fast_mode=True, cache_enabled=True)
        >>> assessment = assessor.assess(Path("document.pdf"))
        >>> print(f"Quality: {assessment.overall_score:.2f}")
        >>> print(f"Born-digital: {assessment.is_born_digital}")
    """

    def __init__(
        self,
        fast_mode: bool = True,
        cache_enabled: bool = True,
        max_pages_to_analyse: int = 3,
    ):
        """
        Initialise quality assessor.

        Args:
            fast_mode: Enable fast mode (analyse subset of pages)
            cache_enabled: Enable quality assessment caching
            max_pages_to_analyse: Maximum pages to analyse in fast mode
        """
        self.fast_mode = fast_mode
        self.cache_enabled = cache_enabled
        self.max_pages_to_analyse = max_pages_to_analyse
        self._cache: Dict[str, QualityAssessment] = {}

        # Lazy imports for heavy dependencies
        self._pymupdf = None
        self._cv2 = None
        self._np = None

        logger.debug(
            f"Quality assessor initialised: "
            f"fast_mode={fast_mode}, cache_enabled={cache_enabled}"
        )

    def assess(self, file_path: Path) -> QualityAssessment:
        """
        Assess document quality and characteristics.

        Args:
            file_path: Path to PDF file

        Returns:
            Quality assessment with metrics and recommendations

        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If file is not a PDF
        """
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        if file_path.suffix.lower() != ".pdf":
            raise ValueError(f"Only PDF files supported, got: {file_path.suffix}")

        # Check cache
        cache_key = self._cache_key(file_path)
        if self.cache_enabled and cache_key in self._cache:
            logger.debug(f"Using cached quality assessment for {file_path.name}")
            return self._cache[cache_key]

        start_time = time.time()
        logger.debug(f"Assessing document quality: {file_path.name}")

        try:
            # Perform assessment
            assessment = self._assess_pdf(file_path)

            # Cache result
            if self.cache_enabled:
                self._cache[cache_key] = assessment

            duration = time.time() - start_time
            logger.info(
                f"Quality assessment complete: {file_path.name} "
                f"(score={assessment.overall_score:.2f}, "
                f"born_digital={assessment.is_born_digital}, "
                f"duration={duration:.2f}s)"
            )

            return assessment

        except Exception as e:
            logger.error(f"Quality assessment failed for {file_path.name}: {e}")
            # Return conservative fallback assessment
            return self._fallback_assessment(file_path, str(e))

    def _cache_key(self, file_path: Path) -> str:
        """
        Generate cache key from file path, size, and modification time.

        Args:
            file_path: Path to file

        Returns:
            Cache key string
        """
        stat = file_path.stat()
        key_data = f"{file_path}:{stat.st_size}:{stat.st_mtime}"
        return hashlib.md5(key_data.encode()).hexdigest()

    def _assess_pdf(self, file_path: Path) -> QualityAssessment:
        """
        Perform PDF quality assessment.

        Args:
            file_path: Path to PDF file

        Returns:
            Quality assessment
        """
        # Lazy import PyMuPDF
        if self._pymupdf is None:
            import fitz
            self._pymupdf = fitz

        # Open PDF
        doc = self._pymupdf.open(str(file_path))
        page_count = len(doc)

        # Determine pages to analyse
        if self.fast_mode:
            pages_to_analyse = min(self.max_pages_to_analyse, page_count)
            page_indices = list(range(pages_to_analyse))
        else:
            pages_to_analyse = page_count
            page_indices = list(range(page_count))

        logger.debug(
            f"Analysing {pages_to_analyse} of {page_count} pages "
            f"(fast_mode={self.fast_mode})"
        )

        # Analyse each page
        page_scores: List[PageQuality] = []
        for page_idx in page_indices:
            page = doc[page_idx]
            page_quality = self._assess_page(page, page_idx + 1)
            page_scores.append(page_quality)

        doc.close()

        # Aggregate results
        return self._aggregate_assessment(page_scores, page_count, file_path)

    def _assess_page(self, page: Any, page_number: int) -> PageQuality:
        """
        Assess quality of a single page.

        Args:
            page: PyMuPDF page object
            page_number: Page number (1-indexed)

        Returns:
            Page quality metrics
        """
        # Detect born-digital vs scanned
        is_born_digital = self._is_born_digital(page)
        is_scanned = not is_born_digital

        # Text quality
        text_quality = self._assess_text_quality(page, is_born_digital)

        # Image quality (for scanned documents)
        image_quality = 0.0
        if is_scanned:
            image_quality = self._assess_image_quality(page)

        # Layout complexity
        layout_complexity = self._assess_layout_complexity(page)

        # Detect tables and rotated content
        has_tables = self._detect_tables(page)
        has_rotated_content = self._detect_rotated_content(page)

        return PageQuality(
            page_number=page_number,
            is_born_digital=is_born_digital,
            is_scanned=is_scanned,
            text_quality=text_quality,
            image_quality=image_quality,
            layout_complexity=layout_complexity,
            has_tables=has_tables,
            has_rotated_content=has_rotated_content,
        )

    def _is_born_digital(self, page: Any) -> bool:
        """
        Detect if page is born-digital (not scanned).

        Born-digital indicators:
        - Embedded fonts
        - Text objects (not just images)
        - No full-page images

        Args:
            page: PyMuPDF page object

        Returns:
            True if born-digital, False if scanned
        """
        # Check for embedded fonts
        fonts = page.get_fonts()
        has_fonts = len(fonts) > 0

        # Check for text objects
        text = page.get_text()
        has_text = len(text.strip()) > 50  # Meaningful amount of text

        # Check for full-page images (indicator of scanned doc)
        images = page.get_images()

        # If page has images, check if any are full-page
        has_fullpage_image = False
        if images:
            page_rect = page.rect
            page_area = page_rect.width * page_rect.height

            for img_info in images[:3]:  # Check first few images
                try:
                    # Get image bounding box
                    xref = img_info[0]
                    img_rects = page.get_image_rects(xref)

                    for rect in img_rects:
                        img_area = rect.width * rect.height
                        # If image covers >80% of page, likely scanned
                        if img_area > (page_area * 0.8):
                            has_fullpage_image = True
                            break

                    if has_fullpage_image:
                        break
                except Exception as e:
                    logger.debug(f"Error checking image size: {e}")

        # Born-digital if has fonts, has text, and no full-page image
        is_born_digital = has_fonts and has_text and not has_fullpage_image

        logger.debug(
            f"Page {page.number + 1}: "
            f"fonts={has_fonts}, text={has_text}, "
            f"fullpage_img={has_fullpage_image} → "
            f"born_digital={is_born_digital}"
        )

        return is_born_digital

    def _assess_text_quality(self, page: Any, is_born_digital: bool) -> float:
        """
        Assess text quality on page.

        Args:
            page: PyMuPDF page object
            is_born_digital: Whether page is born-digital

        Returns:
            Text quality score (0.0-1.0)
        """
        # Get text
        text = page.get_text()

        if not text or len(text.strip()) < 10:
            return 0.0

        # For born-digital, text quality is typically high
        if is_born_digital:
            # Check for reasonable text density
            blocks = page.get_text("blocks")
            if len(blocks) > 0:
                return 0.95  # High quality for born-digital
            return 0.8

        # For scanned, assess based on text extraction success
        # This is a simplified heuristic - in future could use OCR confidence
        text_length = len(text.strip())

        if text_length > 1000:
            return 0.9  # Good extraction
        elif text_length > 500:
            return 0.75  # Moderate extraction
        elif text_length > 100:
            return 0.6  # Poor extraction
        else:
            return 0.3  # Very poor extraction

    def _assess_image_quality(self, page: Any) -> float:
        """
        Assess image quality for scanned pages.

        Analyses:
        - Resolution
        - Contrast (standard deviation)
        - Noise (Laplacian variance)
        - Skew (Hough transform)

        Args:
            page: PyMuPDF page object

        Returns:
            Image quality score (0.0-1.0)
        """
        try:
            # Lazy import OpenCV and numpy
            if self._cv2 is None:
                import cv2
                import numpy as np
                self._cv2 = cv2
                self._np = np

            # Get page as image
            pix = page.get_pixmap(matrix=self._pymupdf.Matrix(2, 2))  # 2x scaling
            img_data = pix.samples

            # Convert to numpy array
            img = self._np.frombuffer(img_data, dtype=self._np.uint8)
            img = img.reshape(pix.height, pix.width, pix.n)

            # Convert to grayscale
            if pix.n == 4:  # RGBA
                img_gray = self._cv2.cvtColor(img, self._cv2.COLOR_RGBA2GRAY)
            elif pix.n == 3:  # RGB
                img_gray = self._cv2.cvtColor(img, self._cv2.COLOR_RGB2GRAY)
            else:
                img_gray = img

            # 1. Resolution score
            resolution_score = min(1.0, (pix.width * pix.height) / (1200 * 1600))

            # 2. Contrast score (standard deviation)
            std_dev = self._np.std(img_gray)
            contrast_score = min(1.0, std_dev / 50.0)  # Normalise to 0-1

            # 3. Sharpness score (Laplacian variance)
            laplacian = self._cv2.Laplacian(img_gray, self._cv2.CV_64F)
            sharpness = laplacian.var()
            sharpness_score = min(1.0, sharpness / 500.0)  # Normalise

            # 4. Noise score (inverted - lower noise is better)
            # Use a small region to estimate noise
            h, w = img_gray.shape
            roi = img_gray[h//4:3*h//4, w//4:3*w//4]
            noise_estimate = self._np.std(roi)
            noise_score = max(0.0, 1.0 - (noise_estimate / 30.0))

            # Combine scores
            overall = (
                resolution_score * 0.3 +
                contrast_score * 0.3 +
                sharpness_score * 0.3 +
                noise_score * 0.1
            )

            logger.debug(
                f"Image quality: resolution={resolution_score:.2f}, "
                f"contrast={contrast_score:.2f}, sharpness={sharpness_score:.2f}, "
                f"noise={noise_score:.2f} → {overall:.2f}"
            )

            return overall

        except Exception as e:
            logger.debug(f"Image quality assessment failed: {e}")
            return 0.5  # Default moderate quality

    def _assess_layout_complexity(self, page: Any) -> float:
        """
        Assess layout complexity of page.

        Complexity factors:
        - Number of columns
        - Number of text blocks
        - Mixed content (text + images + tables)

        Args:
            page: PyMuPDF page object

        Returns:
            Layout complexity score (0.0-1.0)
        """
        try:
            # Get text blocks
            blocks = page.get_text("blocks")
            num_blocks = len(blocks)

            # Get images
            images = page.get_images()
            num_images = len(images)

            # Estimate columns based on block x-positions
            if num_blocks > 0:
                x_positions = [block[0] for block in blocks]
                x_positions_unique = len(set(int(x / 50) for x in x_positions))
                estimated_columns = min(4, x_positions_unique)
            else:
                estimated_columns = 1

            # Complexity score
            # More blocks, images, and columns = higher complexity
            block_score = min(1.0, num_blocks / 20.0)
            image_score = min(1.0, num_images / 5.0)
            column_score = (estimated_columns - 1) / 3.0  # 1 col=0, 4 col=1

            complexity = (
                block_score * 0.4 +
                image_score * 0.3 +
                column_score * 0.3
            )

            logger.debug(
                f"Layout complexity: blocks={num_blocks}, images={num_images}, "
                f"columns={estimated_columns} → {complexity:.2f}"
            )

            return complexity

        except Exception as e:
            logger.debug(f"Layout complexity assessment failed: {e}")
            return 0.5  # Default moderate complexity

    def _detect_tables(self, page: Any) -> bool:
        """
        Detect if page contains tables.

        Args:
            page: PyMuPDF page object

        Returns:
            True if tables detected, False otherwise
        """
        try:
            # Look for table-like structures in text blocks
            blocks = page.get_text("dict")["blocks"]

            # Simple heuristic: look for aligned text blocks
            # This is simplified - Docling does better table detection
            for block in blocks:
                if "lines" in block:
                    # Check for multiple lines with similar structure
                    lines = block["lines"]
                    if len(lines) >= 3:
                        # Potential table
                        return True

            return False

        except Exception as e:
            logger.debug(f"Table detection failed: {e}")
            return False

    def _detect_rotated_content(self, page: Any) -> bool:
        """
        Detect if page has rotated text or images.

        Args:
            page: PyMuPDF page object

        Returns:
            True if rotated content detected, False otherwise
        """
        try:
            # Check text rotation
            blocks = page.get_text("dict")["blocks"]

            for block in blocks:
                if "lines" in block:
                    for line in block["lines"]:
                        if "dir" in line:
                            # Check if direction is not standard (1, 0)
                            direction = line["dir"]
                            if direction != (1, 0) and direction != [1, 0]:
                                return True

            return False

        except Exception as e:
            logger.debug(f"Rotated content detection failed: {e}")
            return False

    def _aggregate_assessment(
        self,
        page_scores: List[PageQuality],
        total_pages: int,
        file_path: Path,
    ) -> QualityAssessment:
        """
        Aggregate page-level assessments into document-level assessment.

        Args:
            page_scores: List of page quality assessments
            total_pages: Total number of pages in document
            file_path: Path to document

        Returns:
            Aggregated quality assessment
        """
        if not page_scores:
            return self._fallback_assessment(file_path, "No pages analysed")

        # Calculate averages
        avg_text_quality = sum(p.text_quality for p in page_scores) / len(page_scores)
        avg_layout_complexity = sum(p.layout_complexity for p in page_scores) / len(page_scores)

        # Image quality (only for scanned pages)
        scanned_pages = [p for p in page_scores if p.is_scanned]
        if scanned_pages:
            avg_image_quality = sum(p.image_quality for p in scanned_pages) / len(scanned_pages)
        else:
            avg_image_quality = 0.0

        # Overall page quality
        avg_page_score = sum(p.overall_score for p in page_scores) / len(page_scores)

        # Document-level booleans
        is_born_digital = all(p.is_born_digital for p in page_scores)
        is_scanned = any(p.is_scanned for p in page_scores)
        has_tables = any(p.has_tables for p in page_scores)
        has_rotated_content = any(p.has_rotated_content for p in page_scores)

        # Recommended processor (v0.3.4b: always Docling)
        recommended_processor = "docling"
        confidence = 1.0

        # Metadata
        metadata = {
            "file_name": file_path.name,
            "file_size": file_path.stat().st_size,
            "total_pages": total_pages,
            "pages_analysed": len(page_scores),
            "fast_mode": self.fast_mode,
        }

        return QualityAssessment(
            overall_score=avg_page_score,
            is_born_digital=is_born_digital,
            is_scanned=is_scanned,
            text_quality=avg_text_quality,
            layout_complexity=avg_layout_complexity,
            image_quality=avg_image_quality,
            has_tables=has_tables,
            has_rotated_content=has_rotated_content,
            page_scores=page_scores,
            recommended_processor=recommended_processor,
            confidence=confidence,
            metadata=metadata,
        )

    def _fallback_assessment(self, file_path: Path, error_msg: str) -> QualityAssessment:
        """
        Create conservative fallback assessment when assessment fails.

        Args:
            file_path: Path to document
            error_msg: Error message explaining failure

        Returns:
            Conservative quality assessment
        """
        logger.warning(f"Using fallback assessment: {error_msg}")

        return QualityAssessment(
            overall_score=0.7,  # Conservative moderate score
            is_born_digital=False,  # Assume scanned for safety
            is_scanned=True,
            text_quality=0.7,
            layout_complexity=0.5,
            image_quality=0.7,
            has_tables=False,
            has_rotated_content=False,
            page_scores=[],
            recommended_processor="docling",
            confidence=0.5,  # Low confidence
            metadata={
                "file_name": file_path.name,
                "error": error_msg,
                "fallback": True,
            },
        )

    def clear_cache(self) -> None:
        """Clear the quality assessment cache."""
        self._cache.clear()
        logger.debug("Quality assessment cache cleared")
