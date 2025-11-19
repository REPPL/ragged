# Version Development Logs

**Purpose:** Version-specific development narratives

---

## Overview

This directory contains **development logs** organised by version, providing a narrative account of how each version was built.

**Important:** This is NOT the canonical source for implementation records. For technical documentation, see [implementation/version/](../../../../implementation/version/).

### Distinction

| Directory | Purpose | Content Type | Audience |
|-----------|---------|--------------|----------|
| **process/devlogs/version/** | Development narrative | Daily narrative, decision timeline, lessons learned | Researchers, future developers |
| **implementation/version/** | Canonical implementation record | Technical specs, release notes, test docs | Current developers, users |

**Single Source of Truth:** All technical implementation records are in `implementation/version/`. This directory provides narrative context only.

---

## Structure

Each version directory contains:
- `README.md` - Overview with cross-reference to canonical docs
- `decisions-index.md` - Timeline of decisions (ADRs are canonical)
- `phases.md`, `timeline.md` - Development narrative
- `archive/` - Historical development notes

---

## Current Versions

- **[v0.1/](./v0.1/)** - MVP development narrative (complete)
  - Canonical docs: [implementation/version/v0.1/](../../../../implementation/version/v0.1/)
- **[v0.2/](./v0.2/)** - Enhanced retrieval development (in progress)
  - Canonical docs: [implementation/version/v0.2/](../../../../implementation/version/v0.2/)

---

## Related Documentation

- [Daily Logs](../daily/) - Day-by-day progress
- **[Implementations](../../../../implementation/version/)** - **Canonical source of truth**
- [Decisions](../../../../decisions/adrs/) - Architectural decisions

---
