# Phase 2 Completion Guide: Document Loaders

## What's Already Done ✅

- [x] Document models (Pydantic) - 16 tests, 97% coverage
- [x] Security utilities (path validation, file size checks, MIME detection)
- [x] Test fixtures and infrastructure

## What's Needed

Implement 4 document loaders + parsers + tests.

---

## Step 1: Create `src/ingestion/loaders.py`

```python
"""
Document loaders for various file formats.

This module provides loaders for PDF, TXT, Markdown, and HTML files
with security validation and error handling.
"""

from pathlib import Path
from typing import Optional, Tuple

from src.ingestion.models import Document
from src.utils.logging import get_logger
from src.utils.security import validate_file_path, validate_file_size, validate_mime_type

logger = get_logger(__name__)


def load_document(
    file_path: Path,
    format: Optional[str] = None,
) -> Document:
    """
    Load a document from file, auto-detecting format if not specified.

    Args:
        file_path: Path to document file
        format: Optional format override ('pdf', 'txt', 'md', 'html')

    Returns:
        Document instance

    Raises:
        ValueError: If format not supported
        SecurityError: If file fails security checks
        FileNotFoundError: If file doesn't exist

    TODO: Implement:
          1. Validate file path and size
          2. Detect format if not specified (from extension + MIME)
          3. Call appropriate loader
          4. Return Document
    """
    # Validate security
    file_path = validate_file_path(file_path)
    validate_file_size(file_path)

    # Detect format
    if format is None:
        format = _detect_format(file_path)

    # Load based on format
    loaders = {
        "pdf": load_pdf,
        "txt": load_txt,
        "md": load_markdown,
        "html": load_html,
    }

    loader = loaders.get(format.lower())
    if loader is None:
        raise ValueError(f"Unsupported format: {format}")

    return loader(file_path)


def _detect_format(file_path: Path) -> str:
    """
    Detect document format from extension and MIME type.

    TODO: Check extension, validate with MIME type
    """
    raise NotImplementedError()


def load_pdf(file_path: Path) -> Document:
    """
    Load PDF using PyMuPDF4LLM.

    TODO: Install: pip install pymupdf pymupdf4llm
          Import: import pymupdf4llm
          Use: pymupdf4llm.to_markdown(file_path)
          Extract metadata: title, author, page_count
    """
    raise NotImplementedError()


def load_txt(file_path: Path) -> Document:
    """
    Load plain text file.

    TODO: 1. Try UTF-8
          2. If fails, detect encoding with chardet
          3. Read content
          4. Create Document
    """
    raise NotImplementedError()


def load_markdown(file_path: Path) -> Document:
    """
    Load Markdown file.

    TODO: 1. Read as UTF-8
          2. Optional: Parse frontmatter for metadata
          3. Create Document
    """
    raise NotImplementedError()


def load_html(file_path: Path) -> Document:
    """
    Load HTML using Trafilatura.

    TODO: Install: pip install trafilatura
          Import: import trafilatura
          Use: trafilatura.extract(html, include_links=False)
          Extract: title from metadata
    """
    raise NotImplementedError()
```

---

## Step 2: Create Tests

Create `tests/ingestion/test_loaders.py`:

```python
"""Tests for document loaders."""

import pytest
from pathlib import Path

from src.ingestion.loaders import (
    load_document,
    load_pdf,
    load_txt,
    load_markdown,
    load_html,
)


class TestLoadTxt:
    """Test TXT loader."""

    @pytest.mark.skip(reason="TODO")
    def test_loads_utf8(self, sample_txt_path):
        """Test loading UTF-8 text file."""
        doc = load_txt(sample_txt_path)
        assert doc.content
        assert doc.metadata.format == "txt"

    @pytest.mark.skip(reason="TODO")
    def test_handles_different_encodings(self, temp_dir):
        """Test loading files with different encodings."""
        # Create file with latin-1 encoding
        # Load and verify
        pass


class TestLoadMarkdown:
    """Test Markdown loader."""

    @pytest.mark.skip(reason="TODO")
    def test_loads_markdown(self, sample_md_path):
        """Test loading Markdown file."""
        doc = load_markdown(sample_md_path)
        assert doc.content
        assert doc.metadata.format == "md"


class TestLoadPdf:
    """Test PDF loader (requires test PDF)."""

    @pytest.mark.skip(reason="TODO")
    def test_loads_pdf(self):
        """Test loading PDF file."""
        # You'll need to create or download a test PDF
        pass


class TestLoadHtml:
    """Test HTML loader."""

    @pytest.mark.skip(reason="TODO")
    def test_loads_html(self, temp_dir):
        """Test loading HTML file."""
        # Create test HTML
        html_file = temp_dir / "test.html"
        html_file.write_text(
            "<html><body><h1>Title</h1><p>Content</p></body></html>"
        )
        doc = load_html(html_file)
        assert "Content" in doc.content


class TestLoadDocument:
    """Test auto-detection loader."""

    @pytest.mark.skip(reason="TODO")
    def test_auto_detects_format(self, sample_txt_path):
        """Test format auto-detection."""
        doc = load_document(sample_txt_path)  # No format specified
        assert doc.metadata.format == "txt"

    @pytest.mark.skip(reason="TODO")
    def test_uses_specified_format(self, sample_txt_path):
        """Test using explicit format."""
        doc = load_document(sample_txt_path, format="txt")
        assert doc.metadata.format == "txt"
```

---

## Step 3: Install Dependencies

```bash
pip install pymupdf pymupdf4llm trafilatura chardet
```

---

## Step 4: Implementation Tips

### For TXT Loader:
```python
def load_txt(file_path: Path) -> Document:
    try:
        content = file_path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        import chardet
        raw = file_path.read_bytes()
        detected = chardet.detect(raw)
        encoding = detected['encoding']
        content = raw.decode(encoding)

    return Document.from_file(
        file_path=file_path,
        content=content,
        format="txt",
    )
```

### For PDF Loader:
```python
def load_pdf(file_path: Path) -> Document:
    import pymupdf4llm

    # Extract text and structure
    md_text = pymupdf4llm.to_markdown(str(file_path))

    # Get metadata
    import pymupdf
    doc = pymupdf.open(file_path)
    metadata = doc.metadata

    return Document.from_file(
        file_path=file_path,
        content=md_text,
        format="pdf",
        title=metadata.get("title"),
        author=metadata.get("author"),
        page_count=len(doc),
    )
```

### For HTML Loader:
```python
def load_html(file_path: Path) -> Document:
    import trafilatura

    html = file_path.read_text(encoding="utf-8")
    text = trafilatura.extract(
        html,
        include_links=False,
        include_images=False,
    )

    # Try to get title
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(html, 'html.parser')
    title = soup.title.string if soup.title else None

    return Document.from_file(
        file_path=file_path,
        content=text or "",
        format="html",
        title=title,
    )
```

---

## Step 5: Testing

Run tests as you implement:

```bash
# Run specific test file
pytest tests/ingestion/test_loaders.py -v

# Run with coverage
pytest tests/ingestion/test_loaders.py --cov=src.ingestion.loaders

# Run all ingestion tests
pytest tests/ingestion/ -v
```

---

## Step 6: Create Test Files

You'll need sample files for testing. Create them in `tests/data/`:

```bash
mkdir -p tests/data

# Sample TXT
echo "This is a test document." > tests/data/sample.txt

# Sample MD
echo -e "# Test\n\nThis is markdown." > tests/data/sample.md

# Sample HTML
cat > tests/data/sample.html << EOF
<html>
<head><title>Test Page</title></head>
<body>
<h1>Test Header</h1>
<p>This is test content.</p>
</body>
</html>
EOF

# For PDF: Download a sample or create one
```

Update test fixtures in `conftest.py`:
```python
@pytest.fixture
def sample_data_dir() -> Path:
    return Path(__file__).parent / "data"

@pytest.fixture
def sample_txt(sample_data_dir) -> Path:
    return sample_data_dir / "sample.txt"
```

---

## Completion Criteria

Phase 2 is complete when:

- [ ] All 4 loaders implemented (PDF, TXT, MD, HTML)
- [ ] 20+ tests written and passing
- [ ] 85%+ coverage on loaders module
- [ ] Security validation integrated
- [ ] Error handling comprehensive
- [ ] All test files created

---

## Next Phase

After Phase 2 is complete, move to **Phase 3: Chunking System**

See the skeleton files already created:
- `src/chunking/token_counter.py`
- `src/chunking/splitters.py`
- Test skeletons in `tests/chunking/`

---

## Estimated Time

- Step 1 (Skeleton): 1 hour
- Step 2 (TXT + MD loaders): 1 hour
- Step 3 (HTML loader): 1 hour
- Step 4 (PDF loader): 2 hours
- Step 5 (Tests): 2 hours
- Step 6 (Edge cases + polish): 1 hour

**Total: ~8 hours**
