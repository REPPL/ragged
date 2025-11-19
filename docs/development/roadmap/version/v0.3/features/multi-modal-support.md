# Multi-Modal Document Intelligence

State-of-the-art OCR, table extraction, and image understanding for production-ready document processing with 95% PDF success rate.

## Feature Overview

Multi-modal support transforms ragged from a text-only RAG system into a comprehensive document intelligence platform capable of processing real-world PDFs containing text, tables, images, charts, and complex layouts. The feature replaces the existing Tesseract + Camelot stack with modern deep learning approaches (Docling + PaddleOCR) that deliver 30× performance improvements and 97.9% table extraction accuracy.

This is the foundation for handling production document workloads where 95% of PDFs contain more than just plain text - they include financial tables, scientific diagrams, product images, and complex multi-column layouts. By integrating computer vision (Docling) for born-digital documents, state-of-the-art OCR (PaddleOCR) for messy scans, and vision-language models (llava) for image understanding, ragged achieves professional-grade document processing capabilities.

The implementation follows a confidence-based routing architecture where document quality assessment automatically selects the optimal processor (Docling for clean documents, PaddleOCR for challenging cases), ensuring both speed and accuracy. All processing remains fully offline and privacy-preserving, aligning with ragged's core philosophy.

## Design Goals

1. **PDF Success Rate**: Process 95% of real-world PDFs successfully (text + tables + images + layout)
   - Born-digital PDFs: >99% accuracy
   - Clean scans: >98% accuracy
   - Messy/degraded scans: >95% accuracy

2. **Table Extraction Quality**: Achieve 97.9% accuracy on complex tables using TableFormer
   - Financial tables with merged cells
   - Scientific tables with formulas
   - Multi-page tables with headers

3. **Processing Performance**: 30× faster than existing Tesseract-based stack
   - Born-digital PDFs: <1 second/page
   - Clean scans: 2-3 seconds/page
   - Messy scans: 5-8 seconds/page (PaddleOCR fallback)

4. **Layout Preservation**: Maintain document structure and reading order
   - Headings, paragraphs, lists correctly identified
   - Multi-column layouts preserved
   - Logical reading order maintained

5. **Multi-Modal Understanding**: Extract and understand non-text elements
   - Images extracted and described (llava integration)
   - Charts and diagrams interpreted
   - Formulas recognised (when available)

6. **Privacy Preservation**: All processing remains offline and on-premises
   - No external API calls
   - No data transmission
   - Full user control

## Technical Architecture

### Module Structure

```
src/
└── ragged/
    └── processing/
        ├── __init__.py
        ├── base_processor.py           # Base interface (modified - 100 lines)
        ├── docling_processor.py        # Docling integration (350 lines)
        │   └── class DoclingProcessor
        ├── paddleocr_processor.py      # PaddleOCR fallback (300 lines)
        │   └── class PaddleOCRProcessor
        ├── quality_assessment.py       # Document quality scoring (250 lines)
        │   └── class QualityAssessor
        ├── processor_router.py         # Confidence-based routing (200 lines)
        │   └── class ProcessorRouter
        └── vision_processor.py         # Vision integration (modified - 150 lines)
            └── class VisionProcessor

tests/processing/
├── test_docling_processor.py          # Unit tests (400 lines)
├── test_paddleocr_processor.py        # Unit tests (350 lines)
├── test_quality_assessment.py         # Unit tests (300 lines)
├── test_processor_router.py           # Unit tests (250 lines)
├── test_vision_integration.py         # Integration tests (200 lines)
└── test_e2e_multimodal.py             # E2E tests (300 lines)

# REMOVED (v0.3.0):
# src/ragged/processing/tesseract_processor.py
# src/ragged/processing/camelot_processor.py
```

### Data Flow

```
PDF Document Input
    ↓
┌───────────────────────────────────────┐
│  Document Quality Assessment          │
│  - is_born_digital? (PDF metadata)    │
│  - scan_quality (DPI, contrast)       │
│  - confidence_score (aggregate)       │
└───────────┬───────────────────────────┘
            ↓
┌───────────────────────────────────────┐
│  Processor Router                     │
│  Confidence >= 85%? → Docling         │
│  Confidence 70-85%? → Docling + validate│
│  Confidence < 70%?  → PaddleOCR       │
└───────┬───────────┬───────────────────┘
        ↓           ↓
   ┌────────┐  ┌──────────┐
   │Docling │  │PaddleOCR │
   │Path    │  │Path      │
   └────┬───┘  └─────┬────┘
        │            │
        ↓            ↓
Layout Analysis   Text Detection
(DocLayNet)       (Rotated boxes)
        ↓            ↓
Table Extraction  Text Recognition
(TableFormer)     (80+ languages)
        ↓            ↓
Text Extraction   Confidence Scoring
(CV/EasyOCR)
        ↓            ↓
Image Extraction  Output Normalisation
        ↓            │
Vision (llava)       │
        ↓            │
    ┌───┴────────────┴──┐
    │ Confidence Check   │
    │ Fallback if needed │
    └────────┬───────────┘
             ↓
    ┌────────────────────┐
    │ Structured Output  │
    │ - Markdown         │
    │ - JSON metadata    │
    │ - Extracted images │
    └────────────────────┘
```

### API Interfaces

```python
"""Modern multi-modal document processing."""

from pathlib import Path
from typing import Dict, List, Optional, Tuple
from enum import Enum
from dataclasses import dataclass


class ProcessorType(Enum):
    """Document processor types."""

    DOCLING = "docling"
    PADDLEOCR = "paddleocr"


class DocumentQuality(Enum):
    """Document quality classifications."""

    HIGH = "high"  # Born-digital, >85% confidence
    MEDIUM = "medium"  # Clean scan, 70-85% confidence
    LOW = "low"  # Messy scan, <70% confidence


@dataclass
class ProcessingResult:
    """Result from document processing."""

    markdown: str  # Converted markdown content
    confidence: float  # Overall confidence score (0.0-1.0)
    processor_used: ProcessorType  # Which processor was used
    metadata: Dict  # Extracted metadata
    images: List[Path]  # Extracted image paths
    tables: List[Dict]  # Extracted tables with structure
    processing_time: float  # Time in seconds


@dataclass
class QualityAssessment:
    """Document quality assessment result."""

    is_born_digital: bool  # True if computer-generated PDF
    scan_quality: float  # 0.0-1.0 for scanned docs
    text_clarity: float  # 0.0-1.0 character sharpness
    layout_complexity: float  # 0.0-1.0 complexity score
    overall_confidence: float  # Weighted average
    recommended_processor: ProcessorType


class QualityAssessor:
    """Assess document quality and recommend processor."""

    def __init__(self):
        """Initialise quality assessor."""
        pass

    def assess(self, pdf_path: Path) -> QualityAssessment:
        """
        Assess document quality.

        Args:
            pdf_path: Path to PDF file

        Returns:
            Quality assessment with processor recommendation
        """
        pass


class DoclingProcessor:
    """Modern document processor using Docling (computer vision + OCR)."""

    def __init__(
        self,
        enable_tables: bool = True,
        enable_formulas: bool = True,
        enable_vision: bool = True,
        ocr_engine: str = "easyocr",  # Docling's built-in OCR
    ):
        """
        Initialise Docling processor.

        Args:
            enable_tables: Enable table extraction (TableFormer)
            enable_formulas: Enable formula recognition
            enable_vision: Enable image extraction and description
            ocr_engine: OCR engine for scanned docs ("easyocr")
        """
        pass

    def process(self, pdf_path: Path) -> ProcessingResult:
        """
        Process document with Docling.

        Args:
            pdf_path: Path to PDF file

        Returns:
            Processing result with markdown, metadata, images, tables

        Raises:
            ProcessingError: If processing fails
        """
        pass


class PaddleOCRProcessor:
    """Fallback processor for messy/degraded documents using PaddleOCR."""

    def __init__(
        self,
        lang: str = "en",
        use_angle_cls: bool = True,  # Enable rotation detection
        use_gpu: bool = True,
    ):
        """
        Initialise PaddleOCR processor.

        Args:
            lang: Language code ("en", "ch", "fr", etc. - 80+ supported)
            use_angle_cls: Enable text rotation/skew detection
            use_gpu: Use GPU if available (fallback to CPU)
        """
        pass

    def process(self, pdf_path: Path) -> ProcessingResult:
        """
        Process document with PaddleOCR.

        Args:
            pdf_path: Path to PDF file

        Returns:
            Processing result with normalised output

        Raises:
            ProcessingError: If processing fails
        """
        pass


class ProcessorRouter:
    """Route documents to appropriate processor based on quality."""

    def __init__(
        self,
        confidence_threshold_high: float = 0.85,
        confidence_threshold_low: float = 0.70,
    ):
        """
        Initialise processor router.

        Args:
            confidence_threshold_high: Threshold for using Docling only
            confidence_threshold_low: Threshold below which PaddleOCR is used
        """
        self.assessor = QualityAssessor()
        self.docling = DoclingProcessor()
        self.paddleocr = PaddleOCRProcessor()
        self.threshold_high = confidence_threshold_high
        self.threshold_low = confidence_threshold_low

    def process(self, pdf_path: Path) -> ProcessingResult:
        """
        Process document with optimal processor.

        Workflow:
        1. Assess document quality
        2. Select processor based on confidence
        3. Process with selected processor
        4. Validate results, fallback if needed

        Args:
            pdf_path: Path to PDF file

        Returns:
            Processing result from selected processor
        """
        pass
```

### Integration Points

- **Embedding Pipeline**: Processed markdown is chunked and embedded as usual
- **Vision Integration**: Extracted images passed to existing llava vision processor
- **Metadata Storage**: Table structures and image references stored in ChromaDB metadata
- **CLI**: Existing `ragged ingest` command automatically uses new processors
- **Configuration**: Persona-based processor preferences (accuracy/speed/balanced)

## Security & Privacy

### Requirements

- **Path Traversal Prevention**: Validate all file paths before processing
- **File Size Limits**: Enforce maximum PDF size (configurable, default 100MB)
- **Temporary File Cleanup**: Delete extracted images and intermediate files after processing
- **No External Calls**: All processing offline (Docling, PaddleOCR, llava are local)
- **Input Validation**: Verify PDF format before processing (prevent malformed files)

### Privacy Risk Score

**Score**: 75/100 (Good privacy protection, medium risk)

**Justification**:

**Risk Factors**:
- File uploads from users (potential for sensitive documents)
- Temporary files created during processing (images, tables)
- No user data collected (OCR happens locally)
- No network communication (fully offline)

**Mitigation**:
- All processing happens on-premises (no cloud APIs)
- Temporary files have restrictive permissions (0o600)
- Automatic cleanup of temporary files (TTL-based)
- Path traversal validation prevents directory escape
- File size limits prevent resource exhaustion

The medium privacy risk score (75/100) reflects the nature of document processing (handling potentially sensitive user files) rather than actual privacy violations. All mitigations are in place to ensure user documents remain private.

### Integration with Security Foundation

**Requires**: v0.2.10 (Session Isolation - minimal), v0.2.11 (File Security - essential)

**Key APIs Used**:

```python
from ragged.privacy import CleanupScheduler
from ragged.utils import validate_path, enforce_file_limit

# Validate file path (prevent directory traversal)
safe_path = validate_path(user_provided_path, allowed_dir=Path("~/.ragged/uploads"))

# Enforce file size limit
enforce_file_limit(pdf_path, max_size_mb=100)

# Schedule cleanup of temporary files
scheduler = CleanupScheduler()
scheduler.schedule_cleanup(
    data_path=Path("~/.ragged/temp/extractions"),
    ttl_days=1,  # Delete after 24 hours
    cron_schedule="0 */6 * * *"  # Every 6 hours
)

# Set restrictive permissions on extracted files
import os
for image_path in extracted_images:
    os.chmod(image_path, 0o600)  # Owner read/write only
```

### Detailed Policies

- [Security Policy](../../../../security/policy.md#secure-coding-standards) - File upload validation and input sanitisation
- [Privacy Architecture](../../../../security/privacy-architecture.md#data-lifecycle-management) - Temporary file cleanup

## Implementation Phases

### Phase 1: Architecture & Research (8-10h)

**Objective**: Validate Docling and PaddleOCR performance, design routing architecture

**Steps**:
1. Install Docling and PaddleOCR in test environment
2. Benchmark on 20 representative PDFs (born-digital, clean scans, messy scans, tables)
3. Measure accuracy, speed, and quality vs existing Tesseract
4. Use architecture-advisor agent for stack review
5. Design confidence-based routing logic
6. Plan migration strategy from Tesseract + Camelot

**Dependencies**: None

**Deliverables**:
- Benchmark results documented
- Architecture decision record updated (ADR already exists: 2025-11-17-docling-ocr-decision.md)
- Routing logic design finalised
- Migration strategy defined

**Verification**:
- [ ] Docling 30× faster than Tesseract confirmed
- [ ] PaddleOCR handles rotated text confirmed
- [ ] Table extraction >97% accuracy validated
- [ ] Architecture-advisor review complete

### Phase 2: Docling Integration (15-20h)

**Objective**: Replace Tesseract and Camelot with Docling as primary processor

**Steps**:
1. Remove `pytesseract` and `camelot-py` from dependencies
2. Add Docling dependencies (`docling>=2.0.0`, `opencv-python>=4.8.0`)
3. Create `src/processing/docling_processor.py`
4. Implement `DoclingProcessor` class with layout analysis
5. Integrate TableFormer for table extraction
6. Implement reading order preservation
7. Convert Docling JSON output to ragged markdown format
8. Create unit tests (>80% coverage)
9. Test on diverse document types

**Dependencies**: Phase 1 complete

**Deliverables**:
- Docling fully integrated and tested
- Tesseract and Camelot removed
- Unit tests passing
- Conversion to ragged format working

**Verification**:
- [ ] Docling processes born-digital PDFs correctly
- [ ] Table extraction working (TableFormer)
- [ ] Layout analysis preserves structure
- [ ] Output format matches ragged expectations
- [ ] Unit tests >80% coverage

### Phase 3: PaddleOCR Fallback (10-14h)

**Objective**: Implement PaddleOCR as fallback for challenging documents

**Steps**:
1. Add PaddleOCR dependencies (`paddleocr>=2.8.0`, `paddlepaddle>=2.6.0`)
2. Create `src/processing/paddleocr_processor.py`
3. Implement `PaddleOCRProcessor` class
4. Support rotated/skewed text detection (slanted bounding boxes)
5. Implement text recognition with 80+ language support
6. Normalise PaddleOCR output to ragged format
7. Create unit tests
8. Test on messy/degraded documents

**Dependencies**: Phase 2 complete (for output format compatibility)

**Deliverables**:
- PaddleOCR fallback functional
- Rotated text handling working
- Output normalisation complete
- Unit tests passing

**Verification**:
- [ ] PaddleOCR handles rotated text (slanted boxes)
- [ ] Works on degraded scans
- [ ] Output format matches Docling/ragged
- [ ] Unit tests passing

### Phase 4: Quality Assessment & Routing (8-12h)

**Objective**: Implement intelligent document quality assessment and processor selection

**Steps**:
1. Create `src/processing/quality_assessment.py`
2. Implement `QualityAssessor` class
3. Implement born-digital detection (PDF metadata, fonts)
4. Implement scan quality scoring (DPI, contrast analysis)
5. Aggregate confidence scores
6. Create `src/processing/processor_router.py`
7. Implement confidence-based routing logic (>85%: Docling, <70%: PaddleOCR)
8. Create integration tests for routing decisions
9. Tune thresholds on diverse document set

**Dependencies**: Phases 2 and 3 complete

**Deliverables**:
- Quality assessment working
- Routing logic functional
- Thresholds tuned
- Integration tests passing

**Verification**:
- [ ] Born-digital detection accurate
- [ ] Scan quality scoring reasonable
- [ ] Routing selects correct processor
- [ ] Fallback triggers on low confidence
- [ ] Integration tests passing

### Phase 5: Vision Integration (7-10h)

**Objective**: Integrate Docling image extraction with llava for image understanding

**Steps**:
1. Modify `src/processing/vision_processor.py`
2. Extract images from Docling output
3. Pass extracted images to llava vision model
4. Generate image descriptions
5. Add descriptions as alt-text in markdown output
6. Create integration tests
7. Validate image quality and description accuracy

**Dependencies**: Phase 2 complete (Docling image extraction)

**Deliverables**:
- Vision integration working
- Image extraction and description automated
- Alt-text added to markdown
- Integration tests passing

**Verification**:
- [ ] Images extracted from Docling correctly
- [ ] llava generates accurate descriptions
- [ ] Alt-text formatted properly in markdown
- [ ] Integration tests passing

### Phase 6: Testing & Migration (6-10h)

**Objective**: Comprehensive testing and migration from old stack

**Steps**:
1. Create test corpus of 100+ diverse PDFs
2. Run comprehensive tests (born-digital, clean scans, messy scans, tables, images)
3. Performance benchmarking (speed vs Tesseract)
4. Quality comparison (accuracy vs Tesseract)
5. Migration testing (reprocess existing documents)
6. Edge case testing (malformed PDFs, empty pages, etc.)
7. Create user migration guide
8. Document performance improvements

**Dependencies**: Phases 2-5 complete

**Deliverables**:
- Comprehensive test results
- Performance benchmarks documented
- Quality improvements validated
- Migration guide complete
- Edge cases handled

**Verification**:
- [ ] 95% PDF success rate achieved
- [ ] Performance 5-30× faster than Tesseract
- [ ] Table extraction >97% accuracy
- [ ] Migration guide clear and complete

### Phase 7: Documentation & Release (3-5h)

**Objective**: Complete documentation and release v0.3.5

**Steps**:
1. Use documentation-architect agent for OCR pipeline docs
2. Document Docling integration (API, configuration, examples)
3. Document PaddleOCR fallback (when it triggers, configuration)
4. Document routing logic (confidence thresholds, tuning)
5. Create user migration guide (upgrade path from v0.2.x)
6. Add examples for different document types
7. Use documentation-auditor agent for review
8. Use git-documentation-committer agent for commits
9. Tag v0.3.0 release

**Dependencies**: Phase 6 complete

**Deliverables**:
- Complete API documentation
- User migration guide
- Configuration examples
- Release tagged

**Verification**:
- [ ] Documentation complete and accurate
- [ ] Examples working
- [ ] Migration guide tested
- [ ] `/verify-docs` passing
- [ ] Release tagged

## Code Examples

### Current Behaviour (v0.2.X)

```python
# Simple Tesseract-based OCR with Camelot for tables
from ragged.processing import TesseractProcessor, CamelotExtractor

# Process PDF (slow, limited accuracy)
processor = TesseractProcessor()
text = processor.extract_text("document.pdf")  # 100 pages: ~300 seconds

# Extract tables separately (unreliable)
extractor = CamelotExtractor()
tables = extractor.extract_tables("document.pdf")  # ~70% accuracy

# Manual integration (text + tables)
combined = integrate_text_and_tables(text, tables)

# Issues:
# - Slow (100 pages/min)
# - Poor table accuracy (~70%)
# - No layout awareness
# - No reading order
# - Rotated text fails
```

### Enhanced Behaviour (v0.3.X - Automatic Routing)

```python
# Modern multi-modal processing with automatic routing
from ragged.processing import ProcessorRouter

# Initialize router (uses Docling + PaddleOCR fallback)
router = ProcessorRouter(
    confidence_threshold_high=0.85,  # Docling only
    confidence_threshold_low=0.70,   # PaddleOCR fallback
)

# Process PDF (automatic quality assessment and routing)
result = router.process("document.pdf")

# Comprehensive results:
print(f"Markdown:\n{result.markdown}")
print(f"Confidence: {result.confidence:.2%}")
print(f"Processor: {result.processor_used}")
print(f"Tables: {len(result.tables)} extracted")
print(f"Images: {len(result.images)} extracted")
print(f"Time: {result.processing_time:.2f}s")  # 100 pages: ~10 seconds (30× faster)

# Automatic handling:
# - Born-digital PDFs: Docling (computer vision) → 99% accuracy, <1s/page
# - Clean scans: Docling + EasyOCR → 98% accuracy, 2-3s/page
# - Messy/rotated: PaddleOCR fallback → 95% accuracy, 5-8s/page
# - Tables: TableFormer → 97.9% accuracy
# - Images: Extracted + llava descriptions
# - Layout: Preserved with reading order
```

### Explicit Processor Selection

```python
# Use Docling explicitly for born-digital PDFs (fastest)
from ragged.processing import DoclingProcessor

docling = DoclingProcessor(
    enable_tables=True,
    enable_formulas=True,
    enable_vision=True,
)

result = docling.process("born_digital.pdf")
# Result: 99% accuracy, <1s/page, tables + images extracted

# Use PaddleOCR explicitly for messy scans (most robust)
from ragged.processing import PaddleOCRProcessor

paddleocr = PaddleOCRProcessor(
    lang="en",
    use_angle_cls=True,  # Handle rotation
    use_gpu=True,
)

result = paddleocr.process("messy_scan.pdf")
# Result: 95% accuracy, handles rotated/skewed text, 5-8s/page
```

### Security Integration Example

```python
# Multi-modal processing with security best practices
from ragged.processing import ProcessorRouter
from ragged.privacy import CleanupScheduler
from ragged.utils import validate_path, enforce_file_limit
from pathlib import Path

# Validate user-provided path
user_pdf = validate_path(
    user_input_path,
    allowed_dir=Path("~/.ragged/uploads")
)

# Enforce file size limit
enforce_file_limit(user_pdf, max_size_mb=100)

# Process with automatic cleanup
router = ProcessorRouter()
result = router.process(user_pdf)

# Schedule cleanup of extracted images (TTL: 24 hours)
scheduler = CleanupScheduler()
scheduler.schedule_cleanup(
    data_path=Path("~/.ragged/temp/extractions"),
    ttl_days=1,
    cron_schedule="0 */6 * * *"
)

# Set restrictive permissions on temporary files
import os
for image in result.images:
    os.chmod(image, 0o600)
```

**Why This Improvement Matters**

Multi-modal support transforms ragged from handling simple text documents to processing real-world PDFs with tables, images, and complex layouts. The 30× performance improvement, 97.9% table accuracy, and automatic fallback handling make ragged suitable for production document workloads where reliability and speed are critical.

## Testing Requirements

### Unit Tests

- [ ] `DoclingProcessor` class (>80% coverage)
  - Layout analysis integration
  - Table extraction (TableFormer)
  - Text extraction methods
  - Output format conversion
  - Error handling

- [ ] `PaddleOCRProcessor` class (>80% coverage)
  - Text detection (rotated boxes)
  - Text recognition (multiple languages)
  - Output normalisation
  - Error handling

- [ ] `QualityAssessor` class (>80% coverage)
  - Born-digital detection
  - Scan quality scoring
  - Confidence aggregation
  - Edge cases (empty PDFs, corrupted files)

- [ ] `ProcessorRouter` class (>80% coverage)
  - Routing logic (all confidence ranges)
  - Fallback triggering
  - Processor selection
  - Error propagation

### Integration Tests

- [ ] Docling → ragged format conversion
- [ ] PaddleOCR → ragged format conversion
- [ ] Quality assessment → routing decision
- [ ] Confidence-based fallback (Docling → PaddleOCR)
- [ ] Vision integration (Docling images → llava)
- [ ] End-to-end pipeline (PDF → markdown + metadata)

### End-to-End Tests

- [ ] Born-digital PDF (100 pages) → <100s processing
- [ ] Clean scan (50 pages) → accurate text extraction
- [ ] Messy scan with rotation → PaddleOCR fallback triggers
- [ ] Complex tables → TableFormer extraction working
- [ ] Multi-column layout → reading order preserved
- [ ] Document with images → llava descriptions generated

### Security Tests

- [ ] Path traversal attempt → blocked
- [ ] Oversized PDF (>100MB) → rejected
- [ ] Malformed PDF → graceful error
- [ ] Temporary file cleanup → files deleted after TTL
- [ ] File permissions → restrictive (0o600)

### Performance Benchmarks

| Document Type | Target | Measurement |
|--------------|--------|-------------|
| Born-digital (100 pages) | <100s | Time from input to markdown output |
| Clean scan (50 pages) | <150s | Time from input to markdown output |
| Messy scan (20 pages) | <160s | Time from input to markdown output with fallback |
| Table extraction (10 complex tables) | >97% accuracy | Manual validation vs ground truth |
| Image extraction (20 images) | 100% extracted | All images present in output |

## Acceptance Criteria

- [ ] All 7 implementation phases complete
- [ ] All unit tests passing (>80% coverage per module)
- [ ] All integration tests passing
- [ ] All e2e tests passing
- [ ] All security tests passing
- [ ] Performance benchmarks met (95% PDF success rate)
- [ ] Docling accuracy >99% on born-digital PDFs
- [ ] Docling + PaddleOCR accuracy >95% on messy scans
- [ ] Table extraction accuracy >97% (TableFormer)
- [ ] Processing speed 5-30× faster than Tesseract
- [ ] Layout preservation working correctly
- [ ] Vision integration functional (images + llava)
- [ ] Tesseract and Camelot fully removed
- [ ] Documentation complete (API docs, migration guide, examples)
- [ ] `/verify-docs` passing
- [ ] British English compliance

## Related Versions

- **v0.3.0** - Complete multi-modal implementation (55-62h)

This feature is implemented entirely in v0.3.0. See [v0.3.0 roadmap](../v0.3.0.md) for detailed implementation plan with phase breakdowns, execution checklist, and agent workflow.

## Dependencies

### From v0.2.10/v0.2.11 (Security Foundation)

- `validate_path()` - Path traversal prevention
- `enforce_file_limit()` - File size limits
- `CleanupScheduler` - Automatic temporary file cleanup

### External Libraries

**Removed (v0.3.0)**:
- `pytesseract` (v0.3.0) - Replaced by Docling
- `camelot-py` (v0.11.0) - Replaced by Docling TableFormer

**Added (v0.3.0)**:
- **docling** (>= 2.0.0) - MIT license - Primary processor
- **paddleocr** (>= 2.8.0) - Apache 2.0 license - Fallback OCR
- **paddlepaddle** (>= 2.6.0) - Apache 2.0 license - PaddleOCR backend
- **opencv-python** (>= 4.8.0) - BSD license - Image preprocessing
- **Pillow** (>= 10.0.0) - HPND license - Image handling (already present)

All new dependencies are GPL-3.0 compatible.

### Hardware/System Requirements

**Minimum**:
- 8GB RAM (16GB recommended for large PDFs)
- 4 CPU cores
- 2GB disk space (for models and temporary files)

**Optimal**:
- 16GB+ RAM
- 8+ CPU cores
- GPU with 4GB+ VRAM (for PaddleOCR acceleration)
- 5GB disk space

**Note**: Docling and PaddleOCR work on CPU, but GPU significantly improves PaddleOCR performance (5-10× faster).

## Risk Assessment

### Technical Risks

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Docling dependency instability | Low | High | Pin version, extensive testing, monitor releases, PaddleOCR fallback available |
| PaddleOCR performance on large batches | Medium | Medium | Only use for low-confidence docs, async processing, user expectation management |
| Routing logic errors (wrong processor) | Medium | High | Extensive testing on diverse docs, configurable thresholds, logging for analysis |
| Breaking changes for existing users | High | Medium | Migration guide, automatic re-processing option, clear communication |
| Table extraction failures (2.1% failure rate) | Medium | Medium | Validate extraction, provide fallback formatting, allow manual correction |

### Performance Risks

- **Docling CPU performance**: Docling GPU utilisation is not yet optimal (may be slower than benchmarks suggest)
  - **Mitigation**: Test on actual hardware first, PaddleOCR can be primary if Docling underperforms, batch processing optimisation

- **PaddlePaddle complexity**: PaddlePaddle framework adds dependency complexity and installation challenges
  - **Mitigation**: Well-documented installation, Docker containers isolate dependencies, fallback is optional

- **Memory usage on large PDFs**: Processing 500+ page PDFs may exhaust memory
  - **Mitigation**: Page-by-page processing mode, configurable batch size, memory monitoring

### Security/Privacy Risks

- **Malicious PDF exploits**: Specially crafted PDFs could exploit parser vulnerabilities
  - **Mitigation**: File format validation, size limits, sandboxed processing (future), graceful error handling

- **Temporary file exposure**: Extracted images remain in temp directory
  - **Mitigation**: Restrictive file permissions (0o600), TTL-based cleanup (24 hours), secure temp directory

- **Path traversal via filenames**: User-provided paths could escape allowed directories
  - **Mitigation**: Strict path validation (v0.2.10), allowed directory whitelisting

## Related Documentation

- [Docling OCR Decision ADR](../../../decisions/2025-11-17-docling-ocr-decision.md) - Full rationale for Docling + PaddleOCR selection
- [v0.3.0 Roadmap](../v0.3.0.md) - Detailed implementation plan for multi-modal processing
- [v0.3 Planning](../../../planning/version/v0.3/README.md) - High-level v0.3 design goals
- [v0.3 Master Roadmap](../README.md) - Complete v0.3 overview with all 13 versions
- [Security Policy](../../../../security/policy.md#input-validation) - File upload security requirements
- [Privacy Architecture](../../../../security/privacy-architecture.md#data-lifecycle) - Temporary file management

---

**Total Feature Effort:** 57-71 hours (across all phases)
