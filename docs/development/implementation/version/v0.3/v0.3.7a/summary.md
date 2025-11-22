# v0.3.7a - Document Version Tracking Implementation Summary

**Status:** ✅ Completed
**Release Date:** 2025-11-22
**Breaking Changes:** 0 (100% backward compatible)

---

## Overview

v0.3.7a introduces document version tracking to ragged, enabling detection of document changes, version history queries, and laying the foundation for partial re-indexing optimisations.

**Key Achievement:** SQLite-based version tracking with hierarchical hashing, comprehensive CLI, and 96% test coverage.

---

## Features Delivered

### 1. SQLite Version Store ✅

**What:** Persistent version tracking database using SQLite.

**Implementation:** `src/storage/version_tracker.py` (540 lines)

**Capabilities:**
- Three-table schema (documents, versions, chunk_versions)
- ACID transactions for data integrity
- Indexed queries for performance
- Automatic version numbering (1, 2, 3, ...)
- Chunk-to-version linking

**Database Schema:**
```sql
-- Document identity (stable across versions)
CREATE TABLE documents (
    doc_id TEXT PRIMARY KEY,
    file_path TEXT NOT NULL,
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL
);

-- Version records
CREATE TABLE versions (
    version_id TEXT PRIMARY KEY,
    doc_id TEXT NOT NULL,
    content_hash TEXT NOT NULL,
    page_hashes TEXT NOT NULL,
    version_number INTEGER NOT NULL,
    created_at TIMESTAMP NOT NULL,
    file_path TEXT NOT NULL,
    metadata TEXT,
    UNIQUE(doc_id, version_number)
);

-- Chunk-to-version mapping
CREATE TABLE chunk_versions (
    chunk_id TEXT NOT NULL,
    version_id TEXT NOT NULL,
    page_number INTEGER,
    chunk_sequence INTEGER,
    PRIMARY KEY (chunk_id, version_id)
);
```

**Location:** `~/.ragged/versions.db` by default

---

### 2. Hierarchical Content Hashing ✅

**What:** Two-level SHA-256 hashing for change detection.

**Algorithm:**
1. **Page-Level:** Hash each page individually
   ```python
   page_hashes = [
       hashlib.sha256(page_content).hexdigest()
       for page_content in pages
   ]
   ```

2. **Document-Level:** Hash of concatenated page hashes
   ```python
   document_hash = hashlib.sha256(
       "".join(page_hashes).encode()
   ).hexdigest()
   ```

**Benefits:**
- **Consistent:** Same content always produces same hash
- **Efficient:** Enables partial re-indexing (future)
- **Granular:** Detects which specific pages changed
- **Deduplication:** Automatic duplicate detection

---

### 3. Version Query API ✅

**What:** Python API for version operations.

**Core Methods:**

```python
tracker = VersionTracker()

# Track a new version
version = tracker.track_document(
    file_path="document.pdf",
    content_hash="abc123...",
    page_hashes=["page1...", "page2..."],
    metadata={"author": "Jane Doe"}
)

# Check if document changed
is_new = tracker.is_new_version(file_path, content_hash)

# Retrieve versions
version = tracker.get_version(doc_id, version_number=2)
version = tracker.get_version_by_id(version_id)
version = tracker.get_version_by_hash(content_hash)

# List all versions
versions = tracker.list_versions(doc_id)

# Find document
doc_id = tracker.find_document_by_path(file_path)

# Link chunks
tracker.link_chunk_to_version(chunk_id, version_id)
```

---

### 4. CLI Commands ✅

**What:** User-facing commands for version management.

**Implementation:** `src/cli/commands/versions.py` (380+ lines)

**Commands:**

#### `ragged versions list <file_path>`
List all versions of a document with summary table.

```bash
ragged versions list path/to/document.pdf

# Output:
┌─────────┬─────────────┬─────────────┬──────────────┬───────┐
│ Version │ Version ID  │ Hash        │ Created At   │ Pages │
├─────────┼─────────────┼─────────────┼──────────────┼───────┤
│       1 │ abc123...   │ 1a2b3c...   │ 2025-11-20   │    10 │
│       2 │ def456...   │ 4d5e6f...   │ 2025-11-22   │    12 │
└─────────┴─────────────┴─────────────┴──────────────┴───────┘
```

#### `ragged versions show <identifier>`
Show detailed information about a specific version.

```bash
ragged versions show abc123def456
ragged versions show --version-number 2 doc_xyz789
ragged versions show --content-hash 1a2b3c4d...
```

#### `ragged versions check <file_path>`
Check if document has changed since last indexing.

```bash
ragged versions check document.pdf

# Output:
✓ Document unchanged (matches latest version)
```

#### `ragged versions compare <doc_id> <v1> <v2>`
Compare two versions side-by-side.

```bash
ragged versions compare doc_abc123 1 2

# Shows:
# - Content hash changes
# - Page count differences
# - Changed pages
# - Metadata differences
```

---

## Code Metrics

### Production Code

| File | Lines | Purpose |
|------|-------|---------|
| `src/storage/version_tracker.py` | 540 | Version tracking core |
| `src/cli/commands/versions.py` | 380+ | CLI interface |
| `src/storage/__init__.py` | +2 | Package exports |
| `src/main.py` | +2 | CLI registration |
| **Total** | **924+** | **New production code** |

### Test Code

| File | Lines | Tests | Coverage |
|------|-------|-------|----------|
| `tests/storage/test_version_tracker.py` | 450+ | 24 | 96% |

**Test Categories:**
- Database operations (6 tests)
- Hashing algorithms (2 tests)
- Version tracking (5 tests)
- Version queries (6 tests)
- Edge cases (5 tests)

---

## Quality Metrics

### Type Safety
- ✅ 100% type hints
- ✅ Mypy compliant
- ✅ Dataclass for DocumentVersion

### Documentation
- ✅ British English docstrings
- ✅ Comprehensive examples
- ✅ ADR-0020 created
- ✅ Implementation summary
- ✅ CLI help text

### Testing
- ✅ 24 unit tests
- ✅ 96% coverage
- ✅ All tests passing
- ✅ Edge cases covered

### Code Style
- ✅ Black formatted
- ✅ Ruff linted
- ✅ No deprecation warnings (Python 3.12)

---

## Technical Decisions

### Decision 1: SQLite for Version Storage

**Choice:** SQLite database (`~/.ragged/versions.db`)

**Alternatives Considered:**
- ChromaDB metadata (rejected: tight coupling)
- JSON files (rejected: poor query performance)
- Git (rejected: over-engineered)

**Why SQLite Won:**
- Built into Python (zero dependencies)
- ACID transactions
- Indexed queries (fast)
- Relational queries (joins)
- Battle-tested, mature

### Decision 2: Hierarchical Hashing

**Choice:** Page-level + document-level SHA-256

**Why:**
- Enables partial re-indexing (future)
- Detects which pages changed
- Consistent hashing
- Standard cryptographic algorithm

**Alternative:** Single document hash (rejected: no granularity)

### Decision 3: Sequential Version Numbers

**Choice:** 1, 2, 3, ... per document

**Why:**
- Human-friendly
- Chronological ordering
- Easy to reference
- Familiar convention

**Alternative:** Timestamps (rejected: time zone issues, less intuitive)

### Decision 4: Python 3.12 Datetime Compatibility

**Issue:** Deprecated datetime adapter in SQLite3

**Solution:** Convert to ISO format strings
```python
# Before
conn.execute("INSERT ... VALUES (?)", (datetime.now(),))

# After
conn.execute("INSERT ... VALUES (?)", (datetime.now().isoformat(),))
```

**Why:** Future-proof, no deprecation warnings

---

## Integration Points

### With Existing Systems

1. **Storage Package:**
   - Exports: `VersionTracker`, `DocumentVersion`
   - Clean separation from VectorStore

2. **CLI:**
   - New command group: `ragged versions`
   - Follows existing CLI patterns
   - Rich formatting for output

3. **Settings:**
   - Uses `get_settings()` for database path
   - Default: `~/.ragged/versions.db`
   - Configurable via settings

### Future Integration (v0.3.7b+)

1. **Indexing Pipeline:**
   - Call `is_new_version()` before indexing
   - Call `track_document()` after indexing
   - Link chunks with `link_chunk_to_version()`

2. **Query Results:**
   - Attribute results to specific versions
   - Show version metadata in citations
   - Filter by version in search

3. **Partial Re-indexing:**
   - Use page hashes to detect changed pages
   - Re-index only modified pages
   - Significant performance improvement

---

## Performance Characteristics

### Hashing Performance

- **SHA-256:** ~1ms per page (typical)
- **Document hash:** <10ms for 100-page PDF
- **Negligible overhead** compared to PDF parsing

### Database Performance

- **Insert version:** <1ms (SQLite write)
- **Query version:** <1ms (indexed lookup)
- **List versions:** <5ms (100 versions)
- **Concurrent safe:** ACID transactions

### Storage Requirements

- **SQLite overhead:** ~1KB per version
- **Page hashes:** ~64 bytes per page
- **Minimal:** <100KB for typical document history

---

## Backward Compatibility

### Existing Code

✅ **100% backward compatible**

- Version tracking is opt-in
- Existing indexing works unchanged
- No breaking API changes
- Additive changes only

### Existing Databases

✅ **No migration required**

- SQLite database is new
- ChromaDB unchanged
- Old documents: No version history (starts from v0.3.7a)
- Graceful degradation

### Existing CLI

✅ **All existing commands work**

- New `versions` command group added
- No changes to existing commands
- Same user experience

---

## Known Limitations

### 1. No Automatic Integration (Yet)

**Current State:** Version tracking is manual (API only)

**Future (v0.3.7b):**
- Automatic during `ragged add`
- Duplicate detection before indexing
- Chunk-version linking built-in

### 2. No Partial Re-indexing (Yet)

**Current State:** Page hashes stored but not used

**Future (v0.3.7c+):**
- Detect which pages changed
- Re-index only those pages
- Significant performance improvement for large documents

### 3. No Retention Policies (Yet)

**Current State:** All versions kept indefinitely

**Future:**
- Configurable retention (e.g., keep last N versions)
- Automatic cleanup of old versions
- Compression/archival options

### 4. Binary-Only Hashing

**Current State:** Works for PDFs, images, any binary

**Limitation:** No semantic change detection
- Example: Reformat paragraph → new hash (even if content same)
- Future: Semantic similarity for near-duplicate detection

---

## Testing Strategy

### Test Coverage

**24 comprehensive tests covering:**

1. **Initialisation:**
   - Database creation
   - Schema verification
   - Path handling

2. **Hashing:**
   - Page-level hashing
   - Document-level hashing
   - Consistency checks

3. **Version Tracking:**
   - New document (version 1)
   - Updated document (version 2+)
   - Duplicate detection
   - Metadata persistence

4. **Queries:**
   - Get by version number
   - Get by version ID
   - Get by content hash
   - List all versions
   - Find by file path

5. **Edge Cases:**
   - Multiple documents
   - Concurrent tracking
   - Relative/absolute paths
   - Missing files
   - Empty metadata

### Test Fixtures

```python
@pytest.fixture
def temp_db():
    """Temporary SQLite database for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir) / "test_versions.db"

@pytest.fixture
def tracker(temp_db):
    """VersionTracker instance with temp database."""
    return VersionTracker(db_path=temp_db)
```

### Test Results

```
======================== 24 passed in 1.17s =========================
Coverage: 96% on version_tracker.py
```

---

## Documentation

### Created

1. **ADR-0020:** Architecture Decision Record
   - `docs/development/decisions/adrs/0020-document-version-tracking.md`
   - Context, decision, alternatives, consequences

2. **Implementation Summary:** This document
   - `docs/development/implementation/version/v0.3/v0.3.7a/summary.md`
   - Features, metrics, decisions, limitations

3. **Code Documentation:**
   - Comprehensive docstrings (British English)
   - Type hints throughout
   - Examples in docstrings

4. **CLI Help:**
   - `ragged versions --help`
   - `ragged versions list --help`
   - `ragged versions show --help`
   - `ragged versions check --help`
   - `ragged versions compare --help`

---

## Related Documentation

- [ADR-0020: Document Version Tracking](../../../decisions/adrs/0020-document-version-tracking.md)
- [VectorStore Abstraction (v0.3.6)](../v0.3.6/summary.md)
- [v0.3.7 Roadmap](../../../roadmap/version/v0.3.7/README.md)

---

**Status:** ✅ Completed
**Release Date:** 2025-11-22
**Breaking Changes:** 0
**Test Coverage:** 96%
**Production Code:** 924+ lines
**Test Code:** 450+ lines (24 tests)
