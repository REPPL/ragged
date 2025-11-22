# ADR-0020: Document Version Tracking

**Date:** 2025-11-22
**Status:** Accepted (Implemented in v0.3.7a)
**Deciders:** ragged development team
**Tags:** architecture, storage, versioning, v0.3.7a

---

## Context

ragged currently lacks a mechanism to track document versions over time. When users update a PDF (e.g., fix errors, add pages, revise content), the system:

1. **Cannot detect changes** - No way to know if a document has been updated
2. **Loses version history** - Old versions are lost when re-indexing
3. **Cannot query by version** - Users cannot retrieve specific versions
4. **Wastes resources** - Re-indexes unchanged documents unnecessarily

### User Scenarios

**Scenario 1: Legal Document Updates**
- User indexes contract_v1.pdf (10 pages)
- Contract updated with new clause → contract_v2.pdf (12 pages)
- User wants to query both versions separately
- Current system: Only latest version available

**Scenario 2: Academic Paper Revisions**
- Researcher indexes paper draft (50 pages)
- Paper revised based on feedback
- Need to track which version findings came from
- Current system: No version attribution

**Scenario 3: Compliance Documentation**
- Company policy updated quarterly
- Need to prove which policy version was active on specific date
- Current system: Cannot retrieve historical versions

### Current State

- No version tracking mechanism
- Document re-indexing overwrites previous data
- No change detection
- No version history queries
- Inefficient: Always full re-index

### Target State (v0.3.7a)

- Content-based version detection (SHA-256 hashing)
- Hierarchical hashing (page-level + document-level)
- Persistent version storage (SQLite)
- Version-specific queries via CLI
- Automatic duplicate detection
- Partial re-indexing support (future)

---

## Decision

We will implement **SQLite-based document version tracking** with hierarchical content hashing to enable version detection, storage, and retrieval.

### Architecture

```
┌─────────────────────────────────────────┐
│        Document Indexing Flow           │
├─────────────────────────────────────────┤
│                                         │
│  PDF File → Hash Calculation            │
│              ├─ Page 1 → SHA-256        │
│              ├─ Page 2 → SHA-256        │
│              └─ Page N → SHA-256        │
│                    ↓                    │
│           Combine page hashes           │
│                    ↓                    │
│           Document SHA-256              │
│                    ↓                    │
│         Version Tracker Check           │
│         ├─ New document? → v1           │
│         ├─ Same hash? → Skip            │
│         └─ Different hash? → v2+        │
│                    ↓                    │
│        Store in SQLite + ChromaDB       │
│                                         │
└─────────────────────────────────────────┘
```

### Core Components

#### 1. DocumentVersion Dataclass

```python
@dataclass
class DocumentVersion:
    version_id: str           # UUID for this version
    doc_id: str              # Stable document identifier
    content_hash: str        # SHA-256 of document
    page_hashes: List[str]   # SHA-256 of each page
    version_number: int      # Sequential (1, 2, 3, ...)
    created_at: datetime     # When version was created
    file_path: str           # Absolute path to file
    metadata: Dict[str, Any] # Custom metadata
```

#### 2. VersionTracker Class

**Storage:** SQLite database (`~/.ragged/versions.db`)

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
    page_hashes TEXT NOT NULL,  -- JSON array
    version_number INTEGER NOT NULL,
    created_at TIMESTAMP NOT NULL,
    file_path TEXT NOT NULL,
    metadata TEXT,              -- JSON object
    FOREIGN KEY (doc_id) REFERENCES documents(doc_id),
    UNIQUE(doc_id, version_number)
);

-- Chunk-to-version mapping
CREATE TABLE chunk_versions (
    chunk_id TEXT NOT NULL,
    version_id TEXT NOT NULL,
    page_number INTEGER,
    chunk_sequence INTEGER,
    FOREIGN KEY (version_id) REFERENCES versions(version_id),
    PRIMARY KEY (chunk_id, version_id)
);
```

**Key Methods:**
- `calculate_content_hash()` - Hierarchical SHA-256 hashing
- `track_document()` - Add/update version record
- `is_new_version()` - Check if content changed
- `get_version()` - Retrieve specific version
- `list_versions()` - Get all versions of a document
- `link_chunk_to_version()` - Associate chunks with versions

#### 3. CLI Commands

```bash
# List all versions of a document
ragged versions list path/to/document.pdf

# Show version details
ragged versions show <version_id>
ragged versions show --version-number 2 <doc_id>
ragged versions show --content-hash <hash>

# Check if document changed
ragged versions check path/to/document.pdf

# Compare two versions
ragged versions compare <doc_id> 1 2
```

---

## Consequences

### Positive

1. **Change Detection**
   - Automatic detection of document updates
   - Avoids re-indexing unchanged documents
   - Improves efficiency and user experience

2. **Version History**
   - Complete audit trail of document changes
   - Retrieve any historical version
   - Compliance and legal use cases enabled

3. **Partial Re-indexing (Future)**
   - Page-level hashes enable detecting specific changed pages
   - Re-index only modified pages (not implemented in v0.3.7a)
   - Significant performance improvement for large documents

4. **Clean Separation**
   - SQLite separate from ChromaDB (single responsibility)
   - Easy to query version metadata
   - No pollution of vector store with version data

5. **Chunk Attribution**
   - Link chunks to specific versions
   - Track which version a result came from
   - Important for reproducibility and citations

### Negative

1. **Additional Storage**
   - SQLite database adds disk usage (~1KB per version)
   - Minimal compared to vector embeddings
   - **Mitigation:** Configurable retention policies (future)

2. **Additional Dependency**
   - SQLite (built into Python, no new package)
   - **Mitigation:** Zero additional dependencies

3. **Complexity**
   - More moving parts in indexing pipeline
   - **Mitigation:** Clear separation of concerns, comprehensive tests

4. **Migration Path**
   - Existing users have no version history for old documents
   - **Mitigation:** Graceful degradation, versions tracked from v0.3.7a onward

### Neutral

1. **Performance Impact**
   - Minimal: SHA-256 hashing is fast (<1ms per page)
   - SQLite queries are negligible overhead
   - Benefits outweigh cost for large documents

2. **Backward Compatibility**
   - 100% backward compatible (version tracking optional)
   - Existing code works unchanged
   - CLI commands are additive

---

## Alternatives Considered

### Alternative 1: Store Versions in ChromaDB Metadata

**Approach:** Use ChromaDB metadata to track version information.

**Rejected Because:**
- Pollutes vector store with non-vector data
- ChromaDB not designed for relational queries
- Difficult to query version history
- Tight coupling between versioning and vector storage
- No separation of concerns

### Alternative 2: File-Based Version Storage (JSON)

**Approach:** Store version info in `.ragged/versions/<doc_id>.json` files.

**Pros:**
- Simple, no database required
- Easy to inspect manually
- Git-friendly

**Cons:**
- Poor query performance (must scan all files)
- No ACID guarantees
- Difficult to implement complex queries (e.g., "find all versions between dates")
- No built-in indexing
- Race conditions in concurrent access

**Why SQLite Won:**
- Built-in to Python (no dependencies)
- ACID transactions
- Indexed queries (fast lookups)
- Relational queries (join documents ↔ versions ↔ chunks)
- Mature, battle-tested
- Minimal overhead

### Alternative 3: Git-Based Versioning

**Approach:** Use git to track document versions.

**Pros:**
- Robust version control
- Diffing built-in
- Industry standard

**Cons:**
- Heavyweight for binary PDFs
- Git not optimised for large binary files
- Requires git installation
- Complex API for simple version queries
- Poor fit for content-based deduplication

**Why Rejected:** Over-engineered for the use case. Git excels at text diffs, not binary PDF versioning.

### Alternative 4: Content-Addressed Storage (CAS)

**Approach:** Use content hashes as identifiers (like Git internally).

**Pros:**
- Automatic deduplication
- Content-addressable retrieval
- Space-efficient

**Cons:**
- No human-readable version numbers
- Difficult to query "latest version"
- No chronological ordering
- Complex to implement version sequences

**Decision:** Use CAS internally (content_hash) but expose sequential version numbers (1, 2, 3) for user-friendliness.

---

## Implementation Details

### Hashing Strategy

**Hierarchical SHA-256:**

1. **Page-Level Hashing:**
   ```python
   page_hashes = [
       hashlib.sha256(page_content).hexdigest()
       for page_content in pages
   ]
   ```

2. **Document-Level Hashing:**
   ```python
   document_hash = hashlib.sha256(
       "".join(page_hashes).encode()
   ).hexdigest()
   ```

**Why This Approach:**
- Consistent: Same content → same hash
- Efficient: Incremental hashing possible
- Granular: Page-level changes detectable
- Standard: SHA-256 widely trusted

### Version Numbering

**Sequential (1, 2, 3, ...) per document:**
- Easy to understand
- Chronological ordering
- Human-friendly references
- Compatible with semantic versioning conventions

**Alternative Considered:** Timestamps
- **Rejected:** Less intuitive, time zone issues, collisions possible

### Duplicate Detection

**Before indexing:**
```python
if tracker.is_new_version(file_path, content_hash):
    # Index the document
    version = tracker.track_document(...)
else:
    # Skip indexing (already exists)
    logger.info("Document unchanged, skipping")
```

**Benefits:**
- Saves CPU time (no unnecessary embedding generation)
- Saves disk space (no duplicate chunks)
- Faster indexing for large document sets

### Chunk-Version Linking

**During indexing:**
```python
for chunk in chunks:
    chunk_id = vectorstore.add(chunk)
    tracker.link_chunk_to_version(
        chunk_id=chunk_id,
        version_id=version.version_id,
        page_number=chunk.page,
        chunk_sequence=chunk.sequence
    )
```

**Use Case:** Retrieve version for a search result chunk.

---

## Testing Strategy

**Comprehensive test coverage (24 tests):**

1. **Database Operations:**
   - Initialisation creates schema
   - CRUD operations work correctly
   - Transactions are atomic

2. **Hashing:**
   - Consistent hashing (same input → same output)
   - Page-level hashing accurate
   - Document-level hash derived correctly

3. **Version Tracking:**
   - New documents get version 1
   - Updated documents increment version
   - Duplicate detection works
   - Metadata persisted correctly

4. **Querying:**
   - Get version by number
   - Get version by ID
   - Get version by hash
   - List all versions
   - Find document by path

5. **Edge Cases:**
   - Multiple documents tracked independently
   - Concurrent version tracking
   - Relative paths converted to absolute
   - Missing files handled gracefully

**Test Coverage:** 96% on version_tracker.py

---

## Migration Path

**v0.3.7a:**
- ✅ SQLite version tracking implemented
- ✅ CLI commands for version queries
- ⏸ Integration with indexing pipeline (v0.3.7b)
- ⏸ Partial re-indexing (future)
- ⏸ Retention policies (future)

**Future Enhancements (v0.3.7+):**
1. **Automatic integration** - Version tracking during `ragged add`
2. **Partial re-indexing** - Re-index only changed pages
3. **Retention policies** - Auto-delete old versions after N days
4. **Version comparison** - Diff tool for document changes
5. **Version restore** - Roll back to previous version

**Backward Compatibility:**
- Existing documents: No version history (starts from v0.3.7a)
- Existing code: 100% compatible (additive changes only)
- Existing databases: No migration required

---

## Related Documentation

- [v0.3.7a Implementation Summary](../../implementation/version/v0.3/v0.3.7a/summary.md)
- [VectorStore Abstraction (ADR-0015)](./0015-vectorstore-abstraction.md)
- [v0.3.7 Roadmap](../../roadmap/version/v0.3.7/README.md)

---

**Status:** Accepted (Implemented)
**Last Updated:** 2025-11-22
