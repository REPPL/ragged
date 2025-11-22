# ADR-0015: VectorStore Abstraction Layer

**Date:** 2025-11-16
**Status:** Accepted (Phase 1-2 completed in v0.3.6)
**Deciders:** ragged development team
**Tags:** architecture, storage, plugins, v0.3.6, v0.4

---

## Context

ragged currently tightly couples to ChromaDB as its vector storage backend. As the project evolves towards v0.4 (Plugin Architecture), we need to support:

1. **Multiple vector store backends** (ChromaDB, LEANN, future options)
2. **User choice** based on storage vs performance trade-offs
3. **Migration paths** between backends
4. **Pluggable architecture** for extensibility

The analysis of LEANN integration (see [LEANN Integration Analysis](../2025-11-16-leann-integration-analysis.md)) highlighted the need for a VectorStore abstraction layer to enable optional backends without breaking existing users.

### Current State

- Direct ChromaDB usage throughout codebase
- No abstraction layer
- Difficult to add alternative backends
- Hard-coded ChromaDB-specific logic

### Target State (v0.4)

- Clean VectorStore interface
- ChromaDB and LEANN implementations
- Easy to add future backends
- Migration tools between backends

---

## Decision

We will implement a **VectorStore abstraction layer** that provides a unified interface for all vector storage operations, with backend-specific implementations for ChromaDB, LEANN, and future vector databases.

### Core Interface

```python
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

@dataclass
class VectorStoreDocument:
    """Unified document representation across backends."""
    id: str
    content: str
    embedding: Optional[List[float]] = None
    metadata: Dict[str, Any] = None

@dataclass
class VectorStoreQueryResult:
    """Unified query result representation."""
    documents: List[VectorStoreDocument]
    distances: List[float]
    metadatas: List[Dict[str, Any]]

class VectorStore(ABC):
    """Abstract base class for vector store backends."""

    @abstractmethod
    def add(
        self,
        documents: List[VectorStoreDocument],
        collection_name: str = "default"
    ) -> List[str]:
        """Add documents to the vector store.

        Args:
            documents: List of documents to add
            collection_name: Name of the collection

        Returns:
            List of document IDs
        """
        pass

    @abstractmethod
    def search(
        self,
        query_embedding: List[float],
        n_results: int = 10,
        collection_name: str = "default",
        filter_dict: Optional[Dict[str, Any]] = None
    ) -> VectorStoreQueryResult:
        """Search for similar documents.

        Args:
            query_embedding: Query vector
            n_results: Number of results to return
            collection_name: Collection to search
            filter_dict: Metadata filters

        Returns:
            Query results
        """
        pass

    @abstractmethod
    def delete(
        self,
        document_ids: List[str],
        collection_name: str = "default"
    ) -> None:
        """Delete documents by ID.

        Args:
            document_ids: IDs of documents to delete
            collection_name: Collection to delete from
        """
        pass

    @abstractmethod
    def update(
        self,
        documents: List[VectorStoreDocument],
        collection_name: str = "default"
    ) -> None:
        """Update existing documents.

        Args:
            documents: Documents to update
            collection_name: Collection to update
        """
        pass

    @abstractmethod
    def get_collection_stats(
        self,
        collection_name: str = "default"
    ) -> Dict[str, Any]:
        """Get statistics about a collection.

        Args:
            collection_name: Collection name

        Returns:
            Statistics dict (count, size, etc.)
        """
        pass

    @abstractmethod
    def list_collections(self) -> List[str]:
        """List all collection names."""
        pass

    @abstractmethod
    def create_collection(
        self,
        collection_name: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Create a new collection.

        Args:
            collection_name: Name for the new collection
            metadata: Optional collection metadata
        """
        pass

    @abstractmethod
    def delete_collection(
        self,
        collection_name: str
    ) -> None:
        """Delete an entire collection.

        Args:
            collection_name: Collection to delete
        """
        pass

    @abstractmethod
    def close(self) -> None:
        """Close connections and cleanup resources."""
        pass
```

### Backend Implementations

**ChromaDB Backend:**
```python
from ragged.vectorstore import VectorStore, VectorStoreDocument, VectorStoreQueryResult
import chromadb

class ChromaDBStore(VectorStore):
    """ChromaDB implementation of VectorStore interface."""

    def __init__(self, persist_directory: str = "./chroma_data"):
        self.client = chromadb.PersistentClient(path=persist_directory)
        self._collections = {}

    def add(self, documents: List[VectorStoreDocument], collection_name: str = "default") -> List[str]:
        collection = self._get_collection(collection_name)
        # Implementation details...
        return document_ids

    def search(self, query_embedding: List[float], n_results: int = 10, ...) -> VectorStoreQueryResult:
        collection = self._get_collection(collection_name)
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            where=filter_dict
        )
        # Convert ChromaDB format to unified format
        return VectorStoreQueryResult(...)

    # ... other methods
```

**LEANN Backend:**
```python
from ragged.vectorstore import VectorStore, VectorStoreDocument, VectorStoreQueryResult
from leann import LeannBuilder, LeannSearcher

class LeannVectorStore(VectorStore):
    """LEANN implementation of VectorStore interface."""

    def __init__(self, persist_directory: str = "./leann_data"):
        self.persist_directory = persist_directory
        self._collections = {}

    def add(self, documents: List[VectorStoreDocument], collection_name: str = "default") -> List[str]:
        builder = self._get_builder(collection_name)
        # Implementation details using LEANN's graph-based approach...
        return document_ids

    def search(self, query_embedding: List[float], n_results: int = 10, ...) -> VectorStoreQueryResult:
        searcher = self._get_searcher(collection_name)
        results = searcher.search(...)
        # Convert LEANN format to unified format
        return VectorStoreQueryResult(...)

    # ... other methods
```

### Factory Pattern

```python
from typing import Literal
from ragged.vectorstore import VectorStore
from ragged.vectorstore.chromadb import ChromaDBStore
from ragged.vectorstore.leann import LeannVectorStore

BackendType = Literal["chromadb", "leann"]

def create_vectorstore(
    backend: BackendType = "chromadb",
    **backend_kwargs
) -> VectorStore:
    """Factory function to create vector store instances.

    Args:
        backend: Backend type to create
        **backend_kwargs: Backend-specific configuration

    Returns:
        VectorStore instance

    Raises:
        ValueError: If backend not supported or not installed
    """
    if backend == "chromadb":
        return ChromaDBStore(**backend_kwargs)
    elif backend == "leann":
        try:
            return LeannVectorStore(**backend_kwargs)
        except ImportError:
            raise ValueError(
                "LEANN backend not installed. "
                "Install with: pip install ragged[leann]"
            )
    else:
        raise ValueError(f"Unknown backend: {backend}")
```

### Configuration

**pyproject.toml:**
```toml
[project.optional-dependencies]
leann = [
    "leann>=1.0.0",
    "sentence-transformers>=3.0.0"
]
```

**config.yaml:**
```yaml
vectorstore:
  backend: "chromadb"  # or "leann"
  chromadb:
    persist_directory: "./data/chroma"
  leann:
    persist_directory: "./data/leann"
    graph_degree: 32
    search_complexity: 100
```

---

## Consequences

### Positive

1. **Pluggable Architecture** ✅
   - Easy to add new backends (Pinecone, Weaviate, etc.)
   - Users can choose based on needs
   - Future-proof design

2. **Clean Separation** ✅
   - Backend logic isolated in implementations
   - Easy to test each backend independently
   - Reduces coupling throughout codebase

3. **Migration Support** ✅
   - Unified interface enables migration tools
   - Can run both backends simultaneously for testing
   - Gradual migration paths

4. **Optional Dependencies** ✅
   - LEANN as pip extra keeps core lightweight
   - Simple install for beginners (ChromaDB only)
   - Advanced users can opt-in to LEANN

### Negative

1. **Maintenance Overhead** ⚠️
   - Must maintain multiple backend implementations
   - Testing surface doubles (or more)
   - Bug fixes may need backend-specific handling

2. **Abstraction Complexity** ⚠️
   - Lowest common denominator interface
   - May hide backend-specific optimisations
   - Performance tuning more complex

3. **Migration Risks** ⚠️
   - Users may face data migration challenges
   - Backend-specific features may not transfer
   - Documentation burden for migration paths

### Mitigation Strategies

1. **Shared Test Suite**
   - Parameterised tests run against all backends
   - Ensures consistent behaviour
   - Catches backend-specific regressions

2. **Backend-Specific Extensions**
   - Allow backends to expose additional features
   - Document trade-offs clearly
   - Provide migration warnings

3. **Comprehensive Documentation**
   - Backend comparison matrix
   - Migration guides for each transition
   - Performance benchmarks

---

## Implementation Notes (v0.3.6)

**Release Date:** 2025-11-22

### What Was Implemented

Phase 1 and Phase 2 were completed in v0.3.6 with the following key deliverables:

**1. Abstract Interface** (`src/storage/vectorstore_interface.py`)
- VectorStore ABC with 9 abstract methods
- Uses `numpy.ndarray` for embeddings (performance optimisation)
- Returns Dict[str, Any] instead of custom dataclasses (backward compatibility)
- Methods: health_check, add, query, delete, update_metadata, get_documents_by_metadata, list, count, clear, get_collection_info

**2. ChromaDB Implementation** (`src/storage/chromadb_store.py`)
- ChromaDBStore(VectorStore) implements full interface
- Preserved all existing functionality:
  - Circuit breaker protection (_chroma_circuit_breaker)
  - Automatic retry with exponential backoff (@with_retry decorator)
  - Metadata serialization for complex types
- Zero behavioral changes from original implementation
- All 14 storage tests passing

**3. Factory Function** (`src/storage/vectorstore_factory.py`)
- get_vectorstore(backend, collection_name, host, port) factory
- Supports backend selection: 'chromadb', 'leann', 'qdrant', 'weaviate'
- Returns NotImplementedError for future backends with roadmap references
- Defaults to 'chromadb' if not specified

**4. Backward Compatibility** (`src/storage/vector_store.py`)
- Original module now re-exports: `from chromadb_store import ChromaDBStore as VectorStore`
- 100% backward compatible - all existing imports work unchanged
- All modules using VectorStore continue working without modification

**5. Package Exports** (`src/storage/__init__.py`)
- Exports VectorStoreInterface (for type hints)
- Exports VectorStore (backward compatible alias)
- Exports get_vectorstore (recommended for new code)
- Exports ChromaDBStore (specific implementation)

### Key Differences from Original Proposal

1. **No Custom Dataclasses:** Kept Dict return types instead of VectorStoreDocument/VectorStoreQueryResult for backward compatibility
2. **Numpy Arrays:** Used np.ndarray for embeddings instead of List[float] for better performance
3. **Additional Methods:** Added list(), get_documents_by_metadata(), update_metadata() based on actual usage patterns
4. **Simpler Factory:** Function-based factory instead of class-based for ease of use
5. **Re-export Pattern:** Used re-export for backward compatibility instead of direct refactoring

### Testing

- All 14 storage tests passing
- Backward compatibility verified via programmatic import checks
- Integration modules (ingestion, retrieval) continue working unchanged

---

## Implementation Plan

### Phase 1: Interface Design (v0.3.6) ✅ **COMPLETED**
**Effort: 4-6 hours (Actual: 4 hours)**

- [x] Finalise VectorStore interface
- [x] ~~Define VectorStoreDocument and VectorStoreQueryResult~~ (deferred - used simpler Dict returns for backward compatibility)
- [x] Create abstract base class (`src/storage/vectorstore_interface.py`)
- [x] Document interface contracts

**Completed:** 2025-11-22

### Phase 2: ChromaDB Refactor (v0.3.6) ✅ **COMPLETED**
**Effort: 4-6 hours (Actual: 5 hours)**

- [x] Implement ChromaDBStore class (`src/storage/chromadb_store.py`)
- [x] Extract all ChromaDB logic to ChromaDBStore
- [x] Update ragged core to use VectorStore interface via re-export
- [x] Ensure all existing tests pass (14/14 storage tests passing)
- [x] Create factory function (`src/storage/vectorstore_factory.py`)

**Completed:** 2025-11-22

### Phase 3: LEANN Implementation (v0.4)
**Effort: 12-16 hours**

- [ ] Implement LeannVectorStore class
- [ ] Handle embedding format conversions
- [ ] Implement metadata mapping
- [ ] Create LEANN-specific tests

### Phase 4: Factory & Configuration (v0.4)
**Effort: 4-6 hours**

- [ ] Implement create_vectorstore factory
- [ ] Add backend selection to CLI: `--backend`
- [ ] Update configuration system
- [ ] Add optional dependency to pyproject.toml

### Phase 5: Migration Tools (v0.4)
**Effort: 8-12 hours**

- [ ] Implement migration command: `ragged migrate chromadb-to-leann`
- [ ] Handle collection-level migration
- [ ] Preserve metadata during migration
- [ ] Add progress reporting

### Phase 6: Testing & Documentation (v0.4)
**Effort: 6-8 hours**

- [ ] Parameterised integration tests
- [ ] Backend comparison benchmarks
- [ ] Migration documentation
- [ ] Platform-specific installation guides

---

## Alternatives Considered

### Alternative 1: Keep ChromaDB-Only
**Rejected:** Doesn't address storage scaling concerns, limits user choice

### Alternative 2: LEANN-Only (Replace ChromaDB)
**Rejected:** Breaking change, removes simpler option for beginners, too risky

### Alternative 3: Adapter Pattern (Keep Direct ChromaDB Usage)
**Rejected:** Only wraps one backend, doesn't enable true pluggability

### Alternative 4: Dynamic Backend Loading
**Rejected:** Overly complex for current needs, harder to test and maintain

---

## Related Decisions

- [ADR-0006: Docker for Development](./0006-docker-for-development.md) - Deployment architecture
- [ADR-0010: Click and Rich for CLI](./0010-click-rich-for-cli.md) - CLI architecture
- [LEANN Integration Analysis](../2025-11-16-leann-integration-analysis.md) - Context for this decision

---

## References

- [Martin Fowler: Repository Pattern](https://martinfowler.com/eaaCatalog/repository.html)
- [Python ABC Documentation](https://docs.python.org/3/library/abc.html)
- [ChromaDB Documentation](https://docs.trychroma.com/)
- [LEANN GitHub](https://github.com/yichuan-w/LEANN)

---

**Last Updated:** 2025-11-22
**Next Review:** v0.4.0 (LEANN implementation)

---

## Related Documentation

- [ChromaDB Storage (ADR-0003)](./0003-chromadb-for-vector-storage.md) - Initial implementation
- [VectorStore Refactoring (v0.4.2)](../../roadmap/version/v0.4/v0.4.2.md) - Abstraction implementation
- [Storage Architecture](../../planning/architecture/) - Vector storage design
- [v0.4.2 Implementation](../../implementation/version/v0.4/v0.4.2/) - What was built

---
