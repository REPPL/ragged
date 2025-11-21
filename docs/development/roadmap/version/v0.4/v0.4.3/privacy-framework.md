# Privacy Framework for v0.4.3 Memory System

**Purpose**: Define comprehensive privacy validation framework and user privacy controls for the personal memory system.

**Foundation**: Builds on v0.2.11 privacy infrastructure (encryption, PII detection, data lifecycle, GDPR toolkit).

---

## Overview

The v0.4.3 memory system introduces **behaviour data collection**—the most privacy-sensitive data type in ragged. This framework ensures users have complete control and visibility over their personal data.

**Core Principle**: **Privacy by Design** - Privacy built into system architecture, not added as an afterthought.

---

## Privacy Validation Framework

### 1. Data Minimisation

**Principle**: Collect only data necessary for memory functionality.

#### What We Collect (Justified)

**Explicitly Collected** (with clear purpose):
- **Persona names/descriptions**: Required for context switching (user-provided)
- **Focus areas**: Required for personalised ranking (user-provided)
- **Active projects**: Required for context awareness (user-provided)

**Implicitly Collected** (requires justification):
- **Query text**: Required for memory recall, topic extraction
  - *Mitigation*: Optional PII redaction (v0.2.11)
  - *User control*: Can disable, delete, export
- **Query timestamps**: Required for temporal analysis
  - *Purpose*: Understand usage patterns, enable timeline queries
  - *User control*: Can delete time ranges
- **Retrieved document IDs**: Required for relevance learning
  - *Purpose*: Learn which documents helpful for which queries
  - *User control*: Can delete specific interactions
- **Topic extraction**: Required for interest profiling
  - *Purpose*: Personalise ranking based on interests
  - *User control*: Can view, edit, delete topics

**Derived Data** (computed from collected data):
- **Topic interest levels**: Computed from query frequency
- **User-topic relationships**: Graph of interests
- **Topic co-occurrence**: Which topics appear together

#### What We DO NOT Collect

- ❌ **Document content**: Not stored in memory system (only IDs)
- ❌ **IP addresses**: No network calls, no IPs collected
- ❌ **Device fingerprints**: No tracking across devices
- ❌ **Location data**: No geolocation
- ❌ **Browser/system info**: No telemetry
- ❌ **Usage analytics for external services**: Zero telemetry
- ❌ **Crash reports sent externally**: Crashes logged locally only

### 2. Data Lifecycle Management

**Principle**: Users control data from collection through deletion.

#### Collection Phase

**User Awareness**:
- First-run wizard explains memory system
- User opts in (memory disabled by default)
- Clear explanation of what data collected
- Privacy documentation prominent

**Consent Mechanism**:
```bash
# First time running with memory system
$ ragged query "machine learning"
> Memory system available but disabled. Enable memory to get personalised results?
> Memory collects: query text, timestamps, retrieved documents, topics
> All data stored locally in ~/.ragged/memory/ (zero cloud dependencies)
> You can view, edit, or delete your data anytime.
>
> Enable memory? [y/N]: _
```

#### Storage Phase

**Protection Mechanisms**:
- Encryption at rest (v0.2.11 - AES-256-GCM)
- File permissions: 0600 (user-only access)
- No external storage (100% local)
- PII detection and optional redaction (v0.2.11)

**Storage Location** (transparent to user):
```
~/.ragged/memory/
├── profiles/
│   ├── personas.yaml          # Persona definitions (encrypted if sensitive)
│   ├── preferences.db          # User preferences (encrypted)
│   └── user_profile.yaml
├── interactions/
│   ├── queries.db              # Query history (encrypted)
│   └── feedback.db             # User feedback (encrypted)
└── graph/
    └── kuzu_db/                # Knowledge graph
```

#### Usage Phase

**User Visibility**:
- Users can view all collected data anytime
- Memory usage shown in query output (optional)
- Statistics available (`ragged memory stats`)

**Access Control**:
- Only active persona can access its data
- Strict persona isolation
- Plugins require explicit permission (future)

#### Deletion Phase

**User Control**:
- Delete specific interactions
- Delete date ranges
- Delete all data for persona
- Permanent deletion (no "soft delete")

**Verification**:
- Deletion immediately removes from database
- Vacuum operations to reclaim space
- No residual data in logs or temp files

### 3. User Privacy Controls

**Requirement**: Users must have **complete control** over their personal data.

#### Required Privacy Controls (GDPR Articles 15, 17, 20)

##### Right to Access (GDPR Article 15)

**Implementation**:
```bash
# View all collected data
ragged memory show-all --persona researcher

# View specific interaction
ragged memory show <interaction-id>

# View topics extracted
ragged memory topics --persona researcher

# View timeline
ragged memory timeline --since "-30d"

# View statistics
ragged memory stats --persona researcher
```

**Output Format** (human-readable):
```
Interaction: 7f3a8b2c-4d5e-6f7a-8b9c-0d1e2f3a4b5c
Persona: researcher
Query: "how does RAG work with knowledge graphs?"
Timestamp: 2026-03-15 14:32:18
Retrieved Documents: 3 documents
  - doc_123: "RAG Architecture Overview"
  - doc_456: "Knowledge Graphs in NLP"
  - doc_789: "LEANN: Graph-based Vector Storage"
Topics Extracted: RAG, knowledge graphs, vector storage
Model Used: sentence-transformers/all-MiniLM-L6-v2
Latency: 347ms
Feedback: positive
```

##### Right to Erasure (GDPR Article 17)

**Implementation**:
```bash
# Delete specific interaction
ragged memory delete <interaction-id> --confirm

# Delete date range
ragged memory delete --since "2026-01-01" --until "2026-02-01" --confirm

# Delete all data for persona (keep persona definition)
ragged memory clear --persona researcher --confirm

# Delete persona and all its data
ragged persona delete researcher --confirm
```

**Deletion Guarantees**:
- Immediate removal from databases
- Graph relationships removed
- No soft delete (data permanently gone)
- Database vacuum to reclaim space
- No residual data in logs

**Verification**:
```python
# Post-deletion test
def test_data_deletion_permanent():
    """Verify deleted data cannot be recovered."""
    interaction_id = create_test_interaction()
    delete_interaction(interaction_id)

    # Verify not in database
    assert not interaction_exists(interaction_id)

    # Verify not in graph
    assert not graph_has_node(interaction_id)

    # Verify not in backups (if any)
    assert not in_backup_files(interaction_id)
```

##### Right to Data Portability (GDPR Article 20)

**Implementation**:
```bash
# Export all data in machine-readable format
ragged memory export my-memory.json --persona researcher

# Export specific date range
ragged memory export memory-2026-q1.json --since "2026-01-01" --until "2026-03-31"

# Export in different formats
ragged memory export my-memory.csv --format csv
ragged memory export my-memory.yaml --format yaml
```

**Export Format** (structured JSON):
```json
{
  "metadata": {
    "persona": "researcher",
    "exported_at": "2026-03-15T14:32:18Z",
    "ragged_version": "0.4.4",
    "total_interactions": 1247
  },
  "interactions": [
    {
      "id": "7f3a8b2c-4d5e-6f7a-8b9c-0d1e2f3a4b5c",
      "timestamp": "2026-03-15T14:32:18Z",
      "query": "how does RAG work with knowledge graphs?",
      "retrieved_documents": ["doc_123", "doc_456", "doc_789"],
      "topics": ["RAG", "knowledge graphs", "vector storage"],
      "model_used": "sentence-transformers/all-MiniLM-L6-v2",
      "latency_ms": 347,
      "feedback": "positive"
    }
  ],
  "topics": [
    {
      "name": "RAG",
      "interest_level": 0.87,
      "first_seen": "2026-01-10T09:23:45Z",
      "last_seen": "2026-03-15T14:32:18Z",
      "frequency": 42
    }
  ],
  "graph_relationships": [
    {
      "from": "researcher",
      "to": "RAG",
      "type": "INTERESTED_IN",
      "frequency": 42
    }
  ]
}
```

#### Additional Privacy Controls

##### Disable Memory Collection

**Implementation**:
```bash
# Disable memory for specific persona
ragged memory disable --persona researcher

# Re-enable later
ragged memory enable --persona researcher
```

**Behaviour When Disabled**:
- No new interactions recorded
- Existing memory data retained (user can delete separately)
- Queries still work (no personalisation)
- Clear message: "Memory disabled - no personalisation"

##### PII Redaction (Inherited from v0.2.11)

**Implementation**:
```bash
# Enable automatic PII redaction for queries
ragged config set memory.pii_redaction true

# Review PII detection
ragged memory show <id> --show-redacted
```

**PII Detection** (v0.2.11):
- Email addresses → `[EMAIL]`
- Phone numbers → `[PHONE]`
- Credit card numbers → `[CARD]`
- Social security numbers → `[SSN]`
- IP addresses → `[IP]`
- Names (context-dependent) → `[NAME]`

##### Audit Logging

**Implementation**:
```bash
# View audit log for privacy-sensitive operations
ragged memory audit-log --operations delete,export
```

**Logged Operations**:
- Data exports (timestamp, persona, record count)
- Data deletions (timestamp, persona, interaction IDs)
- Persona switches (timestamp, from, to)
- Memory disable/enable (timestamp, persona)

**Audit Log Storage**:
- Local only: `~/.ragged/memory/audit.log`
- Encrypted at rest
- User can view and delete audit logs

---

## Privacy by Design Principles

### 1. Proactive Not Reactive

**Implementation**:
- Privacy built into architecture from start
- Security audit before implementation
- Privacy impact assessment completed
- Privacy controls designed before features

### 2. Privacy as Default Setting

**Implementation**:
- Memory system **disabled by default**
- User must explicitly enable
- No "dark patterns" to encourage enabling
- Clear privacy documentation before enabling

### 3. Privacy Embedded into Design

**Implementation**:
- Local-only storage (no cloud option)
- Encryption at rest for all sensitive data
- Persona isolation enforced at database level
- No network calls in memory operations

### 4. Full Functionality (Positive-Sum, Not Zero-Sum)

**Implementation**:
- Memory system provides value (personalisation)
- Privacy protection doesn't reduce functionality
- Users get both personalisation and privacy
- No trade-offs required

### 5. End-to-End Security (Full Lifecycle Protection)

**Implementation**:
- Data encrypted from collection to deletion
- Secure key management (system keyring)
- Access controls at every layer
- Audit logging for sensitive operations

### 6. Visibility and Transparency

**Implementation**:
- Users see all collected data
- Clear documentation of data collection
- Privacy policy in plain English
- Source code open (GPL-3.0)

### 7. Respect for User Privacy (User-Centric)

**Implementation**:
- Users control all data (view, edit, delete, export)
- No telemetry or external sharing
- GDPR rights fully supported
- User trust prioritised over features

---

## GDPR Compliance Mapping

### Article 15: Right to Access

**Requirement**: Users can obtain confirmation of data processing and access their data.

**Implementation**:
- ✅ `ragged memory show-all` - View all data
- ✅ `ragged memory show <id>` - View specific interaction
- ✅ `ragged memory topics` - View extracted topics
- ✅ `ragged memory timeline` - View temporal data
- ✅ `ragged memory stats` - View statistics

**Compliance**: Full compliance via CLI commands.

### Article 17: Right to Erasure

**Requirement**: Users can request deletion of their data.

**Implementation**:
- ✅ `ragged memory delete <id>` - Delete specific interaction
- ✅ `ragged memory delete --since/--until` - Delete date range
- ✅ `ragged memory clear` - Delete all persona data
- ✅ `ragged persona delete` - Delete persona and data
- ✅ Permanent deletion (no soft delete, no recovery)

**Compliance**: Full compliance via CLI commands with verification tests.

### Article 20: Right to Data Portability

**Requirement**: Users can receive their data in structured, machine-readable format.

**Implementation**:
- ✅ `ragged memory export` - Export to JSON/CSV/YAML
- ✅ Structured format (see export format above)
- ✅ Machine-readable (JSON schema)
- ✅ Complete data export (all fields)

**Compliance**: Full compliance via export functionality.

### Additional GDPR Requirements

**Article 5: Principles of Data Processing**:
- ✅ Lawfulness, fairness, transparency: Explicit consent, clear documentation
- ✅ Purpose limitation: Data used only for memory/personalisation
- ✅ Data minimisation: Only necessary data collected
- ✅ Accuracy: Users can view and correct data
- ✅ Storage limitation: Users can delete anytime
- ✅ Integrity and confidentiality: Encryption, access controls

**Article 25: Data Protection by Design and by Default**:
- ✅ Privacy by design principles applied (see above)
- ✅ Default to most privacy-friendly settings (memory disabled)
- ✅ Pseudonymisation where possible (persona names, not real names)

---

## Privacy Documentation Requirements

### 1. User-Facing Privacy Documentation

**Location**: `docs/guides/privacy.md`

**Required Sections**:

#### What Data Ragged Collects
- Complete list of collected data
- Purpose for each data type
- Legal basis (consent)

#### Where Your Data Is Stored
- Local storage location (`~/.ragged/memory/`)
- No cloud storage
- Encryption details (for technical users)

#### How to View Your Data
- Step-by-step guide to `ragged memory show-all`
- Examples of viewing specific data

#### How to Delete Your Data
- Step-by-step guide to `ragged memory delete`
- How to delete everything
- Verification that data is deleted

#### How to Export Your Data
- Step-by-step guide to `ragged memory export`
- Explanation of export formats
- How to use exported data

#### How to Disable Memory Collection
- Step-by-step guide to `ragged memory disable`
- What happens when disabled
- How to re-enable

#### Your GDPR Rights
- Plain English explanation of Articles 15, 17, 20
- How ragged supports each right
- How to exercise your rights

#### Privacy by Design
- Explanation of privacy-first architecture
- Why local-only storage
- Why no telemetry

### 2. Developer Privacy Documentation

**Location**: `docs/development/guides/privacy-development.md`

**Required Sections**:

#### Privacy Architecture
- How persona isolation works
- How encryption is applied
- How PII detection works

#### Adding Privacy-Sensitive Features
- Privacy impact assessment checklist
- When to require consent
- How to handle new data types

#### Testing Privacy
- Privacy test scenarios (see [testing-scenarios.md](./testing-scenarios.md))
- How to verify no network calls
- How to verify data locality

#### Privacy Code Review Checklist
- What to look for in code reviews
- Common privacy anti-patterns
- Security considerations

---

## Privacy Validation Checklist

Before v0.4.3 release, verify:

### Data Collection
- [ ] Only necessary data collected (data minimisation)
- [ ] User consent obtained before collection
- [ ] Clear documentation of what is collected
- [ ] PII detection enabled and tested

### Data Storage
- [ ] All sensitive data encrypted at rest
- [ ] File permissions restrictive (0600)
- [ ] No data stored in cloud
- [ ] Storage location documented

### User Controls
- [ ] Users can view all data (Article 15)
- [ ] Users can delete data (Article 17)
- [ ] Users can export data (Article 20)
- [ ] Users can disable collection
- [ ] All controls tested and functional

### Data Protection
- [ ] Encryption verified (AES-256-GCM)
- [ ] Key management secure (system keyring)
- [ ] Access controls enforced
- [ ] Persona isolation verified

### Privacy Testing
- [ ] No network calls during memory operations
- [ ] All data in `~/.ragged/memory/`
- [ ] Cross-persona isolation verified
- [ ] Deletion is permanent (no recovery)
- [ ] Export format validated

### Documentation
- [ ] User privacy guide complete
- [ ] Developer privacy guide complete
- [ ] Privacy policy available
- [ ] GDPR compliance documented

### GDPR Compliance
- [ ] Article 15 (access) implemented
- [ ] Article 17 (erasure) implemented
- [ ] Article 20 (portability) implemented
- [ ] Article 5 principles verified
- [ ] Article 25 (privacy by design) verified

---

## Related Documentation

- [v0.4.3 README](./README.md) - Main implementation roadmap
- [Security Audit Requirements](./security-audit.md) - Security validation
- [Testing Scenarios](./testing-scenarios.md) - Privacy test scenarios
- [v0.2.11 Privacy Infrastructure](../../v0.2/v0.2.11.md) - Foundation (encryption, PII detection, GDPR toolkit)

---
