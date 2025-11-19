# Feature Specifications

**Purpose:** Centralised repository for all feature specifications and roadmaps

---

## Overview

This directory consolidates ALL feature specifications and roadmaps in one location, organised by scope:

- **Cross-version features** - Features that span multiple versions (root level)
- **Version-specific features** - Features specific to a version (version subdirectories)

**Taxonomy:**
```
features/
├── README.md (this file)
├── {cross-version-feature}.md (e.g., hardware-optimisation-roadmap.md)
└── v{X}.{Y}/ (version-specific features)
    ├── README.md
    └── {feature-name}.md
```

---

## Cross-Version Features

Features that span multiple versions or have complex multi-phase implementation timelines.

### [hardware-optimisation-roadmap.md](./hardware-optimisation-roadmap.md)
**Versions:** v0.1 - v1.0

**Phases:**
- Phase 1: Basic detection (v0.1)
- Phase 2: Model recommendations (v0.2)
- Phase 3: Automatic configuration (v0.3)
- Phase 4: Dynamic optimisation (v1.0)

**Effort:** 38-55 hours total

---

### [model-selection-roadmap.md](./model-selection-roadmap.md)
**Versions:** v0.1 - v2.1+

**Phases:**
- v0.1: Single model support
- v0.2: Basic routing
- v0.3: Complexity analysis
- v0.4: Persona integration
- v0.5: Advanced routing
- v1.0: Production routing
- v1.1+: Learning-based routing
- v2.0+: Cloud integration

---

## Version-Specific Features

Detailed feature specifications for individual versions.

### [v0.3](./v0.3/)
Advanced RAG techniques and features planned for v0.3 series.

**Features:**
- Chunking Strategies
- CLI Features
- Data Generation
- Evaluation & Quality
- Multi-Modal Support
- Query Processing

**See:** [v0.3 Features README](./v0.3/README.md)

---

## Feature Specification Format

Each feature specification includes:
- Overview and goals
- Implementation details
- Effort estimates (in hours)
- Dependencies and prerequisites
- Success criteria
- Testing requirements
- Integration points

---

## Related Documentation

- [Version Roadmaps](../version/) - Complete version roadmaps
- [Planning](../../planning/) - Design documents
- [Decisions](../../decisions/) - Architectural decisions
- [Implementation Records](../../implementation/) - Completed features

---
