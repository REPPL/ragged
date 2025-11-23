# Your First Scan: Converting a Messy Book to Perfect PDF

**v0.4.9: Step-by-Step Tutorial**

This tutorial walks you through processing your first scanned book with ragged, from a messy collection of scans to a perfect, searchable PDF with metadata.

**What you'll learn:**
- How to process a single scanned book
- How ragged automatically fixes common scan issues
- How to verify the results
- How to integrate processed scans into your RAG system

**Time required:** 10-15 minutes

**What you need:**
- Ragged installed (`pip install ragged`)
- A scanned book (PDF or folder of images)

---

## Step 1: Prepare Your Scan

For this tutorial, we'll use a scanned book as an example. Your scan can be:

**Option A: Single PDF file**
```
~/scans/my-book.pdf
```

**Option B: Folder of images**
```
~/scans/my-book/
├── scan_001.jpg
├── scan_002.jpg
├── scan_003.jpg
└── ...
```

**Option C: Mixed folder**
```
~/scans/my-book/
├── chapter1.pdf
├── chapter2.pdf
└── images/
    ├── cover.jpg
    └── back.jpg
```

**For this tutorial**, let's assume you have `~/scans/philosophy-book.pdf` (a scanned PDF from your scanner).

---

## Step 2: Preview What Will Happen (Dry Run)

Before processing, let's preview what ragged will do:

```bash
ragged scan process ~/scans/philosophy-book.pdf --dry-run
```

**Example output:**
```
╭─ Scan Processing Preview ─────────────────────────────╮
│                                                        │
│ Input: /Users/you/scans/philosophy-book.pdf           │
│ Type: Single PDF                                       │
│ Pages: 245                                             │
│                                                        │
│ Processing Plan:                                       │
│ ✓ Detect text layer (or apply OCR)                    │
│ ✓ Correct rotation and page order                     │
│ ✓ Extract metadata (title, author, year)              │
│ ✓ Export to markdown                                  │
│ ✓ Organize with semantic filename                     │
│                                                        │
│ Output: ~/.ragged/documents/corrected/                 │
│                                                        │
╰────────────────────────────────────────────────────────╯
```

**What this tells you:**
- ragged detected a single PDF with 245 pages
- It will check for text (or add OCR if missing)
- Pages will be automatically corrected
- Metadata will be extracted
- Output will go to `~/.ragged/documents/`

**Tip:** Always run `--dry-run` first to preview changes.

---

## Step 3: Process the Scan

Now let's actually process the scan:

```bash
ragged scan process ~/scans/philosophy-book.pdf
```

**What happens now:**

### Phase 1: Preprocessing (10-30 seconds)
```
[1/5] Preprocessing...
  ✓ Detected text layer
  ✓ No OCR needed
  ✓ Validated 245 pages
```

**Ragged checks:**
- Does the PDF have embedded text? (If not, applies OCR)
- Are images clear enough? (Enhances if needed)
- Are pages readable?

### Phase 2: Auto-Correction (20-60 seconds)
```
[2/5] Auto-correcting...
  ✓ Detected rotation: 2 pages rotated 90°
  ✓ Corrected rotation
  ✓ Extracted page numbers from headers
  ✓ Detected page 35 before page 34 (misordered)
  ✓ Reordered pages: 1 swap performed
  ✓ No duplicates detected
```

**Ragged fixes:**
- Rotated pages (upside down or sideways)
- Pages out of order (page 3 scanned before page 2)
- Duplicate pages (same page scanned twice)

**Important:** This happens **automatically**. You don't need to do anything.

### Phase 3: Metadata Extraction (5-15 seconds)
```
[3/5] Extracting metadata...
  ✓ Analysed title page
  ✓ Found title: "Being and Time"
  ✓ Found author: "Martin Heidegger"
  ✓ Found year: 1927
  ✓ Found publisher: "Max Niemeyer Verlag"
  ✓ Confidence: 0.95 (high)
```

**Ragged extracts:**
- Book title (from title page)
- Author name
- Publication year
- Publisher name

**Privacy note:** This happens 100% offline. No internet connection used.

### Phase 4: Markdown Export (30-90 seconds)
```
[4/5] Exporting to markdown...
  ✓ Converted 245 pages
  ✓ Preserved formatting
  ✓ Created markdown: Being-and-Time-Martin-Heidegger-1927.md
```

**Ragged creates:**
- Clean markdown file
- Preserved structure (headings, paragraphs)
- Usable for note-taking, analysis, etc.

### Phase 5: Organization (1-2 seconds)
```
[5/5] Organizing...
  ✓ Generated semantic filename
  ✓ Backed up original: ~/.ragged/documents/originals/a3f7e9.../
  ✓ Saved corrected PDF: Being-and-Time-Martin-Heidegger-1927.pdf
  ✓ Saved markdown: Being-and-Time-Martin-Heidegger-1927.md
  ✓ Recorded lineage: processing_log.jsonl

╭─ Processing Complete ──────────────────────────────────╮
│                                                        │
│ ✓ Corrected PDF:                                       │
│   ~/.ragged/documents/corrected/                       │
│   Being-and-Time-Martin-Heidegger-1927.pdf            │
│                                                        │
│ ✓ Markdown:                                            │
│   ~/.ragged/documents/markdown/                        │
│   Being-and-Time-Martin-Heidegger-1927.md             │
│                                                        │
│ ✓ Original backup:                                     │
│   ~/.ragged/documents/originals/a3f7e9.../            │
│                                                        │
│ Processing time: 1m 45s                                │
│                                                        │
╰────────────────────────────────────────────────────────╯
```

**Ragged organised:**
- Semantic filename (Title-Author-Year.pdf)
- Original backed up safely
- Markdown exported
- Lineage tracked

---

## Step 4: Verify the Results

### Check the Corrected PDF

Open the corrected PDF:

```bash
open ~/.ragged/documents/corrected/Being-and-Time-Martin-Heidegger-1927.pdf
```

**Verify:**
- ✓ All pages are right-side up
- ✓ Pages are in correct order (1, 2, 3, ...)
- ✓ Text is searchable (Cmd+F / Ctrl+F works)
- ✓ No duplicate pages
- ✓ Quality looks good

### Check the Markdown

View the markdown:

```bash
cat ~/.ragged/documents/markdown/Being-and-Time-Martin-Heidegger-1927.md | head -50
```

**You should see:**
```markdown
# Being and Time

## Introduction

The question of Being has today been forgotten...

[... clean, formatted text ...]
```

**Use it for:**
- Note-taking apps (Obsidian, Notion)
- Text analysis
- Searching specific passages

### Check the Lineage

View processing history:

```bash
tail -1 ~/.ragged/metadata/processing_log.jsonl | python -m json.tool
```

**You'll see:**
```json
{
  "lineage_id": "20251123140000-a3f7e9d2",
  "timestamp": "2025-11-23T14:00:00Z",
  "original": {
    "path": "/Users/you/scans/philosophy-book.pdf",
    "backup": "/Users/you/.ragged/documents/originals/a3f7e9.../original.pdf",
    "size_bytes": 12456789,
    "hash": "a3f7e9d2..."
  },
  "processed": {
    "corrected_pdf": "/Users/you/.ragged/documents/corrected/Being-and-Time-Martin-Heidegger-1927.pdf",
    "markdown": "/Users/you/.ragged/documents/markdown/Being-and-Time-Martin-Heidegger-1927.md"
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

**This provides:**
- Complete processing history
- Original file location
- Metadata extracted
- Timestamps

---

## Step 5: Ingest into RAG (Optional)

Now you can use your perfectly processed book in ragged's RAG system:

```bash
ragged ingest pdf ~/.ragged/documents/corrected/Being-and-Time-Martin-Heidegger-1927.pdf
```

**Then query it:**

```bash
ragged query text "What is Dasein according to Heidegger?"
```

**Example response:**
```
╭─ Answer ───────────────────────────────────────────────╮
│                                                        │
│ Dasein, according to Heidegger, is the mode of Being  │
│ that is characteristic of human existence. It is the  │
│ being for whom Being is an issue...                   │
│                                                        │
╰────────────────────────────────────────────────────────╯

Sources:
• Being-and-Time-Martin-Heidegger-1927.pdf (page 42)
• Being-and-Time-Martin-Heidegger-1927.pdf (page 67)
```

---

## Common Issues and Solutions

### Issue 1: "OCR failed"

**Cause:** Image quality too poor for OCR.

**Solution:** Try different OCR engine:
```bash
ragged scan process ~/scans/book.pdf --ocr-engine paddleocr
```

PaddleOCR has higher accuracy (95-98%) vs EasyOCR (90-95%).

### Issue 2: Pages still misordered

**Cause:** Pages don't have detectable page numbers.

**What happened:**
- Ragged looks for page numbers in headers/footers
- If none found, it keeps original order
- Future versions (v0.8.x) will have manual verification

**Workaround:** Manually reorder before processing.

### Issue 3: Incorrect metadata

**Example:** Title extracted as "Chapter 1" instead of "Being and Time"

**Cause:** Title page format doesn't match ragged's regex patterns.

**Workaround:** Manually rename after processing:
```bash
mv ~/.ragged/documents/corrected/Chapter-1-2024.pdf \
   ~/.ragged/documents/corrected/Being-and-Time-Heidegger-1927.pdf
```

**Future:** v0.8.x will add manual metadata editing and optional web lookup.

### Issue 4: Processing is slow

**Solutions:**

1. **Use GPU acceleration** (if you have CUDA or Apple Silicon):
   ```bash
   ragged scan process book.pdf --gpu
   ```

2. **Use faster OCR**:
   ```bash
   ragged scan process book.pdf --ocr-engine easyocr
   ```

3. **Reduce DPI** (in `~/.ragged/config.yml`):
   ```yaml
   scan_pdf_dpi: 150  # Lower = faster (default: 300)
   ```

---

## Next Steps

**Congratulations!** You've successfully processed your first scanned book.

### Process Multiple Books

Process an entire folder:
```bash
ragged scan process ~/scans/ --batch
```

Each book will be processed independently.

### Customize Settings

Create `~/.ragged/config.yml`:
```yaml
# OCR settings
scan_ocr_engine: paddleocr  # Better accuracy
scan_ocr_language: eng      # English

# Output settings
scan_keep_originals: true   # Always backup
scan_export_markdown: true  # Always export
```

### Learn More

- **[Complete Guide](../guides/scanning-books.md)** - All features and options
- **[API Reference](../reference/scan-api.md)** - Technical details
- **[Configuration Reference](../reference/configuration.md)** - All settings

### Build Your Library

1. **Process all your scans**:
   ```bash
   ragged scan process ~/scans/ --batch
   ```

2. **Ingest into RAG**:
   ```bash
   ragged ingest pdf ~/.ragged/documents/corrected/*.pdf
   ```

3. **Query your entire library**:
   ```bash
   ragged query text "Compare Heidegger and Sartre on authenticity"
   ```

---

## Summary

**What you learned:**
- ✅ How to preview processing with `--dry-run`
- ✅ How ragged's 5-phase pipeline works
- ✅ How to verify results (PDF, markdown, lineage)
- ✅ How to integrate with RAG
- ✅ How to troubleshoot common issues

**Key takeaways:**
- **Automatic correction** - Page reordering happens automatically
- **100% offline** - No internet connection needed
- **Privacy-first** - All data stays on your device
- **Traceable** - Complete lineage tracking

**Next tutorial:** [Processing Folders of Books](./batch-processing.md)

---

## See Also

- [Scanning Books Guide](../guides/scanning-books.md)
- [Configuration Reference](../reference/configuration.md)
- [Troubleshooting Common Issues](../guides/troubleshooting-scans.md)
