"""
Document retrieval using vector similarity search.

Handles query processing, embedding, and retrieval of relevant document chunks.
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from src.embeddings.factory import get_embedder
from src.storage.vector_store import VectorStore
from src.utils.logging import get_logger

logger = get_logger(__name__)


@dataclass
class RetrievedChunk:
    """A retrieved chunk with metadata and score."""

    text: str
    score: float  # Similarity score (lower distance = higher similarity)
    chunk_id: str
    document_id: str
    document_path: str
    chunk_position: int
    metadata: Dict[str, Any]

    def __repr__(self) -> str:
        """String representation."""
        preview = self.text[:50] + "..." if len(self.text) > 50 else self.text
        return f"RetrievedChunk(score={self.score:.3f}, text='{preview}')"


class Retriever:
    """
    Retrieve relevant document chunks for queries.

    Combines embedding and vector search to find relevant chunks.
    """

    def __init__(
        self,
        vector_store: Optional[VectorStore] = None,
        embedder = None,
    ):
        """
        Initialize retriever.

        Args:
            vector_store: Vector store instance (creates default if None)
            embedder: Embedder instance (creates default if None)
        """
        self.vector_store = vector_store or VectorStore()
        self.embedder = embedder or get_embedder()

        # Health check
        if not self.vector_store.health_check():
            logger.warning("Vector store health check failed")

        logger.info(f"Retriever initialized with {self.embedder.model_name}")

    def retrieve(
        self,
        query: str,
        k: int = 5,
        filter_metadata: Optional[Dict[str, Any]] = None,
        min_score: Optional[float] = None,
    ) -> List[RetrievedChunk]:
        """
        Retrieve relevant chunks for a query.

        Args:
            query: Query string
            k: Number of chunks to retrieve
            filter_metadata: Optional metadata filter
            min_score: Optional minimum similarity score threshold

        Returns:
            List of retrieved chunks ordered by relevance

        Example:
            >>> retriever = Retriever()
            >>> results = retriever.retrieve("What is machine learning?", k=3)
            >>> for chunk in results:
            ...     print(f"{chunk.score:.3f}: {chunk.text[:50]}")
        """
        logger.info(f"Retrieving top {k} chunks for query")

        # Embed query
        query_embedding = self.embedder.embed_text(query)

        # Query vector store
        results = self.vector_store.query(
            query_embedding=query_embedding,
            k=k,
            where=filter_metadata,
        )

        # Parse results into RetrievedChunk objects
        chunks = []
        if results and results.get("ids") and len(results["ids"]) > 0:
            # ChromaDB returns lists within lists
            ids = results["ids"][0] if isinstance(results["ids"][0], list) else results["ids"]
            documents = results["documents"][0] if isinstance(results["documents"][0], list) else results["documents"]
            metadatas = results["metadatas"][0] if isinstance(results["metadatas"][0], list) else results["metadatas"]
            distances = results["distances"][0] if isinstance(results["distances"][0], list) else results["distances"]

            for i, (chunk_id, text, metadata, distance) in enumerate(zip(ids, documents, metadatas, distances)):
                # Convert distance to similarity score (lower distance = better match)
                # For display purposes, we keep distance as score
                score = distance

                # Filter by min_score if provided
                if min_score is not None and score > min_score:
                    continue

                chunk = RetrievedChunk(
                    text=text,
                    score=score,
                    chunk_id=chunk_id,
                    document_id=metadata.get("document_id", ""),
                    document_path=metadata.get("source_path", ""),
                    chunk_position=metadata.get("chunk_position", 0),
                    metadata=metadata,
                )
                chunks.append(chunk)

        logger.info(f"Retrieved {len(chunks)} chunks")
        return chunks

    def retrieve_with_context(
        self,
        query: str,
        k: int = 5,
        context_chunks: int = 1,
    ) -> List[RetrievedChunk]:
        """
        Retrieve chunks with surrounding context.

        Retrieves k chunks, then adds context_chunks before/after each.

        Args:
            query: Query string
            k: Number of main chunks to retrieve
            context_chunks: Number of chunks to include before/after each result

        Returns:
            List of chunks with context

        TODO: Implement context retrieval (v0.2 feature):
              1. Retrieve k chunks
              2. For each chunk, get adjacent chunks by position
              3. Deduplicate results
              4. Return with context
        """
        # For v0.1, just call regular retrieve
        return self.retrieve(query, k=k)

    def deduplicate_chunks(self, chunks: List[RetrievedChunk]) -> List[RetrievedChunk]:
        """
        Remove duplicate chunks from results.

        Args:
            chunks: List of retrieved chunks

        Returns:
            Deduplicated list
        """
        seen = set()
        deduplicated = []

        for chunk in chunks:
            if chunk.chunk_id not in seen:
                seen.add(chunk.chunk_id)
                deduplicated.append(chunk)

        if len(deduplicated) < len(chunks):
            logger.info(f"Deduplicated {len(chunks) - len(deduplicated)} chunks")

        return deduplicated
