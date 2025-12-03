# Feature-Centric Roadmap Standard

**Status:** Mandatory for all development projects

---

## Overview

This document defines the REQUIRED structure for roadmap documentation. All projects MUST use feature-centric roadmaps rather than version-centric approaches.

**Core insight:** Features are the primary unit of work. Versions/milestones are bundles of features shipped together.

---

## Why This Standard Exists

Version-centric roadmaps create significant problems at scale:

### Problem 1: Parallel Hierarchies

Version-centric approaches create multiple directories per version:

```
planning/version/v0.6/      # What & why
roadmap/version/v0.6/       # How & when
implementation/version/v0.6/ # What was built
process/devlogs/version/v0.6/ # How it was built
```

Finding information about a single version requires checking **four separate locations**.

### Problem 2: File Explosion

Each minor release becomes a separate file:

```
roadmap/version/v0.6/
├── v0.6.0.md
├── v0.6.1.md
├── v0.6.2.md
├── v0.6.3.md
...
└── v0.6.15.md   # 16 files for one version series
```

### Problem 3: Scattered Features

Features that span multiple versions are duplicated across version files:

- Security hardening appears in v0.2, v0.5, v0.6, and v0.7 roadmaps
- Each copy must be maintained separately
- Information drifts out of sync

### Problem 4: Maintenance Burden

When a feature's scope changes:

- Update planning/version/vX.X/
- Update roadmap/version/vX.X.X/
- Update implementation/version/vX.X/
- Update devlogs/version/vX.X/

Four updates for one change. This creates maintenance debt.

### Problem 5: Navigation Difficulty

"What are we working on now?" requires:

1. Check roadmap/ for planned work
2. Cross-reference planning/ for design context
3. Check implementation/ for completed work
4. Review devlogs/ for current status

No single location provides the answer.

---

## Mandatory Principles

### Principle 1: Features Are the Primary Unit of Work

**Features** are discrete pieces of value delivered to users. They are the fundamental building blocks of your product.

**Versions/Milestones** are bundles of features shipped together. They are delivery containers, not work units.

This separation is crucial:

| Concept | Purpose | Changes When |
|---------|---------|--------------|
| Feature | Defines the work | Scope changes |
| Milestone | Defines the delivery | Schedule changes |

A feature's specification should remain stable even if its target milestone shifts.

### Principle 2: Single Source of Truth

Each feature specification lives in **exactly one location**:

```
roadmap/features/[status]/feature-name.md
```

Milestone documents **reference** features—they do not duplicate them:

```markdown
## Features Included in v0.7

- [Model Routing](../features/active/model-routing.md) - Intelligent query classification
- [Session Security](../features/completed/session-security.md) - Redis-backed persistence
```

If information exists in two places, it will eventually contradict itself.

### Principle 3: Status by Location

Instead of status fields that become stale, use directory location:

| Directory | Status | Meaning |
|-----------|--------|---------|
| `features/active/` | 🔄 In Progress | Currently being worked on |
| `features/planned/` | 📅 Queued | Designed, awaiting implementation |
| `features/completed/` | ✅ Done | Shipped and documented |

Moving a file from `planned/` to `active/` updates its status automatically. No metadata to maintain.

### Principle 4: Progressive Disclosure

Not all information needs the same visibility:

| Level | Location | Content |
|-------|----------|---------|
| Overview | `roadmap/README.md` | Current focus, blockers, priorities |
| Index | `features/README.md` | All features with status table |
| Detail | `features/*/name.md` | Full specification |
| Release | `milestones/v0.X.md` | Feature bundle, release notes |

Users can drill down to their required level of detail.

---

## Required Structure

All projects MUST implement this directory structure:

```
roadmap/
├── README.md                    # Status dashboard (required)
│
├── features/                    # Feature specifications (required)
│   ├── README.md                # Feature index with status table
│   │
│   ├── active/                  # Currently in progress
│   │   ├── README.md            # Active work summary
│   │   └── *.md                 # Feature documents
│   │
│   ├── planned/                 # Queued for future
│   │   ├── README.md            # Planned work summary
│   │   └── *.md                 # Feature documents
│   │
│   └── completed/               # Archive of done work
│       ├── README.md            # Completion history
│       └── *.md                 # Feature documents
│
└── milestones/                  # Release planning (required)
    ├── README.md                # Timeline overview
    └── v0.X.md                  # One file per major version
```

---

## Feature Document Template

Every feature document MUST include these sections:

```markdown
# Feature: [Name] ([ID])

**Status:** 🔄 Active | 📅 Planned | ✅ Completed
**Target Milestone:** v0.X.X
**Estimated Hours:** XX-XXh

---

## Problem Statement

[Why this feature is needed. What problem does it solve? What user need does it address?]

## Design Approach

[High-level approach to solving the problem. Key technical decisions. Architecture implications.]

## Implementation Tasks

- [ ] Phase 1: [Description]
  - [ ] Task 1.1
  - [ ] Task 1.2
- [ ] Phase 2: [Description]
  - [ ] Task 2.1
  - [ ] Task 2.2

## Success Criteria

- [ ] Criterion 1 (measurable)
- [ ] Criterion 2 (measurable)
- [ ] Criterion 3 (measurable)

## Dependencies

- **Requires:** [Link to prerequisite feature]
- **Blocks:** [Link to dependent feature]

## Related Documentation

- [ADR: Decision Record](../../decisions/adrs/0XX-name.md)
- [Planning: Design Rationale](../../planning/...)

---

**Completed:** [Date] (only when moved to completed/)
```

### Section Requirements

| Section | Required | Purpose |
|---------|----------|---------|
| Problem Statement | ✅ Yes | Why this work matters |
| Design Approach | ✅ Yes | How we solve it |
| Implementation Tasks | ✅ Yes | What to do |
| Success Criteria | ✅ Yes | How we know it's done |
| Dependencies | If applicable | Ordering constraints |
| Related Documentation | ✅ Yes | Cross-references |

---

## Milestone Document Template

Every milestone document MUST include:

```markdown
# Milestone: v0.X.X

**Target:** [Date or criteria]
**Status:** Planning | Ready | In Progress | Released
**Theme:** [1-3 word theme]

---

## Summary

[Brief description of what this milestone achieves for users.]

## Features Included

### Completed
- [Feature Name](../features/completed/name.md) - Brief description

### In Progress
- [Feature Name](../features/active/name.md) - Brief description

### Planned
- [Feature Name](../features/planned/name.md) - Brief description

## Dependencies

- **Requires:** v0.X.X complete
- **Blocks:** v0.X.X

## Release Notes (Draft)

### New Features
- Feature 1: Description
- Feature 2: Description

### Improvements
- Improvement 1

### Bug Fixes
- Fix 1

---

**Released:** [Date] (only when shipped)
```

### Key Rules

1. **Reference, don't duplicate:** Feature details live in feature documents
2. **Keep lightweight:** Milestones are bundles, not specifications
3. **Update status:** Move feature links between sections as status changes

---

## Dashboard README Template

The `roadmap/README.md` MUST serve as a status dashboard:

```markdown
# Development Roadmap

**Current Focus:** [1-2 active features]
**Next Milestone:** v0.X.X

---

## Active Work

| Feature | Status | Target |
|---------|--------|--------|
| [Name](features/active/name.md) | 🔄 Phase 2/3 | v0.X |

## Blockers

- [ ] Blocker description (owner, since date)

## Next Priorities

1. [Feature Name](features/planned/name.md) - Brief rationale
2. [Feature Name](features/planned/name.md) - Brief rationale
3. [Feature Name](features/planned/name.md) - Brief rationale

## Recent Completions

- [Feature Name](features/completed/name.md) - Completed [date]

## Quick Links

- [All Features](../../implementation/README.md)
- [Milestone Timeline](../../implementation/README.md)
- [v0.X Milestone](milestones/v0.X.md)
```

---

## When to Split Features

**Split into separate documents when:**

- Feature has 5+ implementation phases
- Multiple developers working on same feature
- Feature spans multiple milestones
- Feature has complex dependencies

**Keep as single document when:**

- Simple feature (< 3 tasks)
- Single milestone scope
- No design complexity
- Clear, bounded scope

**Never split across milestones:** If a feature appears in multiple milestones, it's one feature document with phases, not multiple features.

---

## Migration from Version-Centric

### Step 1: Inventory

List all features across all version files:

```bash
grep -rh "^## " roadmap/version/ | sort | uniq
```

### Step 2: Deduplicate

Identify features that appear in multiple version files. These become single feature documents.

### Step 3: Extract

For each unique feature:

1. Create `features/[status]/feature-name.md`
2. Consolidate all information about that feature
3. Determine current status (active/planned/completed)

### Step 4: Create Milestones

For each major version:

1. Create `milestones/v0.X.md`
2. Reference features (don't copy)
3. Add release context

### Step 5: Remove Old Structure

Once migration is verified:

1. Delete `roadmap/version/` directory
2. Update all cross-references
3. Git history preserves old content

---

## Benefits

| Metric | Version-Centric | Feature-Centric |
|--------|-----------------|-----------------|
| Files per version series | 16+ | 1 milestone + N features |
| Finding information | 4 directories | 1 directory |
| Cross-cutting features | Duplicated N times | Single source |
| Status tracking | Manual metadata | Folder location |
| Maintenance burden | O(versions × features) | O(features) |
| Navigation | Indirect | Direct |

---

## Exceptions

This standard MAY be relaxed ONLY for:

- **Proof-of-concept projects** with < 3 planned features
- **Single-session experiments** not intended for continuation

All other projects MUST follow this standard.

---

## Compliance Checklist

Before any release, verify:

- [ ] All features documented in `roadmap/features/`
- [ ] Active features in `features/active/`
- [ ] Completed features moved to `features/completed/`
- [ ] Milestone documents reference (not duplicate) features
- [ ] Dashboard README reflects current state
- [ ] No orphaned version-centric files
- [ ] All cross-references valid

---

## Related Documentation

- [Version Lifecycle](./version-lifecycle.md) - How versions progress through stages
- [Time Tracking](./time-tracking.md) - Tracking AI-assisted development time
- [AI Assistance](./ai-assistance.md) - AI transparency standards

---

**Status:** Mandatory
