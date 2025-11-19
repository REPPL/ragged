# Cold Start Holistic Optimisation

**Phase**: 2 | **Effort**: 3-4h | **Priority**: MUST-HAVE

**Target**: Complete cold start <1s (currently ~2-3s)

**Optimisations**:
1. ChromaDB connection pooling
2. Config caching (Settings already singleton ✅)
3. Lazy initialisation audit
4. Parallel component init

**Implementation**:
```python
# Connection pool for ChromaDB
class ChromaDBPool:
    _pool = []
    def get_connection(self):
        # Reuse existing or create new
        # Keep-alive for reuse

# Parallel init
async def init_all_components():
    await asyncio.gather(
        init_embedder(),
        init_vector_store(),
        init_retriever(),
    )
```

**Success**: Cold start <1s

**Timeline**: 3-4h

---

**Status**: ✅ IMPLEMENTED (commit 06e9d8b)
