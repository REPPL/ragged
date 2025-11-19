# Performance Optimisations (v0.2.7)

This document details the performance optimisations planned for v0.2.7.

**Total Estimated Time**: 37 hours

**Related Documentation:** [Main v0.2.7 Roadmap](../README.md)

---

## Part 2: Performance Optimizations (37 hours)

### PERF-001: Embedding Caching

**Priority**: High
**Estimated Time**: 5 hours
**Impact**: 50-90% faster repeat queries

#### Current State
Every query re-embeds the same text, wasting computation.

#### Solution

**LRU Cache for Query Embeddings**:
```python
# src/embeddings/cache.py (NEW FILE)
"""Embedding caching system."""
from functools import lru_cache
import hashlib
import pickle
from pathlib import Path
from typing import Optional
import numpy as np

class EmbeddingCache:
    """
    Persistent cache for embeddings.

    Stores embeddings on disk to avoid re-computation across sessions.
    """

    def __init__(self, cache_dir: Path = Path("data/cache/embeddings")):
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def get_cache_key(self, text: str, model: str) -> str:
        """Generate cache key for text + model combination."""
        content = f"{model}:{text}"
        return hashlib.sha256(content.encode()).hexdigest()

    def get(self, text: str, model: str) -> Optional[np.ndarray]:
        """Get cached embedding if exists."""
        key = self.get_cache_key(text, model)
        cache_file = self.cache_dir / f"{key}.pkl"

        if cache_file.exists():
            with open(cache_file, 'rb') as f:
                return pickle.load(f)

        return None

    def set(self, text: str, model: str, embedding: np.ndarray):
        """Cache an embedding."""
        key = self.get_cache_key(text, model)
        cache_file = self.cache_dir / f"{key}.pkl"

        with open(cache_file, 'wb') as f:
            pickle.dump(embedding, f)

    def clear(self):
        """Clear all cached embeddings."""
        for cache_file in self.cache_dir.glob("*.pkl"):
            cache_file.unlink()

        logger.info("Cleared embedding cache")
```

**Integration into Embedders**:
```python
# src/embeddings/base.py
from src.embeddings.cache import EmbeddingCache

class BaseEmbedder:
    def __init__(self, use_cache: bool = True):
        self.use_cache = use_cache
        if use_cache:
            self.cache = EmbeddingCache()

    def embed(self, text: str) -> np.ndarray:
        """Embed text with caching."""
        # Check cache first
        if self.use_cache:
            cached = self.cache.get(text, self.model_name)
            if cached is not None:
                logger.debug(f"Cache hit for text: {text[:50]}...")
                return cached

        # Compute embedding
        embedding = self._embed_internal(text)

        # Store in cache
        if self.use_cache:
            self.cache.set(text, self.model_name, embedding)

        return embedding
```

#### Testing Requirements
- [ ] Test cache hit/miss behaviour
- [ ] Test cache persistence across sessions
- [ ] Benchmark query speed with/without cache
- [ ] Test cache clearing

#### Files to Create
- `src/embeddings/cache.py` (~150 lines)
- `tests/embeddings/test_cache.py` (~100 lines)

#### Files to Modify
- `src/embeddings/base.py`
- `src/embeddings/sentence_transformer.py`
- `src/embeddings/ollama_embedder.py`

#### Acceptance Criteria
- ✅ 50-90% faster repeat queries
- ✅ Cache persists across sessions
- ✅ Cache can be cleared via CLI

---

### PERF-002-006: Additional Performance Improvements

**PERF-002: Async Document Processing** (12 hours)
- Parallel processing of multiple documents
- 2-4x faster batch ingestion
- Async embedding generation

**PERF-003: Lazy Model Loading** (6 hours)
- Unload models after inactivity timeout
- Reduced memory footprint (400MB → 100MB idle)
- Automatic reload on next use

**PERF-004: BM25 Index Persistence** (3 hours)
- Save/load BM25 index to disk
- Instant startup vs 10-30s rebuild
- Incremental index updates

**PERF-005: Chunking Optimisation** (5 hours)
- Batch token counting
- Estimate-then-verify approach
- 2x faster chunking

**PERF-006: Vector Store Query Optimisation** (6 hours)
- Query batching where possible
- Connection pooling for ChromaDB
- 30% faster multi-query scenarios


---

## Related Documentation

- [Main v0.2.7 Roadmap](../README.md)
- [UX Improvements](./ux-improvements.md)
- [CLI Enhancements](./cli-enhancements.md)
- [Configuration Management](./configuration-management.md)

---

**License:** GPL-3.0
