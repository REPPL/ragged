# ADR-0016: Memory System Architecture

**Date:** 2025-11-22
**Status:** Accepted (for v0.4.5 implementation)
**Deciders:** ragged development team
**Tags:** architecture, memory, privacy, v0.4.5

---

## Context

Version 0.4.x transforms ragged from a document retrieval tool into an intelligent personal knowledge assistant. This requires a comprehensive personal memory system that can:

1. **Track user behaviour** - Remember what users query, when, and how often
2. **Learn interests** - Build profiles of user interests and topics
3. **Personalise results** - Boost relevant documents based on learned preferences
4. **Understand context** - Know temporal context (when things happened)
5. **Maintain privacy** - All data stays local, encrypted, with user control

### Requirements

**Functional**:
- Multiple persona support (researcher, developer, personal, etc.)
- Interaction tracking (queries, retrieved documents, timestamps)
- Interest profile building (topics, frequency, recency, confidence)
- Knowledge graph (relationships between topics, documents, personas)
- Temporal awareness (facts valid at specific times)

**Non-Functional**:
- 100% local operation (no cloud dependencies)
- Encryption at rest (AES-256-GCM)
- GDPR compliance (Articles 15, 17, 20)
- Performance: <100ms memory operations, <300ms graph queries
- Privacy-first design (user controls: view, delete, export, disable)

### Constraints

- Must build on v0.2.10/v0.2.11 privacy foundation
- Cannot break backward compatibility
- Must pass security audit before implementation
- Storage overhead <20% of document storage
- Works offline without degradation

---

## Decision

We will implement a **multi-layered memory architecture** with four storage components, each optimised for specific data types and query patterns:

### Architecture Overview

```
~/.ragged/memory/
├── profiles/          # Persona metadata (JSON, encrypted)
├── interactions/      # Interaction history (SQLite, encrypted)
├── semantic/          # Memory vectors (LEANN on macOS/Linux, ChromaDB on Windows)
└── graph/            # Knowledge graph (Kuzu embedded)
```

### Layer 1: Persona Profiles

**Storage**: JSON files with AES-256-GCM encryption
**Purpose**: Persona metadata and configuration
**Access Pattern**: Infrequent, full-object reads

```python
@dataclass
class Persona:
    """User persona metadata."""
    name: str
    created_at: datetime
    description: str
    settings: PersonaSettings
    encryption_key_id: str
```

**Rationale**: Simple file-based storage suitable for infrequently-accessed metadata. Encryption ensures privacy even if file system is compromised.

---

### Layer 2: Interaction History

**Storage**: SQLite with WAL mode, encrypted at rest
**Purpose**: Temporal query log, document access tracking
**Access Pattern**: Time-range queries, aggregations

```sql
CREATE TABLE interactions (
    id TEXT PRIMARY KEY,
    persona TEXT NOT NULL,
    query TEXT NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    retrieved_doc_ids TEXT,  -- JSON array
    metadata TEXT,           -- JSON
    FOREIGN KEY (persona) REFERENCES personas(name)
);

CREATE INDEX idx_interactions_persona_time
ON interactions(persona, timestamp);
```

**Rationale**:
- SQLite excellent for time-series data and local analytics
- WAL mode enables concurrent reads during writes
- Indexes optimise timeline queries
- Lightweight, no external dependencies

---

### Layer 3: Semantic Memory

**Storage**: Multi-backend vector store (platform-aware)
**Purpose**: Semantic search over memory (query similarity, topic clustering)
**Access Pattern**: Vector similarity search

```python
class MemoryVectorStore:
    """Semantic memory storage."""
    def __init__(self, platform: str):
        if platform in ["darwin", "linux"]:
            self.backend = LEANNStore(path="~/.ragged/memory/semantic/")
        else:  # Windows
            self.backend = ChromaDBStore(path="~/.ragged/memory/semantic/")
```

**Rationale**:
- LEANN on macOS/Linux: 97% storage savings critical for memory data
- ChromaDB fallback on Windows: Maximum compatibility
- Reuses VectorStore abstraction from v0.4.1
- Same interface regardless of backend

---

### Layer 4: Knowledge Graph

**Storage**: Kuzu embedded graph database
**Purpose**: Relationships (persona→topic, topic→document, topic→topic)
**Access Pattern**: Graph traversals, relationship queries

```cypher
// Schema
CREATE NODE TABLE Persona(name STRING, PRIMARY KEY(name));
CREATE NODE TABLE Topic(name STRING, confidence DOUBLE, PRIMARY KEY(name));
CREATE NODE TABLE Document(id STRING, PRIMARY KEY(id));

CREATE REL TABLE INTERESTED_IN(FROM Persona TO Topic, frequency INT, recency DOUBLE, first_seen TIMESTAMP, last_seen TIMESTAMP);
CREATE REL TABLE RELATED_TO(FROM Topic TO Topic, co_occurrence INT);
CREATE REL TABLE ACCESSED(FROM Persona TO Document, timestamps TIMESTAMP[]);
```

**Rationale**:
- Graphs natural for relationship-heavy memory data
- Kuzu embeddable, no server required
- Excellent query performance for traversals
- Built-in temporal property support

---

## Consequences

### Positive

1. **Optimised for Purpose**: Each layer uses storage best suited for its data type
2. **Privacy-First**: Encryption, local-only, user controls baked in
3. **Scalable**: Handles years of interaction history efficiently
4. **Platform-Aware**: LEANN where supported, ChromaDB everywhere
5. **Query Flexibility**: SQL for time-series, Cypher for graphs, vector for semantics
6. **Offline-First**: No external dependencies, works without network

### Negative

1. **Complexity**: Four storage systems to maintain
2. **Backup Coordination**: Must backup all four layers coherently
3. **Migration Overhead**: Moving between backends requires careful data mapping
4. **Storage Overhead**: Four databases instead of one
5. **Testing Burden**: Must test each layer independently and integrated

### Mitigations

**Complexity**:
- Abstract each layer behind clean interfaces
- Comprehensive integration tests
- Clear documentation of layer responsibilities

**Backup**:
- Unified backup command: `ragged memory backup <output-file>`
- Atomic backup via temporary directory
- Versioned backup format with integrity checks

**Migration**:
- Migration tools in v0.4.11 (ChromaDB ↔ LEANN)
- Export/import for persona portability
- Schema version tracking

**Storage Overhead**:
- Monitor actual usage (target: <20% of document storage)
- Compression where appropriate
- Retention policies (optional, user-controlled)

**Testing**:
- Layer-specific unit tests
- Integration tests for cross-layer operations
- Privacy test suite (comprehensive scenarios)
- Performance benchmarks

---

## Alternatives Considered

### Alternative 1: Single Database (PostgreSQL)

**Approach**: Use PostgreSQL with pgvector extension for all storage

**Rejected Because**:
- Requires PostgreSQL server (breaks embeddable requirement)
- Overkill for single-user, local-only use case
- Graph queries awkward in SQL
- No significant benefit over specialised embedded databases

### Alternative 2: All-SQLite

**Approach**: Use SQLite for everything (including vectors and graph)

**Rejected Because**:
- Vector search in SQLite inefficient (no indexing)
- Graph traversals awkward in SQL (recursive CTEs complex)
- Missing 97% storage savings from LEANN
- Not as performant for specialised use cases

### Alternative 3: In-Memory Only

**Approach**: Keep memory data in Python dictionaries, persist as JSON

**Rejected Because**:
- Large memory footprint (years of history)
- Slow queries (linear scans)
- No indexing or query optimisation
- Complex backup/restore logic
- Doesn't scale

---

## Implementation Plan

### Phase 1: Foundation (v0.4.5)
- Persona management (Layer 1)
- Interaction tracking (Layer 2)
- Knowledge graph foundation (Layer 4)
- Privacy controls and encryption
- Basic CLI commands

### Phase 2: Behaviour Learning (v0.4.7-v0.4.8)
- Semantic memory (Layer 3) with multi-backend support
- Topic extraction and interest profiles
- Personalised ranking
- Advanced graph queries

### Phase 3: Temporal Features (v0.4.10)
- Temporal fact storage (extends Layer 2)
- Timeline queries
- Time-aware retrieval
- Historical context

---

## Security Considerations

**Encryption**:
- AES-256-GCM for all sensitive data at rest
- Per-persona encryption keys
- Key derivation from user passphrase (PBKDF2, 100k iterations)
- Encrypted fields: queries, document content references, metadata

**Access Control**:
- Persona isolation enforced at database level
- No cross-persona data access without explicit user command
- SQLite user_version for schema migration tracking

**Audit Trail**:
- All memory operations logged (if user enables)
- Privacy-safe logging (no sensitive data in logs)
- Export capabilities for transparency (GDPR Article 15)

**Security Audit**:
- Formal security audit required before v0.4.5 implementation (see v0.4.4)
- Privacy threat model documented
- GDPR compliance validation

---

## Performance Characteristics

**Expected Performance** (v0.4.5 onwards):

| Operation | Target | Approach |
|-----------|--------|----------|
| Persona load | <50ms | Small JSON files, OS cache |
| Interaction insert | <50ms | SQLite WAL mode, batched |
| Interaction query (30d) | <200ms | Indexed time-range query |
| Graph query | <300ms | Kuzu optimised traversals |
| Memory search | <500ms | LEANN or ChromaDB |
| Profile update | <100ms | In-memory, async persist |
| Backup | <10s | Parallel copy of all layers |

**Optimisation Strategies**:
- Database indexing (timestamp, persona, topics)
- Query caching (LRU, 30min TTL)
- Batch inserts for interactions
- Async writes where possible
- Prepared statements for repeated queries

---

## Privacy Framework

**GDPR Compliance** (Articles 15, 17, 20):

```bash
# Article 15: Right to Access
ragged memory export --persona researcher --output my-data.json

# Article 17: Right to Erasure
ragged memory delete --persona researcher --confirm

# Article 20: Right to Data Portability
ragged memory export --persona researcher --format json --output portable.json
```

**Privacy Controls**:
- View all tracked data (full transparency)
- Delete specific topics, queries, or entire personas
- Disable memory collection temporarily or permanently
- Export all data in portable format
- PII detection and optional redaction

**Data Minimisation**:
- Only store what's necessary for functionality
- Configurable retention (optional)
- User controls what gets tracked
- Anonymous usage option (disable persona tracking)

---

## Monitoring & Observability

**Storage Metrics**:
- Total memory storage size
- Per-layer breakdown
- Growth rate tracking
- Storage vs document ratio

**Performance Metrics**:
- Query latency percentiles (p50, p95, p99)
- Cache hit rates
- Database sizes
- Backup duration

**Privacy Metrics**:
- Personas tracked
- Interactions per persona
- Topics tracked
- Data age distribution

**CLI**:
```bash
ragged memory stats --persona researcher
ragged memory storage-usage
ragged memory privacy-report
```

---

## Related Documentation

**Planning**:
- [v0.4 Planning Overview](../../planning/version/v0.4/README.md) - High-level memory system design

**Roadmap**:
- [v0.4.5 Roadmap](../../roadmap/version/v0.4/v0.4.5/README.md) - Memory foundation implementation
- [v0.4.7-v0.4.8 Roadmap](../../roadmap/version/v0.4/v0.4.7.md) - Behaviour learning
- [v0.4.10 Roadmap](../../roadmap/version/v0.4/v0.4.10/README.md) - Temporal memory

**Other ADRs**:
- [ADR-0015: VectorStore Abstraction](./0015-vectorstore-abstraction.md) - Foundation for semantic memory layer
- [ADR-0018: LEANN Integration Decision](./0018-leann-integration-decision.md) - Platform-aware backend selection
- [ADR-0011: Privacy-Safe Logging](./0011-privacy-safe-logging.md) - Privacy in logging

**Security**:
- [v0.4.5 Security Audit](../../roadmap/version/v0.4/v0.4.5/security-audit.md) - Security audit requirements
- [v0.4.5 Privacy Framework](../../roadmap/version/v0.4/v0.4.5/privacy-framework.md) - Privacy design

---

## Decision Rationale

This architecture was chosen because it:

1. **Respects Privacy**: Built on v0.2.10/v0.2.11 foundation, encryption by default, user control
2. **Optimises for Purpose**: Each storage layer suited to its data type and access patterns
3. **Scales Gracefully**: Handles years of history without degradation
4. **Maintains Compatibility**: Works on all platforms with appropriate backends
5. **Enables Innovation**: Flexible foundation for temporal, semantic, and graph-based features
6. **Stays Local**: No cloud dependencies, works offline, user owns their data

The multi-layer approach adds complexity but delivers significantly better performance and capabilities than alternatives. The privacy-first design ensures user trust and GDPR compliance from day one.

---

**Status**: Accepted (awaiting security audit completion before v0.4.5 implementation)
