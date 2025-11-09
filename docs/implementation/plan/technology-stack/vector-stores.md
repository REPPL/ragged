# Vector Stores

**Status**: 🚧 Coming Soon
**Last Updated**: 2025-11-09

## Overview

This document covers the evaluation and selection of vector database solutions for ragged's semantic search capabilities.

---

## Coming Soon

This document will cover:

### Vector Store Requirements

#### Functional Requirements
- **Similarity Search**: Efficient k-NN search
- **Filtering**: Metadata-based filtering
- **CRUD Operations**: Add, update, delete vectors
- **Persistence**: Durable storage
- **Collections**: Namespace isolation

#### Non-Functional Requirements
- **Performance**: Sub-second query latency
- **Scalability**: Handle 10k-1M+ documents
- **Resource Usage**: Reasonable memory/disk usage
- **Privacy**: Local-first, no cloud dependencies
- **Ease of Use**: Simple API and setup

### Candidate Solutions

#### ChromaDB (Leading Candidate)
**Pros**:
- ✅ Lightweight, embedded database
- ✅ Simple Python API
- ✅ Built for RAG use cases
- ✅ Active development
- ✅ Good documentation
- ✅ Metadata filtering
- ✅ Collection support

**Cons**:
- ⚠️ Relatively new project
- ⚠️ Performance at very large scale TBD

**Use Case**: Default for v0.1-v1.0

#### Qdrant
**Pros**:
- ✅ Production-grade performance
- ✅ Rich filtering capabilities
- ✅ Excellent documentation
- ✅ Both embedded and server modes
- ✅ Advanced indexing (HNSW)

**Cons**:
- ⚠️ Heavier weight than ChromaDB
- ⚠️ More complex setup

**Use Case**: Alternative option, production deployments

#### FAISS (Facebook AI Similarity Search)
**Pros**:
- ✅ Extremely fast
- ✅ Battle-tested
- ✅ GPU support

**Cons**:
- ❌ Lower-level API
- ❌ No metadata filtering
- ❌ No persistence layer
- ❌ Requires wrapper code

**Use Case**: Considered but not selected

#### Milvus
**Pros**:
- ✅ Production-grade
- ✅ Highly scalable

**Cons**:
- ❌ Complex deployment
- ❌ Overkill for local use
- ❌ Resource intensive

**Use Case**: Not suitable for local-first

### Implementation Strategy

#### v0.1: ChromaDB Default
```python
import chromadb

# Create client
client = chromadb.PersistentClient(path="./data/chroma")

# Create collection
collection = client.create_collection(
    name="documents",
    metadata={"description": "Document chunks"}
)

# Add vectors
collection.add(
    embeddings=embeddings,
    documents=texts,
    metadatas=metadata,
    ids=ids
)

# Query
results = collection.query(
    query_embeddings=query_embedding,
    n_results=10,
    where={"source": "paper.pdf"}
)
```

#### Abstraction Layer
```python
class VectorStore(ABC):
    @abstractmethod
    def add(vectors, metadata, ids)

    @abstractmethod
    def search(query_vector, k, filters) -> Results

    @abstractmethod
    def delete(ids)

    @abstractmethod
    def update(ids, vectors, metadata)

class ChromaDBStore(VectorStore):
    # Implementation

class QdrantStore(VectorStore):
    # Alternative implementation
```

### Indexing Strategies

#### HNSW (Hierarchical Navigable Small World)
- Default for both ChromaDB and Qdrant
- Excellent recall/speed trade-off
- Configurable parameters (M, ef_construction)

#### IVF (Inverted File Index)
- Better for very large datasets
- Faster search, slightly lower recall
- Available in Qdrant

#### Flat Index
- Exact search, no approximation
- Suitable for small datasets (<10k vectors)
- Baseline for quality comparison

### Performance Optimisation

#### Index Tuning
- **HNSW M parameter**: Graph connectivity
- **ef_construction**: Build-time accuracy
- **ef_search**: Query-time accuracy
- **Batch size**: Insertion throughput

#### Query Optimisation
- **Filter early**: Apply metadata filters first
- **Reranking**: Two-stage retrieval
- **Caching**: Common query results
- **Prewarming**: Load index into memory

#### Storage Optimisation
- **Compression**: Vector quantisation
- **Pruning**: Remove old/irrelevant data
- **Partitioning**: Split large collections

### Evaluation Criteria

#### Performance Metrics
- **Query Latency**: p50, p95, p99
- **Throughput**: Queries per second
- **Indexing Speed**: Vectors per second
- **Memory Usage**: RAM requirements
- **Disk Usage**: Storage requirements

#### Quality Metrics
- **Recall@k**: Percentage of true k-NN found
- **Precision@k**: Relevance of results
- **NDCG**: Ranking quality

### Version Roadmap

#### v0.1: ChromaDB Foundation
- Basic CRUD operations
- Single collection
- Simple metadata filtering
- Persistent storage

#### v0.2: Enhanced Querying
- Multiple collections
- Advanced filtering
- Performance tuning

#### v0.3: Optimisation
- Index tuning
- Caching layer
- Batch operations

#### v0.4: Alternative Backends
- Qdrant support
- Pluggable vector stores
- Migration tools

#### v1.0: Production Ready
- Optimal configuration
- Comprehensive benchmarks
- Migration utilities

---

## Related Documentation

- **[Embeddings](embeddings.md)** - Embedding models
- **[Storage Model](../architecture/storage-model.md)** - Overall storage architecture
- **[Hardware Optimisation](../core-concepts/hardware-optimisation.md)** - Performance tuning
- **[Technology Comparisons](../../../research/background/technology-comparisons.md)** - Detailed comparisons

---

*This document will be expanded with benchmarks and specific configuration examples*
