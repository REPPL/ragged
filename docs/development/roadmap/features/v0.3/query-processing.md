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
        2. Position (earlier sentences slightly favoured)
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

