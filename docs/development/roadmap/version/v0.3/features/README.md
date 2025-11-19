# v0.3 Feature Specifications

This directory contains detailed technical specifications for each major feature area in v0.3, organised by functional domain and implementation sequence.

## Purpose

Feature specifications serve as the canonical source of technical detail for v0.3 features. Version roadmaps (v0.3.0 through v0.3.0) reference these specifications rather than duplicating content, maintaining Single Source of Truth (SSOT) compliance.

## Navigation by Category

### Core Functionality (150-165h)

**[Query Processing](./query-processing.md)** - Advanced retrieval techniques
Implements query decomposition, HyDE (Hypothetical Document Embeddings), reranking with cross-encoders, and context compression using LLMLingua.
*Implemented in:* v0.3.0, v0.3.2

**[Chunking Strategies](./chunking-strategies.md)** - Intelligent document splitting
Implements semantic chunking (embedding-based), agentic chunking (LLM-guided), and proposition-based chunking with performance comparisons.
*Implemented in:* v0.3.6

**[RAGAS Evaluation](./evaluation-quality.md)** - Quality measurement framework
Implements MRR (Mean Reciprocal Rank), NDCG (Normalised Discounted Cumulative Gain), and full RAGAS score evaluation with target >0.80.
*Implemented in:* v0.3.0 (foundation), v0.3.0 (full framework), v0.3.0 (integration testing)

### Document Intelligence (90-108h)

**[Multi-Modal Support](./multi-modal-support.md)** - OCR, tables, images with Docling
Implements Docling integration for OCR, table extraction, image/chart processing, and multi-modal embedding strategies. Target: 95% PDF success rate.
*Implemented in:* v0.3.5

### User Experience (85-95h)

**[CLI Features](./cli-features.md)** - Enhanced CLI and interactive REPL
Implements all 11 CLI enhancements (query modes, export formats, versioning, configuration management, etc.) plus interactive REPL with session management.
*Implemented in:* v0.3.0 (CLI enhancements), v0.3.0 (REPL)

### Data & Generation (50-58h)

**[Data Generation](./data-generation.md)** - LLM generation improvements
Implements chain-of-thought generation, precise character-level citations, and enhanced metadata extraction with RAGAS score >0.80.
*Implemented in:* v0.3.8

## Navigation by Implementation Order

1. **[RAGAS Evaluation](./evaluation-quality.md)** - Foundation for measuring quality (v0.3.0, v0.3.0, v0.3.0)
2. **[Query Processing](./query-processing.md)** - Core RAG improvements (v0.3.0, v0.3.0)
3. **[Multi-Modal Support](./multi-modal-support.md)** - Document intelligence (v0.3.0)
4. **[Chunking Strategies](./chunking-strategies.md)** - Advanced chunking (v0.3.0)
5. **[CLI Features](./cli-features.md)** - User experience (v0.3.0, v0.3.0)
6. **[Data Generation](./data-generation.md)** - Generation quality (v0.3.0)

## Security Integration

All features integrate with the v0.2.10/v0.2.11 security foundation:

- **Session isolation** for multi-user features (REPL, REST API)
- **Query hashing** for metrics (never plaintext storage)
- **Encryption at rest** for sensitive data (session files, history)
- **PII detection** and user warnings
- **GDPR compliance** (delete, export, access rights)

### High-Risk Features

Features requiring detailed privacy/security implementation:

| Feature | Privacy Risk | Key Security Requirements |
|---------|--------------|---------------------------|
| **CLI REPL** | 90/100 | Session isolation, encrypted history, PII warnings, TTL cleanup |
| **Metrics DB** | 95/100 | Query hashing only (no plaintext), encryption, TTL cleanup |
| **REST API** | 92/100 | Session isolation, authentication, rate limiting |

See individual version roadmaps for detailed privacy implementation sections.

## Using Feature Specifications

### For Implementers

When implementing a v0.3.X version:

1. Read the relevant feature specification(s) first
2. Follow the implementation phases defined in the spec
3. Use code examples as reference (before/after patterns)
4. Integrate security APIs as documented
5. Meet acceptance criteria before marking complete

### For Reviewers

When reviewing v0.3 implementations:

1. Verify all acceptance criteria from feature spec are met
2. Check security integration matches specification
3. Validate test coverage meets requirements
4. Confirm performance benchmarks achieved

### For Planners

When planning new features:

1. Use `TEMPLATE.md` as starting point
2. Follow hybrid security approach (summary + links)
3. Define measurable acceptance criteria
4. Break into 4-6 hour implementation phases

## Creating New Feature Specifications

Use the **[TEMPLATE.md](./TEMPLATE.md)** file as the starting point for creating new feature specifications. The template includes all required sections and follows v0.3 standards.

## Related Documentation

- [v0.3 Master Roadmap](../README.md) - Complete v0.3 overview
- [v0.3 Planning](../../../planning/version/v0.3/README.md) - High-level design goals
- [Security Policy](../../../../security/policy.md) - Security requirements
- [Privacy Architecture](../../../../security/privacy-architecture.md) - Privacy implementation details

---

**Total Feature Effort:** 375-426 hours (including all 6 feature areas)
