# ADR-0013: Citation Format [Source: filename]

**Status:** Accepted

**Date:** 2025-11-09

**Deciders:** Development Team

**Area:** Generation, UX

## Context

Need a clear, parseable citation format for LLM-generated answers that:
- Helps users verify information
- Builds trust in the system
- Is readable for humans
- Is parseable by code
- Works reliably with LLM instruction following

## Decision

Use `[Source: filename]` format for citations in generated answers.

Format specification:
- Square brackets distinguish from parenthetical notes
- "Source:" prefix is clear and explicit
- Filename only (not full path for privacy/readability)
- LLMs understand and follow this format reliably

## Rationale

- **Readability**: Users immediately understand the notation
- **Parseability**: Simple regex extraction (`\[Source:\s*([^\]]+)\]`)
- **LLM-Friendly**: Common format in LLM training data, follows instructions well
- **Markdown-Compatible**: Renders well in markdown and plain text
- **Unambiguous**: Square brackets clearly mark citations vs regular text
- **Privacy**: Filename only (not full path) avoids exposing directory structure

## Alternatives Considered

### 1. Footnote Numbers [1], [2]

**Pros:**
- Cleaner inline in text
- Academic standard
- Compact

**Cons:**
- Requires separate mapping/legend
- Harder to parse and track
- Less immediately clear to users
- Ordering matters

**Rejected:** Less clear, more complexity

### 2. Inline (filename)

**Pros:**
- Simpler notation
- Familiar parenthetical style

**Cons:**
- Ambiguous with other parenthetical content
- Harder to extract reliably
- Less visually distinct

**Rejected:** Insufficient visual distinction

### 3. HTML-style `<cite>filename</cite>`

**Pros:**
- Structured and semantic
- Standard HTML element

**Cons:**
- Ugly in plain text
- LLMs less reliable with HTML tags
- Doesn't render well in terminal

**Rejected:** Poor plain text appearance

### 4. Markdown Links `[text](filename)`

**Pros:**
- Standard markdown
- Clickable in some viewers

**Cons:**
- Requires link text decision
- More complex to generate
- Link won't work (filename not URL)

**Rejected:** Links don't work, overcomplicates

### 5. No Citations

**Pros:**
- Cleaner text
- Simpler implementation

**Cons:**
- No trust/verification
- Core feature requirement

**Rejected:** Citations are essential for trust

## Implementation

### System Prompt

```python
SYSTEM_PROMPT = """
You are a helpful assistant. Answer questions based on the provided context.

IMPORTANT: Include citations in your answer using [Source: filename] format
after each claim or fact. Place the citation immediately after the relevant
sentence or statement.

Example:
"The Python documentation recommends using virtual environments [Source: python-guide.pdf].
This isolates project dependencies [Source: python-guide.pdf]."
"""
```

### Citation Extraction

```python
import re

def extract_citations(response: str) -> list[str]:
    """Extract citation filenames from response."""
    pattern = r'\[Source:\s*([^\]]+)\]'
    citations = re.findall(pattern, response)
    return [c.strip() for c in citations]
```

## Consequences

### Positive

- Users know where information came from (builds trust)
- Simple to implement and parse
- LLMs follow instructions reliably (high compliance)
- Clean presentation in terminal and markdown
- Privacy-friendly (filename only)

### Negative

- Manual citation by LLM (not always perfect or consistent)
- Can't automatically verify citation accuracy
- Multiple citations can clutter text slightly
- LLM may forget to cite or cite incorrectly

### Neutral

- Trade-off between accuracy and simplicity is acceptable for v0.1
- Can add citation verification in future versions

## Limitations

- LLM-generated citations not guaranteed to be accurate
- No automatic verification that cited file actually contains the claim
- Citation granularity is file-level, not chunk-level

## Future Enhancements

v0.2+:
- Automatic citation verification (map citations to actual chunks)
- Chunk-level citations `[Source: filename, chunk 3]`
- Citation confidence scores

v0.3+:
- Clickable citations in web UI linking to source chunks
- Citation highlighting in source documents
- Alternative citation styles (configurable)

## Related

- [ADR-0012: Ollama for LLM Generation](./0012-ollama-for-llm-generation.md)
- [User Stories](../../planning/requirements/user-stories/README.md)
