# Ragged v0.2.5 - Split into Sub-Versions

**Status:** Split

**Note:** This version has been split into three smaller, more focused versions for efficient implementation.

---

## Overview

The original v0.2.5 roadmap contained 16 issues totalling 40-50 hours. To enable more focused, token-efficient implementation sessions, this has been split into three priority-based versions:

---

## Split Versions

### v0.2.3 - Critical Bugs (P0)
**Total Hours:** 12-15 hours
**Status:** Planned
**Priority:** P0 - Must complete first

**Issues:**
- BUG-001: API endpoints non-functional (blocks Web UI)
- BUG-002: Logger undefined in settings.py
- BUG-003: Zero test coverage for new modules (606 lines)

**See:** [v0.2.3/README.md](../v0.2.3/README.md)

---

### v0.2.4 - High Priority Bugs (P1)
**Total Hours:** 20-25 hours
**Status:** Planned
**Priority:** P1 - Complete after v0.2.3

**Issues:**
- BUG-004: Inconsistent error handling
- BUG-005: Path handling edge cases
- BUG-006: Memory leaks in batch processing
- BUG-007: ChromaDB metadata type restrictions
- BUG-008: Incomplete hybrid retrieval integration
- BUG-009: Few-shot examples unused
- BUG-010: Duplicate detection incomplete
- BUG-011: Page tracking edge cases

**See:** [v0.2.4/README.md](../v0.2.4/README.md)

---

### v0.2.6 - Quality Improvements (P2)
**Total Hours:** 12-19 hours
**Status:** Planned
**Priority:** P2 - Complete after v0.2.4

**Issues:**
- QUALITY-001: Type hint coverage
- QUALITY-002: Docstring completeness
- QUALITY-003: TODO comments cleanup
- QUALITY-004: Code duplication
- QUALITY-005: Magic numbers

**See:** [v0.2.6/README.md](../v0.2.6/README.md)

---

## Implementation Order

1. **v0.2.3** (P0 Critical) - Blocks functionality
2. **v0.2.4** (P1 High Priority) - Significant quality impact
3. **v0.2.6** (P2 Quality) - Maintainability improvements

Each version is sized for 1-2 focused implementation sessions with clear commit boundaries.

---

## Why Split?

**Token Efficiency:** Smaller versions fit better within AI context windows, enabling more focused sessions without running out of tokens.

**Clearer Priorities:** Critical bugs fixed first, then high priority, then quality improvements.

**Better Commits:** Each sub-version produces a clean, reviewable commit focused on specific improvements.

**Parallel Work:** Different priority levels could theoretically be worked on by different contributors.

---

## Combined Success Criteria

After completing all three split versions (v0.2.3 + v0.2.4 + v0.2.6):

**Functionality:**
- ✅ Web UI fully functional
- ✅ All critical bugs resolved
- ✅ Zero crashes on valid inputs

**Quality:**
- ✅ Test coverage ≥80%
- ✅ Error handling consistent
- ✅ Code quality improved
- ✅ No technical debt remaining

**Testing:**
- ✅ All automated tests pass
- ✅ Manual testing completed
- ✅ No regressions

---

**Last Updated:** 2025-11-12

**Status:** Split into v0.2.3, v0.2.4, v0.2.6

**Next Version:** v0.2.7 (UX & Performance improvements)
