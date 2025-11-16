# ADR-0008: tiktoken for Token Counting

**Status:** Accepted

**Date:** 2025-11-09

**Deciders:** Development Team

**Area:** Chunking

## Context

Need accurate token counting to:
- Respect LLM context limits
- Create appropriately-sized chunks
- Avoid truncation or overflow errors
- Ensure consistent chunk sizing

Character-based estimates can be off by 50% or more, leading to unpredictable behaviour.

## Decision

Use tiktoken with cl100k_base encoding for all token counting operations.

## Rationale

- **Accuracy**: Same tokeniser used by GPT models (OpenAI standard)
- **Industry Standard**: Widely adopted for token counting
- **Fast**: Rust implementation provides excellent performance
- **Reliable**: Battle-tested by OpenAI in production
- **Caching Support**: Encoding caching for repeated operations
- **Deterministic**: Consistent token counts across runs

## Alternatives Considered

### 1. Character-based Estimation

**Pros:**
- Very fast
- No dependencies
- Simple implementation

**Cons:**
- Highly inaccurate (can be off by 50%+)
- Varies by language and content
- Unreliable for context limits

**Rejected:** Insufficient accuracy for production use

### 2. transformers Tokeniser

**Pros:**
- Model-specific tokenisation
- Hugging Face ecosystem

**Cons:**
- Slower than tiktoken
- Different tokeniser for each model
- Heavier dependency

**Rejected:** Unnecessary complexity, slower performance

### 3. Simple Word Count × 1.3

**Pros:**
- Very fast
- Approximation rule of thumb

**Cons:**
- Highly inaccurate
- No scientific basis
- Fails on technical content

**Rejected:** Too unreliable for chunk sizing

## Implementation

```python
import tiktoken
from functools import lru_cache

@lru_cache(maxsize=1)
def get_tokenizer():
    """Get cached tokenizer instance."""
    return tiktoken.get_encoding("cl100k_base")

def count_tokens(text: str) -> int:
    """Count tokens in text."""
    tokenizer = get_tokenizer()
    return len(tokenizer.encode(text))
```

## Consequences

### Positive

- Accurate chunk sizing
- Respects token limits reliably
- Performance is good with caching
- Industry-standard approach
- Consistent behaviour across different content types

### Negative

- Additional dependency (not stdlib)
- Rust compilation required on install
- cl100k_base may not match all LLMs exactly (though close enough)
- Slight overhead compared to character counting

### Neutral

- LRU cache on tokeniser reduces overhead significantly
- Encoding cache helps with repeated text

## Performance Notes

LRU cache on tokeniser instance reduces overhead significantly for repeated operations. For typical RAG workloads, token counting overhead is <5% of total processing time.

## Related

- [ADR-0009: Recursive Character Text Splitter](./0009-recursive-character-text-splitter.md)
- [Core Concepts: Chunking Strategy](../../planning/core-concepts/chunking.md)
