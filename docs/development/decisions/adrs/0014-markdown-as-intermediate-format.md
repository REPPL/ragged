# ADR-0014: Markdown as Intermediate Format

**Status:** Accepted

**Date:** 2025-11-09

**Deciders:** Development Team

**Area:** Document Processing

## Context

After loading documents from various formats (PDF, TXT, HTML, Markdown), need a common intermediate representation for:
- Consistent chunking
- Better retrieval (structure awareness)
- Improved answer generation (LLMs understand structure)
- Human debuggability

## Decision

Use Markdown as the intermediate format for all documents:
- **PDFs**: PyMuPDF4LLM converts PDF → Markdown
- **TXT files**: Remain as plain text (Markdown-compatible)
- **Markdown files**: Unchanged (already Markdown)
- **HTML files**: Converted to Markdown via Trafilatura

All downstream processing (chunking, embedding, retrieval) operates on Markdown.

## Rationale

- **Structure Preservation**: Markdown preserves headings, lists, tables, emphasis
- **LLM-Friendly**: Markdown is common in LLM training data, models understand it well
- **Human-Readable**: Easy to debug and inspect intermediate format
- **Consistent**: Single format for all downstream processing
- **Semantic**: More semantic than plain text, less noisy than HTML
- **Tooling**: Rich ecosystem of markdown tools and libraries
- **Future-Proof**: Can enhance with metadata, front matter, etc.

## Alternatives Considered

### 1. Plain Text

**Pros:**
- Simplest format
- Universal compatibility
- Smallest representation

**Cons:**
- Loses all structure (headings, lists, tables)
- No semantic information
- Harder for LLMs to understand context
- Poor chunking boundaries

**Rejected:** Structure loss degrades quality too much

### 2. HTML

**Pros:**
- Rich structure
- Preserves formatting
- Standard web format

**Cons:**
- Noisy tags clutter text
- Harder for LLMs to process
- Inconsistent HTML from different sources
- Larger representation

**Rejected:** Tag noise degrades LLM performance

### 3. JSON/Structured Format

**Pros:**
- Machine-readable
- Fully structured
- Precise metadata

**Cons:**
- Not human-readable
- LLMs trained on text, not JSON
- Complex schema management
- Overkill for text documents

**Rejected:** Optimises for machines over LLMs

### 4. Custom RAG Format

**Pros:**
- Optimised exactly for RAG use case
- Complete control

**Cons:**
- More implementation work
- Less compatible with tools
- Reinventing the wheel
- No ecosystem

**Rejected:** Markdown already solves this problem

## Implementation

### Document Loaders

```python
# PDF → Markdown
import pymupdf4llm

def load_pdf(path: str) -> str:
    return pymupdf4llm.to_markdown(path)

# HTML → Markdown
import trafilatura

def load_html(path: str) -> str:
    with open(path) as f:
        html = f.read()
    return trafilatura.extract(html, output_format='markdown')

# TXT → Markdown (identity)
def load_txt(path: str) -> str:
    with open(path) as f:
        return f.read()

# Markdown → Markdown (identity)
def load_markdown(path: str) -> str:
    with open(path) as f:
        return f.read()
```

### Downstream Processing

All chunking, embedding, and retrieval code operates on Markdown strings:

```python
def chunk_document(markdown_text: str) -> list[str]:
    """Chunk markdown text."""
    # RecursiveCharacterTextSplitter works on markdown
    return splitter.split_text(markdown_text)
```

## Consequences

### Positive

- Better retrieval (semantic structure helps matching)
- Better generation (LLMs understand markdown structure)
- Human-debuggable intermediate format
- Consistent processing pipeline
- Natural format for documentation and technical content
- Can add front matter for metadata

### Negative

- Conversion quality depends on source format
- Some information loss from PDF (fonts, colours, exact layout)
- Markdown parsing complexity for advanced features
- Tables may not convert perfectly from all sources

### Neutral

- Trade-off between structure preservation and simplicity
- Good enough for v0.1, can enhance in future versions

## Conversion Quality

**High Quality:**
- Markdown files (identity)
- Clean PDFs (PyMuPDF4LLM excellent)
- Simple HTML (Trafilatura good)

**Medium Quality:**
- Complex PDFs (multi-column, unusual layouts)
- Rich HTML (some styling lost)

**Limitations:**
- Scanned PDFs (OCR required first)
- Complex tables (may need manual cleanup)

## Future Enhancements

v0.2+:
- Enhanced table handling
- Front matter for document metadata
- Mermaid diagrams preservation

v0.3+:
- LaTeX math preservation
- Code block language detection and handling
- Custom markdown extensions for RAG

## Lessons Learned

Markdown is an excellent LLM-friendly intermediate representation. The structure preservation significantly improves both retrieval accuracy and answer quality compared to plain text.

## Related

- [ADR-0007: PyMuPDF4LLM for PDF Processing](./0007-pymupdf4llm-for-pdf-processing.md)
- [ADR-0009: Recursive Character Text Splitter](./0009-recursive-character-text-splitter.md)
- [Architecture: Document Loaders](../architecture/document-loaders.md)
