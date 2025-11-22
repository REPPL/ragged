# ADR-0009: Recursive Character Text Splitter

**Status:** Accepted

**Date:** 2025-11-09

**Deciders:** Development Team

**Area:** Chunking

## Context

Need to split documents into chunks for embedding and retrieval whilst:
- Preserving semantic boundaries where possible
- Respecting token limits
- Maintaining context across chunk boundaries
- Handling edge cases (very long sentences, paragraphs)

## Decision

Implement RecursiveCharacterTextSplitter that tries increasingly smaller separators in order:

1. Paragraphs (`\n\n`)
2. Lines (`\n`)
3. Sentences (`. `)
4. Words (` `)
5. Characters (``)

Falls back to smaller units only when necessary to respect token limits.

## Rationale

- **Semantic Preservation**: Tries to split at natural boundaries first
- **Fallback Strategy**: Handles edge cases gracefully by falling back to smaller units
- **Token-Aware**: Uses tiktoken for accurate sizing (not character count)
- **Overlap Support**: Maintains context across chunks with configurable overlap
- **Proven Pattern**: Successfully used by LangChain and other RAG systems
- **Practical**: Balances semantic quality with simplicity

## Alternatives Considered

### 1. Fixed-Size Splitting

**Pros:**
- Simple to implement
- Predictable chunk sizes
- Fast

**Cons:**
- Breaks mid-sentence frequently
- Poor semantic boundaries
- Degrades retrieval quality

**Rejected:** Unacceptable quality trade-off

### 2. Sentence-Only Splitting

**Pros:**
- Clean semantic boundaries
- Grammatically complete chunks

**Cons:**
- Sentences vary widely in token count
- May exceed context limits
- Doesn't handle edge cases well

**Rejected:** Insufficient handling of edge cases

### 3. Sliding Window

**Pros:**
- Maximum context preservation
- Every token appears in multiple chunks

**Cons:**
- High redundancy
- Many more chunks to process
- Storage inefficiency

**Rejected:** Excessive redundancy for v0.1

### 4. Semantic Chunking (AI-Based)

**Pros:**
- Best possible semantic boundaries
- Topic-aware splitting

**Cons:**
- Slow (requires LLM calls)
- Expensive (many API calls)
- Complex implementation
- Violates local-only principle if using API

**Rejected:** Too slow for v0.1, consider for v0.3+

## Implementation

```python
class RecursiveCharacterTextSplitter:
    def __init__(
        self,
        chunk_size: int = 512,
        chunk_overlap: int = 128,
        separators: list[str] = ["\n\n", "\n", ". ", " ", ""]
    ):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.separators = separators

    def split_text(self, text: str) -> list[str]:
        """Split text using recursive strategy."""
        # Try each separator in order
        for separator in self.separators:
            chunks = self._split_by_separator(text, separator)
            if all(count_tokens(c) <= self.chunk_size for c in chunks):
                return chunks
        # Fallback: force split by characters
        return self._force_split(text)
```

## Consequences

### Positive

- Good balance of semantic preservation and practicality
- Handles edge cases gracefully (very long sentences)
- Overlap maintains context across boundaries
- Fast and reliable
- Deterministic behaviour

### Negative

- Not perfect semantic boundaries (compromise solution)
- Paragraph detection can be ambiguous (single vs double newline)
- Overlap creates some redundancy in storage and processing
- May split tables or code blocks awkwardly

### Neutral

- Recursive strategy adds some complexity but improves quality
- Trade-off between quality and simplicity is acceptable for v0.1

## Future Enhancements

Consider semantic chunking for v0.3+ when:
- Local LLM inference is faster
- We have GPU acceleration widely available
- Speed is less critical than quality

## Related

- [ADR-0008: tiktoken for Token Counting](./0008-tiktoken-for-token-counting.md)
- [Core Concepts: Chunking Strategy](../../planning/core-concepts/chunking.md)

---

## Related Documentation

- [Intelligent Chunking (v0.3.3)](../../roadmap/version/v0.3/v0.3.3.md) - Advanced chunking
- [Token Counting (ADR-0008)](./0008-tiktoken-for-token-counting.md) - Related decision
- [Chunking Architecture](../../planning/architecture/) - System design

---
