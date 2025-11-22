## Part 3: Multi-Modal Support (35 hours)

### FEAT-007: Docling Primary Processor

**Priority**: Critical
**Estimated Time**: 15-18 hours
**Impact**: State-of-the-art document processing with 30× speed improvement
**Dependencies**: Docling (MIT), Ollama llava model

**Note:** This feature replaces the original Tesseract-based approach with modern computer vision.

#### Scope
Comprehensive document processing with Docling:
1. **Layout Analysis**: DocLayNet model for structure detection
2. **Table Extraction**: TableFormer with 97.9% accuracy
3. **Reading Order**: Preserve document flow
4. **Vision Integration**: Ollama llava for image understanding
5. **Structured Output**: Markdown + JSON for RAG pipelines

#### Implementation

```python
# src/ingestion/document_processor.py (NEW FILE)
"""Modern document processing with Docling + PaddleOCR."""
from typing import List, Dict, Optional
from pathlib import Path
from docling.document_converter import DocumentConverter
from docling.datamodel.document import Document as DoclingDocument
import logging

logger = logging.get_logger(__name__)

class ModernDocumentProcessor:
    """
    Process documents with Docling (primary) and PaddleOCR (fallback).

    Capabilities:
    - Layout analysis (DocLayNet)
    - Table extraction (TableFormer)
    - Reading order preservation
    - Vision integration (Ollama llava)
    - Confidence-based OCR routing
    """

    def __init__(
        self,
        use_vision: bool = False,
        vision_model: str = "llava:latest",
        confidence_threshold: float = 0.85
    ):
        """
        Initialise document processor.

        Args:
            use_vision: Generate image descriptions using vision model
            vision_model: Ollama vision model name
            confidence_threshold: Fallback to PaddleOCR if below this
        """
        self.use_vision = use_vision
        self.vision_model = vision_model
        self.confidence_threshold = confidence_threshold

        # Initialise Docling converter
        self.docling_converter = DocumentConverter()

        # Lazy-load PaddleOCR (only if needed)
        self._paddle_ocr = None

        if use_vision:
            from src.generation.ollama_client import OllamaClient
            self.vision_client = OllamaClient(model=vision_model)

    def extract_images_from_pdf(
        self,
        pdf_path: Path
    ) -> List[Dict]:
        """
        Extract all images from PDF.

        Args:
            pdf_path: Path to PDF file

        Returns:
            List of image dictionaries with:
                - image: PIL Image object
                - page: Page number
                - bbox: Bounding box (x0, y0, x1, y1)
                - image_index: Index on page
        """
        images = []

        doc = fitz.open(pdf_path)

        for page_num, page in enumerate(doc):
            # Get images on page
            image_list = page.get_images()

            for img_index, img in enumerate(image_list):
                try:
                    # Extract image
                    xref = img[0]
                    base_image = doc.extract_image(xref)
                    image_bytes = base_image["image"]

                    # Convert to PIL Image
                    import io
                    pil_image = Image.open(io.BytesIO(image_bytes))

                    # Get bounding box (if available)
                    bbox = page.get_image_bbox(img)

                    images.append({
                        'image': pil_image,
                        'page': page_num + 1,
                        'bbox': bbox,
                        'image_index': img_index
                    })

                except Exception as e:
                    logger.warning(
                        f"Failed to extract image {img_index} from page {page_num + 1}: {e}"
                    )
                    continue

        doc.close()

        logger.info(f"Extracted {len(images)} images from {pdf_path}")
        return images

    def process_image(
        self,
        image: Image.Image,
        page: int
    ) -> Dict[str, str]:
        """
        Process a single image with OCR and/or vision.

        Args:
            image: PIL Image
            page: Page number

        Returns:
            Dictionary with:
                - ocr_text: Extracted text (if use_ocr)
                - description: Image description (if use_vision)
                - page: Page number
        """
        result = {'page': page}

        # OCR
        if self.use_ocr:
            try:
                ocr_text = pytesseract.image_to_string(image)
                if ocr_text.strip():
                    result['ocr_text'] = ocr_text.strip()
                    logger.debug(f"OCR extracted {len(ocr_text)} chars from image on page {page}")
            except Exception as e:
                logger.warning(f"OCR failed for image on page {page}: {e}")

        # Vision model description
        if self.use_vision:
            try:
                # Save image temporarily
                temp_path = Path(f"/tmp/ragged_image_{page}.png")
                image.save(temp_path)

                # Generate description
                description = self.vision_client.generate_from_image(
                    image_path=temp_path,
                    prompt="Describe this image in detail. If it contains diagrams, charts, or tables, explain what they show."
                )

                if description.strip():
                    result['description'] = description.strip()
                    logger.debug(f"Vision model described image on page {page}")

                # Clean up
                temp_path.unlink()

            except Exception as e:
                logger.warning(f"Vision model failed for image on page {page}: {e}")

        return result

    def process_all_images(
        self,
        pdf_path: Path
    ) -> List[Dict]:
        """
        Extract and process all images from PDF.

        Args:
            pdf_path: Path to PDF

        Returns:
            List of processed image data
        """
        # Extract images
        images = self.extract_images_from_pdf(pdf_path)

        # Process each image
        processed = []
        for img_data in images:
            result = self.process_image(
                img_data['image'],
                img_data['page']
            )
            result.update({
                'bbox': img_data['bbox'],
                'image_index': img_data['image_index']
            })
            processed.append(result)

        return processed
```

**Integration into Document Loading**:
```python
# src/ingestion/loaders.py - enhance PDF loader
class PDFLoader:
    def load(self, file_path: Path) -> Document:
        # Standard text extraction
        doc = self._extract_text(file_path)

        # Extract images if enabled
        if settings.process_images:
            image_processor = ImageProcessor(
                use_ocr=settings.use_ocr,
                use_vision=settings.use_vision_model
            )

            image_data = image_processor.process_all_images(file_path)

            # Add image content to document metadata
            doc.metadata['images'] = image_data

            # Optionally append image text to document text
            for img in image_data:
                if 'ocr_text' in img:
                    doc.text += f"\n\n[Image on page {img['page']} - OCR text]: {img['ocr_text']}"
                if 'description' in img:
                    doc.text += f"\n\n[Image on page {img['page']} - Description]: {img['description']}"

        return doc
```

#### Testing Requirements
- [ ] Test image extraction from PDF
- [ ] Test OCR on text images
- [ ] Test vision model descriptions
- [ ] Test retrieval includes image content
- [ ] Test with various image types (photos, diagrams, scanned text)

#### Files to Create
- `src/ingestion/image_processor.py` (~350 lines)
- `tests/ingestion/test_image_processor.py` (~200 lines)

#### Files to Modify
- `src/ingestion/loaders.py` (integrate image processing)
- `src/config/settings.py` (add image processing settings)

#### Dependencies to Add
```toml
# pyproject.toml - v0.3.5 Modern Document Processing
docling = "^2.0.0"              # MIT - Primary processor
paddleocr = "^2.8.0"            # Apache 2.0 - Fallback OCR
paddlepaddle = "^2.6.0"         # Apache 2.0
opencv-python = "^4.8.0"        # BSD - Image preprocessing
Pillow = "^10.0.0"              # HPND - Image handling
PyMuPDF = "^1.23.0"             # Already have this
```

#### Dependencies Removed
```toml
# Removed in v0.3.5
# pytesseract = "^0.3.10"      # Replaced by Docling/PaddleOCR
# camelot-py = "^0.11.0"       # Replaced by Docling TableFormer
```

#### Acceptance Criteria
- ✅ Can extract images from PDFs
- ✅ OCR works on text images
- ✅ Vision model generates useful descriptions
- ✅ Image content searchable via retrieval

---

### FEAT-008: PaddleOCR Fallback Engine

**Priority**: High
**Estimated Time**: 10-12 hours
**Impact**: Handle worst-case messy documents with state-of-the-art OCR
**Dependencies**: PaddleOCR (Apache 2.0), PaddlePaddle

**Note:** PaddleOCR serves as fallback when Docling confidence is below threshold (<85%).

#### Implementation

```python
# src/ingestion/ocr_engines/paddle_engine.py (NEW FILE)
"""PaddleOCR fallback engine for messy documents."""
from typing import List, Dict, Optional
from pathlib import Path
from paddleocr import PaddleOCR
import logging

logger = logging.get_logger(__name__)

class PaddleOCREngine:
    """
    PaddleOCR fallback engine for challenging documents.

    Handles:
    - Rotated/skewed text (slanted bounding boxes)
    - Poor quality scans
    - 80+ languages
    - Handwriting recognition
    """

    def __init__(
        self,
        lang: str = 'en',
        use_angle_cls: bool = True,
        use_gpu: bool = False
    ):
        """
        Initialise PaddleOCR engine.

        Args:
            lang: Language code ('en', 'fr', 'de', etc.)
            use_angle_cls: Enable rotation detection
            use_gpu: Use GPU acceleration if available
        """
        self.ocr = PaddleOCR(
            lang=lang,
            use_angle_cls=use_angle_cls,
            use_gpu=use_gpu,
            show_log=False
        )

    def process_document(
        self,
        pdf_path: Path
    ) -> Dict:
        """
        Process document with PaddleOCR.

        Args:
            pdf_path: Path to PDF document

        Returns:
            Dictionary with:
            - text: Extracted text
            - confidence: Average confidence score
            - pages: Per-page results
            - rotation_detected: Whether rotation was found
        """
        # Convert PDF to images (one per page)
        from pdf2image import convert_from_path
        images = convert_from_path(pdf_path)

        all_text = []
        all_confidences = []
        page_results = []

        for page_num, image in enumerate(images, 1):
            # Run OCR on page
            result = self.ocr.ocr(image, cls=True)

            page_text = []
            page_confidences = []

            if result and result[0]:
                for line in result[0]:
                    # Each line: [[coords], (text, confidence)]
                    coords, (text, confidence) = line
                    page_text.append(text)
                    page_confidences.append(confidence)

            # Combine page text
            page_full_text = '\n'.join(page_text)
            all_text.append(page_full_text)

            if page_confidences:
                avg_conf = sum(page_confidences) / len(page_confidences)
                all_confidences.append(avg_conf)
            else:
                avg_conf = 0.0

            page_results.append({
                'page': page_num,
                'text': page_full_text,
                'confidence': avg_conf
            })

        # Calculate overall metrics
        full_text = '\n\n'.join(all_text)
        avg_confidence = sum(all_confidences) / len(all_confidences) if all_confidences else 0.0

        return {
            'text': full_text,
            'confidence': avg_confidence,
            'pages': page_results,
            'engine': 'paddleocr'
        }
```

**Integration into Document Processor**:
```python
# src/ingestion/document_processor.py
class ModernDocumentProcessor:
    def process_pdf(self, pdf_path: Path) -> Dict:
        """Process PDF with Docling, fallback to PaddleOCR if needed."""
        # Try Docling first
        docling_result = self.docling_converter.convert(pdf_path)

        # Check confidence
        if docling_result.confidence >= self.confidence_threshold:
            logger.info(f"Using Docling result (confidence: {docling_result.confidence:.2f})")
            return docling_result

        # Fallback to PaddleOCR
        logger.warning(f"Low Docling confidence ({docling_result.confidence:.2f}), using PaddleOCR fallback")

        if not self._paddle_ocr:
            from src.ingestion.ocr_engines.paddle_engine import PaddleOCREngine
            self._paddle_ocr = PaddleOCREngine()

        paddle_result = self._paddle_ocr.process_document(pdf_path)
        logger.info(f"PaddleOCR result (confidence: {paddle_result['confidence']:.2f})")

        return paddle_result
```

#### Testing Requirements
- [ ] Test PaddleOCR on messy/rotated scans
- [ ] Test confidence-based routing
- [ ] Test with various languages
- [ ] Test performance on GPU vs CPU
- [ ] Validate accuracy on worst-case documents

#### Files to Create
- `src/ingestion/ocr_engines/base.py` (~80 lines) - Abstract interface
- `src/ingestion/ocr_engines/paddle_engine.py` (~200 lines)
- `tests/ingestion/test_paddle_engine.py` (~150 lines)

#### Dependencies
```toml
paddleocr = "^2.8.0"            # Apache 2.0 - Fallback OCR
paddlepaddle = "^2.6.0"         # Apache 2.0 - Backend
pdf2image = "^1.16.0"           # MIT - PDF to image conversion
```

#### Acceptance Criteria
- ✅ PaddleOCR processes messy documents successfully
- ✅ Confidence-based routing works correctly (>85% = Docling, <85% = PaddleOCR)
- ✅ Rotated/skewed text detected accurately
- ✅ Performance acceptable (5-8s/page on messy scans)
- ✅ Multi-language support functional

---


---

## Related Documentation

- [Multi-Modal RAG (v0.5)](../../version/v0.5/) - Full implementation plan
- [ColPali Integration (v0.5.1)](../../version/v0.5/features/VISION-001-colpali-integration.md) - Vision model
- [v0.3.10 PDF Correction](../../version/v0.3/v0.3.10.md) - Text extraction improvements
- [Vision & Multimodal Planning](../../../../planning/version/v0.5/) - v0.5 design goals

---
