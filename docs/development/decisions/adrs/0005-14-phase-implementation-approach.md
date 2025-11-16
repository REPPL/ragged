# ADR-0005: 14-Phase Implementation Approach

**Status:** Accepted

**Date:** 2025-11-09

**Deciders:** Development Team

**Area:** Development Process

## Context

Needed a structured approach to implement a complete RAG system from scratch with clear milestones and deliverables. Building a RAG system from the ground up is complex, with many interdependencies between components. Without a clear structure, it's easy to lose track of progress, introduce bugs through rushed development, or create incomplete features.

## Decision

Implement v0.1 in 14 distinct phases:

**Foundation** (Phase 1):
- Core infrastructure

**Core Features** (Phases 2-8):
- Phase 2: Configuration management
- Phase 3: Document loaders
- Phase 4: Embedding generation
- Phase 5: Vector storage
- Phase 6: Chunking system
- Phase 7: Retrieval implementation
- Phase 8: CLI interface

**Quality & Release** (Phases 9-14):
- Phase 9: Integration testing
- Phase 10: Unit test coverage
- Phase 11: Security audit
- Phase 12: Documentation
- Phase 13: Performance optimisation
- Phase 14: Release preparation

## Rationale

- **Incremental Progress**: Each phase delivers working functionality that can be tested and validated
- **Clear Dependencies**: Each phase builds on previous ones, making the development path obvious
- **Testability**: Discrete phases enable focused testing at each stage
- **Tracking**: Easy to measure progress (e.g., "7/14 phases complete") and estimate remaining work
- **Risk Management**: Issues are contained within phases, preventing cascade failures
- **Parallelisation**: Some phases (e.g., 10, 11) can proceed in parallel once core is stable
- **Team Coordination**: Multiple developers can work on different phases simultaneously

## Alternatives Considered

### 1. Monolithic Development

Build everything, then test at the end.

**Rejected because:**
- Too risky - bugs discovered late are expensive to fix
- Hard to track progress - "90% done" syndrome
- No intermediate milestones for validation
- Integration issues discovered too late

### 2. Feature-Based Increments

One complete feature at a time (e.g., "PDF ingestion", "embedding", "query").

**Rejected because:**
- Doesn't match natural system architecture
- Features have heavy interdependencies
- Harder to parallelise work
- Less clear what "complete" means for a feature

### 3. Strict TDD

Test-first for absolutely everything.

**Partially adopted:**
- Hybrid TDD approach chosen
- Tests for core logic and algorithms
- Integration tests for workflows
- But not test-first for exploratory code

## Consequences

### Positive

- Clear roadmap and progress tracking
- Easier to onboard collaborators (they can see which phase we're in)
- Manageable scope per phase (typically 4-8 hours each)
- Natural git commit points at phase boundaries
- Early testing catches issues before they compound
- Predictable development velocity

### Negative

- Some artificial boundaries (e.g., Phase 5 vs 6 could be combined)
- Overhead in phase documentation and planning
- Temptation to skip phases or combine them under time pressure
- May feel slow compared to rapid prototyping

### Neutral

- Requires discipline to stick to phase plan
- Phase granularity may not suit all team sizes

## Implementation

Each phase followed this pattern:
1. Define phase objectives and success criteria
2. Implement minimum code to meet objectives
3. Write tests for phase deliverables
4. Document phase completion
5. Review before moving to next phase

Actual implementation matched plan closely, with minor adjustments:
- Phase 10 and 11 were partially parallelised
- Some phases took slightly longer than estimated
- Overall approach proved valuable for incremental delivery

## Lessons Learned

**For v0.2 and beyond:**
- Consider fewer, larger phases (8-10 instead of 14) to reduce overhead
- Phase boundaries should align with natural testing points
- Keep phases small enough to complete in 4-8 hours
- Document phase completion criteria upfront
- Allow flexibility to adjust phases based on discoveries

**What worked well:**
- Incremental progress was motivating
- Easy to track completion percentage
- Natural points for git commits and documentation
- Parallel work on testing phases

**What could improve:**
- Some phase boundaries felt artificial
- Documentation overhead was significant
- Fewer phases with larger scope might be more efficient

## Related

- [v0.1 Implementation Summary](../../implementations/version/v0.1/summary.md)
- [Development Methodology](../../process/methodology/README.md)
- [Time Tracking for v0.1](../../process/time-logs/version/v0.1/v0.1.0-time-log.md)
