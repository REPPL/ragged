# [Feature Name]

*[One sentence description of what this feature does and why it matters]*

## Feature Overview

*[2-3 paragraphs explaining:
- What problem this feature solves
- Why users need this feature
- How it fits into the broader v0.3 vision
- Key innovations or differentiators]*

## Design Goals

*[List measurable success criteria. Use specific metrics, not vague statements.]*

1. **[Goal Category]**: [Specific measurable outcome]
   - Example: **Performance**: Query latency < 500ms for 95th percentile
   - Example: **Quality**: RAGAS score > 0.80 on evaluation dataset

2. **[Goal Category]**: [Specific measurable outcome]

3. **[Goal Category]**: [Specific measurable outcome]

## Technical Architecture

### Module Structure

```
[Project directory tree showing where files will be created]
src/
└── ragged/
    └── [feature-module]/
        ├── __init__.py
        ├── core.py
        ├── [specific-component].py
        └── utils.py
```

### Data Flow

```
[ASCII diagram showing data flow through the system]

User Input → [Component 1] → [Component 2] → Output
                   ↓
            [Component 3]
                   ↓
            [Component 4]
```

### API Interfaces

```python
"""[Module docstring]"""

from typing import [Relevant types]


class [MainComponent]:
    """[Class docstring describing purpose and usage]"""

    def __init__(
        self,
        param1: [Type],
        param2: [Type],
        optional_param: [Type] = [default],
    ):
        """
        Initialise [component].

        Args:
            param1: [Description]
            param2: [Description]
            optional_param: [Description]
        """
        pass

    def main_method(
        self,
        input_param: [Type],
    ) -> [ReturnType]:
        """
        [Method description].

        Args:
            input_param: [Description]

        Returns:
            [Description of return value]

        Raises:
            [ExceptionType]: [When this exception is raised]
        """
        pass
```

### Integration Points

*[List how this feature integrates with existing ragged components]*

- **[Component 1]**: [How they interact]
- **[Component 2]**: [How they interact]
- **[External dependency]**: [Purpose and integration method]

## Security & Privacy

### Requirements

*[High-level security/privacy requirements for this feature]*

- [Requirement 1: e.g., "User queries must be hashed before storage"]
- [Requirement 2: e.g., "Session isolation required for multi-user scenarios"]
- [Requirement 3: e.g., "Encryption at rest for sensitive data"]

### Privacy Risk Score

**Score**: [90-100/100] ([Excellent/Good/Moderate])

**Justification**:
*[Explain why this score was assigned. Consider:
- Data sensitivity (what data is collected/stored)
- User identifiability (can data identify users?)
- Retention period (how long is data kept?)
- Access controls (who can access the data?)]*

### Integration with Security Foundation

**Requires**: v0.2.10 (Session Isolation), v0.2.11 (Encryption, PII Detection)

**Key APIs Used**:

```python
from ragged.session import SessionManager, Session
from ragged.privacy import (
    EncryptionManager,
    hash_query,
    contains_pii,
    redact_pii,
    CleanupScheduler,
)

# Example integration code showing how this feature uses security APIs
session_mgr = SessionManager()
session = session_mgr.get_or_create_session()

# [Feature-specific implementation]
```

### Detailed Policies

- [Security Policy](../../../../security/policy.md#relevant-section) - [What aspect]
- [Privacy Architecture](../../../../security/privacy-architecture.md#relevant-section) - [What aspect]

## Implementation Phases

### Phase 1: [Phase Name] (Xh)

**Objective**: [What this phase achieves]

**Steps**:
1. [Specific implementation step]
2. [Specific implementation step]
3. [Specific implementation step]

**Dependencies**: [What must exist before this phase]

**Deliverables**:
- [Deliverable 1]
- [Deliverable 2]

**Verification**:
- [ ] [How to verify this phase is complete]
- [ ] [Specific test or check]

### Phase 2: [Phase Name] (Xh)

*[Repeat structure from Phase 1]*

### Phase 3: [Phase Name] (Xh)

*[Repeat structure from Phase 1]*

## Code Examples

### Current Behaviour (v0.2.X)

```python
# Simple/basic implementation showing current state
[Code example]
```

### Enhanced Behaviour (v0.3.X)

```python
# Enhanced implementation showing new functionality
from ragged.[feature-module] import [Component]

# Example demonstrating the feature in action
[Code example]
```

### Security Integration Example

```python
# Example showing how security APIs are integrated
from ragged.session import SessionManager
from ragged.privacy import hash_query, EncryptionManager

# [Feature-specific code using security foundation]
[Code example]
```

**Why This Improvement Matters**

*[1-2 sentences explaining the user-facing benefit of this enhancement]*

## Testing Requirements

### Unit Tests

*[Describe unit test coverage requirements]*

- [ ] [Component 1] unit tests (>80% coverage)
- [ ] [Component 2] unit tests (>80% coverage)
- [ ] Edge cases covered ([specific edge cases])

### Integration Tests

*[Describe integration test requirements]*

- [ ] [Integration scenario 1]
- [ ] [Integration scenario 2]
- [ ] Error handling and recovery

### End-to-End Tests

*[Describe e2e test requirements]*

- [ ] [User workflow 1]
- [ ] [User workflow 2]
- [ ] Performance benchmarks met

### Security Tests

*[If applicable - describe security testing requirements]*

- [ ] Session isolation verified (no cross-user data leakage)
- [ ] PII detection accuracy (100+ test cases)
- [ ] Encryption round-trip validated
- [ ] Query hashing verified (no plaintext in logs)

### Performance Benchmarks

*[Define specific performance targets]*

| Metric | Target | Measurement Method |
|--------|--------|-------------------|
| [Metric 1] | [Target value] | [How to measure] |
| [Metric 2] | [Target value] | [How to measure] |

## Acceptance Criteria

*[Go/no-go checklist for considering this feature complete]*

- [ ] All implementation phases complete
- [ ] All tests passing (unit, integration, e2e)
- [ ] Performance benchmarks met
- [ ] Security requirements satisfied (if applicable)
- [ ] Documentation complete (docstrings, user guides)
- [ ] Code review approved
- [ ] `/verify-docs` passing
- [ ] British English compliance

## Related Versions

*[List which v0.3.X versions implement this feature]*

- **v0.3.X** - [What aspect is implemented] (Xh)
- **v0.3.Y** - [What aspect is implemented] (Yh)

See individual version roadmaps for detailed implementation plans.

## Dependencies

### From v0.2.10/v0.2.11 (Security Foundation)

*[If applicable - list required security APIs]*

- `SessionManager` - [What it provides]
- `EncryptionManager` - [What it provides]
- `hash_query()` - [What it provides]

### External Libraries

*[List third-party dependencies]*

- **[Library name]** (version): [Purpose]
- **[Library name]** (version): [Purpose]

### Hardware/System Requirements

*[If applicable - list special requirements]*

- [Requirement 1: e.g., "GPU with 8GB+ VRAM for optimal performance"]
- [Requirement 2: e.g., "Minimum 16GB RAM for large document processing"]

## Risk Assessment

### Technical Risks

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| [Risk description] | [High/Medium/Low] | [High/Medium/Low] | [How to mitigate] |
| [Risk description] | [High/Medium/Low] | [High/Medium/Low] | [How to mitigate] |

### Performance Risks

*[Identify potential performance bottlenecks and optimisation strategies]*

- **[Bottleneck 1]**: [Description and mitigation]
- **[Bottleneck 2]**: [Description and mitigation]

### Security/Privacy Risks

*[If applicable - identify security/privacy concerns]*

- **[Risk 1]**: [Description and mitigation]
- **[Risk 2]**: [Description and mitigation]

## Related Documentation

- [v0.3.X Roadmap](../v0.3.X.md) - Detailed implementation for version X
- [v0.3 Planning](../../../planning/version/v0.3/README.md) - High-level design goals
- [v0.3 Master Roadmap](../README.md) - Complete v0.3 overview
- [Security Policy](../../../../security/policy.md) - Security requirements
- [ADR-XXX](../../../../decisions/adrs/XXX-title.md) - Related architectural decision

---

**Total Feature Effort:** X-Y hours
