# Autonomous Agentic RAG

**Source**: https://github.com/FareedKhan-dev/autonomous-agentic-rag
**Author**: Fareed Khan ([GitHub](https://github.com/FareedKhan-dev))
**License**: To be verified from repository

---

## Overview

Self-improving RAG system for clinical trial design with autonomous evolution of Standard Operating Procedures through multi-agent collaboration and Pareto optimisation.

**Key Innovations**:
- Hierarchical multi-agent architecture (guild-level + director-level agents)
- Differentiated model strategy (cost-performance optimisation)
- Self-improving system that evolves its own procedures
- Multi-dimensional evaluation with Pareto front analysis
- LangGraph orchestration for complex workflows

---

## Concepts Borrowed

### 1. Differentiated Model Strategy (v0.5.1)
**Original**: Different LLMs for different cognitive loads (Llama 3.1 8B for planning, Llama 3 70B for strategic reasoning)

**Adapted for ragged**: Query complexity analysis with automatic model routing for general-purpose knowledge management, using Ollama for local-only deployment

**Differences**: ragged focuses on personal knowledge (vs clinical trials), privacy-first local-only execution, simplified routing for single-user context

### 2. Self-Improving Query Strategies (v0.5.2, v0.6.1)
**Original**: Autonomous SOP evolution through performance diagnostician and SOP architect agents

**Adapted for ragged**: Strategy evolution for retrieval approaches (BM25, dense, hybrid, reranking) based on success metrics

**Differences**: ragged focuses on retrieval strategies (not full SOPs), simpler optimisation, privacy-preserving local learning

### 3. Multi-Agent Orchestration (v1.x)
**Original**: Guild-level specialist agents (Medical Researcher, Regulatory, Ethics, Clinical Designer) with director-level strategy agents

**Adapted for ragged**: Customisable specialist agents (domain-agnostic), director agents for strategy optimisation, human-in-the-loop decision points, optional domain-specific agent plugins

**Differences**: General-purpose agents (not clinical domain), plugin-based extensibility, simpler for single-user context, emphasis on explainability

### 4. Compliance & Governance Frameworks (v2.x)
**Original**: FDA regulatory integration, ethics and safety reviews, multi-dimensional compliance scoring

**Adapted for ragged**: Configurable compliance frameworks, audit trails and provenance tracking, enterprise governance features, privacy-preserving compliance

**Differences**: Framework-agnostic (not FDA-specific), privacy-first compliance with local audit trails, optional enterprise feature

### 5. Multi-Dimensional Evaluation (v0.5.3)
**Original**: Performance evaluation across accuracy, feasibility, compliance, ethics with radar charts and Pareto visualisation

**Adapted for ragged**: Extended evaluation framework adding conciseness, citation quality, source diversity, confidence metrics to existing MRR, NDCG, RAGAS

**Differences**: Domain-agnostic quality dimensions, focus on retrieval + generation quality, user-facing trade-off visualisation

---

## Key Differences

**Philosophy**:
- **Source**: Enterprise healthcare, cloud-capable, multi-user
- **ragged**: Personal knowledge, 100% local, privacy-first, single-user

**Domain**:
- **Source**: Clinical trial design (specialised)
- **ragged**: General-purpose knowledge management

**Architecture**:
- ragged builds on existing plugin system (v0.4.1)
- Simpler agent hierarchy for personal use
- Emphasis on user control and explainability

---

## Implementation Timeline

| Version | Features | Status |
|---------|----------|--------|
| v0.5.1 | Differentiated model strategy | Planned |
| v0.5.2 | Self-improving query strategies | Planned |
| v0.5.3 | Multi-dimensional evaluation | Planned |
| v1.2.0 | Multi-agent orchestration | Planned |
| v2.1.0 | Compliance frameworks | Planned |

---

## Related Inspirations

- [Mem0](./mem0.md) - Personalised memory layer (when created)
- [Graphiti](./graphiti.md) - Temporal knowledge graphs (when created)
- [LangGraph](./langgraph.md) - Agent workflow orchestration (when created)

---

## Attribution

This work builds upon innovative concepts from **Autonomous Agentic RAG** by **Fareed Khan**.

We are grateful for their open-source contribution and the novel approach they pioneered in self-improving RAG systems. Their insight that RAG system design forms a "high dimensional vector space" that can be optimised autonomously has significantly influenced ragged's development roadmap.

**Original project**: https://github.com/FareedKhan-dev/autonomous-agentic-rag

---

## License Compatibility

**Source License**: To be verified
**ragged License**: GPL-3.0
**Note**: Concepts and patterns adapted, not code copied. Implementation is original to ragged.
