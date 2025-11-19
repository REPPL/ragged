# Test Data

**Purpose:** Sample documents and fixtures for manual testing.

---

## Directory Structure

```
test_data/
├── README.md           # This file
├── documents/          # Sample documents for testing
│   ├── sample.pdf
│   ├── sample.md
│   ├── sample.html
│   ├── sample.txt
│   └── sample_folder/  # Folder with multiple documents
└── fixtures/           # Test fixtures and expected outputs
    ├── expected_query_results.json
    └── sample_metadata.json
```

---

## What Belongs Here

✅ **Sample documents** - Test files in various formats (PDF, MD, HTML, TXT)
✅ **Test fixtures** - Expected outputs, sample metadata, configuration files
✅ **Small test datasets** - Curated sets of documents for specific scenarios
✅ **Reference data** - Known-good outputs for validation

❌ **Large files** (>10MB) - Use `.gitignore` and provide download instructions
❌ **Copyrighted content** - Only use public domain or self-created content
❌ **Sensitive data** - No real PII, credentials, or proprietary information
❌ **Binary blobs** - Avoid unnecessary binary files

---

## Creating Test Documents

### Sample PDF

```python
from fpdf import FPDF

pdf = FPDF()
pdf.add_page()
pdf.set_font("Arial", size=12)
pdf.cell(200, 10, txt="Sample Document", ln=True)
pdf.cell(200, 10, txt="This is a test document for ragged.", ln=True)
pdf.output("sample.pdf")
```

### Sample Markdown

```markdown
# Sample Document

This is a **test document** for ragged.

## Sections

- Section 1
- Section 2
- Section 3

## Content

Lorem ipsum dolor sit amet, consectetur adipiscing elit.
```

### Sample HTML

```html
<!DOCTYPE html>
<html>
<head>
    <title>Sample Document</title>
</head>
<body>
    <h1>Sample Document</h1>
    <p>This is a test document for ragged.</p>
    <ul>
        <li>Item 1</li>
        <li>Item 2</li>
    </ul>
</body>
</html>
```

### Sample Text

```
Sample Document

This is a plain text test document for ragged.

It contains multiple paragraphs and basic formatting.

Key points:
- Point 1
- Point 2
- Point 3
```

---

## Using Test Data in Tests

### From conftest.py Fixtures

```python
def test_with_sample_documents(sample_documents):
    """Uses sample_documents fixture from conftest.py"""
    for doc in sample_documents:
        assert doc.exists()
```

### Loading Directly

```python
from pathlib import Path

def test_with_specific_file():
    test_data_dir = Path(__file__).parent.parent / "test_data"
    sample_pdf = test_data_dir / "documents" / "sample.pdf"

    assert sample_pdf.exists()
    # Use sample_pdf in test
```

### From Test Utilities

```python
from scripts.manual_tests.utils.helpers import load_test_data

def test_with_fixtures():
    expected = load_test_data("expected_query_results.json")
    # Compare actual results with expected
```

---

## Test Data Guidelines

### Document Characteristics

**Sample documents should:**
- Be small (< 1MB each)
- Represent common use cases
- Have known, predictable content
- Be properly formatted
- Include metadata

**Diverse formats:**
- PDF (single page and multi-page)
- Markdown (with headers, lists, code blocks)
- HTML (simple and complex structure)
- Plain text (various encodings)

### Content Guidelines

**Include documents with:**
- Simple content (for basic tests)
- Complex content (for edge cases)
- Special characters (Unicode, emoji)
- Various lengths (short, medium, long)
- Different structures (tables, lists, nested sections)

**Avoid:**
- Copyrighted content
- Real personal information
- Offensive or inappropriate content
- Extremely large files
- Malformed or corrupted files (unless testing error handling)

---

## Maintenance

### When to Add Test Data

- [ ] New document format supported
- [ ] New edge case discovered
- [ ] Regression test requires specific file
- [ ] Performance test needs benchmark data

### When to Remove Test Data

- [ ] File no longer used in any tests
- [ ] Replaced by better test data
- [ ] File too large (move to external storage)

### Keeping Test Data Current

1. Review test data quarterly
2. Update sample documents to reflect current formats
3. Add new test cases as features evolve
4. Remove obsolete test data
5. Document purpose of each test file

---

## Large Test Files

For files > 10MB, **do not commit to git**. Instead:

1. Add to `.gitignore`
2. Document in `large_files.md`:
   ```markdown
   ## Large Test Files

   ### test_large.pdf (50MB)
   - **Purpose:** Performance testing
   - **Download:** [URL]
   - **SHA-256:** [checksum]
   ```

3. Provide download script:
   ```bash
   ./scripts/download_test_data.sh
   ```

---

## Sample Dataset Collections

### Basic Collection

For quick smoke tests:
- `sample.pdf` (1 page, ~100 words)
- `sample.md` (simple markdown, ~200 words)
- `sample.txt` (plain text, ~150 words)

### Comprehensive Collection

For full integration tests:
- 5 PDFs (varying pages: 1, 3, 5, 10, 20)
- 5 Markdown files (varying complexity)
- 5 HTML files (simple to complex)
- 5 Text files (varying encodings)

### Edge Case Collection

For error handling and edge cases:
- Empty file
- Very small file (< 10 bytes)
- File with only special characters
- File with mixed encodings
- Corrupted file (for error testing)

---

## Git LFS Consideration

If test files grow large (>100MB total), consider Git LFS:

```bash
# Track PDF files with LFS
git lfs track "*.pdf"

# Commit .gitattributes
git add .gitattributes
git commit -m "Configure Git LFS for PDFs"
```

**Note:** Currently not implemented. Discuss with team if needed.

---

## Related Documentation

- [Test Utilities](../utils/README.md) - Using test data in tests
- [conftest.py](../conftest.py) - Test data fixtures
- [Sample Documents Generation](../utils/helpers.py) - Programmatic generation

---

**Maintained By:** ragged development team
