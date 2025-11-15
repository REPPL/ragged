# Development Templates

This folder contains standardized templates for documenting decisions, tracking progress, and maintaining consistency across the Ragged project.

## Overview

Templates ensure consistent documentation practices and make it easy to capture important information throughout the development process. Each template includes:
- Clear structure and sections
- Usage instructions
- Best practices and examples
- Cross-referencing guidelines

---

## Available Templates

### [ADR Template](./adr-template.md)
**Architecture Decision Records (ADRs)** - Document significant architectural and technical decisions.

**When to use:**
- Making technology choices (libraries, frameworks, tools)
- Architectural pattern decisions
- Significant design changes
- Trade-off evaluations

**Output location:** `/docs/development/adr/XXXX-title.md`

**Example decisions:**
- Choosing ChromaDB vs. other vector databases
- Selecting Ollama for local LLM inference
- Deciding on Svelte for web UI framework

---

### [Devlog Template](./devlog-template.md)
**Daily Development Logs** - Track daily development activities, progress, and blockers.

**When to use:**
- Daily development sessions
- Recording completed work
- Documenting challenges and solutions
- Planning next steps

**Output location:** `/docs/development/process/devlog/daily/YYYY-MM-DD.md`

**Benefits:**
- Historical record of development progress
- Insight into time spent on different tasks
- Learning from past challenges

---

### [Feature Time Log Template](./feature-time-log-template.md)
**Feature-specific time tracking** - Detailed time logs for individual features or user stories.

**When to use:**
- Tracking time for specific features
- Estimating future work
- Analysing development velocity
- Retrospective analysis

**Output location:** `/docs/development/process/time-logs/feature-name-YYYY-MM-DD.md`

**Metrics tracked:**
- Time per development phase
- Research vs. implementation time
- Testing and debugging time
- Documentation time

---

### [User Story Template](./user-story-template.md)
**User Story Documentation** - Comprehensive user story format with acceptance criteria, roadmap, and technical details.

**When to use:**
- Defining new user-facing features
- Documenting requirements
- Planning persona-specific capabilities
- Establishing testable acceptance criteria

**Output location:** `/docs/development/planning/requirements/user-stories/US-XXX-title.md`

**Key sections:**
- Overview with persona mapping
- Detailed acceptance criteria (Given/When/Then)
- Feature roadmap across versions
- Technical constraints and success metrics

---

### [Version Summary Template](./version-summary-template.md)
**Version Release Documentation** - Comprehensive documentation for each version release.

**When to use:**
- Completing a version milestone (v0.1, v0.2, etc.)
- Documenting version-specific features
- Summarizing changes and improvements
- Planning next version

**Output location:** `/docs/development/planning/versions/vX.Y/README.md`

**Key sections:**
- Version goals and completion status
- Features delivered
- Technical changes
- Testing results
- Known limitations

---

## Template Usage Guidelines

### General Best Practices

1. **Copy, don't modify**: Always copy templates to their output location
2. **Fill all sections**: Complete all required sections (marked with ✅)
3. **Use British English**: Maintain consistency with project documentation
4. **Link extensively**: Cross-reference related documents
5. **Update regularly**: Keep documents current as work progresses

### Naming Conventions

- **ADRs**: `ADR-XXX-brief-description.md` (sequential numbering)
- **Devlogs**: `YYYY-MM-DD.md` (ISO date format)
- **Time Logs**: `feature-name-YYYY-MM-DD.md`
- **User Stories**: `US-XXX-brief-description.md` (ID prefix)
- **Version Summaries**: `README.md` in version folder

### Cross-Referencing

Templates include placeholders for cross-references:
- Link to related user stories
- Reference architectural decisions
- Connect to implementation docs
- Point to test coverage

---

## Folder Structure

Templates support this documentation structure:

```
docs/development/
├── planning/
│   ├── requirements/
│   │   └── user-stories/   # User stories go here
│   └── versions/           # Version summaries go here
│       ├── v0.1/
│       │   └── README.md
│       ├── v0.2/
│       └── ...
├── adrs/                   # ADRs go here
└── process/
    ├── devlogs/            # Daily logs go here
    ├── time-logs/          # Feature time logs go here
    └── templates/          # Templates (this folder)
```

---

## Customization

Templates can be adapted for project-specific needs:
- Add sections relevant to Ragged
- Modify example content
- Adjust formatting preferences
- Extend metadata fields

**Important**: Update this README if templates are modified significantly.

---

## Cross-References

- **Development Guide**: [../../README.md](../../README.md)
- **Version Roadmap**: [../../planning/versions/](../../planning/versions/)
- **User Stories**: [../../planning/requirements/user-stories/](../../planning/requirements/user-stories/)

---

## Template Maintenance

**Review Cycle**: Quarterly or when process changes
**Owner**: Development team
**Last Updated**: 2025-11-09

---

## Quick Start

1. **Creating an ADR**: Copy `adr-template.md` → `/docs/development/adrs/XXXX-title.md`
2. **Daily Devlog**: Copy `devlog-template.md` → `/docs/development/process/devlogs/daily/YYYY-MM-DD.md`
3. **New User Story**: Copy `user-story-template.md` → `/docs/development/planning/requirements/user-stories/US-XXX-title.md`
4. **Version Summary**: Copy `version-summary-template.md` → `/docs/development/planning/versions/vX.Y/README.md`
5. **Time Tracking**: Copy `feature-time-log-template.md` → `/docs/development/process/time-logs/feature-name.md`
