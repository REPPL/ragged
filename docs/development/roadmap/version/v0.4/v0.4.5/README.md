# v0.4.5 - Memory Foundation: Personas & Tracking

**Hours**: 35-40 | **Priority**: P0 - Core Feature | **Status**: Planned

**Dependencies**: v0.4.4 complete (Quality baseline established), **Security audit PASSED**, v0.4.3 complete (LEANN backend available)

---

## 🔒 SECURITY GATE: Implementation Blocked Until Audit Passes

**CRITICAL**: v0.4.5 implementation **CANNOT** begin until formal security audit is complete and passes.

### Why This Gate Exists

v0.4.5 introduces the **personal memory system**—the most privacy-sensitive component in ragged's architecture. This system will store:

- **User behaviour patterns** (query history, topic interests, temporal activity)
- **Personal preferences** (focus areas, active projects, usage statistics)
- **Knowledge graphs** (user-topic-document relationships)
- **Interaction metadata** (retrieved documents, model usage, feedback)

**Unlike document content** (which users explicitly ingest), **behaviour data is implicitly collected**. This requires the highest level of privacy protection and user control.

### Security Audit Requirements

**Status**: ⏳ **Must complete during/after v0.4.4**

**Timeline**: 2-3 weeks (concurrent with v0.4.4 development)

**Scope**: See [security-audit.md](./security-audit.md) for complete requirements

**Key Deliverables**:
1. ✅ Memory system architecture reviewed
2. ✅ Privacy threat model validated
3. ✅ Data isolation guarantees verified
4. ✅ User privacy controls assessed
5. ✅ GDPR compliance confirmed
6. ✅ No critical security findings

**Pass Criteria**: See [security-audit.md](./security-audit.md#success-criteria)

### Implementation Checklist

Before starting v0.4.5 implementation, verify:

- [ ] Security audit complete (see [v0.4.4.md](../v0.4.4.md#security-audit-preparation))
- [ ] Audit report shows **NO critical findings**
- [ ] All high-priority recommendations addressed in design
- [ ] Privacy framework documented (see [privacy-framework.md](./privacy-framework.md))
- [ ] Testing scenarios prepared (see [testing-scenarios.md](./testing-scenarios.md))
- [ ] Team has reviewed and approved audit findings
- [ ] v0.4.3 LEANN backend complete (multi-backend support available)

**If audit fails**: Design changes required, v0.4.5 implementation delayed until resolved.

---

## Overview

Implement personal memory system foundation with persona management, interaction tracking, and knowledge graph initialisation - designed with **multi-backend support from day one** (LEANN + ChromaDB).

**Vision**: Enable ragged to remember user context, preferences, and interaction history - all locally with zero cloud dependencies, leveraging LEANN's storage efficiency (97% savings) where available.

**Multi-Backend Architecture**: Memory system is **designed for LEANN from the start**, with graceful fallback to ChromaDB on unsupported platforms. This avoids migration complexity and provides storage efficiency from day one on macOS/Linux.

**Theoretical Foundation**: Inspired by [Context Engineering 2.0](../../../../acknowledgements/context-engineering-2.0.md), this release implements **structured context layering**—organising personal knowledge as hierarchical entities (users → topics → documents → temporal relationships). Knowledge graphs reduce computational uncertainty (entropy reduction) by making relationships explicit and machine-understandable.

---

## Core Deliverables

### 1. Persona Manager (8h)

User persona system for context switching.

```python
# Usage
ragged persona create researcher --description "ML researcher" --focus "RAG, NLP, privacy"
ragged persona switch researcher
ragged persona list
```

**Features**:
- Create/switch/delete personas
- Focus areas and preferences
- Usage statistics
- Active project tracking

**Files**:
- `ragged/memory/persona.py` (~250 lines)
- `tests/memory/test_persona.py` (~150 lines)

---

### 2. Interaction Tracking (6h)

SQLite-based interaction history storage.

**Schema**:
```sql
CREATE TABLE interactions (
    id TEXT PRIMARY KEY,
    persona TEXT NOT NULL,
    query TEXT NOT NULL,
    response TEXT,
    timestamp TIMESTAMP,
    retrieved_doc_ids TEXT,  -- JSON
    model_used TEXT,
    latency_ms REAL,
    feedback TEXT,           -- positive/negative
    session_id TEXT
);
```

**Features**:
- Record all queries and responses
- Track retrieved documents
- User feedback collection
- Session management

**Privacy Considerations**:
- All data stored locally in `~/.ragged/memory/interactions/`
- Encryption at rest (inherited from v0.2.11)
- PII detection and optional redaction (inherited from v0.2.11)
- User can view, edit, or delete any interaction
- Export functionality for data portability (GDPR Article 20)

**Files**:
- `ragged/memory/interactions.py` (~200 lines)
- `tests/memory/test_interactions.py` (~150 lines)

---

### 3. Knowledge Graph Foundation (6h)

Kuzu-based graph database for relationships.

**Schema**:
```cypher
// Nodes
CREATE NODE TABLE User(name STRING, created_at TIMESTAMP);
CREATE NODE TABLE Topic(name STRING, interest_level FLOAT);
CREATE NODE TABLE Document(doc_id STRING, title STRING);

// Relationships
CREATE REL TABLE INTERESTED_IN(FROM User TO Topic, frequency INT);
CREATE REL TABLE ACCESSED(FROM User TO Document, timestamp TIMESTAMP);
```

**Features**:
- User-topic relationships
- Document access tracking
- Topic co-occurrence
- Temporal information

**Privacy Considerations**:
- Graph data stored locally in `~/.ragged/memory/graph/`
- No external graph database connections
- User can query and visualise their own graph
- User can delete specific nodes/relationships
- Full graph export for portability

**Files**:
- `ragged/memory/graph.py` (~300 lines)
- `tests/memory/test_graph.py` (~200 lines)

---

### 4. CLI Commands (8h)

Memory management interface.

```bash
# Persona management
ragged persona create <name> --description "..." --focus "topics"
ragged persona switch <name>
ragged persona list
ragged persona delete <name> --confirm

# Memory viewing
ragged memory list --limit 10 --persona researcher
ragged memory topics --persona researcher
ragged memory timeline --since "-30d"
ragged memory show <interaction-id>

# Memory management
ragged memory delete <interaction-id> --confirm
ragged memory export <output-file> --persona researcher
ragged memory clear --persona researcher --confirm
```

**Privacy-Focused Commands** (see [privacy-framework.md](./privacy-framework.md#user-privacy-controls)):
```bash
# View all collected data
ragged memory show-all --persona researcher

# Export for portability (GDPR Article 20)
ragged memory export my-memory.json --persona researcher

# Delete specific interactions (GDPR Article 17)
ragged memory delete <id> --confirm

# Clear all memory for persona (GDPR Article 17)
ragged memory clear --persona researcher --confirm

# Disable memory collection
ragged memory disable --persona researcher
```

**Files**:
- Update `ragged/cli/main.py` with command groups
- `tests/cli/test_memory_commands.py` (~200 lines)

---

### 5. Comprehensive Testing (7-9h)

Dedicated testing effort for memory system with **privacy focus**.

**Test Coverage**:
- Unit tests: Persona, interactions, graph
- Integration tests: Full workflows
- Privacy tests: Local-only validation (see [testing-scenarios.md](./testing-scenarios.md))
- Persistence tests: Survive restarts
- User control tests: Delete, export, clear operations

**Privacy Test Requirements** (see [testing-scenarios.md](./testing-scenarios.md)):
- ✅ Network isolation: No external calls during memory operations
- ✅ Data locality: All data in `~/.ragged/memory/`
- ✅ Persona isolation: No cross-contamination between personas
- ✅ Encryption validation: Data encrypted at rest
- ✅ User control: All CRUD operations work correctly
- ✅ Export functionality: Data portability validated
- ✅ Deletion effectiveness: Data fully removed when deleted

---

## Testing Requirements

**Coverage**: ≥85% for memory modules

**Privacy Tests** (comprehensive scenarios in [testing-scenarios.md](./testing-scenarios.md)):
- ✅ No network calls (monitor all connections)
- ✅ Data stays in `~/.ragged/memory/`
- ✅ Persona isolation (no cross-contamination)
- ✅ Encryption at rest validated
- ✅ User control operations functional (view, edit, delete, export)
- ✅ PII detection working correctly
- ✅ Data deletion is permanent (no residual data)

**Automated Privacy Testing**:
```python
# Example test structure
def test_memory_no_network_calls():
    """Verify memory system makes zero network calls."""
    with NetworkMonitor() as monitor:
        # Create persona, record interactions, query memory
        pass
    assert monitor.external_calls == 0

def test_memory_data_locality():
    """Verify all memory data stored in expected location."""
    memory_dir = Path.home() / ".ragged" / "memory"
    # Verify all DB files, YAML files in memory_dir
    assert all_files_in_directory(memory_dir)

def test_persona_isolation():
    """Verify personas don't see each other's data."""
    persona_a.query("machine learning")
    persona_b.query("cooking recipes")
    # Verify persona_a doesn't see persona_b's cooking data
    assert "cooking" not in persona_a.get_topics()
```

---

## Documentation

**Required** (~1,500 lines):

1. **Tutorial**: Getting Started with Personas (~400 lines)
   - Creating first persona
   - Switching between personas
   - Viewing memory
   - Privacy controls

2. **Guide**: Memory System User Guide (~600 lines)
   - Memory architecture explanation
   - Privacy guarantees (see [privacy-framework.md](./privacy-framework.md))
   - User controls (view, edit, delete, export)
   - Persona management
   - Knowledge graph visualisation
   - Disabling memory collection

3. **Reference**: Memory API Documentation (~300 lines)
   - Persona API
   - Interaction API
   - Graph API
   - Privacy controls API

4. **Privacy**: User Privacy Documentation (~200 lines)
   - What data is collected
   - Where data is stored
   - How to view your data
   - How to delete your data
   - How to export your data
   - How to disable collection
   - GDPR rights explained

---

## Success Criteria

Version 0.4.5 is successful if:

1. ✅ **Security audit passed** (no critical findings)
2. ✅ Persona system works seamlessly
3. ✅ Memory tracking transparent to users
4. ✅ All interactions stored locally (verified by privacy tests)
5. ✅ Users can view/edit/delete memory (all controls functional)
6. ✅ Knowledge graph initialised
7. ✅ Privacy guaranteed (100% local, tested rigorously)
8. ✅ 85%+ test coverage (including privacy test scenarios)
9. ✅ Performance: Persona switch <100ms, interaction record <50ms
10. ✅ CLI commands functional
11. ✅ Documentation complete (including privacy documentation)
12. ✅ User privacy controls working (delete, export, clear)
13. ✅ No network calls during memory operations (automated testing)
14. ✅ Encryption at rest validated
15. ✅ GDPR compliance verified (Articles 15, 17, 20)
16. ✅ Multi-backend memory system works (LEANN on macOS/Linux, ChromaDB on Windows)
17. ✅ Memory data portable between backends (backend-agnostic storage)

---

## Performance Targets

- Persona switching: <100ms
- Interaction recording: <50ms (async)
- Graph query: <300ms
- Memory retrieval: <200ms
- Memory deletion: <100ms
- Memory export: <2s for 1000 interactions

---

## File Summary

**New Files** (~2,400 lines):
- Memory core: ~750 lines
- CLI: Update existing
- Tests: ~900 lines (including privacy tests)
- Documentation: ~1,500 lines

**Dependencies**:
- `kuzu>=0.6.0` - Graph database
- `pydantic>=2.0` - Already used
- `python-dateutil>=2.8` - Temporal operations
- VectorStore backend (from v0.4.3): LEANN or ChromaDB (auto-selected)

---

## Storage Architecture

```
~/.ragged/memory/
├── profiles/
│   ├── personas.yaml          # Persona definitions
│   ├── preferences.db          # SQLite (encrypted)
│   └── user_profile.yaml
├── interactions/
│   ├── queries.db              # SQLite (encrypted)
│   └── feedback.db             # SQLite (encrypted)
├── semantic/
│   └── memory_vectors/         # Multi-backend: LEANN (macOS/Linux) or ChromaDB (Windows)
└── graph/
    └── kuzu_db/                # Kuzu database
```

**Multi-Backend Integration** (v0.4.3 foundation):
- Memory system uses `VectorStore` interface (backend-agnostic)
- macOS/Linux: LEANN backend by default (97% storage savings)
- Windows: ChromaDB backend (fully functional)
- User can override backend selection via config

**Memory Storage Efficiency**:
- LEANN (macOS/Linux): ~6MB for 10K interactions (97% savings)
- ChromaDB (Windows): ~200MB for 10K interactions (standard)

**Encryption** (inherited from v0.2.11):
- All SQLite databases encrypted at rest
- YAML files containing sensitive data encrypted
- Kuzu database: Investigate encryption support
- Vector storage: Backend-specific encryption (both LEANN and ChromaDB support encryption)

---

## Risk Assessment

**High Risk** (Addressed by security audit):
- Privacy violations → Mitigation: Formal audit, comprehensive privacy tests
- Data leakage → Mitigation: Network monitoring tests, data locality validation
- Inadequate user controls → Mitigation: GDPR compliance validation

**Medium Risk**:
- Kuzu integration complexity → Mitigation: Comprehensive examples and tests
- Privacy guarantees → Mitigation: Explicit testing, no network calls

**Low Risk**:
- SQLite integration (well-established)
- YAML configuration (simple)

---

## Privacy Framework

**See**: [privacy-framework.md](./privacy-framework.md) for complete privacy framework including:
- User privacy controls specification
- Data minimisation principles
- Consent mechanisms
- Privacy by design principles
- GDPR compliance mapping

---

## Testing Scenarios

**See**: [testing-scenarios.md](./testing-scenarios.md) for comprehensive privacy testing scenarios including:
- Network isolation tests
- Data locality tests
- Persona isolation tests
- User control tests
- Encryption validation tests
- PII detection tests

---

## Security Audit

**See**: [security-audit.md](./security-audit.md) for complete security audit requirements, scope, and pass criteria.

**Critical**: v0.4.5 implementation blocked until audit passes.

---

## Related Documentation

- [v0.4 Overview](../README.md) - Release series overview
- [v0.4 Detailed Spec](../v0.4-detailed-spec.md) - Part 2: Milestone 1
- [v0.4.4](../v0.4.4.md) - Code quality (previous) - **Security audit preparation**
- [v0.4.3](../v0.4.3.md) - LEANN backend (previous) - **Multi-backend foundation**
- [v0.4.6](../v0.4.6.md) - Stability & performance (next)
- [Security Audit Requirements](./security-audit.md) - **MUST PASS BEFORE IMPLEMENTATION**
- [Privacy Framework](./privacy-framework.md) - User privacy controls and validation
- [Testing Scenarios](./testing-scenarios.md) - Comprehensive privacy testing

---
