# Multi-Tier Caching Strategy

**Phase**: 3 | **Effort**: 3-4h | **Priority**: MUST-HAVE

**Current**: Single-tier query cache (exists ✅)

**Enhancement**: Three-tier caching

**Tiers**:
- **L1**: Query embedding cache (fast, small, in-memory)
- **L2**: Document embedding cache (medium, disk-backed)
- **L3**: Retrieved results cache (comprehensive, existing QueryCache)

**Implementation**:
```python
class MultiTierCache:
    def __init__(self):
        self.l1 = LRUCache(maxsize=1000)      # Query embeddings
        self.l2 = DiskCache(maxsize_mb=500)   # Doc embeddings
        self.l3 = QueryCache(maxsize=10000)   # Results (existing)

    def get_query_embedding(self, query):
        # Check L1 first, fallback to compute
        pass

    def get_result(self, query, params):
        # Check L3, recompute if miss
        pass
```

**Success**: 30-50x improvement for common queries

**Timeline**: 3-4h
