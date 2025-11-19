# Privacy Testing Scenarios for v0.4.0 Memory System

**Purpose**: Comprehensive privacy test scenarios to validate memory system privacy guarantees.

**Coverage**: Network isolation, data locality, persona isolation, user controls, encryption, PII detection.

---

## Overview

The memory system handles highly sensitive personal data requiring rigorous privacy testing. This document defines comprehensive test scenarios to validate all privacy guarantees.

**Testing Philosophy**: **Verify, don't trust** - Every privacy claim must be validated by automated tests.

---

## Test Scenario Categories

### 1. Network Isolation Tests

**Goal**: Verify memory system makes **zero external network calls**.

#### Scenario 1.1: Memory Operations Have No Network Activity

**Test Implementation**:
```python
import pytest
from tests.fixtures.network_monitor import NetworkMonitor

def test_memory_operations_no_network():
    """Verify no network calls during memory operations."""
    with NetworkMonitor() as monitor:
        # Create persona
        persona = create_persona("researcher", focus="RAG, NLP")

        # Record interactions
        record_interaction(
            persona="researcher",
            query="how does RAG work?",
            retrieved_docs=["doc_1", "doc_2"]
        )

        # Query memory
        interactions = list_interactions(persona="researcher")

        # View topics
        topics = list_topics(persona="researcher")

        # Export data
        export_memory(persona="researcher", output="test_export.json")

        # Delete interaction
        delete_interaction(interactions[0].id)

    # Assert zero network calls
    assert monitor.get_external_calls() == 0, \
        f"Memory operations made {monitor.get_external_calls()} external network calls"
    assert monitor.get_dns_queries() == 0, \
        f"Memory operations made {monitor.get_dns_queries()} DNS queries"
```

**Expected Result**: Test passes with 0 network calls and 0 DNS queries.

**Tools**:
- `NetworkMonitor`: Custom test fixture monitoring all socket operations
- Alternative: Use `pytest-socket` to block all network access

#### Scenario 1.2: Kuzu Graph Database Has No Network Calls

**Test Implementation**:
```python
def test_kuzu_no_network():
    """Verify Kuzu graph operations make no network calls."""
    with NetworkMonitor() as monitor:
        # Initialize graph
        graph = initialize_knowledge_graph()

        # Add nodes
        graph.add_user_node("researcher")
        graph.add_topic_node("RAG", interest_level=0.8)

        # Add relationships
        graph.add_relationship(
            from_node="researcher",
            to_node="RAG",
            rel_type="INTERESTED_IN",
            properties={"frequency": 10}
        )

        # Query graph
        topics = graph.get_user_topics("researcher")

    assert monitor.get_external_calls() == 0
```

**Expected Result**: Test passes with 0 network calls.

#### Scenario 1.3: Memory Disabled Still Makes No Network Calls

**Test Implementation**:
```python
def test_memory_disabled_no_network():
    """Verify disabling memory doesn't trigger network calls."""
    with NetworkMonitor() as monitor:
        # Disable memory
        disable_memory(persona="researcher")

        # Verify status
        status = get_memory_status(persona="researcher")
        assert status.enabled is False

        # Re-enable
        enable_memory(persona="researcher")

    assert monitor.get_external_calls() == 0
```

**Expected Result**: Test passes with 0 network calls.

---

### 2. Data Locality Tests

**Goal**: Verify all memory data stored in `~/.ragged/memory/` with no external storage.

#### Scenario 2.1: All Memory Files in Expected Location

**Test Implementation**:
```python
import os
from pathlib import Path

def test_memory_files_in_expected_location():
    """Verify all memory files in ~/.ragged/memory/."""
    memory_dir = Path.home() / ".ragged" / "memory"

    # Create persona and interactions
    create_persona("researcher")
    record_interaction(persona="researcher", query="test query")

    # Verify directory exists
    assert memory_dir.exists(), "Memory directory not found"

    # Expected files/directories
    expected_paths = [
        memory_dir / "profiles" / "personas.yaml",
        memory_dir / "profiles" / "preferences.db",
        memory_dir / "interactions" / "queries.db",
        memory_dir / "graph" / "kuzu_db"
    ]

    # Verify all expected paths exist
    for path in expected_paths:
        assert path.exists(), f"Expected memory file/dir not found: {path}"

    # Verify no memory data outside ~/.ragged/memory/
    outside_paths = [
        Path("/tmp"),
        Path.home() / ".cache",
        Path.home() / ".local" / "share",
        Path("/var")
    ]

    for outside in outside_paths:
        memory_files = list(outside.rglob("*ragged*memory*"))
        assert len(memory_files) == 0, \
            f"Found memory files outside expected location: {memory_files}"
```

**Expected Result**: All memory files in `~/.ragged/memory/`, none elsewhere.

#### Scenario 2.2: Temp Files Cleaned Up

**Test Implementation**:
```python
def test_no_temp_files_leak():
    """Verify no temporary files containing memory data."""
    import tempfile

    temp_dir = Path(tempfile.gettempdir())

    # Perform memory operations
    create_persona("researcher")
    record_interaction(persona="researcher", query="sensitive query")
    export_memory(persona="researcher", output="export.json")
    delete_persona("researcher")

    # Check for temp files
    temp_memory_files = list(temp_dir.rglob("*ragged*"))
    temp_memory_files += list(temp_dir.rglob("*kuzu*"))
    temp_memory_files += list(temp_dir.rglob("*persona*"))

    assert len(temp_memory_files) == 0, \
        f"Found temporary memory files: {temp_memory_files}"
```

**Expected Result**: No temporary files containing memory data.

#### Scenario 2.3: File Permissions Restrictive

**Test Implementation**:
```python
def test_memory_file_permissions():
    """Verify memory files have restrictive permissions (0600)."""
    memory_dir = Path.home() / ".ragged" / "memory"

    create_persona("researcher")
    record_interaction(persona="researcher", query="test")

    # Check all .db and .yaml files
    sensitive_files = list(memory_dir.rglob("*.db"))
    sensitive_files += list(memory_dir.rglob("*.yaml"))

    for file_path in sensitive_files:
        stat_info = os.stat(file_path)
        mode = stat_info.st_mode & 0o777

        # Should be 0600 (owner read/write only)
        assert mode == 0o600, \
            f"File {file_path} has insecure permissions: {oct(mode)} (expected 0600)"
```

**Expected Result**: All sensitive files have 0600 permissions (owner-only read/write).

---

### 3. Persona Isolation Tests

**Goal**: Verify personas are completely isolated (no data leakage between personas).

#### Scenario 3.1: Personas Cannot See Each Other's Interactions

**Test Implementation**:
```python
def test_persona_isolation_interactions():
    """Verify personas don't see each other's interactions."""
    # Create two personas
    create_persona("researcher", focus="RAG, NLP")
    create_persona("developer", focus="Python, databases")

    # Record interactions for researcher
    researcher_query = "how does RAG work?"
    record_interaction(persona="researcher", query=researcher_query)

    # Record interactions for developer
    developer_query = "best Python ORM for SQLite?"
    record_interaction(persona="developer", query=developer_query)

    # Verify researcher sees only their interactions
    researcher_interactions = list_interactions(persona="researcher")
    assert len(researcher_interactions) == 1
    assert researcher_interactions[0].query == researcher_query
    assert developer_query not in [i.query for i in researcher_interactions]

    # Verify developer sees only their interactions
    developer_interactions = list_interactions(persona="developer")
    assert len(developer_interactions) == 1
    assert developer_interactions[0].query == developer_query
    assert researcher_query not in [i.query for i in developer_interactions]
```

**Expected Result**: Personas see only their own interactions.

#### Scenario 3.2: Personas Cannot See Each Other's Topics

**Test Implementation**:
```python
def test_persona_isolation_topics():
    """Verify personas don't see each other's topics."""
    create_persona("researcher", focus="RAG, NLP")
    create_persona("chef", focus="cooking, recipes")

    # Generate topics for researcher
    record_interaction(persona="researcher", query="retrieval augmented generation")
    record_interaction(persona="researcher", query="natural language processing")

    # Generate topics for chef
    record_interaction(persona="chef", query="best pasta recipe")
    record_interaction(persona="chef", query="how to make pizza dough")

    # Verify researcher sees only AI topics
    researcher_topics = list_topics(persona="researcher")
    researcher_topic_names = [t.name for t in researcher_topics]
    assert "RAG" in researcher_topic_names or "NLP" in researcher_topic_names
    assert "cooking" not in researcher_topic_names
    assert "recipes" not in researcher_topic_names

    # Verify chef sees only cooking topics
    chef_topics = list_topics(persona="chef")
    chef_topic_names = [t.name for t in chef_topics]
    assert "cooking" in chef_topic_names or "recipes" in chef_topic_names
    assert "RAG" not in chef_topic_names
    assert "NLP" not in chef_topic_names
```

**Expected Result**: Personas see only their own topics.

#### Scenario 3.3: Graph Queries Cannot Cross Personas

**Test Implementation**:
```python
def test_persona_isolation_graph():
    """Verify graph queries cannot traverse across personas."""
    graph = initialize_knowledge_graph()

    # Create two personas with topics
    graph.add_user_node("researcher")
    graph.add_topic_node("RAG")
    graph.add_relationship("researcher", "RAG", "INTERESTED_IN", {"frequency": 10})

    graph.add_user_node("chef")
    graph.add_topic_node("cooking")
    graph.add_relationship("chef", "cooking", "INTERESTED_IN", {"frequency": 15})

    # Query researcher's topics
    researcher_topics = graph.get_user_topics("researcher")
    assert "RAG" in researcher_topics
    assert "cooking" not in researcher_topics

    # Query chef's topics
    chef_topics = graph.get_user_topics("chef")
    assert "cooking" in chef_topics
    assert "RAG" not in chef_topics

    # Attempt cross-persona query (should return empty)
    cross_query = graph.get_topics_shared_between("researcher", "chef")
    assert len(cross_query) == 0, "Found shared topics between isolated personas"
```

**Expected Result**: Graph queries cannot find cross-persona data.

---

### 4. User Control Tests

**Goal**: Verify all user privacy controls work correctly (view, delete, export).

#### Scenario 4.1: User Can View All Collected Data

**Test Implementation**:
```python
def test_user_can_view_all_data():
    """Verify user can view all collected data (GDPR Article 15)."""
    create_persona("researcher")

    # Record multiple interactions
    queries = ["query 1", "query 2", "query 3"]
    for query in queries:
        record_interaction(persona="researcher", query=query)

    # View all interactions
    interactions = list_interactions(persona="researcher")
    assert len(interactions) == 3

    # Verify all queries visible
    interaction_queries = [i.query for i in interactions]
    for query in queries:
        assert query in interaction_queries

    # View specific interaction details
    first_interaction = interactions[0]
    details = show_interaction(first_interaction.id)
    assert details.query == "query 1"
    assert details.timestamp is not None
    assert details.persona == "researcher"
```

**Expected Result**: User can view all collected data with full details.

#### Scenario 4.2: User Can Delete Specific Interactions

**Test Implementation**:
```python
def test_user_can_delete_interactions():
    """Verify user can delete interactions (GDPR Article 17)."""
    create_persona("researcher")

    # Record interactions
    interaction_1 = record_interaction(persona="researcher", query="query 1")
    interaction_2 = record_interaction(persona="researcher", query="query 2")
    interaction_3 = record_interaction(persona="researcher", query="query 3")

    # Delete middle interaction
    delete_interaction(interaction_2.id)

    # Verify deleted
    remaining = list_interactions(persona="researcher")
    assert len(remaining) == 2
    remaining_ids = [i.id for i in remaining]
    assert interaction_1.id in remaining_ids
    assert interaction_2.id not in remaining_ids
    assert interaction_3.id in remaining_ids

    # Verify cannot retrieve deleted interaction
    with pytest.raises(InteractionNotFound):
        show_interaction(interaction_2.id)
```

**Expected Result**: Deleted interactions are permanently removed.

#### Scenario 4.3: User Can Delete Date Ranges

**Test Implementation**:
```python
from datetime import datetime, timedelta

def test_user_can_delete_date_range():
    """Verify user can delete date ranges."""
    create_persona("researcher")

    # Record interactions across different dates
    base_date = datetime.now()
    record_interaction(persona="researcher", query="old query 1",
                      timestamp=base_date - timedelta(days=60))
    record_interaction(persona="researcher", query="old query 2",
                      timestamp=base_date - timedelta(days=45))
    record_interaction(persona="researcher", query="recent query",
                      timestamp=base_date - timedelta(days=5))

    # Delete interactions older than 30 days
    delete_interactions_before(
        persona="researcher",
        before=base_date - timedelta(days=30)
    )

    # Verify only recent interaction remains
    remaining = list_interactions(persona="researcher")
    assert len(remaining) == 1
    assert remaining[0].query == "recent query"
```

**Expected Result**: Date range deletion works correctly.

#### Scenario 4.4: User Can Export All Data

**Test Implementation**:
```python
import json

def test_user_can_export_data():
    """Verify user can export data (GDPR Article 20)."""
    create_persona("researcher", focus="RAG, NLP")

    # Record interactions
    record_interaction(persona="researcher", query="query 1")
    record_interaction(persona="researcher", query="query 2")

    # Export data
    export_file = "test_export.json"
    export_memory(persona="researcher", output=export_file)

    # Verify export file exists
    assert Path(export_file).exists()

    # Verify export format
    with open(export_file) as f:
        export_data = json.load(f)

    assert "metadata" in export_data
    assert export_data["metadata"]["persona"] == "researcher"
    assert "interactions" in export_data
    assert len(export_data["interactions"]) == 2
    assert "topics" in export_data

    # Verify all fields present
    interaction = export_data["interactions"][0]
    required_fields = ["id", "timestamp", "query", "persona"]
    for field in required_fields:
        assert field in interaction

    # Cleanup
    Path(export_file).unlink()
```

**Expected Result**: Export file contains all data in structured format.

#### Scenario 4.5: User Can Clear All Persona Data

**Test Implementation**:
```python
def test_user_can_clear_persona_data():
    """Verify user can clear all data for persona."""
    create_persona("researcher")

    # Record multiple interactions
    for i in range(10):
        record_interaction(persona="researcher", query=f"query {i}")

    # Verify data exists
    interactions = list_interactions(persona="researcher")
    assert len(interactions) == 10

    # Clear all data
    clear_memory(persona="researcher")

    # Verify data cleared
    interactions = list_interactions(persona="researcher")
    assert len(interactions) == 0

    # Verify persona definition still exists
    personas = list_personas()
    assert "researcher" in [p.name for p in personas]
```

**Expected Result**: All persona data cleared, persona definition retained.

---

### 5. Encryption Validation Tests

**Goal**: Verify data is encrypted at rest.

#### Scenario 5.1: SQLite Databases Are Encrypted

**Test Implementation**:
```python
def test_sqlite_databases_encrypted():
    """Verify SQLite databases are encrypted at rest."""
    create_persona("researcher")
    record_interaction(persona="researcher", query="sensitive query")

    # Find database files
    memory_dir = Path.home() / ".ragged" / "memory"
    db_files = list(memory_dir.rglob("*.db"))
    assert len(db_files) > 0

    # Attempt to read raw database file
    for db_file in db_files:
        with open(db_file, "rb") as f:
            raw_data = f.read(1024)  # Read first 1KB

        # Encrypted data should not contain plaintext query
        assert b"sensitive query" not in raw_data, \
            f"Found plaintext in encrypted database: {db_file}"

        # Verify SQLite header is encrypted (not "SQLite format 3")
        assert raw_data[:16] != b"SQLite format 3\x00", \
            f"Database not encrypted: {db_file}"
```

**Expected Result**: Database files are encrypted, no plaintext visible.

#### Scenario 5.2: YAML Files with Sensitive Data Are Encrypted

**Test Implementation**:
```python
def test_yaml_files_encrypted():
    """Verify YAML files with sensitive data are encrypted."""
    create_persona("researcher", focus="sensitive focus area")

    # Find YAML files
    memory_dir = Path.home() / ".ragged" / "memory"
    yaml_files = list(memory_dir.rglob("*.yaml"))

    for yaml_file in yaml_files:
        # Check if contains sensitive data marker
        if "personas" in yaml_file.name or "profile" in yaml_file.name:
            with open(yaml_file, "rb") as f:
                raw_data = f.read()

            # Should not contain plaintext focus area
            assert b"sensitive focus area" not in raw_data, \
                f"Found plaintext in YAML file: {yaml_file}"
```

**Expected Result**: YAML files with sensitive data are encrypted.

---

### 6. PII Detection Tests

**Goal**: Verify PII detection works correctly (inherited from v0.2.11).

#### Scenario 6.1: Email Addresses Redacted

**Test Implementation**:
```python
def test_email_pii_redaction():
    """Verify email addresses are redacted."""
    create_persona("researcher")

    # Enable PII redaction
    enable_pii_redaction(persona="researcher")

    # Record interaction with email
    query = "contact me at john.doe@example.com for more info"
    record_interaction(persona="researcher", query=query)

    # Retrieve interaction
    interactions = list_interactions(persona="researcher")
    stored_query = interactions[0].query

    # Verify email redacted
    assert "john.doe@example.com" not in stored_query
    assert "[EMAIL]" in stored_query
```

**Expected Result**: Email addresses replaced with `[EMAIL]`.

#### Scenario 6.2: Phone Numbers Redacted

**Test Implementation**:
```python
def test_phone_pii_redaction():
    """Verify phone numbers are redacted."""
    create_persona("researcher")
    enable_pii_redaction(persona="researcher")

    query = "call me at +1-555-123-4567"
    record_interaction(persona="researcher", query=query)

    interactions = list_interactions(persona="researcher")
    stored_query = interactions[0].query

    assert "555-123-4567" not in stored_query
    assert "[PHONE]" in stored_query
```

**Expected Result**: Phone numbers replaced with `[PHONE]`.

---

## Test Automation Requirements

### CI/CD Integration

**Goal**: All privacy tests must run automatically on every commit.

**Implementation**:
```yaml
# .github/workflows/privacy-tests.yml
name: Privacy Tests

on: [push, pull_request]

jobs:
  privacy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.12'

      - name: Install dependencies
        run: pip install -e ".[dev]"

      - name: Run privacy test suite
        run: pytest tests/privacy/ -v --strict-markers

      - name: Verify zero network calls
        run: pytest tests/privacy/test_network_isolation.py -v

      - name: Verify data locality
        run: pytest tests/privacy/test_data_locality.py -v

      - name: Verify persona isolation
        run: pytest tests/privacy/test_persona_isolation.py -v
```

### Test Coverage Requirements

**Goal**: 100% coverage for privacy-critical code paths.

**Critical Paths** (require 100% coverage):
- Network isolation mechanisms
- Data deletion operations
- Persona isolation logic
- Encryption key handling
- PII detection

**Measurement**:
```bash
pytest tests/privacy/ --cov=ragged/memory --cov-report=html --cov-fail-under=100
```

---

## Manual Testing Checklist

Before v0.4.0 release, manually verify:

### Network Isolation
- [ ] Run memory operations with network monitoring tool (Wireshark, tcpdump)
- [ ] Verify zero external connections
- [ ] Verify zero DNS queries

### Data Locality
- [ ] Check `~/.ragged/memory/` contains all expected files
- [ ] Search `/tmp` for any ragged memory files (should be none)
- [ ] Search system for any memory files outside expected location

### Persona Isolation
- [ ] Create two personas with different topics
- [ ] Verify each persona sees only their data
- [ ] Switch between personas and verify isolation maintained

### User Controls
- [ ] View all data for persona
- [ ] Delete specific interaction and verify removed
- [ ] Export data and verify completeness
- [ ] Clear all data and verify persona still exists

### Encryption
- [ ] Examine raw database files (should not contain plaintext)
- [ ] Verify SQLite header encrypted
- [ ] Verify YAML files encrypted

### PII Detection
- [ ] Record query with email address
- [ ] Verify email redacted to `[EMAIL]`
- [ ] Repeat for phone, credit card, etc.

---

## Related Documentation

- [v0.4.0 README](./README.md) - Main implementation roadmap
- [Security Audit Requirements](./security-audit.md) - Security validation
- [Privacy Framework](./privacy-framework.md) - User privacy controls specification
- [v0.2.11 Privacy Infrastructure](../../v0.2/v0.2.11.md) - Foundation (encryption, PII detection)

---
