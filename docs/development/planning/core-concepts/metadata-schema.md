# Metadata Schema Specification

**Purpose**: Define comprehensive metadata structure for all document types
**Implementation**: v0.2+

---

## Overview

ragged maintains extensive metadata for every ingested document to enable:
- **Accurate citations** with page numbers, authors, dates
- **Advanced filtering** by document type, date range, source
- **Duplicate detection** via content hashing
- **Provenance tracking** for academic integrity
- **Quality metrics** for OCR and processing

## Base Metadata (All Documents)

```json
{
  "document_id": "string",           // SHA256 hash (first 12 chars)
  "original_filename": "string",      // User-provided filename
  "original_path": "string",          // Full path to original file
  "original_paths": ["string"],       // All paths if duplicates exist

  "file_type": "string",              // MIME type (application/pdf, text/html)
  "file_size_bytes": "integer",       // Original file size
  "file_extension": "string",         // .pdf, .html, .md, etc.

  "upload_date": "ISO8601",           // When first uploaded
  "upload_by": "string",              // User ID (if multi-user mode)
  "processing_date": "ISO8601",       // When normalisation completed

  "content_hash": "string",           // SHA256 of original file
  "normalized_hash": "string",        // SHA256 of normalised markdown
  "minhash_signature": "array",       // MinHash for near-duplicate detection

  "duplicate_of": "string|null",      // Document ID if this is a duplicate
  "duplicates": ["string"],           // Other IDs that are duplicates of this
  "similarity_score": "float|null",   // 0.0-1.0 if duplicate detected

  "document_type": "enum",            // academic_paper|web_article|book|magazine|...
  "language": "string",               // ISO 639-1 (en, es, fr, etc.)
  "collection": "string",             // User-assigned collection/folder
  "tags": ["string"],                 // User-assigned tags

  "markdown_path": "string",          // Path to normalised .md file
  "images_paths": ["string"],         // Extracted images

  "processing_metadata": {
    "processor": "string",            // docling-v1.0, trafilatura-v2.0
    "ocr_performed": "boolean",
    "processing_time_seconds": "float",
    "warnings": ["string"],
    "errors": ["string"]
  }
}
```

## Academic Paper Metadata

Used when `document_type == "academic_paper"`.

Extracted by **GROBID** for PDFs, **Trafilatura** for web-hosted papers.

```json
{
  "academic_metadata": {
    // Core bibliographic
    "title": "string",
    "subtitle": "string|null",
    "authors": [
      {
        "first_name": "string",
        "middle_name": "string|null",
        "last_name": "string",
        "full_name": "string",          // Formatted as "Last, First M."
        "email": "string|null",
        "orcid": "string|null",          // 0000-0002-1234-5678
        "affiliation": {
          "institution": "string",
          "department": "string|null",
          "country": "string|null"
        }
      }
    ],

    // Publication venue
    "publication_type": "enum",         // journal|conference|preprint|thesis|book|report
    "venue": "string",                  // Journal name or conference
    "volume": "string|null",
    "issue": "string|null",
    "pages": {
      "start": "integer|null",
      "end": "integer|null",
      "total": "integer"                // Total pages in PDF
    },
    "publisher": "string|null",

    // Dates
    "publication_date": "ISO8601|null", // YYYY-MM-DD
    "submission_date": "ISO8601|null",
    "acceptance_date": "ISO8601|null",
    "year": "integer",                  // Extracted year

    // Identifiers
    "doi": "string|null",               // 10.1038/s41586-023-12345-6
    "pmid": "string|null",              // PubMed ID
    "pmcid": "string|null",             // PubMed Central ID
    "arxiv_id": "string|null",          // 2301.12345
    "isbn": "string|null",              // For books
    "issn": "string|null",              // For journals
    "url": "string|null",               // Canonical URL

    // Content
    "abstract": "string|null",
    "keywords": ["string"],
    "subjects": ["string"],             // ACM/MSC classification

    // Structure
    "sections": ["string"],             // ["Introduction", "Methods", ...]
    "figures_count": "integer",
    "tables_count": "integer",
    "equations_count": "integer",
    "references_count": "integer",

    // Extracted references (optional, v0.3+)
    "references": [
      {
        "index": "integer",
        "title": "string",
        "authors": "string",            // Formatted author string
        "venue": "string",
        "year": "integer",
        "doi": "string|null"
      }
    ],

    // Research metadata
    "research_area": "string|null",     // CS, Biology, Physics, etc.
    "methodology": ["string"],          // experiment, survey, theoretical, etc.

    // Acknowledgements (v0.3+)
    "funding": ["string"],              // Grant numbers, agencies
    "acknowledgements": "string|null"
  }
}
```

## Web Article Metadata

Used when `document_type == "web_article"`.

Extracted by **Trafilatura** from saved HTML files.

```json
{
  "web_metadata": {
    // Core article info
    "title": "string",
    "description": "string|null",       // Meta description or excerpt
    "author": "string|null",            // Single author string
    "authors": ["string"],              // Multiple authors if detected

    // Publication details
    "site_name": "string",              // "Medium", "The New York Times"
    "url": "string",                    // Original URL
    "canonical_url": "string|null",     // Canonical if different
    "publication_date": "ISO8601|null", // When published
    "modified_date": "ISO8601|null",    // Last modified

    // Classification
    "categories": ["string"],           // Site-provided categories
    "tags": ["string"],                 // Site-provided tags
    "section": "string|null",           // "Technology", "Opinion", etc.

    // Images
    "featured_image": {
      "url": "string|null",
      "caption": "string|null",
      "alt_text": "string|null"
    },
    "images": [
      {
        "url": "string",
        "caption": "string|null",
        "extracted_path": "string"      // Local path if downloaded
      }
    ],

    // Social/engagement (if available in HTML)
    "comments_count": "integer|null",
    "shares_count": "integer|null",
    "reading_time_minutes": "integer|null",

    // Technical
    "language_detected": "string",      // ISO 639-1
    "paywall": "boolean",               // Detected paywall indicator
    "license": "string|null",           // CC-BY, Copyright, etc.

    // Content structure
    "word_count": "integer",
    "has_code_blocks": "boolean",
    "has_math": "boolean",
    "has_tables": "boolean"
  }
}
```

## Book Metadata

Used when `document_type == "book"`.

```json
{
  "book_metadata": {
    "title": "string",
    "subtitle": "string|null",
    "authors": ["string"],
    "editors": ["string"],
    "publisher": "string|null",
    "publication_year": "integer",
    "edition": "string|null",           // "2nd Edition", "Revised"

    "isbn_10": "string|null",
    "isbn_13": "string|null",
    "doi": "string|null",

    "series": "string|null",            // Book series name
    "series_number": "integer|null",

    "pages_total": "integer",
    "chapters": [
      {
        "number": "integer",
        "title": "string",
        "start_page": "integer",
        "end_page": "integer"
      }
    ],

    "subjects": ["string"],
    "language": "string"
  }
}
```

## Magazine/Periodical Metadata

Used when `document_type == "magazine"`.

Particularly relevant for scanned magazines (OCR processed).

```json
{
  "magazine_metadata": {
    "publication_name": "string",       // "Scientific American", "The Economist"
    "issue_date": "ISO8601",            // Cover date
    "volume": "string|null",
    "issue_number": "string|null",

    "articles": [
      {
        "title": "string",
        "author": "string|null",
        "start_page": "integer",
        "end_page": "integer",
        "section": "string|null"        // "Features", "News", etc.
      }
    ],

    "cover_image": "string|null",       // Path to extracted cover
    "issn": "string|null"
  }
}
```

## OCR Metadata

Used when `processing_metadata.ocr_performed == true`.

```json
{
  "ocr_metadata": {
    "ocr_engine": "string",             // "paddleocr-v2.7", "surya-v1.0"
    "ocr_language": "string",           // Language used for OCR

    "confidence": {
      "mean": "float",                  // 0.0-1.0, average confidence
      "median": "float",
      "min": "float",
      "max": "float"
    },

    "layout_analysis": {
      "multi_column": "boolean",
      "columns_detected": "integer",
      "regions": [
        {
          "type": "enum",               // text|title|list|table|figure|caption
          "bbox": {
            "x": "integer",
            "y": "integer",
            "width": "integer",
            "height": "integer"
          },
          "page": "integer",
          "confidence": "float"
        }
      ]
    },

    "quality_flags": {
      "low_confidence_regions": "integer",   // Count of regions < 0.7 confidence
      "unrecognized_characters": "integer",
      "requires_manual_review": "boolean"
    }
  }
}
```

## Chunk-Level Metadata

When documents are chunked, each chunk inherits relevant metadata.

Stored in **ChromaDB/Qdrant** metadata field.

```json
{
  "chunk_id": "string",                 // document_id + chunk number
  "document_id": "string",              // Parent document
  "chunk_index": "integer",             // 0-based index in document

  "text": "string",                      // Actual chunk text
  "markdown": "string",                 // Chunk as markdown (with formatting)

  "position": {
    "start_char": "integer",            // Character offset in full markdown
    "end_char": "integer",
    "start_page": "integer|null",       // Original page number (if available)
    "end_page": "integer|null"
  },

  "structure": {
    "heading": "string|null",           // Parent heading
    "heading_level": "integer|null",    // 1-6 for # to ######
    "section": "string|null",           // Top-level section name
    "is_table": "boolean",
    "is_code": "boolean",
    "is_list": "boolean"
  },

  // Inherited from parent document
  "document_title": "string",
  "document_authors": ["string"],
  "document_date": "ISO8601|null",
  "document_url": "string|null",
  "document_doi": "string|null",

  // Retrieval metadata
  "embedding_model": "string",          // Model used for this chunk
  "embedding_date": "ISO8601",
  "chunk_strategy": "string"            // recursive|semantic|late
}
```

## Collection Metadata

Collections group related documents.

Stored in separate **SQLite table** `collections`.

```json
{
  "collection_id": "string",            // UUID
  "collection_name": "string",          // "Deep Learning Papers 2024"
  "description": "string|null",
  "created_date": "ISO8601",
  "created_by": "string",               // User ID

  "document_count": "integer",          // Number of documents
  "document_ids": ["string"],           // List of member documents

  "settings": {
    "embedding_model": "string|null",   // Override default
    "chunk_size": "integer|null",
    "chunk_overlap": "integer|null"
  },

  "tags": ["string"],
  "is_public": "boolean",               // If multi-user
  "shared_with": ["string"]             // User IDs
}
```

## Storage Implementation

### SQLite Schema (Metadata Database)

```sql
-- Main documents table
CREATE TABLE documents (
    document_id TEXT PRIMARY KEY,
    original_filename TEXT NOT NULL,
    file_type TEXT NOT NULL,
    upload_date TEXT NOT NULL,  -- ISO8601
    processing_date TEXT,

    content_hash TEXT UNIQUE NOT NULL,
    normalized_hash TEXT,

    document_type TEXT,
    language TEXT,
    collection TEXT,

    metadata_json TEXT NOT NULL,  -- Full JSON metadata

    -- Duplicates
    duplicate_of TEXT,
    FOREIGN KEY (duplicate_of) REFERENCES documents(document_id)
);

-- File paths (multiple paths can map to same document)
CREATE TABLE file_paths (
    path_id INTEGER PRIMARY KEY AUTOINCREMENT,
    document_id TEXT NOT NULL,
    file_path TEXT UNIQUE NOT NULL,
    added_date TEXT NOT NULL,
    FOREIGN KEY (document_id) REFERENCES documents(document_id)
);

-- Collections
CREATE TABLE collections (
    collection_id TEXT PRIMARY KEY,
    collection_name TEXT NOT NULL,
    created_date TEXT NOT NULL,
    metadata_json TEXT NOT NULL
);

-- Document-Collection membership
CREATE TABLE collection_members (
    collection_id TEXT NOT NULL,
    document_id TEXT NOT NULL,
    added_date TEXT NOT NULL,
    PRIMARY KEY (collection_id, document_id),
    FOREIGN KEY (collection_id) REFERENCES collections(collection_id),
    FOREIGN KEY (document_id) REFERENCES documents(document_id)
);

-- MinHash signatures for duplicate detection
CREATE TABLE minhash_signatures (
    document_id TEXT PRIMARY KEY,
    signature BLOB NOT NULL,  -- Serialized MinHash array
    FOREIGN KEY (document_id) REFERENCES documents(document_id)
);

-- Indexes
CREATE INDEX idx_content_hash ON documents(content_hash);
CREATE INDEX idx_document_type ON documents(document_type);
CREATE INDEX idx_collection ON documents(collection);
CREATE INDEX idx_upload_date ON documents(upload_date);
CREATE INDEX idx_duplicate_of ON documents(duplicate_of);
```

### ChromaDB Metadata (Per Chunk)

ChromaDB stores metadata alongside embeddings:

```python
collection.add(
    ids=["doc123_chunk_0", "doc123_chunk_1"],
    documents=["First chunk text...", "Second chunk text..."],
    metadatas=[
        {
            "document_id": "doc123",
            "chunk_index": 0,
            "document_title": "Deep Learning Paper",
            "document_authors": "Smith, J.; Doe, A.",
            "document_date": "2024-01-15",
            "document_doi": "10.1038/...",
            "start_page": 1,
            "end_page": 2,
            "heading": "Introduction",
            "section": "Introduction"
        },
        {...}
    ],
    embeddings=[[0.1, 0.2, ...], [0.3, 0.4, ...]]
)
```

## Querying Metadata

### Filter by Document Type

```python
# Get all academic papers
papers = db.query(
    "SELECT * FROM documents WHERE document_type = 'academic_paper'"
)

# Get papers from specific journal
papers = db.query("""
    SELECT * FROM documents
    WHERE document_type = 'academic_paper'
    AND JSON_EXTRACT(metadata_json, '$.academic_metadata.venue') = 'Nature'
""")
```

### Filter by Date Range

```python
# Papers published in 2024
papers = db.query("""
    SELECT * FROM documents
    WHERE document_type = 'academic_paper'
    AND JSON_EXTRACT(metadata_json, '$.academic_metadata.year') = 2024
""")
```

### Filter by Author

```python
# Papers by specific author
papers = db.query("""
    SELECT * FROM documents
    WHERE metadata_json LIKE '%"last_name": "Smith"%'
""")
```

### Complex Queries

```python
# Deep learning papers from top conferences in last 2 years
papers = db.query("""
    SELECT * FROM documents
    WHERE document_type = 'academic_paper'
    AND JSON_EXTRACT(metadata_json, '$.academic_metadata.year') >= 2023
    AND (
        JSON_EXTRACT(metadata_json, '$.academic_metadata.venue') IN ('NeurIPS', 'ICML', 'ICLR')
    )
    AND (
        metadata_json LIKE '%deep learning%'
        OR metadata_json LIKE '%neural network%'
    )
""")
```

## Metadata in Citations

When returning answers, ragged uses metadata to generate proper citations:

### Academic Paper Citation (APA Style)

```python
def format_academic_citation(metadata: dict) -> str:
    """Generate APA-style citation."""
    authors = metadata["academic_metadata"]["authors"]
    author_str = format_authors(authors)  # "Smith, J., & Doe, A."

    year = metadata["academic_metadata"]["year"]
    title = metadata["academic_metadata"]["title"]
    venue = metadata["academic_metadata"]["venue"]
    doi = metadata["academic_metadata"]["doi"]

    citation = f"{author_str} ({year}). {title}. {venue}."
    if doi:
        citation += f" https://doi.org/{doi}"

    return citation

# Output: "Smith, J., & Doe, A. (2024). Deep Learning for Computer Vision. Nature. https://doi.org/10.1038/..."
```

### Web Article Citation

```python
def format_web_citation(metadata: dict) -> str:
    """Generate web article citation."""
    author = metadata["web_metadata"].get("author", "Unknown")
    date = metadata["web_metadata"]["publication_date"]
    title = metadata["web_metadata"]["title"]
    site = metadata["web_metadata"]["site_name"]
    url = metadata["web_metadata"]["url"]

    return f"{author}. ({date}). {title}. {site}. {url}"

# Output: "John Smith. (2024-11-09). AI Breakthrough. Medium. https://medium.com/..."
```

## Version Roadmap

### v0.1
- **Basic metadata only**: filename, file_type, upload_date
- No duplicate detection
- No specialised metadata (academic, web, etc.)

### v0.2
- **Full metadata extraction**: GROBID + Trafilatura
- **Academic paper metadata**: All bibliographic fields
- **Web article metadata**: Author, date, URL, tags
- **Duplicate detection**: SHA256 + MinHash
- **SQLite metadata database**

### v0.3
- **Enhanced metadata**: References extraction, funding info
- **OCR metadata**: Confidence scores, layout analysis
- **Collection management**: User-created collections
- **Advanced querying**: Date ranges, author search, etc.

### v1.0
- **Metadata UI**: Visual metadata editor, bulk editing
- **Metadata export**: BibTeX, RIS, CSV
- **Citation management**: Generate bibliographies
- **Metadata validation**: Enforce completeness, accuracy

## Testing Strategy

### Metadata Extraction Tests

```python
def test_grobid_extracts_paper_metadata():
    """Test GROBID extracts academic metadata correctly."""
    pdf_path = "test_data/sample_paper.pdf"
    metadata = extract_metadata(pdf_path, doc_type="academic_paper")

    assert metadata["academic_metadata"]["title"] is not None
    assert len(metadata["academic_metadata"]["authors"]) > 0
    assert metadata["academic_metadata"]["doi"] is not None
    assert metadata["academic_metadata"]["year"] >= 1900

def test_trafilatura_extracts_web_metadata():
    """Test Trafilatura extracts web article metadata."""
    html_path = "test_data/medium_article.html"
    metadata = extract_metadata(html_path, doc_type="web_article")

    assert metadata["web_metadata"]["title"] is not None
    assert metadata["web_metadata"]["site_name"] == "Medium"
    assert metadata["web_metadata"]["url"] is not None
```

### Citation Tests

```python
def test_academic_citation_format():
    """Test APA citation generation."""
    metadata = load_test_metadata("paper_metadata.json")
    citation = format_academic_citation(metadata)

    assert "Smith, J." in citation
    assert "(2024)" in citation
    assert "https://doi.org/" in citation
```

## References

- **Dublin Core Metadata**: https://www.dublincore.org/specifications/dublin-core/
- **Schema.org**: https://schema.org/ScholarlyArticle
- **JATS**: https://jats.nlm.nih.gov/
- **TEI**: https://tei-c.org/
- **GROBID TEI Output**: https://grobid.readthedocs.io/en/latest/TEI-encoding-of-results/
- **Trafilatura Metadata**: https://trafilatura.readthedocs.io/en/latest/corefunctions.html#metadata-extraction

---

**Next Steps**: See [duplicate-detection.md](./duplicate-detection.md) for content-based deduplication strategy.
