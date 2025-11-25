# v0.5 Series Lineage

Traceability from concept to implementation for v0.5 Multi-Modal Vision RAG.

---

## Overview

The v0.5 series introduced multi-modal capabilities to ragged, enabling visual document understanding through ColPali vision embeddings. This document traces the evolution from design to implementation.

---

## Lineage Map

```
Planning (What & Why)
    │
    ├── docs/development/planning/version/v0.5/README.md
    │   └── High-level vision goals and architecture decisions
    │
    ▼
Roadmap (How & When)
    │
    ├── docs/development/roadmap/version/v0.5/README.md
    │   └── Series overview and release strategy
    │
    ├── docs/development/roadmap/version/v0.5/v0.5.0.md
    │   └── ColPali + Dual Storage specification (55-75h)
    │
    ├── docs/development/roadmap/version/v0.5/v0.5.1.md
    │   └── GPU Resource Management specification (18-24h)
    │
    ├── docs/development/roadmap/version/v0.5/v0.5.2.md
    │   └── Multi-Modal Vision Queries specification (28-38h)
    │
    └── (v0.5.3-v0.5.10 roadmaps exist)
    │
    ▼
Implementation (What Was Built)
    │
    ├── docs/development/implementation/version/v0.5/README.md
    │   └── Series implementation overview (8/12 complete)
    │
    ├── docs/development/implementation/version/v0.5/v0.5.0/README.md
    │   └── ColPali + Dual Storage (1,951 lines)
    │
    ├── docs/development/implementation/version/v0.5/v0.5.1/README.md
    │   └── GPU Resource Management (1,143 lines)
    │
    ├── docs/development/implementation/version/v0.5/v0.5.2/README.md
    │   └── Multi-Modal Vision Queries (660 lines)
    │
    └── (v0.5.3-v0.5.8 implementation records exist)
```

---

## Version-by-Version Lineage

### v0.5.0: ColPali + Dual Storage Foundation

| Phase | Document | Key Content |
|-------|----------|-------------|
| Planning | [v0.5 Planning](../../../planning/version/v0.5/README.md) | Multi-modal vision goals |
| Roadmap | [v0.5.0 Roadmap](../../../roadmap/version/v0.5/v0.5.0.md) | VISION-001, VISION-002 specs |
| Implementation | [v0.5.0 Implementation](./v0.5.0/README.md) | 1,951 lines across 4 files |

**Code Files:**
- `src/embeddings/colpali_embedder.py` (882 lines)
- `src/storage/dual_store.py` (830 lines)
- `src/storage/schema.py` (239 lines)

### v0.5.1: GPU Resource Management

| Phase | Document | Key Content |
|-------|----------|-------------|
| Roadmap | [v0.5.1 Roadmap](../../../roadmap/version/v0.5/v0.5.1.md) | VISION-004 spec |
| Implementation | [v0.5.1 Implementation](./v0.5.1/README.md) | 1,143 lines in src/gpu/ |

**Code Files:**
- `src/gpu/device_manager.py` (343 lines)
- `src/gpu/oom_handler.py` (284 lines)
- `src/gpu/memory_monitor.py` (266 lines)
- `src/gpu/batch_sizer.py` (210 lines)

### v0.5.2: Multi-Modal Vision Queries

| Phase | Document | Key Content |
|-------|----------|-------------|
| Roadmap | [v0.5.2 Roadmap](../../../roadmap/version/v0.5/v0.5.2.md) | VISION-003 spec |
| Implementation | [v0.5.2 Implementation](./v0.5.2/README.md) | 660 lines across 2 files |

**Code Files:**
- `src/retrieval/vision_retriever.py` (407 lines)
- `src/retrieval/query_processor.py` (253 lines)

### v0.5.3-v0.5.8: CLI, Testing, Security

These versions have existing implementation records in their respective directories.

---

## Code Statistics Summary

| Version | Focus | Lines | Files |
|---------|-------|-------|-------|
| v0.5.0 | ColPali + Storage | 1,951 | 4 |
| v0.5.1 | GPU Management | 1,143 | 5 |
| v0.5.2 | Vision Retrieval | 660 | 2 |
| v0.5.3 | CLI Commands | 2,437 | 8 |
| v0.5.4 | Legacy Removal | ~500 docs | 4 |
| v0.5.5 | Test Fixes | 2,604 | 301 |
| v0.5.7 | Security (Vision) | 2,700 | ~20 |
| v0.5.8 | Security (CLI) | 1,800 | 25+ |
| **Total** | | **~13,795** | **~369** |

---

## Key Decisions Made

1. **128-dim vision embeddings** (mean-pooled from multi-vector) - Balances quality vs storage
2. **Separate collections** for text (384-dim) and vision (128-dim) - Different embedding spaces
3. **RRF fusion** for hybrid queries - Simple, effective, tunable
4. **CUDA > MPS > CPU** device priority - Optimal performance on available hardware
5. **Encryption at rest** for vision metadata - GDPR compliance

---

## Remaining Work

| Version | Status | Focus |
|---------|--------|-------|
| v0.5.6 | Planned | Quality Metrics & Evaluation |
| v0.5.9 | Planned | Advanced features |
| v0.5.10 | Planned | Advanced features |
| v0.5.11 | Planned | Advanced features |

---

## Related Documentation

- [v0.5 Planning](../../../planning/version/v0.5/README.md)
- [v0.5 Roadmap](../../../roadmap/version/v0.5/README.md)
- [v0.5 Implementation Overview](./README.md)

---

**Status:** Lineage Complete for v0.5.0-v0.5.8
