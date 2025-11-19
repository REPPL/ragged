# Chunking Strategies

**Status:** 🚧 Coming Soon

## Overview

This document covers document chunking strategies for optimal retrieval in ragged's RAG pipeline.

---

## Coming Soon

This document will cover:

### Why Chunking Matters

#### The Chunking Trade-off
- **Too Small**: Loss of context, too many irrelevant chunks
- **Too Large**: Less precise retrieval, context window limits
- **Optimal Size**: Depends on document type, query patterns, LLM context limits

#### Impact on Quality
- Retrieval precision and recall
- Answer quality and relevance
- Citation granularity
- Processing efficiency

### Chunking Strategies

#### 1. Fixed-Size Chunking (v0.1 Default)
**Strategy**: Split text into fixed-size chunks with overlap

**Parameters**:
- **Chunk Size**: 512-1024 tokens (configurable)
- **Overlap**: 50-100 tokens (10-20% of chunk size)
- **Splitting**: On paragraph/sentence boundaries when possible

**Pros**:
- ✅ Simple and predictable
- ✅ Consistent chunk sizes
- ✅ Fast processing
- ✅ Good baseline performance

**Cons**:
- ⚠️ May split mid-concept
- ⚠️ Ignores document structure
- ⚠️ One-size-fits-all approach

**Implementation**:
```python
def fixed_size_chunk(text, chunk_size=512, overlap=50):
    tokens = tokenise(text)
    chunks = []

    for i in range(0, len(tokens), chunk_size - overlap):
        chunk = tokens[i:i + chunk_size]
        chunks.append(detokenize(chunk))

    return chunks
```

#### 2. Semantic Chunking (v0.3+)
**Strategy**: Split based on semantic coherence

**Techniques**:
- **Sentence Embeddings**: Group semantically similar sentences
- **Topic Modeling**: Split at topic boundaries
- **Coherence Scoring**: Measure semantic continuity

**Pros**:
- ✅ Preserves semantic units
- ✅ More meaningful chunks
- ✅ Better retrieval quality

**Cons**:
- ⚠️ Slower processing
- ⚠️ Variable chunk sizes
- ⚠️ More complex implementation

#### 3. Structure-Aware Chunking (v0.3+)
**Strategy**: Respect document structure

**For Papers/Reports**:
- Chunk by section (Introduction, Methods, Results)
- Preserve headings and subheadings
- Keep related content together

**For Code Documentation**:
- Chunk by function/class
- Keep docstrings with code
- Preserve code blocks

**For Books**:
- Chunk by chapter/section
- Preserve narrative flow
- Consider chapter structure

**Pros**:
- ✅ Respects logical units
- ✅ Better context preservation
- ✅ Improves citation quality

**Cons**:
- ⚠️ Requires document parsing
- ⚠️ Format-specific logic
- ⚠️ Variable chunk sizes

#### 4. Hybrid Chunking (v0.4+)
**Strategy**: Combine multiple approaches

**Example**:
1. Parse document structure (sections, paragraphs)
2. Split large sections using semantic boundaries
3. Ensure chunks meet size constraints
4. Add overlap for context continuity

**Pros**:
- ✅ Best of multiple approaches
- ✅ Adaptive to content
- ✅ Optimal quality

**Cons**:
- ⚠️ Most complex
- ⚠️ Slowest processing
- ⚠️ Requires tuning

### Special Considerations

#### Tables and Lists
- **Keep together**: Don't split tables across chunks
- **Context**: Include table captions and surrounding text
- **Metadata**: Tag chunks containing tables

#### Code Blocks
- **Preserve**: Keep code blocks intact
- **Context**: Include surrounding explanation
- **Language**: Tag with programming language

#### Formulas and Equations
- **Keep together**: Don't split mathematical expressions
- **Context**: Include definitions and explanations
- **Rendering**: Preserve LaTeX/MathML

#### Images and Figures
- **Captions**: Include figure captions in chunks
- **References**: Link to figure descriptions
- **Metadata**: Tag chunks referencing figures

### Metadata Enrichment

#### Chunk Metadata
```python
chunk_metadata = {
    'document_id': 'doc_123',
    'chunk_id': 'chunk_1',
    'source': 'research_paper.pdf',
    'page': 5,
    'section': 'Introduction',
    'chunk_index': 0,
    'total_chunks': 42,
    'has_table': False,
    'has_code': True,
    'language': 'python'
}
```

#### Benefits
- **Filtering**: Retrieve from specific sections
- **Context**: Provide document structure to LLM
- **Citation**: Precise source attribution
- **Analysis**: Track chunk-level metrics

### Chunking Pipeline

#### v0.1 Pipeline
```python
def chunk_document(document):
    # 1. Extract text
    text = extract_text(document)

    # 2. Normalise
    normalised = normalise_text(text)

    # 3. Split into chunks
    chunks = fixed_size_chunk(normalised, size=512, overlap=50)

    # 4. Generate embeddings
    embeddings = embed_chunks(chunks)

    # 5. Store with metadata
    store_chunks(chunks, embeddings, metadata)
```

#### v0.3 Enhanced Pipeline
```python
def chunk_document_enhanced(document):
    # 1. Parse structure
    parsed = parse_document_structure(document)

    # 2. Extract sections
    sections = extract_sections(parsed)

    # 3. Semantic chunking per section
    chunks = []
    for section in sections:
        section_chunks = semantic_chunk(
            section.text,
            max_size=1024,
            coherence_threshold=0.7
        )
        chunks.extend(section_chunks)

    # 4. Add overlap
    chunks_with_overlap = add_context_overlap(chunks, overlap=100)

    # 5. Enrich metadata
    chunks_with_metadata = enrich_metadata(chunks_with_overlap, parsed)

    return chunks_with_metadata
```

### Optimisation

#### Chunk Size Tuning
- **Benchmark**: Test different sizes (256, 512, 1024 tokens)
- **Metrics**: Retrieval precision, recall, answer quality
- **Adaptation**: Optimise per document type

#### Overlap Tuning
- **Context continuity**: 10-20% overlap typical
- **Query patterns**: More overlap for complex queries
- **Trade-offs**: Redundancy vs context

#### Processing Performance
- **Batching**: Process multiple documents in parallel
- **Caching**: Reuse embeddings for unchanged chunks
- **Incremental**: Only rechunk modified documents

### Evaluation

#### Retrieval Metrics
- **Precision@k**: Relevant chunks in top-k
- **Recall@k**: Percentage of relevant chunks found
- **MRR**: Ranking quality

#### Quality Metrics
- **Context Sufficiency**: Chunks contain enough context
- **Boundary Quality**: Splits at logical points
- **Overlap Effectiveness**: Context continuity preserved

### Version Roadmap

#### v0.1: Fixed-Size Baseline
- Simple fixed-size chunking
- Configurable size and overlap
- Sentence boundary awareness

#### v0.2: Configuration
- User-configurable chunking parameters
- Per-collection chunk size
- Metadata tracking

#### v0.3: Semantic Chunking
- Structure-aware parsing
- Semantic boundary detection
- Enhanced metadata

#### v0.4: Hybrid Strategies
- Multi-strategy chunking
- Document type detection
- Automatic optimisation

#### v1.0: Optimised Defaults
- Benchmarked defaults
- Auto-tuning based on content
- Comprehensive evaluation

---

## Related Documentation

- **[Document Processing](document-processing.md)** - Document ingestion pipeline
- **[Document Normalisation](../core-concepts/document-normalisation.md)** - Text normalisation
- **[Embeddings](embeddings.md)** - Embedding generation
- **[RAG Fundamentals](../core-concepts/rag-fundamentals.md)** - RAG technical background

---

*This document will be expanded with benchmarks and chunking examples for different document types*
