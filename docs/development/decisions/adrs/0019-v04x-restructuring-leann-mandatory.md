# ADR-0019: v0.4.x Roadmap Restructuring - LEANN as Mandatory Core Backend

**Date:** 2025-11-22

**Status:** Accepted

**Deciders:** ragged core team

---

## Context

The original v0.4.x roadmap (10 releases, 195-242 hours) planned LEANN backend integration as **conditional** at v0.4.8, dependent on a storage evaluation decision point at v0.4.5.

During roadmap planning, the following issues were identified:

1. **Scope imbalances**: Three releases (v0.4.3, v0.4.5, v0.4.7) at 35-45 hours each, too large for single releases
2. **Security gap**: Plugin architecture (old v0.4.0) lacked dedicated sandboxing implementation
3. **Architecture incoherence**: Memory system designed for ChromaDB-first with potential retrofit to LEANN was suboptimal
4. **Conditional complexity**: LEANN decision framework added unnecessary uncertainty and migration burden

## Decision

**Restructure v0.4.x from 10 releases to 14 releases** (272-330 hours) with **LEANN as mandatory core backend** implemented **before** the memory system.

### Key Changes

1. **NEW v0.4.0: Plugin Sandboxing & Security** (8-10h)
   - Extracted from original v0.4.0
   - Security-first foundation before any plugins run

2. **LEANN mandatory at v0.4.3** (35-42h, was conditional v0.4.8)
   - Platform-aware implementation (macOS/Linux with graceful fallback to ChromaDB on Windows)
   - Implemented **before** memory system (v0.4.5) for clean architecture

3. **Split heavy releases**:
   - Memory Foundation: Kept as-is (35-40h acceptable for most critical release)
   - Behaviour Learning: Split into v0.4.7 (17-20h) + v0.4.8 (18-20h)
   - Temporal Memory: Expanded to v0.4.10 (37-45h) with multi-file directory

4. **NEW infrastructure releases**:
   - v0.4.11: Backend Migration & Selection Tools (12-18h)
   - v0.4.12: Performance Optimisation & Benchmarking (13-17h)

### New Structure

**Total**: 14 releases, 272-330 hours (+40%)

**Phase 1: Foundation & Security** (v0.4.0-v0.4.4, 98-119h)
- Plugin sandboxing, architecture, multi-backend, LEANN, quality baseline

**Phase 2: Memory System Core** (v0.4.5-v0.4.8, 85-98h)
- Personas, stability, behaviour learning (Parts 1 & 2)

**Phase 3: Advanced Features** (v0.4.9-v0.4.10, 47-57h)
- Refactoring, temporal memory

**Phase 4: Stabilisation** (v0.4.11-v0.4.13, 40-55h)
- Migration tools, performance, production readiness

## Rationale

### Why LEANN Mandatory?

1. **Storage efficiency is core to ragged's value proposition**
   - 97% storage savings aligns with privacy-first, local-first design
   - Enables larger personal knowledge bases on consumer hardware

2. **Cleaner architecture**
   - Memory system designed with LEANN from day one (no migration needed)
   - Backend-agnostic storage via VectorStore interface

3. **Platform-aware is acceptable**
   - macOS/Linux users (majority of target audience) get LEANN automatically
   - Windows users get ChromaDB (fully functional, no features lost)
   - Graceful fallback ensures cross-platform compatibility

4. **Removes decision complexity**
   - No conditional branching in roadmap
   - No storage evaluation instrumentation needed
   - Team can commit to full implementation

### Why Before Memory System?

**Architecture Coherence**: Designing memory for LEANN from the start avoids:
- Dual implementation (ChromaDB version, then LEANN version)
- Migration complexity for memory data
- Potential data loss or corruption during migration
- User confusion about storage backend selection

**Benefits**:
- Memory vectors stored in backend-agnostic format
- Users get storage efficiency immediately (macOS/Linux)
- Zero migration burden for memory data

### Why 14 Releases?

1. **Better scope balance**: Max 37-45h (Temporal, expanded), compared to original 40-45h
2. **Dedicated security release**: v0.4.0 establishes baseline
3. **Infrastructure investment**: Migration and performance deserve dedicated releases
4. **Incremental delivery**: More rollback points, better testing isolation

## Consequences

### Positive

- ✅ Storage efficiency from day one (97% savings on macOS/Linux)
- ✅ Cleaner memory system architecture (multi-backend aware from start)
- ✅ Better scope balance (no 40h+ releases except Temporal)
- ✅ Security-first approach (dedicated sandboxing release)
- ✅ Cross-platform compatibility maintained (Windows via ChromaDB)
- ✅ Migration tools as first-class feature (v0.4.11)

### Negative

- ⚠️ +40% time investment (195-242h → 272-330h)
- ⚠️ Platform-specific builds required (macOS, Linux)
- ⚠️ Windows users don't get storage savings (acceptable trade-off)
- ⚠️ More releases = more overhead (documentation, testing, release management)

### Neutral

- Timeline extends from ~8 months to ~11-12 months at current velocity
- Target completion: Q4 2026 → Q2 2027
- LEANN is architecturally mandatory but runtime optional (based on platform)

## Alternatives Considered

### Alternative 1: Keep LEANN Conditional (Original Plan)
- **Rejected**: Architecture complexity, potential migration burden, decision point overhead

### Alternative 2: LEANN Windows Support
- **Deferred**: Requires C++ Windows build toolchain, increases complexity
- **Future**: Can be added in v0.5.x when LEANN Windows builds available

### Alternative 3: Split Into More Smaller Releases (>14)
- **Rejected**: Overhead of 16-18 releases outweighs benefits
- **Current**: 14 releases provides good balance

## Implementation Notes

- All 14 release specifications created
- Supporting documents updated (README.md, execution-playbook.md, progress-tracker.md)
- Cross-references verified
- Documentation standards maintained (British English, SSOT, directory naming)

## Related Documentation

- [v0.4 Overview](../roadmap/version/v0.4/README.md) - 14-release structure
- [v0.4.3](../roadmap/version/v0.4/v0.4.3.md) - LEANN Backend (platform-aware)
- [v0.4.5](../roadmap/version/v0.4/v0.4.5/README.md) - Memory Foundation (multi-backend)
- [v0.4.11](../roadmap/version/v0.4/v0.4.11.md) - Backend Migration Tools
- [ADR-0015: VectorStore Abstraction](./0015-vectorstore-abstraction.md) - Foundation

---

**Status**: Accepted
