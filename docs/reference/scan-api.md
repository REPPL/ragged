# Scan Processing API Reference

**v0.4.9**

This document provides technical reference for ragged's scan processing API.

## Overview

The scan processing system consists of 5 main modules:

1. **OCR Engines** (`ragged.processing.ocr_engines`) - Text extraction from images
2. **Scan Preprocessor** (`ragged.processing.scan_preprocessor`) - PDF/image processing
3. **Page Reordering** (`ragged.correction.transformers.ordering`) - Automatic page correction
4. **Metadata Extractor** (`ragged.processing.metadata_extractor`) - Bibliographic metadata extraction
5. **Output Organizer** (`ragged.processing.output_organizer`) - File organisation and lineage tracking

---

## Module: `ragged.processing.ocr_engines`

### Classes

#### `BaseOCREngine` (Abstract Base Class)

Base class for all OCR engines.

**Methods:**

```python
@abstractmethod
def extract_text(
    self,
    image: Image.Image | Path | np.ndarray,
    language: str = "eng"
) -> OCRResult:
    """Extract text from image.

    Args:
        image: PIL Image, path to image file, or numpy array
        language: ISO 639-2/3 language code (default: 'eng')

    Returns:
        OCRResult with text, confidence, and bounding boxes
    """
```

#### `EasyOCREngine`

Fast OCR engine (90-95% accuracy).

**Initialization:**

```python
engine = EasyOCREngine(
    languages: list[str] = ["en"],
    gpu: bool = False
)
```

**Parameters:**
- `languages`: List of language codes (e.g., `["en", "fr"]`)
- `gpu`: Use GPU acceleration if available

**Features:**
- Fast processing speed
- Good accuracy for clean scans
- Multi-language support (80+ languages)
- CPU and GPU support

**Example:**

```python
from ragged.processing.ocr_engines import EasyOCREngine
from PIL import Image

engine = EasyOCREngine(gpu=False)
image = Image.open("page.jpg")
result = engine.extract_text(image, language="eng")

print(f"Text: {result.text}")
print(f"Confidence: {result.confidence:.2f}")
```

#### `PaddleOCREngine`

State-of-the-art OCR engine (95-98% accuracy).

**Initialization:**

```python
engine = PaddleOCREngine(
    language: str = "en",
    use_angle_cls: bool = True,
    use_gpu: bool = False
)
```

**Parameters:**
- `language`: Language code (ISO 639-2/3)
- `use_angle_cls`: Enable rotation detection (recommended: `True`)
- `use_gpu`: Use GPU acceleration if available

**Features:**
- Highest accuracy (95-98%)
- Advanced features (rotation detection, table support)
- 80+ languages
- CPU and GPU support

**Example:**

```python
from ragged.processing.ocr_engines import PaddleOCREngine

engine = PaddleOCREngine(language="en", use_angle_cls=True, use_gpu=False)
result = engine.extract_text("scan.jpg", language="eng")

# Access bounding boxes
for box in result.boxes:
    print(f"Text: {box.text}, Confidence: {box.confidence:.2f}")
```

#### `OCREngineSelector`

Automatic OCR engine selection based on quality.

**Initialization:**

```python
selector = OCREngineSelector(
    quality_threshold: float = 0.70,
    prefer_gpu: bool = False
)
```

**Parameters:**
- `quality_threshold`: Threshold for engine selection (0.0-1.0)
  - `>= 0.70`: Use EasyOCR (fast)
  - `< 0.70`: Use PaddleOCR (accurate)
- `prefer_gpu`: Prefer GPU if available

**Method:**

```python
def select(self, quality_score: float) -> BaseOCREngine:
    """Select appropriate OCR engine based on quality score."""
```

**Example:**

```python
from ragged.processing.ocr_engines import OCREngineSelector

selector = OCREngineSelector(quality_threshold=0.70, prefer_gpu=False)

# High quality scan -> EasyOCR (fast)
engine_fast = selector.select(quality_score=0.85)

# Low quality scan -> PaddleOCR (accurate)
engine_accurate = selector.select(quality_score=0.55)
```

### Data Classes

#### `OCRResult`

Result from OCR extraction.

**Fields:**

```python
@dataclass
class OCRResult:
    text: str                    # Extracted text
    confidence: float            # Overall confidence (0.0-1.0)
    boxes: list[BoundingBox]     # Bounding boxes for each text region
    engine: str                  # Engine used ("easyocr" or "paddleocr")
```

#### `BoundingBox`

Bounding box for detected text region.

**Fields:**

```python
@dataclass
class BoundingBox:
    text: str                    # Text in this box
    confidence: float            # Confidence for this box (0.0-1.0)
    coordinates: list[tuple[int, int]]  # Box coordinates [(x1,y1), (x2,y2), ...]
```

---

## Module: `ragged.processing.scan_preprocessor`

### Classes

#### `ScanPreprocessor`

Main scan preprocessing pipeline.

**Initialization:**

```python
preprocessor = ScanPreprocessor(
    ocr_engine: Literal["auto", "easyocr", "paddleocr"] = "auto",
    ocr_language: str = "eng",
    force_ocr: bool = False,
    pdf_dpi: int = 300,
    enable_preprocessing: bool = True,
    prefer_gpu: bool = False
)
```

**Parameters:**
- `ocr_engine`: OCR engine selection strategy
  - `"auto"`: Automatic quality-based selection (recommended)
  - `"easyocr"`: Always use EasyOCR
  - `"paddleocr"`: Always use PaddleOCR
- `ocr_language`: ISO 639-2/3 language code
- `force_ocr`: Force OCR even if PDF has text layer
- `pdf_dpi`: DPI for PDF to image conversion (150-600)
- `enable_preprocessing`: Enable image enhancement (deskew, denoise, contrast)
- `prefer_gpu`: Use GPU if available

**Methods:**

##### `preprocess()`

```python
def preprocess(
    self,
    input_path: Path,
    output_path: Path | None = None
) -> PreprocessResult:
    """Preprocess scanned document.

    Args:
        input_path: Path to PDF, image file, or folder
        output_path: Output PDF path (optional, creates temp if None)

    Returns:
        PreprocessResult with processed PDF path and metadata

    Raises:
        FileNotFoundError: If input path doesn't exist
        ValueError: If unsupported file type
    """
```

**Example:**

```python
from pathlib import Path
from ragged.processing.scan_preprocessor import ScanPreprocessor

preprocessor = ScanPreprocessor(
    ocr_engine="auto",
    ocr_language="eng",
    enable_preprocessing=True,
    prefer_gpu=False
)

result = preprocessor.preprocess(
    input_path=Path("~/scans/book.pdf"),
    output_path=Path("~/output/processed.pdf")
)

print(f"Input type: {result.input_type}")
print(f"Total pages: {result.total_pages}")
print(f"OCR applied: {result.ocr_applied}")
print(f"Processing time: {result.processing_time:.1f}s")
```

##### `detect_input_type()`

```python
def detect_input_type(self, input_path: Path) -> InputType:
    """Detect input type from path.

    Returns:
        InputType enum value:
        - SINGLE_PDF: Single PDF file
        - SINGLE_IMAGE: Single image file (JPG, PNG, TIFF, BMP)
        - FOLDER_IMAGES: Folder containing only images
        - FOLDER_PDFS: Folder containing only PDFs
        - FOLDER_MIXED: Folder with both images and PDFs
    """
```

### Data Classes

#### `PreprocessResult`

Result from preprocessing operation.

```python
@dataclass
class PreprocessResult:
    pdf_path: Path               # Path to processed PDF
    input_type: InputType        # Detected input type
    total_pages: int             # Number of pages in output
    ocr_applied: bool            # Whether OCR was applied
    preprocessing_applied: bool  # Whether image enhancement was applied
    processing_time: float       # Processing time in seconds
```

#### `InputType`

Enum for input type classification.

```python
class InputType(Enum):
    SINGLE_PDF = "single_pdf"
    SINGLE_IMAGE = "single_image"
    FOLDER_IMAGES = "folder_images"
    FOLDER_PDFS = "folder_pdfs"
    FOLDER_MIXED = "folder_mixed"
```

---

## Module: `ragged.correction.transformers.ordering`

### Classes

#### `PageReorderTransformer`

Automatic page reordering with interpolation.

**Initialization:**

```python
transformer = PageReorderTransformer()
```

**Methods:**

##### `transform()`

```python
def transform(self, pdf_path: Path) -> Path | None:
    """Reorder pages if needed.

    Args:
        pdf_path: Path to PDF to reorder

    Returns:
        Path to reordered PDF, or None if no reordering needed

    Process:
        1. Extract logical page numbers from headers/footers
        2. Interpolate missing page numbers
        3. Build reordering map
        4. Apply reordering if < 80% of pages affected
    """
```

**Example:**

```python
from pathlib import Path
from ragged.correction.transformers.ordering import PageReorderTransformer

transformer = PageReorderTransformer()

# Reorder pages if needed
result_path = transformer.transform(Path("~/scans/misordered.pdf"))

if result_path:
    print(f"Pages reordered: {result_path}")
else:
    print("No reordering needed - pages already in correct order")
```

**Page Number Interpolation:**

The transformer uses intelligent interpolation to handle books where not every page has a page number:

```python
# Example: Chapter start page has no page number
# Input:  [(0, 1), (1, None), (2, 3)]
# Output: [(0, 1), (1, 2),    (2, 3)]

# Example: Blank page has no page number
# Input:  [(0, 1), (1, None), (2, None), (3, 4)]
# Output: [(0, 1), (1, 2),    (2, 3),    (3, 4)]
```

**Safety Checks:**

- Reordering is skipped if >80% of pages would be affected (likely indicates incorrect page number detection)
- Requires at least 2 known page numbers for interpolation
- Detects gaps (missing pages in physical document)

---

## Module: `ragged.processing.metadata_extractor`

### Classes

#### `MetadataExtractor`

Extract bibliographic metadata from scanned documents.

**Initialization:**

```python
extractor = MetadataExtractor(
    titlepage_pages: int = 3,
    ocr_language: str = "eng",
    use_vision: bool = False,
    prefer_gpu: bool = False
)
```

**Parameters:**
- `titlepage_pages`: Number of pages to analyse for metadata (1-10)
- `ocr_language`: Language code for OCR
- `use_vision`: Use vision-based extraction (not yet implemented)
- `prefer_gpu`: Use GPU if available

**Methods:**

##### `extract()`

```python
def extract(self, pdf_path: Path) -> ExtractedMetadata:
    """Extract metadata from PDF.

    Args:
        pdf_path: Path to PDF file

    Returns:
        ExtractedMetadata with title, author, year, publisher

    Strategy:
        1. PDF embedded metadata (fast, often incomplete)
        2. Title page OCR + regex (main method, 70-80% accuracy)
        3. Vision analysis (optional, not yet implemented)
        4. Fallback (filename sanitisation)
    """
```

**Example:**

```python
from pathlib import Path
from ragged.processing.metadata_extractor import MetadataExtractor

extractor = MetadataExtractor(
    titlepage_pages=3,
    ocr_language="eng",
    use_vision=False
)

metadata = extractor.extract(Path("~/scans/book.pdf"))

print(f"Title: {metadata.title}")
print(f"Author: {metadata.author}")
print(f"Year: {metadata.year}")
print(f"Publisher: {metadata.publisher}")
print(f"Confidence: {metadata.confidence:.2f}")
print(f"Method: {metadata.method}")
```

### Data Classes

#### `ExtractedMetadata`

Extracted bibliographic metadata.

```python
@dataclass
class ExtractedMetadata:
    title: str | None            # Book title
    author: str | None           # Author name
    year: int | None             # Publication year
    publisher: str | None        # Publisher name
    confidence: float            # Confidence score (0.0-1.0)
    method: str                  # Extraction method used
```

**Confidence Scoring:**

- **0.9-1.0**: High confidence (all fields extracted)
- **0.7-0.9**: Good confidence (title, author, year)
- **0.5-0.7**: Medium confidence (title and author)
- **0.3-0.5**: Low confidence (title only)
- **0.1-0.3**: Fallback (filename used)

**Extraction Methods:**

- `"pdf_metadata"`: From PDF embedded metadata
- `"titlepage_ocr"`: From title page OCR + regex
- `"vision"`: From vision analysis (not yet implemented)
- `"fallback"`: From filename sanitisation

---

## Module: `ragged.processing.output_organizer`

### Classes

#### `OutputOrganizer`

Organise processed outputs with semantic naming and lineage tracking.

**Initialization:**

```python
organizer = OutputOrganizer(
    output_dir: Path = Path.home() / ".ragged" / "documents",
    naming_convention: Literal["title-author-year", "hash", "original"] = "title-author-year",
    keep_originals: bool = True,
    track_lineage: bool = True
)
```

**Parameters:**
- `output_dir`: Base output directory
- `naming_convention`: File naming strategy
  - `"title-author-year"`: Semantic naming (default)
  - `"hash"`: Content-based hash (16 chars)
  - `"original"`: Preserve original filename
- `keep_originals`: Backup original files
- `track_lineage`: Track processing history in JSONL

**Methods:**

##### `organize()`

```python
def organize(
    self,
    original: Path,
    corrected: Path,
    markdown: Path | None = None,
    metadata: dict[str, Any] | None = None
) -> OrganizedOutput:
    """Organise processed outputs.

    Args:
        original: Path to original file
        corrected: Path to corrected PDF
        markdown: Path to markdown file (optional)
        metadata: Extracted metadata dictionary (optional)

    Returns:
        OrganizedOutput with paths to organized files

    Process:
        1. Generate semantic filename from metadata
        2. Backup original to originals/[hash]/
        3. Copy corrected PDF to corrected/
        4. Copy markdown to markdown/
        5. Record lineage in processing_log.jsonl
    """
```

**Example:**

```python
from pathlib import Path
from ragged.processing.output_organizer import OutputOrganizer

organizer = OutputOrganizer(
    output_dir=Path.home() / ".ragged" / "documents",
    naming_convention="title-author-year",
    keep_originals=True,
    track_lineage=True
)

result = organizer.organize(
    original=Path("~/scans/book.pdf"),
    corrected=Path("~/temp/corrected.pdf"),
    markdown=Path("~/temp/book.md"),
    metadata={
        "title": "Being and Time",
        "author": "Martin Heidegger",
        "year": 1927,
        "publisher": "Max Niemeyer Verlag"
    }
)

print(f"Corrected PDF: {result.corrected_path}")
print(f"Markdown: {result.markdown_path}")
print(f"Original backup: {result.original_path}")
print(f"Lineage ID: {result.lineage_id}")
```

##### `get_lineage()`

```python
def get_lineage(
    self,
    lineage_id: str | None = None
) -> list[dict[str, Any]]:
    """Retrieve lineage records.

    Args:
        lineage_id: Specific lineage ID to retrieve (optional)

    Returns:
        List of lineage records (all records if lineage_id is None)
    """
```

##### `search_by_metadata()`

```python
def search_by_metadata(
    self,
    title: str | None = None,
    author: str | None = None,
    year: int | None = None,
    publisher: str | None = None
) -> list[dict[str, Any]]:
    """Search lineage records by metadata.

    Args:
        title: Title substring to search (case-insensitive)
        author: Author substring to search (case-insensitive)
        year: Exact year to match
        publisher: Publisher substring to search (case-insensitive)

    Returns:
        List of matching lineage records
    """
```

**Example:**

```python
# Search for all books by Heidegger
results = organizer.search_by_metadata(author="Heidegger")

for record in results:
    print(f"Title: {record['metadata']['title']}")
    print(f"File: {record['processed']['corrected_pdf']}")
    print()
```

### Data Classes

#### `OrganizedOutput`

Result from organization operation.

```python
@dataclass
class OrganizedOutput:
    original_path: Path          # Path to original backup (or original if not backed up)
    corrected_path: Path         # Path to corrected PDF
    markdown_path: Path | None   # Path to markdown file (or None)
    lineage_id: str             # Unique lineage identifier
```

### Directory Structure

```
output_dir/  (default: ~/.ragged/documents/)
├── originals/               # Original backups (immutable)
│   └── [content-hash]/      # Content-based hash directory
│       └── original.pdf     # Original file
├── corrected/               # Corrected PDFs
│   └── Title-Author-Year.pdf
└── markdown/                # Markdown exports
    └── Title-Author-Year.md

output_dir/../metadata/      # Metadata directory
└── processing_log.jsonl     # Lineage tracking (JSONL format)
```

### Lineage Tracking Format

Each line in `processing_log.jsonl` is a JSON object:

```json
{
  "lineage_id": "20251123140000-a3f7e9d2",
  "timestamp": "2025-11-23T14:00:00Z",
  "original": {
    "path": "/path/to/original.pdf",
    "backup": "/Users/name/.ragged/documents/originals/a3f7e9.../original.pdf",
    "size_bytes": 12456789,
    "hash": "a3f7e9d2..."
  },
  "processed": {
    "corrected_pdf": "/Users/name/.ragged/documents/corrected/Title-Author-Year.pdf",
    "markdown": "/Users/name/.ragged/documents/markdown/Title-Author-Year.md"
  },
  "metadata": {
    "title": "Being and Time",
    "author": "Martin Heidegger",
    "year": 1927,
    "publisher": "Max Niemeyer Verlag"
  },
  "processor_version": "v0.4.9"
}
```

---

## Configuration Settings

Configuration in `~/.ragged/config.yml`:

```yaml
# OCR Settings
scan_ocr_engine: auto                     # auto, easyocr, paddleocr
scan_ocr_language: eng                    # ISO 639-2/3 code
scan_ocr_gpu: false                       # Use GPU if available
scan_force_ocr: false                     # Force OCR even if text exists

# Processing Settings
scan_pdf_dpi: 300                         # DPI for PDF to image (150-600)
scan_enable_preprocessing: true           # Image enhancement
scan_auto_reorder: true                   # Automatic page reordering

# Export Settings
scan_export_markdown: true                # Export to markdown
scan_keep_originals: true                 # Backup original files

# Output Settings
scan_output_dir: null                     # null = ~/.ragged/documents/
scan_naming_convention: title-author-year # title-author-year, hash, original

# Metadata Settings
scan_metadata_titlepage_pages: 3          # Pages to analyse (1-10)
scan_enable_lineage_tracking: true        # Track processing history
```

---

## Complete Pipeline Example

Full example using all components:

```python
from pathlib import Path
from ragged.processing.scan_preprocessor import ScanPreprocessor
from ragged.correction.transformers.ordering import PageReorderTransformer
from ragged.processing.metadata_extractor import MetadataExtractor
from ragged.processing.output_organizer import OutputOrganizer

# 1. Preprocess scan
preprocessor = ScanPreprocessor(
    ocr_engine="auto",
    ocr_language="eng",
    enable_preprocessing=True,
    prefer_gpu=False
)

preprocess_result = preprocessor.preprocess(
    input_path=Path("~/scans/book.pdf"),
    output_path=Path("/tmp/preprocessed.pdf")
)

print(f"[1/5] Preprocessing complete: {preprocess_result.total_pages} pages")

# 2. Reorder pages
transformer = PageReorderTransformer()
reordered_path = transformer.transform(preprocess_result.pdf_path)

if reordered_path:
    corrected_path = reordered_path
    print(f"[2/5] Pages reordered")
else:
    corrected_path = preprocess_result.pdf_path
    print(f"[2/5] No reordering needed")

# 3. Extract metadata
extractor = MetadataExtractor(
    titlepage_pages=3,
    ocr_language="eng"
)

metadata = extractor.extract(corrected_path)
print(f"[3/5] Metadata extracted: {metadata.title} by {metadata.author}")

# 4. Export to markdown (using existing DoclingProcessor)
from ragged.processing.processors import DoclingProcessor

docling = DoclingProcessor()
markdown_result = docling.process_pdf(corrected_path)
markdown_path = Path("/tmp/book.md")
markdown_path.write_text(markdown_result.content)
print(f"[4/5] Markdown exported")

# 5. Organize outputs
organizer = OutputOrganizer(
    output_dir=Path.home() / ".ragged" / "documents",
    naming_convention="title-author-year",
    keep_originals=True,
    track_lineage=True
)

organized = organizer.organize(
    original=Path("~/scans/book.pdf"),
    corrected=corrected_path,
    markdown=markdown_path,
    metadata={
        "title": metadata.title,
        "author": metadata.author,
        "year": metadata.year,
        "publisher": metadata.publisher
    }
)

print(f"[5/5] Organization complete")
print(f"\nCorrected PDF: {organized.corrected_path}")
print(f"Markdown: {organized.markdown_path}")
print(f"Lineage ID: {organized.lineage_id}")
```

---

## Error Handling

### Common Exceptions

```python
# FileNotFoundError
preprocessor.preprocess(Path("/nonexistent/file.pdf"))
# Raises: FileNotFoundError

# ValueError (unsupported file type)
preprocessor.preprocess(Path("document.docx"))
# Raises: ValueError: Unsupported file type

# OCR errors (caught internally, returns low confidence)
result = extractor.extract(Path("very-blurry-scan.pdf"))
# Returns: ExtractedMetadata with confidence < 0.3, method="fallback"
```

### Best Practices

1. **Always check file existence** before processing
2. **Handle None returns** (e.g., when reordering not needed)
3. **Check confidence scores** for metadata extraction
4. **Use try-except** for file I/O operations
5. **Clean up temporary files** after processing

---

## Performance Considerations

### OCR Engine Selection

- **EasyOCR**: 2-5 seconds per page (CPU)
- **PaddleOCR**: 3-8 seconds per page (CPU), 1-3 seconds (GPU)

**Recommendation**: Use `ocr_engine="auto"` for quality-based selection.

### GPU Acceleration

**Supported:**
- CUDA-capable NVIDIA GPUs
- Apple Silicon (MPS backend)

**Speedup:**
- 2-5x faster for OCR
- Minimal speedup for preprocessing

**Enable:**
```python
preprocessor = ScanPreprocessor(prefer_gpu=True)
```

### Memory Usage

**Per Page:**
- Image preprocessing: ~50-100 MB
- OCR processing: ~200-500 MB
- Metadata extraction: ~50-100 MB

**Large Documents:**
- Process in batches for documents >500 pages
- Use lower DPI (150-200) for faster processing

---

## See Also

- [User Guide: Scanning Books](../guides/scanning-books.md)
- [Tutorial: Your First Scan](../tutorials/your-first-scan.md)
- [Configuration Reference](./configuration.md)
