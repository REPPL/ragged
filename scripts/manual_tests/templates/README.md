# Manual Test Templates

**Purpose:** Templates for creating manual tests for new ragged versions.

**Pattern:** Reusable templates with placeholders for quick test creation.

---

## Directory Structure

```
templates/
├── version_test_template/       # Template for version-specific tests
│   ├── README.template.md
│   ├── smoke_test.template.py
│   └── feature_test.template.py
├── docs_template/               # Template for test documentation
│   └── manual-test-plan.template.md
└── create_version_tests.sh      # Automation script
```

---

## Using Templates

### Automated Creation (Recommended)

```bash
# Create tests for new version
./scripts/manual_tests/templates/create_version_tests.sh v0.2.12 "cli,formatting,validation"

# This creates:
# - scripts/manual_tests/version/v0.2.12/
# - docs/development/process/testing/manual/v0.2/v0.2.12-manual-tests.md
# - Updates run_tests.py with new version
```

### Manual Creation

1. **Copy template directory:**
   ```bash
   cp -r scripts/manual_tests/templates/version_test_template/ \
         scripts/manual_tests/version/v0.2.12/
   ```

2. **Rename template files:**
   ```bash
   cd scripts/manual_tests/version/v0.2.12/
   mv README.template.md README.md
   mv smoke_test.template.py smoke_test.py
   mv feature_test.template.py cli_features_test.py
   ```

3. **Replace placeholders:**
   - `{VERSION}` → `v0.2.12`
   - `{DATE}` → `2025-11-20`
   - `{FEATURES}` → List of features (e.g., "CLI enhancements, formatting")
   - `{FEATURE_TAG}` → pytest marker (e.g., "cli", "formatting")
   - `{ROADMAP_LINK}` → Link to roadmap document

4. **Implement tests:**
   - Fill in test cases
   - Add version-specific logic
   - Update feature tags

5. **Create documentation:**
   ```bash
   cp scripts/manual_tests/templates/docs_template/manual-test-plan.template.md \
      docs/development/process/testing/manual/v0.2/v0.2.12-manual-tests.md
   ```

6. **Update documentation placeholders:**
   - Replace `{VERSION}`, `{FEATURES}`, `{DATE}`
   - Add test scenarios
   - Link to executable tests

---

## Template Files

### 1. `version_test_template/README.template.md`

Version-specific test directory README with:
- Version overview
- Features tested
- Feature tags used
- Links to roadmap and implementation docs

**Placeholders:**
- `{VERSION}` - Version number (e.g., v0.2.12)
- `{DATE}` - Date created
- `{FEATURES}` - Feature list
- `{ROADMAP_LINK}` - Path to roadmap
- `{IMPLEMENTATION_LINK}` - Path to implementation docs

### 2. `version_test_template/smoke_test.template.py`

Basic smoke test template with:
- Standard imports
- pytest markers (smoke, version)
- Basic fixture setup
- Placeholder test functions

**Placeholders:**
- `{VERSION}` - Version number
- `{FEATURE_TAG}` - pytest feature marker

### 3. `version_test_template/feature_test.template.py`

Feature-specific test template with:
- Standard imports
- pytest markers (feature, version)
- Feature-specific fixtures
- Placeholder test functions
- Example assertions

**Placeholders:**
- `{VERSION}` - Version number
- `{FEATURE_NAME}` - Feature being tested
- `{FEATURE_TAG}` - pytest feature marker

### 4. `docs_template/manual-test-plan.template.md`

Manual test plan documentation template with:
- Test plan overview
- Feature matrix
- Test scenarios
- Verification checklist
- Known issues section
- Links to executable tests

**Placeholders:**
- `{VERSION}` - Version number
- `{DATE}` - Date created
- `{FEATURES}` - Feature list
- `{FEATURE_MATRIX}` - Table of features and tags
- `{ROADMAP_LINK}` - Path to roadmap
- `{TEST_SCRIPTS_PATH}` - Path to test scripts

---

## Automation Script (`create_version_tests.sh`)

### Usage

```bash
./scripts/manual_tests/templates/create_version_tests.sh <version> <features>

# Arguments:
#   version   - Version number (e.g., v0.2.12)
#   features  - Comma-separated feature tags (e.g., "cli,formatting,validation")

# Example:
./scripts/manual_tests/templates/create_version_tests.sh v0.2.12 "cli,formatting"
```

### What It Does

1. Creates version test directory (`version/v0.2.12/`)
2. Copies and processes templates
3. Replaces all placeholders
4. Creates documentation in `docs/development/process/testing/manual/`
5. Updates `run_tests.py` to include new version
6. Prints next steps

### Example Output

```
✅ Created version test directory: scripts/manual_tests/version/v0.2.12/
✅ Created test files:
   - smoke_test.py
   - cli_features_test.py
   - formatting_features_test.py
✅ Created README.md
✅ Created manual test plan: docs/development/process/testing/manual/v0.2/v0.2.12-manual-tests.md
✅ Updated run_tests.py

Next steps:
1. Implement tests in scripts/manual_tests/version/v0.2.12/
2. Add test scenarios to docs/development/process/testing/manual/v0.2/v0.2.12-manual-tests.md
3. Run tests: pytest scripts/manual_tests/version/v0.2.12/
4. Update roadmap and implementation docs with test links
```

---

## Customising Templates

### Modifying Existing Templates

1. Edit template files in `templates/`
2. Add new placeholders using `{PLACEHOLDER_NAME}` format
3. Update `create_version_tests.sh` to replace new placeholders
4. Test template generation with dummy version

### Creating New Templates

1. Create new template file (e.g., `migration_test.template.py`)
2. Add placeholders
3. Update `create_version_tests.sh` to process new template
4. Document new template in this README

---

## Placeholder Reference

| Placeholder | Description | Example |
|-------------|-------------|---------|
| `{VERSION}` | Version number | `v0.2.12` |
| `{DATE}` | Current date | `2025-11-20` |
| `{FEATURES}` | Feature list | `CLI enhancements, output formatters` |
| `{FEATURE_TAG}` | pytest marker | `cli`, `formatting` |
| `{FEATURE_NAME}` | Human-readable feature name | `CLI Features`, `Output Formatting` |
| `{ROADMAP_LINK}` | Path to roadmap | `../../../docs/development/roadmap/version/v0.2/v0.2.12/` |
| `{IMPLEMENTATION_LINK}` | Path to implementation | `../../../docs/development/implementation/version/v0.2/v0.2.12.md` |
| `{TEST_SCRIPTS_PATH}` | Path to test scripts | `scripts/manual_tests/version/v0.2.12/` |
| `{FEATURE_MATRIX}` | Feature table markdown | Table of features and tags |

---

## Best Practices

### When Creating New Version Tests

1. ✅ **Use automation script** - Ensures consistency
2. ✅ **Follow naming conventions** - `{feature}_test.py` format
3. ✅ **Add comprehensive markers** - version, feature, smoke
4. ✅ **Document expected behaviour** - Clear docstrings
5. ✅ **Link to roadmap** - Traceability to feature specs
6. ✅ **Create test plan docs** - In `docs/development/process/testing/manual/`

### Template Maintenance

1. ✅ **Update templates with patterns** - As testing patterns evolve
2. ✅ **Add common utilities** - Reduce duplication
3. ✅ **Version template changes** - Track template evolution
4. ✅ **Test templates regularly** - Ensure automation works

---

## Related Documentation

- [Version Tests](../version/README.md) - Version-specific test directory
- [Manual Test Plans](../../../docs/development/process/testing/manual/) - Test documentation
- [Roadmap](../../../docs/development/roadmap/README.md) - Feature planning
- [Implementation](../../../docs/development/implementation/README.md) - What was built

---

**Maintained By:** ragged development team
