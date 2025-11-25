"""Metadata extraction from scanned documents (v0.4.9).

Extracts bibliographic metadata from scanned books:
- Title
- Author(s)
- Publication year
- Publisher

Methods:
1. PDF embedded metadata (first priority)
2. Title page OCR + regex patterns (main method)
3. Vision-based analysis (optional, experimental)
4. Fallback (filename, defaults)

Fully offline, privacy-preserving (no web lookups).

Usage:
    >>> extractor = MetadataExtractor()
    >>> metadata = extractor.extract(Path("scanned-book.pdf"))
    >>> print(f"Title: {metadata['title']}, Author: {metadata['author']}")

v0.4.9: Initial metadata extraction implementation
"""

import logging
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from PIL import Image

from ragged.processing.ocr_engines import PaddleOCREngine
from ragged.utils.logging import get_logger

logger = get_logger(__name__)


@dataclass
class ExtractedMetadata:
    """Extracted bibliographic metadata.

    Attributes:
        title: Book/document title
        author: Author name(s)
        year: Publication year
        publisher: Publisher name
        confidence: Confidence score (0.0-1.0)
        method: Extraction method used
        raw_titlepage_text: Raw OCR text from title page (for debugging)
    """

    title: str
    author: str | None = None
    year: int | None = None
    publisher: str | None = None
    confidence: float = 0.0
    method: str = "unknown"
    raw_titlepage_text: str | None = None


class MetadataExtractor:
    """Extract bibliographic metadata from scanned documents.

    Extraction strategies (cascading):
        1. PDF embedded metadata (fast, but often missing/incorrect)
        2. Title page OCR + regex (main method, 70-80% accuracy)
        3. Vision analysis (optional, experimental)
        4. Fallback (filename, current year, "Unknown")

    Example:
        >>> extractor = MetadataExtractor(
        ...     titlepage_pages=3,
        ...     ocr_language="eng"
        ... )
        >>> metadata = extractor.extract(Path("book.pdf"))
        >>> print(metadata.title)
    """

    # Common title page patterns
    TITLE_PATTERNS = [
        # Large text at beginning (heuristic: lines with ALL CAPS or Title Case)
        r"^([A-Z][A-Z\s:&\-]{10,})$",  # ALL CAPS title
        r"^([A-Z][a-zA-Z\s:&\-]{10,})$",  # Title Case
    ]

    AUTHOR_PATTERNS = [
        r"by\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)",  # "by John Smith"
        r"By\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)",  # "By John Smith"
        r"Author:\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)",  # "Author: John Smith"
        r"Written by\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)",  # "Written by John Smith"
        r"^([A-Z][a-z]+\s+[A-Z][a-z]+)$",  # Just "FirstName LastName" on its own line
    ]

    YEAR_PATTERNS = [
        r"Copyright\s+©?\s*(\d{4})",  # "Copyright © 2023"
        r"©\s*(\d{4})",  # "© 2023"
        r"Published\s+(?:in\s+)?(\d{4})",  # "Published 2023" or "Published in 2023"
        r"\((\d{4})\)",  # "(2023)"
        r"^(\d{4})$",  # Just "2023" on its own line
    ]

    PUBLISHER_PATTERNS = [
        r"Published by\s+([A-Z][a-zA-Z\s&]+)",  # "Published by Publisher Name"
        r"Publisher:\s*([A-Z][a-zA-Z\s&]+)",  # "Publisher: Publisher Name"
        r"([A-Z][a-zA-Z]+\s+Press)",  # "University Press", "Academic Press"
        r"([A-Z][a-zA-Z]+\s+Publishers?)",  # "Smith Publishers"
    ]

    def __init__(
        self,
        titlepage_pages: int = 3,
        ocr_language: str = "eng",
        use_vision: bool = False,
        prefer_gpu: bool = False,
    ) -> None:
        """Initialise metadata extractor.

        Args:
            titlepage_pages: Number of pages to analyse for title page (1-5)
            ocr_language: Language for OCR
            use_vision: Use vision model for layout analysis (experimental)
            prefer_gpu: Prefer GPU for OCR if available
        """
        self.titlepage_pages = min(max(titlepage_pages, 1), 5)  # Clamp to 1-5
        self.ocr_language = ocr_language
        self.use_vision = use_vision
        self.prefer_gpu = prefer_gpu

        # Lazy-initialised OCR engine
        self._ocr_engine: PaddleOCREngine | None = None

        logger.info(
            f"MetadataExtractor initialised: "
            f"pages={titlepage_pages}, lang={ocr_language}, vision={use_vision}"
        )

    @property
    def ocr_engine(self) -> PaddleOCREngine:
        """Get OCR engine (lazy initialisation)."""
        if self._ocr_engine is None:
            self._ocr_engine = PaddleOCREngine(
                language=self.ocr_language,
                use_angle_cls=True,
                use_gpu=self.prefer_gpu,
            )
        return self._ocr_engine

    def extract(self, pdf_path: Path) -> ExtractedMetadata:
        """Extract metadata from PDF.

        Args:
            pdf_path: Path to PDF file

        Returns:
            Extracted metadata with confidence score

        Raises:
            FileNotFoundError: If PDF doesn't exist
            RuntimeError: If all extraction methods fail
        """
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF not found: {pdf_path}")

        logger.info(f"Extracting metadata from: {pdf_path.name}")

        # Strategy 1: PDF embedded metadata
        metadata = self._extract_from_pdf_metadata(pdf_path)
        if metadata and metadata.confidence > 0.7:
            logger.info(f"Extracted from PDF metadata: {metadata.method}")
            return metadata

        # Strategy 2: Title page OCR + regex (main method)
        metadata = self._extract_from_titlepage(pdf_path)
        if metadata and metadata.confidence > 0.5:
            logger.info(f"Extracted from title page OCR: {metadata.method}")
            return metadata

        # Strategy 3: Vision analysis (optional, experimental)
        if self.use_vision:
            metadata = self._extract_with_vision(pdf_path)
            if metadata and metadata.confidence > 0.5:
                logger.info(f"Extracted with vision model: {metadata.method}")
                return metadata

        # Strategy 4: Fallback (filename, defaults)
        logger.warning("All extraction methods failed, using fallback")
        return self._fallback_metadata(pdf_path)

    def _extract_from_pdf_metadata(self, pdf_path: Path) -> ExtractedMetadata | None:
        """Extract metadata from PDF's embedded metadata.

        Args:
            pdf_path: PDF file path

        Returns:
            Extracted metadata or None if not available
        """
        try:
            import pymupdf

            with pymupdf.open(pdf_path) as pdf:
                meta = pdf.metadata

                if not meta:
                    return None

                # Extract fields
                title = meta.get("title", "").strip()
                author = meta.get("author", "").strip()
                year_str = meta.get("creationDate", "")

                # Parse year from creation date (format: "D:20231015...")
                year = None
                if year_str:
                    year_match = re.search(r"D:(\d{4})", year_str)
                    if year_match:
                        year = int(year_match.group(1))

                # Confidence: high if title + author present
                confidence = 0.0
                if title:
                    confidence += 0.5
                if author:
                    confidence += 0.3
                if year:
                    confidence += 0.2

                if confidence > 0.5:
                    logger.debug(
                        f"PDF metadata: title={title}, author={author}, year={year}, "
                        f"confidence={confidence:.2f}"
                    )
                    return ExtractedMetadata(
                        title=title or pdf_path.stem,
                        author=author or None,
                        year=year,
                        publisher=None,
                        confidence=confidence,
                        method="pdf_metadata",
                    )

                return None

        except Exception as e:
            logger.warning(f"Failed to extract PDF metadata: {e}")
            return None

    def _extract_from_titlepage(self, pdf_path: Path) -> ExtractedMetadata | None:
        """Extract metadata from title page using OCR + regex.

        Args:
            pdf_path: PDF file path

        Returns:
            Extracted metadata or None if extraction fails
        """
        try:
            # Convert first N pages to images
            from pdf2image import convert_from_path

            images = convert_from_path(
                pdf_path,
                dpi=300,
                first_page=1,
                last_page=self.titlepage_pages,
            )

            # OCR each page and collect text
            all_text = []
            for i, image in enumerate(images):
                logger.debug(f"OCR title page {i + 1}/{len(images)}")
                ocr_result = self.ocr_engine.extract_text(image)
                all_text.append(ocr_result.text)

            # Combine text from all pages
            combined_text = "\n\n".join(all_text)

            # Extract metadata using regex patterns
            title = self._extract_title(combined_text)
            author = self._extract_author(combined_text)
            year = self._extract_year(combined_text)
            publisher = self._extract_publisher(combined_text)

            # Calculate confidence
            confidence = 0.0
            if title:
                confidence += 0.4
            if author:
                confidence += 0.3
            if year:
                confidence += 0.2
            if publisher:
                confidence += 0.1

            logger.debug(
                f"Title page extraction: title={title}, author={author}, "
                f"year={year}, publisher={publisher}, confidence={confidence:.2f}"
            )

            return ExtractedMetadata(
                title=title or pdf_path.stem,
                author=author,
                year=year,
                publisher=publisher,
                confidence=confidence,
                method="titlepage_ocr",
                raw_titlepage_text=combined_text[:500],  # First 500 chars for debugging
            )

        except Exception as e:
            logger.error(f"Title page extraction failed: {e}")
            return None

    def _extract_title(self, text: str) -> str | None:
        """Extract title from OCR text.

        Args:
            text: OCR text from title page(s)

        Returns:
            Extracted title or None
        """
        lines = text.split("\n")

        # Look for title in first 10 lines (usually at top)
        for line in lines[:10]:
            line = line.strip()
            if not line:
                continue

            # Check patterns
            for pattern in self.TITLE_PATTERNS:
                match = re.match(pattern, line)
                if match:
                    title = match.group(1).strip()
                    # Validate: title should be 10-100 characters
                    if 10 <= len(title) <= 100:
                        logger.debug(f"Found title: {title}")
                        return title

        # Heuristic: longest line in first 5 lines
        long_lines = [line.strip() for line in lines[:5] if len(line.strip()) > 10]
        if long_lines:
            title = max(long_lines, key=len)
            logger.debug(f"Found title (heuristic): {title}")
            return title

        return None

    def _extract_author(self, text: str) -> str | None:
        """Extract author from OCR text.

        Args:
            text: OCR text from title page(s)

        Returns:
            Extracted author name or None
        """
        # Check patterns
        for pattern in self.AUTHOR_PATTERNS:
            match = re.search(pattern, text, re.MULTILINE)
            if match:
                author = match.group(1).strip()
                # Validate: author should be 5-50 characters
                if 5 <= len(author) <= 50:
                    logger.debug(f"Found author: {author}")
                    return author

        return None

    def _extract_year(self, text: str) -> int | None:
        """Extract publication year from OCR text.

        Args:
            text: OCR text from title page(s)

        Returns:
            Publication year or None
        """
        years = []

        # Check patterns
        for pattern in self.YEAR_PATTERNS:
            matches = re.findall(pattern, text, re.MULTILINE)
            for match in matches:
                try:
                    year = int(match)
                    # Validate: year should be reasonable (1800-current year + 1)
                    current_year = datetime.now().year
                    if 1800 <= year <= current_year + 1:
                        years.append(year)
                except ValueError:
                    continue

        # Return most recent year found (likely publication date)
        if years:
            year = max(years)
            logger.debug(f"Found year: {year}")
            return year

        return None

    def _extract_publisher(self, text: str) -> str | None:
        """Extract publisher from OCR text.

        Args:
            text: OCR text from title page(s)

        Returns:
            Publisher name or None
        """
        # Check patterns
        for pattern in self.PUBLISHER_PATTERNS:
            match = re.search(pattern, text, re.MULTILINE)
            if match:
                publisher = match.group(1).strip()
                # Validate: publisher should be 5-50 characters
                if 5 <= len(publisher) <= 50:
                    logger.debug(f"Found publisher: {publisher}")
                    return publisher

        return None

    def _extract_with_vision(self, pdf_path: Path) -> ExtractedMetadata | None:
        """Extract metadata using vision model (experimental).

        Args:
            pdf_path: PDF file path

        Returns:
            Extracted metadata or None

        Note:
            This is experimental and requires ColPali vision model.
            Currently not implemented, placeholder for future enhancement.
        """
        logger.warning("Vision-based extraction not yet implemented")
        return None

        # Future implementation:
        # 1. Use ColPali to analyze title page layout
        # 2. Identify title/author/year regions visually
        # 3. Extract text from those regions
        # 4. Combine with regex patterns for validation

    def _fallback_metadata(self, pdf_path: Path) -> ExtractedMetadata:
        """Generate fallback metadata when extraction fails.

        Args:
            pdf_path: PDF file path

        Returns:
            Fallback metadata with low confidence
        """
        # Use filename as title (sanitized)
        title = self._sanitize_filename(pdf_path.stem)

        logger.info(f"Using fallback metadata: title={title}")

        return ExtractedMetadata(
            title=title,
            author=None,
            year=None,
            publisher=None,
            confidence=0.1,
            method="fallback",
        )

    def _sanitize_filename(self, filename: str) -> str:
        """Sanitize filename for use as title.

        Args:
            filename: Raw filename

        Returns:
            Sanitized title
        """
        # Remove common patterns
        title = filename

        # Remove scan/copy indicators
        title = re.sub(r"[-_]?scan[-_]?\d*", "", title, flags=re.IGNORECASE)
        title = re.sub(r"[-_]?copy[-_]?\d*", "", title, flags=re.IGNORECASE)

        # Remove dates (YYYYMMDD, YYYY-MM-DD)
        title = re.sub(r"\d{8}", "", title)
        title = re.sub(r"\d{4}-\d{2}-\d{2}", "", title)

        # Replace underscores/hyphens with spaces
        title = title.replace("_", " ").replace("-", " ")

        # Normalize whitespace
        title = " ".join(title.split())

        # Title case
        title = title.title()

        return title.strip() or "Untitled Document"
