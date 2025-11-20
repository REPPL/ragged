# ragged v0.4 Design Overview


**Status:** 📋 Planned

---

## Overview

Version 0.4 introduces a **Personal Memory System** and **Knowledge Graphs**, transforming ragged from a document retrieval tool into an intelligent personal knowledge assistant that learns from your interactions—all locally.

**Goal**: Make ragged remember what you care about and provide increasingly personalised responses over time.

**For detailed implementation plans, see:**
- [Roadmap: v0.4.0](../../../roadmap/version/v0.4.0/) - Personal memory & knowledge graphs (180-225 hours)

---

## Prerequisites

**Security & Privacy Foundation (REQUIRED):**

v0.4 features store highly sensitive user data (behaviour patterns, interests, temporal history). The security and privacy infrastructure from v0.2.10 and v0.2.11 is **mandatory** before implementing any v0.4 features.

- ✅ **v0.2.10 (Security Hardening)** - Session isolation, JSON serialisation, security testing
- ✅ **v0.2.11 (Privacy Infrastructure)** - Encryption, PII detection, TTL cleanup, GDPR compliance
- ✅ **v0.3.x (Production-Ready RAG)** - All v0.3 features must be complete

**Why Critical for v0.4:**

v0.4 introduces the most privacy-sensitive features yet:
- **Behaviour learning** - Tracks query patterns and interests (potential for profiling)
- **Temporal memory** - Time-based user activity tracking
- **Entity extraction** - May capture PII from documents
- **Interest tracking** - Infers user preferences (sensitive)
- **Persona management** - Multiple user contexts (cross-context leakage risk)

**Without v0.2.10/v0.2.11:**
- ❌ Behaviour data stored in plaintext (severe privacy violation)
- ❌ Interest profiles vulnerable to unauthorised access
- ❌ Temporal history could reveal sensitive patterns
- ❌ No automatic cleanup (indefinite user profiling)
- ❌ GDPR non-compliance

**See:**
- [Security & Privacy Foundation](../../security/README.md)
- [v0.2.10 Roadmap](../../../roadmap/version/v0.2/v0.2.10/)
- [v0.2.11 Roadmap](../../../roadmap/version/v0.2/v0.2.11/)

---

## Design Goals

### 1. Personal Memory System
**Problem**: Every query starts from scratch, no learning or personalisation.

**Solution**:
- Persona management (work, research, personal contexts)
- Behaviour learning from query patterns
- Temporal memory (what you worked on when)
- Interest tracking and topic preferences

**Expected Impact**: Responses tailored to your interests and context

### 2. Knowledge Graphs
**Problem**: Documents exist in isolation, no understanding of relationships.

**Solution**:
- Entity extraction and linking
- Topic and concept mapping
- Document relationship graphs
- Multi-hop reasoning across documents

**Expected Impact**: Better understanding of complex, interconnected topics

### 3. Personalised Ranking
**Problem**: Retrieval ignores your preferences and history.

**Solution**:
- Interest-based boosting
- Recency boosting for recent topics
- Project-aware relevance
- Context-sensitive ranking

**Expected Impact**: Most relevant documents appear first, based on your usage

### 4. Plugin Architecture
**Problem**: Can't extend ragged with custom functionality.

**Solution**:
- Plugin system for custom embedders
- Custom retrieval strategies
- Custom chunking strategies
- Hook system for workflow integration

**Expected Impact**: Community can extend ragged for specialised use cases

---

## Key Features

- **Persona Management**: Switch contexts (work/research/personal)
- **Knowledge Graphs**: Connect topics, documents, concepts
- **Temporal Memory**: Track what you worked on when
- **Interest Learning**: Automatically learn from query patterns
- **Personalised Retrieval**: Boost documents based on your interests
- **Plugin System**: Extend with custom functionality

---

## Success Criteria

- Personalized ranking improves relevance by >20%
- Knowledge graph enables multi-hop reasoning
- Plugin system allows community extensions
- Memory system works entirely locally (no cloud)
- Temporal queries work ("what did I read about ML last week?")

---

## Total Effort

**180-225 hours** across personal memory, knowledge graphs, and plugins

**Timeline:** ~4-6 months with single developer

---

## Privacy & Security Considerations

v0.4 handles highly sensitive user data. All features **must** integrate with v0.2.10/v0.2.11 privacy infrastructure.

### Data Privacy Requirements

| Feature | Data Stored | Privacy Mitigation | TTL |
|---------|-------------|-------------------|-----|
| **Persona Management** | User context profiles | Encrypted storage, session isolation | 90 days |
| **Behaviour Learning** | Query pattern hashes | Query hashing (NOT plaintext), encrypted DB | 90 days |
| **Temporal Memory** | Activity timestamps | Query hashes + timestamps, no sensitive data | 90 days |
| **Interest Tracking** | Topic preference scores | Aggregated only, no individual queries | 90 days |
| **Knowledge Graphs** | Entities, relationships | PII detection on extraction, encrypted nodes | 180 days |

### Privacy-by-Design Principles

**1. Data Minimisation:**
- Store behaviour patterns as aggregates, NOT individual queries
- Use query hashes (SHA-256) instead of plaintext
- Topic preferences as numeric scores, not query logs
- Entity extraction with PII filtering

**2. Encryption at Rest:**
```python
# ALL user profiles encrypted
from ragged.privacy import EncryptionManager

encryption = EncryptionManager()
encrypted_profile = encryption.encrypt(profile_json.encode())
profile_file.write_bytes(encrypted_profile)
profile_file.chmod(0o600)  # User-only permissions
```

**3. Session Isolation:**
```python
# Personas scoped to sessions
from ragged.session import SessionManager

session = SessionManager().get_or_create_session()
persona = PersonaManager(session_id=session.session_id)
# No cross-session persona access
```

**4. TTL-Based Cleanup:**
```python
# Automatic cleanup of old behaviour data
from ragged.privacy import CleanupScheduler

scheduler = CleanupScheduler()
scheduler.schedule_cleanup(
    data_path=Path("~/.ragged/memory/behaviour.db"),
    ttl_days=90  # Behaviour patterns expire after 90 days
)
```

**5. GDPR Compliance:**
```bash
# User can export all memory data
ragged privacy export --include-memory --output my-memory.json

# User can delete all memory data
ragged privacy delete --confirm  # Includes behaviour, personas, graphs

# User can view what's stored
ragged privacy status
# Output:
#   Memory System:  3 personas, 127 behaviour patterns
#   Knowledge Graph: 542 entities, 1,234 relationships
#   Oldest Data:    45 days ago
```

### Privacy Risk Assessment

| Feature | Privacy Risk | Risk Score | Mitigation |
|---------|-------------|-----------|-----------|
| **Persona Management** | Medium | 85/100 | Encrypted storage, session isolation, TTL |
| **Behaviour Learning** | **HIGH** | **88/100** | Query hashing, aggregation, encryption, TTL |
| **Temporal Memory** | **HIGH** | **87/100** | Query hashing, timestamps only, encryption, TTL |
| **Interest Tracking** | Medium | 90/100 | Aggregated scores, no raw queries, TTL |
| **Knowledge Graphs** | **HIGH** | **85/100** | PII filtering on extraction, encrypted, TTL |
| **Plugin System** | **HIGH** | TBD | Sandboxing, permissions, code review required |

**Interpretation:** 85-90/100 = Excellent privacy with comprehensive mitigations

### Security Testing Requirements

**For ALL v0.4 features:**
- [ ] No plaintext user data in storage
- [ ] Query hashing verified (no plaintext queries)
- [ ] Encryption at rest functional
- [ ] File permissions 0o600 enforced
- [ ] Session isolation tested (no cross-session leakage)
- [ ] TTL cleanup functional (automated tests)
- [ ] GDPR deletion complete (all memory data removed)
- [ ] GDPR export complete (all memory data returned)
- [ ] PII detection tested (entity extraction filtered)

**Security Agent Workflow:**

Use `codebase-security-auditor` agent:
1. After implementing each memory/graph feature
2. Before committing any behaviour tracking code
3. Before release
4. Quarterly audits of memory system

### User Control & Transparency

**Privacy Configuration:**
```bash
# Configure memory retention
ragged config set memory.ttl_days 90
ragged config set memory.behaviour_learning_enabled true
ragged config set memory.interest_tracking_enabled true

# Disable memory features (opt-out)
ragged config set memory.enabled false

# View memory statistics
ragged memory stats
```

**Privacy Warnings:**
- First use: Display privacy policy for memory system
- Behaviour learning: "ragged is learning from your queries to improve results"
- Entity extraction: "Extracting entities from documents (PII filtered)"
- Plugin installation: "Third-party plugin - review permissions"

---

## Out of Scope (Deferred to v0.5+)

❌ **Not in v0.4**:
- Vision-based retrieval (v0.5)
- Multi-modal embeddings (v0.5)
- Web UI (v1.0)
- Multi-user support (v1.0)

---

## Related Documentation

- [v0.3 Planning](../v0.3/) - Advanced retrieval & multi-modal
- [v0.5 Planning](../v0.5/) - Vision integration
- [Roadmap: v0.4.0](../../../roadmap/version/v0.4.0/) - Detailed implementation plan
- [Architecture](../../architecture/) - System architecture

---
