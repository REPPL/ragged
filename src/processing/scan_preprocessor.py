"""Scan preprocessing for messy scanned documents (v0.4.9).

Handles preprocessing of "messy" scans before document processing:
- Detects input type (single file, folder of images, folder of PDFs, mixed)
- Sorts files intelligently (numeric, alphabetic, date-based)
- Converts images to PDF
- Applies OCR to image-only pages
- Preprocesses images (deskew, denoise, contrast adjustment)

Usage:
    >>> preprocessor = ScanPreprocessor()
    >>> result = preprocessor.preprocess(Path("~/scans/book-folder/"))
    >>> corrected_pdf = result.output_path

v0.4.9: Initial scan preprocessing implementation
"""
from __future__ import annotations


import logging
import re
from collections import defaultdict
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any

import numpy as np
from PIL import Image

from ragged.processing.ocr_engines import OCREngineSelector, PaddleOCREngine
from ragged.utils.logging import get_logger

logger = get_logger(__name__)


class InputType(Enum):
    """Type of input detected."""

    SINGLE_PDF = "single_pdf"  # Single PDF file
    SINGLE_IMAGE = "single_image"  # Single image file
    FOLDER_IMAGES = "folder_images"  # Folder containing only images
    FOLDER_PDFS = "folder_pdfs"  # Folder containing only PDFs
    FOLDER_MIXED = "folder_mixed"  # Folder with both images and PDFs


@dataclass
class PreprocessResult:
    """Result of scan preprocessing.

    Attributes:
        output_path: Path to preprocessed PDF
        input_type: Type of input detected
        num_files_processed: Number of input files processed
        ocr_applied: Whether OCR was applied
        preprocessing_applied: Whether image preprocessing was applied
        warnings: List of warning messages
        processing_time_seconds: Total processing time
    """

    output_path: Path
    input_type: InputType
    num_files_processed: int
    ocr_applied: bool
    preprocessing_applied: bool
    warnings: list[str]
    processing_time_seconds: float


class ScanPreprocessor:
    """Preprocessor for messy scanned documents.

    Handles:
        - Single PDF (pass through or apply OCR if needed)
        - Single image (convert to PDF)
        - Folder of images (sort, convert, merge)
        - Folder of PDFs (sort, merge)
        - Mixed folder (convert images, merge all)

    Image preprocessing:
        - Deskew (rotation correction)
        - Denoise (Gaussian blur)
        - Contrast adjustment (adaptive)
        - Binarization (optional)

    OCR:
        - Automatic OCR detection (image-only pages)
        - PaddleOCR for best accuracy on difficult scans
        - Quality-based OCR engine selection

    Example:
        >>> preprocessor = ScanPreprocessor(
        ...     apply_ocr=True,
        ...     preprocess_images=True,
        ...     ocr_language="eng"
        ... )
        >>> result = preprocessor.preprocess(Path("~/scans/book/"))
        >>> print(f"Preprocessed: {result.output_path}")
    """

    # Supported image formats
    IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".tiff", ".tif", ".bmp"}
    PDF_EXTENSION = ".pdf"

    def __init__(
        self,
        apply_ocr: bool = True,
        preprocess_images: bool = True,
        ocr_language: str = "eng",
        ocr_threshold: float = 0.70,
        deskew: bool = True,
        denoise: bool = True,
        auto_contrast: bool = True,
        prefer_gpu: bool = False,
    ) -> None:
        """Initialise scan preprocessor.

        Args:
            apply_ocr: Apply OCR to image-only pages
            preprocess_images: Apply image preprocessing (deskew, denoise, etc.)
            ocr_language: Language for OCR (ISO 639-2/3 code)
            ocr_threshold: Quality threshold for OCR engine selection
            deskew: Enable deskewing (rotation correction)
            denoise: Enable denoising (Gaussian blur)
            auto_contrast: Enable automatic contrast adjustment
            prefer_gpu: Prefer GPU for OCR if available
        """
        self.apply_ocr = apply_ocr
        self.preprocess_images = preprocess_images
        self.ocr_language = ocr_language
        self.ocr_threshold = ocr_threshold
        self.deskew_enabled = deskew
        self.denoise_enabled = denoise
        self.auto_contrast_enabled = auto_contrast
        self.prefer_gpu = prefer_gpu

        # Lazy-initialised OCR engine
        self._ocr_selector: OCREngineSelector | None = None

        logger.info(
            f"ScanPreprocessor initialised: "
            f"ocr={apply_ocr}, preprocess={preprocess_images}, lang={ocr_language}"
        )

    @property
    def ocr_selector(self) -> OCREngineSelector:
        """Get OCR engine selector (lazy initialisation)."""
        if self._ocr_selector is None:
            self._ocr_selector = OCREngineSelector(
                threshold=self.ocr_threshold,
                language=self.ocr_language,
                prefer_gpu=self.prefer_gpu,
            )
        return self._ocr_selector

    def preprocess(self, input_path: Path, output_path: Path | None = None) -> PreprocessResult:
        """Preprocess messy scans into clean PDF.

        Args:
            input_path: Single file or folder to preprocess
            output_path: Output PDF path (None = auto-generate in temp dir)

        Returns:
            Preprocessing result with output path and metadata

        Raises:
            ValueError: If input path doesn't exist or is unsupported
            RuntimeError: If preprocessing fails
        """
        import time

        start_time = time.time()
        warnings = []

        # Validate input
        if not input_path.exists():
            raise ValueError(f"Input path does not exist: {input_path}")

        # Detect input type
        input_type = self._detect_input_type(input_path)
        logger.info(f"Detected input type: {input_type.value}")

        # Process based on input type
        try:
            if input_type == InputType.SINGLE_PDF:
                result_path, num_files, ocr_applied, preproc_applied = self._process_single_pdf(
                    input_path, output_path
                )
            elif input_type == InputType.SINGLE_IMAGE:
                result_path, num_files, ocr_applied, preproc_applied = self._process_single_image(
                    input_path, output_path
                )
            elif input_type == InputType.FOLDER_IMAGES:
                result_path, num_files, ocr_applied, preproc_applied = self._process_image_folder(
                    input_path, output_path
                )
            elif input_type == InputType.FOLDER_PDFS:
                result_path, num_files, ocr_applied, preproc_applied = self._process_pdf_folder(
                    input_path, output_path
                )
            elif input_type == InputType.FOLDER_MIXED:
                result_path, num_files, ocr_applied, preproc_applied = self._process_mixed_folder(
                    input_path, output_path
                )
            else:
                raise ValueError(f"Unsupported input type: {input_type}")

            processing_time = time.time() - start_time

            logger.info(
                f"Preprocessing complete: {num_files} files processed, "
                f"OCR={ocr_applied}, preprocessing={preproc_applied}, "
                f"{processing_time:.2f}s"
            )

            return PreprocessResult(
                output_path=result_path,
                input_type=input_type,
                num_files_processed=num_files,
                ocr_applied=ocr_applied,
                preprocessing_applied=preproc_applied,
                warnings=warnings,
                processing_time_seconds=processing_time,
            )

        except Exception as e:
            logger.error(f"Preprocessing failed: {e}")
            raise RuntimeError(f"Scan preprocessing failed: {e}") from e

    def _detect_input_type(self, path: Path) -> InputType:
        """Detect type of input (file vs folder, images vs PDFs).

        Args:
            path: Input path

        Returns:
            Detected input type

        Raises:
            ValueError: If path is empty folder or contains no supported files
        """
        if path.is_file():
            # Single file
            ext = path.suffix.lower()
            if ext == self.PDF_EXTENSION:
                return InputType.SINGLE_PDF
            elif ext in self.IMAGE_EXTENSIONS:
                return InputType.SINGLE_IMAGE
            else:
                raise ValueError(f"Unsupported file type: {ext}")

        # Folder - scan contents
        files = [f for f in path.rglob("*") if f.is_file()]
        if not files:
            raise ValueError(f"Empty folder: {path}")

        # Count file types
        num_pdfs = sum(1 for f in files if f.suffix.lower() == self.PDF_EXTENSION)
        num_images = sum(1 for f in files if f.suffix.lower() in self.IMAGE_EXTENSIONS)

        if num_images > 0 and num_pdfs == 0:
            return InputType.FOLDER_IMAGES
        elif num_pdfs > 0 and num_images == 0:
            return InputType.FOLDER_PDFS
        elif num_pdfs > 0 and num_images > 0:
            return InputType.FOLDER_MIXED
        else:
            raise ValueError(f"No supported files found in folder: {path}")

    def _process_single_pdf(
        self, input_path: Path, output_path: Path | None
    ) -> tuple[Path, int, bool, bool]:
        """Process single PDF file.

        Args:
            input_path: Input PDF path
            output_path: Output PDF path (None = use input path)

        Returns:
            Tuple of (output_path, num_files, ocr_applied, preprocessing_applied)
        """
        # For single PDF, check if OCR needed
        ocr_applied = False
        preprocessing_applied = False

        if self.apply_ocr:
            # Check if PDF has text layer
            has_text = self._pdf_has_text_layer(input_path)
            if not has_text:
                logger.info("PDF has no text layer, applying OCR...")
                output_path = output_path or input_path.parent / f"{input_path.stem}_ocr.pdf"
                self._apply_ocr_to_pdf(input_path, output_path)
                ocr_applied = True
                return (output_path, 1, ocr_applied, preprocessing_applied)

        # No OCR needed, return original or copy
        if output_path and output_path != input_path:
            import shutil

            shutil.copy2(input_path, output_path)
            return (output_path, 1, ocr_applied, preprocessing_applied)
        else:
            return (input_path, 1, ocr_applied, preprocessing_applied)

    def _process_single_image(
        self, input_path: Path, output_path: Path | None
    ) -> tuple[Path, int, bool, bool]:
        """Process single image file.

        Args:
            input_path: Input image path
            output_path: Output PDF path

        Returns:
            Tuple of (output_path, num_files, ocr_applied, preprocessing_applied)
        """
        # Load image
        image = Image.open(input_path)

        # Preprocess if enabled
        preprocessing_applied = False
        if self.preprocess_images:
            image = self._preprocess_image(image)
            preprocessing_applied = True

        # Convert to PDF
        if output_path is None:
            output_path = input_path.parent / f"{input_path.stem}.pdf"

        self._image_to_pdf(image, output_path)

        # Apply OCR if enabled
        ocr_applied = False
        if self.apply_ocr:
            temp_ocr = output_path.parent / f"{output_path.stem}_ocr.pdf"
            self._apply_ocr_to_pdf(output_path, temp_ocr)
            output_path = temp_ocr
            ocr_applied = True

        return (output_path, 1, ocr_applied, preprocessing_applied)

    def _process_image_folder(
        self, input_path: Path, output_path: Path | None
    ) -> tuple[Path, int, bool, bool]:
        """Process folder containing only images.

        Args:
            input_path: Input folder path
            output_path: Output PDF path

        Returns:
            Tuple of (output_path, num_files, ocr_applied, preprocessing_applied)
        """
        # Find all images
        images = [f for f in input_path.rglob("*") if f.suffix.lower() in self.IMAGE_EXTENSIONS]

        # Sort files
        images = self._sort_files(images)

        logger.info(f"Found {len(images)} images, converting to PDF...")

        # Convert each image and merge
        with TemporaryDirectory() as tmpdir:
            temp_dir = Path(tmpdir)
            pdf_paths = []

            for i, img_path in enumerate(images):
                # Load and preprocess image
                image = Image.open(img_path)
                if self.preprocess_images:
                    image = self._preprocess_image(image)

                # Convert to PDF
                temp_pdf = temp_dir / f"page_{i:04d}.pdf"
                self._image_to_pdf(image, temp_pdf)
                pdf_paths.append(temp_pdf)

            # Merge PDFs
            if output_path is None:
                output_path = input_path / "merged_scan.pdf"

            self._merge_pdfs(pdf_paths, output_path)

        # Apply OCR if enabled
        ocr_applied = False
        if self.apply_ocr:
            temp_ocr = output_path.parent / f"{output_path.stem}_ocr.pdf"
            self._apply_ocr_to_pdf(output_path, temp_ocr)
            output_path = temp_ocr
            ocr_applied = True

        return (output_path, len(images), ocr_applied, self.preprocess_images)

    def _process_pdf_folder(
        self, input_path: Path, output_path: Path | None
    ) -> tuple[Path, int, bool, bool]:
        """Process folder containing only PDFs.

        Args:
            input_path: Input folder path
            output_path: Output PDF path

        Returns:
            Tuple of (output_path, num_files, ocr_applied, preprocessing_applied)
        """
        # Find all PDFs
        pdfs = [f for f in input_path.rglob("*") if f.suffix.lower() == self.PDF_EXTENSION]

        # Sort files
        pdfs = self._sort_files(pdfs)

        logger.info(f"Found {len(pdfs)} PDFs, merging...")

        # Merge PDFs
        if output_path is None:
            output_path = input_path / "merged_scan.pdf"

        self._merge_pdfs(pdfs, output_path)

        # Apply OCR if enabled
        ocr_applied = False
        if self.apply_ocr:
            has_text = self._pdf_has_text_layer(output_path)
            if not has_text:
                logger.info("Merged PDF has no text layer, applying OCR...")
                temp_ocr = output_path.parent / f"{output_path.stem}_ocr.pdf"
                self._apply_ocr_to_pdf(output_path, temp_ocr)
                output_path = temp_ocr
                ocr_applied = True

        return (output_path, len(pdfs), ocr_applied, False)

    def _process_mixed_folder(
        self, input_path: Path, output_path: Path | None
    ) -> tuple[Path, int, bool, bool]:
        """Process folder containing both images and PDFs.

        Args:
            input_path: Input folder path
            output_path: Output PDF path

        Returns:
            Tuple of (output_path, num_files, ocr_applied, preprocessing_applied)
        """
        # Find all files
        images = [f for f in input_path.rglob("*") if f.suffix.lower() in self.IMAGE_EXTENSIONS]
        pdfs = [f for f in input_path.rglob("*") if f.suffix.lower() == self.PDF_EXTENSION]

        # Sort all files together
        all_files = images + pdfs
        all_files = self._sort_files(all_files)

        logger.info(f"Found {len(images)} images and {len(pdfs)} PDFs, processing...")

        # Convert images to PDF first
        with TemporaryDirectory() as tmpdir:
            temp_dir = Path(tmpdir)
            pdf_paths = []

            for file_path in all_files:
                if file_path.suffix.lower() in self.IMAGE_EXTENSIONS:
                    # Convert image
                    image = Image.open(file_path)
                    if self.preprocess_images:
                        image = self._preprocess_image(image)
                    temp_pdf = temp_dir / f"{file_path.stem}.pdf"
                    self._image_to_pdf(image, temp_pdf)
                    pdf_paths.append(temp_pdf)
                else:
                    # Keep PDF as-is
                    pdf_paths.append(file_path)

            # Merge all PDFs
            if output_path is None:
                output_path = input_path / "merged_scan.pdf"

            self._merge_pdfs(pdf_paths, output_path)

        # Apply OCR if enabled
        ocr_applied = False
        if self.apply_ocr:
            has_text = self._pdf_has_text_layer(output_path)
            if not has_text:
                logger.info("Merged PDF has no text layer, applying OCR...")
                temp_ocr = output_path.parent / f"{output_path.stem}_ocr.pdf"
                self._apply_ocr_to_pdf(output_path, temp_ocr)
                output_path = temp_ocr
                ocr_applied = True

        return (output_path, len(all_files), ocr_applied, self.preprocess_images and len(images) > 0)

    def _sort_files(self, files: list[Path]) -> list[Path]:
        """Sort files intelligently (numeric, alphabetic, or date-based).

        Args:
            files: List of file paths

        Returns:
            Sorted list of file paths

        Sorting strategy:
            1. Numeric: scan_001.jpg, scan_002.jpg (natural sort)
            2. Alphabetic: If no numbers, sort alphabetically
            3. Date-based: If no clear naming, sort by modification time
        """
        # Try numeric sort first (natural sort)
        def natural_sort_key(path: Path) -> list[int | str]:
            """Generate natural sort key for path."""
            parts = []
            for part in re.split(r"(\d+)", path.stem):
                if part.isdigit():
                    parts.append(int(part))
                else:
                    parts.append(part.lower())
            return parts

        # Check if files have numbers
        has_numbers = any(re.search(r"\d+", f.stem) for f in files)

        if has_numbers:
            # Numeric natural sort
            return sorted(files, key=natural_sort_key)
        else:
            # Alphabetic or date-based
            # Try alphabetic first
            alpha_sorted = sorted(files, key=lambda f: f.stem.lower())

            # If names are very similar (like "scan", "scan", "scan"),
            # fall back to modification time
            unique_stems = {f.stem.lower() for f in files}
            if len(unique_stems) < len(files) * 0.5:  # More than 50% duplicates
                logger.info("Files have similar names, sorting by modification time...")
                return sorted(files, key=lambda f: f.stat().st_mtime)
            else:
                return alpha_sorted

    def _preprocess_image(self, image: Image.Image) -> Image.Image:
        """Preprocess image (deskew, denoise, contrast adjustment).

        Args:
            image: Input PIL Image

        Returns:
            Preprocessed PIL Image
        """
        # Convert to numpy array
        img_array = np.array(image)

        # Deskew (rotation correction)
        if self.deskew_enabled:
            img_array = self._deskew_image(img_array)

        # Denoise (Gaussian blur)
        if self.denoise_enabled:
            img_array = self._denoise_image(img_array)

        # Auto-contrast
        if self.auto_contrast_enabled:
            img_array = self._adjust_contrast(img_array)

        return Image.fromarray(img_array)

    def _deskew_image(self, image: np.ndarray) -> np.ndarray:
        """Deskew image (correct rotation).

        Args:
            image: Input image array

        Returns:
            Deskewed image array
        """
        try:
            from skimage import transform
            from skimage.feature import canny
            from skimage.transform import hough_line, hough_line_peaks

            # Convert to grayscale if needed
            if len(image.shape) == 3:
                from skimage.color import rgb2gray

                gray = rgb2gray(image)
            else:
                gray = image

            # Edge detection
            edges = canny(gray)

            # Hough transform to find lines
            h, theta, d = hough_line(edges)

            # Find most prominent lines
            _, angles, _ = hough_line_peaks(h, theta, d, num_peaks=10)

            # Calculate median angle
            if len(angles) > 0:
                angle_deg = np.median(np.degrees(angles))

                # Correct angle (if > 45°, it's the perpendicular)
                if angle_deg > 45:
                    angle_deg -= 90
                elif angle_deg < -45:
                    angle_deg += 90

                # Only deskew if angle is significant (> 0.5°)
                if abs(angle_deg) > 0.5:
                    logger.debug(f"Deskewing by {angle_deg:.2f}°")
                    rotated = transform.rotate(image, angle_deg, resize=True, mode="edge")
                    # Convert back to uint8
                    return (rotated * 255).astype(np.uint8) if rotated.max() <= 1 else rotated.astype(np.uint8)

            return image

        except Exception as e:
            logger.warning(f"Deskew failed, using original image: {e}")
            return image

    def _denoise_image(self, image: np.ndarray) -> np.ndarray:
        """Denoise image using Gaussian blur.

        Args:
            image: Input image array

        Returns:
            Denoised image array
        """
        try:
            import cv2

            # Apply Gaussian blur (kernel size 3x3)
            denoised = cv2.GaussianBlur(image, (3, 3), 0)
            logger.debug("Applied Gaussian denoising")
            return denoised

        except Exception as e:
            logger.warning(f"Denoise failed, using original image: {e}")
            return image

    def _adjust_contrast(self, image: np.ndarray) -> np.ndarray:
        """Adjust image contrast automatically.

        Args:
            image: Input image array

        Returns:
            Contrast-adjusted image array
        """
        try:
            import cv2

            # Convert to LAB color space
            if len(image.shape) == 3:
                lab = cv2.cvtColor(image, cv2.COLOR_RGB2LAB)
                l, a, b = cv2.split(lab)

                # Apply CLAHE (Contrast Limited Adaptive Histogram Equalisation)
                clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
                l = clahe.apply(l)

                # Merge and convert back
                lab = cv2.merge([l, a, b])
                adjusted = cv2.cvtColor(lab, cv2.COLOR_LAB2RGB)
            else:
                # Grayscale: apply CLAHE directly
                clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
                adjusted = clahe.apply(image)

            logger.debug("Applied adaptive contrast adjustment")
            return adjusted

        except Exception as e:
            logger.warning(f"Contrast adjustment failed, using original image: {e}")
            return image

    def _image_to_pdf(self, image: Image.Image, output_path: Path) -> None:
        """Convert PIL Image to PDF.

        Args:
            image: Input PIL Image
            output_path: Output PDF path
        """
        try:
            import img2pdf

            # Convert image to bytes
            img_bytes = image.tobytes()

            # Create PDF
            with open(output_path, "wb") as f:
                # img2pdf requires image in bytes or file path
                # Save temporarily
                temp_img = output_path.parent / f"{output_path.stem}_temp.png"
                image.save(temp_img)
                f.write(img2pdf.convert(str(temp_img)))
                temp_img.unlink()  # Clean up

            logger.debug(f"Converted image to PDF: {output_path}")

        except Exception as e:
            logger.error(f"Image to PDF conversion failed: {e}")
            # Fallback: use PIL's built-in PDF save
            image.save(output_path, "PDF")

    def _merge_pdfs(self, pdf_paths: list[Path], output_path: Path) -> None:
        """Merge multiple PDFs into single PDF.

        Args:
            pdf_paths: List of PDF paths to merge
            output_path: Output merged PDF path
        """
        try:
            import pymupdf

            # Create new PDF
            merged_pdf = pymupdf.open()

            # Append each PDF
            for pdf_path in pdf_paths:
                with pymupdf.open(pdf_path) as pdf:
                    merged_pdf.insert_pdf(pdf)

            # Save merged PDF
            merged_pdf.save(output_path)
            merged_pdf.close()

            logger.info(f"Merged {len(pdf_paths)} PDFs into {output_path}")

        except Exception as e:
            logger.error(f"PDF merge failed: {e}")
            raise RuntimeError(f"Failed to merge PDFs: {e}") from e

    def _pdf_has_text_layer(self, pdf_path: Path) -> bool:
        """Check if PDF has embedded text layer.

        Args:
            pdf_path: PDF file path

        Returns:
            True if PDF has text, False if image-only
        """
        try:
            import pymupdf

            with pymupdf.open(pdf_path) as pdf:
                # Check first few pages for text
                for page_num in range(min(3, len(pdf))):
                    page = pdf[page_num]
                    text = page.get_text().strip()
                    if len(text) > 50:  # Has substantial text
                        return True

            return False

        except Exception as e:
            logger.warning(f"Failed to check PDF text layer: {e}")
            return False  # Assume no text if check fails

    def _apply_ocr_to_pdf(self, input_pdf: Path, output_pdf: Path) -> None:
        """Apply OCR to PDF pages without text layer.

        Args:
            input_pdf: Input PDF path
            output_pdf: Output PDF path with OCR text layer
        """
        logger.info(f"Applying OCR to PDF: {input_pdf}")

        try:
            import pymupdf
            from pdf2image import convert_from_path

            # Use PaddleOCR for best accuracy on scanned documents
            ocr_engine = PaddleOCREngine(
                language=self.ocr_language,
                use_angle_cls=True,
                use_gpu=self.prefer_gpu,
            )

            # Convert PDF pages to images
            images = convert_from_path(input_pdf, dpi=300)

            # Create new PDF with OCR text
            merged_pdf = pymupdf.open()

            for i, image in enumerate(images):
                logger.debug(f"OCR processing page {i + 1}/{len(images)}")

                # Run OCR
                ocr_result = ocr_engine.extract_text(image)

                # Create PDF page with image and text layer
                # Convert PIL Image to PyMuPDF compatible format
                img_bytes = image.tobytes()
                width, height = image.size

                # Create new page
                page = merged_pdf.new_page(width=width, height=height)

                # Insert image
                temp_img = output_pdf.parent / f"temp_page_{i}.png"
                image.save(temp_img)
                page.insert_image(page.rect, filename=str(temp_img))
                temp_img.unlink()

                # Add OCR text as invisible layer (for searchability)
                if ocr_result.text:
                    # Insert text blocks with bounding boxes
                    if ocr_result.bounding_boxes:
                        for bbox, text_block in zip(
                            ocr_result.bounding_boxes,
                            ocr_result.text.split("\n")
                        ):
                            rect = pymupdf.Rect(
                                bbox.x,
                                bbox.y,
                                bbox.x + bbox.width,
                                bbox.y + bbox.height
                            )
                            # Insert as invisible text for search
                            page.insert_textbox(
                                rect,
                                text_block,
                                color=(1, 1, 1),  # White (invisible on white bg)
                                fontsize=10,
                            )

            # Save OCR'd PDF
            merged_pdf.save(output_pdf)
            merged_pdf.close()

            logger.info(f"OCR complete: {output_pdf}")

        except Exception as e:
            logger.error(f"OCR failed: {e}")
            raise RuntimeError(f"Failed to apply OCR to PDF: {e}") from e
