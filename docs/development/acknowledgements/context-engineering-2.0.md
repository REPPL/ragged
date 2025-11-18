# Context Engineering 2.0

**Source**: arXiv:2510.26493 - "Context Engineering 2.0: The Context of Context Engineering"
**Authors**: Qishuo Hua, Lyumanshan Ye, Dayuan Fu, Yang Xiao, Xiaojie Cai, Yunze Wu, Jifan Lin, Junfei Wang, Pengfei Liu
**Institution**: GAIR (Generative AI Research), Shanghai
**Published**: 30 October 2025
**Repository**: https://github.com/GAIR-NLP/Context-Engineering-2.0
**Paper**: https://arxiv.org/abs/2510.26493
**License**: Research paper (arXiv)

---

## Overview

Theoretical framework positioning context engineering as entropy reduction—transforming high-entropy human intentions into low-entropy, machine-understandable formats through systematic information organisation.

**Key Innovation**: Four-stage evolutionary model (CE 1.0→4.0) mapping context engineering progression from basic context provision through meta-level self-optimising systems.

---

## What We Borrowed

### 1. Entropy Reduction Framework (All Versions)
**Original**: Context engineering as process of reducing computational uncertainty through structured information organisation

**Adapted for ragged**: Theoretical foundation for knowledge graphs, retrieval architecture, and personalisation—framing these as uncertainty reduction mechanisms

**Differences**: Applied to personal knowledge management (not general AI), privacy-first local-only context, single-user optimisation

### 2. Structured Context Layering (v0.4.4-v0.4.8)
**Original**: Hierarchical organisation of information by relevance with clear reasoning pathways

**Adapted for ragged**: Knowledge graph structure as layered context (entities → topics → documents → temporal relationships), multi-stage retrieval as progressive context refinement

**Differences**: Local-only graph storage (Kuzu), privacy-preserving context, simpler hierarchy for single-user use

### 3. Context-Aware Retrieval (v0.4.6, v0.6.0)
**Original**: Matching context selection to specific task requirements beyond keyword matching

**Adapted for ragged**: Personalised ranking based on learned interests, query classification driving context scope, intelligent retrieval strategy selection

**Differences**: User-centric personalisation (vs task-centric), privacy-preserving learning, local-only adaptation

### 4. Dynamic Context Adaptation (v0.6.0)
**Original**: Adjusting context scope based on task complexity and resource constraints

**Adapted for ragged**: Query complexity → context scope mapping (simple queries use narrow recent context, complex queries leverage full knowledge graph + temporal memory)

**Differences**: Optimised for local compute constraints, user control over context breadth, privacy-preserving adaptation

### 5. Knowledge Graph Integration (v0.4.4)
**Original**: Structuring factual relationships for clearer reasoning and multi-hop queries

**Adapted for ragged**: Temporal knowledge graphs connecting entities, topics, documents across time for personal knowledge queries

**Differences**: Personal knowledge focus (not general facts), privacy-first local storage (Kuzu), temporal dimension for personal memory

### 6. Context Compression (v0.6.0)
**Original**: Summarising large document sets while preserving critical information

**Adapted for ragged**: Chain-of-context patterns for complex queries, efficient context use on resource-constrained local systems

**Differences**: Optimised for local inference, user-visible compression controls, privacy-preserving summarisation

---

## Key Differences

**Philosophy**:
- **Source**: General framework for AI context management
- **ragged**: Privacy-first personal knowledge assistant, 100% local

**Scope**:
- **Source**: Covers CE 1.0→4.0 evolutionary stages (including speculative future)
- **ragged**: Focuses on proven CE 2.0 techniques, incremental adoption

**Implementation**:
- **Source**: Theoretical research framework
- **ragged**: Practical implementation in local-only RAG system

---

## Implementation Timeline

| Version | Features | Status |
|---------|----------|--------|
| v0.4.4-v0.4.8 | Knowledge graphs as structured context | Planned Q3 2026 |
| v0.4.6 | Context-aware personalised ranking | Planned |
| v0.6.0 | Dynamic context adaptation, compression | Planned Q4 2026 |
| v1.x | Multi-agent context coordination | Planned 2027 |

---

## Related

- [Knowledge Graph ADR](../decisions/adrs/) (when created)
- [v0.4.4 Roadmap](../roadmap/version/v0.4.0/v0.4.4.md)
- [v0.4.6 Roadmap](../roadmap/version/v0.4.0/v0.4.6.md)
- [v0.4.8 Roadmap](../roadmap/version/v0.4.0/v0.4.8.md)

---

## Attribution

This work draws theoretical inspiration from **Context Engineering 2.0** research by **GAIR (Generative AI Research)**.

The entropy reduction framework provides valuable theoretical grounding for ragged's knowledge graph, retrieval architecture, and personalisation features. The recognition that context engineering extends beyond prompt engineering to encompass systematic information organisation has influenced ragged's architectural design.

We are grateful to the GAIR team for their research that helps contextualise ragged's design philosophy: reducing uncertainty in personal knowledge retrieval through structured context (knowledge graphs, personalisation, temporal memory).

**Original research**: https://arxiv.org/abs/2510.26493

---

## License Compatibility

**Source License**: Research paper (arXiv)
**ragged License**: GPL-3.0
**Compatibility**: ✅ Compatible (theoretical concepts, no code implementation in source)
