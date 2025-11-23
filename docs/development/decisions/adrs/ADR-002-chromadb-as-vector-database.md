# ADR-002: ChromaDB as Vector Database

**Status:** Accepted

---

## Context and Problem Statement

ragged requires a vector database to store and retrieve document embeddings for RAG (Retrieval-Augmented Generation). The choice of vector database affects performance, deployment complexity, scalability, and alignment with project goals.

**Key Requirements**:
- Local-first operation (no mandatory cloud dependencies)
- Support for multiple embedding dimensions (text: 384-dim, vision: 128-dim)
- Fast similarity search with metadata filtering
- Simple deployment (no complex infrastructure)
- Open-source with permissive licensing
- Python-native integration
- Ability to handle both small (MB) and large (GB) collections

**Constraints**:
- Must work on consumer hardware (laptops, desktops)
- No external services or API keys required for core functionality
- GPL-3.0 compatible licensing
- Minimal operational overhead for end users

## Prior Art

**Influences from Other Projects**:
- ✅ Reviewed vector database landscape (ChromaDB, Qdrant, Weaviate, Pinecone, Milvus)
- Standard RAG systems use various backends depending on scale and deployment model

**External Inspirations**:
- Pinecone - Cloud-first, managed service model
- Qdrant - Rust-based, performance-focused
- Weaviate - GraphQL interface, schema-first
- ChromaDB - Python-native, local-first

**Key Differences**: ragged prioritises local-first operation over scale-out capabilities.

## Decision Drivers

1. **Privacy-First Philosophy**: Must work entirely locally without cloud dependencies
2. **Simplicity**: End users should not need to operate complex database infrastructure
3. **Python Integration**: Seamless integration with Python data science ecosystem
4. **Flexibility**: Support for different embedding dimensions and metadata schemas
5. **Performance**: Fast enough for interactive use on consumer hardware
6. **License Compatibility**: Must be GPL-3.0 compatible

## Considered Options

### Option 1: ChromaDB

**Description**: Python-native embedding database with local-first design, persistent storage, and optional client-server mode.

**Pros**:
- ✅ **Local-first by default** - works entirely offline
- ✅ **Python-native** - seamless integration, no language barriers
- ✅ **Simple deployment** - pip install, no separate server required
- ✅ **Flexible collections** - different embedding dimensions per collection
- ✅ **Good metadata filtering** - WHERE clauses for filtering
- ✅ **Apache 2.0 license** - GPL-3.0 compatible
- ✅ **Active development** - strong community, regular updates
- ✅ **Docker support** - optional client-server mode for scaling

**Cons**:
- ❌ Slower than Rust-based alternatives (Qdrant) at massive scale
- ❌ Less mature than enterprise solutions (Pinecone, Weaviate)
- ❌ Limited replication/clustering (v0.4.x)

**Implementation Effort**: Low

### Option 2: Qdrant

**Description**: Rust-based vector database with strong performance characteristics and gRPC API.

**Pros**:
- ✅ **High performance** - Rust implementation, optimised for speed
- ✅ **Rich filtering** - advanced query capabilities
- ✅ **Clustering support** - production-ready scaling
- ✅ **Good documentation** - comprehensive guides

**Cons**:
- ❌ **Separate server required** - users must run Qdrant server
- ❌ **Operational complexity** - more moving parts
- ❌ **gRPC dependency** - additional network layer
- ❌ **Not Python-native** - language barrier for debugging

**Implementation Effort**: Medium

### Option 3: Weaviate

**Description**: GraphQL-based vector database with schema-first design and advanced features.

**Pros**:
- ✅ **Feature-rich** - built-in ML models, hybrid search
- ✅ **GraphQL API** - flexible query interface
- ✅ **Enterprise-ready** - production deployments at scale

**Cons**:
- ❌ **Schema-first design** - requires upfront schema definition
- ❌ **Operational complexity** - complex deployment
- ❌ **Resource-intensive** - higher memory/CPU requirements
- ❌ **Go-based** - not Python-native

**Implementation Effort**: High

### Option 4: Pinecone

**Description**: Managed cloud vector database service with excellent performance.

**Pros**:
- ✅ **Best-in-class performance** - highly optimised
- ✅ **Zero operational overhead** - fully managed
- ✅ **Excellent developer experience** - simple API

**Cons**:
- ❌ **Cloud-only** - violates privacy-first principle
- ❌ **Requires API keys** - not self-contained
- ❌ **Vendor lock-in** - proprietary service
- ❌ **Cost** - usage-based pricing

**Implementation Effort**: Low (for integration) but incompatible with project goals

### Option 5: FAISS + Custom Persistence

**Description**: Use Facebook's FAISS library with custom persistence layer.

**Pros**:
- ✅ **Excellent performance** - heavily optimised C++
- ✅ **Flexible** - complete control over implementation
- ✅ **Local-first** - no server required

**Cons**:
- ❌ **No built-in persistence** - must implement from scratch
- ❌ **No metadata filtering** - vectors only, no associated data
- ❌ **High implementation effort** - weeks of development
- ❌ **Maintenance burden** - ongoing support required

**Implementation Effort**: Very High

## Decision Outcome

**Chosen Option**: "ChromaDB (Option 1)"

**Justification**:

ChromaDB aligns perfectly with ragged's core principles:

1. **Privacy-First**: Works entirely locally by default. Users can run ragged without any external services or API keys. Data never leaves the user's machine unless explicitly configured.

2. **Simplicity**: Single `pip install chromadb` - no separate server to manage. Users don't need to understand database operations, Docker networking, or server administration.

3. **Python-Native**: Seamless integration with ragged's Python codebase. Debugging, profiling, and development are straightforward without crossing language boundaries.

4. **Flexibility**: Supports ragged's dual embedding architecture (384-dim text, 128-dim vision) through separate collections. Metadata filtering enables hybrid retrieval patterns.

5. **Appropriate Performance**: Fast enough for interactive use on consumer hardware (100-1000 document collections respond in milliseconds). Performance bottlenecks are in LLM generation, not retrieval.

6. **Optional Scaling**: For users who outgrow embedded mode, ChromaDB supports client-server deployment via Docker without code changes.

**Trade-Off Accepted**: We accept slightly lower performance than Qdrant at massive scale (10M+ vectors) in exchange for simplicity and local-first operation. ragged targets individual users with document collections in the 100-10,000 range, where ChromaDB performs excellently.

**Consequences**:
- **Positive**:
  - Zero configuration vector database for end users
  - Complete data privacy - no external dependencies
  - Simple debugging and development workflow
  - GPL-3.0 compatible licensing (Apache 2.0)
  - Can evolve to client-server mode without code changes
  - Active community and regular updates
  - Native Python means easy extension and customisation

- **Negative**:
  - Performance ceiling lower than Qdrant/Weaviate at massive scale
  - Persistence layer still maturing (improved in 0.4.x → 0.5.x)
  - Limited built-in replication (enterprise users may need alternatives)

- **Neutral**:
  - Python implementation means performance tied to Python runtime
  - Collection-based architecture requires explicit management
  - Docker Compose includes separate ChromaDB service (optional overhead)

## Implementation Notes

**When**: Implemented in v0.1 (initial release)

**Dependencies**:
- `chromadb>=0.4.0` in pyproject.toml
- Docker Compose configuration for optional client-server mode
- Persistence directory: `~/.ragged/storage` (default)

**Migration Strategy**: Not applicable - initial implementation.

**Evolution Path**:
- v0.1-0.4: Embedded ChromaDB (single process)
- v0.5+: Added Docker Compose support for client-server mode
- Future: Consider pgvector plugin if PostgreSQL integration needed

## Validation

**How will we know this was the right decision?**
- Users can run ragged without understanding vector databases ✅
- Performance remains acceptable for target use cases (100-10,000 docs) ✅
- No user complaints about privacy/cloud dependencies ✅
- Development velocity remains high (Python-native benefits) ✅
- Can support advanced users who need client-server mode ✅

**Review Date**: After v1.0 (if usage patterns show need for different backend)

**Potential Future Changes**:
- If 80%+ of users need >1M document collections, reconsider Qdrant
- If enterprise users demand replication, provide Qdrant as alternative backend
- If performance becomes bottleneck, benchmark against newer ChromaDB versions first

## References

- [ChromaDB Documentation](https://docs.trychroma.com/)
- [ChromaDB GitHub](https://github.com/chroma-core/chroma)
- Storage Implementation
- [ADR-003: Privacy-First Design](./ADR-003-privacy-first-local-only-design.md)
- [ADR-005: Dual Embedding Storage](./ADR-005-dual-embedding-storage-architecture.md)

---

## Research Notes

**Sources Consulted**:
- ChromaDB, Qdrant, Weaviate, Pinecone, Milvus documentation
- Vector database comparison benchmarks (ANN Benchmarks)
- ragged storage layer implementation (`src/storage/`)

**Key Insights**:
- Local-first significantly narrows viable options (excludes Pinecone, cloud-only solutions)
- Python-native reduces friction for contributors and debugging
- Operational simplicity more valuable than raw performance for target users
- Collection-based architecture maps well to ragged's use cases (separate text/vision embeddings)

## Alternatives Not Considered

- **SQLite with vector extensions** - too limited for similarity search at scale
- **Redis with vector module** - requires separate Redis server, similar complexity to Qdrant
- **Elasticsearch with vector fields** - massive operational overhead for RAG use case
- **Custom implementation** - reinventing the wheel, high maintenance burden

---

**Supersedes**: N/A

**Superseded By**: N/A
