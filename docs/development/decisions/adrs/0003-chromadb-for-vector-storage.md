# ADR-0003: ChromaDB for Vector Storage

**Status:** Accepted

**Date:** 2025-11-09

**Area:** Vector Database, Storage

**Related:**
- [Vector Stores Evaluation](../technology-stack/vector-stores.md)
- [Storage Model](../architecture/storage-model.md)

---

## Context

ragged requires a vector database to:
- Store document embeddings (384 or 768 dimensions)
- Perform similarity search (cosine, L2, or IP distance)
- Filter by metadata (collection, source, date, etc.)
- Handle CRUD operations for documents
- Scale to thousands of documents for local use

The vector database must work locally (no cloud dependencies), integrate well with Python, and provide good performance for <10k documents in v0.1.

## Decision

Use **ChromaDB** as the primary vector database with HTTP client mode:
- Deploy as Docker container or standalone service
- HTTP client integration from Python
- Persistent storage on disk
- Collections for logical document grouping

## Rationale

**Local-First:**
- Fully local deployment
- No external dependencies or cloud services
- Works offline
- User controls all data

**Simplicity:**
- Easy setup (single Docker container)
- Simple Python API
- Minimal configuration required
- Good documentation

**Features:**
- Metadata filtering with `where` clauses
- Multiple distance metrics (L2, cosine, IP)
- Collections for multi-tenancy
- Full CRUD operations
- Batch operations for performance

**Python Integration:**
- Native Python client
- Type hints support
- Async support (for future)
- Good error messages

**Performance:**
- Fast enough for v0.1 (<10k chunks)
- In-memory caching
- Batch upsert support
- Efficient HTTP protocol

**Ecosystem:**
- Active development and community
- Integration with popular RAG frameworks
- Well-maintained documentation

## Alternatives Considered

**1. Qdrant**
- **Pros:** Better performance at scale, more features, production-ready
- **Cons:** More complex setup, heavier resource usage, overkill for v0.1
- **Decision:** Consider for v0.3+ when scale requirements increase

**2. FAISS (Facebook AI Similarity Search)**
- **Pros:** Very fast, battle-tested, flexible
- **Cons:** No built-in metadata filtering, no persistence out-of-box, lower-level API
- **Decision:** Too low-level for v0.1, difficult to add metadata filtering

**3. Milvus**
- **Pros:** Production-grade, highly scalable, enterprise features
- **Cons:** Overkill for v0.1, complex deployment (multiple containers), heavy resource usage
- **Decision:** Defer to v1.0+ for enterprise deployments

**4. Weaviate**
- **Pros:** GraphQL API, built-in vectorization, schema management
- **Cons:** More complex, heavier footprint, steeper learning curve
- **Decision:** Too complex for v0.1 needs

**5. Pinecone**
- **Pros:** Managed service, excellent performance
- **Cons:** Cloud-only (violates [ADR-0001](./0001-local-only-processing.md))
- **Decision:** Rejected—not local

**6. pgvector (PostgreSQL extension)**
- **Pros:** Leverages existing database, simple
- **Cons:** Requires PostgreSQL, slower than specialized vector DBs
- **Decision:** Defer—consider for v0.2 if SQL integration needed

## Consequences

### Positive

✅ **Simple Setup:** Single Docker container
✅ **Easy Integration:** Clean Python API
✅ **Local Storage:** All data on user's machine
✅ **Metadata Filtering:** Rich query capabilities
✅ **Collections:** Logical document grouping
✅ **CRUD Operations:** Full data management
✅ **Good Performance:** Fast enough for v0.1 use cases
✅ **Active Development:** Regular updates

### Negative

⚠️ **Scale Limitations:** May need migration for >10k documents
⚠️ **HTTP Overhead:** Network latency vs. in-process
⚠️ **Resource Usage:** Requires separate service
⚠️ **Query Optimisation:** Limited advanced query options
⚠️ **Migration Path:** May need to migrate to Qdrant later

### Trade-Offs Accepted

- HTTP overhead acceptable for local use (low latency)
- Scale limitations fine for v0.1 scope
- Simple API preferred over advanced features
- Docker dependency acceptable (standard tooling)

## Implementation Notes

**Connection pattern:**
```python
import chromadb

# HTTP client (recommended for production)
client = chromadb.HttpClient(
    host="localhost",
    port=8001
)

# Collection management
collection = client.get_or_create_collection(
    name="documents",
    metadata={"description": "User documents"}
)
```

**Operations:**
```python
# Upsert with metadata
collection.upsert(
    ids=["doc1_chunk0"],
    embeddings=[[0.1, 0.2, ...]],
    documents=["chunk text"],
    metadatas=[{"source": "doc.pdf", "page": 1}]
)

# Query with filtering
results = collection.query(
    query_embeddings=[[0.1, 0.2, ...]],
    n_results=5,
    where={"source": "doc.pdf"}
)
```

**Deployment:**
- Docker Compose for development
- Standalone for production
- Persistent volume for data
- Health checks configured

## Migration Path

**Trigger for migration:** >10k documents OR performance issues

**Migration options:**
1. **Qdrant** (most likely)—better performance, more features
2. **Milvus** (enterprise)—if production-grade needed
3. **Hybrid** (Chroma + Qdrant)—gradual migration

**Migration strategy:**
- Export from ChromaDB collections
- Transform to target format
- Bulk import to new database
- Verify data integrity
- Update configuration

## Performance Characteristics

**v0.1 Benchmarks (M1 Mac):**
- Upsert: ~500 documents/second
- Query: <50ms for 10 results
- Metadata filtering: <100ms
- Collection creation: <10ms

**Resource usage:**
- Memory: ~200-500MB
- Disk: ~2x embedding size
- CPU: Low (HTTP client mode)

## Future Considerations

**v0.2:**
- Evaluate performance with larger datasets
- Consider connection pooling
- Benchmark against alternatives

**v0.3:**
- Re-evaluate if >10k documents common
- Consider migration to Qdrant
- Add performance monitoring

**v1.0:**
- Support multiple vector database backends
- Plugin architecture for swappable stores
- Migration tools between databases

---

**Last Updated:** 2025-11-13

**Supersedes:** None

**Superseded By:** None (subject to re-evaluation in v0.3)
