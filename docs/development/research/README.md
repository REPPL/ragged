# Development Research

Technical research and analysis conducted during ragged development.

## Purpose

This directory contains in-depth technical research on technologies, architectures, and approaches being considered for future ragged features. Research here informs design decisions documented in `/docs/development/planning/` and `/docs/development/decisions/`.

## Contents

### Multi-Modal & Vision Research

- [ColPali Architecture](./colpali-architecture.md) - Vision Language Model research for v0.5.0 multi-modal document processing

## What Belongs Here

**Research documentation includes:**
- Technical architecture analysis of third-party models/systems
- Comparative technology evaluations
- Performance benchmarking studies
- Proof-of-concept findings
- Academic paper summaries relevant to ragged
- Technology landscape surveys

**This is for:** Deep dives into specific technologies before committing to implementation decisions.

## What Doesn't Belong Here

- **Design decisions** → Use `/docs/development/decisions/adrs/`
- **High-level feature planning** → Use `/docs/development/planning/`
- **Implementation details** → Use `/docs/development/implementation/`
- **General background knowledge** → Use `/docs/research/` or `/docs/explanation/`
- **External research papers** → Link to original sources rather than duplicating

## Research Workflow

1. **Identify need**: Feature planning identifies knowledge gaps
2. **Conduct research**: Create research document in this directory
3. **Make decision**: Research informs ADR in `/docs/development/decisions/adrs/`
4. **Plan implementation**: Decision leads to planning docs in `/docs/development/planning/`
5. **Archive/reference**: Research remains available for future reference

## Research Document Format

Research documents should include:
- **Executive Summary**: Key findings in 2-3 sentences
- **Architecture/Technical Details**: In-depth analysis
- **Evaluation Criteria**: How the technology was assessed
- **Recommendations**: Clear guidance for decision-makers
- **References**: Links to original sources, papers, documentation

## Related Documentation

- [Background Research](../../research/) - General RAG and AI background knowledge
- [Architecture Decision Records](../decisions/adrs/) - Decisions informed by this research
- [Version Planning](../planning/version/) - Feature planning that drives research needs
- [Technology Planning](../planning/technologies/) - Technology selection and integration plans

---

**Status**: Active research area for v0.5.0 and beyond
