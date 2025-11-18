# Research Notes

**Purpose**: Track external research, articles, and academic papers relevant to ragged's development

---

## Overview

This directory contains research notes analysing external sources that inform ragged's design but don't necessarily warrant formal acknowledgement. These notes help distinguish between:

- **Formal acknowledgements** (`docs/development/acknowledgements/`) - Original research ragged implements or draws significant inspiration from
- **Research notes** (here) - Background research, future considerations, or well-established techniques

---

## When to Create Research Notes vs Acknowledgements

### Research Note (this directory)

Create a research note when:
- ✅ Technique is well-established (no specific source to attribute)
- ✅ Feature already independently planned before encountering source
- ✅ Educational article compiling existing knowledge (not original research)
- ✅ Future consideration not yet implemented in ragged
- ✅ Background research informing general understanding

### Formal Acknowledgement (`docs/development/acknowledgements/`)

Create acknowledgement file when:
- ✅ Original academic research with novel contribution
- ✅ Specific technique implemented in ragged roadmap
- ✅ Significant influence on architectural decisions
- ✅ ragged borrows concepts, algorithms, or approaches

---

## Available Research Notes

### [RAG Latency Optimisation](./rag-latency-optimisation.md)

**Topics Covered**:
- Semantic chunking for attention optimisation
- REFRAG: Dynamic retrieval during decoding
- Speculative RAG (Google Research)
- Streaming, parallel processing, and caching techniques

**Status**: Informs v0.6.0 latency optimisation features

**Sources Analysed**:
- Florian June's "RAG Too Slow? 97% Latency Reduction" (Medium article)
- arXiv:2509.01092v1 - "REFRAG: Rethinking RAG based Decoding"
- arXiv:2407.08223 - "Speculative RAG" (Google Research)

---

## Research Note Template

When creating new research notes, include:

1. **Source Information**
   - Title, authors, publication, URL
   - Date accessed
   - License/copyright status

2. **Key Concepts Summary**
   - Main innovations or techniques
   - Claimed performance improvements
   - Trade-offs and limitations

3. **Relevance Assessment**
   - How it applies to ragged's architecture
   - Current implementation status
   - Future applicability

4. **Attribution Decision**
   - Why research note vs formal acknowledgement
   - Whether to revisit decision when implemented

5. **Related Documentation**
   - Links to roadmap features
   - Links to formal acknowledgements
   - Links to implementation plans

---

## Contributing Research Notes

When encountering relevant external research:

1. **Evaluate Attribution Need**
   - Is this original research or compilation?
   - Does ragged already have this planned independently?
   - Would formal acknowledgement be appropriate?

2. **Create Note or Acknowledgement**
   - Research note: Add to this directory
   - Formal acknowledgement: Add to `docs/development/acknowledgements/`

3. **Update This README**
   - Add link to new research note
   - Brief description of topics covered

4. **Link from Roadmap**
   - If relevant to specific features, link from roadmap documentation

---

## Related Documentation

- [Formal Acknowledgements](../../development/acknowledgements/) - Projects and research ragged formally acknowledges
- [Development Roadmap](../../development/roadmap/) - Feature planning and implementation timeline
- [Research Background](../background/) - Initial research that informed ragged's design

---

**Maintained By**: ragged development team
**License**: GPL-3.0
**Last Updated**: 2025-11-18
