# US-002: Personal Knowledge Vault

**ID**: US-002
**Title**: Personal Knowledge Vault
**Status:** ✅ Active
**Priority**: Critical
**Personas**: Researcher (primary), Casual (secondary)
**Versions**: v0.1 - v1.0

---

## Overview

**As a** researcher managing years of accumulated personal insights and information
**I want** a local RAG-powered system that securely stores and retrieves my personal vault (meeting notes, ideas, hypotheses, conference takeaways, personal observations, and informal communications)
**So that** I can capture fleeting thoughts, track the evolution of my ideas over time, and rediscover forgotten insights that might inform current research

---

## Acceptance Criteria

### Input & Capture

#### AC-001: Multiple Input Methods (v0.1-v0.3)
**Given** the need to capture ideas quickly
**When** I want to create a note
**Then** the system should support:
- ✅ Text input via CLI/UI (v0.1)
- ✅ Markdown formatting (v0.2)
- ✅ LaTeX equations support (v0.3)
- 🚧 Voice-to-text transcription (v1.1 - deferred)
- 🚧 Image capture with OCR (v1.1 - deferred)

**Test Coverage**: `tests/integration/test_note_capture.py`

**Success Metric**: < 5 seconds from thought to captured note

---

#### AC-002: Markdown & LaTeX Support (v0.2)
**Given** technical note-taking needs
**When** I write notes
**Then** the system should:
- ✅ Render Markdown formatting
- ✅ Support LaTeX equations inline and block
- ✅ Preserve formatting in search and retrieval
- ✅ Export formatted notes

**Test Coverage**: `tests/unit/test_markdown_latex.py`

**Example**:
```markdown
# Research Note: Quantum Computing

**Hypothesis**: Quantum entanglement could be used for...

$$
|\psi\rangle = \frac{1}{\sqrt{2}}(|00\rangle + |11\rangle)
$$

This suggests that...
```

---

#### AC-003: Private Annotations (v0.3)
**Given** research materials
**When** I read documents
**Then** I should be able to:
- ✅ Add private annotations to any document
- ✅ Link annotations to specific passages
- ✅ Search annotations separately from source text
- ✅ View annotations in context

**Test Coverage**: `tests/integration/test_annotations.py`

---

### Knowledge Organisation

#### AC-004: Auto-linking to Research (v0.3)
**Given** personal notes and research documents
**When** I create a note
**Then** the system should:
- ✅ Automatically link notes to relevant research documents
- ✅ Suggest related papers based on note content
- ✅ Show bidirectional links (notes ↔ papers)
- ✅ Enable graph-based exploration

**Test Coverage**: `tests/integration/test_auto_linking.py`

**Success Metric**: 80%+ accuracy in suggested links (manual validation)

---

#### AC-005: Vault Separation (v0.1)
**Given** personal and professional content
**When** storing information
**Then** the system should:
- ✅ Maintain strict separation between personal vault and research library
- ✅ Prevent personal notes from appearing in research queries (unless explicitly requested)
- ✅ Allow optional cross-vault search when needed
- ✅ Clearly label vault source in results

**Test Coverage**: `tests/integration/test_vault_separation.py`

---

#### AC-006: Theme Identification (v0.3)
**Given** collection of personal notes
**When** the system analyses content
**Then** it should:
- ✅ Identify recurring themes and patterns
- ✅ Cluster related notes
- ✅ Suggest tags based on themes
- ✅ Visualise theme evolution over time

**Test Coverage**: `tests/evaluation/test_theme_clustering.py`

---

#### AC-007: Personalised Ontology (v0.4)
**Given** how I connect ideas
**When** the system learns my patterns
**Then** it should:
- ✅ Develop personalised concept ontology
- ✅ Understand my specific terminology
- ✅ Map relationships between my concepts
- ✅ Use ontology to improve search and suggestions

**Test Coverage**: `tests/integration/test_personal_ontology.py`

---

### Temporal Features

#### AC-008: Timeline Views (v0.4)
**Given** notes spanning months or years
**When** I want to see idea evolution
**Then** the system should:
- ✅ Provide timeline visualisation of notes
- ✅ Show how ideas developed over time
- ✅ Filter timeline by topic or tag
- ✅ Jump to specific time periods

**Test Coverage**: `tests/integration/test_timeline_views.py`

---

#### AC-009: Temporal Queries (v0.4)
**Given** timestamped notes
**When** I ask temporal questions
**Then** the system should answer queries like:
- ✅ "When did I first consider this hypothesis?"
- ✅ "What were my concerns about methodology X in 2023?"
- ✅ "How has my thinking on Y evolved?"
- ✅ "What was I working on last March?"

**Test Coverage**: `tests/e2e/test_temporal_queries.py`

**Success Metric**: 85%+ accuracy on temporal query dataset

---

#### AC-010: Insight Digests (v0.5)
**Given** accumulated notes over time
**When** I want to review past insights
**Then** the system should:
- ✅ Offer daily digest of related past insights
- ✅ Provide weekly summaries of note activity
- ✅ Suggest relevant old notes for current work
- ✅ Highlight forgotten connections

**Test Coverage**: `tests/integration/test_insight_digests.py`

---

### Citation & Reference Management

#### AC-011: Smart Citations for Personal Notes (v0.3)
**Given** personal notes linked to sources
**When** I reference my notes
**Then** the system should:
- ✅ Create citations linking notes to source materials
- ✅ Use customisable citation formats
- ✅ Support informal citation styles
- ✅ Maintain citation integrity

**Test Coverage**: `tests/unit/test_personal_citations.py`

---

#### AC-012: Informal Citation Styles (v0.3)
**Given** informal note-taking
**When** I reference sources
**Then** the system should support citations like:
- ✅ Meeting references: "Meeting with Dr X, March 2024"
- ✅ Conference notes: "CONF2024 keynote discussion"
- ✅ Personal observations: "Observation 2024-03-15, 14:30"
- ✅ Conversation references: "Discussion with Y about Z"

**Test Coverage**: `tests/unit/test_informal_citations.py`

---

### Self-Learning Capabilities

#### AC-013: Organisation Pattern Learning (v0.4)
**Given** my note-taking habits
**When** the system observes my behaviour
**Then** it should learn:
- ✅ My tagging patterns and preferences
- ✅ My folder/category structures
- ✅ My linking preferences
- ✅ How I organise different types of notes

**Test Coverage**: `tests/integration/test_organisation_learning.py`

---

#### AC-014: Predictive Pre-fetching (v0.5)
**Given** historical access patterns
**When** I start working
**Then** the system should predict and pre-fetch:
- ✅ Relevant notes based on time of day
- ✅ Notes related to current project context
- ✅ Notes historically accessed together
- ✅ Recently modified related notes

**Test Coverage**: `tests/integration/test_predictive_prefetch.py`

**Success Metric**: 60%+ accuracy in predicted notes being accessed

---

#### AC-015: Insight Connection Memory (v0.5)
**Given** historical insight combinations
**When** certain notes led to breakthroughs
**Then** the system should:
- ✅ Remember which information combinations led to insights
- ✅ Proactively suggest related content
- ✅ Recreate conditions that sparked past insights
- ✅ Learn what connections are valuable to me

**Test Coverage**: `tests/integration/test_insight_connections.py`

---

### Security & Privacy

#### AC-016: Encryption (v0.3)
**Given** sensitive personal information
**When** storing notes
**Then** the system should:
- ✅ Implement full-text encryption
- ✅ Use local key management (no cloud keys)
- ✅ Encrypt at rest
- ✅ Support encrypted search

**Test Coverage**: `tests/security/test_encryption.py`

**Success Metric**: Zero data breaches or privacy violations

---

#### AC-017: Data Isolation (v0.1)
**Given** privacy requirements
**When** operating
**Then** the system must ensure:
- ✅ Complete isolation from external services
- ✅ No data transmission to internet
- ✅ Local-only storage
- ✅ Auditable data access

**Test Coverage**: `tests/security/test_data_isolation.py`

---

#### AC-018: Secure Backup (v0.4)
**Given** valuable personal knowledge
**When** I want to backup
**Then** the system should:
- ✅ Provide encrypted backup options
- ✅ Support local backup (external drive)
- ✅ Enable backup verification
- ✅ Support restore from backup

**Test Coverage**: `tests/integration/test_backup_restore.py`

---

## Technical Constraints

### Platform Requirements (v1.0)
- ✅ Operates entirely offline
- ✅ Uses local LLM inference
- ✅ No cloud dependencies
- ✅ All processing on local machine

### Privacy Requirements
- ✅ Full-text encryption for sensitive notes
- ✅ Local key management
- ✅ No telemetry or analytics
- ✅ Complete data ownership

### Performance Requirements
- ✅ Note capture latency < 100ms (v0.1)
- ✅ Search response < 2 seconds (v0.2)
- ✅ Timeline rendering < 1 second for 1000 notes (v0.4)

---

## Success Metrics

### Quantitative
- **Note retrieval accuracy**: > 95%
- **Search response time**: < 2 seconds average
- **Capture latency**: < 100ms
- **Zero data breaches**: 100% privacy maintained
- **Temporal query accuracy**: > 85%

### Qualitative
- **Increase in rediscovered insights**: > 40%
- **Successful thought capture**: > 90% of user's informal thoughts
- **User satisfaction**: 4.5+ / 5 for knowledge organisation
- **Privacy confidence**: 5 / 5 for data security

---

## Feature Roadmap

### v0.1 - MVP (Weeks 1-3)
**Completion**: 25% of US-002

**Features**:
- ✅ Basic text note capture
- ✅ Simple note search
- ✅ Vault separation from research library
- ✅ Local-only storage

**Acceptance Criteria**: AC-001 (basic), AC-005, AC-017

---

### v0.2 - Document Normalisation (Weeks 4-7)
**Completion**: 40% of US-002

**Features**:
- ✅ Markdown support
- ✅ Improved search quality
- ✅ Tagging system
- ✅ Note organisation

**Acceptance Criteria**: AC-002

---

### v0.3 - Personal Memory & Personas (Weeks 8-11)
**Completion**: 65% of US-002

**Features**:
- ✅ LaTeX equations
- ✅ Private annotations
- ✅ Auto-linking to research
- ✅ Theme identification
- ✅ Smart citations
- ✅ Informal citation styles
- ✅ Encryption

**Acceptance Criteria**: AC-002 (LaTeX), AC-003, AC-004, AC-006, AC-011, AC-012, AC-016

---

### v0.4 - Advanced Features (Weeks 12-15)
**Completion**: 80% of US-002

**Features**:
- ✅ Personalised ontology
- ✅ Timeline views
- ✅ Temporal queries
- ✅ Organisation pattern learning
- ✅ Secure backup

**Acceptance Criteria**: AC-007, AC-008, AC-009, AC-013, AC-018

---

### v0.5 - Pre-production (Weeks 16-18)
**Completion**: 90% of US-002

**Features**:
- ✅ Insight digests
- ✅ Predictive pre-fetching
- ✅ Insight connection memory
- ✅ Advanced temporal features

**Acceptance Criteria**: AC-010, AC-014, AC-015

---

### v1.0 - Production (Weeks 19-20)
**Completion**: 100% of US-002

**Features**:
- ✅ Production-grade performance
- ✅ Comprehensive testing
- ✅ Full security audit
- ✅ Complete documentation

**Acceptance Criteria**: All AC-001 through AC-018 complete

---

## Related Personas

### Primary: Researcher
**Definition**: [Researcher Persona](../../core-concepts/personal-memory-personas.md#researcher-persona)

**Use Case**: Personal research notes, hypotheses, observations

**Configuration**:
```yaml
persona: researcher
vault_settings:
  separation: strict
  encryption: enabled
  auto_linking: enabled
memory_scope: persona_only
```

### Secondary: Casual
**Definition**: [Casual Persona](../../core-concepts/personal-memory-personas.md#casual-persona)

**Use Case**: Personal knowledge management, meeting notes, ideas

**Configuration**:
```yaml
persona: casual
vault_settings:
  separation: relaxed
  encryption: optional
  auto_linking: enabled
response_style: conversational
```

---

## Cross-References

### Implementation
- [Personal Memory & Personas](../../core-concepts/personal-memory-personas.md)
- [Temporal Memory (Kuzu)](../../core-concepts/personal-memory-personas.md#temporal-memory-kuzu)
- [Privacy & Security](../../core-concepts/personal-memory-personas.md#privacy-security)

### Architecture
- [Memory Coordinator](../../core-concepts/personal-memory-personas.md#memory-coordinator)
- [Encryption Strategy](../../architecture/README.md#encryption)

### Testing
- [Security Testing](../../core-concepts/testing-strategy.md#safety-and-security-testing)
- [Privacy Testing](../../core-concepts/testing-strategy.md#pii-detection)

---

## Implementation Notes

### Technical Approach

**Vault Separation**:
```python
class VaultManager:
    """Manage separate vaults with isolation"""

    def __init__(self, base_path: Path):
        self.research_vault = base_path / "research"
        self.personal_vault = base_path / "personal"

    def query(self, text: str, vault: str = "research", cross_vault: bool = False):
        """Query with vault isolation"""
        if cross_vault:
            return self._query_all_vaults(text)
        else:
            return self._query_single_vault(text, vault)
```

**Temporal Queries using Kuzu**:
```python
class TemporalNoteGraph:
    """Graph-based temporal note relationships"""

    def query_evolution(self, concept: str, start_date: date, end_date: date):
        """
        Query how thinking evolved on a concept

        Uses Kuzu graph DB to traverse temporal edges
        """
        cypher = """
        MATCH (n:Note)-[r:EVOLVED_INTO]->(m:Note)
        WHERE n.concept = $concept
          AND n.created >= $start
          AND n.created <= $end
        RETURN n, r, m
        ORDER BY n.created
        """
        return self.graph.execute(cypher, params={
            'concept': concept,
            'start': start_date,
            'end': end_date
        })
```

**Encryption**:
```python
class NoteEncryption:
    """Encrypt sensitive notes"""

    def __init__(self, key_path: Path):
        self.key = self._load_or_generate_key(key_path)
        self.cipher = Fernet(self.key)

    def encrypt_note(self, content: str) -> bytes:
        """Encrypt note content"""
        return self.cipher.encrypt(content.encode())

    def decrypt_note(self, encrypted: bytes) -> str:
        """Decrypt note content"""
        return self.cipher.decrypt(encrypted).decode()
```

---

## Dependencies

### External
- **Kuzu**: Temporal graph database
- **cryptography**: Encryption library
- **SQLite**: Note metadata storage
- **ChromaDB**: Semantic search

### Internal
- Memory system (core component)
- Persona system (v0.3)
- Research vault (US-001)

---

## Risks & Mitigations

### Risk 1: Encryption Performance
**Risk**: Encrypted search may be slow
**Impact**: Medium - User experience
**Mitigation**:
- Benchmark encrypted vs. plaintext search
- Use selective encryption (only sensitive notes)
- Optimise encryption key caching

### Risk 2: Temporal Query Complexity
**Risk**: Complex temporal queries may be difficult to implement
**Impact**: Medium - Advanced feature
**Mitigation**:
- Start with simple temporal queries (v0.4)
- Use Kuzu's built-in temporal support
- Defer complex temporal analytics to v0.5

### Risk 3: Privacy Guarantee
**Risk**: Accidental data leakage to internet
**Impact**: High - Core privacy promise
**Mitigation**:
- Network traffic monitoring in tests
- Firewall validation
- Code audit for external calls
- User-configurable network blocking

---

## Change History

| Date | Version | Changes | Author |
|------|---------|---------|--------|
| 2025-11-09 | 1.1 | Enhanced with version mapping, persona links, detailed AC | Claude |
| 2025-11-09 | 1.0 | Original user story created | User |

---

**Status:** ✅ Active
**Next Review**: v0.3 milestone
**Owner**: Product/Requirements
