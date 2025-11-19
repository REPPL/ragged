# Workflow Tests

**Purpose:** Test **end-to-end user scenarios** from start to finish.

**Pattern:** Complete user journeys that validate the entire system working together.

---

## What Belongs Here

✅ **Complete user journeys** - From setup to achieving a goal
✅ **Multi-step scenarios** - Involving multiple commands/features
✅ **Real-world use cases** - Actual user workflows
✅ **Integration scenarios** - Multiple components working together

❌ **Single-feature tests** - Use `version/` directory
❌ **Critical path validation** - Use `regression/` directory
❌ **Performance measurement** - Use `performance/` directory

---

## Test Coverage

### 1. New User Onboarding (`test_new_user_onboarding.py`)

**Scenario:** First-time user experience from installation to first query.

**Steps:**
1. Fresh ragged installation
2. Configuration setup (models, paths)
3. Health check (verify services)
4. Add first document
5. Execute first query
6. Validate response quality

**Success Criteria:**
- Complete workflow in < 10 minutes
- Clear error messages if services unavailable
- Successful query with relevant results

### 2. Document Lifecycle (`test_document_lifecycle.py`)

**Scenario:** Full document management from addition to deletion.

**Steps:**
1. Add document to system
2. Verify document appears in list
3. Query to retrieve document
4. Update document metadata
5. Search with metadata filters
6. Delete document
7. Verify document removed

**Success Criteria:**
- All CRUD operations succeed
- Metadata persists correctly
- Search filters work accurately
- Clean deletion (no orphaned data)

### 3. Query Workflows (`test_query_workflows.py`)

**Scenario:** Advanced query features and history management.

**Steps:**
1. Execute simple query
2. Execute query with metadata filters
3. Review query history
4. Replay historical query
5. Search query history
6. Clear query history

**Success Criteria:**
- All query types return relevant results
- History persists correctly
- Replay produces identical results
- History search works accurately

### 4. Backup & Restore (`test_backup_restore.py`)

**Scenario:** Data export, system clear, and import recovery.

**Steps:**
1. Add multiple documents
2. Execute several queries (create history)
3. Export all data (documents + metadata)
4. Clear entire system
5. Verify system is empty
6. Import backed-up data
7. Verify all documents restored
8. Verify query history restored

**Success Criteria:**
- Export includes all data
- Import fully restores system state
- No data loss during export/import
- System functional after restore

---

## pytest Markers

All workflow tests should use these markers:

```python
import pytest

@pytest.mark.workflow
@pytest.mark.requires_ollama
@pytest.mark.requires_chromadb
@pytest.mark.slow
def test_new_user_onboarding():
    """Test complete first-time user experience"""
    pass
```

---

## Running Tests

### Run all workflow tests

```bash
pytest scripts/manual_tests/workflows/
```

### Run specific workflow

```bash
pytest scripts/manual_tests/workflows/test_new_user_onboarding.py
```

### Run workflows excluding slow tests

```bash
pytest scripts/manual_tests/workflows/ -m 'workflow and not slow'
```

---

## Workflow Execution Times

| Workflow | Estimated Time | Complexity |
|----------|----------------|------------|
| New User Onboarding | 5-10 min | Low |
| Document Lifecycle | 3-5 min | Medium |
| Query Workflows | 5-8 min | Medium |
| Backup & Restore | 8-12 min | High |

**Total:** ~25-35 minutes for complete workflow validation

---

## Maintenance

### When to Update

- ✅ **New user-facing features** added
- ✅ **User workflows change** significantly
- ✅ **New use cases** identified
- ✅ **Integration points** modified

### How to Update

1. Add new workflow tests for new user scenarios
2. Update existing workflows if steps change
3. Document expected execution times
4. Ensure workflows remain realistic (avoid artificial scenarios)

---

## Creating New Workflow Tests

### Template

```python
import pytest

@pytest.mark.workflow
@pytest.mark.requires_ollama
@pytest.mark.requires_chromadb
def test_my_workflow():
    """
    Scenario: [Describe the user scenario]

    Steps:
    1. [First step]
    2. [Second step]
    3. ...

    Success Criteria:
    - [Criterion 1]
    - [Criterion 2]
    """
    # Setup

    # Step 1

    # Step 2

    # Assertions

    # Cleanup
```

---

## Related Documentation

- [Version Tests](../version/README.md) - Feature-specific tests
- [Regression Tests](../regression/README.md) - Critical path validation
- [Interactive Checklists](../interactive/README.md) - Manual validation steps
- [Manual Test Plans](../../../docs/development/process/testing/manual/) - Test documentation

---

**Maintained By:** ragged development team
