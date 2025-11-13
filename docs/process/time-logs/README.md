# Time Logs

**Purpose:** Transparent tracking of actual development time per version and feature.

---

## Overview

This directory contains time logs documenting actual hours spent on ragged development. Unlike estimates in roadmaps, these are empirical measurements of completed work.

**Philosophy:**
- Track reality, not estimates
- Include all time: implementation, debugging, testing, documentation
- Distinguish AI-assisted vs. manual work
- Share what worked and what didn't

---

## Structure

```
time-logs/
├── README.md (this file)
└── version/
    ├── v0.1/
    │   └── v0.1-time-log.md
    ├── v0.2/
    │   ├── v0.2.0-time-log.md
    │   ├── v0.2.1-time-log.md
    │   └── v0.2.2-time-log.md
    └── vX.X/
        └── vX.X-time-log.md
```

**Naming Convention:**
- Major/minor versions get folders: `version/v0.1/`, `version/v0.2/`
- Individual time logs: `vX.X.X-time-log.md`

---

## What We Track

### Time Breakdown

For each version/feature:
- **Implementation:** Writing code
- **Debugging:** Fixing issues
- **Testing:** Writing and running tests
- **Documentation:** Writing docs
- **Total Hours:** Sum of all time

### AI Assistance Tracking

- **AI-Assisted Time:** Hours using AI coding tools
- **Manual Time:** Hours without AI assistance
- **AI Percentage:** % of time with AI help
- **Effectiveness:** What AI did well, what needed manual work

### Context

- **Task Type:** Scaffolding, implementation, refactoring, testing, docs
- **Challenges:** Problems encountered and how resolved
- **Learning:** Insights and discoveries
- **Would Do Differently:** Retrospective improvements

---

## Related Documentation

- [Methodology](../methodology/) - How we develop with AI
- [Development Logs](../devlog/) - Daily progress logs
- [Roadmap](../roadmap/) - Planned work (estimates)
- [Templates](../templates/) - Document templates

---

**Last Updated:** 2025-11-12
**Status:** Active - all development time tracked from v0.1 onwards
