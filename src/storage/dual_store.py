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
v0.5.7: Encryption at rest for GDPR compliance
"""
from __future__ import annotations


import base64
import logging
from pathlib import Path
from typing import Any

import chromadb
import numpy as np
from chromadb.api import ClientAPI

from ragged.security.encryption import get_encryption_manager
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
        enable_encryption: bool = True,
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
            enable_encryption: Enable encryption of sensitive metadata (GDPR compliance)

        Example:
            >>> store = DualEmbeddingStore()  # Default in-memory
            >>> store = DualEmbeddingStore(persist_directory=Path("~/.ragged/storage"))

        Security (v0.5.7):
            - Sensitive metadata (image_hash) encrypted with AES-256
            - Embeddings kept unencrypted for semantic search
            - GDPR Article 32 compliance for data at rest
        """
        self.collection_name = collection_name
        self.persist_directory = persist_directory
        self.enable_encryption = enable_encryption

        # Initialize encryption manager for metadata
        if self.enable_encryption:
            self.encryption_manager = get_encryption_manager()
            logger.info("Encryption enabled for sensitive metadata (GDPR compliance)")
        else:
            self.encryption_manager = None
            logger.warning(
                "Encryption DISABLED - sensitive metadata stored in plaintext. "
                "Enable encryption for GDPR compliance."
            )

        if client is not None:
            self.client = client
        else:
            if persist_directory:
                self.client = chromadb.PersistentClient(path=str(persist_directory))
            else:
                self.client = chromadb.Client()

        # Create separate collections for text and vision (different dimensions)
        self.text_collection = self.client.get_or_create_collection(
            name=f"{collection_name}_text",
            metadata={"schema_version": "v0.5.7", "embedding_type": "text", "encryption_enabled": str(enable_encryption)}
        )
        self.vision_collection = self.client.get_or_create_collection(
            name=f"{collection_name}_vision",
            metadata={"schema_version": "v0.5.7", "embedding_type": "vision", "encryption_enabled": str(enable_encryption)}
        )

        logger.info(
            f"Initialised DualEmbeddingStore with collections '{collection_name}_text' and '{collection_name}_vision'"
        )

    def _encrypt_metadata_field(self, value: str) -> str:
        """
        Encrypt a metadata field value.

        Args:
            value: Plaintext string to encrypt

        Returns:
            Base64-encoded encrypted value

        Security (v0.5.7):
            - Uses Fernet (AES-128 + HMAC)
            - Returns base64-encoded ciphertext (ChromaDB compatible)
        """
        if not self.enable_encryption or self.encryption_manager is None:
            return value

        # Encrypt and encode as base64 for ChromaDB string storage
        encrypted_bytes = self.encryption_manager.encrypt(value.encode('utf-8'))
        return base64.b64encode(encrypted_bytes).decode('ascii')

    def _decrypt_metadata_field(self, encrypted_value: str, is_encrypted: bool = True) -> str:
        """
        Decrypt a metadata field value.

        Args:
            encrypted_value: Base64-encoded encrypted value
            is_encrypted: Whether the value is actually encrypted

        Returns:
            Decrypted plaintext string

        Security (v0.5.7):
            - Verifies HMAC before decryption
            - Handles both encrypted and plaintext metadata (migration support)
        """
        if not is_encrypted or not self.enable_encryption or self.encryption_manager is None:
            return encrypted_value

        try:
            # Decode base64 and decrypt
            encrypted_bytes = base64.b64decode(encrypted_value.encode('ascii'))
            decrypted_bytes = self.encryption_manager.decrypt(encrypted_bytes)
            return decrypted_bytes.decode('utf-8')
        except Exception as e:
            logger.error(f"Decryption failed for metadata field: {e}")
            # Return as-is if decryption fails (legacy unencrypted data)
            return encrypted_value

    def _decrypt_vision_metadata(self, metadata: dict[str, Any]) -> dict[str, Any]:
        """
        Decrypt sensitive fields in vision metadata.

        Args:
            metadata: Vision metadata dictionary from ChromaDB

        Returns:
            Metadata dictionary with decrypted sensitive fields

        Security (v0.5.7):
            - Decrypts image_hash if encrypted flag is true
            - Preserves all other metadata fields
            - Handles legacy unencrypted metadata gracefully
        """
        if not metadata:
            return metadata

        # Check if metadata is encrypted
        is_encrypted = metadata.get("encrypted") == "true"

        if not is_encrypted:
            return metadata

        # Create copy to avoid modifying original
        decrypted = metadata.copy()

        # Decrypt sensitive fields
        if "image_hash" in decrypted:
            decrypted["image_hash"] = self._decrypt_metadata_field(
                decrypted["image_hash"], is_encrypted=True
            )

        return decrypted

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
            ValueError: If embedding dimension, shape, or values are invalid

        Example:
            >>> embedding = np.random.rand(384)
            >>> id = store.add_text_embedding(
            ...     "doc123", "chunk1", 0, embedding, "Sample text", page_number=0
            ... )
            >>> id
            'doc123_chunk_0_text'
        """
        # SECURITY FIX (CRITICAL-4): Enhanced embedding validation
        # Validate embedding is numpy array
        if not isinstance(embedding, np.ndarray):
            raise ValueError(f"Text embedding must be numpy array, got {type(embedding).__name__}")

        # Validate embedding shape (must be 1D)
        if embedding.ndim != 1:
            raise ValueError(f"Text embedding must be 1-dimensional, got {embedding.ndim}D array")

        # Validate embedding dimension
        if embedding.shape[0] != 384:
            raise ValueError(f"Text embedding must be 384-dimensional, got {embedding.shape[0]}")

        # SECURITY FIX (CRITICAL-4): Validate embedding values (no NaN, Inf)
        if not np.isfinite(embedding).all():
            nan_count = np.isnan(embedding).sum()
            inf_count = np.isinf(embedding).sum()
            raise ValueError(
                f"Text embedding contains invalid values: {nan_count} NaN, {inf_count} Inf. "
                f"This may indicate corruption or attack."
            )

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
            ValueError: If embedding dimension, shape, or values are invalid

        Example:
            >>> embedding = np.random.rand(128)
            >>> id = store.add_vision_embedding(
            ...     "doc123", 0, embedding, "abc123hash", has_diagrams=True
            ... )
            >>> id
            'doc123_page_0_vision'
        """
        # SECURITY FIX (CRITICAL-4): Enhanced embedding validation
        # Validate embedding is numpy array
        if not isinstance(embedding, np.ndarray):
            raise ValueError(
                f"Vision embedding must be numpy array, got {type(embedding).__name__}"
            )

        # Validate embedding shape (must be 1D)
        if embedding.ndim != 1:
            raise ValueError(
                f"Vision embedding must be 1-dimensional, got {embedding.ndim}D array"
            )

        # Validate embedding dimension
        if embedding.shape[0] != 128:
            raise ValueError(f"Vision embedding must be 128-dimensional, got {embedding.shape[0]}")

        # SECURITY FIX (CRITICAL-4): Validate embedding values (no NaN, Inf)
        if not np.isfinite(embedding).all():
            nan_count = np.isnan(embedding).sum()
            inf_count = np.isinf(embedding).sum()
            raise ValueError(
                f"Vision embedding contains invalid values: {nan_count} NaN, {inf_count} Inf. "
                f"This may indicate corruption or attack."
            )

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

        # SECURITY FIX (v0.5.7 CRITICAL-1): Encrypt sensitive metadata (image_hash)
        if self.enable_encryption:
            # Encrypt image_hash (contains SHA-256 hash of page image)
            if "image_hash" in metadata_filtered:
                metadata_filtered["image_hash"] = self._encrypt_metadata_field(
                    metadata_filtered["image_hash"]
                )
            # Mark metadata as encrypted for decryption on retrieval
            metadata_filtered["encrypted"] = "true"
            logger.debug(f"Encrypted sensitive metadata for {embedding_id}")
        else:
            metadata_filtered["encrypted"] = "false"

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
            Query results with IDs, distances, metadatas (decrypted)

        Raises:
            ValueError: If query embedding dimension incorrect

        Example:
            >>> query = np.random.rand(128)
            >>> results = store.query_vision(query, k=5)
            >>> len(results["ids"][0])
            5

        Security (v0.5.7):
            - Automatically decrypts encrypted metadata fields
            - Transparent encryption/decryption for backward compatibility
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

        # SECURITY FIX (v0.5.7 CRITICAL-1): Decrypt encrypted metadata
        if results.get("metadatas") and len(results["metadatas"]) > 0:
            decrypted_metadatas = []
            for metadata in results["metadatas"][0]:
                decrypted = self._decrypt_vision_metadata(metadata)
                decrypted_metadatas.append(decrypted)
            results["metadatas"] = [decrypted_metadatas]

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
            Dictionary with embeddings, metadatas (decrypted), and IDs

        Example:
            >>> results = store.get_by_document("doc123")
            >>> len(results["ids"])  # Both text and vision
            25
            >>> results_text = store.get_by_document("doc123", EmbeddingType.TEXT)
            >>> len(results_text["ids"])  # Only text
            20

        Security (v0.5.7):
            - Automatically decrypts vision metadata
            - Transparent for backward compatibility
        """
        where_filter = {"document_id": document_id}

        if embedding_type == EmbeddingType.TEXT:
            results = self.text_collection.get(where=where_filter, include=["embeddings", "metadatas"])
        elif embedding_type == EmbeddingType.VISION:
            results = self.vision_collection.get(where=where_filter, include=["embeddings", "metadatas"])
            # SECURITY FIX (v0.5.7 CRITICAL-1): Decrypt vision metadata
            if results.get("metadatas"):
                results["metadatas"] = [
                    self._decrypt_vision_metadata(m) for m in results["metadatas"]
                ]
        else:
            # Get from both collections and merge
            text_results = self.text_collection.get(where=where_filter, include=["embeddings", "metadatas"])
            vision_results = self.vision_collection.get(where=where_filter, include=["embeddings", "metadatas"])

            # SECURITY FIX (v0.5.7 CRITICAL-1): Decrypt vision metadata
            if vision_results.get("metadatas"):
                vision_results["metadatas"] = [
                    self._decrypt_vision_metadata(m) for m in vision_results["metadatas"]
                ]

            # Merge results - handle different embedding dimensions (text: 384, vision: 128)
            # Explicitly convert to lists to avoid numpy broadcasting issues
            text_embeddings = text_results.get("embeddings")
            vision_embeddings = vision_results.get("embeddings")

            # Convert None or numpy arrays to lists
            if text_embeddings is None:
                text_embeddings = []
            elif hasattr(text_embeddings, 'tolist'):
                text_embeddings = text_embeddings.tolist()

            if vision_embeddings is None:
                vision_embeddings = []
            elif hasattr(vision_embeddings, 'tolist'):
                vision_embeddings = vision_embeddings.tolist()

            results = {
                "ids": text_results["ids"] + vision_results["ids"],
                "embeddings": list(text_embeddings) + list(vision_embeddings),
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

        # SECURITY FIX (CRITICAL-6): Maximum rank to prevent integer overflow
        MAX_RANK = 10_000  # Reasonable upper bound for retrieval results

        # Process text results
        if text_results and text_results["ids"] and len(text_results["ids"][0]) > 0:
            for rank, (doc_id, metadata, distance) in enumerate(
                zip(
                    text_results["ids"][0],
                    text_results["metadatas"][0],
                    text_results["distances"][0],
                )
            ):
                # SECURITY FIX (CRITICAL-6): Validate rank is within safe bounds
                if rank < 0 or rank > MAX_RANK:
                    logger.warning(
                        f"Rank {rank} out of bounds [0, {MAX_RANK}], skipping result"
                    )
                    continue

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
                # SECURITY FIX (CRITICAL-6): Validate rank is within safe bounds
                if rank < 0 or rank > MAX_RANK:
                    logger.warning(
                        f"Rank {rank} out of bounds [0, {MAX_RANK}], skipping result"
                    )
                    continue

                rrf_score = vision_weight / (RRF_K + rank + 1)
                doc_scores[doc_id] = doc_scores.get(doc_id, 0.0) + rrf_score

                # SECURITY FIX (v0.5.7 CRITICAL-1): Decrypt vision metadata
                # Note: Vision metadata should already be decrypted by query_vision(),
                # but decrypt here for safety in case called with raw results
                decrypted_metadata = self._decrypt_vision_metadata(metadata)

                # Store metadata and distance (prefer first occurrence)
                if doc_id not in doc_metadata:
                    doc_metadata[doc_id] = decrypted_metadata
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

    def count_vision_embeddings(self) -> int:
        """
        Count total vision embeddings in storage.

        Returns:
            Number of vision embeddings

        Example:
            >>> count = store.count_vision_embeddings()
            >>> count
            42
        """
        return self.vision_collection.count()

    def get_all_vision_documents(self) -> dict[str, Any]:
        """
        Retrieve all vision embeddings.

        Returns:
            Dictionary with all vision embeddings, metadatas (decrypted), and IDs

        Example:
            >>> results = store.get_all_vision_documents()
            >>> len(results["ids"])
            42

        Security (v0.5.7):
            - Automatically decrypts all vision metadata
            - Transparent for backward compatibility
        """
        results = self.vision_collection.get(include=["metadatas", "embeddings"])

        # SECURITY FIX (v0.5.7 CRITICAL-1): Decrypt vision metadata
        if results.get("metadatas"):
            results["metadatas"] = [
                self._decrypt_vision_metadata(m) for m in results["metadatas"]
            ]

        return results

    def delete_vision_embeddings(self, ids: list[str]) -> int:
        """
        Delete specific vision embeddings by ID.

        Args:
            ids: List of embedding IDs to delete

        Returns:
            Number of embeddings deleted

        Example:
            >>> deleted = store.delete_vision_embeddings(["id1", "id2"])
            >>> deleted
            2
        """
        if not ids:
            return 0

        self.vision_collection.delete(ids=ids)
        return len(ids)
