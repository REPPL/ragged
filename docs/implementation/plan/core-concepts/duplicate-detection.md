# Duplicate Detection Strategy

**Last Updated**: 2025-11-09
**Purpose**: Content-based duplicate detection (filename-independent)
**Implementation**: v0.2+

---

## Overview

ragged implements **multi-level duplicate detection** to identify:
1. **Exact duplicates**: Same file uploaded multiple times with different names
2. **Near-duplicates**: Same content with minor edits (typo fixes, formatting changes)
3. **Semantic duplicates**: Different wording but same meaning (paraphrases, rewrites)

This is critical because your data collection (~2,000+ documents) may contain the same paper/article saved under different filenames or from different sources.

## Why Not Rely on Filenames?

### Problems with Filename-Based Deduplication

1. **Same content, different names**:
   - `deep-learning-paper.pdf`
   - `2301.12345v1.pdf` (arXiv ID)
   - `1-s2.0-S0166497225000331-main.pdf` (ScienceDirect)
   - `Smith et al 2024.pdf` (manually renamed)

2. **Different versions of same paper**:
   - Preprint vs. published version
   - Different pagination (preprint vs. journal)
   - Author corrections, errata

3. **Downloaded from multiple sources**:
   - arXiv PDF
   - Publisher PDF (with watermarks, different fonts)
   - ResearchGate PDF (with "Downloaded from..." headers)

## Multi-Level Detection Strategy

```
┌────────────────────────┐
│   Input Document       │
└───────────┬────────────┘
            │
            ▼
┌────────────────────────┐
│  Level 1: Exact Match  │
│  (SHA256 hash)         │
└───────────┬────────────┘
            │
            ├─── Match found? → Mark as duplicate, skip processing
            │
            ▼ No match
┌────────────────────────┐
│ Level 2: Near-Duplicate│
│ (MinHash + LSH)        │
└───────────┬────────────┘
            │
            ├─── High similarity (>0.9)? → Flag for review
            │
            ▼ Low similarity
┌────────────────────────┐
│   Process Document     │
│   (Normalize to MD)    │
└───────────┬────────────┘
            │
            ▼
┌────────────────────────┐
│ Level 3: Semantic Dup. │
│ (Embedding similarity) │
└───────────┬────────────┘
            │
            ├─── Very high similarity (>0.95)? → Flag as possible duplicate
            │
            ▼
┌────────────────────────┐
│  Store as Unique Doc   │
└────────────────────────┘
```

## Level 1: Exact Duplicates (SHA256)

### Algorithm

**Content Hashing** with SHA256 of the original file.

```python
import hashlib

def compute_content_hash(file_path: str) -> str:
    """Compute SHA256 hash of file content."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        # Read in chunks to handle large files
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()
```

### Storage

```python
# Before processing any new file
content_hash = compute_content_hash(uploaded_file)

# Check if already exists
existing = db.query(
    "SELECT document_id FROM documents WHERE content_hash = ?",
    (content_hash,)
)

if existing:
    # This is an exact duplicate
    # Add new file path to existing document
    db.execute(
        "INSERT INTO file_paths (document_id, file_path) VALUES (?, ?)",
        (existing["document_id"], uploaded_file.path)
    )
    return existing["document_id"]  # Don't process again
else:
    # New unique file, proceed with processing
    process_document(uploaded_file, content_hash)
```

### Performance

- **Speed**: Extremely fast (~100MB/s on modern CPUs)
- **Accuracy**: 100% for exact matches
- **Memory**: Minimal (streaming hash computation)
- **False Positives**: Zero
- **False Negatives**: Zero (for exact matches)

### Limitations

**Does NOT detect**:
- **Different file formats**: PDF vs. DOCX of same content
- **Different PDF renderings**: Same content, different fonts/layout
- **Minor edits**: Typo fixes, whitespace changes
- **Versioned content**: v1 vs. v2 with edits

These require Level 2 or Level 3.

## Level 2: Near-Duplicates (MinHash + LSH)

### Algorithm

**MinHash with Locality Sensitive Hashing (LSH)** on normalized markdown.

#### Step 1: Normalize Document to Markdown

```python
# After document normalization (v0.2+)
markdown_text = convert_to_markdown(uploaded_file)  # Docling, Trafilatura, etc.

# Normalize whitespace, lowercase
normalized = normalize_text(markdown_text)
```

#### Step 2: Generate MinHash Signature

```python
from datasketch import MinHash

def compute_minhash(text: str, num_perm: int = 128) -> MinHash:
    """Generate MinHash signature from text."""
    m = MinHash(num_perm=num_perm)

    # Tokenize into shingles (n-grams of words)
    words = text.lower().split()
    shingles = [
        " ".join(words[i:i+3])  # 3-word shingles
        for i in range(len(words) - 2)
    ]

    for shingle in shingles:
        m.update(shingle.encode('utf-8'))

    return m
```

#### Step 3: Store in LSH Index

```python
from datasketch import MinHashLSH

# Initialize LSH index (persistent)
lsh = MinHashLSH(
    threshold=0.8,  # Similarity threshold (80%)
    num_perm=128    # Must match MinHash num_perm
)

# Add document signatures
lsh.insert(document_id, minhash)
```

#### Step 4: Query for Near-Duplicates

```python
# Check if new document is similar to existing ones
similar_docs = lsh.query(new_minhash)

if similar_docs:
    # Found potential near-duplicates
    # Compute exact Jaccard similarity
    for doc_id in similar_docs:
        existing_minhash = load_minhash(doc_id)
        similarity = new_minhash.jaccard(existing_minhash)

        if similarity > 0.9:
            # Very high similarity - likely duplicate
            flag_for_review(new_doc_id, doc_id, similarity)
```

### Parameters

**Tunable Parameters**:

| Parameter | Value | Rationale |
|-----------|-------|-----------|
| `num_perm` | 128 | Balance between accuracy and speed |
| `threshold` | 0.8 | 80% similarity triggers LSH match |
| `shingle_size` | 3 | 3-word shingles for text |
| `review_threshold` | 0.9 | >90% similarity flagged as likely duplicate |

**Threshold Interpretation**:
- **0.95-1.0**: Almost certainly duplicate (auto-mark)
- **0.85-0.95**: Likely duplicate (flag for review)
- **0.7-0.85**: Possibly related (show as "similar documents")
- **<0.7**: Probably unique

### Performance

- **Time Complexity**: O(num_docs * b) where b is number of LSH bands
- **Space Complexity**: O(num_docs * num_perm * 8 bytes) ≈ 1KB per document
- **Query Time**: Sub-second for 10K+ documents
- **Accuracy**: ~95% recall, ~90% precision at 0.8 threshold

### Example: Detecting Near-Duplicates

**Document A** (arXiv version):
```markdown
# Deep Learning for Computer Vision

## Abstract
We present a novel approach...

## 1. Introduction
Recent advances in deep learning...
```

**Document B** (published version, minor edits):
```markdown
# Deep Learning for Computer Vision

## Abstract
We present a new approach...  # "novel" → "new"

## 1 Introduction            # "1." → "1"
Recent advances in deep learning...
```

**MinHash similarity**: ~0.95 (very high)
**Outcome**: Flagged as near-duplicate, user can merge or keep separate

### Persistent Storage

```python
# SQLite table for MinHash signatures
CREATE TABLE minhash_signatures (
    document_id TEXT PRIMARY KEY,
    signature BLOB NOT NULL,  # Pickled MinHash object
    created_date TEXT NOT NULL,
    FOREIGN KEY (document_id) REFERENCES documents(document_id)
);

# Save MinHash
import pickle

def save_minhash(document_id: str, minhash: MinHash):
    """Persist MinHash signature."""
    signature_bytes = pickle.dumps(minhash)
    db.execute(
        "INSERT INTO minhash_signatures VALUES (?, ?, ?)",
        (document_id, signature_bytes, datetime.now().isoformat())
    )

# Load MinHash
def load_minhash(document_id: str) -> MinHash:
    """Load persisted MinHash."""
    row = db.query(
        "SELECT signature FROM minhash_signatures WHERE document_id = ?",
        (document_id,)
    )
    return pickle.loads(row["signature"])
```

### LSH Index Rebuilding

**Problem**: LSH index is in-memory, needs rebuilding on restart.

**Solution**: Rebuild from persisted MinHash signatures.

```python
def rebuild_lsh_index():
    """Rebuild LSH index from database on startup."""
    lsh = MinHashLSH(threshold=0.8, num_perm=128)

    rows = db.query("SELECT document_id, signature FROM minhash_signatures")
    for row in rows:
        minhash = pickle.loads(row["signature"])
        lsh.insert(row["document_id"], minhash)

    return lsh
```

**Startup Time**: ~1-2 seconds for 10K documents, ~10-20 seconds for 100K.

## Level 3: Semantic Duplicates (Embedding Similarity)

### Algorithm

**Embedding-based similarity** using document-level embeddings.

Detects semantically identical documents with different wording.

#### Step 1: Generate Document Embedding

```python
from sentence_transformers import SentenceTransformer

model = SentenceTransformer('all-MiniLM-L6-v2')

def compute_document_embedding(markdown_text: str) -> np.ndarray:
    """Generate single embedding for entire document."""
    # Truncate to model's max length (512 tokens for MiniLM)
    # Or use summary/abstract if available
    truncated = markdown_text[:10000]  # ~2000 words

    embedding = model.encode(truncated, convert_to_numpy=True)
    return embedding  # Shape: (384,) for MiniLM
```

#### Step 2: Store in Vector Database

```python
# Use separate ChromaDB collection for document-level embeddings
doc_collection = chromadb.create_collection(
    name="documents_fulltext",
    metadata={"description": "Document-level embeddings for deduplication"}
)

doc_collection.add(
    ids=[document_id],
    embeddings=[doc_embedding.tolist()],
    metadatas=[{"document_id": document_id, "title": title}]
)
```

#### Step 3: Query for Semantic Duplicates

```python
# After processing new document
similar_docs = doc_collection.query(
    query_embeddings=[new_doc_embedding.tolist()],
    n_results=5,  # Top 5 most similar
    include=["distances", "metadatas"]
)

for i, doc_id in enumerate(similar_docs["ids"][0]):
    similarity = 1 - similar_docs["distances"][0][i]  # Cosine similarity

    if similarity > 0.95:
        # Extremely high semantic similarity
        flag_as_semantic_duplicate(new_doc_id, doc_id, similarity)
    elif similarity > 0.85:
        # Highly related, but maybe not duplicate
        mark_as_related(new_doc_id, doc_id, similarity)
```

### Thresholds

| Cosine Similarity | Interpretation | Action |
|-------------------|----------------|--------|
| 0.98-1.0 | Identical content | Auto-mark as duplicate |
| 0.95-0.98 | Very likely duplicate | Flag for review |
| 0.85-0.95 | Highly similar | Show as "related document" |
| 0.7-0.85 | Somewhat similar | Show in "see also" |
| <0.7 | Different content | No action |

### Performance

- **Embedding Time**: ~100ms per document (CPU), ~10ms (GPU)
- **Storage**: 384 floats × 4 bytes = 1.5KB per document (for MiniLM)
- **Query Time**: <100ms for 10K documents (ChromaDB with HNSW index)
- **Accuracy**: Excellent for semantic similarity, may miss surface-level differences

### Example: Semantic Duplicate Detection

**Document A** (Technical paper):
```markdown
# Neural Networks for Image Classification

Convolutional neural networks (CNNs) have revolutionized
computer vision by achieving state-of-the-art accuracy on
image classification benchmarks like ImageNet.
```

**Document B** (Popular science article):
```markdown
# How AI Learns to Recognize Pictures

Artificial intelligence uses special algorithms called
convolutional networks that can identify objects in photos
with incredible accuracy, beating human performance on
standard tests.
```

**Embedding similarity**: ~0.88 (high, but not duplicate)
**Outcome**: Marked as "related" but not duplicate

**Document C** (Paraphrase):
```markdown
# Neural Networks for Image Classification

CNNs have revolutionized computer vision, achieving
state-of-the-art accuracy on image classification
benchmarks such as ImageNet.
```

**Embedding similarity**: ~0.97 (very high)
**Outcome**: Flagged as likely duplicate (minor paraphrase)

### When to Use Embedding Similarity

**Use Cases**:
- Detecting **paraphrased content** (plagiarism detection)
- Finding **different versions** with significant rewrites
- Identifying **translations** (if using multilingual embeddings)
- Grouping **related documents** for browsing

**Limitations**:
- **Computationally expensive**: Requires embedding every document
- **Storage overhead**: 1.5KB per document for embeddings
- **Not suitable for large-scale** (>100K documents) without optimization
- **May miss exact duplicates** if semantic content differs (tables, code)

**Recommendation**: Use as **targeted tool** in v0.3+, not default for all documents.

## Multi-Level Integration

### Combined Workflow

```python
async def check_duplicates(file_path: str) -> DuplicateResult:
    """
    Check for duplicates using all three levels.

    Returns:
        DuplicateResult with:
        - is_duplicate: bool
        - duplicate_of: document_id or None
        - similarity_score: 0.0-1.0
        - detection_method: "exact" | "near" | "semantic"
    """

    # Level 1: Exact match (SHA256)
    content_hash = compute_content_hash(file_path)
    exact_match = db.query(
        "SELECT document_id FROM documents WHERE content_hash = ?",
        (content_hash,)
    )

    if exact_match:
        return DuplicateResult(
            is_duplicate=True,
            duplicate_of=exact_match["document_id"],
            similarity_score=1.0,
            detection_method="exact"
        )

    # Level 2: Near-duplicate (MinHash)
    markdown = await convert_to_markdown(file_path)
    minhash = compute_minhash(markdown)
    similar_docs = lsh.query(minhash)

    for doc_id in similar_docs:
        existing_minhash = load_minhash(doc_id)
        similarity = minhash.jaccard(existing_minhash)

        if similarity > 0.95:
            # Very high text similarity
            return DuplicateResult(
                is_duplicate=True,
                duplicate_of=doc_id,
                similarity_score=similarity,
                detection_method="near"
            )

    # Level 3: Semantic duplicate (optional, v0.3+)
    if config.enable_semantic_dedup:
        doc_embedding = compute_document_embedding(markdown)
        semantic_results = doc_collection.query(
            query_embeddings=[doc_embedding.tolist()],
            n_results=1
        )

        if semantic_results["ids"][0]:
            similarity = 1 - semantic_results["distances"][0][0]
            if similarity > 0.95:
                return DuplicateResult(
                    is_duplicate=True,
                    duplicate_of=semantic_results["ids"][0][0],
                    similarity_score=similarity,
                    detection_method="semantic"
                )

    # No duplicates found
    return DuplicateResult(
        is_duplicate=False,
        duplicate_of=None,
        similarity_score=0.0,
        detection_method=None
    )
```

## Handling Duplicates

### Storage Strategy

**Option 1: Single Document, Multiple Paths** (Recommended)

```python
# Store document once
document_id = "abc123"  # Based on content hash

# Track all file paths
file_paths = [
    "/uploads/deep-learning-paper.pdf",
    "/uploads/2301.12345v1.pdf",
    "/uploads/smith-et-al-2024.pdf"
]

# In database
{
    "document_id": "abc123",
    "original_filename": "deep-learning-paper.pdf",  # First uploaded
    "all_filenames": [
        "deep-learning-paper.pdf",
        "2301.12345v1.pdf",
        "smith-et-al-2024.pdf"
    ],
    "duplicate_of": null,
    ...
}
```

**Advantages**:
- No wasted storage (original file stored once)
- No wasted processing (normalize/chunk/embed once)
- User can see all filenames that map to this document

**Option 2: Separate Documents, Linked**

```python
# Original document
{
    "document_id": "abc123",
    "original_filename": "deep-learning-paper.pdf",
    "duplicate_of": null,
    "duplicates": ["def456", "ghi789"]
}

# Duplicate 1
{
    "document_id": "def456",
    "original_filename": "2301.12345v1.pdf",
    "duplicate_of": "abc123",  # Points to original
    "duplicates": []
}

# Duplicate 2
{
    "document_id": "ghi789",
    "original_filename": "smith-et-al-2024.pdf",
    "duplicate_of": "abc123",
    "duplicates": []
}
```

**Advantages**:
- Preserves all original files
- Can track different metadata (if files differ slightly)
- Easier to unlink if user decides they're NOT duplicates

**Disadvantages**:
- Uses more disk space (3x for 3 duplicates)

**Recommendation**: Use Option 1 (single document, multiple paths) for exact/near duplicates, Option 2 for semantic duplicates (which may have different metadata).

### User Interface

**Duplicate Notification**:
```
┌──────────────────────────────────────────────────────┐
│ ⚠️  Duplicate Detected                               │
├──────────────────────────────────────────────────────┤
│ The uploaded file appears to be a duplicate:         │
│                                                       │
│ New file:                                             │
│   📄 "2301.12345v1.pdf"                              │
│                                                       │
│ Existing document:                                    │
│   📄 "Deep Learning for Computer Vision"            │
│   👤 Smith, J., Doe, A.                              │
│   📅 Uploaded: 2024-10-15                            │
│   📂 Collection: "Deep Learning Papers"              │
│                                                       │
│ Similarity: 98% (SHA256 exact match)                 │
│                                                       │
│ [ Keep Both ]  [ Replace Existing ]  [ Link Files ]  │
└──────────────────────────────────────────────────────┘
```

**Options**:
1. **Keep Both**: Store as separate documents (override duplicate detection)
2. **Replace Existing**: Delete old, keep new (useful if new has better quality)
3. **Link Files**: Store once, track both filenames (default for duplicates)

### Batch Deduplication

For existing collections, run deduplication periodically:

```python
async def deduplicate_collection(collection_id: str):
    """Find and merge duplicates in existing collection."""

    docs = get_collection_documents(collection_id)

    # Build MinHash index
    lsh = MinHashLSH(threshold=0.8, num_perm=128)
    for doc in docs:
        markdown = load_markdown(doc["document_id"])
        minhash = compute_minhash(markdown)
        lsh.insert(doc["document_id"], minhash)

    # Find duplicate clusters
    duplicates = []
    processed = set()

    for doc in docs:
        if doc["document_id"] in processed:
            continue

        minhash = load_minhash(doc["document_id"])
        similar = lsh.query(minhash)

        if len(similar) > 1:
            # Found duplicate cluster
            cluster = []
            for sim_id in similar:
                if sim_id not in processed:
                    cluster.append(sim_id)
                    processed.add(sim_id)

            duplicates.append(cluster)

    return duplicates  # User can review and merge
```

## Performance Optimization

### Incremental Indexing

**Problem**: Rebuilding entire LSH index on every upload is slow.

**Solution**: Incremental updates.

```python
class PersistentLSH:
    """LSH index with disk persistence."""

    def __init__(self, db_path: str):
        self.lsh = MinHashLSH(threshold=0.8, num_perm=128)
        self.db_path = db_path
        self._load_from_disk()

    def _load_from_disk(self):
        """Load all MinHash signatures from SQLite."""
        signatures = db.query("SELECT document_id, signature FROM minhash_signatures")
        for row in signatures:
            minhash = pickle.loads(row["signature"])
            self.lsh.insert(row["document_id"], minhash)

    def insert(self, document_id: str, minhash: MinHash):
        """Insert new signature (in-memory and on-disk)."""
        # In-memory
        self.lsh.insert(document_id, minhash)

        # On-disk
        save_minhash(document_id, minhash)

    def query(self, minhash: MinHash) -> List[str]:
        """Query for similar documents."""
        return self.lsh.query(minhash)
```

### Parallel Processing

```python
from concurrent.futures import ThreadPoolExecutor

async def batch_dedup_check(file_paths: List[str]) -> List[DuplicateResult]:
    """Check multiple files for duplicates in parallel."""

    with ThreadPoolExecutor(max_workers=4) as executor:
        results = list(executor.map(check_duplicates, file_paths))

    return results
```

### Caching

```python
from functools import lru_cache

@lru_cache(maxsize=1000)
def load_minhash_cached(document_id: str) -> MinHash:
    """Load MinHash with in-memory caching."""
    return load_minhash(document_id)
```

## Version Roadmap

### v0.1
- **No duplicate detection**
- Documents can be uploaded multiple times

### v0.2
- **Level 1: SHA256** (exact duplicates)
- **Level 2: MinHash+LSH** (near-duplicates)
- SQLite storage for hashes/signatures
- Basic UI notification

### v0.3
- **Level 3: Embedding similarity** (semantic duplicates)
- Batch deduplication tool
- Advanced duplicate review UI
- User can merge/unlink duplicates

### v1.0
- **Automatic deduplication** (optional setting)
- Duplicate clusters (find groups of related docs)
- Similarity-based document browsing
- Export duplicate reports

## Testing Strategy

```python
def test_exact_duplicate_detection():
    """Test SHA256 detects exact duplicates."""
    # Upload same file twice with different names
    doc1_id = upload_document("paper.pdf", filename="original.pdf")
    doc2_id = upload_document("paper.pdf", filename="copy.pdf")

    # Should have same document ID
    assert doc1_id == doc2_id

    # Should have both filenames tracked
    filenames = get_filenames(doc1_id)
    assert "original.pdf" in filenames
    assert "copy.pdf" in filenames

def test_near_duplicate_detection():
    """Test MinHash detects near-duplicates."""
    # Create near-duplicate (same content, minor edits)
    markdown_a = "# Title\n\nSome content here."
    markdown_b = "# Title\n\nSome content here!"  # Added exclamation

    minhash_a = compute_minhash(markdown_a)
    minhash_b = compute_minhash(markdown_b)

    similarity = minhash_a.jaccard(minhash_b)
    assert similarity > 0.95  # Very high similarity

def test_semantic_duplicate_detection():
    """Test embeddings detect semantic duplicates."""
    doc_a = "Deep learning has revolutionized computer vision."
    doc_b = "Computer vision has been transformed by deep learning."

    emb_a = compute_document_embedding(doc_a)
    emb_b = compute_document_embedding(doc_b)

    similarity = cosine_similarity(emb_a, emb_b)
    assert similarity > 0.85  # High semantic similarity
```

## References

- **MinHash Original Paper**: Broder, A. Z. (1997). "On the resemblance and containment of documents"
- **LSH Tutorial**: https://milvus.io/docs/minhash-lsh.md
- **datasketch Library**: https://github.com/ekzhu/datasketch
- **text-dedup**: https://github.com/ChenghaoMou/text-dedup (LLM training dedup)
- **Simhash**: https://github.com/sumonbis/NearDuplicateDetection

---

**Next Steps**: Implement in v0.2 alongside document normalization pipeline.
