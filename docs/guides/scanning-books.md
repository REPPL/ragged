# Scanning Books with Ragged

**v0.4.9: Messy Scans to Perfect PDFs**

This guide shows you how to use ragged's scan processing feature to convert messy scanned documents into perfect, searchable PDFs with automatically extracted metadata.

## Overview

Ragged's scan processing pipeline transforms your scanned books and documents through 5 automated phases:

1. **Preprocessing**: OCR, image enhancement, and PDF creation
2. **Auto-Correction**: Page rotation, reordering, and duplicate detection
3. **Metadata Extraction**: Title, author, year, publisher from title pages
4. **Markdown Export**: Convert to markdown for text analysis
5. **Organization**: Semantic file naming and lineage tracking

**Privacy**: All processing happens 100% locally on your computer. No internet connection required, no data leaves your device.

## Quick Start

Process a single PDF:
```bash
ragged scan process ~/scans/book.pdf
```

Process a folder of images:
```bash
ragged scan process ~/scans/book-folder/
```

Preview without processing:
```bash
ragged scan process ~/scans/book.pdf --dry-run
```

## Input Formats

Ragged accepts various input formats:

### Single Files

**PDF files**:
```bash
ragged scan process ~/scans/scanned-book.pdf
```

**Image files** (JPG, PNG, TIFF, BMP):
```bash
ragged scan process ~/scans/page-001.jpg
```

### Folders

**Folder of images** (will be merged into single PDF):
```bash
ragged scan process ~/scans/book-images/
```

**Folder of PDFs** (will be merged):
```bash
ragged scan process ~/scans/book-chapters/
```

**Mixed content** (images and PDFs):
```bash
ragged scan process ~/scans/mixed-content/
```

Ragged automatically:
- Detects file types
- Sorts files naturally (scan_001, scan_002, etc.)
- Merges into single PDF
- Applies OCR where needed

## Common Scenarios

### Scenario 1: Scanned Book with Misordered Pages

Your scanner saved pages out of order (page 3 came before page 2):

```bash
ragged scan process ~/scans/messy-book.pdf
```

Ragged will:
- Extract page numbers from headers/footers
- Detect that pages are misordered
- Automatically reorder based on logical page numbers
- Create correctly ordered PDF

**Result**: `~/.ragged/documents/corrected/Book-Title-Author-Year.pdf`

### Scenario 2: Low-Quality Scans

Your scans are blurry, skewed, or have poor contrast:

```bash
ragged scan process ~/scans/blurry-scan.pdf --ocr-engine paddleocr
```

Ragged will:
- Deskew rotated pages
- Enhance contrast (CLAHE)
- Reduce noise
- Apply high-accuracy OCR (PaddleOCR)

**Options**:
- `--ocr-engine auto`: Automatic selection (default)
- `--ocr-engine easyocr`: Fast OCR (90-95% accuracy)
- `--ocr-engine paddleocr`: Best quality (95-98% accuracy)

### Scenario 3: Multiple Scanned Books

Process an entire directory of books:

```bash
ragged scan process ~/scans/ --batch
```

Each book will be:
- Processed independently
- Named semantically (Title-Author-Year.pdf)
- Tracked in processing log
- Organised in structured directories

### Scenario 4: Foreign Language Documents

Scan a French book:

```bash
ragged scan process ~/scans/livre-francais.pdf --ocr-language fra
```

Supported languages: 80+ (ISO 639-2/3 codes)
- English: `eng`
- French: `fra`
- German: `deu`
- Spanish: `spa`
- Italian: `ita`
- Portuguese: `por`
- Chinese: `chi_sim` / `chi_tra`
- Japanese: `jpn`
- Korean: `kor`
- Arabic: `ara`
- Russian: `rus`

[Full language list](https://github.com/PaddlePaddle/PaddleOCR/blob/release/2.8/doc/doc_en/multi_languages_en.md)

### Scenario 5: GPU Acceleration

If you have a CUDA-capable GPU or Apple Silicon:

```bash
ragged scan process ~/scans/large-book.pdf --gpu
```

Speeds up:
- OCR processing (2-5x faster)
- Image preprocessing

## Output Structure

Ragged organises processed documents into a structured directory:

```
~/.ragged/
├── documents/              # Processed scans
│   ├── originals/          # Immutable backups
│   │   └── abc123.../      # Content hash
│   │       └── original.pdf
│   ├── corrected/          # Clean, searchable PDFs
│   │   └── The-Art-of-RAG-Smith-2024.pdf
│   └── markdown/           # Markdown exports
│       └── The-Art-of-RAG-Smith-2024.md
└── metadata/
    └── processing_log.jsonl    # Lineage tracking
```

### File Naming

**Semantic naming** (default):
- Format: `Title-Author-Year.pdf`
- Example: `The-Art-of-RAG-Smith-2024.pdf`
- Falls back to `Scanned-Book-YYYYMMDD.pdf` if metadata unavailable

**Hash-based naming**:
```bash
ragged scan process book.pdf --naming-convention hash
```
- Format: `<16-char-hash>.pdf`
- Example: `abc123def456.pdf`

**Original naming**:
```bash
ragged scan process book.pdf --naming-convention original
```
- Keeps original filename (sanitised)

### Duplicate Handling

If a file with the same name already exists:
- First: `Book-Title-2024.pdf`
- Second: `Book-Title-2024-001.pdf`
- Third: `Book-Title-2024-002.pdf`

## Advanced Options

### Custom Output Directory

```bash
ragged scan process book.pdf --output-dir ~/Documents/Books
```

Default: `~/.ragged/documents/`

### Force OCR

Force OCR even if PDF already has text layer:

```bash
ragged scan process book.pdf --force-ocr
```

Useful for:
- Low-quality embedded text
- Incorrectly recognised text
- Missing text in some pages

### Disable Auto-Reordering

If you want pages in original order:

```bash
ragged scan process book.pdf --no-reorder-pages
```

**Not recommended**: Only use if you know pages are already correct.

### Skip Markdown Export

If you only want the PDF:

```bash
ragged scan process book.pdf --no-export-markdown
```

### Don't Keep Originals

If you want to save disk space:

```bash
ragged scan process book.pdf --no-keep-original
```

**Warning**: Original files won't be backed up. Make sure you have your own backup.

## Metadata Extraction

Ragged automatically extracts bibliographic metadata from scanned documents:

### What Gets Extracted

- **Title**: Book or document title
- **Author**: Author name(s)
- **Publication Year**: Year published
- **Publisher**: Publisher name

### How It Works

Ragged uses a cascading extraction strategy (100% offline):

1. **PDF Embedded Metadata** (fast, often incomplete)
2. **Title Page OCR + Regex** (main method, 70-80% accuracy)
   - Analyses first 3 pages
   - Looks for patterns like "by Author Name", "Copyright © Year"
3. **Fallback** (filename sanitisation)

### Confidence Scoring

Each extraction gets a confidence score:
- **High (0.7-1.0)**: Title, author, and year found
- **Medium (0.5-0.7)**: Partial metadata
- **Low (0.1-0.5)**: Fallback to filename

### Privacy

**No web lookups**: Ragged never connects to the internet for metadata. No ISBN lookups, no API calls, no data collection.

**Future**: Optional web lookup will be added in v0.8.x as an opt-in feature.

### Customise Metadata Extraction

Analyse more pages for metadata:

```bash
# Check first 5 pages instead of 3
ragged scan process book.pdf --metadata-titlepage-pages 5
```

Note: This is a configuration setting, not a CLI option. Set in `~/.ragged/config.yml`:

```yaml
scan_metadata_titlepage_pages: 5
```

## Lineage Tracking

Every processed document is tracked in `~/.ragged/metadata/processing_log.jsonl`:

```json
{
  "lineage_id": "20250123103000-abc12345",
  "timestamp": "2025-01-23T10:30:00Z",
  "original": {
    "path": "/path/to/original.pdf",
    "backup": "/Users/name/.ragged/documents/originals/abc123.../original.pdf",
    "size_bytes": 1234567,
    "hash": "abc123..."
  },
  "processed": {
    "corrected_pdf": "/Users/name/.ragged/documents/corrected/Title-Author-2024.pdf",
    "markdown": "/Users/name/.ragged/documents/markdown/Title-Author-2024.md"
  },
  "metadata": {
    "title": "The Art of RAG",
    "author": "Smith",
    "year": 2024,
    "publisher": "Tech Press"
  },
  "processor_version": "v0.4.9"
}
```

This provides:
- Complete processing history
- Original file hash (prevents duplicates)
- Metadata extraction results
- Paths to all outputs

## Configuration

Create `~/.ragged/config.yml` to customise defaults:

```yaml
# OCR settings
scan_ocr_engine: paddleocr      # auto, easyocr, paddleocr
scan_ocr_language: eng          # ISO 639-2/3 code
scan_ocr_gpu: false             # Use GPU if available
scan_force_ocr: false           # Force OCR even if text exists

# Processing settings
scan_pdf_dpi: 300               # DPI for PDF to image (150-600)
scan_enable_preprocessing: true  # Image enhancement
scan_auto_reorder: true         # Automatic page reordering
scan_export_markdown: true      # Export to markdown
scan_keep_originals: true       # Backup original files

# Output settings
scan_output_dir: null           # null = ~/.ragged/documents/
scan_naming_convention: title-author-year  # title-author-year, hash, original

# Metadata settings
scan_metadata_titlepage_pages: 3  # Pages to analyse (1-10)
scan_enable_lineage_tracking: true
```

## Troubleshooting

### "Unable to get page count. Is poppler installed and in PATH?"

**Cause**: Poppler system dependency is not installed.

**What is poppler?** Poppler provides command-line tools (`pdftoppm`, `pdfinfo`) required by `pdf2image` to convert PDF pages to images for OCR processing.

**Solution**:

**macOS:**
```bash
brew install poppler

# Verify installation
pdfinfo --version
```

**Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install poppler-utils

# Verify installation
pdfinfo --version
```

**Windows:**
1. Download poppler from [poppler-windows releases](https://github.com/oschwartz10612/poppler-windows/releases/)
2. Extract to `C:\Program Files\poppler`
3. Add `C:\Program Files\poppler\Library\bin` to PATH

After installing poppler, retry the scan command.

### "OCR failed" Error

**Cause**: OCR engine couldn't process the image.

**Solution**:
1. Try different OCR engine:
   ```bash
   ragged scan process book.pdf --ocr-engine paddleocr
   ```
2. Check image quality (very blurry images may fail)
3. Ensure dependencies installed: `pip install paddleocr easyocr`

### Pages Still Out of Order

**Cause**:
- Pages don't have detectable page numbers
- Page numbers in unusual locations
- Custom page numbering (roman numerals, etc.)

**Solution**:
1. Check that pages have visible page numbers in headers/footers
2. Manually reorder before processing
3. Future: Manual verification UI (v0.8.x)

### Incorrect Metadata

**Cause**: Title page format doesn't match regex patterns.

**Solution**:
- Current: Manually rename files after processing
- Future: Manual metadata editing (v0.8.x), web lookup option (v0.8.x)

### Slow Processing

**Solution**:
1. Use GPU acceleration:
   ```bash
   ragged scan process book.pdf --gpu
   ```
2. Use faster OCR:
   ```bash
   ragged scan process book.pdf --ocr-engine easyocr
   ```
3. Reduce PDF DPI (in config.yml):
   ```yaml
   scan_pdf_dpi: 150  # Lower = faster
   ```

### Out of Disk Space

**Solution**:
1. Don't keep originals:
   ```bash
   ragged scan process book.pdf --no-keep-original
   ```
2. Skip markdown export:
   ```bash
   ragged scan process book.pdf --no-export-markdown
   ```
3. Clean old backups:
   ```bash
   rm -rf ~/.ragged/documents/originals/*
   ```

## Best Practices

### 1. Test with Dry Run First

```bash
ragged scan process ~/scans/book.pdf --dry-run
```

Preview what will be processed before committing.

### 2. Keep Originals (Default)

Always keep backups of original scans. Storage is cheap, rescanning is expensive.

### 3. Use Batch Processing

Process entire directories at once:

```bash
ragged scan process ~/scans/ --batch
```

Ragged handles each file independently.

### 4. Check Metadata After Processing

Open the corrected PDF and verify:
- Title is correct
- Author is correct
- Pages are in order

### 5. Use Quality OCR for Important Documents

For archival or important documents:

```bash
ragged scan process important.pdf --ocr-engine paddleocr
```

95-98% accuracy vs 90-95% for EasyOCR.

## Next Steps

After processing your scans:

1. **Ingest into RAG**:
   ```bash
   ragged ingest pdf ~/.ragged/documents/corrected/Book-Title-2024.pdf
   ```

2. **Query the document**:
   ```bash
   ragged query text "What is RAG?"
   ```

3. **Explore markdown**:
   - Open `~/.ragged/documents/markdown/Book-Title-2024.md`
   - Use in editors, note-taking apps, or analysis tools

## See Also

- [Tutorial: Your First Scan](../tutorials/your-first-scan.md)
- [API Reference: Scan Processing](../reference/scan-api.md)
- [Configuration Reference](../reference/configuration.md)
