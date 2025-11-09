# Document Processing Technologies

**Last Updated**: 2025-11-09
**Purpose**: Comprehensive evaluation of document processing tools for ragged
**Implementation**: v0.2+

---

## Overview

This document evaluates state-of-the-art (2025) technologies for converting various document formats to Markdown, extracting metadata, and handling OCR. These tools form the foundation of ragged's document normalization pipeline.

## Document-to-Markdown Converters

### IBM Docling ⭐ RECOMMENDED

**Version**: 1.x (2024/2025)
**License**: MIT (Open Source)
**Primary Use**: PDF, DOCX, PPTX, XLSX → Markdown

#### Capabilities

- **Multi-format support**: PDF, DOCX, PPTX, XLSX, Images, HTML, AsciiDoc, Markdown
- **Advanced AI models**:
  - DocLayNet for layout analysis
  - TableFormer for complex table recognition (97.9% accuracy)
- **OCR support**: 30x faster than traditional approaches
- **Structure preservation**: Near-perfect rows/columns in tables
- **Export formats**: Markdown, HTML, DocTags, lossless JSON

####Installation

```bash
# Python package
pip install docling

# With FastAPI integration
pip install fastapi uvicorn docling python-multipart

# Docker (recommended for production)
docker pull docling/docling:latest
```

#### Usage Example

```python
from docling.document_converter import DocumentConverter

converter = DocumentConverter()
result = converter.convert("research-paper.pdf")

# Export to markdown
markdown_text = result.document.export_to_markdown()

# Access metadata
metadata = {
    "title": result.document.title,
    "authors": result.document.authors,
    "page_count": result.document.num_pages
}
```

#### Pros

- ✅ Best table extraction (97.9% accuracy)
- ✅ Self-hostable (no per-page API charges)
- ✅ Open source (MIT license)
- ✅ Structure preservation excellent
- ✅ Multi-format support
- ✅ OCR integrated

#### Cons

- ❌ Larger resource footprint (~8GB Docker image with full models)
- ❌ Some accuracy issues with currency symbols/footnotes
- ❌ Newer tool (less battle-tested than alternatives)

#### Performance

- **CPU**: 2-5 pages/second
- **GPU**: 10-20 pages/second (with OCR)
- **Memory**: ~2GB RAM minimum
- **Docker**: 500MB (CPU-optimized) to 8GB (full models)

---

### Marker

**Version**: 1.10.1 (September 2025)
**License**: Open Source
**Primary Use**: High-speed batch PDF processing

#### Capabilities

- **Speed**: 10x faster than Nougat, 25 pages/sec on H100 (batch mode)
- **Multi-format**: PDF, images, PPTX, DOCX, XLSX, HTML, EPUB
- **Quality**: Superior to LlamaParse, Mathpix in benchmarks
- **OCR**: Uses Surya OCR (optional ocrmypdf for speed)
- **GPU acceleration**: Optimized for CUDA

#### Installation

```bash
pip install marker-pdf

# GPU setup
export TORCH_DEVICE=cuda
export INFERENCE_RAM=8  # GB, match your GPU VRAM
```

#### Usage Example

```python
from marker.convert import convert_single_pdf

markdown, metadata = convert_single_pdf(
    "paper.pdf",
    output_format="markdown",
    use_llm=True  # Optional, highest accuracy
)
```

#### Pros

- ✅ Extremely fast (25 pages/sec with GPU)
- ✅ Excellent benchmarks vs. commercial tools
- ✅ GPU acceleration
- ✅ Open source

#### Cons

- ❌ Requires ~3GB VRAM (default)
- ❌ Best results need GPU
- ❌ Figure processing not perfect

#### Performance

- **CPU**: Moderate
- **GPU**: 25 pages/sec (H100 batch mode)
- **Memory**: 3GB VRAM recommended

**Use Case**: Fallback for Docling, batch processing large PDF collections

---

### PyMuPDF4LLM

**Version**: 0.1.9 (November 2025)
**License**: AGPL/Commercial
**Primary Use**: Simple, fast PDF→Markdown

#### Capabilities

- Lightweight and fast
- Multi-column page detection
- Table detection (heuristic)
- Image extraction (PNG + Markdown references)
- Direct LlamaIndex integration

#### Installation

```bash
pip install pymupdf4llm
```

#### Usage Example

```python
import pymupdf4llm

markdown = pymupdf4llm.to_markdown("document.pdf")

# With images
markdown = pymupdf4llm.to_markdown(
    "document.pdf",
    write_images=True,
    image_path="./images/"
)
```

#### Pros

- ✅ Very lightweight and fast
- ✅ Simple installation
- ✅ Good multi-column support
- ✅ LlamaIndex integration

#### Cons

- ❌ PDF-only (no DOCX, HTML, etc.)
- ❌ Simpler table detection vs. Docling
- ❌ No OCR support
- ❌ Less sophisticated than AI-powered alternatives

#### Performance

- **CPU**: Very fast (5-10 pages/sec)
- **Memory**: Minimal

**Use Case**: v0.1 simple PDF ingestion (before Docling in v0.2)

---

## OCR Technologies

### PaddleOCR + PP-Structure ⭐ RECOMMENDED

**Version**: 2.7+ (2024/2025)
**License**: Apache 2.0 (Open Source)
**Primary Use**: Scanned documents with complex layouts

#### Capabilities

- **80+ languages** supported
- **PP-Structure**: Layout analysis (tables, multi-column, images)
- **Best open-source accuracy** (benchmarks)
- **GPU acceleration**: TensorRT optimization
- **Reading order detection**

#### Installation

```bash
# Basic
pip install paddleocr paddlenlp

# GPU support (recommended)
# CUDA 11.8 + cuDNN 8.9 OR CUDA 12.6 + cuDNN 9.5
pip install paddlepaddle-gpu
```

#### Usage Example

```python
from paddleocr import PPStructure

# Initialize with layout analysis
engine = PPStructure(
    layout=True,    # Detect layout regions
    table=True,     # Extract tables
    ocr=True,       # Perform OCR
    show_log=False
)

# Process scanned document
result = engine("scanned_magazine.pdf")

# Result includes:
# - Layout regions (title, text, list, table, figure)
# - OCR text per region
# - Reading order
# - Bounding boxes
```

#### Pros

- ✅ Best open-source accuracy
- ✅ Superior for structured documents (tables, magazines)
- ✅ Multi-column support excellent
- ✅ GPU acceleration
- ✅ Production-ready

#### Cons

- ❌ More complex installation (CUDA/cuDNN setup)
- ❌ Heavier dependencies vs. alternatives

#### Performance

- **CPU**: 0.1-0.5 pages/sec
- **GPU**: 2-5 pages/sec
- **Memory**: GPU setup recommended

**Use Case**: Scanned magazines, multi-column documents, complex layouts

---

### Surya OCR

**Version**: 1.0+ (2024)
**License**: Open Source
**Primary Use**: Modern multi-column OCR

#### Capabilities

- **90+ languages**
- **Multi-column layout preservation**
- **Reading order detection**
- **Layout analysis** (tables, images, captions, headers)
- **Low-resource language support**: 2.61% WER

#### Installation

```bash
pip install surya-ocr

# GPU recommended
export TORCH_DEVICE=cuda
```

#### Usage Example

```python
from surya import OCREngine

engine = OCREngine()
result = engine.process("scanned_document.pdf")

# Get text with layout info
for region in result.regions:
    print(f"Type: {region.type}, Text: {region.text}")
```

#### Pros

- ✅ Modern, AI-powered
- ✅ Excellent layout preservation
- ✅ 90+ languages
- ✅ Good multi-column support

#### Cons

- ❌ Requires GPU for best performance
- ❌ Newer (less battle-tested)

#### Performance

- **CPU**: Slow
- **GPU**: Fast
- **Memory**: GPU recommended

**Use Case**: Alternative to PaddleOCR, modern scanned documents

---

### Tesseract OCR (Reference - NOT Recommended for ragged)

**Version**: 5.x
**License**: Apache 2.0
**Primary Use**: Legacy OCR

#### Why Not Recommended for ragged?

- ❌ Poor multi-column handling (critical for magazines)
- ❌ Breaks words incorrectly
- ❌ Slower than modern alternatives
- ❌ Lower accuracy on complex layouts

**Only use if**: Need 100+ language support and have simple, single-column documents.

---

## Web Content Extraction

### Trafilatura ⭐ RECOMMENDED

**Version**: 2.0.0 (2025)
**License**: Apache 2.0 (Open Source)
**Primary Use**: News articles, blog posts, web content

#### Capabilities

- **Best benchmarks** for web content extraction (2025)
- **Metadata extraction**: title, author, date, site, categories, tags, language
- **Boilerplate removal**: Superior to competitors
- **Multiple output formats**: CSV, JSON, HTML, Markdown, TXT, XML
- **Production-proven**: 186K articles from 1.5K newspapers

#### Installation

```bash
pip install trafilatura[all]
```

#### Usage Example

```python
import trafilatura

# Read saved HTML file
with open("medium_article.html") as f:
    html = f.read()

# Extract to markdown
markdown = trafilatura.extract(
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

#### Pros

- ✅ Best overall extraction accuracy
- ✅ Excellent metadata support
- ✅ Multiple output formats
- ✅ Active development (2.0 in 2025)
- ✅ Lightweight

#### Cons

- ❌ Web-focused (not for PDFs)

#### Performance

- **Speed**: 20-50 pages/sec (CPU-only)
- **Memory**: Minimal

**Use Case**: Primary tool for saved HTML from Medium, NYT, WaPo, WSJ, FT

---

### newspaper4k

**Version**: Active fork (2024/2025)
**License**: MIT
**Primary Use**: News articles with NLP features

#### Capabilities

- **NLP integration**: Keyword extraction, summarization
- **0.949 F1 score** (vs. 0.912 for abandoned newspaper3k)
- **Multilingual support**

#### Installation

```bash
# macOS
brew install libxml2 libxslt libtiff libjpeg webp little-cms2

# Then
pip install newspaper4k
```

#### Pros

- ✅ NLP features (keywords, summary)
- ✅ Good metadata extraction
- ✅ Active fork (vs. abandoned newspaper3k)

#### Cons

- ❌ System dependencies (libxml2, etc.)
- ❌ Lower precision than Trafilatura

**Use Case**: Secondary option if NLP features needed

---

## Metadata Extraction

### GROBID ⭐ RECOMMENDED

**Version**: 0.8.0 (2024/2025)
**License**: Apache 2.0 (Open Source)
**Primary Use**: Academic paper metadata extraction

#### Capabilities

- **68 bibliographic labels**: title, authors (first/middle/last), affiliations, addresses, journal, volume, issue, pages, DOI, PMID
- **Full text structures**: sections, paragraphs, references, figures, captions
- **Reference extraction**: ~0.87 F1-score (PubMed), ~0.90 (bioRxiv)
- **Processing**: 2-5 seconds/page, >90% accuracy
- **Production deployments**: ResearchGate, Semantic Scholar, HAL, scite.ai, Academia.edu

#### Installation

```bash
# Docker (recommended)
docker pull grobid/grobid:0.8.0

# Python client
pip install grobid-client-python
```

#### Usage Example

```python
from grobid_client.grobid_client import GrobidClient

client = GrobidClient(config_path="./config.json")
client.process(
    "processFulltextDocument",
    input_path="./pdfs",
    output="./output"
)

# Outputs structured XML/TEI with all metadata
```

#### Pros

- ✅ Production-ready (major platforms use it)
- ✅ Comprehensive metadata (68 labels)
- ✅ High accuracy (>90%)
- ✅ Fast (2-5 sec/page)
- ✅ Docker deployment

#### Cons

- ❌ Requires Docker for Windows
- ❌ Java-based (Python client is wrapper)
- ❌ Academic focus only

#### Performance

- **Speed**: 2-5 sec/page
- **Memory**: ~500MB-8GB Docker image

**Use Case**: Academic papers (PDFs identified as research papers)

---

## Duplicate Detection

### datasketch (MinHash + LSH)

**Version**: Latest (2024/2025)
**License**: MIT (Open Source)
**Primary Use**: Near-duplicate detection at scale

#### Installation

```bash
pip install datasketch
```

#### Usage Example

```python
from datasketch import MinHash, MinHashLSH

# Initialize LSH index
lsh = MinHashLSH(threshold=0.8, num_perm=128)

# Create MinHash for document
m = MinHash(num_perm=128)
for word in document.split():
    m.update(word.encode('utf-8'))

# Add to index
lsh.insert("doc1", m)

# Query for similar documents
similar = lsh.query(new_minhash)
```

**Use Case**: Level 2 duplicate detection in ragged

---

## Comparison Matrix

| Tool | Format | Speed | Accuracy | OCR | GPU | Use in ragged |
|------|--------|-------|----------|-----|-----|---------------|
| **Docling** | PDF, DOCX, PPTX | Medium | Excellent (97.9% tables) | Yes | Optional | v0.2+ (primary) |
| **Marker** | PDF, multi | Very Fast | Excellent | Yes | Recommended | v0.2+ (fallback) |
| **PyMuPDF4LLM** | PDF only | Fast | Good | No | No | v0.1 (simple) |
| **PaddleOCR** | Images, PDFs | Medium | Best OSS | Yes | Recommended | v0.2+ (scanned) |
| **Surya** | Images, PDFs | Medium | Excellent | Yes | Recommended | v0.2+ (alternative OCR) |
| **Trafilatura** | HTML | Very Fast | Best | No | No | v0.2+ (web content) |
| **GROBID** | PDF (academic) | Fast | >90% | No | No | v0.2+ (metadata) |
| **datasketch** | Text | Very Fast | Good | N/A | No | v0.2+ (duplicates) |

---

## Version Roadmap

### v0.1
- PyMuPDF4LLM (simple PDF)
- Trafilatura (HTML)
- No OCR
- No GROBID

### v0.2 ⭐
- **Docling** (PDF, DOCX, PPTX with OCR)
- **PaddleOCR** (scanned documents)
- **Trafilatura** (HTML)
- **GROBID** (academic metadata)
- **datasketch** (MinHash duplicate detection)

### v0.3+
- Marker (batch processing, GPU acceleration)
- Surya OCR (alternative OCR)
- Enhanced metadata extraction
- LLM-based metadata enrichment

---

## Installation Script (v0.2)

```bash
#!/bin/bash

# Core document processing
pip install docling
pip install trafilatura[all]
pip install python-magic
pip install datasketch

# Metadata extraction
pip install grobid-client-python

# OCR (optional, GPU recommended)
pip install paddleocr paddlenlp

# Docker for GROBID
docker pull grobid/grobid:0.8.0
```

---

## References

- **Docling**: https://github.com/docling-project/docling
- **Marker**: https://github.com/VikParuchuri/marker
- **PyMuPDF4LLM**: https://github.com/pymupdf/PyMuPDF4LLM
- **PaddleOCR**: https://paddlepaddle.github.io/PaddleOCR/
- **Surya**: https://github.com/datalab-to/surya
- **Trafilatura**: https://github.com/adbar/trafilatura
- **GROBID**: https://github.com/kermitt2/grobid
- **datasketch**: https://github.com/ekzhu/datasketch

---

**Next Steps**: Begin v0.2 implementation with Docling, Trafilatura, PaddleOCR, and GROBID integration.
