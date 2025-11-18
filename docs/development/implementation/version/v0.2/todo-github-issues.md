# GitHub Issues for Deferred TODOs (v0.2.5)

**Created**: 2025-11-17
**Context**: v0.2.5 QUALITY-009 - TODO cleanup Part 3

---

## Summary

During v0.2.5 development, comprehensive TODO cleanup was performed. The following 2 TODOs remain in the codebase as legitimate future enhancements that should be tracked as GitHub issues.

---

## Issue 1: Implement Contextual Overlap Calculation

**Location**: `src/chunking/contextual.py:146`

**Current Code**:
```python
overlap_with_previous=0,  # TODO: Calculate actual overlap
```

**Description**:
The contextual chunker currently sets `overlap_with_previous` to 0 for all chunks. This should be enhanced to calculate the actual token/character overlap between consecutive chunks to provide accurate metadata.

**Rationale**:
- Accurate overlap information is useful for debugging chunking behaviour
- Helps users understand how chunks relate to each other
- Enables better quality assessment of chunking strategies

**Priority**: Low (Nice-to-have enhancement)

**Estimated Effort**: 2-4 hours

**Related**:
- Connected to v0.2.5 TODO-023 (QUALITY-011 - Contextual overlap)
- Part of chunking quality improvements planned for v0.2.7

**Suggested Labels**: `enhancement`, `chunking`, `quality`, `good-first-issue`

**Suggested Milestone**: v0.2.7

---

## Issue 2: Implement Token-Based Context Truncation

**Location**: `src/chunking/contextual.py:267`

**Current Code**:
```python
# TODO: Implement token-based truncation if needed
# For now, return full context
return full_context
```

**Description**:
The `_format_context_for_prompt()` method currently returns the full context from all retrieved chunks without truncation. For LLMs with context limits, this could cause issues when many chunks are retrieved.

**Rationale**:
- Prevents context overflow for LLMs with token limits
- Enables better control over prompt construction
- Allows prioritisation of most relevant context

**Proposed Solution**:
1. Add configurable `max_context_tokens` parameter
2. Implement token counting for context
3. Truncate from least relevant chunks first when limit exceeded
4. Add warning logging when truncation occurs

**Priority**: Medium (Important for production use)

**Estimated Effort**: 4-6 hours

**Related**:
- Part of prompt optimisation planned for v0.2.7
- Relates to LLM integration improvements

**Suggested Labels**: `enhancement`, `llm-integration`, `prompt-engineering`

**Suggested Milestone**: v0.2.7

---

## Action Items

**For Project Maintainer**:
1. Create GitHub issue for "Implement Contextual Overlap Calculation"
2. Create GitHub issue for "Implement Token-Based Context Truncation"
3. Add appropriate labels and milestones
4. Consider adding to v0.2.7 Session 4 (Chunking/query optimisation)

**After Issues Created**:
1. Update TODO comments in code to reference GitHub issue numbers
2. Remove this document or archive it

---

## Related Documentation

- [v0.2.5 Roadmap](../../roadmap/version/v0.2.5/README.md) - QUALITY-009
- [v0.2.7 Planning](../../planning/version/v0.2/v0.2.7-design.md) - Future enhancements
- [Chunking ADR](../../decisions/adrs/) - Contextual chunking decisions

---

**License**: GPL-3.0
