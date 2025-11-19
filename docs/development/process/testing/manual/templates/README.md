# Manual Testing Templates

**Purpose:** Reusable templates for manual testing documentation.

---

## Overview

This directory contains template files for creating consistent manual test documentation across ragged versions.

Templates provide standardised structure for:
- Test plans
- Test case formats
- Test result reporting
- Version-specific manual testing

---

## Contents

### Available Templates

- **version-manual-test-template.md** - Standard template for version-specific manual testing
  - Pre-defined test categories
  - Consistent result tracking format
  - Quality gate checklists

---

## Usage

### Creating Version-Specific Test Documentation

1. **Copy the template:**
   ```bash
   cp version-manual-test-template.md ../vX.X/manual-tests.md
   ```

2. **Rename with version number:**
   ```bash
   # Example for v0.3.x:
   cp version-manual-test-template.md ../v0.3/manual-tests.md
   ```

3. **Fill in version-specific details:**
   - Update version number in header
   - Customise test cases for version features
   - Add version-specific quality gates
   - Document test results

4. **Save in parent directory:**
   - Store completed tests in `manual/vX.X/`
   - Keep templates unchanged in `templates/`

---

## Template Structure

All templates follow this structure:

1. **Test Metadata** - Version, date, tester
2. **Test Categories** - Organised by feature area
3. **Test Cases** - Specific scenarios to validate
4. **Results Tracking** - Pass/fail status with notes
5. **Quality Gates** - Release criteria checklist

---

## Best Practices

### When to Use Templates

- ✅ Starting manual testing for a new version
- ✅ Regression testing after major changes
- ✅ Pre-release quality validation
- ✅ User acceptance testing

### Customisation Guidelines

- **DO** add version-specific test cases
- **DO** adapt categories for new features
- **DO** update quality gates for version goals
- **DON'T** remove essential test categories
- **DON'T** modify template structure significantly

### Documentation Standards

- Use British English (behaviour, colour, organise)
- Follow ragged commit message conventions
- Link to relevant roadmap/implementation docs
- Track actual vs expected results clearly

---

## Related Documentation

- [Manual Testing Guide](../) - Manual testing methodology
- [Testing Process](../../) - Overall testing approach
- [Quality Assurance](../../../roadmap/) - Version quality gates

---
