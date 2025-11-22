# Document Normalisation Pipeline

**Purpose**: Design specification for converting all input formats to standardized Markdown
**Status:** Core feature for v0.2

---

## Overview

**ragged** implements a document normalisation pipeline that converts all input formats (PDF, HTML, DOCX, images, etc.) into a standardized **Markdown format** before chunking and embedding. This approach significantly enhances retrieval quality, consistency, and user experience.

## Why Normalise to Markdown?

### 1. **Consistent Chunking Across All Document Types**
- **Problem**: Different formats (PDF, HTML, DOCX) have different structures
- **Solution**: Markdown provides a universal structure (headings, lists, tables, code blocks)
- **Benefit**: Chunking algorithms work consistently regardless of source format

### 2. **Preserves Document Structure**
- **Headings**: `#`, `##`, `###` hierarchy enables semantic chunking
- **Lists**: Ordered and unordered lists preserved
- **Tables**: Structure maintained for accurate retrieval
- **Code Blocks**: Syntax preservation for technical documents
- **Emphasis**: Bold, italic, links retained

### 3. **Better Retrieval Quality**
- **Semantic chunking** can leverage heading boundaries
- **Late chunking** benefits from consistent structure
- **Context preservation**: Parent headings can be included in chunks
- **Citation quality**: Original structure makes source attribution clearer

### 4. **Enhanced User Experience**
- **Display**: Markdown renders beautifully in web UI
- **Citations**: Can show formatted source text, not raw HTML/PDF
- **Search highlighting**: Easier to highlight matches in Markdown
- **Export**: Users can export chunks as formatted documents

### 5. **Future-Proofing**
- **GraphRAG**: Markdown structure aids entity extraction
- **Multi-modal**: Images referenced in markdown can be processed separately
- **Fine-tuning**: Consistent format for training data if needed

## Document Processing Pipeline

```
┌─────────────┐
│ Input File  │
│ (any format)│
└─────┬───────┘
      │
      ▼
┌─────────────────────┐
│ Format Detection    │
│ (MIME type + magic) │
└─────┬───────────────┘
      │
      ▼
┌─────────────────────────────────────────────┐
│           Format-Specific Processing         │
│                                              │
│  ┌──────────┐  ┌──────────┐  ┌───────────┐ │
│  │   PDF    │  │   HTML   │  │  Scanned  │ │
│  │ (Docling)│  │(Trafilat)│  │   Image   │ │
│  └────┬─────┘  └────┬─────┘  └─────┬─────┘ │
│       │             │               │        │
│       │             │         ┌─────▼─────┐ │
│       │             │         │    OCR    │ │
│       │             │         │(PaddleOCR)│ │
│       │             │         └─────┬─────┘ │
│       └─────────────┴───────────────┘       │
└───────────────────┬─────────────────────────┘
                    │
                    ▼
          ┌──────────────────┐
          │ Metadata Extract │
          │ GROBID/Trafilat  │
          └────────┬─────────┘
                   │
                   ▼
          ┌──────────────────┐
          │ Normalise to MD  │
          │ Clean + Structure│
          └────────┬─────────┘
                   │
                   ▼
          ┌──────────────────┐
          │ Duplicate Check  │
          │ SHA256/MinHash   │
          └────────┬─────────┘
                   │
                   ▼
          ┌──────────────────┐
          │  Store MD File   │
          │  + Metadata JSON │
          └────────┬─────────┘
                   │
                   ▼
          ┌──────────────────┐
          │  Chunking        │
          │  (v0.1: basic,   │
          │   v0.3: semantic)│
          └────────┬─────────┘
                   │
                   ▼
          ┌──────────────────┐
          │  Embedding       │
          │  Vector Storage  │
          └──────────────────┘
```

## Format-Specific Processors

### 1. PDF Documents (Academic Papers, Books, Reports)

**Processor**: **IBM Docling** (primary)

**Why Docling?**
- Best-in-class table extraction (97.9% accuracy)
- Excellent structure preservation (headings, lists, sections)
- OCR support for scanned PDFs (30x faster than traditional)
- Self-hosted (no API costs, privacy-preserving)
- Open source (MIT license)
- Multi-format support (PDF, DOCX, PPTX, etc.)

**Installation**:
```python
# Python package
pip install docling

# With FastAPI integration
pip install fastapi uvicorn docling python-multipart
```

**Usage**:
```python
from docling.document_converter import DocumentConverter

converter = DocumentConverter()
result = converter.convert("paper.pdf")

# Export to markdown
markdown_text = result.document.export_to_markdown()
metadata = result.document.metadata  # Title, authors, etc.
```

**Alternative**: Marker (for speed on GPU infrastructure)
- 25 pages/second in batch mode (H100)
- Excellent benchmarks vs. commercial tools
- Falls back if Docling fails

### 2. HTML Documents (Saved Web Pages, News Articles)

**Processor**: **Trafilatura**

**Why Trafilatura?**
- Best benchmarks for web content extraction (2025)
- Superior metadata extraction (author, date, title, tags)
- Excellent boilerplate removal (ads, navigation, etc.)
- Markdown export built-in
- Production-proven (186K articles from 1.5K newspapers)

**Specific Sites** (from your collection):
- **Medium**: Article text, author, date, claps, tags
- **NYT/WaPo/WSJ/FT**: Article text, author, date, section
- **Academic blogs**: Full content with code blocks preserved

**Installation**:
```python
pip install trafilatura[all]
```

**Usage**:
```python
import trafilatura

# Read saved HTML file
with open("article.html") as f:
    html = f.read()

# Extract to markdown
markdown_text = trafilatura.extract(
    html,
    output_format="markdown",
    include_comments=False,
    include_tables=True,
    include_formatting=True
)

# Extract metadata
metadata = trafilatura.extract_metadata(html)
# Returns: title, author, date, sitename, categories, tags, description
```

**Fallback**: newspaper4k (for NLP features, keyword extraction)

### 3. Scanned Documents (Old Magazines, Image PDFs)

**Processor**: **PaddleOCR + PP-Structure**

**Why PaddleOCR?**
- Best open-source OCR accuracy (2025)
- PP-Structure for layout analysis (columns, tables, images)
- Multi-column support (critical for magazines)
- Reading order detection
- 80+ languages
- GPU acceleration

**Magazine-Specific Features**:
- **Multi-column layout** detection
- **Image extraction** with captions
- **Table recognition**
- **Reading order** preservation
- **Header/footer** detection

**Installation**:
```bash
# Basic
pip install paddleocr

# With layout analysis
pip install paddleocr paddlenlp
```

**Usage**:
```python
from paddleocr import PPStructure

# Initialize with layout analysis
engine = PPStructure(
    layout=True,  # Detect layout
    table=True,   # Extract tables
    ocr=True,     # Perform OCR
    show_log=False
)

# Process scanned image or PDF
result = engine("scanned_magazine.pdf")

# Result includes:
# - Layout regions (title, text, list, table, figure)
# - OCR text for each region
# - Reading order
# - Bounding boxes
```

**Alternative**: Surya OCR
- Excellent multi-column support
- 90+ languages
- Reading order detection
- Newer, potentially better for modern layouts

**Conversion to Markdown**:
- Reconstruct document structure based on layout analysis
- Convert regions to Markdown elements (headings, paragraphs, tables, lists)
- Preserve reading order
- Extract images as separate files, reference in Markdown

### 4. Microsoft Office Documents (DOCX, PPTX, XLSX)

**Processor**: **Docling** (same as PDF)

**Why?**
- Native support for Office formats
- Structure preservation
- Table extraction from Excel
- Slide content from PowerPoint

**Alternative**: Unstructured.io (if Docling fails)

### 5. Plain Text and Markdown

**Processor**: **Direct ingestion** (minimal processing)

- **Markdown**: Validate and normalise (consistent heading levels, etc.)
- **Plain Text**: Auto-detect structure (blank lines = paragraphs, etc.)
- **Code Files**: Wrap in code blocks with language detection

## Metadata Extraction

### Academic Papers (PDF)

**Tool**: **GROBID** (GeneRation Of BIbliographic Data)

**Extracted Fields** (68 labels):
- **Bibliographic**: Title, Authors (first/middle/last), Affiliations, Addresses
- **Publication**: Journal/Conference, Volume, Issue, Pages, DOI, PMID, arXiv ID
- **Content**: Abstract, Sections, References, Figures, Tables, Captions
- **Dates**: Publication date, submission date
- **Identifiers**: DOI, PMID, arXiv ID, ISBN/ISSN

**Installation**:
```bash
# Docker (recommended)
docker pull grobid/grobid:0.8.0

# Python client
pip install grobid-client-python
```

**Usage**:
```python
from grobid_client.grobid_client import GrobidClient

client = GrobidClient(config_path="./config.json")
client.process("processFulltextDocument",
               input_path="./pdfs",
               output="./output")
```

**Integration**:
- Run GROBID Docker container as microservice
- Call from ragged backend for PDFs identified as academic papers
- Fall back to Docling metadata if GROBID fails

### Web Articles (HTML)

**Tool**: **Trafilatura** (built-in metadata extraction)

**Extracted Fields**:
- **Core**: Title, Author, Date, Site name, URL
- **Extended**: Categories, Tags, Description, Language
- **Technical**: Modified date, canonical URL

**Schema Compliance**:
- Dublin Core compatible
- Schema.org NewsArticle/BlogPosting
- Open Graph Protocol

### Metadata Schema

See [metadata-schema.md](./metadata-schema.md) for complete specification.

## Duplicate Detection

See [duplicate-detection.md](./duplicate-detection.md) for complete strategy.

**Summary**:
1. **SHA256 hash** of normalised markdown (exact duplicates)
2. **MinHash+LSH** for near-duplicates (different filenames, minor edits)
3. **Embedding similarity** for semantic duplicates (rewrites, paraphrases)

## Storage Architecture

### Directory Structure

```
ragged_data/
├── originals/          # Original uploaded files (never modified)
│   ├── abc123.pdf
│   ├── def456.html
│   └── ghi789.jpg
├── normalised/         # Converted markdown files
│   ├── abc123.md       # From abc123.pdf
│   ├── def456.md       # From def456.html
│   └── ghi789.md       # From ghi789.jpg (OCR)
├── metadata/           # JSON metadata per document
│   ├── abc123.json     # {"title": "...", "authors": [...], ...}
│   ├── def456.json
│   └── ghi789.json
├── images/             # Extracted images (referenced in markdown)
│   ├── abc123_fig1.png
│   ├── abc123_fig2.png
│   └── def456_hero.jpg
└── duplicates.db       # SQLite DB tracking duplicate relationships
```

### Document ID Generation

```python
import hashlib

def generate_document_id(file_path: str) -> str:
    """Generate unique ID from file content (not filename)."""
    with open(file_path, 'rb') as f:
        content_hash = hashlib.sha256(f.read()).hexdigest()
    return content_hash[:12]  # First 12 chars (collision probability ~1e-14)
```

### Metadata JSON Format

```json
{
  "document_id": "abc123",
  "original_filename": "deep-learning-paper.pdf",
  "original_path": "/path/to/upload/deep-learning-paper.pdf",
  "file_type": "application/pdf",
  "file_size_bytes": 2458624,
  "upload_date": "2025-11-09T10:30:00Z",
  "processing_date": "2025-11-09T10:30:15Z",
  "processor": "docling-v1.0",

  "content_hash": "sha256:abc123def456...",
  "duplicate_of": null,  // or "def456" if duplicate
  "duplicates": [],      // Other IDs that duplicate this

  "document_type": "academic_paper",  // or "web_article", "book", "magazine", etc.

  "academic_metadata": {
    "title": "Deep Learning for Computer Vision",
    "authors": [
      {"first": "Jane", "middle": "A", "last": "Doe", "affiliation": "MIT"},
      {"first": "John", "last": "Smith", "affiliation": "Stanford"}
    ],
    "journal": "Nature",
    "volume": "615",
    "issue": "7950",
    "pages": "123-145",
    "year": 2023,
    "doi": "10.1038/s41586-023-12345-6",
    "pmid": null,
    "arxiv_id": "2301.12345",
    "abstract": "We present...",
    "keywords": ["deep learning", "computer vision"],
    "references_count": 87
  },

  "web_metadata": null,  // Only for web articles

  "structure": {
    "pages": 23,
    "sections": ["Introduction", "Methods", "Results", "Discussion"],
    "figures": 12,
    "tables": 5,
    "has_math": true,
    "has_code": false
  },

  "ocr_metadata": null,  // Only if OCR was performed

  "processing_metadata": {
    "markdown_path": "normalised/abc123.md",
    "image_paths": ["images/abc123_fig1.png", "images/abc123_fig2.png"],
    "processing_time_seconds": 15.3,
    "ocr_performed": false,
    "warnings": [],
    "errors": []
  }
}
```

## Quality Assurance

### 1. Markdown Validation

**Post-Processing Checks**:
- Heading hierarchy (no skipped levels: `##` after `####`)
- Table structure (consistent columns)
- Link validity (internal references, images exist)
- Code block language tags
- Special characters escaped

### 2. Metadata Completeness

**Required Fields** (enforced):
- document_id
- original_filename
- file_type
- upload_date
- content_hash

**Recommended Fields** (warnings if missing):
- title (extracted or derived from filename)
- document_type

### 3. OCR Quality Metrics

**Tracked Metrics**:
- Confidence scores per region
- Low-confidence regions flagged for review
- Character recognition accuracy (if ground truth available)

### 4. Duplicate Detection Accuracy

**Metrics**:
- Exact duplicates found (SHA256)
- Near-duplicates found (MinHash)
- False positive rate (manual review of sample)

## Performance Considerations

### Processing Speed Benchmarks (Target)

| Format | Tool | CPU (pages/sec) | GPU (pages/sec) | Notes |
|--------|------|-----------------|-----------------|-------|
| PDF (text) | Docling | 2-5 | 10-20 | With OCR: 30x slower on CPU |
| PDF (scanned) | PaddleOCR | 0.1-0.5 | 2-5 | Layout analysis adds overhead |
| HTML | Trafilatura | 20-50 | N/A | Very fast, CPU-only |
| DOCX | Docling | 5-10 | 15-30 | Simpler than PDF |

### Resource Requirements

**CPU-Only Setup**:
- RAM: 8GB minimum (16GB recommended)
- Storage: 2x input file size (originals + normalised)
- Expected: 2-5 seconds/page for PDFs

**GPU Setup**:
- GPU: 4GB VRAM minimum (8GB recommended)
- RAM: 16GB
- Expected: 10-20 seconds/page for scanned PDFs with OCR

### Batch Processing

**Queue System** (v0.3+):
- Asynchronous processing with Celery
- Priority queue (user-initiated > background)
- Progress tracking per document
- Retry logic for failures

## Error Handling

### Fallback Chain

1. **Primary processor fails** → Try alternative (e.g., Docling fails → Marker)
2. **Alternative fails** → Extract raw text (PyPDF2, BeautifulSoup)
3. **Raw extraction fails** → Store original, mark as "processing_failed"
4. **User notification** → Show failed documents, allow manual re-processing

### Common Failure Modes

| Issue | Primary Cause | Solution |
|-------|---------------|----------|
| PDF extraction fails | Encrypted/password-protected | Prompt for password |
| OCR produces gibberish | Wrong language detection | Allow manual language override |
| HTML extraction empty | Paywall/JavaScript-required | Manual content paste option |
| Table structure lost | Complex spanning cells | Flag for manual review |
| Metadata extraction fails | Non-standard format | Use filename/user-provided metadata |

## Version Roadmap

### v0.1 (Basic Ingestion)
**Goal**: Minimal viable document processing

**Supported**:
- PDF: PyMuPDF4LLM (simple, fast, no OCR)
- HTML: Trafilatura
- TXT/MD: Direct ingestion
- **No OCR**, **No GROBID**, **Basic metadata only**

**Rationale**: Get working system quickly, validate architecture

### v0.2 (Document Normalisation) ⭐ **KEY FEATURE**
**Goal**: Production-quality document processing

**Supported**:
- PDF: Docling (with OCR fallback)
- HTML: Trafilatura
- Scanned PDFs/Images: PaddleOCR
- DOCX/PPTX: Docling
- **Full metadata extraction**: GROBID + Trafilatura
- **Duplicate detection**: SHA256 + MinHash
- **Markdown normalisation**: All formats → clean MD

**Timeline**: +2 weeks to v0.2 (total 6-7 weeks)

**Rationale**: This is critical for quality. Must come early.

### v0.3 (Enhanced Processing)
**Goal**: Advanced metadata and duplicate handling

**Enhancements**:
- Batch processing queue (Celery)
- Enhanced duplicate detection (embedding similarity)
- Metadata enrichment (extract more fields)
- User feedback on OCR quality

### v1.0 (Production)
**Goal**: Enterprise-grade document processing

**Features**:
- Processing monitoring and analytics
- Automatic re-processing on format updates
- Plugin architecture for custom processors
- Admin UI for document management

## Testing Strategy

### Unit Tests

```python
def test_pdf_to_markdown_preserves_structure():
    """Test that headings, tables, lists are preserved."""
    converter = DocumentConverter()
    result = converter.convert("test_paper.pdf")
    markdown = result.document.export_to_markdown()

    assert "# Introduction" in markdown
    assert "## Methods" in markdown
    assert "| Header 1 | Header 2 |" in markdown  # Table
    assert "- List item" in markdown

def test_duplicate_detection_exact():
    """Test SHA256 detects exact duplicates."""
    hash1 = compute_content_hash("file1.pdf")
    hash2 = compute_content_hash("file1_copy.pdf")
    assert hash1 == hash2
```

### Integration Tests

```python
def test_full_pipeline_academic_paper():
    """Test complete pipeline from PDF to indexed chunks."""
    # Upload
    doc_id = upload_document("paper.pdf")

    # Wait for processing
    wait_for_processing(doc_id)

    # Check normalised markdown exists
    assert os.path.exists(f"normalised/{doc_id}.md")

    # Check metadata extracted
    metadata = load_metadata(doc_id)
    assert metadata["academic_metadata"]["title"] is not None
    assert len(metadata["academic_metadata"]["authors"]) > 0

    # Check chunks created
    chunks = get_chunks(doc_id)
    assert len(chunks) > 0

    # Check embeddings generated
    assert all(chunk.embedding is not None for chunk in chunks)
```

### Quality Evaluation

**RAGAS Metrics** (on processed documents):
- **Context Precision**: Are retrieved chunks relevant?
- **Context Recall**: Are all relevant chunks retrieved?
- **Faithfulness**: Do answers match source markdown?
- **Answer Relevance**: Do answers address the question?

**Normalisation Quality**:
- Manual review of 100 random documents
- Structure preservation score (headings, tables, lists intact)
- Metadata completeness score

## Future Enhancements

### v0.4+

1. **Agentic Chunking**: Use LLM to determine optimal chunk boundaries
2. **Multi-modal**: Process images, extract text from diagrams
3. **LaTeX Support**: Preserve mathematical equations
4. **Audio/Video**: Transcribe with Whisper, create markdown transcripts
5. **Code Repositories**: Process README, docstrings, comments
6. **Presentation Decks**: Slide-aware chunking

### v1.0+

1. **Incremental Updates**: Re-process only changed sections
2. **Version Control**: Track document versions (v1, v2, etc.)
3. **Collaborative Annotations**: User highlights, notes stored separately
4. **Export Options**: Markdown → PDF, DOCX, HTML

## References

- IBM Docling: https://github.com/docling-project/docling
- Trafilatura: https://github.com/adbar/trafilatura
- PaddleOCR: https://paddlepaddle.github.io/PaddleOCR/
- GROBID: https://github.com/kermitt2/grobid
- Surya OCR: https://github.com/datalab-to/surya
- Marker: https://github.com/VikParuchuri/marker

---

**Next Steps**: See [metadata-schema.md](./metadata-schema.md) and [duplicate-detection.md](./duplicate-detection.md) for detailed specifications.

**Implementation**: Begin in v0.2 after basic RAG pipeline (v0.1) is validated.

---

## Related Documentation

- [PDF Processing (ADR-0007)](../../../decisions/adrs/0007-pymupdf4llm-for-pdf-processing.md) - PDF handling
- [Markdown Format (ADR-0014)](../../../decisions/adrs/0014-markdown-as-intermediate-format.md) - Intermediate format
- [Metadata Schema](./metadata-schema.md) - Document metadata

---
