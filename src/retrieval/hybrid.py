"""Hybrid retrieval combining vector and keyword search."""

import logging
from dataclasses import dataclass
from typing import Any, Literal

from src.retrieval.bm25 import BM25Retriever
from src.retrieval.fusion import reciprocal_rank_fusion, weighted_fusion
from src.retrieval.retriever import RetrievedChunk, Retriever

logger = logging.getLogger(__name__)


@dataclass
class HybridConfig:
    """Configuration for hybrid retrieval."""

    method: Literal["vector", "bm25", "hybrid"] = "hybrid"
    fusion: Literal["rrf", "weighted"] = "rrf"
    rrf_k: int = 60
    alpha: float = 0.5  # Weight for vector search in weighted fusion (1-alpha for BM25)
    top_k_multiplier: int = 2  # Retrieve top_k * multiplier from each method


class HybridRetriever:
    """Hybrid retriever combining vector and BM25 keyword search.

    Provides three retrieval modes:
    - vector: Semantic search only (baseline)
    - bm25: Keyword search only
    - hybrid: Combined search with fusion (recommended)
    """

    def __init__(
        self,
        vector_retriever: Retriever,
        bm25_retriever: BM25Retriever,
        config: HybridConfig | None = None,
    ):
        """Initialize hybrid retriever.

        Args:
            vector_retriever: Vector-based semantic retriever
            bm25_retriever: BM25 keyword retriever
            config: Hybrid retrieval configuration
        """
        self.vector = vector_retriever
        self.bm25 = bm25_retriever
        self.config = config or HybridConfig()

    def retrieve(
        self,
        query: str,
        top_k: int = 5,
        method: Literal["vector", "bm25", "hybrid"] | None = None,
    ) -> list[RetrievedChunk]:
        """Retrieve relevant chunks using specified method.

        Args:
            query: Search query
            top_k: Number of results to return
            method: Retrieval method override (uses config if None)

        Returns:
            List of retrieved chunks, sorted by relevance
        """
        method = method or self.config.method

        if method == "vector":
            return self._vector_only(query, top_k)
        elif method == "bm25":
            return self._bm25_only(query, top_k)
        elif method == "hybrid":
            return self._hybrid_search(query, top_k)
        else:
            raise ValueError(f"Unknown retrieval method: {method}")

    def _vector_only(self, query: str, top_k: int) -> list[RetrievedChunk]:
        """Vector search only."""
        logger.debug(f"Vector-only retrieval for: {query}")
        return self.vector.retrieve(query, k=top_k)

    def _convert_bm25_to_chunk(
        self,
        doc_id: str,
        content: str,
        score: float,
        metadata: dict,
    ) -> RetrievedChunk:
        """Convert BM25 search result to RetrievedChunk format.

        Args:
            doc_id: Document ID from BM25 results
            content: Text content
            score: Relevance score
            metadata: Metadata dictionary from BM25

        Returns:
            RetrievedChunk with standardised format
        """
        return RetrievedChunk(
            text=content,
            score=score,
            chunk_id=doc_id,
            document_id=metadata.get("document_id", ""),
            document_path=metadata.get("source_file", "unknown"),
            chunk_position=metadata.get("chunk_index", 0),
            metadata=metadata,
        )

    def _bm25_only(self, query: str, top_k: int) -> list[RetrievedChunk]:
        """BM25 search only."""
        logger.debug(f"BM25-only retrieval for: {query}")

        results = self.bm25.search(query, top_k=top_k)

        # Convert to RetrievedChunk format
        chunks = [
            self._convert_bm25_to_chunk(doc_id, content, score, metadata)
            for doc_id, content, score, metadata in results
        ]

        return chunks

    def _hybrid_search(self, query: str, top_k: int) -> list[RetrievedChunk]:
        """Hybrid search combining vector and BM25."""
        logger.debug(f"Hybrid retrieval for: {query}")

        # Retrieve from both methods (more results for better fusion)
        k_expanded = top_k * self.config.top_k_multiplier

        # Vector search
        vector_results = self.vector.retrieve(query, k=k_expanded)

        # BM25 search
        bm25_results = self.bm25.search(query, top_k=k_expanded)

        # Convert to common format for fusion
        vector_tuples = [
            (chunk.chunk_id, chunk, chunk.score, chunk.metadata)
            for chunk in vector_results
        ]

        bm25_tuples = bm25_results  # Already in tuple format

        # Fusion
        if self.config.fusion == "rrf":
            fused = reciprocal_rank_fusion(
                [vector_tuples, bm25_tuples],
                k=self.config.rrf_k
            )
        else:  # weighted
            fused = weighted_fusion(
                [vector_tuples, bm25_tuples],
                weights=[self.config.alpha, 1.0 - self.config.alpha]
            )

        # Convert back to RetrievedChunk
        chunks = []
        for doc_id, content, score, metadata in fused[:top_k]:
            # Handle both RetrievedChunk and string content
            if isinstance(content, RetrievedChunk):
                # From vector search
                chunk = RetrievedChunk(
                    text=content.text,
                    score=score,  # Use fusion score
                    chunk_id=content.chunk_id,
                    document_id=content.document_id,
                    document_path=content.document_path,
                    chunk_position=content.chunk_position,
                    metadata=content.metadata,
                )
            else:
                # From BM25 search
                chunk = self._convert_bm25_to_chunk(doc_id, content, score, metadata)
            chunks.append(chunk)

        logger.info(
            f"Hybrid search: {len(vector_results)} vector + {len(bm25_results)} BM25 "
            f"-> {len(chunks)} fused results"
        )

        return chunks

    def update_bm25_index(
        self,
        documents: list[str],
        doc_ids: list[str],
        metadatas: list[dict[str, Any]] | None = None,
    ) -> None:
        """Update BM25 index with new documents.

        Args:
            documents: Document texts
            doc_ids: Document IDs
            metadatas: Optional metadata
        """
        self.bm25.index_documents(documents, doc_ids, metadatas)
        logger.info(f"Updated BM25 index with {len(documents)} documents")
