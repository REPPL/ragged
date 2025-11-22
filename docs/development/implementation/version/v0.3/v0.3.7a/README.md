# v0.3.7a - Document Version Tracking

**Status:** ✅ Completed
**Release Date:** 2025-11-22

---

## Purpose

This directory contains the implementation record for v0.3.7a, documenting the document version tracking system that enables change detection, version history queries, and lays the foundation for partial re-indexing optimisations.

---

## Contents

### [summary.md](./summary.md)
Complete implementation summary including:
- Features delivered (SQLite store, hierarchical hashing, CLI commands)
- Code metrics (924+ lines production, 24 tests, 96% coverage)
- Technical decisions (why SQLite, hierarchical hashing, sequential versioning)
- Known limitations and future enhancements

---

## Quick Facts

**Implemented Features:**

1. **SQLite Version Store**
   - Three-table schema (documents, versions, chunk_versions)
   - ACID transactions
   - Indexed queries
   - Default location: `~/.ragged/versions.db`

2. **Hierarchical Content Hashing**
   - Page-level SHA-256 hashing
   - Document-level hash (concatenated page hashes)
   - Enables partial re-indexing (future)
   - Automatic duplicate detection

3. **Version Query API**
   - `track_document()` - Create new version
   - `is_new_version()` - Check if changed
   - `get_version()` - Retrieve by number/ID/hash
   - `list_versions()` - Get all versions
   - `link_chunk_to_version()` - Associate chunks

4. **CLI Commands**
   - `ragged versions list` - List all versions
   - `ragged versions show` - Show version details
   - `ragged versions check` - Check if document changed
   - `ragged versions compare` - Compare two versions

**Code Metrics:**
- Production code: 924+ lines
  - `version_tracker.py`: 540 lines
  - `versions.py` (CLI): 380+ lines
- Test code: 450+ lines (24 tests)
- Test coverage: 96%
- All tests passing

**Performance:**
- SHA-256 hashing: ~1ms per page
- Database queries: <1ms (indexed)
- Storage overhead: ~1KB per version

---

## Key Technical Decisions

**1. SQLite for Version Storage**
- Built into Python (zero dependencies)
- ACID transactions
- Fast indexed queries
- Rejected alternatives: ChromaDB metadata, JSON files, Git

**2. Hierarchical Hashing**
- Page-level + document-level
- Enables future partial re-indexing
- Consistent, deterministic
- SHA-256 standard algorithm

**3. Sequential Version Numbers**
- Human-friendly (1, 2, 3, ...)
- Chronological ordering
- Easy to reference
- Familiar convention

**4. Python 3.12 Compatibility**
- ISO format strings for datetime
- No deprecation warnings
- Future-proof

---

## Example Usage

### Python API

```python
from src.storage import VersionTracker

tracker = VersionTracker()

# Calculate hash
with open("document.pdf", "rb") as f:
    content = f.read()
content_hash, page_hashes = tracker.calculate_content_hash(content)

# Check if new version
if tracker.is_new_version("document.pdf", content_hash):
    # Track new version
    version = tracker.track_document(
        file_path="document.pdf",
        content_hash=content_hash,
        page_hashes=page_hashes,
        metadata={"author": "Jane Doe"}
    )
    print(f"Tracked version {version.version_number}")
else:
    print("Document unchanged")

# List versions
versions = tracker.list_versions(doc_id)
for v in versions:
    print(f"v{v.version_number}: {v.created_at}")
```

### CLI

```bash
# List all versions
ragged versions list path/to/document.pdf

# Show version details
ragged versions show --version-number 2 doc_abc123

# Check if document changed
ragged versions check document.pdf

# Compare versions
ragged versions compare doc_abc123 1 2
```

---

## Known Limitations

1. **No Automatic Integration:** Version tracking is manual (v0.3.7b will integrate with `ragged add`)
2. **No Partial Re-indexing:** Page hashes stored but not yet used for optimisation
3. **No Retention Policies:** All versions kept indefinitely
4. **Binary-Only Hashing:** No semantic change detection

---

## Navigation

**Related Documentation:**
- [ADR-0020: Document Version Tracking](../../../../decisions/adrs/0020-document-version-tracking.md) - Architecture decision
- [v0.3 Index](../README.md) - All v0.3.x implementations
- [v0.3.7 Roadmap](../../../../roadmap/version/v0.3.7/README.md) - Full v0.3.7 plan (5 features)

**Source Code:**
- [VersionTracker](../../../../../../src/storage/version_tracker.py) - Core implementation
- [CLI Commands](../../../../../../src/cli/commands/versions.py) - User interface
- [Tests](../../../../../../tests/storage/test_version_tracker.py) - 24 comprehensive tests

---

**Status:** ✅ Completed
**Breaking Changes:** 0 (100% backward compatible)
**Test Coverage:** 96%
