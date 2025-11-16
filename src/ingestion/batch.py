"""Batch document ingestion with progress reporting and error handling.

Provides functionality to ingest multiple documents with progress tracking,
duplicate detection, graceful error handling, and memory management.
"""

import gc
import psutil
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import List, Optional

from rich.console import Console
from rich.progress import Progress, TaskID

from src.chunking.splitters import chunk_document
from src.embeddings.factory import get_embedder
from src.ingestion.loaders import load_document
from src.storage.vector_store import VectorStore
from src.utils.logging import get_logger
from src.exceptions import MemoryLimitExceededError

logger = get_logger(__name__)


class IngestionStatus(str, Enum):
    """Status of document ingestion."""

    SUCCESS = "success"
    DUPLICATE = "duplicate"
    SKIPPED = "skipped"
    FAILED = "failed"


@dataclass
class IngestionResult:
    """Result of ingesting a single document."""

    file_path: Path
    status: IngestionStatus
    document_id: Optional[str] = None
    chunks: int = 0
    error: Optional[str] = None
    duplicate_of: Optional[str] = None


@dataclass
class BatchSummary:
    """Summary of batch ingestion."""

    total: int
    successful: int
    duplicates: int
    skipped: int
    failed: int
    total_chunks: int
    results: List[IngestionResult]


class BatchIngester:
    """Batch document ingestion with error handling and memory management."""

    def __init__(
        self,
        console: Console,
        continue_on_error: bool = True,
        skip_duplicates: bool = True,
        memory_limit_mb: Optional[int] = None,
    ):
        """Initialize batch ingester.

        Args:
            console: Rich console for output
            continue_on_error: If True, continue after errors; if False, stop
            skip_duplicates: If True, skip duplicate documents automatically
            memory_limit_mb: Optional memory limit in MB (default: 80% of available)
        """
        self.console = console
        self.continue_on_error = continue_on_error
        self.skip_duplicates = skip_duplicates

        # Set memory limit (default to 80% of available RAM)
        if memory_limit_mb is None:
            total_mb = psutil.virtual_memory().total / (1024 * 1024)
            self.memory_limit_mb = int(total_mb * 0.8)
        else:
            self.memory_limit_mb = memory_limit_mb

        logger.info(f"BatchIngester initialized with {self.memory_limit_mb}MB memory limit")

    def _get_current_memory_mb(self) -> float:
        """Get current process memory usage in MB.

        Returns:
            Current memory usage in megabytes
        """
        process = psutil.Process()
        return process.memory_info().rss / (1024 * 1024)

    def _check_memory_limit(self, operation: str = "batch_processing") -> None:
        """Check if current memory usage exceeds limit.

        Args:
            operation: Name of operation for error message

        Raises:
            MemoryLimitExceededError: If memory limit exceeded
        """
        current_mb = self._get_current_memory_mb()
        if current_mb > self.memory_limit_mb:
            raise MemoryLimitExceededError(
                operation=operation,
                limit_mb=self.memory_limit_mb,
                usage_mb=int(current_mb)
            )

    def _force_garbage_collection(self) -> None:
        """Force garbage collection to free memory."""
        gc.collect()

    def ingest_batch(
        self,
        file_paths: List[Path],
        progress: Optional[Progress] = None,
    ) -> BatchSummary:
        """
        Ingest multiple documents with progress reporting.

        Args:
            file_paths: List of document paths to ingest
            progress: Optional Rich progress bar

        Returns:
            BatchSummary with statistics and results
        """
        results = []
        total_chunks = 0

        # Initialize shared resources
        vector_store = VectorStore()
        embedder = get_embedder()

        # Create progress task
        task = None
        if progress:
            task = progress.add_task("[cyan]Processing documents...", total=len(file_paths))

        for i, file_path in enumerate(file_paths, 1):
            if progress and task:
                progress.update(
                    task,
                    description=f"[cyan][{i}/{len(file_paths)}] {file_path.name}",
                    completed=i - 1,
                )

            # Check memory before processing
            try:
                self._check_memory_limit(f"document_{i}")
            except MemoryLimitExceededError as e:
                logger.warning(f"Memory limit approaching, forcing GC: {e}")
                self._force_garbage_collection()
                # Check again after GC
                self._check_memory_limit(f"document_{i}_post_gc")

            # Ingest single document
            result = self._ingest_single(
                file_path, vector_store, embedder
            )
            results.append(result)

            if result.status == IngestionStatus.SUCCESS:
                total_chunks += result.chunks

            # Force garbage collection after each document to free memory
            self._force_garbage_collection()

            # Fail fast if configured
            if (
                not self.continue_on_error
                and result.status == IngestionStatus.FAILED
            ):
                self.console.print(
                    f"[red]Aborting due to error: {result.error}[/red]"
                )
                break

        if progress and task:
            progress.update(task, completed=len(file_paths))

        # Final garbage collection
        self._force_garbage_collection()

        # Build summary
        summary = BatchSummary(
            total=len(results),
            successful=sum(1 for r in results if r.status == IngestionStatus.SUCCESS),
            duplicates=sum(1 for r in results if r.status == IngestionStatus.DUPLICATE),
            skipped=sum(1 for r in results if r.status == IngestionStatus.SKIPPED),
            failed=sum(1 for r in results if r.status == IngestionStatus.FAILED),
            total_chunks=total_chunks,
            results=results,
        )

        return summary

    def _ingest_single(
        self,
        file_path: Path,
        vector_store: VectorStore,
        embedder,
    ) -> IngestionResult:
        """Ingest a single document with error handling.

        Args:
            file_path: Path to document
            vector_store: Shared vector store instance
            embedder: Shared embedder instance

        Returns:
            IngestionResult with status and details
        """
        try:
            # Load document
            document = load_document(file_path)

            # Check for duplicates
            if self.skip_duplicates:
                file_hash = document.metadata.file_hash
                existing = vector_store.get_documents_by_metadata(
                    where={"file_hash": file_hash}
                )

                if existing and existing.get("ids"):
                    existing_doc_id = existing["metadatas"][0].get("document_id")
                    return IngestionResult(
                        file_path=file_path,
                        status=IngestionStatus.DUPLICATE,
                        duplicate_of=existing_doc_id,
                    )

            # Chunk document
            document = chunk_document(document)

            # Generate embeddings
            chunk_texts = [chunk.text for chunk in document.chunks]
            embeddings = embedder.embed_batch(chunk_texts)

            # Prepare metadata
            ids = [chunk.chunk_id for chunk in document.chunks]
            metadatas = []
            for chunk in document.chunks:
                metadata = chunk.metadata.model_dump()
                # Convert Path to string if present
                if "document_path" in metadata and hasattr(
                    metadata["document_path"], "__fspath__"
                ):
                    metadata["document_path"] = str(metadata["document_path"])

                # Remove None values - ChromaDB only supports str, int, float, bool
                metadata = {k: v for k, v in metadata.items() if v is not None}
                metadatas.append(metadata)

            # Store in vector database
            vector_store.add(
                ids=ids,
                embeddings=embeddings,
                documents=chunk_texts,
                metadatas=metadatas,
            )

            # Explicitly clear large objects to free memory
            del embeddings
            del chunk_texts
            del metadatas

            return IngestionResult(
                file_path=file_path,
                status=IngestionStatus.SUCCESS,
                document_id=document.document_id,
                chunks=len(document.chunks),
            )

        except Exception as e:
            logger.error(f"Failed to ingest {file_path}: {e}", exc_info=True)
            return IngestionResult(
                file_path=file_path,
                status=IngestionStatus.FAILED,
                error=str(e),
            )
