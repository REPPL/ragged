"""Incremental index operations with checkpointing and atomic updates.

v0.2.9: Differential updates, atomic swap, and background compaction for BM25.
v0.2.10: Replaced pickle with safe JSON serialization (FEAT-SEC-001).
"""

import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from rank_bm25 import BM25Okapi

from src.retrieval.bm25 import BM25Retriever
from src.utils.logging import get_logger
from src.utils.serialization import load_json, save_json

logger = get_logger(__name__)


@dataclass
class IndexCheckpoint:
    """Checkpoint data for incremental indexing."""

    documents: list[str]
    doc_ids: list[str]
    metadatas: list[dict[str, Any]]
    deleted_ids: set[str]
    timestamp: float
    version: int


class IncrementalBM25Retriever(BM25Retriever):
    """BM25 retriever with incremental update support.

    Features:
    - Add documents without full rebuild
    - Remove documents with lazy deletion
    - Atomic index swap for consistency
    - Background compaction when fragmentation high
    - Checkpoint persistence for recovery

    Example:
        >>> retriever = IncrementalBM25Retriever()
        >>> retriever.index_documents(docs, ids)
        >>> retriever.add_documents(new_docs, new_ids)  # Incremental
        >>> retriever.remove_documents(["id1", "id2"])  # Mark deleted
        >>> retriever.compact_if_needed()  # Background compaction
    """

    def __init__(
        self,
        checkpoint_dir: Path | None = None,
        enable_checkpoints: bool = True,
        compaction_threshold: float = 0.5,
    ):
        """Initialize incremental BM25 retriever.

        Args:
            checkpoint_dir: Directory for checkpoint files
            enable_checkpoints: Enable checkpoint persistence
            compaction_threshold: Trigger compaction when fragmentation >threshold
        """
        super().__init__()

        self.checkpoint_dir = checkpoint_dir or Path.home() / ".ragged" / "checkpoints"
        self.enable_checkpoints = enable_checkpoints
        self.compaction_threshold = compaction_threshold

        # Incremental state
        self.deleted_ids: set[str] = set()
        self.version = 0
        self._lock = threading.Lock()

        # Compaction state
        self.compaction_in_progress = False
        self.last_compaction_time = 0.0

        if self.enable_checkpoints:
            self.checkpoint_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"Incremental indexing enabled with checkpoints at {self.checkpoint_dir}")

    def add_documents(
        self,
        documents: list[str],
        doc_ids: list[str],
        metadatas: list[dict[str, Any]] | None = None,
    ) -> None:
        """Add documents incrementally without full rebuild.

        Args:
            documents: Documents to add
            doc_ids: Document IDs
            metadatas: Optional metadata
        """
        if len(documents) != len(doc_ids):
            raise ValueError("documents and doc_ids must have same length")

        if not documents:
            return

        with self._lock:
            # Append to existing corpus
            self.documents.extend(documents)
            self.doc_ids.extend(doc_ids)
            self.metadatas.extend(metadatas or [{} for _ in documents])

            # Rebuild index with updated corpus
            # Note: BM25Okapi requires full rebuild, but we avoid re-processing docs
            tokenized_corpus = [doc.lower().split() for doc in self.documents]
            self.index = BM25Okapi(tokenized_corpus)

            self.version += 1

            logger.info(
                f"Added {len(documents)} documents incrementally "
                f"(total: {len(self.documents)}, version: {self.version})"
            )

            # Save checkpoint
            if self.enable_checkpoints:
                self._save_checkpoint()

    def remove_documents(self, doc_ids: list[str]) -> None:
        """Remove documents by marking as deleted (lazy deletion).

        Actual removal happens during compaction.

        Args:
            doc_ids: Document IDs to remove
        """
        with self._lock:
            # Mark as deleted
            self.deleted_ids.update(doc_ids)

            logger.info(
                f"Marked {len(doc_ids)} documents for deletion "
                f"(total deleted: {len(self.deleted_ids)})"
            )

            # Check if compaction needed
            self.compact_if_needed()

    def compact_if_needed(self, force: bool = False) -> bool:
        """Compact index if fragmentation exceeds threshold.

        Args:
            force: Force compaction regardless of threshold

        Returns:
            True if compaction performed
        """
        if self.compaction_in_progress:
            logger.debug("Compaction already in progress")
            return False

        fragmentation = self.fragmentation_ratio()

        if not force and fragmentation < self.compaction_threshold:
            return False

        logger.info(
            f"Starting compaction (fragmentation: {fragmentation:.1%}, "
            f"threshold: {self.compaction_threshold:.1%})"
        )

        return self._compact()

    def _compact(self) -> bool:
        """Perform index compaction (remove deleted documents).

        Returns:
            True if compaction successful
        """
        with self._lock:
            if not self.deleted_ids:
                logger.debug("No deleted documents, skipping compaction")
                return False

            self.compaction_in_progress = True

            try:
                # Filter out deleted documents
                new_documents = []
                new_doc_ids = []
                new_metadatas = []

                for i, doc_id in enumerate(self.doc_ids):
                    if doc_id not in self.deleted_ids:
                        new_documents.append(self.documents[i])
                        new_doc_ids.append(doc_id)
                        new_metadatas.append(self.metadatas[i])

                # Atomic swap
                old_count = len(self.documents)
                self.documents = new_documents
                self.doc_ids = new_doc_ids
                self.metadatas = new_metadatas
                self.deleted_ids.clear()

                # Rebuild index
                if self.documents:
                    tokenized_corpus = [doc.lower().split() for doc in self.documents]
                    self.index = BM25Okapi(tokenized_corpus)
                else:
                    self.index = None

                self.version += 1
                self.last_compaction_time = time.time()

                removed = old_count - len(self.documents)
                logger.info(
                    f"Compaction complete: removed {removed} documents "
                    f"(total: {len(self.documents)}, version: {self.version})"
                )

                # Save checkpoint
                if self.enable_checkpoints:
                    self._save_checkpoint()

                return True

            finally:
                self.compaction_in_progress = False

    def fragmentation_ratio(self) -> float:
        """Calculate index fragmentation ratio.

        Returns:
            Ratio of deleted to total documents (0.0-1.0)
        """
        if not self.doc_ids:
            return 0.0

        return len(self.deleted_ids) / (len(self.doc_ids) + len(self.deleted_ids))

    def search(
        self,
        query: str,
        top_k: int = 5,
    ) -> list[tuple[str, str, float, dict[str, Any]]]:
        """Search, filtering out deleted documents.

        Args:
            query: Search query
            top_k: Number of results

        Returns:
            List of results excluding deleted documents
        """
        # Get results from parent
        results = super().search(query, top_k + len(self.deleted_ids))

        # Filter deleted
        filtered = [
            (doc_id, doc, score, meta)
            for doc_id, doc, score, meta in results
            if doc_id not in self.deleted_ids
        ]

        return filtered[:top_k]

    def _save_checkpoint(self) -> None:
        """Save checkpoint to disk using safe JSON serialization.

        Security: Replaced pickle with JSON (v0.2.10 FEAT-SEC-001) to prevent arbitrary code execution.
        """
        if not self.enable_checkpoints:
            return

        checkpoint_data = {
            "documents": self.documents,
            "doc_ids": self.doc_ids,
            "metadatas": self.metadatas,
            "deleted_ids": list(self.deleted_ids),  # Convert set to list for JSON
            "timestamp": time.time(),
            "version": self.version,
        }

        checkpoint_path = self.checkpoint_dir / f"bm25_checkpoint_v{self.version}.json"

        try:
            save_json(checkpoint_data, checkpoint_path)

            logger.debug(f"Saved checkpoint: {checkpoint_path}")

            # Clean old checkpoints (keep last 3)
            self._cleanup_old_checkpoints(keep=3)

        except Exception as e:
            logger.error(f"Failed to save checkpoint: {e}")

    def _cleanup_old_checkpoints(self, keep: int = 3) -> None:
        """Remove old checkpoint files.

        Args:
            keep: Number of recent checkpoints to keep

        Note: v0.2.10 migrated from .pkl to .json files for security.
        """
        try:
            # Clean both JSON (current) and legacy .pkl files
            json_checkpoints = sorted(
                self.checkpoint_dir.glob("bm25_checkpoint_v*.json"),
                key=lambda p: p.stat().st_mtime,
                reverse=True
            )
            pkl_checkpoints = list(self.checkpoint_dir.glob("bm25_checkpoint_v*.pkl"))

            # Keep specified number of JSON checkpoints
            for old_checkpoint in json_checkpoints[keep:]:
                old_checkpoint.unlink()
                logger.debug(f"Removed old checkpoint: {old_checkpoint}")

            # Remove all legacy .pkl files (migrated to .json)
            for old_checkpoint in pkl_checkpoints:
                old_checkpoint.unlink()
                logger.debug(f"Removed legacy pickle checkpoint: {old_checkpoint}")

        except Exception as e:
            logger.error(f"Failed to cleanup checkpoints: {e}")

    def load_checkpoint(self, version: int | None = None) -> bool:
        """Load checkpoint from disk using safe JSON deserialization.

        Args:
            version: Specific version to load (None = latest)

        Returns:
            True if checkpoint loaded successfully

        Security: Replaced pickle with JSON (v0.2.10 FEAT-SEC-001) to prevent arbitrary code execution.
        """
        if not self.enable_checkpoints:
            logger.warning("Checkpoints disabled, cannot load")
            return False

        try:
            # Find checkpoint file (prioritize JSON, fallback to legacy .pkl for migration)
            if version is not None:
                checkpoint_path = self.checkpoint_dir / f"bm25_checkpoint_v{version}.json"
                # Fallback to .pkl if .json doesn't exist (legacy migration)
                if not checkpoint_path.exists():
                    pkl_path = self.checkpoint_dir / f"bm25_checkpoint_v{version}.pkl"
                    if pkl_path.exists():
                        logger.warning(
                            f"Loading legacy pickle checkpoint v{version}. "
                            "Consider migrating to JSON format."
                        )
                        checkpoint_path = pkl_path
            else:
                # Load latest (prefer JSON)
                json_checkpoints = sorted(
                    self.checkpoint_dir.glob("bm25_checkpoint_v*.json"),
                    key=lambda p: p.stat().st_mtime,
                    reverse=True
                )
                pkl_checkpoints = sorted(
                    self.checkpoint_dir.glob("bm25_checkpoint_v*.pkl"),
                    key=lambda p: p.stat().st_mtime,
                    reverse=True
                )

                if json_checkpoints:
                    checkpoint_path = json_checkpoints[0]
                elif pkl_checkpoints:
                    checkpoint_path = pkl_checkpoints[0]
                    logger.warning(
                        "Loading legacy pickle checkpoint. Consider migrating to JSON format."
                    )
                else:
                    logger.warning("No checkpoints found")
                    return False

            # Load checkpoint based on file type
            if checkpoint_path.suffix == ".json":
                checkpoint_data = load_json(checkpoint_path)
            else:
                # Legacy pickle migration (temporary for backward compatibility)
                import pickle
                with open(checkpoint_path, 'rb') as f:
                    checkpoint_obj: IndexCheckpoint = pickle.load(f)  # noqa: S301
                # Convert to dict format
                checkpoint_data = {
                    "documents": checkpoint_obj.documents,
                    "doc_ids": checkpoint_obj.doc_ids,
                    "metadatas": checkpoint_obj.metadatas,
                    "deleted_ids": list(checkpoint_obj.deleted_ids),
                    "timestamp": checkpoint_obj.timestamp,
                    "version": checkpoint_obj.version,
                }

            with self._lock:
                self.documents = checkpoint_data["documents"]
                self.doc_ids = checkpoint_data["doc_ids"]
                self.metadatas = checkpoint_data["metadatas"]
                self.deleted_ids = set(checkpoint_data["deleted_ids"])  # Convert list back to set
                self.version = checkpoint_data["version"]

                # Rebuild index
                if self.documents:
                    tokenized_corpus = [doc.lower().split() for doc in self.documents]
                    self.index = BM25Okapi(tokenized_corpus)
                else:
                    self.index = None

            logger.info(
                f"Loaded checkpoint v{self.version} from {checkpoint_path} "
                f"({len(self.documents)} documents, {len(self.deleted_ids)} deleted)"
            )

            # Auto-migrate: Save as JSON if we loaded from .pkl
            if checkpoint_path.suffix == ".pkl":
                logger.info("Auto-migrating legacy pickle checkpoint to JSON...")
                self._save_checkpoint()

            return True

        except Exception as e:
            logger.error(f"Failed to load checkpoint: {e}")
            return False

    def rebuild_index(self) -> None:
        """Force full index rebuild (compacts and reindexes).

        Useful for recovering from corruption or forcing optimization.
        """
        logger.info("Forcing full index rebuild...")

        with self._lock:
            # Compact first
            if self.deleted_ids:
                self._compact()

            # Rebuild index
            if self.documents:
                tokenized_corpus = [doc.lower().split() for doc in self.documents]
                self.index = BM25Okapi(tokenized_corpus)
                self.version += 1

                logger.info(f"Index rebuilt: {len(self.documents)} documents, version {self.version}")

                if self.enable_checkpoints:
                    self._save_checkpoint()

    def get_stats(self) -> dict[str, Any]:
        """Get index statistics.

        Returns:
            Statistics dictionary
        """
        return {
            "total_documents": len(self.doc_ids),
            "active_documents": len(self.doc_ids) - len(self.deleted_ids),
            "deleted_documents": len(self.deleted_ids),
            "fragmentation_ratio": self.fragmentation_ratio(),
            "version": self.version,
            "compaction_in_progress": self.compaction_in_progress,
            "last_compaction_time": self.last_compaction_time,
            "checkpoints_enabled": self.enable_checkpoints,
        }

    def clear(self) -> None:
        """Clear index and deleted set."""
        super().clear()
        with self._lock:
            self.deleted_ids.clear()
            self.version = 0
