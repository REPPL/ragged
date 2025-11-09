# Research Documentation

**Academic and research-oriented materials for ragged**

---

## Overview

This directory contains research materials, methodology documentation, and experimental results related to ragged's development. It supports academic reproducibility and provides context for design decisions.

## Purpose

1. **Reproducibility**: Document research methodology for academic purposes
2. **Evidence-Based Design**: Show research backing architectural decisions
3. **Benchmarking**: Track performance and quality metrics over time
4. **Knowledge Sharing**: Contribute to RAG research community

## Directory Structure

```
research/
├── README.md (this file)
├── background/              # Research background (migrated from project-setup)
│   ├── rag-landscape.md
│   ├── vector-databases.md
│   └── ...
├── methodology/             # Research methods
│   └── (Will be added as experiments are conducted)
├── experiments/             # Experimental results
│   └── (Will be added during development)
├── benchmarks/              # Performance benchmarks
│   └── (Will be added starting v0.2)
└── citations.md             # Bibliography of referenced papers

## Available Research Materials

### Background Research

**Migrated from `project-setup/background/`**:
- Research on RAG landscape
- Vector database comparisons
- Embedding model evaluations
- Chunking strategy research

These materials informed ragged's initial design.

### Planned Research Documentation

**Methodology** (v0.2+):
- Evaluation framework design (RAGAS)
- Benchmark dataset creation
- Quality metrics definitions
- Reproducibility protocols

**Experiments** (v0.3+):
- Chunking strategy comparisons
- Embedding model evaluations
- Retrieval method benchmarks
- User study results (if conducted)

**Benchmarks** (v0.2+):
- Retrieval accuracy metrics
- Response quality measurements
- Performance benchmarks (speed, memory)
- Comparison to other RAG systems

## Research Principles

### Open Science

- All research methods documented
- Data and code publicly available (where possible)
- Negative results published (what didn't work)
- Reproducibility prioritized

### Evidence-Based

- Design decisions backed by research
- Claims supported by data
- Benchmarks reported honestly
- Limitations acknowledged

### Community Contribution

- Share findings with RAG research community
- Publish benchmarks for comparison
- Contribute to open datasets
- Cite and acknowledge sources

## Citing ragged Research

If you use ragged or its research materials in academic work:

### In-Text Citation

> The ragged project documented a transparent AI-assisted development process
> including time tracking and architectural decisions (ragged Project, 2025).

### Bibliography Entry

```
ragged Project. (2025). ragged: Privacy-First Local RAG System - Development
Documentation and Research. GitHub. https://github.com/REPPL/ragged/tree/main/docs
```

### Specific Documents

For citing specific research documents, use git commit hash:

```
ragged Project. (2025). Document Normalization Pipeline Design [commit abc123].
Retrieved from https://github.com/REPPL/ragged/blob/abc123/docs/implementation/plan/core-concepts/document-normalization.md
```

## Research Questions ragged Addresses

### AI-Assisted Development

1. How effective are AI coding tools for RAG system development?
2. What tasks benefit most/least from AI assistance?
3. How much time do AI tools save in practice?
4. What are the quality trade-offs?

**Data Source**: `docs/development/time-logs/`

### RAG Architecture

1. Does markdown normalization improve retrieval quality?
2. How do different chunking strategies affect accuracy?
3. What's the optimal chunk size for different document types?
4. How effective is duplicate detection in real datasets?

**Data Source**: Benchmarks and experiments (coming in v0.2+)

### Privacy-First RAG

1. Can local RAG match cloud-based quality?
2. What are the performance trade-offs?
3. How does it scale with large document collections?

**Data Source**: Benchmarks (coming in v0.2+)

## Experimental Design

### Evaluation Framework (Planned for v0.2)

**Metrics**:
- **Retrieval Accuracy**: Precision, recall, F1 score
- **Response Quality**: Faithfulness, relevance, coherence (RAGAS)
- **Performance**: Latency, throughput, memory usage
- **User Experience**: Qualitative feedback (if user studies conducted)

**Benchmarks**:
- Standard RAG benchmarks (if available)
- Custom benchmark on academic papers (user's dataset)
- Custom benchmark on web articles (user's dataset)

**Methodology**:
- Document methodology before experiments
- Use consistent datasets across versions
- Report all results (including failures)
- Open data and code where possible

## Data Availability

### What Will Be Public

✅ Aggregated performance metrics
✅ Benchmark results on public datasets
✅ Research methodology documentation
✅ Code for experiments

### What Will Be Private

❌ User's actual document collection (privacy)
❌ Specific document contents used in testing
❌ Any personally identifiable information

**Note**: Benchmarks will use public or synthetic datasets only.

## Contribution to RAG Research

ragged aims to contribute:

1. **Open Dataset**: Benchmarking tasks for local RAG systems
2. **Evaluation Metrics**: Quality measurements for privacy-first RAG
3. **Implementation Case Study**: Transparent AI-assisted development
4. **Reproducible Research**: Fully documented development process

## Reproducibility Checklist

For each research claim in ragged documentation:

- [ ] Methodology documented
- [ ] Data sources identified
- [ ] Code/configuration provided
- [ ] Results reported with confidence intervals
- [ ] Limitations acknowledged
- [ ] Reproduction steps clear

## Future Research Directions

**Short-term** (v0.2-v0.3):
- Chunking strategy effectiveness
- Metadata extraction accuracy
- Duplicate detection precision/recall

**Medium-term** (v0.4-v0.5):
- Self-RAG effectiveness
- GraphRAG quality improvements
- Adaptive retrieval benefits

**Long-term** (v1.0+):
- Production deployment case studies
- User study results
- Comparison to commercial RAG systems

## Questions?

- **Research Collaboration**: [GitHub Discussions](https://github.com/REPPL/ragged/discussions)
- **Academic Inquiries**: See README for contact information
- **Citing ragged**: Use formats above or ask in discussions

---

**Status**: Research materials being collected during planning and development.

**Next Steps**:
1. Organize migrated background research
2. Design evaluation framework (v0.2)
3. Conduct first benchmarks (v0.2)
4. Document experimental methodology

---

**Related Documentation**:
- [Development Process](../development/) - How ragged is built
- [Implementation Plan](../implementation/plan/) - Technical architecture
- [Explanation](../explanation/) - Conceptual understanding
