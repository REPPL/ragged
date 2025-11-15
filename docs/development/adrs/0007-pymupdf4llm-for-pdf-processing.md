# ADR-0007: PyMuPDF4LLM for PDF Processing

**Status:** Accepted

**Date:** 2025-11-09

**Deciders:** Development Team

**Area:** Document Ingestion

## Context

PDFs are a primary document format that ragged must support. Need reliable extraction that preserves document structure (headings, lists, tables) for optimal RAG performance. Simple text extraction loses important semantic information that helps with both chunking and retrieval quality.

## Decision

Use PyMuPDF4LLM for PDF processing, which converts PDFs to Markdown format.

## Rationale

- **Structure Preservation**: Maintains headings, lists, tables in a semantic format
- **LLM-Optimised**: Output format specifically designed for LLM processing
- **Quality**: Superior to raw text extraction whilst maintaining simplicity
- **Simple API**: Single function call to convert PDF to Markdown
- **Active Development**: Part of pymupdf ecosystem which is well-maintained
- **Markdown Output**: Natural fit for downstream processing pipeline

## Alternatives Considered

### 1. PyPDF2

**Pros:**
- Lightweight dependency
- Pure Python (no C++ compilation)

**Cons:**
- Poor handling of complex PDFs
- No structure preservation
- Raw text output only

**Rejected:** Inadequate structure preservation for quality RAG

### 2. pdfplumber

**Pros:**
- Excellent table extraction capabilities
- Good for structured data extraction

**Cons:**
- More complex API
- Overkill for text extraction
- Heavier dependency

**Rejected:** Too complex for primary use case

### 3. Apache Tika

**Pros:**
- Handles many document formats
- Enterprise-grade

**Cons:**
- Java dependency (heavy)
- Overkill for PDF-only processing
- Complex setup

**Rejected:** Violates simplicity principle, heavyweight dependency

### 4. PyMuPDF (raw)

**Pros:**
- Direct access to PDF internals
- Very fast

**Cons:**
- PyMuPDF4LLM provides better wrapper for LLM use cases
- More manual work to extract structure

**Rejected:** PyMuPDF4LLM is superior wrapper for our needs

## Implementation

```python
import pymupdf4llm

def load_pdf(file_path: str) -> str:
    """Load PDF and convert to Markdown."""
    markdown_text = pymupdf4llm.to_markdown(file_path)
    return markdown_text
```

## Consequences

### Positive

- Excellent PDF extraction quality
- Markdown output is semantic and readable
- Headings and structure preserved for better chunking
- Works well with downstream chunking system
- Human-debuggable intermediate format

### Negative

- Larger dependency than PyPDF2
- C++ extension requires compilation on some platforms (installation complexity)
- Markdown conversion may not be perfect for all PDFs (especially complex layouts)
- Some formatting information lost (fonts, colours, exact positioning)

### Neutral

- Adds another dependency to manage
- Requires pymupdf base library

## Lessons Learned

Markdown output is significantly superior to plain text for RAG use cases. The preserved structure improves both retrieval accuracy and answer quality.

## Related

- [ADR-0014: Markdown as Intermediate Format](./0014-markdown-as-intermediate-format.md)
- [Architecture: Document Loaders](../architecture/document-loaders.md)
