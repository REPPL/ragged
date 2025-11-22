## Part 2: Advanced Chunking Strategies (28 hours)

### FEAT-005: Semantic Chunking

**Priority**: High
**Estimated Time**: 10 hours
**Impact**: More coherent chunks, better retrieval
**Research**: "Dense Passage Retrieval for Open-Domain Question Answering"

#### Problem
Fixed-size chunking can split related content or group unrelated content. Semantic chunking creates chunks based on topic coherence.

#### Implementation

```python
# src/chunking/semantic.py (NEW FILE)
"""Semantic chunking based on topic coherence."""
from typing import List
import numpy as np
from scipy.spatial.distance import cosine
from src.embeddings.base import BaseEmbedder

class SemanticChunker:
    """
    Create chunks based on semantic coherence.

    Splits text at points where topic changes significantly.
    """

    def __init__(
        self,
        embedder: BaseEmbedder,
        similarity_threshold: float = 0.7,
        min_chunk_size: int = 100,
        max_chunk_size: int = 1000
    ):
        """
        Initialize semantic chunker.

        Args:
            embedder: Embedding model for computing similarity
            similarity_threshold: Similarity below which to split (0-1)
            min_chunk_size: Minimum tokens per chunk
            max_chunk_size: Maximum tokens per chunk
        """
        self.embedder = embedder
        self.similarity_threshold = similarity_threshold
        self.min_chunk_size = min_chunk_size
        self.max_chunk_size = max_chunk_size

    def chunk(self, document: Document) -> List[Chunk]:
        """
        Chunk document using semantic similarity.

        Process:
        1. Split into sentences
        2. Embed each sentence
        3. Compute sentence-to-sentence similarity
        4. Split at low-similarity boundaries
        5. Merge small chunks, split large chunks

        Args:
            document: Document to chunk

        Returns:
            List of semantically coherent chunks
        """
        # Split into sentences
        sentences = self._split_sentences(document.text)

        if len(sentences) <= 1:
            return [Chunk(text=document.text, metadata=document.metadata)]

        # Embed sentences (batch for efficiency)
        sentence_embeddings = self.embedder.embed_batch(sentences)

        # Find split points based on similarity
        split_indices = self._find_split_points(
            sentences,
            sentence_embeddings
        )

        # Create chunks
        chunks = self._create_chunks_from_splits(
            sentences,
            split_indices,
            document.metadata
        )

        # Enforce size constraints
        chunks = self._enforce_size_constraints(chunks)

        return chunks

    def _find_split_points(
        self,
        sentences: List[str],
        embeddings: np.ndarray
    ) -> List[int]:
        """
        Find indices where to split based on semantic similarity.

        Splits at points where consecutive sentences have low similarity.
        """
        split_indices = [0]  # Always start at 0

        for i in range(len(sentences) - 1):
            # Compute similarity between consecutive sentences
            sim = 1 - cosine(embeddings[i], embeddings[i + 1])

            # Also consider similarity to chunk average
            chunk_start = split_indices[-1]
            chunk_embedding = np.mean(embeddings[chunk_start:i+1], axis=0)
            sim_to_chunk = 1 - cosine(embeddings[i + 1], chunk_embedding)

            # Split if similarity drops below threshold
            if sim < self.similarity_threshold or sim_to_chunk < self.similarity_threshold:
                split_indices.append(i + 1)

        split_indices.append(len(sentences))  # Always end at end

        return split_indices

    def _create_chunks_from_splits(
        self,
        sentences: List[str],
        split_indices: List[int],
        metadata: dict
    ) -> List[Chunk]:
        """Create chunks from split points."""
        chunks = []

        for i in range(len(split_indices) - 1):
            start = split_indices[i]
            end = split_indices[i + 1]

            chunk_sentences = sentences[start:end]
            chunk_text = " ".join(chunk_sentences)

            chunk = Chunk(
                text=chunk_text,
                metadata=metadata.copy()
            )
            chunk.metadata['chunk_method'] = 'semantic'
            chunk.metadata['sentence_count'] = len(chunk_sentences)

            chunks.append(chunk)

        return chunks

    def _enforce_size_constraints(self, chunks: List[Chunk]) -> List[Chunk]:
        """
        Enforce min/max chunk sizes.

        Merges chunks that are too small, splits chunks that are too large.
        """
        result = []
        i = 0

        while i < len(chunks):
            chunk = chunks[i]
            chunk_size = len(chunk.text.split())

            # If too small, merge with next
            if chunk_size < self.min_chunk_size and i < len(chunks) - 1:
                next_chunk = chunks[i + 1]
                merged = Chunk(
                    text=chunk.text + " " + next_chunk.text,
                    metadata=chunk.metadata.copy()
                )
                result.append(merged)
                i += 2  # Skip next chunk (merged)

            # If too large, split
            elif chunk_size > self.max_chunk_size:
                # Use recursive splitter for large chunks
                from src.chunking.splitters import RecursiveChunker
                splitter = RecursiveChunker(
                    chunk_size=self.max_chunk_size,
                    chunk_overlap=50
                )
                sub_chunks = splitter.chunk_text(chunk.text)

                for sub_chunk in sub_chunks:
                    sub_chunk.metadata = chunk.metadata.copy()
                    result.append(sub_chunk)

                i += 1

            # Just right
            else:
                result.append(chunk)
                i += 1

        return result

    def _split_sentences(self, text: str) -> List[str]:
        """Split text into sentences."""
        # Use nltk or spaCy for better sentence splitting
        try:
            import nltk
            nltk.download('punkt', quiet=True)
            return nltk.sent_tokenize(text)
        except ImportError:
            # Fallback to simple splitting
            import re
            sentences = re.split(r'[.!?]+', text)
            return [s.strip() for s in sentences if s.strip()]
```

#### Testing Requirements
- [ ] Test semantic chunking produces coherent chunks
- [ ] Compare with fixed-size chunking
- [ ] Test retrieval quality improvement
- [ ] Benchmark chunking time
- [ ] Test with various document types

#### Files to Create
- `src/chunking/semantic.py` (~300 lines)
- `tests/chunking/test_semantic.py` (~150 lines)

#### Acceptance Criteria
- ✅ Semantic chunks are topically coherent
- ✅ Retrieval quality improves vs fixed-size (5-10% by RAGAS)
- ✅ Acceptable performance (<5s for typical document)
- ✅ Configurable similarity threshold

---

### FEAT-006: Hierarchical Chunking

**Priority**: Medium
**Estimated Time**: 18 hours
**Impact**: Precision + context in one system
**Research**: "Retrieve Smaller, Read Larger" patterns

#### Concept
Maintain parent-child relationships between chunks:
- **Small child chunks** for precise retrieval
- **Large parent chunks** for context when generating

Best of both worlds: precise retrieval + sufficient context for generation.

#### Implementation

```python
# src/chunking/hierarchical.py (NEW FILE)
"""Hierarchical chunking with parent-child relationships."""
from typing import List, Dict, Optional
from dataclasses import dataclass, field
import uuid

@dataclass
class HierarchicalChunk:
    """Chunk with parent-child relationships."""
    id: str
    text: str
    metadata: dict
    level: int  # 0 = parent, 1 = child, 2 = grandchild, etc.
    parent_id: Optional[str] = None
    child_ids: List[str] = field(default_factory=list)

class HierarchicalChunker:
    """
    Create hierarchical chunk structure.

    Two levels:
    - Parent chunks: Large (800-1000 tokens) for context
    - Child chunks: Small (200-300 tokens) for retrieval
    """

    def __init__(
        self,
        parent_chunk_size: int = 1000,
        child_chunk_size: int = 250,
        overlap: int = 50
    ):
        """
        Initialize hierarchical chunker.

        Args:
            parent_chunk_size: Size of parent chunks (tokens)
            child_chunk_size: Size of child chunks (tokens)
            overlap: Overlap between chunks (tokens)
        """
        self.parent_chunk_size = parent_chunk_size
        self.child_chunk_size = child_chunk_size
        self.overlap = overlap

    def chunk(self, document: Document) -> Dict[str, List[HierarchicalChunk]]:
        """
        Create hierarchical chunks.

        Returns:
            Dictionary with 'parents' and 'children' lists
        """
        # Create parent chunks (large)
        parents = self._create_parent_chunks(document)

        # Create child chunks for each parent
        children = []
        for parent in parents:
            parent_children = self._create_child_chunks(parent)
            children.extend(parent_children)

        return {
            'parents': parents,
            'children': children
        }

    def _create_parent_chunks(self, document: Document) -> List[HierarchicalChunk]:
        """Create parent (large) chunks."""
        from src.chunking.splitters import RecursiveChunker

        # Use standard chunker for parents
        chunker = RecursiveChunker(
            chunk_size=self.parent_chunk_size,
            chunk_overlap=self.overlap
        )

        standard_chunks = chunker.chunk(document)

        # Convert to hierarchical chunks
        parents = []
        for i, chunk in enumerate(standard_chunks):
            parent = HierarchicalChunk(
                id=str(uuid.uuid4()),
                text=chunk.text,
                metadata=chunk.metadata.copy(),
                level=0,
                parent_id=None
            )
            parent.metadata['chunk_index'] = i
            parent.metadata['chunk_type'] = 'parent'

            parents.append(parent)

        return parents

    def _create_child_chunks(
        self,
        parent: HierarchicalChunk
    ) -> List[HierarchicalChunk]:
        """Create child chunks from parent."""
        from src.chunking.splitters import RecursiveChunker

        # Chunk parent text into smaller pieces
        chunker = RecursiveChunker(
            chunk_size=self.child_chunk_size,
            chunk_overlap=self.overlap // 2  # Less overlap for children
        )

        child_texts = chunker.chunk_text(parent.text)

        # Create child chunks linked to parent
        children = []
        for i, child_text in enumerate(child_texts):
            child = HierarchicalChunk(
                id=str(uuid.uuid4()),
                text=child_text,
                metadata=parent.metadata.copy(),
                level=1,
                parent_id=parent.id
            )
            child.metadata['child_index'] = i
            child.metadata['chunk_type'] = 'child'

            children.append(child)

            # Link to parent
            parent.child_ids.append(child.id)

        return children

class HierarchicalRetriever:
    """
    Retrieve using hierarchical chunks.

    Retrieves with children, provides context with parents.
    """

    def __init__(
        self,
        vector_store,
        embedder,
        parent_store: Optional[Dict[str, HierarchicalChunk]] = None
    ):
        """
        Initialize hierarchical retriever.

        Args:
            vector_store: Vector store containing CHILD chunks
            embedder: Embedding model
            parent_store: Mapping of child_id -> parent chunk
        """
        self.vector_store = vector_store
        self.embedder = embedder
        self.parent_store = parent_store or {}

    def retrieve(
        self,
        query: str,
        k: int = 5,
        return_parents: bool = True
    ) -> List[HierarchicalChunk]:
        """
        Retrieve using child chunks, optionally return parents.

        Args:
            query: Query string
            k: Number of chunks to retrieve
            return_parents: If True, return parent chunks instead of children

        Returns:
            Retrieved chunks (parents if return_parents=True)
        """
        # Embed query
        query_embedding = self.embedder.embed(query)

        # Retrieve child chunks
        child_results = self.vector_store.query(
            query_embeddings=[query_embedding],
            n_results=k
        )

        children = self._parse_results(child_results)

        if not return_parents:
            return children

        # Get parent chunks
        parents = []
        seen_parent_ids = set()

        for child in children:
            parent_id = child.parent_id

            # Skip if already added this parent
            if parent_id in seen_parent_ids:
                continue

            # Get parent chunk
            parent = self.parent_store.get(parent_id)
            if parent:
                # Attach which child was matched
                parent.metadata['matched_child'] = child.text[:100]
                parents.append(parent)
                seen_parent_ids.add(parent_id)

        return parents

    def _parse_results(self, results: dict) -> List[HierarchicalChunk]:
        """Parse results into hierarchical chunks."""
        # Implementation depends on vector store format
        chunks = []
        # ... parsing logic ...
        return chunks
```

**Storage Strategy**:
```python
# Store BOTH parents and children
def store_hierarchical_chunks(chunks_dict: dict):
    # Store children in vector DB (for retrieval)
    child_texts = [c.text for c in chunks_dict['children']]
    child_embeddings = embedder.embed_batch(child_texts)
    child_metadata = [c.metadata for c in chunks_dict['children']]

    vector_store.add(
        texts=child_texts,
        embeddings=child_embeddings,
        metadatas=child_metadata
    )

    # Store parents in separate collection (or file)
    parent_store = {c.id: c for c in chunks_dict['parents']}

    # Also create child_id -> parent_id mapping
    child_to_parent = {
        child.id: child.parent_id
        for child in chunks_dict['children']
    }

    return parent_store, child_to_parent
```

#### Testing Requirements
- [ ] Test hierarchical chunking creates correct relationships
- [ ] Test retrieval with children, context with parents
- [ ] Compare retrieval quality vs flat chunking
- [ ] Test parent-child link integrity
- [ ] Measure context quality improvement

#### Files to Create
- `src/chunking/hierarchical.py` (~400 lines)
- `src/retrieval/hierarchical_retriever.py` (~200 lines)
- `tests/chunking/test_hierarchical.py` (~200 lines)

#### Acceptance Criteria
- ✅ Hierarchical chunks maintain parent-child links
- ✅ Retrieval precision improves (smaller chunks)
- ✅ Generation context improves (larger chunks)
- ✅ Overall quality improvement (5-15% by RAGAS)

---


---

## Related Documentation

- [Intelligent Chunking (v0.3.3)](../../version/v0.3/v0.3.3.md) - Implementation roadmap
- [v0.3.3 Implementation Summary](../../../implementation/version/v0.3/v0.3.3/) - What was built
- [Chunking Architecture](../../../../planning/architecture/) - System architecture
- [v0.3 Planning](../../../../planning/version/v0.3/) - Design goals

---
