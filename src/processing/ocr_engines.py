"""OCR engine abstraction and implementations for ragged (v0.4.9).

Provides unified interface for multiple OCR engines with automatic fallback
based on document quality assessment.

Supported engines:
- EasyOCR: Fast, 90-95% accuracy (Docling default)
- PaddleOCR: State-of-the-art, 95-98% accuracy (fallback for difficult docs)

Architecture:
    BaseOCREngine (ABC)
    ├── EasyOCREngine (via Docling)
    └── PaddleOCREngine (fallback)

    OCREngineSelector (quality-based routing)

Usage:
    >>> from ragged.processing.ocr_engines import OCREngineSelector
    >>> selector = OCREngineSelector()
    >>> engine = selector.select(quality_assessment)
    >>> result = engine.extract_text(image)

v0.4.9: Initial OCR engine abstraction
"""

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image

logger = logging.getLogger(__name__)


@dataclass
class BoundingBox:
    """Bounding box coordinates for detected text."""

    x: int
    y: int
    width: int
    height: int
    confidence: float


@dataclass
class OCRResult:
    """Result from OCR text extraction.

    Attributes:
        text: Extracted text content
        confidence: Overall confidence score (0.0-1.0)
        bounding_boxes: Optional bounding boxes for each detected text region
        language: Detected language code (e.g., 'eng', 'fra')
        engine: OCR engine used ('easyocr', 'paddleocr', etc.)
    """

    text: str
    confidence: float
    bounding_boxes: list[BoundingBox] | None = None
    language: str = "eng"
    engine: str = "unknown"


class BaseOCREngine(ABC):
    """Abstract base class for OCR engines.

    All OCR engines must implement the extract_text method.
    """

    def __init__(self, language: str = "eng", **kwargs: Any) -> None:
        """Initialise OCR engine.

        Args:
            language: Language code (ISO 639-2/3, e.g., 'eng', 'fra')
            **kwargs: Engine-specific configuration
        """
        self.language = language
        self.config = kwargs

    @abstractmethod
    def extract_text(self, image: Image.Image | Path | np.ndarray) -> OCRResult:
        """Extract text from image using OCR.

        Args:
            image: Input image (PIL Image, file path, or numpy array)

        Returns:
            OCR result with extracted text and metadata

        Raises:
            RuntimeError: If OCR engine not available or extraction fails
        """
        pass

    def _load_image(self, image: Image.Image | Path | np.ndarray) -> Image.Image:
        """Load image from various formats.

        Args:
            image: Input in various formats

        Returns:
            PIL Image

        Raises:
            ValueError: If image format not supported
        """
        if isinstance(image, Image.Image):
            return image
        elif isinstance(image, (str, Path)):
            return Image.open(image)
        elif isinstance(image, np.ndarray):
            return Image.fromarray(image)
        else:
            raise ValueError(f"Unsupported image type: {type(image)}")

    def _convert_to_rgb(self, image: Image.Image) -> Image.Image:
        """Convert image to RGB format (required by most OCR engines).

        Args:
            image: Input image

        Returns:
            RGB image
        """
        if image.mode != "RGB":
            return image.convert("RGB")
        return image


class EasyOCREngine(BaseOCREngine):
    """EasyOCR engine (Docling's default OCR backend).

    Fast deep learning-based OCR with 90-95% accuracy.
    Supported by Docling's automatic OCR selection.

    Performance:
        - 1.6s/page (GPU)
        - 5s/page (Apple Silicon)
        - 13s/page (x86 CPU)

    Accuracy: 90-95% on clean documents

    Languages: 80+ supported
    """

    def __init__(self, language: str = "eng", gpu: bool = True, **kwargs: Any) -> None:
        """Initialise EasyOCR engine.

        Args:
            language: Language code (e.g., 'en', 'fr', 'de')
            gpu: Use GPU acceleration if available
            **kwargs: Additional EasyOCR configuration
        """
        super().__init__(language, **kwargs)
        self.gpu = gpu
        self._reader: Any | None = None

    def extract_text(self, image: Image.Image | Path | np.ndarray) -> OCRResult:
        """Extract text using EasyOCR.

        Args:
            image: Input image

        Returns:
            OCR result with text and confidence

        Raises:
            RuntimeError: If EasyOCR not available
        """
        # Lazy import (avoid startup overhead)
        if self._reader is None:
            try:
                import easyocr
            except ImportError as e:
                raise RuntimeError(
                    "EasyOCR not installed. Install with: pip install easyocr"
                ) from e

            # Initialise reader (cached for subsequent calls)
            self._reader = easyocr.Reader([self.language], gpu=self.gpu)
            logger.info(f"EasyOCR initialised: language={self.language}, gpu={self.gpu}")

        # Load and preprocess image
        img = self._load_image(image)
        img = self._convert_to_rgb(img)

        # Run OCR
        results = self._reader.readtext(np.array(img))

        # Extract text and confidence
        if not results:
            return OCRResult(text="", confidence=0.0, engine="easyocr", language=self.language)

        # Combine all detected text regions
        text_blocks = []
        bboxes = []
        confidences = []

        for bbox, text, conf in results:
            text_blocks.append(text)
            confidences.append(conf)

            # Convert bbox to BoundingBox (EasyOCR returns 4 points)
            x_coords = [p[0] for p in bbox]
            y_coords = [p[1] for p in bbox]
            bboxes.append(
                BoundingBox(
                    x=int(min(x_coords)),
                    y=int(min(y_coords)),
                    width=int(max(x_coords) - min(x_coords)),
                    height=int(max(y_coords) - min(y_coords)),
                    confidence=conf,
                )
            )

        # Combine text with newlines
        full_text = "\n".join(text_blocks)
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0

        logger.debug(
            f"EasyOCR extracted {len(text_blocks)} text blocks, "
            f"confidence: {avg_confidence:.2f}"
        )

        return OCRResult(
            text=full_text,
            confidence=avg_confidence,
            bounding_boxes=bboxes,
            language=self.language,
            engine="easyocr",
        )


class PaddleOCREngine(BaseOCREngine):
    """PaddleOCR engine (state-of-the-art offline OCR).

    Most accurate OCR engine for difficult documents (95-98% accuracy).
    Features:
        - Slanted bounding boxes (handles rotated/skewed text)
        - PP-StructureV3 (tables, formulas, handwriting)
        - 97.9% table extraction accuracy

    Performance:
        - 5-8s/page (GPU)
        - 15-20s/page (CPU)

    Accuracy: 95-98% on messy scans

    Languages: 80+ supported

    Use as fallback for documents with quality score < 0.70.
    """

    def __init__(
        self,
        language: str = "en",
        use_angle_cls: bool = True,
        use_gpu: bool = False,
        **kwargs: Any,
    ) -> None:
        """Initialise PaddleOCR engine.

        Args:
            language: Language code (e.g., 'en', 'french', 'german')
            use_angle_cls: Enable text angle classification (rotation detection)
            use_gpu: Use GPU acceleration (requires CUDA/ROCm)
            **kwargs: Additional PaddleOCR configuration
        """
        super().__init__(language, **kwargs)
        self.use_angle_cls = use_angle_cls
        self.use_gpu = use_gpu
        self._ocr: Any | None = None

    def extract_text(self, image: Image.Image | Path | np.ndarray) -> OCRResult:
        """Extract text using PaddleOCR.

        Args:
            image: Input image

        Returns:
            OCR result with text, confidence, and bounding boxes

        Raises:
            RuntimeError: If PaddleOCR not installed
        """
        # Lazy import (avoid startup overhead)
        if self._ocr is None:
            try:
                from paddleocr import PaddleOCR
            except ImportError as e:
                raise RuntimeError(
                    "PaddleOCR not installed. Install with: pip install paddleocr paddlepaddle"
                ) from e

            # Initialise OCR (cached for subsequent calls)
            self._ocr = PaddleOCR(
                lang=self.language,
                use_angle_cls=self.use_angle_cls,
                use_gpu=self.use_gpu,
                show_log=False,  # Suppress verbose logging
            )
            logger.info(
                f"PaddleOCR initialised: language={self.language}, "
                f"gpu={self.use_gpu}, angle_cls={self.use_angle_cls}"
            )

        # Load and preprocess image
        img = self._load_image(image)
        img = self._convert_to_rgb(img)

        # Run OCR (returns list of [bbox, (text, confidence)])
        result = self._ocr.ocr(np.array(img), cls=self.use_angle_cls)

        # Handle empty result
        if not result or not result[0]:
            return OCRResult(text="", confidence=0.0, engine="paddleocr", language=self.language)

        # Extract text blocks and metadata
        text_blocks = []
        bboxes = []
        confidences = []

        for line in result[0]:
            bbox_points, (text, conf) = line
            text_blocks.append(text)
            confidences.append(conf)

            # Convert bbox to BoundingBox (PaddleOCR returns 4 corner points)
            x_coords = [p[0] for p in bbox_points]
            y_coords = [p[1] for p in bbox_points]
            bboxes.append(
                BoundingBox(
                    x=int(min(x_coords)),
                    y=int(min(y_coords)),
                    width=int(max(x_coords) - min(x_coords)),
                    height=int(max(y_coords) - min(y_coords)),
                    confidence=conf,
                )
            )

        # Combine text with newlines
        full_text = "\n".join(text_blocks)
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0

        logger.debug(
            f"PaddleOCR extracted {len(text_blocks)} text blocks, "
            f"confidence: {avg_confidence:.2f}"
        )

        return OCRResult(
            text=full_text,
            confidence=avg_confidence,
            bounding_boxes=bboxes,
            language=self.language,
            engine="paddleocr",
        )


class OCREngineSelector:
    """Automatic OCR engine selection based on document quality.

    Routes documents to appropriate OCR engine:
        - High quality (>= 0.70): EasyOCR (fast, 90-95% accuracy)
        - Low quality (< 0.70): PaddleOCR (slow, 95-98% accuracy)

    Usage:
        >>> selector = OCREngineSelector()
        >>> engine = selector.select(quality_assessment)
        >>> result = engine.extract_text(image)
    """

    def __init__(
        self,
        threshold: float = 0.70,
        language: str = "eng",
        prefer_gpu: bool = True,
    ) -> None:
        """Initialise OCR engine selector.

        Args:
            threshold: Quality threshold for engine selection
                       (< threshold → PaddleOCR, >= threshold → EasyOCR)
            language: Default language for OCR engines
            prefer_gpu: Use GPU acceleration if available
        """
        self.threshold = threshold
        self.language = language
        self.prefer_gpu = prefer_gpu

        # Lazy-initialised engines (avoid startup overhead)
        self._easyocr_engine: EasyOCREngine | None = None
        self._paddleocr_engine: PaddleOCREngine | None = None

        logger.info(
            f"OCREngineSelector initialised: threshold={threshold}, language={language}"
        )

    def select(self, quality_score: float) -> BaseOCREngine:
        """Select appropriate OCR engine based on quality score.

        Args:
            quality_score: Document quality score (0.0-1.0)
                          Higher score = better quality

        Returns:
            Selected OCR engine

        Selection logic:
            - quality >= 0.70: EasyOCR (fast, good accuracy)
            - quality < 0.70: PaddleOCR (slow, best accuracy)
        """
        if quality_score >= self.threshold:
            # High quality → EasyOCR (fast path)
            if self._easyocr_engine is None:
                self._easyocr_engine = EasyOCREngine(
                    language=self.language,
                    gpu=self.prefer_gpu,
                )
            logger.info(
                f"Selected EasyOCR (quality={quality_score:.2f} >= {self.threshold:.2f})"
            )
            return self._easyocr_engine
        else:
            # Low quality → PaddleOCR (accuracy path)
            if self._paddleocr_engine is None:
                # Map language codes (EasyOCR uses 'en', PaddleOCR uses 'en')
                paddle_lang = self._map_language_code(self.language)
                self._paddleocr_engine = PaddleOCREngine(
                    language=paddle_lang,
                    use_angle_cls=True,  # Enable rotation detection
                    use_gpu=self.prefer_gpu,
                )
            logger.info(
                f"Selected PaddleOCR (quality={quality_score:.2f} < {self.threshold:.2f})"
            )
            return self._paddleocr_engine

    def select_by_name(self, engine_name: str) -> BaseOCREngine:
        """Select OCR engine by name (override automatic selection).

        Args:
            engine_name: Engine name ('easyocr' or 'paddleocr')

        Returns:
            Selected OCR engine

        Raises:
            ValueError: If engine name not recognised
        """
        if engine_name == "easyocr":
            if self._easyocr_engine is None:
                self._easyocr_engine = EasyOCREngine(
                    language=self.language,
                    gpu=self.prefer_gpu,
                )
            return self._easyocr_engine
        elif engine_name == "paddleocr":
            if self._paddleocr_engine is None:
                paddle_lang = self._map_language_code(self.language)
                self._paddleocr_engine = PaddleOCREngine(
                    language=paddle_lang,
                    use_angle_cls=True,
                    use_gpu=self.prefer_gpu,
                )
            return self._paddleocr_engine
        else:
            raise ValueError(
                f"Unknown OCR engine: {engine_name}. "
                f"Supported engines: 'easyocr', 'paddleocr'"
            )

    def _map_language_code(self, language: str) -> str:
        """Map language code between EasyOCR and PaddleOCR conventions.

        EasyOCR uses 2-letter codes ('en'), PaddleOCR uses full names ('en').
        Both happen to use the same 'en' code, but this method allows future
        language mapping if needed.

        Args:
            language: Language code (EasyOCR format)

        Returns:
            Language code (PaddleOCR format)
        """
        # Currently both use 'en', but this allows future customisation
        language_map = {
            "eng": "en",
            "en": "en",
            "fr": "french",
            "de": "german",
            "es": "spanish",
            "zh": "ch",  # Chinese
        }
        return language_map.get(language, language)
