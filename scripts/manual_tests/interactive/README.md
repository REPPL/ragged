# Interactive Checklists

**Purpose:** Manual validation checklists for UI, error scenarios, and cross-platform testing.

**Pattern:** Step-by-step checklists requiring human verification (not automated).

---

## What Belongs Here

✅ **UI validation** - Visual/interactive element testing
✅ **Error scenario testing** - Edge cases requiring human judgment
✅ **Cross-platform validation** - macOS/Linux/Windows compatibility
✅ **Usability testing** - User experience evaluation

❌ **Automated tests** - Use other directories (version/, regression/, workflows/)
❌ **Performance benchmarks** - Use `performance/` directory
❌ **Feature tests** - Use `version/` directory

---

## Checklists

### 1. UI Validation (`ui_validation.md`)

**Purpose:** Manual validation of Gradio web interface.

**Sections:**
- Document upload interface
- Query input and result display
- Source citation rendering
- Configuration panel
- Error message display
- Responsive design (desktop/tablet/mobile)
- Accessibility (screen readers, keyboard navigation)

**Time:** ~30-45 minutes

### 2. CLI Features (`cli_features.md`)

**Purpose:** Manual verification of CLI command functionality.

**Sections:**
- Command help text clarity
- Argument parsing edge cases
- Output formatting (JSON/table/CSV/YAML/markdown)
- Shell completion (bash/zsh/fish)
- Error messages and suggestions
- Colour output (ANSI colours)

**Time:** ~20-30 minutes

### 3. Error Scenarios (`error_scenarios.md`)

**Purpose:** Validation of error handling and recovery.

**Sections:**
- Service unavailable (Ollama, ChromaDB)
- Invalid configuration
- Malformed documents
- Network failures
- Disk full scenarios
- Permission errors
- Concurrent operation conflicts

**Time:** ~30-40 minutes

### 4. Cross-Platform (`cross_platform.md`)

**Purpose:** Validation across operating systems.

**Sections:**
- Installation on macOS/Linux/Windows
- Path handling (Unix vs Windows paths)
- Shell completion installation
- Docker compatibility
- Dependency installation
- Configuration file locations

**Time:** ~1-2 hours (across all platforms)

---

## How to Use Checklists

### Format

Each checklist uses this format:

```markdown
## Feature: Document Upload

### Test Case 1: Single PDF Upload

**Steps:**
1. Open Gradio UI in browser
2. Click "Upload Document" button
3. Select single PDF file (<10MB)
4. Click "Submit"

**Expected Result:**
- Upload progress indicator appears
- Success message displays after upload
- Document appears in document list
- Document is queryable immediately

**Actual Result:** [Fill in during testing]

**Status:** ☐ Pass ☐ Fail ☐ N/A

**Notes:** [Any observations or issues]

---
```

### Execution

1. Open checklist markdown file
2. Follow steps for each test case
3. Mark checkboxes: ☑ Pass, ☒ Fail, ⊘ N/A
4. Document actual results
5. Add notes for failures or observations
6. Create GitHub issues for failures

### Reporting

After completing checklists:

1. Create test report in `reports/interactive_tests_YYYY-MM-DD.md`
2. Summarise pass/fail rates
3. List critical failures
4. Link to GitHub issues

---

## pytest Markers

While these are manual checklists, they can be referenced in automated tests:

```python
@pytest.mark.interactive
@pytest.mark.manual_validation_required
def test_ui_validation():
    """
    This test requires manual validation.
    See: scripts/manual_tests/interactive/ui_validation.md
    """
    pytest.skip("Manual validation required - see checklist")
```

---

## Maintenance

### When to Update

- ✅ **New UI features** added
- ✅ **CLI commands** added or modified
- ✅ **New error scenarios** identified
- ✅ **Platform support** changes

### How to Update

1. Add new test cases to relevant checklist
2. Update expected results if behaviour changes
3. Mark deprecated test cases as N/A
4. Update time estimates

---

## Checklist Status

| Checklist | Last Updated | Coverage | Time Estimate |
|-----------|--------------|----------|---------------|
| UI Validation | TBD | Gradio interface | 30-45 min |
| CLI Features | TBD | All CLI commands | 20-30 min |
| Error Scenarios | TBD | Edge cases | 30-40 min |
| Cross-Platform | TBD | macOS/Linux/Windows | 1-2 hours |

---

## Related Documentation

- [Gradio UI](../../../docs/guides/web-interface.md) - Web interface documentation
- [CLI Reference](../../../docs/reference/cli-commands.md) - CLI command documentation
- [Version Tests](../version/README.md) - Automated version tests
- [Workflow Tests](../workflows/README.md) - End-to-end scenarios

---

**Maintained By:** ragged development team
