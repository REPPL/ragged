# US-XXX: [User Story Title]

**ID**: US-XXX
**Title**: [Brief descriptive title]
**Status**: ✅ Active | 🚧 In Progress | ⏸️ Deferred | ✔️ Complete | ❌ Rejected
**Priority**: Critical | High | Medium | Low
**Personas**: [Primary persona] (primary), [Secondary persona] (secondary)
**Versions**: vX.X - vY.Y

---

## Overview

**As a** [type of user]
**I want** [capability or feature]
**So that** [benefit or value]

[Additional context paragraph explaining the user story in more detail]

---

## Acceptance Criteria

### [Category Name]

#### AC-001: [Criterion Title] (vX.X)
**Given** [context or precondition]
**When** [action or trigger]
**Then** the system should:
- ✅ [Expected behaviour 1]
- ✅ [Expected behaviour 2]
- ✅ [Expected behaviour 3]
- 🚧 [Optional/deferred behaviour] (vY.Y - deferred)

**Test Coverage**: `tests/[category]/test_[feature].py`

**Success Metric**: [Quantifiable measure of success]

---

#### AC-002: [Criterion Title] (vX.X)
**Given** [context]
**When** [action]
**Then** [expected outcome]

**Test Coverage**: `tests/[category]/test_[feature].py`

---

[Repeat for all acceptance criteria, organised by category]

---

## Technical Constraints

### Platform Requirements (vX.X)
- ✅ [Constraint 1]
- ✅ [Constraint 2]
- ✅ [Constraint 3]

### Performance Requirements
- ✅ [Performance requirement 1] (vX.X)
- ✅ [Performance requirement 2] (vX.X)

### Quality Requirements
- ✅ [Quality requirement 1] (vX.X)
- ✅ [Quality requirement 2] (vX.X)

---

## Success Metrics

### Quantitative
- **[Metric 1]**: [Target value]
- **[Metric 2]**: [Target value]
- **[Metric 3]**: [Target value]

### Qualitative
- **[Metric 1]**: [Target description]
- **[Metric 2]**: [Target description]

---

## Feature Roadmap

### vX.X - [Version Name] (Weeks X-Y)
**Completion**: XX% of US-XXX

**Features**:
- ✅ [Feature 1]
- ✅ [Feature 2]
- ✅ [Feature 3]

**Acceptance Criteria**: AC-001, AC-002

---

### vX.Y - [Version Name] (Weeks X-Y)
**Completion**: XX% of US-XXX

**Features**:
- ✅ [Feature 1]
- ✅ [Feature 2]

**Acceptance Criteria**: AC-003, AC-004, AC-005

---

[Repeat for each version that delivers parts of this user story]

---

### v1.0 - Production (Weeks X-Y)
**Completion**: 100% of US-XXX

**Features**:
- ✅ All features complete
- ✅ Production-grade quality
- ✅ Complete testing
- ✅ Full documentation

**Acceptance Criteria**: All AC-XXX complete

---

## Related Personas

### Primary: [Persona Name]
**Definition**: [Link to persona definition](../../planning/core-concepts/personal-memory-personas.md#[persona-name]-persona)

**Characteristics**:
- [Characteristic 1]
- [Characteristic 2]
- [Characteristic 3]

**Configuration**:
```yaml
persona: [persona_name]
response_style: [style]
detail_level: [level]
preferred_model_tier: [tier]
memory_scope: [scope]
focus_areas:
  - [area 1]
  - [area 2]
```

### Secondary: [Persona Name] (if applicable)
[Same structure as primary]

---

## Cross-References

### Implementation
- [Link to related implementation doc](../../planning/core-concepts/[doc-name].md)
- [Link to related architecture doc](../../planning/architecture/README.md#[section])

### Architecture
- [Link to architectural decision](../../planning/architecture/README.md#[component])
- [Link to system design](../../planning/core-concepts/[doc-name].md#[section])

### Testing
- [Link to test strategy](../../planning/core-concepts/testing-strategy.md#[section])
- [Link to golden dataset](../../testing/golden-dataset/)

---

## Implementation Notes

### Technical Approach

**[Component Name]**:
```python
class ExampleImplementation:
    """Brief description of implementation approach"""

    def example_method(self, param: type) -> return_type:
        """
        Brief description of what this does

        This example shows the intended technical approach
        """
        # Implementation sketch
        pass
```

**[Another Component]**:
```python
class AnotherExample:
    """Description"""
    pass
```

[Provide code sketches, architectural notes, or technical considerations]

---

## Dependencies

### External
- **[Package name]**: [Purpose/reason]
- **[Package name]**: [Purpose/reason]

### Internal
- [Internal component] (vX.X)
- [Internal component] (vX.X)

---

## Risks & Mitigations

### Risk 1: [Risk Name]
**Risk**: [Description of what could go wrong]
**Impact**: High | Medium | Low - [Explanation of impact]
**Mitigation**:
- [Mitigation strategy 1]
- [Mitigation strategy 2]
- [Mitigation strategy 3]

### Risk 2: [Risk Name]
**Risk**: [Description]
**Impact**: High | Medium | Low - [Explanation]
**Mitigation**:
- [Strategy 1]
- [Strategy 2]

[Repeat for all significant risks]

---

## Change History

| Date | Version | Changes | Author |
|------|---------|---------|--------|
| YYYY-MM-DD | X.X | [Description of changes] | [Author name] |
| YYYY-MM-DD | X.X | [Description of changes] | [Author name] |

---

**Status**: [Current status symbol and text]
**Next Review**: [Version milestone or date]
**Owner**: [Team or person responsible]

---

## Usage Instructions

### When to Use This Template

Create a new user story when:
1. Defining new user-facing functionality
2. Documenting significant feature requests
3. Planning persona-specific capabilities
4. Establishing testable requirements

### How to Use This Template

1. **Copy template** to `docs/development/planning/requirements/user-stories/`
2. **Rename** following convention: `US-XXX-brief-description.md`
3. **Fill in all sections**:
   - Use British English throughout
   - Link to relevant personas
   - Map to implementation versions
   - Define clear acceptance criteria
   - Include success metrics
4. **Update index**: Add entry to `README.md` in user-stories folder
5. **Cross-reference**: Link from architecture and implementation docs

### Best Practices

- **Keep user-centric**: Focus on user value, not technical implementation
- **Make testable**: Every AC should be verifiable
- **Version map**: Show how story is delivered incrementally
- **Link extensively**: Connect to personas, architecture, tests
- **Use examples**: Provide code sketches and usage examples
- **Track risks**: Document what could go wrong and how to mitigate
- **Update regularly**: Keep status and completion % current

### Acceptance Criteria Guidelines

**Good AC**:
```
AC-001: PDF Document Ingestion (v0.1)
Given a PDF research paper
When I ingest it into ragged
Then the system should:
- ✅ Extract all text content
- ✅ Preserve document structure
- ✅ Extract metadata (author, title, year)
- ✅ Handle scanned PDFs with OCR

Test Coverage: tests/integration/test_pdf_ingestion.py
Success Metric: 95%+ successful ingestion rate
```

**Poor AC**:
```
The system should work with PDFs.
```

### Version Mapping Guidelines

Show progressive delivery:
```
v0.1: Basic feature (30% complete)
v0.2: Enhanced feature (60% complete)
v0.3: Advanced feature (85% complete)
v1.0: Production ready (100% complete)
```

---

## Maintenance

**Review Cycle**: Every version milestone
**Update Triggers**:
- Feature scope changes
- Acceptance criteria modifications
- Version timeline adjustments
- Technical constraint changes
- Persona evolution

**Archive When**:
- Status becomes ✔️ Complete
- Status becomes ❌ Rejected
- Superseded by new user story

---

**Template Version**: 1.0
**Last Updated**: 2025-11-09
**Maintained By**: Product/Requirements Team
