# VISION-002: Dual Embedding Storage

**Feature:** Dual Text+Vision Vector Storage
**Category:** Storage Infrastructure
**Estimated Effort:** 25-35 hours
**Dependencies:** VISION-001 (ColPali Integration)
**Status:** Planned

---

## Overview

Extend ragged's vector storage to simultaneously store and manage both text embeddings (384-dimensional from all-MiniLM-L6-v2) and vision embeddings (768-dimensional from ColPali). This dual-storage architecture enables multi-modal retrieval whilst maintaining backward compatibility with existing text-only workflows.

**Key Design Principles:**
1. **Parallel Storage:** Text and vision embeddings stored side-by-side with shared metadata
2. **Type Transparency:** Embedding type explicitly tracked in metadata
3. **Flexible Retrieval:** Support text-only, vision-only, or hybrid retrieval modes
4. **Schema Evolution:** Graceful handling of documents with only text or only vision embeddings

---

## Architecture

### Current State (v0.4.x)

```python
# Text-only storage
collection = chromadb.get_collection("documents")
collection.add(
    embeddings=[text_embedding],  # 384-dim
    metadatas=[{"chunk_id": "...", "page": 1}],
    ids=["doc_chunk_1"]
)
```

### Target State (v0.5.0)

```python
# Dual embedding storage
collection = chromadb.get_collection("documents")
collection.add(
    embeddings=[
        text_embedding,    # 384-dim
        vision_embedding   # 768-dim
    ],
    metadatas=[
        {"chunk_id": "...", "page": 1, "embedding_type": "text"},
        {"chunk_id": "...", "page": 1, "embedding_type": "vision"}
    ],
    ids=["doc_chunk_1_text", "doc_chunk_1_vision"]
)
```

### Storage Schema

**Embedding ID Format:**
- Text: `{document_id}_chunk_{n}_text`
- Vision: `{document_id}_page_{n}_vision`

**Metadata Schema:**
```python
{
    # Common fields (both types)
    "document_id": str,        # Parent document UUID
    "embedding_type": str,     # "text" | "vision"
    "created_at": str,         # ISO 8601 timestamp

    # Text embedding fields
    "chunk_id": str,           # Chunk identifier
    "chunk_index": int,        # Position in document
    "parent_chunk_id": str,    # For hierarchical chunking

    # Vision embedding fields
    "page_number": int,        # PDF page number (1-indexed)
    "image_hash": str,         # SHA-256 of rendered page image
    "has_diagrams": bool,      # Visual content detection
    "has_tables": bool,        # Table detection
    "layout_complexity": str   # "simple" | "moderate" | "complex"
}
```

---

## Implementation Plan

### Phase 1: Schema Extension (6-8 hours)

#### Session 1.1: ChromaDB Collection Schema (3-4h)

**Task:** Design and implement dual-embedding collection schema

**Implementation:**

```python
# src/storage/schema.py

from enum import Enum
from typing import TypedDict, Optional
from datetime import datetime


class EmbeddingType(str, Enum):
    """Embedding type enumeration."""
    TEXT = "text"
    VISION = "vision"


class BaseMetadata(TypedDict):
    """Base metadata for all embeddings."""
    document_id: str
    embedding_type: str  # EmbeddingType value
    created_at: str      # ISO 8601


class TextMetadata(BaseMetadata):
    """Metadata for text embeddings."""
    chunk_id: str
    chunk_index: int
    parent_chunk_id: Optional[str]
    text_content: str
    char_count: int


class VisionMetadata(BaseMetadata):
    """Metadata for vision embeddings."""
    page_number: int
    image_hash: str
    has_diagrams: bool
    has_tables: bool
    layout_complexity: str  # "simple" | "moderate" | "complex"
    ocr_confidence: Optional[float]


def generate_embedding_id(
    document_id: str,
    embedding_type: EmbeddingType,
    index: int
) -> str:
    """
    Generate unique embedding identifier.

    Args:
        document_id: Parent document UUID
        embedding_type: Type of embedding
        index: Chunk index (text) or page number (vision)

    Returns:
        Unique embedding ID in format:
        - Text: "{doc_id}_chunk_{index}_text"
        - Vision: "{doc_id}_page_{index}_vision"

    Examples:
        >>> generate_embedding_id("abc123", EmbeddingType.TEXT, 5)
        "abc123_chunk_5_text"
        >>> generate_embedding_id("abc123", EmbeddingType.VISION, 3)
        "abc123_page_3_vision"
    """
    if embedding_type == EmbeddingType.TEXT:
        return f"{document_id}_chunk_{index}_text"
    else:
        return f"{document_id}_page_{index}_vision"


def create_text_metadata(
    document_id: str,
    chunk_id: str,
    chunk_index: int,
    text_content: str,
    parent_chunk_id: Optional[str] = None
) -> TextMetadata:
    """
    Create metadata for text embedding.

    Args:
        document_id: Parent document UUID
        chunk_id: Unique chunk identifier
        chunk_index: Position in document (0-indexed)
        text_content: Actual text content
        parent_chunk_id: Parent chunk for hierarchical chunking

    Returns:
        Complete text metadata dictionary
    """
    return TextMetadata(
        document_id=document_id,
        embedding_type=EmbeddingType.TEXT.value,
        created_at=datetime.utcnow().isoformat(),
        chunk_id=chunk_id,
        chunk_index=chunk_index,
        parent_chunk_id=parent_chunk_id,
        text_content=text_content,
        char_count=len(text_content)
    )


def create_vision_metadata(
    document_id: str,
    page_number: int,
    image_hash: str,
    has_diagrams: bool = False,
    has_tables: bool = False,
    layout_complexity: str = "simple",
    ocr_confidence: Optional[float] = None
) -> VisionMetadata:
    """
    Create metadata for vision embedding.

    Args:
        document_id: Parent document UUID
        page_number: PDF page number (1-indexed)
        image_hash: SHA-256 hash of rendered page image
        has_diagrams: Whether page contains diagrams/charts
        has_tables: Whether page contains tables
        layout_complexity: Layout complexity assessment
        ocr_confidence: OCR confidence if applicable

    Returns:
        Complete vision metadata dictionary
    """
    return VisionMetadata(
        document_id=document_id,
        embedding_type=EmbeddingType.VISION.value,
        created_at=datetime.utcnow().isoformat(),
        page_number=page_number,
        image_hash=image_hash,
        has_diagrams=has_diagrams,
        has_tables=has_tables,
        layout_complexity=layout_complexity,
        ocr_confidence=ocr_confidence
    )
```

**Deliverables:**
- `src/storage/schema.py` (~150 lines)
- Type-safe metadata schemas
- ID generation utilities

**Time:** 3-4 hours

---

#### Session 1.2: Migration Utilities (3-4h)

**Task:** Create utilities for migrating existing text-only collections

**Implementation:**

```python
# src/storage/migration.py

from pathlib import Path
from typing import Dict, List, Optional
import chromadb
from chromadb.api import ClientAPI
from loguru import logger

from ragged.storage.schema import EmbeddingType


class StorageMigration:
    """Utilities for migrating text-only storage to dual-embedding schema."""

    def __init__(self, client: ClientAPI):
        """
        Initialise migration utilities.

        Args:
            client: ChromaDB client instance
        """
        self.client = client

    def detect_schema_version(self, collection_name: str) -> str:
        """
        Detect schema version of existing collection.

        Args:
            collection_name: Name of collection to inspect

        Returns:
            Schema version: "v0.4" (text-only) or "v0.5" (dual-embedding)

        Raises:
            ValueError: If collection doesn't exist
        """
        try:
            collection = self.client.get_collection(collection_name)
        except Exception:
            raise ValueError(f"Collection '{collection_name}' not found")

        # Check if any embeddings have embedding_type metadata
        results = collection.peek(limit=10)

        if not results["metadatas"]:
            return "v0.4"  # Empty collection

        # Check first metadata for embedding_type field
        first_metadata = results["metadatas"][0]
        if "embedding_type" in first_metadata:
            return "v0.5"
        else:
            return "v0.4"

    def migrate_collection(
        self,
        collection_name: str,
        batch_size: int = 100,
        dry_run: bool = False
    ) -> Dict[str, int]:
        """
        Migrate v0.4 collection to v0.5 dual-embedding schema.

        This migration:
        1. Adds "embedding_type": "text" to all existing metadata
        2. Renames IDs from "{doc_id}_chunk_{n}" to "{doc_id}_chunk_{n}_text"
        3. Preserves all existing embeddings and metadata

        Args:
            collection_name: Name of collection to migrate
            batch_size: Number of embeddings to process per batch
            dry_run: If True, only report changes without applying

        Returns:
            Migration statistics:
            {
                "embeddings_migrated": int,
                "ids_renamed": int,
                "metadata_updated": int
            }

        Raises:
            ValueError: If collection is already v0.5 or migration fails
        """
        schema_version = self.detect_schema_version(collection_name)

        if schema_version == "v0.5":
            raise ValueError(
                f"Collection '{collection_name}' is already v0.5 schema"
            )

        logger.info(
            f"Starting migration of '{collection_name}' "
            f"(dry_run={dry_run})"
        )

        collection = self.client.get_collection(collection_name)

        # Get all embeddings in batches
        offset = 0
        total_migrated = 0

        stats = {
            "embeddings_migrated": 0,
            "ids_renamed": 0,
            "metadata_updated": 0
        }

        while True:
            results = collection.get(
                limit=batch_size,
                offset=offset,
                include=["embeddings", "metadatas"]
            )

            if not results["ids"]:
                break  # No more embeddings

            # Migrate batch
            migrated_ids = []
            migrated_embeddings = []
            migrated_metadatas = []

            for i, old_id in enumerate(results["ids"]):
                # Rename ID: "doc_chunk_5" → "doc_chunk_5_text"
                if not old_id.endswith("_text"):
                    new_id = f"{old_id}_text"
                    stats["ids_renamed"] += 1
                else:
                    new_id = old_id

                migrated_ids.append(new_id)
                migrated_embeddings.append(results["embeddings"][i])

                # Add embedding_type to metadata
                metadata = results["metadatas"][i].copy()
                if "embedding_type" not in metadata:
                    metadata["embedding_type"] = EmbeddingType.TEXT.value
                    stats["metadata_updated"] += 1

                migrated_metadatas.append(metadata)

            if not dry_run:
                # Delete old embeddings
                collection.delete(ids=results["ids"])

                # Add migrated embeddings with new IDs
                collection.add(
                    ids=migrated_ids,
                    embeddings=migrated_embeddings,
                    metadatas=migrated_metadatas
                )

            stats["embeddings_migrated"] += len(results["ids"])
            offset += batch_size

            logger.info(
                f"Migrated {stats['embeddings_migrated']} embeddings..."
            )

        logger.info(
            f"Migration complete: {stats['embeddings_migrated']} embeddings, "
            f"{stats['ids_renamed']} IDs renamed, "
            f"{stats['metadata_updated']} metadata updated"
        )

        return stats
```

**Deliverables:**
- `src/storage/migration.py` (~200 lines)
- Schema version detection
- Safe migration with dry-run support

**Time:** 3-4 hours

---

### Phase 2: VisionVectorStore Implementation (8-10 hours)

#### Session 2.1: DualEmbeddingStore Class (4-5h)

**Task:** Implement wrapper for dual text+vision storage

**Implementation:**

```python
# src/storage/dual_store.py

from pathlib import Path
from typing import List, Dict, Optional, Tuple
import numpy as np
import chromadb
from chromadb.api import ClientAPI
from loguru import logger

from ragged.storage.schema import (
    EmbeddingType,
    TextMetadata,
    VisionMetadata,
    generate_embedding_id,
    create_text_metadata,
    create_vision_metadata
)


class DualEmbeddingStore:
    """
    Storage manager for dual text+vision embeddings.

    Handles simultaneous storage and retrieval of:
    - Text embeddings (384-dimensional from all-MiniLM-L6-v2)
    - Vision embeddings (768-dimensional from ColPali)

    Both embedding types share common metadata (document_id, created_at)
    but have type-specific fields for their respective use cases.
    """

    def __init__(
        self,
        collection_name: str = "documents",
        persist_directory: Optional[Path] = None,
        client: Optional[ClientAPI] = None
    ):
        """
        Initialise dual embedding storage.

        Args:
            collection_name: ChromaDB collection name
            persist_directory: Directory for persistent storage
            client: Existing ChromaDB client (or None to create)
        """
        self.collection_name = collection_name

        if client is not None:
            self.client = client
        else:
            if persist_directory:
                self.client = chromadb.PersistentClient(
                    path=str(persist_directory)
                )
            else:
                self.client = chromadb.Client()

        # Get or create collection
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"schema_version": "v0.5"}
        )

        logger.info(
            f"Initialised DualEmbeddingStore with collection "
            f"'{collection_name}'"
        )

    def add_text_embedding(
        self,
        document_id: str,
        chunk_id: str,
        chunk_index: int,
        embedding: np.ndarray,
        text_content: str,
        parent_chunk_id: Optional[str] = None
    ) -> str:
        """
        Add text embedding to storage.

        Args:
            document_id: Parent document UUID
            chunk_id: Unique chunk identifier
            chunk_index: Position in document (0-indexed)
            embedding: 384-dimensional text embedding
            text_content: Actual text content
            parent_chunk_id: Parent chunk for hierarchical chunking

        Returns:
            Generated embedding ID

        Raises:
            ValueError: If embedding dimension incorrect
        """
        if embedding.shape[0] != 384:
            raise ValueError(
                f"Text embedding must be 384-dimensional, "
                f"got {embedding.shape[0]}"
            )

        embedding_id = generate_embedding_id(
            document_id, EmbeddingType.TEXT, chunk_index
        )

        metadata = create_text_metadata(
            document_id=document_id,
            chunk_id=chunk_id,
            chunk_index=chunk_index,
            text_content=text_content,
            parent_chunk_id=parent_chunk_id
        )

        self.collection.add(
            ids=[embedding_id],
            embeddings=[embedding.tolist()],
            metadatas=[metadata]
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
        ocr_confidence: Optional[float] = None
    ) -> str:
        """
        Add vision embedding to storage.

        Args:
            document_id: Parent document UUID
            page_number: PDF page number (1-indexed)
            embedding: 768-dimensional vision embedding
            image_hash: SHA-256 hash of rendered page image
            has_diagrams: Whether page contains diagrams/charts
            has_tables: Whether page contains tables
            layout_complexity: Layout complexity assessment
            ocr_confidence: OCR confidence if applicable

        Returns:
            Generated embedding ID

        Raises:
            ValueError: If embedding dimension incorrect
        """
        if embedding.shape[0] != 768:
            raise ValueError(
                f"Vision embedding must be 768-dimensional, "
                f"got {embedding.shape[0]}"
            )

        embedding_id = generate_embedding_id(
            document_id, EmbeddingType.VISION, page_number
        )

        metadata = create_vision_metadata(
            document_id=document_id,
            page_number=page_number,
            image_hash=image_hash,
            has_diagrams=has_diagrams,
            has_tables=has_tables,
            layout_complexity=layout_complexity,
            ocr_confidence=ocr_confidence
        )

        self.collection.add(
            ids=[embedding_id],
            embeddings=[embedding.tolist()],
            metadatas=[metadata]
        )

        logger.debug(f"Added vision embedding: {embedding_id}")
        return embedding_id

    def add_batch(
        self,
        text_embeddings: Optional[List[Tuple[str, int, np.ndarray, str]]] = None,
        vision_embeddings: Optional[List[Tuple[str, int, np.ndarray, str]]] = None
    ) -> Dict[str, List[str]]:
        """
        Add batch of text and/or vision embeddings.

        Args:
            text_embeddings: List of (doc_id, chunk_idx, embedding, text)
            vision_embeddings: List of (doc_id, page_num, embedding, hash)

        Returns:
            Dictionary with added IDs:
            {
                "text_ids": List[str],
                "vision_ids": List[str]
            }
        """
        added_ids = {"text_ids": [], "vision_ids": []}

        # Add text embeddings in batch
        if text_embeddings:
            text_ids = []
            text_embeds = []
            text_metas = []

            for doc_id, chunk_idx, embedding, text in text_embeddings:
                embedding_id = generate_embedding_id(
                    doc_id, EmbeddingType.TEXT, chunk_idx
                )
                metadata = create_text_metadata(
                    document_id=doc_id,
                    chunk_id=f"{doc_id}_chunk_{chunk_idx}",
                    chunk_index=chunk_idx,
                    text_content=text
                )

                text_ids.append(embedding_id)
                text_embeds.append(embedding.tolist())
                text_metas.append(metadata)

            self.collection.add(
                ids=text_ids,
                embeddings=text_embeds,
                metadatas=text_metas
            )

            added_ids["text_ids"] = text_ids
            logger.info(f"Added {len(text_ids)} text embeddings")

        # Add vision embeddings in batch
        if vision_embeddings:
            vision_ids = []
            vision_embeds = []
            vision_metas = []

            for doc_id, page_num, embedding, img_hash in vision_embeddings:
                embedding_id = generate_embedding_id(
                    doc_id, EmbeddingType.VISION, page_num
                )
                metadata = create_vision_metadata(
                    document_id=doc_id,
                    page_number=page_num,
                    image_hash=img_hash
                )

                vision_ids.append(embedding_id)
                vision_embeds.append(embedding.tolist())
                vision_metas.append(metadata)

            self.collection.add(
                ids=vision_ids,
                embeddings=vision_embeds,
                metadatas=vision_metas
            )

            added_ids["vision_ids"] = vision_ids
            logger.info(f"Added {len(vision_ids)} vision embeddings")

        return added_ids

    def get_by_document(
        self,
        document_id: str,
        embedding_type: Optional[EmbeddingType] = None
    ) -> Dict[str, List]:
        """
        Retrieve all embeddings for a document.

        Args:
            document_id: Document UUID
            embedding_type: Filter by type (None = both types)

        Returns:
            Dictionary with embeddings, metadatas, and IDs
        """
        # Build filter
        where_filter = {"document_id": document_id}
        if embedding_type:
            where_filter["embedding_type"] = embedding_type.value

        results = self.collection.get(
            where=where_filter,
            include=["embeddings", "metadatas"]
        )

        logger.debug(
            f"Retrieved {len(results['ids'])} embeddings "
            f"for document {document_id}"
        )

        return results

    def delete_document(self, document_id: str) -> int:
        """
        Delete all embeddings for a document.

        Args:
            document_id: Document UUID

        Returns:
            Number of embeddings deleted
        """
        results = self.get_by_document(document_id)

        if results["ids"]:
            self.collection.delete(ids=results["ids"])
            logger.info(
                f"Deleted {len(results['ids'])} embeddings "
                f"for document {document_id}"
            )

        return len(results["ids"])
```

**Deliverables:**
- `src/storage/dual_store.py` (~350 lines)
- Type-safe dual storage operations
- Batch processing support

**Time:** 4-5 hours

---

#### Session 2.2: Query Interface (4-5h)

**Task:** Implement retrieval methods for dual embeddings

**Implementation:**

```python
# Extend src/storage/dual_store.py

class DualEmbeddingStore:
    # ... (previous methods) ...

    def query_text(
        self,
        query_embedding: np.ndarray,
        n_results: int = 10,
        where_filter: Optional[Dict] = None
    ) -> Dict[str, List]:
        """
        Query using text embedding.

        Args:
            query_embedding: 384-dimensional query embedding
            n_results: Number of results to return
            where_filter: Additional metadata filters

        Returns:
            Query results with IDs, distances, metadatas
        """
        if query_embedding.shape[0] != 384:
            raise ValueError(
                f"Text query must be 384-dimensional, "
                f"got {query_embedding.shape[0]}"
            )

        # Filter to text embeddings only
        where = {"embedding_type": EmbeddingType.TEXT.value}
        if where_filter:
            where.update(where_filter)

        results = self.collection.query(
            query_embeddings=[query_embedding.tolist()],
            n_results=n_results,
            where=where,
            include=["metadatas", "distances", "documents"]
        )

        logger.debug(f"Text query returned {len(results['ids'][0])} results")
        return results

    def query_vision(
        self,
        query_embedding: np.ndarray,
        n_results: int = 10,
        where_filter: Optional[Dict] = None
    ) -> Dict[str, List]:
        """
        Query using vision embedding.

        Args:
            query_embedding: 768-dimensional query embedding
            n_results: Number of results to return
            where_filter: Additional metadata filters

        Returns:
            Query results with IDs, distances, metadatas
        """
        if query_embedding.shape[0] != 768:
            raise ValueError(
                f"Vision query must be 768-dimensional, "
                f"got {query_embedding.shape[0]}"
            )

        # Filter to vision embeddings only
        where = {"embedding_type": EmbeddingType.VISION.value}
        if where_filter:
            where.update(where_filter)

        results = self.collection.query(
            query_embeddings=[query_embedding.tolist()],
            n_results=n_results,
            where=where,
            include=["metadatas", "distances"]
        )

        logger.debug(f"Vision query returned {len(results['ids'][0])} results")
        return results

    def query_hybrid(
        self,
        text_embedding: np.ndarray,
        vision_embedding: np.ndarray,
        n_results: int = 10,
        text_weight: float = 0.5,
        vision_weight: float = 0.5,
        where_filter: Optional[Dict] = None
    ) -> Dict[str, List]:
        """
        Hybrid query using both text and vision embeddings.

        Retrieves top-k from both embedding types and merges results
        using weighted score fusion.

        Args:
            text_embedding: 384-dimensional text query
            vision_embedding: 768-dimensional vision query
            n_results: Total number of results to return
            text_weight: Weight for text scores (0-1)
            vision_weight: Weight for vision scores (0-1)
            where_filter: Additional metadata filters

        Returns:
            Merged and re-ranked results
        """
        # Query both embedding types
        text_results = self.query_text(
            text_embedding, n_results * 2, where_filter
        )
        vision_results = self.query_vision(
            vision_embedding, n_results * 2, where_filter
        )

        # Merge and re-rank using weighted scores
        # (Implementation of reciprocal rank fusion or score fusion)
        merged = self._merge_hybrid_results(
            text_results, vision_results,
            text_weight, vision_weight,
            n_results
        )

        logger.debug(
            f"Hybrid query returned {len(merged['ids'])} results "
            f"(text_weight={text_weight}, vision_weight={vision_weight})"
        )

        return merged

    def _merge_hybrid_results(
        self,
        text_results: Dict,
        vision_results: Dict,
        text_weight: float,
        vision_weight: float,
        n_results: int
    ) -> Dict[str, List]:
        """
        Merge text and vision results using weighted score fusion.

        Uses reciprocal rank fusion (RRF) with configurable weights:
        score(doc) = text_weight * (1 / (k + rank_text)) +
                     vision_weight * (1 / (k + rank_vision))

        where k=60 (standard RRF constant)
        """
        k = 60  # RRF constant
        doc_scores = {}

        # Score text results
        for i, doc_id in enumerate(text_results["ids"][0]):
            # Extract document_id from embedding_id
            document_id = text_results["metadatas"][0][i]["document_id"]
            doc_scores[document_id] = text_weight * (1 / (k + i + 1))

        # Score vision results
        for i, doc_id in enumerate(vision_results["ids"][0]):
            document_id = vision_results["metadatas"][0][i]["document_id"]
            vision_score = vision_weight * (1 / (k + i + 1))

            if document_id in doc_scores:
                doc_scores[document_id] += vision_score
            else:
                doc_scores[document_id] = vision_score

        # Sort by combined score
        ranked_docs = sorted(
            doc_scores.items(), key=lambda x: x[1], reverse=True
        )[:n_results]

        # Construct result format
        merged = {
            "ids": [[doc_id for doc_id, _ in ranked_docs]],
            "scores": [[score for _, score in ranked_docs]],
            "metadatas": [[]]  # Populate from original results
        }

        return merged
```

**Deliverables:**
- Query methods for text, vision, and hybrid retrieval
- Reciprocal rank fusion for hybrid queries
- Type-safe query validation

**Time:** 4-5 hours

---

### Phase 3: Integration with Ingestion Pipeline (6-8 hours)

#### Session 3.1: Update Document Processor (3-4h)

**Task:** Integrate dual storage into document ingestion

**Implementation:**

```python
# src/ingestion/processor.py (modifications)

from ragged.storage.dual_store import DualEmbeddingStore
from ragged.embeddings.colpali_embedder import ColPaliEmbedder
from ragged.embeddings.text_embedder import TextEmbedder


class DocumentProcessor:
    """Process documents and store dual text+vision embeddings."""

    def __init__(
        self,
        text_embedder: Optional[TextEmbedder] = None,
        vision_embedder: Optional[ColPaliEmbedder] = None,
        store: Optional[DualEmbeddingStore] = None
    ):
        """
        Initialise document processor.

        Args:
            text_embedder: Text embedding model
            vision_embedder: Vision embedding model (optional)
            store: Dual embedding storage
        """
        self.text_embedder = text_embedder or TextEmbedder()
        self.vision_embedder = vision_embedder
        self.store = store or DualEmbeddingStore()

    def process_document(
        self,
        document_path: Path,
        enable_vision: bool = True
    ) -> str:
        """
        Process document with dual text+vision embeddings.

        Args:
            document_path: Path to PDF document
            enable_vision: Whether to generate vision embeddings

        Returns:
            Document UUID
        """
        document_id = str(uuid.uuid4())

        # Extract text and generate text embeddings
        text_chunks = self._extract_text_chunks(document_path)
        text_batch = []

        for i, chunk in enumerate(text_chunks):
            embedding = self.text_embedder.embed(chunk.text)
            text_batch.append(
                (document_id, i, embedding, chunk.text)
            )

        # Generate vision embeddings if enabled
        vision_batch = None
        if enable_vision and self.vision_embedder:
            vision_embeddings, page_numbers = \
                self.vision_embedder.embed_document(document_path)

            vision_batch = []
            for page_num, embedding in zip(page_numbers, vision_embeddings):
                img_hash = self._compute_page_hash(
                    document_path, page_num
                )
                vision_batch.append(
                    (document_id, page_num, embedding, img_hash)
                )

        # Store in batch
        self.store.add_batch(
            text_embeddings=text_batch,
            vision_embeddings=vision_batch
        )

        logger.info(
            f"Processed document {document_id}: "
            f"{len(text_batch)} text, {len(vision_batch or [])} vision"
        )

        return document_id
```

**Deliverables:**
- Updated `DocumentProcessor` with dual storage
- Configurable vision embedding generation
- Batch processing for efficiency

**Time:** 3-4 hours

---

#### Session 3.2: CLI and Configuration Updates (3-4h)

**Task:** Update CLI and configuration for dual storage

**Implementation:**

```python
# src/config/settings.py (additions)

class StorageConfig(BaseSettings):
    """Storage configuration."""

    # Existing text embedding settings
    text_embedding_model: str = "all-MiniLM-L6-v2"
    text_embedding_dim: int = 384

    # New vision embedding settings
    enable_vision_embeddings: bool = False
    vision_embedding_model: str = "vidore/colpali"
    vision_embedding_dim: int = 768

    # Storage settings
    collection_name: str = "documents"
    persist_directory: Path = Path.home() / ".ragged" / "storage"

    # Hybrid retrieval settings
    default_text_weight: float = 0.5
    default_vision_weight: float = 0.5
```

```python
# src/cli.py (additions)

@click.command()
@click.argument("document_path", type=click.Path(exists=True))
@click.option(
    "--vision/--no-vision",
    default=False,
    help="Enable vision embeddings (requires GPU)"
)
@click.option(
    "--gpu-device",
    type=click.Choice(["cuda", "mps", "cpu"]),
    default=None,
    help="GPU device for vision embeddings"
)
def ingest(document_path: str, vision: bool, gpu_device: Optional[str]):
    """Ingest document with optional vision embeddings."""

    # Initialise embedders
    text_embedder = TextEmbedder()

    vision_embedder = None
    if vision:
        vision_embedder = ColPaliEmbedder(device=gpu_device)

    # Initialise storage
    store = DualEmbeddingStore()

    # Process document
    processor = DocumentProcessor(
        text_embedder=text_embedder,
        vision_embedder=vision_embedder,
        store=store
    )

    doc_id = processor.process_document(
        Path(document_path),
        enable_vision=vision
    )

    click.echo(f"Ingested document: {doc_id}")
```

**Deliverables:**
- Configuration options for dual storage
- CLI flags for vision embedding control
- GPU device selection

**Time:** 3-4 hours

---

### Phase 4: Testing (4-6 hours)

#### Session 4.1: Unit Tests (2-3h)

**Test Coverage:**
1. Schema validation and ID generation
2. Metadata creation (text and vision)
3. DualEmbeddingStore add/query operations
4. Migration utilities
5. Batch processing

**Example Tests:**

```python
# tests/storage/test_dual_store.py

import numpy as np
import pytest
from ragged.storage.dual_store import DualEmbeddingStore
from ragged.storage.schema import EmbeddingType


class TestDualEmbeddingStore:
    """Test dual embedding storage operations."""

    @pytest.fixture
    def store(self):
        """In-memory store for testing."""
        return DualEmbeddingStore(collection_name="test_collection")

    def test_add_text_embedding(self, store):
        """Test adding text embedding."""
        embedding = np.random.rand(384)

        embedding_id = store.add_text_embedding(
            document_id="doc123",
            chunk_id="chunk1",
            chunk_index=0,
            embedding=embedding,
            text_content="Test content"
        )

        assert embedding_id == "doc123_chunk_0_text"

        # Verify stored
        results = store.get_by_document("doc123")
        assert len(results["ids"]) == 1
        assert results["metadatas"][0]["embedding_type"] == "text"

    def test_add_vision_embedding(self, store):
        """Test adding vision embedding."""
        embedding = np.random.rand(768)

        embedding_id = store.add_vision_embedding(
            document_id="doc123",
            page_number=1,
            embedding=embedding,
            image_hash="abc123"
        )

        assert embedding_id == "doc123_page_1_vision"

        # Verify stored
        results = store.get_by_document("doc123")
        assert len(results["ids"]) == 1
        assert results["metadatas"][0]["embedding_type"] == "vision"

    def test_batch_add(self, store):
        """Test batch addition of mixed embeddings."""
        text_batch = [
            ("doc1", 0, np.random.rand(384), "chunk 0"),
            ("doc1", 1, np.random.rand(384), "chunk 1")
        ]

        vision_batch = [
            ("doc1", 1, np.random.rand(768), "hash1"),
            ("doc1", 2, np.random.rand(768), "hash2")
        ]

        result = store.add_batch(
            text_embeddings=text_batch,
            vision_embeddings=vision_batch
        )

        assert len(result["text_ids"]) == 2
        assert len(result["vision_ids"]) == 2

        # Verify total count
        all_results = store.get_by_document("doc1")
        assert len(all_results["ids"]) == 4

    def test_query_text_only(self, store):
        """Test querying text embeddings only."""
        # Add mixed embeddings
        store.add_text_embedding(
            "doc1", "chunk1", 0, np.random.rand(384), "text"
        )
        store.add_vision_embedding(
            "doc1", 1, np.random.rand(768), "hash"
        )

        # Query with text embedding
        query = np.random.rand(384)
        results = store.query_text(query, n_results=10)

        # Should only return text embeddings
        assert len(results["ids"][0]) == 1
        assert results["metadatas"][0][0]["embedding_type"] == "text"

    def test_invalid_dimension_rejection(self, store):
        """Test rejection of incorrect embedding dimensions."""
        # Text with wrong dimension
        with pytest.raises(ValueError, match="384-dimensional"):
            store.add_text_embedding(
                "doc1", "chunk1", 0,
                np.random.rand(768),  # Wrong!
                "text"
            )

        # Vision with wrong dimension
        with pytest.raises(ValueError, match="768-dimensional"):
            store.add_vision_embedding(
                "doc1", 1,
                np.random.rand(384),  # Wrong!
                "hash"
            )
```

**Time:** 2-3 hours

---

#### Session 4.2: Integration Tests (2-3h)

**Test Coverage:**
1. End-to-end document ingestion with dual embeddings
2. Migration from v0.4 to v0.5 schema
3. Hybrid retrieval workflow
4. GPU device selection and fallback

**Example Tests:**

```python
# tests/integration/test_dual_storage_pipeline.py

import pytest
from pathlib import Path
from ragged.ingestion.processor import DocumentProcessor
from ragged.storage.dual_store import DualEmbeddingStore
from ragged.embeddings.text_embedder import TextEmbedder


class TestDualStoragePipeline:
    """Integration tests for dual embedding pipeline."""

    @pytest.fixture
    def sample_pdf(self, tmp_path):
        """Create sample PDF for testing."""
        # (PDF generation logic)
        pass

    def test_text_only_ingestion(self, sample_pdf):
        """Test ingestion with text embeddings only."""
        store = DualEmbeddingStore(collection_name="test_text_only")
        processor = DocumentProcessor(
            text_embedder=TextEmbedder(),
            vision_embedder=None,
            store=store
        )

        doc_id = processor.process_document(sample_pdf, enable_vision=False)

        # Verify only text embeddings stored
        results = store.get_by_document(doc_id)
        embedding_types = [m["embedding_type"] for m in results["metadatas"]]
        assert all(t == "text" for t in embedding_types)

    def test_dual_embedding_ingestion(self, sample_pdf):
        """Test ingestion with both text and vision embeddings."""
        pytest.importorskip("torch")  # Requires PyTorch for vision

        from ragged.embeddings.colpali_embedder import ColPaliEmbedder

        store = DualEmbeddingStore(collection_name="test_dual")
        processor = DocumentProcessor(
            text_embedder=TextEmbedder(),
            vision_embedder=ColPaliEmbedder(device="cpu"),
            store=store
        )

        doc_id = processor.process_document(sample_pdf, enable_vision=True)

        # Verify both types stored
        results = store.get_by_document(doc_id)
        embedding_types = set(m["embedding_type"] for m in results["metadatas"])
        assert embedding_types == {"text", "vision"}

    def test_schema_migration(self):
        """Test migration from v0.4 to v0.5 schema."""
        from ragged.storage.migration import StorageMigration

        # Create v0.4 collection (text-only, old schema)
        # (Migration test logic)
        pass
```

**Time:** 2-3 hours

---

## Success Criteria

**Functional Requirements:**
- [ ] Text embeddings stored with `embedding_type: "text"` metadata
- [ ] Vision embeddings stored with `embedding_type: "vision"` metadata
- [ ] Unique ID generation: `{doc}_chunk_{n}_text` and `{doc}_page_{n}_vision`
- [ ] Batch storage for text and vision embeddings
- [ ] Separate query methods for text-only, vision-only, and hybrid retrieval
- [ ] Hybrid query uses reciprocal rank fusion with configurable weights
- [ ] Migration utility converts v0.4 collections to v0.5 schema
- [ ] CLI flags: `--vision/--no-vision` for enabling vision embeddings

**Quality Requirements:**
- [ ] 90%+ test coverage for storage module
- [ ] All tests pass on CPU (vision tests skip if no GPU available)
- [ ] Type hints on all public methods
- [ ] British English docstrings throughout
- [ ] Migration includes dry-run mode for safety

**Performance Requirements:**
- [ ] Batch storage: <100ms per embedding (text or vision)
- [ ] Query latency: <200ms for text, <300ms for vision
- [ ] Migration: <1 minute per 1000 embeddings

---

## Dependencies

**Required:**
- chromadb >= 0.4.0 (vector database)
- numpy >= 1.24.0 (array operations)
- loguru >= 0.7.0 (logging)

**From Other Features:**
- VISION-001: ColPaliEmbedder for vision embeddings
- v0.3.x: TextEmbedder for text embeddings

---

## Known Limitations

1. **No Cross-Type Similarity:** Cannot directly compare text and vision embeddings (different dimensionality, different semantic spaces)
2. **Hybrid Query Complexity:** RRF fusion is heuristic-based, may not be optimal for all use cases
3. **Migration Downtime:** Requires collection deletion/recreation during migration (no in-place update)
4. **Storage Overhead:** Dual embeddings approximately double storage requirements

---

## Future Enhancements (Post-v0.5)

1. **Advanced Fusion Methods:** Learn optimal text/vision weights from user feedback
2. **Embedding Compression:** Quantization or dimensionality reduction for storage efficiency
3. **Partial Updates:** Update text or vision embeddings independently
4. **Cross-Modal Learning:** Train adapter to map text ↔ vision embedding spaces

---

**Status:** Planned
**Estimated Total Effort:** 25-35 hours
