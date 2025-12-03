# Roadmap Restructuring Plan: Version-Centric to Feature-Centric

**Date:** 2025-11-25
**Status:** Documented (pending execution)
**Estimated Effort:** 18-27 hours
**Supersedes:** [2025-11-22-restructuring.md](./2025-11-22-restructuring.md)

---

## Executive Summary

This document provides a detailed migration plan to convert ragged's current version-centric roadmap structure to a feature-centric approach, as defined in the [Feature-Centric Roadmap Standard](../../process/methodology/feature-centric-roadmaps.md).

### Current State

```
roadmap/
├── README.md
├── security-improvements-v0.6.x.md
├── features/v0.3/
└── version/
    ├── README.md (19KB master reference)
    ├── current -> v0.3
    ├── v0.2/ (11 releases)
    ├── v0.3/ (13+ planned)
    ├── v0.4/ (14+ planned)
    ├── v0.5/ (12 planned)
    ├── v0.6/ (16 files: v0.6.0-v0.6.15)
    ├── v0.7/ (5+ planned)
    ├── v0.8/, v0.9/, v1.5/, v2.0/
```

**Problems identified:**
- 16 separate files for v0.6.x alone
- Cross-cutting features duplicated across versions
- 4 parallel hierarchies to check for version info
- Stale `current` symlink (points to v0.3, work is on v0.6.2)

### Target State

```
roadmap/
├── README.md                    # Status dashboard
├── features/
│   ├── README.md                # Feature index
│   ├── active/                  # In progress
│   ├── planned/                 # Queued
│   └── completed/               # Archive
└── milestones/
    ├── README.md                # Timeline
    └── v0.X.md                  # Per major version
```

---

## Pre-Migration Assessment

### Current File Inventory

**v0.6 series (16 files):**
- v0.6.0.md - Web UI security & API maturity
- v0.6.1.md - Query classification foundation
- v0.6.2.md - Automatic model routing (OPTIMISE-002)
- v0.6.3.md - Domain adaptation
- v0.6.4.md - Analytics & caching
- v0.6.5.md - Streaming responses
- v0.6.6.md - CLI analytics commands
- v0.6.7.md - FastAPI REST layer
- v0.6.8.md - Svelte core UI
- v0.6.9.md - Svelte advanced features
- v0.6.10.md - PWA & polish
- v0.6.11.md - Security integration
- v0.6.12.md - Security monitoring
- v0.6.13.md - Security automation
- v0.6.14.md - Security documentation
- v0.6.15.md - Security hardening final

**v0.7 series (5+ files):**
- v0.7.0.md - CLI UX enhancement
- v0.7.1.md - WebUI feature completeness
- v0.7.2.md - Advanced visualisations
- v0.7.3.md - Collaboration features (CONDITIONAL)
- v0.7.4.md - Security hardening
- v0.7.5.md - Testing & QA

### Feature Consolidation Map

| Version Files | Consolidated Feature | Target Location |
|---------------|---------------------|-----------------|
| v0.6.0 | web-ui-security | features/completed/ |
| v0.6.1 | query-classification | features/completed/ |
| v0.6.2 | model-routing | features/active/ |
| v0.6.3 | domain-adaptation | features/planned/ |
| v0.6.4 | analytics-caching | features/planned/ |
| v0.6.5-v0.6.6 | streaming-retrieval | features/planned/ |
| v0.6.7-v0.6.10 | svelte-web-ui | features/planned/ |
| v0.6.11-v0.6.15 | security-hardening-v06 | features/planned/ |
| v0.7.0 | cli-ux-enhancement | features/planned/ |
| v0.7.1 | webui-completeness | features/planned/ |
| v0.7.2 | advanced-visualisations | features/planned/ |
| v0.7.3 | collaboration-features | features/planned/ (CONDITIONAL) |
| v0.7.4-v0.7.5 | security-testing | features/planned/ |

---

## Migration Phases

### Phase 0: Preparation (2-3 hours)

**Tasks:**

- [ ] **P0.1** Commit all current work
  ```bash
  git add -A && git commit -m "chore: pre-migration checkpoint"
  ```

- [ ] **P0.2** Create inventory spreadsheet
  - List every file in `roadmap/version/`
  - Note file sizes and key content
  - Identify feature boundaries

- [ ] **P0.3** Identify active work
  - Current: v0.6.2 (model-routing)
  - Document in-progress state

- [ ] **P0.4** Review cross-cutting features
  - Security hardening spans v0.2, v0.5, v0.6, v0.7
  - Identify consolidation opportunities

**Verification:**
- [ ] All work committed
- [ ] Inventory complete
- [ ] Active work documented

---

### Phase 1: Create New Structure (1-2 hours)

**Tasks:**

- [ ] **P1.1** Create feature directories
  ```bash
  mkdir -p roadmap/features/{active,planned,completed}
  ```

- [ ] **P1.2** Create milestones directory
  ```bash
  mkdir -p roadmap/milestones
  ```

- [ ] **P1.3** Create features/README.md
  ```markdown
  # Feature Index

  ## Status Summary

  | Status | Count | Directory |
  |--------|-------|-----------|
  | 🔄 Active | X | [active/](./active/) |
  | 📅 Planned | X | [planned/](./planned/) |
  | ✅ Completed | X | [completed/](./completed/) |

  ## All Features

  [Table of all features with links]
  ```

- [ ] **P1.4** Create subdirectory READMEs
  - `features/active/README.md`
  - `features/planned/README.md`
  - `features/completed/README.md`

- [ ] **P1.5** Create milestones/README.md
  ```markdown
  # Milestone Timeline

  | Version | Target | Status | Theme |
  |---------|--------|--------|-------|
  | v0.7 | Q1 2026 | Planning | UI Enhancement |
  | v0.8 | Q2 2026 | Planning | Installation |
  | ... | ... | ... | ... |
  ```

**Verification:**
- [ ] All directories created
- [ ] All READMEs present
- [ ] Structure matches standard

---

### Phase 2: Extract Features (8-12 hours)

**Note:** This is the most time-intensive phase. Each feature requires:
1. Reading source version files
2. Consolidating into feature template
3. Adding cross-references
4. Determining correct status folder

#### v0.6.x Features

- [ ] **P2.1** `features/completed/web-ui-security.md`
  - Source: v0.6.0.md
  - Content: Web UI security, API maturity
  - Status: Completed (based on implementation records)

- [ ] **P2.2** `features/completed/query-classification.md`
  - Source: v0.6.1.md
  - Content: Query classification foundation
  - Status: Completed

- [ ] **P2.3** `features/active/model-routing.md`
  - Source: v0.6.2.md
  - Content: OPTIMISE-002 automatic model routing
  - Status: Active (current work)
  - Include: All three phases from source

- [ ] **P2.4** `features/planned/domain-adaptation.md`
  - Source: v0.6.3.md
  - Content: Domain-specific query adaptation

- [ ] **P2.5** `features/planned/analytics-caching.md`
  - Source: v0.6.4.md
  - Content: Query analytics, result caching

- [ ] **P2.6** `features/planned/streaming-retrieval.md`
  - Sources: v0.6.5.md, v0.6.6.md
  - Content: Streaming responses, parallel retrieval, CLI commands
  - **Consolidation:** Merge related files

- [ ] **P2.7** `features/planned/svelte-web-ui.md`
  - Sources: v0.6.7.md, v0.6.8.md, v0.6.9.md, v0.6.10.md
  - Content: FastAPI REST, Svelte core, advanced features, PWA
  - **Consolidation:** Major consolidation (4 files → 1)

- [ ] **P2.8** `features/planned/security-hardening-v06.md`
  - Sources: v0.6.11.md - v0.6.15.md
  - Content: Security integration, monitoring, automation, docs
  - **Consolidation:** Major consolidation (5 files → 1)

#### v0.7.x Features

- [ ] **P2.9** `features/planned/cli-ux-enhancement.md`
  - Source: v0.7.0.md
  - Content: CLI user experience improvements

- [ ] **P2.10** `features/planned/webui-completeness.md`
  - Source: v0.7.1.md
  - Content: WebUI feature completeness

- [ ] **P2.11** `features/planned/advanced-visualisations.md`
  - Source: v0.7.2.md
  - Content: Similarity graphs, performance trends

- [ ] **P2.12** `features/planned/collaboration-features.md`
  - Source: v0.7.3.md
  - Content: User auth, shared collections
  - **Note:** CONDITIONAL - only if demand >15 requests

- [ ] **P2.13** `features/planned/security-testing.md`
  - Sources: v0.7.4.md, v0.7.5.md
  - Content: Security hardening, E2E tests, accessibility
  - **Consolidation:** Merge related files

#### v0.8.x-v2.0 Features

- [ ] **P2.14** Extract remaining version features
  - v0.8: Installation excellence
  - v0.9: Agent capabilities
  - v1.5: Collaboration & multi-user
  - v2.0: Enterprise features

**Feature Document Template:**

```markdown
# Feature: [Name] ([ID])

**Status:** 🔄 Active | 📅 Planned | ✅ Completed
**Target Milestone:** v0.X
**Estimated Hours:** XX-XXh
**Source:** Consolidated from v0.X.X.md [, v0.X.Y.md, ...]

---

## Problem Statement

[From source files]

## Design Approach

[From source files]

## Implementation Tasks

[From source files - consolidate if multiple sources]

## Success Criteria

[From source files]

## Dependencies

[From source files]

## Related Documentation

- Original roadmap: `archive/version/v0.X/v0.X.X.md` (if preserved)
- ADR: [Link if exists]
- Implementation: [Link if exists]

---
```

**Verification:**
- [ ] All features extracted
- [ ] No content lost
- [ ] Status correctly assigned
- [ ] Cross-references valid

---

### Phase 3: Create Milestone Documents (2-3 hours)

**Tasks:**

- [ ] **P3.1** `milestones/v0.7.md`
  ```markdown
  # Milestone: v0.7

  **Target:** Q1 2026
  **Status:** Planning
  **Theme:** User Interface Enhancement

  ## Features

  - [CLI UX Enhancement](../features/planned/cli-ux-enhancement.md)
  - [WebUI Completeness](../features/planned/webui-completeness.md)
  - [Advanced Visualisations](../features/planned/advanced-visualisations.md)
  - [Collaboration Features](../features/planned/collaboration-features.md) (CONDITIONAL)
  - [Security Testing](../features/planned/security-testing.md)

  ## Dependencies

  - Requires: v0.6.15 complete

  ## Release Notes (Draft)

  [To be completed closer to release]
  ```

- [ ] **P3.2** `milestones/v0.8.md` - Installation excellence
- [ ] **P3.3** `milestones/v0.9.md` - Agent capabilities
- [ ] **P3.4** `milestones/v1.5.md` - Collaboration
- [ ] **P3.5** `milestones/v2.0.md` - Enterprise

**Verification:**
- [ ] All milestones reference features (not duplicate)
- [ ] Dependencies documented
- [ ] Targets specified

---

### Phase 4: Update Dashboard (1 hour)

**Tasks:**

- [ ] **P4.1** Rewrite `roadmap/README.md`

```markdown
# Development Roadmap

**Current Focus:** Model Routing (OPTIMISE-002)
**Next Milestone:** v0.7

---

## Active Work

| Feature | Status | Target |
|---------|--------|--------|
| [Model Routing](features/active/model-routing.md) | 🔄 Phase 3/3 | v0.6 |

## Blockers

- None currently

## Next Priorities

1. [Domain Adaptation](features/planned/domain-adaptation.md) - Improve query understanding
2. [Analytics & Caching](features/planned/analytics-caching.md) - Performance optimisation
3. [Streaming Retrieval](features/planned/streaming-retrieval.md) - User experience

## Recent Completions

- [Query Classification](features/completed/query-classification.md) - 2025-11-24
- [Web UI Security](features/completed/web-ui-security.md) - 2025-11-24

## Quick Links

- [All Features](../../implementation/README.md)
- [Milestone Timeline](../../implementation/README.md)
- [v0.7 Milestone](milestones/v0.7.md)

---

## Key Principles

- **Stability First** - Fix critical bugs before features
- **Privacy Always** - All processing remains local
- **AI-Focused Estimates** - Hours for autonomous AI assistant
```

- [ ] **P4.2** Update `features/README.md` with complete index

**Verification:**
- [ ] Dashboard reflects current state
- [ ] All links work
- [ ] Priorities accurate

---

### Phase 5: Remove Old Structure (1 hour)

**Decision:** No archive - git history sufficient.

**Tasks:**

- [ ] **P5.1** Final verification
  - All features extracted
  - All content accessible in new structure
  - No orphaned references

- [ ] **P5.2** Remove version directory
  ```bash
  rm -rf roadmap/version/
  ```

- [ ] **P5.3** Remove stale symlink
  ```bash
  rm roadmap/current  # if exists
  ```

- [ ] **P5.4** Remove superseded files
  ```bash
  rm roadmap/security-improvements-v0.6.x.md  # content now in features/
  ```

- [ ] **P5.5** Clean up features/v0.3 if exists
  - Check if content migrated
  - Remove if redundant

**Verification:**
- [ ] Only new structure remains
- [ ] Git history shows removed files (can restore if needed)
- [ ] No broken references

---

### Phase 6: Update Cross-References (2-3 hours)

**Tasks:**

- [ ] **P6.1** Update `docs/development/README.md`
  - Change roadmap links to new structure
  - Update navigation guide

- [ ] **P6.2** Update `docs/development/planning/` links
  - Version planning docs may reference roadmap

- [ ] **P6.3** Update implementation records
  - Historical links may need updating or notes

- [ ] **P6.4** Update `docs/audit/` references

- [ ] **P6.5** Global link verification
  ```bash
  # Find all internal links and verify
  grep -rh "\[.*\](.*\.md)" docs/ | grep -v "http"
  ```

**Verification:**
- [ ] No broken links (manual spot check)
- [ ] `/verify-docs` passes

---

### Phase 7: Cleanup (1-2 hours)

**Tasks:**

- [ ] **P7.1** Remove duplicate directories
  ```bash
  # If content is in docs/development/research/
  rm -rf docs/research/  # remove duplicate

  # If content is in docs/development/testing/
  rm -rf docs/testing/   # remove duplicate
  ```

- [ ] **P7.2** Consolidate `docs/design/`
  - Move relevant content to `docs/development/planning/`
  - Remove if empty

- [ ] **P7.3** Update affected READMEs
  - `docs/README.md`
  - `docs/development/README.md`
  - Any others referencing removed directories

- [ ] **P7.4** Final verification
  - Run `/verify-docs`
  - Check British English compliance
  - Verify cross-references

**Verification:**
- [ ] No duplicate directories
- [ ] All READMEs updated
- [ ] Documentation audit passes

---

## Post-Migration Checklist

**Content Verification:**
- [ ] All v0.6.x features accessible
- [ ] All v0.7.x features accessible
- [ ] All v0.8-v2.0 features accessible
- [ ] Cross-cutting features consolidated
- [ ] No content lost (compare with pre-migration inventory)

**Structure Verification:**
- [ ] `roadmap/features/active/` contains current work
- [ ] `roadmap/features/planned/` contains queued work
- [ ] `roadmap/features/completed/` contains done work
- [ ] `roadmap/milestones/` contains release bundles
- [ ] All README files present and complete

**Quality Verification:**
- [ ] Dashboard reflects current state
- [ ] All internal links work
- [ ] `/verify-docs` passes
- [ ] British English compliance

**Process Verification:**
- [ ] Git history preserved (can restore old structure if needed)
- [ ] Migration documented in this file
- [ ] Team notified (if applicable)

---

## Rollback Plan

If migration fails at any point:

1. **Identify failure point** - Note which phase failed
2. **Document issues** - Update this file with what went wrong
3. **Git restore** - Restore from pre-migration commit
   ```bash
   git log --oneline  # find pre-migration commit
   git checkout <commit> -- docs/development/roadmap/
   ```
4. **Remove new structure** - Delete features/ and milestones/ if created
5. **Retry** - Address issues and retry migration

---

## Timeline Estimate

| Phase | Estimated Hours | Dependencies |
|-------|-----------------|--------------|
| Phase 0: Preparation | 2-3h | None |
| Phase 1: Create Structure | 1-2h | Phase 0 |
| Phase 2: Extract Features | 8-12h | Phase 1 |
| Phase 3: Create Milestones | 2-3h | Phase 2 |
| Phase 4: Update Dashboard | 1h | Phase 3 |
| Phase 5: Remove Old | 1h | Phase 4 |
| Phase 6: Update Links | 2-3h | Phase 5 |
| Phase 7: Cleanup | 1-2h | Phase 6 |
| **Total** | **18-27h** | |

---

## Related Documentation

- [Feature-Centric Roadmap Standard](../../process/methodology/feature-centric-roadmaps.md) - Target methodology
- [Current Roadmap](.) - Structure being migrated
- [Previous Assessment](./2025-11-22-restructuring.md) - Superseded by this plan

---

**Status:** Documented (pending execution)
