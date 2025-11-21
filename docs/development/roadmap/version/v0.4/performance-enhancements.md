# v0.4.x Performance Optimization Enhancements

**Purpose**: Optional performance enhancements beyond v0.4.4 performance baseline

**Status**: Enhancement opportunities for consideration

**Audience**: Performance engineers, developers, power users

---

## Overview

This document identifies **optional performance optimizations** for v0.4.x beyond the performance baseline established in v0.4.4.

**Baseline Performance** (v0.4.4 targets):
- ✅ Memory operations: <100ms
- ✅ Graph queries: <300ms
- ✅ End-to-end queries: <2s
- ✅ No memory leaks over 1000 operations
- ✅ Database queries optimised (indexes, prepared statements)

**Enhancement Philosophy**: The baseline provides good performance for most users. These enhancements offer **significant speedups** for power users and large-scale deployments.

---

## Performance Enhancement Categories

### Category 1: Query Performance Optimizations

**Priority**: HIGH (queries are primary user interaction)

**Target Users**: Users with large document collections (10,000+ documents)

---

#### Enhancement 1.1: Query Result Caching

**Current State**: Every query performs fresh vector search

**Enhancement**: Cache frequently-accessed query results

**Benefits**:
- 10-50x speedup for repeated queries
- Reduced load on vector database
- Lower CPU/memory usage

**Implementation** (estimated 8-10 hours):

**Design**:
```python
import hashlib
from typing import Optional, List
from functools import lru_cache
from dataclasses import dataclass
from datetime import datetime, timedelta

@dataclass
class CacheEntry:
    """Cached query result."""
    query_hash: str
    results: List[Dict]
    timestamp: datetime
    persona: str
    hit_count: int = 0

class QueryCache:
    """LRU cache for query results with TTL and persona isolation."""

    def __init__(self, max_size: int = 1000, ttl_seconds: int = 3600):
        """
        Initialize query cache.

        Args:
            max_size: Maximum number of cached queries
            ttl_seconds: Time-to-live for cache entries (default: 1 hour)
        """
        self.max_size = max_size
        self.ttl = timedelta(seconds=ttl_seconds)
        self.cache: Dict[str, CacheEntry] = {}

    def get(self, query: str, persona: str, top_k: int) -> Optional[List[Dict]]:
        """
        Retrieve cached results if available and fresh.

        Args:
            query: User query text
            persona: Active persona name
            top_k: Number of results requested

        Returns:
            Cached results if available, None otherwise
        """
        cache_key = self._compute_cache_key(query, persona, top_k)

        entry = self.cache.get(cache_key)
        if entry is None:
            return None

        # Check if entry expired
        if datetime.now() - entry.timestamp > self.ttl:
            del self.cache[cache_key]
            return None

        # Cache hit
        entry.hit_count += 1
        return entry.results

    def put(self, query: str, persona: str, top_k: int, results: List[Dict]) -> None:
        """
        Store query results in cache.

        Args:
            query: User query text
            persona: Active persona name
            top_k: Number of results
            results: Query results to cache
        """
        cache_key = self._compute_cache_key(query, persona, top_k)

        # Evict oldest entry if cache full
        if len(self.cache) >= self.max_size:
            self._evict_lru()

        self.cache[cache_key] = CacheEntry(
            query_hash=cache_key,
            results=results,
            timestamp=datetime.now(),
            persona=persona
        )

    def invalidate_persona(self, persona: str) -> None:
        """Invalidate all cache entries for a persona (e.g., after ingestion)."""
        keys_to_delete = [
            key for key, entry in self.cache.items()
            if entry.persona == persona
        ]
        for key in keys_to_delete:
            del self.cache[key]

    def _compute_cache_key(self, query: str, persona: str, top_k: int) -> str:
        """Compute deterministic cache key from query parameters."""
        key_data = f"{query}|{persona}|{top_k}"
        return hashlib.sha256(key_data.encode()).hexdigest()

    def _evict_lru(self) -> None:
        """Evict least recently used entry."""
        if not self.cache:
            return

        # Find entry with lowest hit count and oldest timestamp
        lru_key = min(
            self.cache.keys(),
            key=lambda k: (self.cache[k].hit_count, self.cache[k].timestamp)
        )
        del self.cache[lru_key]
```

**Integration**:
```python
# In query pipeline
def query(text: str, persona: str, top_k: int = 10) -> List[Dict]:
    """Query with caching."""
    # Check cache first
    cached_results = query_cache.get(text, persona, top_k)
    if cached_results is not None:
        logger.debug(f"Cache hit for query: {text[:50]}...")
        return cached_results

    # Cache miss - perform actual query
    results = _perform_vector_search(text, persona, top_k)

    # Store in cache
    query_cache.put(text, persona, top_k, results)

    return results

# Invalidate cache after ingestion
def ingest_documents(documents: List[Dict], persona: str):
    """Ingest documents and invalidate query cache."""
    _ingest_to_vectorstore(documents, persona)

    # Cache now stale - invalidate
    query_cache.invalidate_persona(persona)
```

**Configuration** (`~/.ragged/config.yaml`):
```yaml
performance:
  query_cache:
    enabled: true
    max_size: 1000  # Max cached queries
    ttl_seconds: 3600  # 1 hour
```

**CLI Commands**:
```bash
# View cache statistics
ragged performance cache-stats
# Output:
# Query Cache Statistics:
#   Total entries: 247
#   Hit rate: 67.3%
#   Avg query time (cache hit): 12ms
#   Avg query time (cache miss): 340ms
#   Space used: 3.2 MB

# Clear cache
ragged performance clear-cache --confirm
```

**Testing Requirements**:
- Cache hit/miss correctly identified
- Stale entries evicted
- Persona isolation maintained

**Trade-offs**:
- **Pro**: Massive speedup for repeated queries
- **Con**: Memory usage (configurable)
- **Con**: Stale results if documents updated

**Recommendation**: **IMPLEMENT** in v0.4.4 or v0.4.5 (high impact)

---

#### Enhancement 1.2: Embedding Caching

**Current State**: Queries re-embedded every time

**Enhancement**: Cache query embeddings

**Benefits**:
- 5-10x speedup for repeated queries
- Reduced embedding model invocations
- Lower GPU/CPU usage

**Implementation** (estimated 4-5 hours):

**Design**:
```python
class EmbeddingCache:
    """Cache embeddings with LRU eviction."""

    def __init__(self, max_size: int = 10000):
        self.max_size = max_size
        self.cache: Dict[str, np.ndarray] = {}

    def get_embedding(self, text: str, model: str) -> Optional[np.ndarray]:
        """Get cached embedding if available."""
        cache_key = hashlib.sha256(f"{text}|{model}".encode()).hexdigest()
        return self.cache.get(cache_key)

    def put_embedding(self, text: str, model: str, embedding: np.ndarray) -> None:
        """Store embedding in cache."""
        cache_key = hashlib.sha256(f"{text}|{model}".encode()).hexdigest()

        if len(self.cache) >= self.max_size:
            # Evict random entry (simple LRU alternative)
            self.cache.pop(next(iter(self.cache)))

        self.cache[cache_key] = embedding

# Usage
def embed_query(text: str, model: str) -> np.ndarray:
    """Embed query with caching."""
    cached_embedding = embedding_cache.get_embedding(text, model)
    if cached_embedding is not None:
        return cached_embedding

    # Cache miss - compute embedding
    embedding = model.encode(text)
    embedding_cache.put_embedding(text, model, embedding)

    return embedding
```

**Performance Impact**:
- Cache hit: <1ms (array lookup)
- Cache miss: 50-200ms (model inference)
- **Speedup**: 50-200x for cache hits

**Testing Requirements**:
- Embedding correctness (cached == fresh)
- Cache eviction works
- Memory usage reasonable

**Trade-offs**:
- **Pro**: Huge speedup for repeated queries
- **Con**: Memory usage (~1KB per embedding × 10,000 = 10 MB)

**Recommendation**: **IMPLEMENT** in v0.4.4 or v0.4.5 (easy win)

---

#### Enhancement 1.3: Approximate Nearest Neighbor (ANN) Indexes

**Current State**: ChromaDB uses HNSW (already good)

**Enhancement**: Optimise HNSW parameters or add IVF-PQ option

**Benefits**:
- 2-5x speedup for large collections (100,000+ vectors)
- Configurable accuracy/speed trade-off

**Implementation** (estimated 6-8 hours):

**Design**:
```python
# HNSW parameter tuning
chroma_client.create_collection(
    name="documents",
    metadata={
        "hnsw:space": "cosine",
        "hnsw:M": 32,  # Max connections per node (default: 16)
        "hnsw:ef_construction": 200,  # Construction time accuracy (default: 100)
        "hnsw:ef_search": 100  # Query time accuracy (default: 10)
    }
)
```

**Parameter Impact**:

| Parameter | Impact | Trade-off |
|-----------|--------|-----------|
| `M` ↑ | Better recall, slower build | Memory usage ↑ |
| `ef_construction` ↑ | Better recall, slower build | Build time ↑ |
| `ef_search` ↑ | Better recall, slower query | Query time ↑ |

**Tuning Guidelines**:
- **Speed-optimised**: M=16, ef_construction=100, ef_search=10 (default)
- **Balanced**: M=32, ef_construction=200, ef_search=50
- **Accuracy-optimised**: M=64, ef_construction=400, ef_search=200

**Configuration**:
```yaml
vector_store:
  backend: "chromadb"
  chromadb:
    hnsw:
      M: 32
      ef_construction: 200
      ef_search: 100
```

**Testing Requirements**:
- Benchmark different parameter combinations
- Measure recall vs speed trade-off
- Document optimal settings for different collection sizes

**Trade-offs**:
- **Pro**: Significant speedup for large collections
- **Con**: More complex configuration
- **Con**: May reduce recall slightly

**Recommendation**: **IMPLEMENT** in v0.4.4 with sensible defaults

---

### Category 2: Memory System Performance

**Priority**: MEDIUM (memory operations relatively fast already)

**Target Users**: Users with extensive interaction history (10,000+ interactions)

---

#### Enhancement 2.1: Graph Query Optimization

**Current State**: Basic graph queries in Kuzu

**Enhancement**: Query optimization and materialized views

**Benefits**:
- 5-10x speedup for complex graph queries
- Pre-computed aggregations

**Implementation** (estimated 10-12 hours):

**Optimizations**:

**1. Indexes on Frequently Queried Fields**:
```cypher
-- Create index on topic name (frequent lookups)
CREATE INDEX ON Topic(name);

-- Create index on interest level (frequent filtering)
CREATE INDEX ON Topic(interest_level);

-- Create index on timestamps (temporal queries)
CREATE INDEX ON ACCESSED(timestamp);
```

**2. Materialized Views for Common Queries**:
```cypher
-- Pre-compute user's top interests
CREATE TABLE UserTopInterests AS
SELECT u.name as user,
       t.name as topic,
       COUNT(r.frequency) as total_access
FROM User u, Topic t, INTERESTED_IN r
WHERE u.id = r.from AND t.id = r.to
GROUP BY u.name, t.name
ORDER BY total_access DESC
LIMIT 20;

-- Refresh periodically (after new interactions)
REFRESH TABLE UserTopInterests;
```

**3. Query Rewriting**:
```python
# Before: Inefficient query
def get_user_topics_slow(user: str) -> List[str]:
    query = """
    MATCH (u:User {name: $user})-[r:INTERESTED_IN]->(t:Topic)
    RETURN t.name
    ORDER BY r.frequency DESC
    """
    return db.execute(query, {"user": user})

# After: Use materialized view
def get_user_topics_fast(user: str) -> List[str]:
    query = """
    SELECT topic FROM UserTopInterests
    WHERE user = $user
    LIMIT 20
    """
    return db.execute(query, {"user": user})
```

**Testing Requirements**:
- Query correctness (optimised == original)
- Performance benchmarks (measure speedup)
- Refresh strategy (when to update materialized views)

**Trade-offs**:
- **Pro**: Significant speedup for common queries
- **Con**: Extra storage for materialized views
- **Con**: Complexity in refresh logic

**Recommendation**: **IMPLEMENT** in v0.4.7 (temporal memory release)

---

#### Enhancement 2.2: Interaction Batch Processing

**Current State**: Interactions recorded one at a time

**Enhancement**: Batch interaction recording

**Benefits**:
- 10-50x speedup for bulk recording
- Reduced database overhead

**Implementation** (estimated 4-5 hours):

**Design**:
```python
class InteractionBatcher:
    """Batch interaction recording for performance."""

    def __init__(self, batch_size: int = 100, flush_interval: float = 5.0):
        """
        Initialize batcher.

        Args:
            batch_size: Flush batch after this many interactions
            flush_interval: Flush batch after this many seconds
        """
        self.batch_size = batch_size
        self.flush_interval = flush_interval
        self.batch: List[Interaction] = []
        self.last_flush = time.time()

    def record(self, interaction: Interaction) -> None:
        """Add interaction to batch."""
        self.batch.append(interaction)

        # Flush if batch full or interval exceeded
        if len(self.batch) >= self.batch_size or \
           time.time() - self.last_flush > self.flush_interval:
            self.flush()

    def flush(self) -> None:
        """Write batch to database."""
        if not self.batch:
            return

        # Batch insert (much faster than individual inserts)
        conn.executemany(
            "INSERT INTO interactions VALUES (?, ?, ?, ?, ?, ?)",
            [(i.id, i.persona, i.query, i.timestamp, i.docs, i.model)
             for i in self.batch]
        )

        self.batch.clear()
        self.last_flush = time.time()
```

**Configuration**:
```yaml
performance:
  interaction_batching:
    enabled: true
    batch_size: 100
    flush_interval_seconds: 5.0
```

**Testing Requirements**:
- All interactions eventually flushed
- No data loss on crash (flush on shutdown)
- Performance improvement measured

**Trade-offs**:
- **Pro**: Massive speedup for bulk operations
- **Con**: Slight delay before data persisted (up to flush_interval)

**Recommendation**: **IMPLEMENT** in v0.4.3 or v0.4.4

---

### Category 3: Database Optimizations

**Priority**: MEDIUM (baseline already has indexes)

**Target Users**: Users with large datasets (100,000+ documents, 10,000+ interactions)

---

#### Enhancement 3.1: Connection Pooling

**Current State**: New connection for each database operation

**Enhancement**: Reuse connections via pooling

**Benefits**:
- 2-5x speedup for frequent database operations
- Reduced connection overhead

**Implementation** (estimated 3-4 hours):

**Design**:
```python
from contextlib import contextmanager
import sqlite3
from queue import Queue, Empty
from threading import Lock

class ConnectionPool:
    """Thread-safe SQLite connection pool."""

    def __init__(self, database: str, pool_size: int = 5):
        """
        Initialize connection pool.

        Args:
            database: Path to SQLite database
            pool_size: Number of connections in pool
        """
        self.database = database
        self.pool_size = pool_size
        self.pool: Queue = Queue(maxsize=pool_size)
        self.lock = Lock()

        # Pre-create connections
        for _ in range(pool_size):
            conn = sqlite3.connect(database, check_same_thread=False)
            self.pool.put(conn)

    @contextmanager
    def get_connection(self):
        """Get connection from pool (context manager)."""
        conn = None
        try:
            # Get connection (wait up to 5 seconds)
            conn = self.pool.get(timeout=5.0)
            yield conn
        except Empty:
            raise RuntimeError("Connection pool exhausted")
        finally:
            if conn is not None:
                # Return connection to pool
                self.pool.put(conn)

# Usage
pool = ConnectionPool("~/.ragged/memory/interactions/queries.db", pool_size=5)

def record_interaction(interaction: Interaction):
    with pool.get_connection() as conn:
        conn.execute("INSERT INTO interactions VALUES (?, ?, ...)", ...)
        conn.commit()
```

**Testing Requirements**:
- Thread safety (concurrent access safe)
- Connection reuse working
- Performance improvement measured

**Trade-offs**:
- **Pro**: Speedup for frequent operations
- **Con**: More memory (multiple open connections)

**Recommendation**: **IMPLEMENT** in v0.4.4

---

#### Enhancement 3.2: Write-Ahead Logging (WAL) Mode

**Current State**: SQLite in default journaling mode

**Enhancement**: Enable WAL mode for better concurrency

**Benefits**:
- Concurrent readers and writers
- 2-3x speedup for write-heavy workloads
- More robust (fewer lock contentions)

**Implementation** (estimated 1-2 hours):

**Design**:
```python
def enable_wal_mode(database_path: str):
    """Enable Write-Ahead Logging for better concurrency."""
    conn = sqlite3.connect(database_path)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")  # Balanced safety/performance
    conn.close()

# Enable at database creation
enable_wal_mode("~/.ragged/memory/interactions/queries.db")
```

**Benefits**:
- Readers don't block writers
- Writers don't block readers
- Better crash recovery

**Testing Requirements**:
- Concurrent read/write tests
- Crash recovery tests
- Performance benchmarks

**Trade-offs**:
- **Pro**: Better concurrency, faster writes
- **Con**: Slightly more disk space (WAL file)

**Recommendation**: **IMPLEMENT IMMEDIATELY** (v0.4.3 or v0.4.4 - easy win)

---

### Category 4: Caching Strategies

**Priority**: HIGH (caching has huge performance impact)

**Target Users**: All users

---

#### Enhancement 4.1: Multi-Level Caching

**Current State**: No caching layers

**Enhancement**: L1 (memory) + L2 (disk) cache hierarchy

**Benefits**:
- L1: Extremely fast (µs latency)
- L2: Fast and persistent across restarts
- 10-100x speedup for hot data

**Implementation** (estimated 8-10 hours):

**Design**:
```python
from diskcache import Cache as DiskCache
from typing import Optional, Any

class MultiLevelCache:
    """Two-level cache: L1 (memory) + L2 (disk)."""

    def __init__(self, l1_size: int = 1000, l2_path: str = "~/.ragged/cache"):
        """
        Initialize multi-level cache.

        Args:
            l1_size: L1 cache size (number of entries)
            l2_path: L2 cache directory path
        """
        self.l1 = {}  # L1: In-memory dict
        self.l2 = DiskCache(l2_path, size_limit=1e9)  # L2: 1GB disk cache
        self.l1_max_size = l1_size

    def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache (L1 then L2).

        Returns:
            Cached value if found, None otherwise
        """
        # Try L1 first (fastest)
        if key in self.l1:
            return self.l1[key]

        # Try L2 (slower but persistent)
        value = self.l2.get(key)
        if value is not None:
            # Promote to L1
            self._put_l1(key, value)
            return value

        return None

    def put(self, key: str, value: Any) -> None:
        """Store value in both cache levels."""
        self._put_l1(key, value)
        self.l2.set(key, value)

    def _put_l1(self, key: str, value: Any) -> None:
        """Store in L1 with LRU eviction."""
        if len(self.l1) >= self.l1_max_size:
            # Evict random entry (simple LRU alternative)
            self.l1.pop(next(iter(self.l1)))

        self.l1[key] = value
```

**Cache Hierarchy**:
```
Query → L1 Cache (memory, ms latency) → L2 Cache (disk, ms-10ms) → Database (100ms+)
```

**Testing Requirements**:
- Cache hit rates measured
- Performance improvement validated
- Persistence across restarts

**Trade-offs**:
- **Pro**: Best of both worlds (speed + persistence)
- **Con**: Complexity in cache coherence

**Recommendation**: **IMPLEMENT** in v0.4.5 or v0.5.0

---

### Category 5: Parallel Processing

**Priority**: MEDIUM (most operations serial currently)

**Target Users**: Users with multi-core systems, batch operations

---

#### Enhancement 5.1: Parallel Document Ingestion

**Current State**: Documents ingested sequentially

**Enhancement**: Parallel embedding and ingestion

**Benefits**:
- Near-linear speedup with CPU cores (4 cores = 3-4x faster)
- Faster bulk ingestion

**Implementation** (estimated 6-8 hours):

**Design**:
```python
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List

def ingest_documents_parallel(documents: List[Dict],
                               persona: str,
                               max_workers: int = 4) -> None:
    """
    Ingest documents in parallel.

    Args:
        documents: Documents to ingest
        persona: Active persona
        max_workers: Number of parallel workers
    """
    # Split into batches
    batch_size = max(len(documents) // max_workers, 1)
    batches = [
        documents[i:i + batch_size]
        for i in range(0, len(documents), batch_size)
    ]

    def process_batch(batch: List[Dict]) -> int:
        """Process one batch of documents."""
        # Embed documents
        embeddings = embedding_model.encode([doc["text"] for doc in batch])

        # Insert into vector store
        vector_store.add(
            embeddings=embeddings,
            documents=batch,
            persona=persona
        )

        return len(batch)

    # Process batches in parallel
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(process_batch, batch) for batch in batches]

        total_ingested = 0
        for future in as_completed(futures):
            count = future.result()
            total_ingested += count
            logger.info(f"Ingested {total_ingested}/{len(documents)} documents")

    logger.info(f"Parallel ingestion complete: {len(documents)} documents")
```

**Configuration**:
```yaml
performance:
  parallel_ingestion:
    enabled: true
    max_workers: 4  # Number of parallel workers
```

**Testing Requirements**:
- Correctness (parallel == sequential)
- Speedup measured (should be near-linear with cores)
- Thread safety verified

**Trade-offs**:
- **Pro**: Significant speedup for bulk ingestion
- **Con**: Higher memory usage (multiple batches in memory)

**Recommendation**: **IMPLEMENT** in v0.4.5 or v0.5.0

---

#### Enhancement 5.2: Async I/O for Memory Operations

**Current State**: Synchronous I/O

**Enhancement**: Async/await for I/O-bound operations

**Benefits**:
- Better concurrency for I/O operations
- Non-blocking memory recording
- Improved responsiveness

**Implementation** (estimated 10-12 hours):

**Design**:
```python
import asyncio
import aiosqlite
from typing import List

class AsyncMemoryStore:
    """Async memory store for non-blocking operations."""

    def __init__(self, database_path: str):
        self.database_path = database_path

    async def record_interaction(self, interaction: Interaction) -> None:
        """Record interaction asynchronously."""
        async with aiosqlite.connect(self.database_path) as db:
            await db.execute(
                "INSERT INTO interactions VALUES (?, ?, ?, ?, ?, ?)",
                (interaction.id, interaction.persona, interaction.query,
                 interaction.timestamp, interaction.docs, interaction.model)
            )
            await db.commit()

    async def get_interactions(self, persona: str,
                                limit: int = 100) -> List[Interaction]:
        """Get interactions asynchronously."""
        async with aiosqlite.connect(self.database_path) as db:
            async with db.execute(
                "SELECT * FROM interactions WHERE persona = ? LIMIT ?",
                (persona, limit)
            ) as cursor:
                rows = await cursor.fetchall()
                return [Interaction.from_row(row) for row in rows]

# Usage
async def query_with_memory(text: str, persona: str):
    """Query with async memory recording."""
    # Perform query
    results = await perform_query(text, persona)

    # Record interaction asynchronously (non-blocking)
    asyncio.create_task(
        memory_store.record_interaction(
            Interaction(query=text, persona=persona, results=results)
        )
    )

    # Return immediately (don't wait for recording)
    return results
```

**Testing Requirements**:
- Correctness (async == sync)
- Performance improvement measured
- Error handling robust

**Trade-offs**:
- **Pro**: Better concurrency, non-blocking I/O
- **Con**: Complexity (async/await throughout codebase)

**Recommendation**: **DEFER** to v0.5.x (significant refactor required)

---

## Performance Monitoring & Profiling

### Built-in Performance Monitoring

**Implementation** (estimated 4-5 hours):

**Design**:
```python
import time
from functools import wraps
from typing import Dict
import statistics

class PerformanceMonitor:
    """Track performance metrics."""

    def __init__(self):
        self.metrics: Dict[str, List[float]] = {}

    def record(self, operation: str, duration: float) -> None:
        """Record operation duration."""
        if operation not in self.metrics:
            self.metrics[operation] = []
        self.metrics[operation].append(duration)

    def get_stats(self, operation: str) -> Dict:
        """Get statistics for operation."""
        durations = self.metrics.get(operation, [])
        if not durations:
            return {}

        return {
            "count": len(durations),
            "mean": statistics.mean(durations),
            "median": statistics.median(durations),
            "p95": statistics.quantiles(durations, n=20)[18],  # 95th percentile
            "p99": statistics.quantiles(durations, n=100)[98],  # 99th percentile
            "min": min(durations),
            "max": max(durations)
        }

# Decorator for automatic timing
def monitor_performance(operation: str):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start = time.perf_counter()
            try:
                return func(*args, **kwargs)
            finally:
                duration = time.perf_counter() - start
                perf_monitor.record(operation, duration)
        return wrapper
    return decorator

# Usage
@monitor_performance("query")
def query(text: str, persona: str):
    # Automatically timed
    pass
```

**CLI Commands**:
```bash
# View performance statistics
ragged performance stats --since "-24h"
# Output:
# Performance Statistics (Last 24 hours):
#
# Operation: query
#   Count: 1,247
#   Mean: 320ms
#   Median: 280ms
#   P95: 580ms
#   P99: 1,200ms
#   Min: 120ms
#   Max: 2,450ms
#
# Operation: memory_record
#   Count: 1,247
#   Mean: 45ms
#   Median: 40ms
#   P95: 80ms
#   P99: 150ms

# Export performance data
ragged performance export --output performance-report.json
```

**Recommendation**: **IMPLEMENT** in v0.4.4

---

### Profiling Tools Integration

**For Developers**:

**CPU Profiling** (`cProfile` + `snakeviz`):
```bash
# Profile query performance
python -m cProfile -o profile.stats scripts/benchmark_queries.py
snakeviz profile.stats
```

**Memory Profiling** (`memory_profiler`):
```python
from memory_profiler import profile

@profile
def memory_intensive_operation():
    # Automatically profile memory usage
    pass
```

**Continuous Profiling** (production):
- Consider **Pyroscope** or **Datadog Profiler** for production deployments
- Overhead: <1% CPU

**Recommendation**: Document profiling best practices in developer guide

---

## Performance Testing Framework

**Benchmark Suite** (estimated 6-8 hours):

**Location**: `scripts/benchmark.py`

**Benchmarks**:
1. **Query Performance**: 1,000 queries on 10,000-document collection
2. **Ingestion Performance**: Ingest 1,000 documents
3. **Memory Operations**: 1,000 interaction recordings
4. **Graph Queries**: 100 complex graph queries
5. **Bulk Operations**: Export/import 10,000 interactions

**Regression Detection**:
```bash
# Run benchmarks and compare to baseline
python scripts/benchmark.py --compare-to benchmarks/v0.4.4-baseline.json --max-regression 5

# Output:
# Benchmark Results:
#   query_latency: 285ms (baseline: 290ms) ✅ 1.7% improvement
#   ingestion_throughput: 125 docs/s (baseline: 120 docs/s) ✅ 4.2% improvement
#   memory_record: 42ms (baseline: 48ms) ✅ 12.5% improvement
#   graph_query: 210ms (baseline: 200ms) ⚠️  5.0% regression (threshold: 5%)
```

**CI/CD Integration**:
```yaml
# .github/workflows/performance.yml
- name: Run performance benchmarks
  run: python scripts/benchmark.py --compare-to benchmarks/baseline.json

- name: Fail on regression >5%
  run: python scripts/check_performance_regression.py --threshold 5
```

**Recommendation**: **IMPLEMENT** in v0.4.2 (baseline establishment)

---

## Implementation Priority Matrix

| Enhancement | Priority | Effort | Impact | Recommended Timeline |
|-------------|----------|--------|--------|---------------------|
| **WAL Mode** | CRITICAL | Low (1-2h) | High | v0.4.3 (immediate) |
| **Embedding Caching** | HIGH | Low (4-5h) | High | v0.4.4 or v0.4.5 |
| **Query Result Caching** | HIGH | Medium (8-10h) | High | v0.4.4 or v0.4.5 |
| **Connection Pooling** | HIGH | Low (3-4h) | Medium | v0.4.4 |
| **Performance Monitoring** | HIGH | Low (4-5h) | Medium | v0.4.4 |
| **Interaction Batching** | MEDIUM | Low (4-5h) | High | v0.4.3 or v0.4.4 |
| **HNSW Tuning** | MEDIUM | Medium (6-8h) | Medium | v0.4.4 |
| **Parallel Ingestion** | MEDIUM | Medium (6-8h) | High | v0.4.5 or v0.5.0 |
| **Graph Query Optimization** | MEDIUM | Medium (10-12h) | Medium | v0.4.7 |
| **Multi-Level Caching** | MEDIUM | Medium (8-10h) | High | v0.4.5 or v0.5.0 |
| **Async I/O** | LOW | High (10-12h) | Medium | v0.5.x (refactor required) |

---

## Performance Targets by Release

### v0.4.4 Targets (Baseline)
- Memory operations: <100ms
- Graph queries: <300ms
- End-to-end queries: <2s

### v0.4.5+ Targets (With Enhancements)
- Memory operations: <50ms (2x improvement)
- Graph queries: <150ms (2x improvement)
- End-to-end queries: <1s (2x improvement)
- Cache hit rate: >60%
- Ingestion throughput: 100+ docs/s

### v0.5.0 Targets (Aggressive Optimization)
- Memory operations: <25ms (4x improvement)
- Graph queries: <100ms (3x improvement)
- End-to-end queries: <500ms (4x improvement)
- Cache hit rate: >80%
- Ingestion throughput: 200+ docs/s

---

## Related Documentation

- [v0.4.4 Stability & Performance](v0.4.4.md) - Performance baseline establishment
- [Testing Guide](testing-guide.md) - Performance testing standards
- [Execution Playbook](execution-playbook.md) - Performance regression gates

---

**Status**: Enhancement opportunities documented (ready for prioritisation)
