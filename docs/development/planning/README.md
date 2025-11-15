# Planning Documentation

**Purpose:** All forward-looking design and planning documents

**Last Updated:** 2025-11-15

---

## Overview

This directory contains all planning and design documentation for ragged—everything about what we plan to build, how it should work, and why certain approaches were chosen.

**Distinction:**
- **planning/** = Future design (what we plan to build)
- **decisions/** = Rationale (why we chose this approach)
- **implementations/** = Past reality (what we actually built)

---

## Structure

### [vision/](./vision/)
Long-term product strategy, principles, and goals

### [requirements/](./requirements/)
User needs, user stories, and functional requirements

### [architecture/](./architecture/)
System architecture, component design, and technical specifications

### [core-concepts/](./core-concepts/)
Foundational technical concepts and design patterns

### [technologies/](./technologies/)
Technology evaluations, comparisons, and selections

### [interfaces/](./interfaces/)
User interface designs (CLI and Web UI)

### [versions/](./versions/)
Version-specific high-level design plans

### [references/](./references/)
Research papers, academic materials, and external resources

---

## Document Lifecycle

```
1. Vision/Requirements → What to build
2. Architecture/Concepts → How to build it
3. Technologies → What tools to use
4. Versions → Phased implementation plan
5. → Decisions (ADRs/RFCs)
6. → Implementation
```

---

## For Contributors

**Planning a new feature:**
1. Start with vision/ to ensure alignment
2. Create requirements/ user stories
3. Design in architecture/ or core-concepts/
4. Evaluate technologies/ if needed
5. Add to appropriate versions/ roadmap
6. Document decisions in decisions/adrs/

---

## Related Documentation

- [Decisions](../decisions/) - Why we chose certain approaches
- [Roadmaps](../roadmaps/) - Implementation timelines
- [Implementations](../implementations/) - What was actually built

---

**Maintained By:** ragged development team

**License:** GPL-3.0
