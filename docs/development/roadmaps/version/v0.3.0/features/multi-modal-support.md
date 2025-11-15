## Part 3: Multi-Modal Support (35 hours)

### FEAT-007: Image Understanding (OCR + Vision)

**Priority**: Medium-High
**Estimated Time**: 20 hours
**Impact**: Handle documents with images, diagrams, scanned text
**Dependencies**: Tesseract OCR, Ollama llava model

#### Scope
Extract and understand images from PDFs:
1. **OCR**: Extract text from images (Tesseract)
2. **Vision**: Describe/understand images (Ollama llava)
3. **Integration**: Include image content in retrieval

#### Implementation

```python
# src/ingestion/image_processor.py (NEW FILE)
"""Image extraction and processing from documents."""
from typing import List, Dict
from pathlib import Path
from PIL import Image
import pytesseract
import fitz  # PyMuPDF
import logging

logger = logging.get_logger(__name__)

class ImageProcessor:
    """
    Extract and process images from documents.

    Supports:
    - OCR for text extraction
    - Vision models for image understanding
    """

    def __init__(
        self,
        use_ocr: bool = True,
        use_vision: bool = False,
        vision_model: str = "llava:latest"
    ):
        """
        Initialize image processor.

        Args:
            use_ocr: Extract text from images using OCR
            use_vision: Generate image descriptions using vision model
            vision_model: Ollama vision model name
        """
        self.use_ocr = use_ocr
        self.use_vision = use_vision
        self.vision_model = vision_model

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
# pyproject.toml
pytesseract = "^0.3.10"
Pillow = "^10.0.0"
PyMuPDF = "^1.23.0"  # Already have this
```

#### Acceptance Criteria
- ✅ Can extract images from PDFs
- ✅ OCR works on text images
- ✅ Vision model generates useful descriptions
- ✅ Image content searchable via retrieval

---

### FEAT-008: Table Extraction & Understanding

**Priority**: Medium
**Estimated Time**: 15 hours
**Impact**: Handle structured data in documents
**Dependencies**: camelot-py or tabula-py

#### Implementation

```python
# src/ingestion/table_processor.py (NEW FILE)
"""Table extraction and processing."""
from typing import List, Dict
from pathlib import Path
import camelot
import pandas as pd

class TableProcessor:
    """Extract and process tables from PDFs."""

    def __init__(self, llm=None):
        self.llm = llm

    def extract_tables(
        self,
        pdf_path: Path,
        pages: str = 'all'
    ) -> List[Dict]:
        """
        Extract tables from PDF.

        Args:
            pdf_path: Path to PDF
            pages: Pages to process ('all' or '1,2,3' or '1-10')

        Returns:
            List of table dictionaries
        """
        try:
            # Extract tables using camelot
            tables = camelot.read_pdf(
                str(pdf_path),
                pages=pages,
                flavor='lattice'  # Use 'stream' for tables without borders
            )

            processed_tables = []

            for i, table in enumerate(tables):
                # Convert to pandas DataFrame
                df = table.df

                # Skip empty tables
                if df.empty:
                    continue

                # Convert to various formats
                table_data = {
                    'table_index': i,
                    'page': table.page,
                    'dataframe': df,
                    'markdown': df.to_markdown(index=False),
                    'csv': df.to_csv(index=False),
                    'html': df.to_html(index=False),
                    'shape': df.shape,
                    'columns': list(df.columns)
                }

                # Generate natural language description if LLM available
                if self.llm:
                    table_data['description'] = self._describe_table(df)

                processed_tables.append(table_data)

            logger.info(f"Extracted {len(processed_tables)} tables from {pdf_path}")
            return processed_tables

        except Exception as e:
            logger.error(f"Table extraction failed: {e}")
            return []

    def _describe_table(self, df: pd.DataFrame) -> str:
        """Generate natural language description of table."""
        description_prompt = f"""
Describe this table in natural language. Explain what data it contains and any key insights.

Table (as CSV):
{df.to_csv(index=False)}

Description:"""

        description = self.llm.generate(
            query=description_prompt,
            context="",
            temperature=0.3,
            max_tokens=200
        )

        return description.strip()

    def convert_to_searchable_text(self, table_data: Dict) -> str:
        """
        Convert table to searchable text format.

        Combines markdown representation with natural language description.
        """
        parts = []

        # Add description if available
        if 'description' in table_data:
            parts.append(f"Table Description: {table_data['description']}")

        # Add markdown representation
        parts.append(f"\nTable (Page {table_data['page']}):\n{table_data['markdown']}")

        return "\n".join(parts)
```

**Integration**:
```python
# src/ingestion/loaders.py
class PDFLoader:
    def load(self, file_path: Path) -> Document:
        doc = self._extract_text(file_path)

        # Extract tables
        if settings.process_tables:
            table_processor = TableProcessor(llm=ollama_client)
            tables = table_processor.extract_tables(file_path)

            # Add tables to document
            for table in tables:
                table_text = table_processor.convert_to_searchable_text(table)
                doc.text += f"\n\n{table_text}"

            doc.metadata['tables'] = tables

        return doc
```

#### Testing Requirements
- [ ] Test table extraction from PDFs
- [ ] Test table-to-markdown conversion
- [ ] Test table descriptions
- [ ] Test retrieval over table content
- [ ] Test with various table formats

#### Files to Create
- `src/ingestion/table_processor.py` (~250 lines)
- `tests/ingestion/test_table_processor.py` (~150 lines)

#### Dependencies
```toml
camelot-py = "^0.11.0"
opencv-python = "^4.8.0"  # Required by camelot
```

#### Acceptance Criteria
- ✅ Can extract tables from PDFs
- ✅ Tables converted to searchable format
- ✅ LLM can answer questions about table data

---

