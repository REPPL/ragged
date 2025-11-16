# ragged v0.2 Design Overview

**Version:** v0.2

**Status:** ✅ Partially Implemented (v0.2.0-v0.2.2 released)

**Last Updated:** 2025-11-16

---

## Overview

Version 0.2 enhances ragged with improved retrieval quality, batch operations, and user experience improvements. The focus is on making ragged more practical for real-world document collections.

**Goal**: Transform from proof-of-concept to usable tool with better retrieval and operational features.

**For detailed implementation plans, see:**
- [Implementation Records](../../../implementation/version/v0.2/) - What was actually built
- [Roadmap: v0.2.3+](../../../roadmap/version/) - Planned enhancements

---

## Design Goals

### 1. Enhanced Retrieval Quality
**Problem**: Basic dense retrieval misses keyword matches and struggles with diverse query types.

**Solution**:
- Hybrid search combining BM25 (keyword) + dense embeddings
- Reciprocal Rank Fusion for combining results
- Normalised scoring for fair comparison

**Expected Impact**: 10-15% improvement in retrieval relevance

### 2. Practical Document Management
**Problem**: Adding documents one-by-one is tedious for large collections.

**Solution**:
- Folder ingestion with recursive scanning
- Batch processing with progress reporting
- Duplicate detection using content hashing
- Interactive overwrite prompts

**Expected Impact**: Can ingest entire document libraries in minutes

### 3. Model Flexibility
**Problem**: Users need to try different models for their use case.

**Solution**:
- Interactive model selection with recommendations
- RAG suitability scoring algorithm
- User configuration file (~/.ragged/config.yml)
- Model discovery from Ollama

**Expected Impact**: Users can optimise for their hardware and quality needs

### 4. User Experience
**Problem**: Cryptic errors, missing information, confusing output.

**Solution**:
- Rich console output with formatting
- Descriptive error messages with recommendations
- Batch summary statistics
- Progress bars for long operations

**Expected Impact**: More confident and efficient usage

---

## Key Features

### Implemented (v0.2.0-v0.2.2)
- ✅ Hybrid retrieval (BM25 + dense + fusion)
- ✅ Folder ingestion with recursive scanning
- ✅ Batch duplicate detection
- ✅ Interactive model selection
- ✅ Enhanced CLI output with Rich
- ✅ User configuration file support
- ✅ Metadata extraction and storage
- ✅ Content-based duplicate detection (SHA256)

### Planned (v0.2.3-v0.2.7)
- 📋 Performance optimisation (caching, async)
- 📋 Advanced metadata filtering
- 📋 Query history and bookmarks
- 📋 Export functionality
- 📋 Batch operations improvements

---

## Success Criteria

### Retrieval Quality
- ✅ Hybrid search improves relevance by >10% (vs dense-only)
- ✅ Handles both semantic and keyword queries effectively
- 📋 MRR@10 > 0.65 (to be measured)

### Usability
- ✅ Can ingest 100+ documents in single command
- ✅ Duplicate detection prevents redundant storage
- ✅ Clear progress indication for all operations
- ✅ Model selection provides actionable recommendations

### Performance
- ✅ Query latency < 2 seconds for typical collections (<1000 docs)
- 📋 Handles collections of 10,000+ documents efficiently (v0.2.7)
- 📋 Memory usage scales linearly with collection size

---

## Architecture Changes

### New Components
- **Hybrid Retriever**: Combines BM25 and dense search
- **Fusion Algorithm**: Reciprocal Rank Fusion implementation
- **Scanner Module**: Recursive directory traversal with ignore patterns
- **Batch Processor**: Multi-document ingestion pipeline
- **Model Manager**: Discovery and recommendation engine

### Modified Components
- **VectorStore**: Added hybrid search methods
- **CLI**: Enhanced with folder commands and model selection
- **Models**: Added file_hash field for duplicate detection

### Configuration
- User config file: `~/.ragged/config.yml`
- Per-directory ignore patterns
- Model preferences and defaults

---

## Trade-Offs

### Hybrid vs Dense-Only
**Benefit**: Better coverage of diverse queries
**Cost**: ~30% slower retrieval (two searches + fusion)
**Decision**: Worth it - quality > speed for RAG

### Batch vs Single-File
**Benefit**: Efficiency for large collections
**Cost**: Higher memory usage during processing
**Decision**: Acceptable - users can control batch size

### Interactive Prompts vs Silent
**Benefit**: User control over duplicates
**Cost**: Cannot fully automate ingestion
**Decision**: Auto-skip in batch mode, prompt in single mode

---

## Out of Scope (Deferred to v0.3+)

❌ **Not in v0.2**:
- Web interface (deferred)
- Advanced chunking strategies (v0.3)
- Reranking with cross-encoders (v0.3)
- Query expansion and rewrites (v0.3)
- Multi-modal support (v0.3)
- Evaluation framework (v0.3)

---

## Related Documentation

- [v0.1 Planning](../v0.1/) - Foundation design
- [v0.3 Planning](../v0.3/) - Next version design
- [Implementation Records](../../../implementation/version/v0.2/) - Actual implementation
- [Roadmaps](../../../roadmap/version/) - Detailed roadmaps for v0.2.3+
- [Architecture](../../architecture/) - System architecture
- [Core Concepts](../../core-concepts/) - Foundational concepts

---

**Maintained By:** ragged development team

**License:** GPL-3.0
