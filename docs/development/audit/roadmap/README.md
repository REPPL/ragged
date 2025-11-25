# Roadmap and Planning Audits

Roadmap audits review planning documentation, task organisation, and version roadmaps for completeness, feasibility, and adherence to project planning standards.

## Audit Reports

All audit reports use the format: `YYYY-MM-DD-description.md`

| Date | Audit | Status |
|------|-------|--------|
| 2025-11-25 | [Feature-Centric Restructuring](./2025-11-25-restructuring-plan.md) | Documented (pending execution) |
| 2025-11-22 | [Initial Restructuring](./2025-11-22-restructuring.md) | Superseded |

### Planning Structure Audits

Assess the organisation and structure of planning documentation:
- Roadmap directory structure
- Version planning hierarchy
- Separation of planning vs. roadmap vs. implementation
- Cross-references between planning phases

### Roadmap Completeness Audits

Review roadmap content for completeness:
- Task breakdown adequacy
- Time estimates reasonableness
- Dependency identification
- Risk assessment
- Success criteria definition

### Planning Standards Compliance

Verify adherence to planning documentation standards:
- Planning (WHAT & WHY) in `docs/development/planning/`
- Roadmap (HOW & WHEN) in `docs/development/roadmap/`
- Implementation (WHAT WAS BUILT) in `docs/development/implementation/`
- Lineage tracking between phases

## Planning Documentation Standards

From `~/Development/.claude/CLAUDE.md`:

**planning/** = WHAT to build & WHY
- High-level design goals
- Alternatives considered
- Trade-offs evaluated

**roadmap/** = HOW & WHEN to build
- Detailed execution plan
- Task breakdown
- Time estimates
- Dependencies

**implementation/** = WHAT was built
- Actual results
- Deviations from plan
- Lessons learnt

## Conducting Roadmap Audits

Key questions to address:
1. Is there clear separation between planning, roadmap, and implementation?
2. Are all roadmap items properly scoped and estimated?
3. Is there bidirectional linking (planning ← → roadmap ← → implementation)?
4. Are dependencies identified and tracked?
5. Are success criteria clearly defined?

## Related Documentation

- [Feature-Centric Roadmap Standard](../../development/process/methodology/feature-centric-roadmaps.md) - Target methodology
- Planning decision tree: `~/Development/.claude/CLAUDE.md`
- Roadmap templates: `docs/development/roadmap/version/`
- Planning templates: `docs/development/planning/version/`
