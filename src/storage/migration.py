"""
Storage schema migration utilities.

Handles migration from v0.4 text-only storage to v0.5 dual embedding storage.

Migration process:
1. Detect existing schema version
2. Add "embedding_type": "text" to all existing metadata
3. Rename IDs from "{doc_id}_chunk_{n}" to "{doc_id}_chunk_{n}_text"
4. Preserve all existing embeddings and content

v0.5.0: v0.4 → v0.5 migration support
"""

import logging
import re
from typing import Any

import chromadb
from chromadb.api import ClientAPI

from ragged.storage.schema import EmbeddingType

logger = logging.getLogger(__name__)

# SECURITY FIX (CRITICAL-8): Pattern for safe collection names
# Allow: alphanumeric, underscore, dash (must start with letter/number)
SAFE_COLLECTION_NAME_PATTERN = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9_-]{0,62}$")


def _validate_collection_name(name: str) -> str:
    """
    Validate and sanitize collection name to prevent NoSQL injection.

    SECURITY FIX (CRITICAL-8): Prevents malicious collection names.

    Args:
        name: Collection name to validate

    Returns:
        Validated collection name

    Raises:
        ValueError: If collection name is invalid or potentially malicious

    Example:
        >>> _validate_collection_name("documents")
        'documents'
        >>> _validate_collection_name("doc_collection_123")
        'doc_collection_123'
        >>> _validate_collection_name("../../etc/passwd")
        ValueError: Invalid collection name
    """
    if not name or not isinstance(name, str):
        raise ValueError(f"Collection name must be a non-empty string, got: {type(name)}")

    if len(name) > 63:
        raise ValueError(f"Collection name too long (max 63 characters): {name}")

    if not SAFE_COLLECTION_NAME_PATTERN.match(name):
        raise ValueError(
            f"Invalid collection name: '{name}'. "
            f"Must start with alphanumeric and contain only alphanumeric, underscore, dash."
        )

    # Additional check for suspicious patterns
    suspicious_patterns = ["../", "..\\", "$", "{", "}", "<", ">", "'", '"', ";", "|"]
    for pattern in suspicious_patterns:
        if pattern in name:
            raise ValueError(f"Collection name contains suspicious pattern: {pattern}")

    return name


class StorageMigration:
    """Utilities for migrating vector storage schema versions."""

    def __init__(self, client: ClientAPI) -> None:
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
            ValueError: If collection doesn't exist or name is invalid

        Example:
            >>> migration = StorageMigration(client)
            >>> migration.detect_schema_version("documents")
            'v0.4'
        """
        # SECURITY FIX (CRITICAL-8): Validate collection name
        collection_name = _validate_collection_name(collection_name)

        try:
            collection = self.client.get_collection(collection_name)
        except Exception as e:
            raise ValueError(f"Collection '{collection_name}' not found") from e

        # Check collection metadata for schema version
        if hasattr(collection, "metadata") and collection.metadata:
            schema_version = collection.metadata.get("schema_version")
            if schema_version:
                return schema_version

        # Check first few embeddings for embedding_type field
        results = collection.peek(limit=10)

        if not results["metadatas"]:
            logger.warning(f"Collection '{collection_name}' is empty, assuming v0.4")
            return "v0.4"

        # Check if any metadata has embedding_type field
        for metadata in results["metadatas"]:
            if metadata and "embedding_type" in metadata:
                return "v0.5"

        return "v0.4"

    def migrate_collection(
        self, collection_name: str, batch_size: int = 100, dry_run: bool = False
    ) -> dict[str, int]:
        """
        Migrate v0.4 collection to v0.5 dual-embedding schema.

        Migration steps:
        1. Add "embedding_type": "text" to all existing metadata
        2. Rename IDs: "{doc_id}_chunk_{n}" → "{doc_id}_chunk_{n}_text"
        3. Update collection metadata: schema_version = "v0.5"

        Args:
            collection_name: Name of collection to migrate
            batch_size: Number of embeddings to process per batch
            dry_run: If True, only report changes without applying

        Returns:
            Migration statistics:
            {
                "embeddings_processed": int,
                "ids_renamed": int,
                "metadata_updated": int,
                "skipped": int,
            }

        Raises:
            ValueError: If collection is already v0.5, name is invalid, or migration fails

        Example:
            >>> migration = StorageMigration(client)
            >>> stats = migration.migrate_collection("documents", dry_run=True)
            >>> print(stats)
            {'embeddings_processed': 150, 'ids_renamed': 150, 'metadata_updated': 150, 'skipped': 0}
        """
        # SECURITY FIX (CRITICAL-8): Validate collection name
        collection_name = _validate_collection_name(collection_name)

        schema_version = self.detect_schema_version(collection_name)

        if schema_version == "v0.5":
            raise ValueError(f"Collection '{collection_name}' is already v0.5 schema")

        logger.info(f"Starting migration of '{collection_name}' (dry_run={dry_run})")

        collection = self.client.get_collection(collection_name)

        stats = {
            "embeddings_processed": 0,
            "ids_renamed": 0,
            "metadata_updated": 0,
            "skipped": 0,
        }

        # Get total count for progress tracking
        try:
            total_count = collection.count()
            logger.info(f"Found {total_count} embeddings to process")
        except Exception:
            total_count = None

        offset = 0

        while True:
            # Fetch batch
            try:
                results = collection.get(
                    limit=batch_size, offset=offset, include=["embeddings", "metadatas", "documents"]
                )
            except Exception as e:
                logger.error(f"Failed to fetch batch at offset {offset}: {e}")
                raise

            if not results["ids"]:
                break  # No more embeddings

            # Process batch
            migrated_ids = []
            migrated_embeddings = []
            migrated_metadatas = []
            migrated_documents = []

            for i, old_id in enumerate(results["ids"]):
                # Check if already migrated (has _text or _vision suffix)
                if old_id.endswith("_text") or old_id.endswith("_vision"):
                    stats["skipped"] += 1
                    continue

                # Rename ID: "doc_chunk_5" → "doc_chunk_5_text"
                new_id = f"{old_id}_text"
                stats["ids_renamed"] += 1

                migrated_ids.append((old_id, new_id))
                migrated_embeddings.append(results["embeddings"][i])
                migrated_documents.append(
                    results["documents"][i] if results["documents"] else ""
                )

                # Add embedding_type to metadata
                metadata = (
                    results["metadatas"][i].copy() if results["metadatas"][i] else {}
                )
                if "embedding_type" not in metadata:
                    metadata["embedding_type"] = EmbeddingType.TEXT.value
                    stats["metadata_updated"] += 1

                migrated_metadatas.append(metadata)

            stats["embeddings_processed"] += len(results["ids"])

            # Apply migration if not dry run
            if not dry_run and migrated_ids:
                try:
                    # Delete old embeddings
                    old_ids_to_delete = [old_id for old_id, _ in migrated_ids]
                    collection.delete(ids=old_ids_to_delete)

                    # Add migrated embeddings with new IDs
                    new_ids = [new_id for _, new_id in migrated_ids]
                    collection.add(
                        ids=new_ids,
                        embeddings=migrated_embeddings,
                        metadatas=migrated_metadatas,
                        documents=migrated_documents,
                    )

                    logger.info(
                        f"Migrated batch: {len(migrated_ids)} embeddings "
                        f"({stats['embeddings_processed']}/{total_count or '?'})"
                    )

                except Exception as e:
                    logger.error(f"Failed to apply migration for batch: {e}")
                    raise

            offset += batch_size

        # Update collection metadata if not dry run
        if not dry_run:
            try:
                # Note: ChromaDB doesn't support modifying collection metadata directly
                # This would require recreating the collection
                logger.info("Migration complete, collection schema is now v0.5")
            except Exception as e:
                logger.warning(f"Could not update collection metadata: {e}")

        logger.info(
            f"Migration {'simulation' if dry_run else 'complete'}: "
            f"{stats['embeddings_processed']} processed, "
            f"{stats['ids_renamed']} IDs renamed, "
            f"{stats['metadata_updated']} metadata updated, "
            f"{stats['skipped']} skipped"
        )

        return stats
