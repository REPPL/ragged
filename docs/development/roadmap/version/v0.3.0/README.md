# Ragged v0.3.0 Roadmap - Advanced RAG Features

**Status:** Planned

**Total Hours:** 180-220 hours (AI implementation)

**Focus:** State-of-the-art RAG capabilities, advanced features

**Breaking Changes:** Minimal - mostly additive features

**Implementation Note:** Due to size (180-220 hours), implement in 6-8 focused sessions of 25-35 hours each

## Overview

Version 0.3.0 transforms ragged into a **state-of-the-art** RAG system with cutting-edge capabilities based on recent research. This release implements advanced techniques that significantly improve retrieval quality, handle multi-modal documents, and provide comprehensive evaluation tools.

**Key Goals**:
- 10-20% retrieval quality improvement (reranking, HyDE)
- Multi-modal document support (images, tables)
- Automated quality measurement (RAGAS)
- Advanced reasoning capabilities (chain-of-thought)
- Production-ready evaluation framework

**Research-Backed**: All features based on published papers and state-of-the-art techniques.

---

## Part 1: Advanced Query Processing & Retrieval (41 hours)

### FEAT-001: Query Decomposition (Multi-Query RAG)

**Priority**: High
**Estimated Time**: 15 hours
**Impact**: Handle complex, multi-part questions
**Research**: "Query Rewriting for Retrieval-Augmented LLMs" (arXiv:2305.14283)

#### Problem
Simple queries work well, but complex questions with multiple parts often produce incomplete answers:
- "Compare machine learning and deep learning approaches to NLP" (requires two retrievals + comparison)
- "What are the benefits and limitations of solar energy?" (requires structured retrieval)

#### Solution: Decompose Complex Queries

**Step 1: Query Analyzer**
```python
# src/query/decomposition.py (NEW FILE)
"""Query decomposition for multi-part questions."""
from typing import List, Dict
from src.generation.ollama_client import OllamaClient

class QueryDecomposer:
    """
    Decompose complex queries into simpler sub-queries.

    Based on "Least-to-Most Prompting" and "Decomposed Prompting" techniques.
    """

    def __init__(self, llm: OllamaClient):
        self.llm = llm

    def decompose(self, query: str) -> List[str]:
        """
        Decompose a complex query into sub-queries.

        Args:
            query: Original complex query

        Returns:
            List of simpler sub-queries that together answer the original

        Example:
            Input: "Compare ML and DL for NLP"
            Output: [
                "What are machine learning approaches to NLP?",
                "What are deep learning approaches to NLP?",
                "What are the key differences between ML and DL?"
            ]
        """
        decomposition_prompt = f"""
You are a query decomposition assistant. Break down complex questions into simpler sub-questions.

Rules:
1. Each sub-question should be answerable independently
2. Together, the sub-questions should fully address the original question
3. Return 2-5 sub-questions
4. Make sub-questions specific and focused

Original Question: {query}

Sub-Questions:"""

        response = self.llm.generate(
            query=decomposition_prompt,
            context="",
            temperature=0.3  # Low temperature for consistency
        )

        # Parse sub-questions from response
        sub_queries = self._parse_sub_queries(response)

        logger.info(f"Decomposed query into {len(sub_queries)} sub-queries")
        return sub_queries

    def _parse_sub_queries(self, response: str) -> List[str]:
        """Parse sub-queries from LLM response."""
        lines = response.strip().split('\n')
        sub_queries = []

        for line in lines:
            # Remove numbering, bullets, etc.
            line = line.strip()
            line = re.sub(r'^\d+[\.)]\s*', '', line)
            line = re.sub(r'^[-*•]\s*', '', line)

            if line and line.endswith('?'):
                sub_queries.append(line)

        return sub_queries if sub_queries else [response.strip()]

    def is_complex_query(self, query: str) -> bool:
        """
        Determine if a query is complex enough to benefit from decomposition.

        Heuristics:
        - Contains comparison words (compare, difference, versus, vs)
        - Contains "and" connecting different concepts
        - Contains multiple question marks
        - Is longer than 10 words
        """
        comparison_keywords = [
            'compare', 'difference', 'versus', 'vs', 'vs.',
            'contrast', 'similarities', 'distinguish'
        ]

        query_lower = query.lower()

        # Check for comparison
        has_comparison = any(kw in query_lower for kw in comparison_keywords)

        # Check for multiple parts
        has_multiple_parts = ' and ' in query_lower or ' or ' in query_lower

        # Check length
        is_long = len(query.split()) > 10

        return has_comparison or has_multiple_parts or is_long
```

**Step 2: Multi-Query Retriever**
```python
# src/retrieval/multi_query.py (NEW FILE)
"""Multi-query retrieval with parallel execution."""
import asyncio
from typing import List, Set
from dataclasses import dataclass

@dataclass
class RetrievalResult:
    """Result from a single retrieval operation."""
    query: str
    chunks: List[Chunk]
    scores: List[float]

class MultiQueryRetriever:
    """
    Retrieve for multiple queries in parallel and combine results.

    Uses reciprocal rank fusion (RRF) for combining results.
    """

    def __init__(self, retriever):
        self.retriever = retriever

    async def retrieve_multi_query(
        self,
        queries: List[str],
        k: int = 5
    ) -> List[Chunk]:
        """
        Retrieve for multiple queries and combine results.

        Args:
            queries: List of queries to retrieve for
            k: Number of results to return overall

        Returns:
            Deduplicated and reranked chunks
        """
        # Retrieve for each query in parallel
        tasks = [
            self._retrieve_async(query, k * 2)  # Retrieve more per query
            for query in queries
        ]

        results = await asyncio.gather(*tasks)

        # Combine results using RRF
        combined = self._reciprocal_rank_fusion(results, k)

        return combined

    async def _retrieve_async(self, query: str, k: int) -> RetrievalResult:
        """Async wrapper for retrieval."""
        chunks = await asyncio.to_thread(
            self.retriever.retrieve,
            query,
            k
        )

        scores = [chunk.score for chunk in chunks]

        return RetrievalResult(
            query=query,
            chunks=chunks,
            scores=scores
        )

    def _reciprocal_rank_fusion(
        self,
        results: List[RetrievalResult],
        k: int,
        rrf_k: int = 60
    ) -> List[Chunk]:
        """
        Combine multiple retrieval results using Reciprocal Rank Fusion.

        RRF formula: score(d) = sum over queries of 1 / (k + rank(d))

        Args:
            results: Results from each query
            k: Number of final results to return
            rrf_k: RRF constant (typically 60)

        Returns:
            Top-k chunks by RRF score
        """
        # Track RRF scores for each unique chunk
        chunk_scores = {}  # chunk_id -> RRF score
        chunk_objects = {}  # chunk_id -> Chunk object

        for result in results:
            for rank, chunk in enumerate(result.chunks):
                chunk_id = self._get_chunk_id(chunk)

                # Initialize if first time seeing this chunk
                if chunk_id not in chunk_scores:
                    chunk_scores[chunk_id] = 0
                    chunk_objects[chunk_id] = chunk

                # Add RRF score
                chunk_scores[chunk_id] += 1.0 / (rrf_k + rank + 1)

        # Sort by RRF score
        sorted_chunks = sorted(
            chunk_scores.items(),
            key=lambda x: x[1],
            reverse=True
        )

        # Return top-k chunks
        top_chunks = [
            chunk_objects[chunk_id]
            for chunk_id, score in sorted_chunks[:k]
        ]

        # Update scores to RRF scores
        for i, (chunk_id, score) in enumerate(sorted_chunks[:k]):
            top_chunks[i].score = score

        return top_chunks

    def _get_chunk_id(self, chunk: Chunk) -> str:
        """Generate unique ID for a chunk."""
        return f"{chunk.metadata['source']}:{chunk.metadata.get('page', 0)}:{chunk.text[:50]}"
```

**Step 3: Integration**
```python
# src/main.py - query command
@click.option(
    "--decompose",
    is_flag=True,
    help="Decompose complex queries into sub-queries"
)
async def query(query_text: str, top_k: int, decompose: bool):
    """Query with optional decomposition."""

    if decompose or QueryDecomposer(ollama_client).is_complex_query(query_text):
        # Decompose query
        decomposer = QueryDecomposer(ollama_client)
        sub_queries = decomposer.decompose(query_text)

        console.print(f"\n[cyan]Decomposed into {len(sub_queries)} sub-queries:[/cyan]")
        for i, sq in enumerate(sub_queries, 1):
            console.print(f"  {i}. {sq}")

        # Retrieve for all sub-queries
        multi_retriever = MultiQueryRetriever(retriever)
        chunks = await multi_retriever.retrieve_multi_query(sub_queries, k=top_k)

        console.print(f"\n[green]Retrieved {len(chunks)} unique chunks[/green]")

    else:
        # Standard single-query retrieval
        chunks = retriever.retrieve(query_text, k=top_k)

    # Generate answer from combined results
    context = build_context(chunks)
    answer = ollama_client.generate(query_text, context)

    display_answer(answer, chunks)
```

#### Testing Requirements
- [ ] Test decomposition of comparison queries
- [ ] Test decomposition of multi-part queries
- [ ] Test RRF combination logic
- [ ] Test parallel retrieval performance
- [ ] Compare quality vs single-query baseline

#### Files to Create
- `src/query/decomposition.py` (~200 lines)
- `src/retrieval/multi_query.py` (~250 lines)
- `tests/query/test_decomposition.py` (~150 lines)
- `tests/retrieval/test_multi_query.py` (~150 lines)

#### Files to Modify
- `src/main.py` (add --decompose flag)
- `src/web/api.py` (support decomposition)

#### Acceptance Criteria
- ✅ Complex queries automatically decomposed
- ✅ Sub-queries retrieved in parallel
- ✅ RRF combines results effectively
- ✅ Quality improvement measurable (RAGAS metrics)

---

### FEAT-002: Hypothetical Document Embeddings (HyDE)

**Priority**: High
**Estimated Time**: 8 hours
**Impact**: Better retrieval for conceptual questions
**Research**: "Precise Zero-Shot Dense Retrieval without Relevance Labels" (arXiv:2212.10496)

#### Concept
Instead of embedding the query directly, generate a hypothetical answer, embed that, and retrieve similar documents. Works remarkably well for conceptual questions.

**Why it works**: Hypothetical answers are more similar to actual document text than raw questions are.

#### Implementation

```python
# src/retrieval/hyde.py (NEW FILE)
"""Hypothetical Document Embeddings (HyDE) retrieval."""
from typing import List
from src.generation.ollama_client import OllamaClient
from src.embeddings.base import BaseEmbedder
from src.retrieval.base import BaseRetriever

class HyDERetriever:
    """
    Retrieve using Hypothetical Document Embeddings.

    Instead of embedding the query, generate a hypothetical answer
    and embed that for retrieval.

    Paper: https://arxiv.org/abs/2212.10496
    """

    def __init__(
        self,
        llm: OllamaClient,
        embedder: BaseEmbedder,
        vector_store,
        use_multiple_hypotheses: bool = False
    ):
        """
        Initialize HyDE retriever.

        Args:
            llm: Language model for generating hypothetical documents
            embedder: Embedding model
            vector_store: Vector store for retrieval
            use_multiple_hypotheses: Generate multiple hypothetical docs
        """
        self.llm = llm
        self.embedder = embedder
        self.vector_store = vector_store
        self.use_multiple_hypotheses = use_multiple_hypotheses

    def retrieve(self, query: str, k: int = 5) -> List[Chunk]:
        """
        Retrieve using HyDE method.

        Args:
            query: User query
            k: Number of chunks to retrieve

        Returns:
            Retrieved chunks
        """
        if self.use_multiple_hypotheses:
            return self._retrieve_multi_hypothesis(query, k)
        else:
            return self._retrieve_single_hypothesis(query, k)

    def _retrieve_single_hypothesis(self, query: str, k: int) -> List[Chunk]:
        """Retrieve using single hypothetical document."""

        # Generate hypothetical answer
        hyde_prompt = self._build_hyde_prompt(query)
        hypothetical_doc = self.llm.generate(
            query=hyde_prompt,
            context="",
            temperature=0.5,
            max_tokens=200
        )

        logger.debug(f"Hypothetical document: {hypothetical_doc[:100]}...")

        # Embed hypothetical document
        hyde_embedding = self.embedder.embed(hypothetical_doc)

        # Retrieve using hypothetical embedding
        results = self.vector_store.query(
            query_embeddings=[hyde_embedding],
            n_results=k
        )

        return self._parse_results(results)

    def _retrieve_multi_hypothesis(self, query: str, k: int) -> List[Chunk]:
        """
        Retrieve using multiple hypothetical documents.

        Generates multiple hypotheses and combines retrieval results.
        """
        num_hypotheses = 3

        # Generate multiple hypothetical documents
        hypotheses = []
        for i in range(num_hypotheses):
            hyde_prompt = self._build_hyde_prompt(query)
            hyp = self.llm.generate(
                query=hyde_prompt,
                context="",
                temperature=0.7 + (i * 0.1),  # Vary temperature for diversity
                max_tokens=200
            )
            hypotheses.append(hyp)

        # Embed all hypotheses
        hyde_embeddings = [
            self.embedder.embed(hyp)
            for hyp in hypotheses
        ]

        # Retrieve for each hypothesis
        all_results = []
        for embedding in hyde_embeddings:
            results = self.vector_store.query(
                query_embeddings=[embedding],
                n_results=k * 2  # Retrieve more per hypothesis
            )
            all_results.extend(self._parse_results(results))

        # Deduplicate and rerank
        unique_chunks = self._deduplicate_chunks(all_results)

        return unique_chunks[:k]

    def _build_hyde_prompt(self, query: str) -> str:
        """
        Build prompt for generating hypothetical document.

        Instructs LLM to write a detailed, factual answer as if from a document.
        """
        return f"""Write a detailed, factual passage that would appear in a reference document to answer this question. Do not include the question itself, only write the answer passage.

Question: {query}

Passage:"""

    def _parse_results(self, results: dict) -> List[Chunk]:
        """Parse vector store results into Chunk objects."""
        # Implementation depends on vector store format
        chunks = []
        # ... parsing logic ...
        return chunks

    def _deduplicate_chunks(self, chunks: List[Chunk]) -> List[Chunk]:
        """Remove duplicate chunks, keeping highest scored."""
        seen = {}
        for chunk in chunks:
            chunk_id = f"{chunk.metadata['source']}:{chunk.text[:100]}"
            if chunk_id not in seen or chunk.score > seen[chunk_id].score:
                seen[chunk_id] = chunk

        return sorted(seen.values(), key=lambda x: x.score, reverse=True)
```

**CLI Integration**:
```python
# src/main.py
@click.option(
    "--hyde",
    is_flag=True,
    help="Use Hypothetical Document Embeddings for retrieval"
)
def query(query_text: str, hyde: bool):
    if hyde:
        retriever = HyDERetriever(ollama_client, embedder, vector_store)
    else:
        retriever = standard_retriever

    results = retriever.retrieve(query_text, k=top_k)
    # ... rest of query logic
```

#### When to Use HyDE

HyDE works best for:
- ✅ Conceptual questions ("What is quantum computing?")
- ✅ Definition requests ("Explain neural networks")
- ✅ Abstract queries ("Benefits of renewable energy")

HyDE may not help for:
- ❌ Specific fact lookup ("Who wrote Pride and Prejudice?")
- ❌ Queries about document structure ("What's in section 3?")
- ❌ Very short queries

**Solution**: Auto-detect query type and use HyDE selectively.

#### Testing Requirements
- [ ] Test single hypothesis retrieval
- [ ] Test multi-hypothesis retrieval
- [ ] Compare with baseline retrieval quality
- [ ] Test on conceptual vs factual questions
- [ ] Measure retrieval quality with RAGAS

#### Files to Create
- `src/retrieval/hyde.py` (~250 lines)
- `tests/retrieval/test_hyde.py` (~150 lines)

#### Acceptance Criteria
- ✅ HyDE retrieval implemented
- ✅ Quality improvement on conceptual queries (10-20% by RAGAS)
- ✅ Auto-detection of when to use HyDE
- ✅ Option for multi-hypothesis mode

---

### FEAT-003: Reranking with Cross-Encoders

**Priority**: High
**Estimated Time**: 6 hours
**Impact**: 10-20% retrieval quality improvement
**Research**: Cross-encoder reranking is state-of-the-art for retrieval

#### Problem
Bi-encoders (like sentence-transformers) encode query and documents separately, missing interaction signals. Cross-encoders score query-document pairs jointly, giving better ranking.

**Trade-off**: Cross-encoders are slower, so use for reranking after initial retrieval.

#### Implementation

```python
# src/retrieval/reranker.py (NEW FILE)
"""Cross-encoder reranking for retrieval."""
from typing import List
from sentence_transformers import CrossEncoder
import numpy as np

class CrossEncoderReranker:
    """
    Rerank retrieved chunks using cross-encoder model.

    Cross-encoders score query-document pairs jointly for better ranking
    than bi-encoder similarity alone.
    """

    def __init__(
        self,
        model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2",
        use_gpu: bool = False
    ):
        """
        Initialize reranker.

        Args:
            model_name: Hugging Face cross-encoder model
            use_gpu: Whether to use GPU acceleration
        """
        self.model = CrossEncoder(
            model_name,
            device='cuda' if use_gpu else 'cpu'
        )
        self.model_name = model_name

        logger.info(f"Loaded cross-encoder: {model_name}")

    def rerank(
        self,
        query: str,
        chunks: List[Chunk],
        top_k: int = None
    ) -> List[Chunk]:
        """
        Rerank chunks using cross-encoder.

        Args:
            query: Query text
            chunks: Initial retrieved chunks
            top_k: Number of top chunks to return (None = all)

        Returns:
            Reranked chunks with updated scores
        """
        if not chunks:
            return chunks

        # Prepare query-chunk pairs
        pairs = [(query, chunk.text) for chunk in chunks]

        # Score all pairs
        scores = self.model.predict(pairs)

        # Update chunk scores
        for chunk, score in zip(chunks, scores):
            chunk.rerank_score = float(score)
            chunk.original_score = chunk.score
            chunk.score = float(score)  # Replace with rerank score

        # Sort by rerank score
        reranked = sorted(
            chunks,
            key=lambda x: x.rerank_score,
            reverse=True
        )

        # Return top-k if specified
        if top_k:
            return reranked[:top_k]

        return reranked

    def rerank_with_diversity(
        self,
        query: str,
        chunks: List[Chunk],
        top_k: int,
        diversity_weight: float = 0.3
    ) -> List[Chunk]:
        """
        Rerank with diversity: balance relevance and diversity.

        Uses Maximal Marginal Relevance (MMR) approach.

        Args:
            query: Query text
            chunks: Chunks to rerank
            top_k: Number to return
            diversity_weight: Weight for diversity (0.0 = pure relevance, 1.0 = pure diversity)

        Returns:
            Reranked chunks balancing relevance and diversity
        """
        # First, get relevance scores
        reranked = self.rerank(query, chunks, top_k=None)

        # Select with MMR
        selected = []
        remaining = reranked.copy()

        while len(selected) < top_k and remaining:
            if not selected:
                # First item: highest score
                selected.append(remaining.pop(0))
            else:
                # MMR: balance relevance and dissimilarity to selected
                mmr_scores = []
                for chunk in remaining:
                    relevance = chunk.rerank_score

                    # Calculate max similarity to already selected
                    max_sim = max(
                        self._text_similarity(chunk.text, s.text)
                        for s in selected
                    )

                    # MMR score
                    mmr = (1 - diversity_weight) * relevance - diversity_weight * max_sim
                    mmr_scores.append((chunk, mmr))

                # Select highest MMR score
                best = max(mmr_scores, key=lambda x: x[1])
                selected.append(best[0])
                remaining.remove(best[0])

        return selected

    def _text_similarity(self, text1: str, text2: str) -> float:
        """Calculate text similarity (simple Jaccard for speed)."""
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())

        intersection = words1 & words2
        union = words1 | words2

        return len(intersection) / len(union) if union else 0.0
```

**Integration with Retrieval**:
```python
# src/retrieval/hybrid.py - enhance with reranking
class HybridRetriever:
    def __init__(self, ..., use_reranker: bool = False):
        self.use_reranker = use_reranker
        if use_reranker:
            self.reranker = CrossEncoderReranker()

    def retrieve(self, query: str, k: int = 5) -> List[Chunk]:
        # Initial retrieval (get more than k)
        initial_k = k * 3 if self.use_reranker else k
        chunks = self._hybrid_retrieve(query, k=initial_k)

        # Rerank if enabled
        if self.use_reranker:
            chunks = self.reranker.rerank(query, chunks, top_k=k)

        return chunks
```

#### Testing Requirements
- [ ] Test reranking improves order
- [ ] Test diversity-aware reranking
- [ ] Benchmark reranking time
- [ ] Compare quality with/without reranking (RAGAS)
- [ ] Test different cross-encoder models

#### Files to Create
- `src/retrieval/reranker.py` (~200 lines)
- `tests/retrieval/test_reranker.py` (~100 lines)

#### Files to Modify
- `src/retrieval/hybrid.py` (add reranker option)
- `src/config/settings.py` (add reranker config)

#### Acceptance Criteria
- ✅ Cross-encoder reranking implemented
- ✅ 10-20% quality improvement (by RAGAS)
- ✅ MMR diversity option available
- ✅ Acceptable performance (<500ms for reranking)

---

### FEAT-004: Contextual Compression

**Priority**: Medium
**Estimated Time**: 12 hours
**Impact**: Better answers, lower token usage
**Research**: LongLLMLingua, RECOMP

#### Problem
Retrieved context often contains irrelevant information mixed with relevant parts. This wastes tokens and can distract the LLM.

#### Solution: Extract Only Relevant Parts

```python
# src/retrieval/compressor.py (NEW FILE)
"""Contextual compression for retrieval."""
from typing import List
import re

class ContextualCompressor:
    """
    Compress retrieved context to only query-relevant portions.

    Based on extractive summarization and sentence filtering.
    """

    def __init__(self, llm: OllamaClient):
        self.llm = llm

    def compress(
        self,
        query: str,
        chunks: List[Chunk],
        compression_ratio: float = 0.5
    ) -> List[Chunk]:
        """
        Compress chunks to only relevant content.

        Args:
            query: User query
            chunks: Retrieved chunks
            compression_ratio: Target compression (0.5 = keep 50% of content)

        Returns:
            Compressed chunks
        """
        compressed_chunks = []

        for chunk in chunks:
            # Extract relevant sentences
            relevant_sentences = self._extract_relevant_sentences(
                query,
                chunk.text,
                keep_ratio=compression_ratio
            )

            # Create compressed chunk
            compressed_text = " ".join(relevant_sentences)

            if compressed_text:  # Only keep if has content
                compressed_chunk = Chunk(
                    text=compressed_text,
                    metadata=chunk.metadata.copy(),
                    score=chunk.score
                )
                compressed_chunk.metadata['compressed'] = True
                compressed_chunk.metadata['original_length'] = len(chunk.text)
                compressed_chunk.metadata['compressed_length'] = len(compressed_text)

                compressed_chunks.append(compressed_chunk)

        return compressed_chunks

    def _extract_relevant_sentences(
        self,
        query: str,
        text: str,
        keep_ratio: float = 0.5
    ) -> List[str]:
        """
        Extract sentences most relevant to query.

        Uses simple sentence scoring based on:
        1. Keyword overlap with query
        2. Position (earlier sentences slightly favored)
        3. Sentence length (penalize very short/long)
        """
        # Split into sentences
        sentences = self._split_sentences(text)

        if not sentences:
            return []

        # Score each sentence
        query_words = set(query.lower().split())
        scored_sentences = []

        for i, sentence in enumerate(sentences):
            score = self._score_sentence(sentence, query_words, position=i)
            scored_sentences.append((sentence, score))

        # Sort by score
        scored_sentences.sort(key=lambda x: x[1], reverse=True)

        # Keep top sentences based on ratio
        num_keep = max(1, int(len(sentences) * keep_ratio))
        top_sentences = scored_sentences[:num_keep]

        # Re-order by original position
        positions = {s: i for i, s in enumerate(sentences)}
        top_sentences.sort(key=lambda x: positions[x[0]])

        return [s for s, score in top_sentences]

    def _score_sentence(
        self,
        sentence: str,
        query_words: set,
        position: int
    ) -> float:
        """Score sentence relevance."""
        sentence_words = set(sentence.lower().split())

        # Keyword overlap
        overlap = len(query_words & sentence_words)
        overlap_score = overlap / len(query_words) if query_words else 0

        # Position score (slight preference for earlier)
        position_score = 1.0 / (1.0 + position * 0.1)

        # Length penalty (penalize very short or very long)
        length = len(sentence.split())
        if length < 5:
            length_score = 0.5
        elif length > 50:
            length_score = 0.8
        else:
            length_score = 1.0

        # Combined score
        return overlap_score * 0.7 + position_score * 0.2 + length_score * 0.1

    def _split_sentences(self, text: str) -> List[str]:
        """Split text into sentences."""
        # Simple sentence splitting
        sentences = re.split(r'[.!?]+', text)
        return [s.strip() for s in sentences if s.strip()]
```

**Advanced: LLM-based Compression**
```python
def compress_with_llm(self, query: str, chunk: Chunk) -> str:
    """Use LLM to extract relevant portions."""
    compression_prompt = f"""
Extract only the parts of this text that are relevant to answering the question.
Keep original wording but remove irrelevant sentences.

Question: {query}

Text: {chunk.text}

Relevant excerpts:"""

    compressed = self.llm.generate(
        query=compression_prompt,
        context="",
        temperature=0.1,
        max_tokens=500
    )

    return compressed
```

#### Testing Requirements
- [ ] Test compression maintains relevant info
- [ ] Test compression removes irrelevant info
- [ ] Measure answer quality with/without compression
- [ ] Measure token savings
- [ ] Test with various compression ratios

#### Files to Create
- `src/retrieval/compressor.py` (~250 lines)
- `tests/retrieval/test_compressor.py` (~150 lines)

#### Acceptance Criteria
- ✅ Compression reduces tokens by 30-50%
- ✅ Answer quality maintained or improved
- ✅ Configurable compression ratio
- ✅ Option for LLM-based vs rule-based compression

---

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

## Part 3: Multi-Modal Support (35 hours)

### FEAT-007: Image Understanding (OCR + Vision)

**Priority**: Medium-High
**Estimated Time**: 20 hours
**Impact**: Handle documents with images, diagrams, scanned text
**Dependencies**: Tesseract OCR, Ollama llava model

#### Scope
Extract and understand images from PDFs:
1. **OCR**: Extract text from images (Tesseract)
2. **Vision**: Describe/understand images (Ollama llava)
3. **Integration**: Include image content in retrieval

#### Implementation

```python
# src/ingestion/image_processor.py (NEW FILE)
"""Image extraction and processing from documents."""
from typing import List, Dict
from pathlib import Path
from PIL import Image
import pytesseract
import fitz  # PyMuPDF
import logging

logger = logging.get_logger(__name__)

class ImageProcessor:
    """
    Extract and process images from documents.

    Supports:
    - OCR for text extraction
    - Vision models for image understanding
    """

    def __init__(
        self,
        use_ocr: bool = True,
        use_vision: bool = False,
        vision_model: str = "llava:latest"
    ):
        """
        Initialize image processor.

        Args:
            use_ocr: Extract text from images using OCR
            use_vision: Generate image descriptions using vision model
            vision_model: Ollama vision model name
        """
        self.use_ocr = use_ocr
        self.use_vision = use_vision
        self.vision_model = vision_model

        if use_vision:
            from src.generation.ollama_client import OllamaClient
            self.vision_client = OllamaClient(model=vision_model)

    def extract_images_from_pdf(
        self,
        pdf_path: Path
    ) -> List[Dict]:
        """
        Extract all images from PDF.

        Args:
            pdf_path: Path to PDF file

        Returns:
            List of image dictionaries with:
                - image: PIL Image object
                - page: Page number
                - bbox: Bounding box (x0, y0, x1, y1)
                - image_index: Index on page
        """
        images = []

        doc = fitz.open(pdf_path)

        for page_num, page in enumerate(doc):
            # Get images on page
            image_list = page.get_images()

            for img_index, img in enumerate(image_list):
                try:
                    # Extract image
                    xref = img[0]
                    base_image = doc.extract_image(xref)
                    image_bytes = base_image["image"]

                    # Convert to PIL Image
                    import io
                    pil_image = Image.open(io.BytesIO(image_bytes))

                    # Get bounding box (if available)
                    bbox = page.get_image_bbox(img)

                    images.append({
                        'image': pil_image,
                        'page': page_num + 1,
                        'bbox': bbox,
                        'image_index': img_index
                    })

                except Exception as e:
                    logger.warning(
                        f"Failed to extract image {img_index} from page {page_num + 1}: {e}"
                    )
                    continue

        doc.close()

        logger.info(f"Extracted {len(images)} images from {pdf_path}")
        return images

    def process_image(
        self,
        image: Image.Image,
        page: int
    ) -> Dict[str, str]:
        """
        Process a single image with OCR and/or vision.

        Args:
            image: PIL Image
            page: Page number

        Returns:
            Dictionary with:
                - ocr_text: Extracted text (if use_ocr)
                - description: Image description (if use_vision)
                - page: Page number
        """
        result = {'page': page}

        # OCR
        if self.use_ocr:
            try:
                ocr_text = pytesseract.image_to_string(image)
                if ocr_text.strip():
                    result['ocr_text'] = ocr_text.strip()
                    logger.debug(f"OCR extracted {len(ocr_text)} chars from image on page {page}")
            except Exception as e:
                logger.warning(f"OCR failed for image on page {page}: {e}")

        # Vision model description
        if self.use_vision:
            try:
                # Save image temporarily
                temp_path = Path(f"/tmp/ragged_image_{page}.png")
                image.save(temp_path)

                # Generate description
                description = self.vision_client.generate_from_image(
                    image_path=temp_path,
                    prompt="Describe this image in detail. If it contains diagrams, charts, or tables, explain what they show."
                )

                if description.strip():
                    result['description'] = description.strip()
                    logger.debug(f"Vision model described image on page {page}")

                # Clean up
                temp_path.unlink()

            except Exception as e:
                logger.warning(f"Vision model failed for image on page {page}: {e}")

        return result

    def process_all_images(
        self,
        pdf_path: Path
    ) -> List[Dict]:
        """
        Extract and process all images from PDF.

        Args:
            pdf_path: Path to PDF

        Returns:
            List of processed image data
        """
        # Extract images
        images = self.extract_images_from_pdf(pdf_path)

        # Process each image
        processed = []
        for img_data in images:
            result = self.process_image(
                img_data['image'],
                img_data['page']
            )
            result.update({
                'bbox': img_data['bbox'],
                'image_index': img_data['image_index']
            })
            processed.append(result)

        return processed
```

**Integration into Document Loading**:
```python
# src/ingestion/loaders.py - enhance PDF loader
class PDFLoader:
    def load(self, file_path: Path) -> Document:
        # Standard text extraction
        doc = self._extract_text(file_path)

        # Extract images if enabled
        if settings.process_images:
            image_processor = ImageProcessor(
                use_ocr=settings.use_ocr,
                use_vision=settings.use_vision_model
            )

            image_data = image_processor.process_all_images(file_path)

            # Add image content to document metadata
            doc.metadata['images'] = image_data

            # Optionally append image text to document text
            for img in image_data:
                if 'ocr_text' in img:
                    doc.text += f"\n\n[Image on page {img['page']} - OCR text]: {img['ocr_text']}"
                if 'description' in img:
                    doc.text += f"\n\n[Image on page {img['page']} - Description]: {img['description']}"

        return doc
```

#### Testing Requirements
- [ ] Test image extraction from PDF
- [ ] Test OCR on text images
- [ ] Test vision model descriptions
- [ ] Test retrieval includes image content
- [ ] Test with various image types (photos, diagrams, scanned text)

#### Files to Create
- `src/ingestion/image_processor.py` (~350 lines)
- `tests/ingestion/test_image_processor.py` (~200 lines)

#### Files to Modify
- `src/ingestion/loaders.py` (integrate image processing)
- `src/config/settings.py` (add image processing settings)

#### Dependencies to Add
```toml
# pyproject.toml
pytesseract = "^0.3.10"
Pillow = "^10.0.0"
PyMuPDF = "^1.23.0"  # Already have this
```

#### Acceptance Criteria
- ✅ Can extract images from PDFs
- ✅ OCR works on text images
- ✅ Vision model generates useful descriptions
- ✅ Image content searchable via retrieval

---

### FEAT-008: Table Extraction & Understanding

**Priority**: Medium
**Estimated Time**: 15 hours
**Impact**: Handle structured data in documents
**Dependencies**: camelot-py or tabula-py

#### Implementation

```python
# src/ingestion/table_processor.py (NEW FILE)
"""Table extraction and processing."""
from typing import List, Dict
from pathlib import Path
import camelot
import pandas as pd

class TableProcessor:
    """Extract and process tables from PDFs."""

    def __init__(self, llm=None):
        self.llm = llm

    def extract_tables(
        self,
        pdf_path: Path,
        pages: str = 'all'
    ) -> List[Dict]:
        """
        Extract tables from PDF.

        Args:
            pdf_path: Path to PDF
            pages: Pages to process ('all' or '1,2,3' or '1-10')

        Returns:
            List of table dictionaries
        """
        try:
            # Extract tables using camelot
            tables = camelot.read_pdf(
                str(pdf_path),
                pages=pages,
                flavor='lattice'  # Use 'stream' for tables without borders
            )

            processed_tables = []

            for i, table in enumerate(tables):
                # Convert to pandas DataFrame
                df = table.df

                # Skip empty tables
                if df.empty:
                    continue

                # Convert to various formats
                table_data = {
                    'table_index': i,
                    'page': table.page,
                    'dataframe': df,
                    'markdown': df.to_markdown(index=False),
                    'csv': df.to_csv(index=False),
                    'html': df.to_html(index=False),
                    'shape': df.shape,
                    'columns': list(df.columns)
                }

                # Generate natural language description if LLM available
                if self.llm:
                    table_data['description'] = self._describe_table(df)

                processed_tables.append(table_data)

            logger.info(f"Extracted {len(processed_tables)} tables from {pdf_path}")
            return processed_tables

        except Exception as e:
            logger.error(f"Table extraction failed: {e}")
            return []

    def _describe_table(self, df: pd.DataFrame) -> str:
        """Generate natural language description of table."""
        description_prompt = f"""
Describe this table in natural language. Explain what data it contains and any key insights.

Table (as CSV):
{df.to_csv(index=False)}

Description:"""

        description = self.llm.generate(
            query=description_prompt,
            context="",
            temperature=0.3,
            max_tokens=200
        )

        return description.strip()

    def convert_to_searchable_text(self, table_data: Dict) -> str:
        """
        Convert table to searchable text format.

        Combines markdown representation with natural language description.
        """
        parts = []

        # Add description if available
        if 'description' in table_data:
            parts.append(f"Table Description: {table_data['description']}")

        # Add markdown representation
        parts.append(f"\nTable (Page {table_data['page']}):\n{table_data['markdown']}")

        return "\n".join(parts)
```

**Integration**:
```python
# src/ingestion/loaders.py
class PDFLoader:
    def load(self, file_path: Path) -> Document:
        doc = self._extract_text(file_path)

        # Extract tables
        if settings.process_tables:
            table_processor = TableProcessor(llm=ollama_client)
            tables = table_processor.extract_tables(file_path)

            # Add tables to document
            for table in tables:
                table_text = table_processor.convert_to_searchable_text(table)
                doc.text += f"\n\n{table_text}"

            doc.metadata['tables'] = tables

        return doc
```

#### Testing Requirements
- [ ] Test table extraction from PDFs
- [ ] Test table-to-markdown conversion
- [ ] Test table descriptions
- [ ] Test retrieval over table content
- [ ] Test with various table formats

#### Files to Create
- `src/ingestion/table_processor.py` (~250 lines)
- `tests/ingestion/test_table_processor.py` (~150 lines)

#### Dependencies
```toml
camelot-py = "^0.11.0"
opencv-python = "^4.8.0"  # Required by camelot
```

#### Acceptance Criteria
- ✅ Can extract tables from PDFs
- ✅ Tables converted to searchable format
- ✅ LLM can answer questions about table data

---

## Part 4: Evaluation & Quality (24 hours)

### FEAT-009: RAGAS Evaluation Framework

**Priority**: High
**Estimated Time**: 16 hours
**Impact**: Quantify system quality, track improvements
**Research**: "RAGAS: Automated Evaluation of RAG Systems" (arXiv:2309.15217)

#### What is RAGAS?

RAGAS (Retrieval-Augmented Generation Assessment) provides automated metrics for RAG quality:
- **Faithfulness**: Is the answer faithful to the retrieved context?
- **Answer Relevancy**: Is the answer relevant to the question?
- **Context Precision**: Are retrieved chunks relevant?
- **Context Recall**: Are all relevant chunks retrieved?

#### Implementation

```python
# src/evaluation/ragas_eval.py (NEW FILE)
"""RAGAS evaluation framework integration."""
from typing import List, Dict
from dataclasses import dataclass
import json
from pathlib import Path

@dataclass
class RAGASMetrics:
    """RAGAS evaluation metrics."""
    faithfulness: float
    answer_relevancy: float
    context_precision: float
    context_recall: float
    overall_score: float

class RAGASEvaluator:
    """
    Evaluate RAG system using RAGAS metrics.

    Requires:
    - Test dataset with questions, ground truth answers
    - RAG system to evaluate
    """

    def __init__(self, llm_for_evaluation):
        """
        Initialize RAGAS evaluator.

        Args:
            llm_for_evaluation: LLM to use for metric calculation
        """
        self.llm = llm_for_evaluation

    def evaluate(
        self,
        test_dataset: List[Dict],
        rag_system
    ) -> RAGASMetrics:
        """
        Evaluate RAG system on test dataset.

        Args:
            test_dataset: List of test cases with format:
                {
                    'question': str,
                    'ground_truth': str,  # Expected answer
                    'contexts': List[str]  # Ground truth contexts (optional)
                }
            rag_system: RAG system to evaluate (must have query method)

        Returns:
            RAGAS metrics
        """
        faithfulness_scores = []
        relevancy_scores = []
        precision_scores = []
        recall_scores = []

        for test_case in test_dataset:
            question = test_case['question']
            ground_truth = test_case['ground_truth']

            # Get RAG system's answer and retrieved contexts
            result = rag_system.query(question)
            answer = result['answer']
            retrieved_contexts = [chunk.text for chunk in result['chunks']]

            # Calculate metrics
            faithfulness = self._calculate_faithfulness(
                question, answer, retrieved_contexts
            )
            faithfulness_scores.append(faithfulness)

            relevancy = self._calculate_answer_relevancy(
                question, answer
            )
            relevancy_scores.append(relevancy)

            # If ground truth contexts provided, calculate precision/recall
            if 'contexts' in test_case:
                precision = self._calculate_context_precision(
                    retrieved_contexts,
                    test_case['contexts']
                )
                precision_scores.append(precision)

                recall = self._calculate_context_recall(
                    retrieved_contexts,
                    test_case['contexts']
                )
                recall_scores.append(recall)

        # Aggregate scores
        metrics = RAGASMetrics(
            faithfulness=sum(faithfulness_scores) / len(faithfulness_scores),
            answer_relevancy=sum(relevancy_scores) / len(relevancy_scores),
            context_precision=sum(precision_scores) / len(precision_scores) if precision_scores else 0.0,
            context_recall=sum(recall_scores) / len(recall_scores) if recall_scores else 0.0,
            overall_score=0.0  # Will calculate below
        )

        # Overall score is average of available metrics
        available_metrics = [
            metrics.faithfulness,
            metrics.answer_relevancy
        ]
        if precision_scores:
            available_metrics.append(metrics.context_precision)
        if recall_scores:
            available_metrics.append(metrics.context_recall)

        metrics.overall_score = sum(available_metrics) / len(available_metrics)

        return metrics

    def _calculate_faithfulness(
        self,
        question: str,
        answer: str,
        contexts: List[str]
    ) -> float:
        """
        Calculate faithfulness: Is answer supported by context?

        Uses LLM to check if each statement in the answer can be
        inferred from the context.
        """
        faithfulness_prompt = f"""
Given a question, answer, and context, determine if the answer is faithful to the context.

An answer is faithful if all statements in it can be inferred from the context.

Question: {question}

Context:
{chr(10).join(contexts)}

Answer: {answer}

For each statement in the answer, can it be inferred from the context?
Provide your analysis and a faithfulness score from 0.0 (not faithful) to 1.0 (completely faithful).

Faithfulness score:"""

        response = self.llm.generate(
            query=faithfulness_prompt,
            context="",
            temperature=0.1
        )

        # Parse score from response
        score = self._parse_score(response)
        return score

    def _calculate_answer_relevancy(
        self,
        question: str,
        answer: str
    ) -> float:
        """
        Calculate answer relevancy: Does answer address the question?
        """
        relevancy_prompt = f"""
Rate how well this answer addresses the question.

Question: {question}

Answer: {answer}

Provide a relevancy score from 0.0 (not relevant) to 1.0 (perfectly relevant).

Relevancy score:"""

        response = self.llm.generate(
            query=relevancy_prompt,
            context="",
            temperature=0.1
        )

        score = self._parse_score(response)
        return score

    def _calculate_context_precision(
        self,
        retrieved: List[str],
        ground_truth: List[str]
    ) -> float:
        """
        Context precision: What fraction of retrieved contexts are relevant?
        """
        if not retrieved:
            return 0.0

        # Count how many retrieved contexts are in ground truth
        relevant_count = sum(
            1 for r in retrieved
            if any(self._is_similar(r, gt) for gt in ground_truth)
        )

        return relevant_count / len(retrieved)

    def _calculate_context_recall(
        self,
        retrieved: List[str],
        ground_truth: List[str]
    ) -> float:
        """
        Context recall: What fraction of relevant contexts were retrieved?
        """
        if not ground_truth:
            return 1.0  # No ground truth to retrieve

        # Count how many ground truth contexts were retrieved
        retrieved_count = sum(
            1 for gt in ground_truth
            if any(self._is_similar(gt, r) for r in retrieved)
        )

        return retrieved_count / len(ground_truth)

    def _is_similar(self, text1: str, text2: str, threshold: float = 0.7) -> bool:
        """Check if two texts are similar (simple Jaccard similarity)."""
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())

        intersection = words1 & words2
        union = words1 | words2

        similarity = len(intersection) / len(union) if union else 0.0
        return similarity >= threshold

    def _parse_score(self, response: str) -> float:
        """Parse score from LLM response."""
        import re

        # Look for number between 0 and 1
        match = re.search(r'([0-1]\.?\d*)', response)
        if match:
            score = float(match.group(1))
            return max(0.0, min(1.0, score))  # Clamp to [0, 1]

        return 0.5  # Default if can't parse
```

**CLI Integration**:
```python
# src/main.py - new command
@main.command()
@click.argument("dataset", type=click.Path(exists=True))
@click.option("--output", help="Output file for results")
def evaluate(dataset: str, output: str):
    """Evaluate RAG system using RAGAS metrics."""
    from src.evaluation.ragas_eval import RAGASEvaluator

    # Load test dataset
    with open(dataset) as f:
        test_data = json.load(f)

    # Initialize evaluator
    evaluator = RAGASEvaluator(ollama_client)

    # Run evaluation
    console.print("[cyan]Running RAGAS evaluation...[/cyan]")
    metrics = evaluator.evaluate(test_data, rag_system)

    # Display results
    table = Table(title="RAGAS Evaluation Results")
    table.add_column("Metric")
    table.add_column("Score", justify="right")

    table.add_row("Faithfulness", f"{metrics.faithfulness:.3f}")
    table.add_row("Answer Relevancy", f"{metrics.answer_relevancy:.3f}")
    table.add_row("Context Precision", f"{metrics.context_precision:.3f}")
    table.add_row("Context Recall", f"{metrics.context_recall:.3f}")
    table.add_row("[bold]Overall Score[/bold]", f"[bold]{metrics.overall_score:.3f}[/bold]")

    console.print(table)

    # Save to file if requested
    if output:
        results = {
            'metrics': {
                'faithfulness': metrics.faithfulness,
                'answer_relevancy': metrics.answer_relevancy,
                'context_precision': metrics.context_precision,
                'context_recall': metrics.context_recall,
                'overall_score': metrics.overall_score
            },
            'timestamp': str(datetime.now())
        }

        with open(output, 'w') as f:
            json.dump(results, f, indent=2)

        console.print(f"\n[green]✓[/green] Results saved to {output}")
```

#### Testing Requirements
- [ ] Test metric calculation on sample data
- [ ] Create test dataset
- [ ] Validate scores are in [0, 1]
- [ ] Test evaluation CLI command
- [ ] Compare metrics before/after improvements

#### Files to Create
- `src/evaluation/ragas_eval.py` (~400 lines)
- `src/evaluation/test_dataset.json` (sample test data)
- `tests/evaluation/test_ragas.py` (~150 lines)

#### Acceptance Criteria
- ✅ RAGAS metrics implemented
- ✅ Can evaluate system on test dataset
- ✅ Metrics track quality improvements
- ✅ CLI command for evaluation

---

### FEAT-010: Answer Confidence Scores

**Priority**: Medium
**Estimated Time**: 8 hours
**Impact**: Users know when to verify answers

#### Implementation

```python
# src/generation/confidence.py (NEW FILE)
"""Confidence scoring for generated answers."""

class ConfidenceScorer:
    """
    Estimate confidence in generated answers.

    Uses multiple signals:
    - Retrieval scores (how good are the retrieved chunks?)
    - Answer-context alignment (does answer match context?)
    - Self-assessment (ask LLM for confidence)
    """

    def __init__(self, llm):
        self.llm = llm

    def calculate_confidence(
        self,
        query: str,
        answer: str,
        chunks: List[Chunk]
    ) -> Dict:
        """
        Calculate confidence score for an answer.

        Returns:
            Dictionary with:
                - score: Overall confidence (0.0-1.0)
                - signals: Individual confidence signals
                - reasoning: Explanation of score
        """
        signals = {}

        # Signal 1: Retrieval quality
        signals['retrieval'] = self._retrieval_quality(chunks)

        # Signal 2: Answer length (very short may indicate low confidence)
        signals['answer_length'] = self._answer_length_signal(answer)

        # Signal 3: LLM self-assessment
        signals['self_assessment'] = self._llm_self_assessment(
            query, answer, chunks
        )

        # Combine signals
        overall_score = (
            signals['retrieval'] * 0.3 +
            signals['answer_length'] * 0.1 +
            signals['self_assessment'] * 0.6
        )

        # Get reasoning
        reasoning = self._explain_confidence(signals, overall_score)

        return {
            'score': overall_score,
            'signals': signals,
            'reasoning': reasoning
        }

    def _retrieval_quality(self, chunks: List[Chunk]) -> float:
        """Score based on retrieval quality."""
        if not chunks:
            return 0.0

        # Average of top chunk scores
        scores = [c.score for c in chunks[:3]]
        return sum(scores) / len(scores)

    def _answer_length_signal(self, answer: str) -> float:
        """Score based on answer length."""
        words = len(answer.split())

        if words < 10:
            return 0.3  # Very short answers may be uncertain
        elif words < 50:
            return 1.0  # Normal length
        elif words < 200:
            return 0.9  # Longer is ok
        else:
            return 0.7  # Very long might be rambling

    def _llm_self_assessment(
        self,
        query: str,
        answer: str,
        chunks: List[Chunk]
    ) -> float:
        """Ask LLM to assess its own confidence."""
        context = "\n\n".join([c.text for c in chunks[:3]])

        prompt = f"""
You just answered a question. Rate your confidence in the answer.

Question: {query}

Context used:
{context}

Your answer: {answer}

On a scale of 0.0 (no confidence) to 1.0 (very confident), how confident are you that this answer is correct and complete?

Consider:
- Is the context sufficient to answer the question?
- Did you make any assumptions?
- Are there gaps in your knowledge?

Confidence score (0.0-1.0):"""

        response = self.llm.generate(
            query=prompt,
            context="",
            temperature=0.1
        )

        # Parse score
        import re
        match = re.search(r'([0-1]\.?\d*)', response)
        if match:
            return float(match.group(1))

        return 0.5  # Default

    def _explain_confidence(self, signals: Dict, score: float) -> str:
        """Generate human-readable explanation of confidence."""
        explanations = []

        if signals['retrieval'] < 0.5:
            explanations.append("Retrieved context had low relevance scores")

        if signals['answer_length'] < 0.5:
            explanations.append("Answer was unusually short")

        if signals['self_assessment'] < 0.5:
            explanations.append("Answer may contain uncertainties or assumptions")

        if score >= 0.8:
            level = "High confidence"
        elif score >= 0.6:
            level = "Moderate confidence"
        else:
            level = "Low confidence"

        if explanations:
            return f"{level}. {'; '.join(explanations)}."
        else:
            return f"{level}. Answer is well-supported by retrieved context."
```

**Display to User**:
```python
# src/main.py - query command
def query(query_text: str):
    # ... retrieval and generation ...

    # Calculate confidence
    confidence = ConfidenceScorer(ollama_client).calculate_confidence(
        query_text, answer, chunks
    )

    # Display answer
    console.print("\n[bold]Answer:[/bold]")
    console.print(answer)

    # Display confidence
    score = confidence['score']
    if score >= 0.8:
        color = "green"
        emoji = "✓"
    elif score >= 0.6:
        color = "yellow"
        emoji = "⚠"
    else:
        color = "red"
        emoji = "⚠"

    console.print(f"\n[{color}]{emoji} Confidence: {score:.1%}[/{color}]")
    console.print(f"[dim]{confidence['reasoning']}[/dim]")

    if score < 0.5:
        console.print("\n[red]Note: Low confidence. Please verify this answer.[/red]")
```

#### Testing Requirements
- [ ] Test confidence calculation on various queries
- [ ] Validate confidence correlates with quality
- [ ] Test low confidence detection
- [ ] Test confidence display in UI

#### Files to Create
- `src/generation/confidence.py` (~200 lines)
- `tests/generation/test_confidence.py` (~100 lines)

#### Acceptance Criteria
- ✅ Confidence scores calculated
- ✅ Low confidence warnings shown
- ✅ Scores correlate with answer quality

---

## Part 5: Advanced Data Management (32 hours)

### FEAT-011-013: Data Management Features

Due to length, I'll summarize:

**FEAT-011: Document Version Tracking** (14 hours)
- Track document versions over time
- Compare versions, query specific versions
- Detect when documents are updated

**FEAT-012: Metadata Filtering & Faceted Search** (10 hours)
- Rich filtering: by author, date, tags, format
- Faceted search in UI
- Complex queries with filters

**FEAT-013: Auto-Tagging & Classification** (8 hours)
- Automatic keyword extraction (KeyBERT, TF-IDF)
- Document classification (topic, category)
- Auto-generate tags on ingestion

---

## Part 6: Advanced Generation (22 hours)

### FEAT-014: Chain-of-Thought Reasoning

**Priority**: Medium-High
**Estimated Time**: 12 hours
**Impact**: Better complex question answering

Multi-step reasoning for complex questions:
1. Extract key information from context
2. Reason about the question
3. Generate final answer

Shows reasoning steps to user for transparency.

### FEAT-015: Enhanced Citations

**Priority**: Medium
**Estimated Time**: 10 hours
**Impact**: Better verifiability

Improvements to citation system:
- Inline citations with hover text (Web UI)
- Click citations to view source
- Confidence scores per citation
- Character-level source attribution

---

## Summary & Implementation Recommendations

### Total Features: 15

| Category | Features | Hours |
|----------|----------|-------|
| Query & Retrieval | 4 | 41 |
| Chunking | 2 | 28 |
| Multi-Modal | 2 | 35 |
| Evaluation | 2 | 24 |
| Data Management | 3 | 32 |
| Generation | 2 | 22 |
| **Total** | **15** | **182** |

### Recommended Implementation Order

**Phase 1: Core Improvements** (70-90 hours)
1. FEAT-009: RAGAS evaluation (establish baseline)
2. FEAT-003: Reranking (quick win)
3. FEAT-002: HyDE retrieval
4. FEAT-001: Query decomposition
5. FEAT-005: Semantic chunking

**Phase 2: Multi-Modal & Advanced Features** (50-70 hours)
6. FEAT-007: Image processing
7. FEAT-008: Table extraction
8. FEAT-010: Confidence scores
9. FEAT-014: Chain-of-thought

**Phase 3: Production Features** (50-60 hours)
10. FEAT-006: Hierarchical chunking
11. FEAT-011: Version tracking
12. FEAT-012: Metadata filtering
13. FEAT-013: Auto-tagging
14. FEAT-004: Contextual compression
15. FEAT-015: Enhanced citations

### Success Criteria

v0.3.0 is successful if:
1. ✅ 10-20% retrieval quality improvement (RAGAS metrics)
2. ✅ Multi-modal documents supported (images, tables)
3. ✅ Evaluation framework operational
4. ✅ Complex questions handled well
5. ✅ All features well-documented
6. ✅ Test coverage ≥75%

### Breaking Changes

Minimal breaking changes - mostly additive:
- New chunking methods opt-in
- Multi-modal processing opt-in
- All advanced features configurable

### Dependencies

New dependencies to add:
```toml
# Multi-modal
pytesseract = "^0.3.10"
camelot-py = "^0.11.0"
opencv-python = "^4.8.0"

# Evaluation
sentence-transformers = "^2.2.0"  # For cross-encoders

# Utilities
keybert = "^0.8.0"  # For auto-tagging
nltk = "^3.8.0"  # For sentence splitting
```

### Research Papers Referenced

1. Query Decomposition: arXiv:2305.14283
2. HyDE: arXiv:2212.10496
3. RAGAS: arXiv:2309.15217
4. Dense Retrieval: Various DPR papers
5. Contextual Compression: LongLLMLingua

---

**Next Steps**: After completing v0.3.0, ragged will be a state-of-the-art RAG system ready for production use.

**Future Considerations** (v0.4+):
- Agent-based RAG (ReAct, function calling)
- Graph RAG (knowledge graphs)
- Online learning (user feedback incorporation)
- Distributed RAG (multi-machine scaling)
