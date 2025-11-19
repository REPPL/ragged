# Intelligent Chunking Strategies

Semantic and hierarchical chunking for topic-coherent chunks with parent-child relationships, improving retrieval precision by 10-15%.

## Feature Overview

Intelligent Chunking replaces fixed-size recursive chunking with topic-aware strategies that preserve semantic boundaries and provide contextual depth. Current fixed chunking (every 1000 characters with 200 overlap) arbitrarily breaks sentences and scatters related content across chunks, degrading retrieval quality. Intelligent chunking uses semantic similarity to detect topic boundaries (semantic chunking) and creates parent-child hierarchies for broader context (hierarchical chunking).

Semantic chunking embeds sentences and identifies topic shifts when similarity drops below a threshold, ensuring chunks contain complete thoughts. Hierarchical chunking creates two levels: large parent chunks (1500-3000 chars) for context and specific child chunks (300-800 chars) for precise retrieval. When a child matches a query, its parent is included in the LLM context, improving answer completeness.

## Design Goals

1. **Retrieval Precision**: Semantic chunks improve precision by 10-15% (chunks match query topics)
2. **Answer Completeness**: Hierarchical context improves completeness by 10-15% (parent provides broader context)
3. **Topic Coherence**: Chunks contain semantically complete thoughts (no mid-sentence splits)
4. **Configurable**: Personas control chunking strategy (accuracy: hierarchical, speed: fixed, balanced: semantic)

## Technical Architecture

### Module Structure

```
src/ragged/chunking/
├── __init__.py
├── base_chunker.py             # Base interface (modified)
├── semantic_chunker.py         # Semantic chunking (250 lines)
│   └── class SemanticChunker
├── hierarchical_chunker.py     # Hierarchical chunking (350 lines)
│   └── class HierarchicalChunker
└── chunk_factory.py            # Strategy selection (100 lines)

tests/chunking/
├── test_semantic_chunker.py
├── test_hierarchical_chunker.py
└── test_integration.py
```

### Data Flow

**Semantic Chunking:**
```
Document → NLTK sentence split → Embed sentences → Calculate similarities
→ Detect boundaries (similarity < threshold) → Group into semantic chunks
```

**Hierarchical Chunking:**
```
Document → Generate parent chunks (large, 1500-3000 chars)
→ For each parent: Generate child chunks (specific, 300-800 chars)
→ Link children to parent (metadata) → Store all with parent_id
→ Retrieval: Query → child retrieved → Include parent in context
```

### API Interfaces

```python
from dataclasses import dataclass
from typing import List, Optional

@dataclass
class Chunk:
    content: str
    metadata: dict
    parent_id: Optional[str] = None
    level: str = "child"  # "parent" or "child"

class SemanticChunker:
    def __init__(self, similarity_threshold: float = 0.75):
        """Semantic chunking based on topic similarity."""
        pass

    def chunk(self, document: str) -> List[Chunk]:
        """Chunk document at semantic boundaries."""
        pass

class HierarchicalChunker:
    def __init__(
        self,
        parent_size: int = 2000,
        child_size: int = 500
    ):
        """Hierarchical chunking with parent-child relationships."""
        pass

    def chunk(self, document: str) -> List[Chunk]:
        """Create parent and child chunks."""
        pass
```

## Security & Privacy

**Privacy Risk Score**: 90/100 (Excellent)
- All processing local, no external calls
- Standard chunking operation, no sensitive data handling

## Implementation Phases

1. **Design & Research** (6-8h): Architecture planning
2. **Semantic Chunking** (10-12h): Implement sentence-level similarity
3. **Hierarchical Chunking** (18-20h): Parent-child relationships
4. **Testing & Validation** (4-6h): RAGAS comparison

## Code Examples

### Current (v0.2 - Fixed)
```python
# Fixed 1000-char chunks with 200 overlap
chunker = RecursiveChunker(chunk_size=1000, overlap=200)
chunks = chunker.chunk(document)
# Issues: Arbitrary boundaries, no topic awareness
```

### Enhanced (v0.3 - Semantic)
```python
# Semantic chunking at topic boundaries
chunker = SemanticChunker(similarity_threshold=0.75)
chunks = chunker.chunk(document)
# Benefits: Complete thoughts, topic-coherent chunks
```

### Enhanced (v0.3 - Hierarchical)
```python
# Hierarchical with parent-child
chunker = HierarchicalChunker(parent_size=2000, child_size=500)
chunks = chunker.chunk(document)

# Retrieval includes parent for context:
# Query → child retrieved → parent included → Better answers
```

## Testing Requirements

- [ ] Semantic chunker preserves topic boundaries
- [ ] Hierarchical chunker creates valid parent-child links
- [ ] RAGAS shows 10-15% improvement
- [ ] Chunk sizes within min/max constraints

## Acceptance Criteria

- [ ] Both strategies implemented and tested
- [ ] Configuration personas integrated
- [ ] RAGAS improvement validated
- [ ] Documentation complete

## Related Versions

- **v0.3.0** - Intelligent chunking implementation (38-40h)

See [v0.3.0 roadmap](../v0.3.0.md) for detailed implementation.

## Dependencies

- **nltk** (>= 3.8.0) - Apache 2.0 - Sentence splitting
- **scipy** (>= 1.11.0) - BSD - Similarity calculations

## Risk Assessment

| Risk | Mitigation |
|------|------------|
| Similarity threshold tuning | Make configurable, test diverse docs |
| Performance overhead (embeddings) | Batch embedding, cache results |
| Parent chunks too generic | Tune sizes, validate with RAGAS |

## Related Documentation

- [v0.3.0 Roadmap](../v0.3.0.md) - Detailed implementation
- [v0.3 Planning](../../../planning/version/v0.3/README.md) - Design goals
- [v0.3 Master Roadmap](../README.md) - Complete v0.3 overview

---

**Total Feature Effort:** 38-46 hours
