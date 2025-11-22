# ADR-0018: LEANN Integration Strategy - Early, Platform-Aware Implementation

**Date:** 2025-11-22
**Status:** Accepted (for v0.4.3 implementation)
**Deciders:** ragged development team
**Tags:** architecture, storage, performance, leann, v0.4.3

---

## Context

LEANN (Learned Embedding Approximate Nearest Neighbors) is a graph-based vector storage system that achieves 97% storage savings compared to traditional vector databases while maintaining 90% top-3 recall accuracy.

### Background

**Original Plan**: LEANN as optional backend, decided in v0.4.5 (Behaviour Learning release)
**Revised Plan**: LEANN mandatory in architecture, implemented early in v0.4.3 (Platform-Aware)

### Why This Decision Matters

1. **Storage Impact**: Personal memory system (v0.4.5+) will generate significant vector data
   - Interaction tracking (queries embedded)
   - Topic extraction (semantic search)
   - Document relationships (graph-based connections)
   - Multi-year history (grows indefinitely)

2. **User Experience**: 97% storage savings = difference between usable and impractical
   - ChromaDB: 10K interactions ≈ 2GB storage
   - LEANN: 10K interactions ≈ 60MB storage
   - Over 3 years: ChromaDB ≈ 21GB vs LEANN ≈ 630MB

3. **Platform Reality**: LEANN not available on all platforms
   - macOS: Fully supported (Intel, ARM64)
   - Linux: Supported (x86_64, ARM64 with build-from-source)
   - Windows: Not currently supported (C++ build challenges)

### The Decision Point

**Should we:**
1. Defer LEANN to later release when Windows support ready?
2. Make LEANN optional with user choice?
3. **Implement LEANN early, platform-aware (auto-select backend)?** ← **CHOSEN**

---

## Decision

We will implement LEANN in **v0.4.3** (early in the roadmap) with **platform-aware automatic backend selection**:

- **macOS (Intel, ARM64)**: Use LEANN (97% savings)
- **Linux (x86_64, ARM64)**: Use LEANN (97% savings)
- **Windows**: Use ChromaDB (full compatibility)

**Key Principle**: LEANN is mandatory in architecture, optional at runtime based on platform capabilities.

### Implementation Strategy

```python
class VectorStoreFactory:
    """Platform-aware vector store selection."""

    @staticmethod
    def create_for_platform(path: str, purpose: str = "documents") -> VectorStore:
        """Create appropriate backend for current platform.

        Args:
            path: Storage path
            purpose: "documents" or "memory"

        Returns:
            Platform-appropriate VectorStore implementation
        """
        platform = detect_platform()

        if platform in [Platform.MACOS, Platform.LINUX_X86_64, Platform.LINUX_ARM64]:
            # LEANN supported
            try:
                return LEANNStore(path=path)
            except LEANNNotAvailable:
                logger.warning(f"LEANN not available on {platform}, falling back to ChromaDB")
                return ChromaDBStore(path=path)

        elif platform == Platform.WINDOWS:
            # Windows: ChromaDB only (for now)
            return ChromaDBStore(path=path)

        else:
            # Unknown platform: Safe fallback
            return ChromaDBStore(path=path)
```

### User Experience

**Users don't choose** - ragged automatically selects best backend:

```bash
# First run on macOS
$ ragged init
Initialising ragged...
✓ Vector store: LEANN (97% storage savings)
✓ Memory storage: LEANN
✓ Ready!

# First run on Windows
$ ragged init
Initialising ragged...
✓ Vector store: ChromaDB (universal compatibility)
✓ Memory storage: ChromaDB
✓ Ready!
```

**Advanced users can check**:
```bash
$ ragged config show storage
Document Store: LEANN (macOS ARM64)
Memory Store: LEANN (macOS ARM64)
Platform: macOS 14.1, ARM64
LEANN Version: 0.2.1
```

---

## Rationale

### Why v0.4.3 (Early)?

**1. Architectural Foundation**

LEANN integration requires:
- VectorStore abstraction (v0.4.1) ✅
- Factory pattern for backend selection ✅
- Platform detection system (new)
- Migration tools foundation (v0.4.11 builds on this)

Implementing in v0.4.3 means memory system (v0.4.5) inherits benefits immediately.

**2. Storage Reality**

Without LEANN, memory system storage becomes prohibitive:

| Timeline | ChromaDB | LEANN | Savings |
|----------|----------|-------|---------|
| 3 months | 1.8GB | 54MB | 97% |
| 1 year | 7.2GB | 216MB | 97% |
| 3 years | 21.6GB | 648MB | 97% |

*Assumptions: 30 queries/day, 300 words/query, 1536-dim embeddings*

**3. User Experience First**

Deciding backend late (v0.4.5) forces users to:
- Understand LEANN vs ChromaDB trade-offs
- Make technical decisions
- Potentially migrate later if they choose wrong

Platform-aware auto-selection:
- Works out of the box
- Optimal choice for their platform
- No user decision required
- Migration tools available if needed (v0.4.11)

### Why Platform-Aware (Not Optional)?

**Alternative: Make LEANN user-choosable on all platforms**

Rejected because:
1. **Complexity**: Users shouldn't need to understand backend trade-offs
2. **Windows**: LEANN not available, offering choice is misleading
3. **Support Burden**: Two backends = double the support questions
4. **Testing**: Combinatorial explosion (2 backends × N features)

**Platform-aware approach**:
- ✅ Optimal default for each platform
- ✅ No user decision required
- ✅ Windows users don't see unavailable option
- ✅ Migration path exists (v0.4.11)

### Why Not Wait for Windows Support?

**Estimated Windows LEANN timeline**: 6-12 months (C++ build toolchain, Windows-specific optimisations)

**Cost of waiting**:
- Defer 97% savings to 2027+
- Memory system (v0.4.5) uses ChromaDB, difficult migration
- Users accumulate data in ChromaDB format
- Harder to migrate later (more data, more disruption)

**Benefit of proceeding**:
- macOS/Linux users get 97% savings immediately
- Memory system built on LEANN from day one (on supported platforms)
- Windows users still fully supported (ChromaDB works great)
- When Windows LEANN ready, migration tools already exist (v0.4.11)

---

## Consequences

### Positive

1. **Immediate Storage Savings**: macOS/Linux users save 97% (majority of developer base)
2. **Architecture Clarity**: Platform-aware from start, no retrofitting
3. **Memory System Ready**: v0.4.5 can use optimal backend immediately
4. **Migration Foundation**: v0.4.11 migration tools work for any backend change
5. **Windows Compatibility**: Full support via ChromaDB fallback
6. **Future-Proof**: Easy to add LEANN Windows support when ready

### Negative

1. **Platform Disparity**: macOS/Linux get storage benefits, Windows doesn't
2. **Testing Complexity**: Must test both backends on appropriate platforms
3. **Documentation**: Need to explain platform differences
4. **Support**: Questions about "why different on Windows?"
5. **Build Complexity**: Platform-specific binaries

### Mitigations

**Platform Disparity**:
- Clearly document in README and docs
- Windows LEANN support planned (roadmap transparency)
- ChromaDB works perfectly on Windows (no functionality loss)
- Migration path available when Windows support arrives

**Testing Complexity**:
- Automated CI/CD on macOS, Linux, Windows
- Contract tests ensure backend compatibility
- Platform-specific test suites
- Regular cross-platform validation

**Documentation**:
```markdown
## Storage Backend by Platform

ragged automatically selects the best storage backend for your platform:

- **macOS**: LEANN (97% storage savings, excellent performance)
- **Linux**: LEANN (97% storage savings, excellent performance)
- **Windows**: ChromaDB (universal compatibility, full feature parity)

All features work identically regardless of backend. You can migrate between backends later using `ragged migrate`.
```

**Support**:
- FAQ addressing platform differences
- Clear messaging: "optimised for your platform"
- Emphasise feature parity (not degradation)

**Build Complexity**:
- Platform-specific wheels in PyPI
- Automated build pipeline
- Clear build documentation

---

## Technical Details

### Platform Detection

```python
import platform
import sys
from enum import Enum

class Platform(Enum):
    MACOS_INTEL = "darwin-x86_64"
    MACOS_ARM = "darwin-arm64"
    LINUX_X86_64 = "linux-x86_64"
    LINUX_ARM64 = "linux-aarch64"
    WINDOWS = "windows"
    UNKNOWN = "unknown"

def detect_platform() -> Platform:
    """Detect current platform for backend selection."""
    system = platform.system().lower()
    machine = platform.machine().lower()

    if system == "darwin":
        if machine in ["arm64", "aarch64"]:
            return Platform.MACOS_ARM
        else:
            return Platform.MACOS_INTEL

    elif system == "linux":
        if machine in ["x86_64", "amd64"]:
            return Platform.LINUX_X86_64
        elif machine in ["arm64", "aarch64"]:
            return Platform.LINUX_ARM64
        else:
            return Platform.UNKNOWN

    elif system == "windows":
        return Platform.WINDOWS

    else:
        return Platform.UNKNOWN
```

### Graceful Fallback

```python
class LEANNNotAvailable(Exception):
    """LEANN backend not available on this platform."""
    pass

def create_backend(backend_type: str, path: str) -> VectorStore:
    """Create backend with graceful fallback."""
    if backend_type == "leann":
        try:
            import leann
            return LEANNStore(path=path)
        except ImportError:
            logger.warning("LEANN not installed, falling back to ChromaDB")
            return ChromaDBStore(path=path)
        except Exception as e:
            logger.error(f"LEANN initialisation failed: {e}")
            return ChromaDBStore(path=path)
    else:
        return ChromaDBStore(path=path)
```

### Migration Support (v0.4.11)

```bash
# Migrate existing ChromaDB to LEANN (if platform supports)
ragged migrate to-leann --verify --backup

# Migrate LEANN to ChromaDB (cross-platform compatibility)
ragged migrate to-chromadb --verify --backup

# Compare backends (before migration)
ragged migrate compare-backends
```

---

## Performance Characteristics

### Storage

| Scenario | ChromaDB | LEANN | Savings |
|----------|----------|-------|---------|
| 10K documents | 2.1GB | 63MB | 97% |
| 100K documents | 21GB | 630MB | 97% |
| 10K memory interactions | 1.8GB | 54MB | 97% |

### Query Performance

| Operation | ChromaDB | LEANN | Difference |
|-----------|----------|-------|------------|
| Top-3 recall | 95% | 90% | -5% (acceptable) |
| Query latency (10K docs) | 45ms | 68ms | +51% (still <100ms target) |
| Query latency (100K docs) | 120ms | 180ms | +50% (still acceptable) |
| Indexing | Fast | Slower (graph build) | Acceptable (one-time) |

**Trade-off Accepted**: Slightly lower recall and higher latency justified by 97% storage savings.

---

## Alternatives Considered

### Alternative 1: Defer to v0.5.x (Wait for Windows)

**Approach**: Postpone LEANN until Windows support ready

**Rejected Because**:
- Delays benefits 6-12 months
- Memory system (v0.4.5) forced to use ChromaDB
- Harder migration later (more accumulated data)
- macOS/Linux users don't benefit from ready solution

### Alternative 2: User-Selectable Backend

**Approach**: Let users choose LEANN vs ChromaDB at setup

**Rejected Because**:
- Burdens users with technical decision
- Windows users confused by unavailable option
- Support complexity (wrong choice regret)
- Double testing burden
- Not aligned with "it just works" philosophy

### Alternative 3: LEANN-Only (Drop ChromaDB)

**Approach**: Make LEANN mandatory, no Windows support

**Rejected Because**:
- Excludes Windows users entirely
- Breaks backward compatibility
- Contradicts inclusive platform support
- Unnecessary (ChromaDB works fine as fallback)

---

## Rollout Plan

### v0.4.1 (VectorStore Abstraction)
- Abstract VectorStore interface
- ChromaDBStore implementation
- Factory pattern foundation
- Contract tests

### v0.4.3 (LEANN Integration)  ← **THIS RELEASE**
- Platform detection system
- LEANNStore implementation
- Platform-aware factory
- Graceful fallback logic
- Cross-platform testing
- Documentation

### v0.4.5 (Memory Foundation)
- Memory system uses platform-appropriate backend automatically
- Benefits from LEANN immediately (macOS/Linux)
- Works perfectly on Windows (ChromaDB)

### v0.4.11 (Migration Tools)
- ChromaDB ↔ LEANN migration
- Backend comparison tools
- Verification and rollback
- Cross-platform compatibility validation

### Future: Windows LEANN Support
- When available, seamless integration
- Migration tools already exist
- No architecture changes required

---

## Monitoring & Validation

### Metrics to Track

**Storage Efficiency**:
```bash
ragged storage report
# Platform: macOS ARM64
# Backend: LEANN
# Documents: 12,543
# Storage: 387MB (vs 12.9GB with ChromaDB, 97% savings)
```

**Performance**:
```bash
ragged benchmark --backend leann
# Top-3 Recall: 91.2%
# Query Latency (p95): 82ms
# Storage: 387MB
```

**Platform Distribution** (telemetry-free, via GitHub discussions):
- Ask users to report platform in setup issues
- Track download statistics by platform
- Community survey (optional)

---

## Related Documentation

**ADRs**:
- [ADR-0015: VectorStore Abstraction](./0015-vectorstore-abstraction.md) - Foundation for this decision
- [ADR-0016: Memory System Architecture](./0016-memory-system-architecture.md) - Benefits from LEANN
- [ADR-0019: v0.4.x Restructuring - LEANN Mandatory](./0019-v04x-restructuring-leann-mandatory.md) - Context for roadmap change

**Analysis**:
- [LEANN Integration Analysis](../2025-11-16-leann-integration-analysis.md) - Detailed evaluation

**Roadmap**:
- [v0.4.3 Roadmap](../../roadmap/version/v0.4/v0.4.3.md) - LEANN implementation plan
- [v0.4.11 Roadmap](../../roadmap/version/v0.4/v0.4.11.md) - Migration tools
- [v0.4 README](../../roadmap/version/v0.4/README.md) - Overall strategy

---

## Decision Rationale Summary

**Why v0.4.3 (Early)?**
- Memory system (v0.4.5) needs storage efficiency from day one
- Easier to build on LEANN than migrate later
- macOS/Linux users are majority of developer base

**Why Platform-Aware (Auto-Select)?**
- Users shouldn't make technical decisions
- Optimal choice for each platform
- Windows users fully supported via ChromaDB
- Migration path available when Windows LEANN ready

**Why Not Wait?**
- 97% savings available now for macOS/Linux
- Memory system scales better with LEANN
- Migration harder with accumulated data
- Windows LEANN timing uncertain (6-12 months)

This decision prioritises user experience (automatic, optimal), storage efficiency (97% savings where available), and pragmatism (full Windows support via fallback) over platform uniformity.

---

**Status**: Accepted (for v0.4.3 implementation)
