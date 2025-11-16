# ragged v0.4 Design Overview

**Version:** v0.4

**Status:** 📋 Planned

**Last Updated:** 2025-11-16

---

## Overview

Version 0.4 introduces a **Personal Memory System** and **Knowledge Graphs**, transforming ragged from a document retrieval tool into an intelligent personal knowledge assistant that learns from your interactions—all locally.

**Goal**: Make ragged remember what you care about and provide increasingly personalised responses over time.

**For detailed implementation plans, see:**
- [Roadmap: v0.4.0](../../../roadmaps/version/v0.4.0/) - Personal memory & knowledge graphs (180-225 hours)

---

## Design Goals

### 1. Personal Memory System
**Problem**: Every query starts from scratch, no learning or personalisation.

**Solution**:
- Persona management (work, research, personal contexts)
- Behaviour learning from query patterns
- Temporal memory (what you worked on when)
- Interest tracking and topic preferences

**Expected Impact**: Responses tailored to your interests and context

### 2. Knowledge Graphs
**Problem**: Documents exist in isolation, no understanding of relationships.

**Solution**:
- Entity extraction and linking
- Topic and concept mapping
- Document relationship graphs
- Multi-hop reasoning across documents

**Expected Impact**: Better understanding of complex, interconnected topics

### 3. Personalised Ranking
**Problem**: Retrieval ignores your preferences and history.

**Solution**:
- Interest-based boosting
- Recency boosting for recent topics
- Project-aware relevance
- Context-sensitive ranking

**Expected Impact**: Most relevant documents appear first, based on your usage

### 4. Plugin Architecture
**Problem**: Can't extend ragged with custom functionality.

**Solution**:
- Plugin system for custom embedders
- Custom retrieval strategies
- Custom chunking strategies
- Hook system for workflow integration

**Expected Impact**: Community can extend ragged for specialized use cases

---

## Key Features

- **Persona Management**: Switch contexts (work/research/personal)
- **Knowledge Graphs**: Connect topics, documents, concepts
- **Temporal Memory**: Track what you worked on when
- **Interest Learning**: Automatically learn from query patterns
- **Personalised Retrieval**: Boost documents based on your interests
- **Plugin System**: Extend with custom functionality

---

## Success Criteria

- Personalized ranking improves relevance by >20%
- Knowledge graph enables multi-hop reasoning
- Plugin system allows community extensions
- Memory system works entirely locally (no cloud)
- Temporal queries work ("what did I read about ML last week?")

---

## Total Effort

**180-225 hours** across personal memory, knowledge graphs, and plugins

**Timeline:** ~4-6 months with single developer

---

## Out of Scope (Deferred to v0.5+)

❌ **Not in v0.4**:
- Vision-based retrieval (v0.5)
- Multi-modal embeddings (v0.5)
- Web UI (v1.0)
- Multi-user support (v1.0)

---

## Related Documentation

- [v0.3 Planning](../v0.3/) - Advanced retrieval & multi-modal
- [v0.5 Planning](../v0.5/) - Vision integration
- [Roadmap: v0.4.0](../../../roadmaps/version/v0.4.0/) - Detailed implementation plan
- [Architecture](../../architecture/) - System architecture

---

**Maintained By:** ragged development team

**License:** GPL-3.0
