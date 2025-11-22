"""
Dual embedding storage for text and vision embeddings.

This module provides a unified storage layer that handles both text embeddings
(384-dim from all-MiniLM-L6-v2) and vision embeddings (128-dim from ColPali)
in a single ChromaDB collection.

Supports:
- Separate storage of text and vision embeddings
- Text-only, vision-only, and hybrid retrieval
- Reciprocal Rank Fusion (RRF) for hybrid queries
- Type-safe metadata handling

v0.5.0: Initial dual embedding storage
"""

import logging
from pathlib import Path
from typing import Any

import chromadb
import numpy as np
from chromadb.api import ClientAPI

from ragged.storage.schema import (
    EmbeddingType,
    TextMetadata,
    VisionMetadata,
    create_text_metadata,
    create_vision_metadata,
    generate_embedding_id,
)

logger = logging.getLogger(__name__)


class DualEmbeddingStore:
    """
    Storage manager for dual text+vision embeddings.

    Handles simultaneous storage and retrieval of:
    - Text embeddings (384-dimensional)
    - Vision embeddings (128-dimensional)

    Both types share common metadata (document_id, created_at) but have
    type-specific fields for their respective use cases.

    Example:
        >>> store = DualEmbeddingStore()
        >>> # Add text embedding
        >>> store.add_text_embedding(
        ...     "doc123", "chunk1", 0, text_embedding, "Sample text"
        ... )
        >>> # Add vision embedding
        >>> store.add_vision_embedding(
        ...     "doc123", 0, vision_embedding, "abc123hash"
        ... )
        >>> # Query with text
        >>> results = store.query_text(query_embedding, k=5)
    """

    def __init__(
        self,
        collection_name: str = "documents",
        persist_directory: Path | None = None,
        client: ClientAPI | None = None,
    ) -> None:
        """
        Initialise dual embedding storage.

        Uses two separate collections internally:
        - {collection_name}_text: 384-dim text embeddings
        - {collection_name}_vision: 128-dim vision embeddings

        Args:
            collection_name: Base collection name
            persist_directory: Directory for persistent storage
            client: Existing ChromaDB client (or None to create)

        Example:
            >>> store = DualEmbeddingStore()  # Default in-memory
            >>> store = DualEmbeddingStore(persist_directory=Path("~/.ragged/storage"))
        """
        self.collection_name = collection_name

        if client is not None:
            self.client = client
        else:
            if persist_directory:
                self.client = chromadb.PersistentClient(path=str(persist_directory))
            else:
                self.client = chromadb.Client()

        # Create separate collections for text and vision (different dimensions)
        self.text_collection = self.client.get_or_create_collection(
            name=f"{collection_name}_text", metadata={"schema_version": "v0.5", "embedding_type": "text"}
        )
        self.vision_collection = self.client.get_or_create_collection(
            name=f"{collection_name}_vision", metadata={"schema_version": "v0.5", "embedding_type": "vision"}
        )

        logger.info(
            f"Initialised DualEmbeddingStore with collections '{collection_name}_text' and '{collection_name}_vision'"
        )

    def add_text_embedding(
        self,
        document_id: str,
        chunk_id: str,
        chunk_index: int,
        embedding: np.ndarray,
        text_content: str,
        page_number: int | None = None,
    ) -> str:
        """
        Add text embedding to storage.

        Args:
            document_id: Parent document UUID
            chunk_id: Unique chunk identifier
            chunk_index: Position in document (0-indexed)
            embedding: 384-dimensional text embedding
            text_content: Actual text content
            page_number: Source page number (optional, 0-indexed)

        Returns:
            Generated embedding ID

        Raises:
            ValueError: If embedding dimension incorrect

        Example:
            >>> embedding = np.random.rand(384)
            >>> id = store.add_text_embedding(
            ...     "doc123", "chunk1", 0, embedding, "Sample text", page_number=0
            ... )
            >>> id
            'doc123_chunk_0_text'
        """
        if embedding.shape[0] != 384:
            raise ValueError(f"Text embedding must be 384-dimensional, got {embedding.shape[0]}")

        embedding_id = generate_embedding_id(document_id, EmbeddingType.TEXT, chunk_index)

        metadata = create_text_metadata(
            document_id=document_id,
            chunk_id=chunk_id,
            chunk_index=chunk_index,
            text_content=text_content,
            page_number=page_number,
        )

        # Remove None values - ChromaDB only supports str, int, float, bool
        metadata_filtered = {k: v for k, v in metadata.items() if v is not None}

        self.text_collection.add(
            ids=[embedding_id],
            embeddings=[embedding.tolist()],
            metadatas=[metadata_filtered],  # type: ignore
            documents=[text_content],
        )

        logger.debug(f"Added text embedding: {embedding_id}")
        return embedding_id

    def add_vision_embedding(
        self,
        document_id: str,
        page_number: int,
        embedding: np.ndarray,
        image_hash: str,
        has_diagrams: bool = False,
        has_tables: bool = False,
        layout_complexity: str = "simple",
    ) -> str:
        """
        Add vision embedding to storage.

        Args:
            document_id: Parent document UUID
            page_number: PDF page number (0-indexed)
            embedding: 128-dimensional vision embedding
            image_hash: SHA-256 hash of rendered page image
            has_diagrams: Whether page contains diagrams/charts
            has_tables: Whether page contains tables
            layout_complexity: Layout complexity ("simple", "moderate", "complex")

        Returns:
            Generated embedding ID

        Raises:
            ValueError: If embedding dimension incorrect

        Example:
            >>> embedding = np.random.rand(128)
            >>> id = store.add_vision_embedding(
            ...     "doc123", 0, embedding, "abc123hash", has_diagrams=True
            ... )
            >>> id
            'doc123_page_0_vision'
        """
        if embedding.shape[0] != 128:
            raise ValueError(f"Vision embedding must be 128-dimensional, got {embedding.shape[0]}")

        embedding_id = generate_embedding_id(document_id, EmbeddingType.VISION, page_number)

        metadata = create_vision_metadata(
            document_id=document_id,
            page_number=page_number,
            image_hash=image_hash,
            has_diagrams=has_diagrams,
            has_tables=has_tables,
            layout_complexity=layout_complexity,
        )

        # Remove None values - ChromaDB only supports str, int, float, bool
        metadata_filtered = {k: v for k, v in metadata.items() if v is not None}

        self.vision_collection.add(
            ids=[embedding_id],
            embeddings=[embedding.tolist()],
            metadatas=[metadata_filtered],  # type: ignore
        )

        logger.debug(f"Added vision embedding: {embedding_id}")
        return embedding_id

    def query_text(
        self, query_embedding: np.ndarray, k: int = 5, where_filter: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """
        Query using text embedding.

        Args:
            query_embedding: 384-dimensional query embedding
            k: Number of results to return
            where_filter: Additional metadata filters

        Returns:
            Query results with IDs, distances, metadatas

        Raises:
            ValueError: If query embedding dimension incorrect

        Example:
            >>> query = np.random.rand(384)
            >>> results = store.query_text(query, k=5)
            >>> len(results["ids"][0])
            5
        """
        if query_embedding.shape[0] != 384:
            raise ValueError(f"Text query must be 384-dimensional, got {query_embedding.shape[0]}")

        # Query text collection (no need to filter by embedding_type)
        results = self.text_collection.query(
            query_embeddings=[query_embedding.tolist()],
            n_results=k,
            where=where_filter,
            include=["metadatas", "distances", "documents"],
        )

        logger.debug(f"Text query returned {len(results['ids'][0])} results")
        return results

    def query_vision(
        self, query_embedding: np.ndarray, k: int = 5, where_filter: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """
        Query using vision embedding.

        Args:
            query_embedding: 128-dimensional query embedding
            k: Number of results to return
            where_filter: Additional metadata filters

        Returns:
            Query results with IDs, distances, metadatas

        Raises:
            ValueError: If query embedding dimension incorrect

        Example:
            >>> query = np.random.rand(128)
            >>> results = store.query_vision(query, k=5)
            >>> len(results["ids"][0])
            5
        """
        if query_embedding.shape[0] != 128:
            raise ValueError(f"Vision query must be 128-dimensional, got {query_embedding.shape[0]}")

        # Query vision collection (no need to filter by embedding_type)
        results = self.vision_collection.query(
            query_embeddings=[query_embedding.tolist()],
            n_results=k,
            where=where_filter,
            include=["metadatas", "distances"],
        )

        logger.debug(f"Vision query returned {len(results['ids'][0])} results")
        return results

    def get_by_document(
        self, document_id: str, embedding_type: EmbeddingType | None = None
    ) -> dict[str, Any]:
        """
        Retrieve all embeddings for a document.

        Args:
            document_id: Document UUID
            embedding_type: Filter by type (None = both types)

        Returns:
            Dictionary with embeddings, metadatas, and IDs

        Example:
            >>> results = store.get_by_document("doc123")
            >>> len(results["ids"])  # Both text and vision
            25
            >>> results_text = store.get_by_document("doc123", EmbeddingType.TEXT)
            >>> len(results_text["ids"])  # Only text
            20
        """
        where_filter = {"document_id": document_id}

        if embedding_type == EmbeddingType.TEXT:
            results = self.text_collection.get(where=where_filter, include=["embeddings", "metadatas"])
        elif embedding_type == EmbeddingType.VISION:
            results = self.vision_collection.get(where=where_filter, include=["embeddings", "metadatas"])
        else:
            # Get from both collections and merge
            text_results = self.text_collection.get(where=where_filter, include=["embeddings", "metadatas"])
            vision_results = self.vision_collection.get(where=where_filter, include=["embeddings", "metadatas"])

            # Merge results
            results = {
                "ids": text_results["ids"] + vision_results["ids"],
                "embeddings": text_results["embeddings"] + vision_results["embeddings"],
                "metadatas": text_results["metadatas"] + vision_results["metadatas"],
            }

        logger.debug(f"Retrieved {len(results['ids'])} embeddings for document {document_id}")

        return results

    def delete_document(self, document_id: str) -> int:
        """
        Delete all embeddings for a document from both collections.

        Args:
            document_id: Document UUID

        Returns:
            Number of embeddings deleted

        Example:
            >>> count = store.delete_document("doc123")
            >>> count
            25
        """
        total_deleted = 0
        where_filter = {"document_id": document_id}

        # Delete from text collection
        text_results = self.text_collection.get(where=where_filter)
        if text_results["ids"]:
            self.text_collection.delete(ids=text_results["ids"])
            total_deleted += len(text_results["ids"])

        # Delete from vision collection
        vision_results = self.vision_collection.get(where=where_filter)
        if vision_results["ids"]:
            self.vision_collection.delete(ids=vision_results["ids"])
            total_deleted += len(vision_results["ids"])

        logger.info(f"Deleted {total_deleted} embeddings for document {document_id}")
        return total_deleted

    def query_hybrid(
        self,
        text_embedding: np.ndarray | None = None,
        vision_embedding: np.ndarray | None = None,
        k: int = 10,
        text_weight: float = 0.5,
        vision_weight: float = 0.5,
        where_filter: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Hybrid query using both text and vision embeddings with RRF fusion.

        Uses Reciprocal Rank Fusion (RRF) to combine results from text and vision
        queries. RRF score = Σ(weight / (k + rank)) for each embedding type.

        Args:
            text_embedding: 384-dimensional text query embedding (optional)
            vision_embedding: 128-dimensional vision query embedding (optional)
            k: Number of results to return (after fusion)
            text_weight: Weight for text results (default: 0.5)
            vision_weight: Weight for vision results (default: 0.5)
            where_filter: Additional metadata filters

        Returns:
            Merged query results with IDs, distances, metadatas, and RRF scores

        Raises:
            ValueError: If neither embedding provided, or weights invalid

        Example:
            >>> text_emb = np.random.rand(384)
            >>> vision_emb = np.random.rand(128)
            >>> results = store.query_hybrid(
            ...     text_embedding=text_emb,
            ...     vision_embedding=vision_emb,
            ...     k=5,
            ...     text_weight=0.6,
            ...     vision_weight=0.4
            ... )
            >>> len(results["ids"])
            5
        """
        if text_embedding is None and vision_embedding is None:
            raise ValueError("At least one embedding (text or vision) must be provided")

        if text_weight < 0 or vision_weight < 0:
            raise ValueError("Weights must be non-negative")

        # Normalize weights
        total_weight = text_weight + vision_weight
        if total_weight == 0:
            raise ValueError("At least one weight must be positive")

        text_weight_norm = text_weight / total_weight
        vision_weight_norm = vision_weight / total_weight

        # Retrieve from each modality (2x k for better fusion coverage)
        retrieval_k = k * 2

        text_results = None
        vision_results = None

        if text_embedding is not None:
            text_results = self.query_text(text_embedding, k=retrieval_k, where_filter=where_filter)

        if vision_embedding is not None:
            vision_results = self.query_vision(
                vision_embedding, k=retrieval_k, where_filter=where_filter
            )

        # Merge results using RRF
        merged = self._merge_with_rrf(
            text_results, vision_results, text_weight_norm, vision_weight_norm, k
        )

        logger.debug(f"Hybrid query returned {len(merged['ids'])} results")
        return merged

    def _merge_with_rrf(
        self,
        text_results: dict[str, Any] | None,
        vision_results: dict[str, Any] | None,
        text_weight: float,
        vision_weight: float,
        k: int,
    ) -> dict[str, Any]:
        """
        Merge text and vision results using Reciprocal Rank Fusion (RRF).

        RRF formula: score(item) = Σ(weight / (k_constant + rank))

        Args:
            text_results: Text query results
            vision_results: Vision query results
            text_weight: Normalised text weight
            vision_weight: Normalised vision weight
            k: Number of final results to return

        Returns:
            Merged results with RRF scores
        """
        RRF_K = 60  # Standard RRF constant

        # Collect all unique document IDs with their RRF scores
        doc_scores: dict[str, float] = {}
        doc_metadata: dict[str, dict[str, Any]] = {}
        doc_distance: dict[str, float] = {}
        doc_document: dict[str, str] = {}

        # Process text results
        if text_results and text_results["ids"] and len(text_results["ids"][0]) > 0:
            for rank, (doc_id, metadata, distance) in enumerate(
                zip(
                    text_results["ids"][0],
                    text_results["metadatas"][0],
                    text_results["distances"][0],
                )
            ):
                rrf_score = text_weight / (RRF_K + rank + 1)
                doc_scores[doc_id] = doc_scores.get(doc_id, 0.0) + rrf_score

                # Store metadata and distance (prefer first occurrence)
                if doc_id not in doc_metadata:
                    doc_metadata[doc_id] = metadata
                    doc_distance[doc_id] = distance

                # Store document text if available
                if text_results.get("documents") and text_results["documents"][0]:
                    doc_document[doc_id] = text_results["documents"][0][rank]

        # Process vision results
        if vision_results and vision_results["ids"] and len(vision_results["ids"][0]) > 0:
            for rank, (doc_id, metadata, distance) in enumerate(
                zip(
                    vision_results["ids"][0],
                    vision_results["metadatas"][0],
                    vision_results["distances"][0],
                )
            ):
                rrf_score = vision_weight / (RRF_K + rank + 1)
                doc_scores[doc_id] = doc_scores.get(doc_id, 0.0) + rrf_score

                # Store metadata and distance (prefer first occurrence)
                if doc_id not in doc_metadata:
                    doc_metadata[doc_id] = metadata
                    doc_distance[doc_id] = distance

        # Sort by RRF score (descending) and take top k
        sorted_docs = sorted(doc_scores.items(), key=lambda x: x[1], reverse=True)[:k]

        # Build result structure matching ChromaDB format
        result_ids = [doc_id for doc_id, _ in sorted_docs]
        result_scores = [score for _, score in sorted_docs]
        result_metadatas = [doc_metadata[doc_id] for doc_id in result_ids]
        result_distances = [doc_distance[doc_id] for doc_id in result_ids]
        result_documents = [doc_document.get(doc_id, "") for doc_id in result_ids]

        return {
            "ids": [result_ids],  # Nested list to match ChromaDB format
            "distances": [result_distances],
            "metadatas": [result_metadatas],
            "documents": [result_documents],
            "rrf_scores": [result_scores],  # Additional field for debugging
        }
