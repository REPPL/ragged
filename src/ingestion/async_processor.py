"""Async document processing for improved performance.

Enables concurrent document loading, chunking, and embedding.
"""

import asyncio
from typing import List, Optional, Callable, Any, Union
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
from dataclasses import dataclass
import time

from src.ingestion.models import Document
from src.ingestion.loaders import load_document
from src.chunking.splitters import RecursiveCharacterTextSplitter
from src.utils.logging import get_logger

logger = get_logger(__name__)


@dataclass
class ProcessingResult:
    """Result of async document processing."""

    document_id: str
    success: bool
    duration: float
    chunks_created: int = 0
    error: Optional[str] = None


class AsyncDocumentProcessor:
    """Async document processor with concurrent execution.

    Processes multiple documents concurrently using asyncio and thread pools.
    """

    def __init__(
        self,
        max_workers: Optional[int] = None,
        use_process_pool: bool = False
    ):
        """Initialize async processor.

        Args:
            max_workers: Maximum number of concurrent workers
            use_process_pool: Use ProcessPoolExecutor instead of ThreadPoolExecutor
        """
        self.max_workers = max_workers
        self.use_process_pool = use_process_pool

        self.executor: Union[ProcessPoolExecutor, ThreadPoolExecutor]
        if use_process_pool:
            self.executor = ProcessPoolExecutor(max_workers=max_workers)
        else:
            self.executor = ThreadPoolExecutor(max_workers=max_workers)

    async def load_document_async(
        self,
        file_path: Path
    ) -> Optional[Document]:
        """Load single document asynchronously.

        Args:
            file_path: Path to document

        Returns:
            Loaded document or None on error
        """
        loop = asyncio.get_event_loop()

        try:
            # Run blocking I/O in executor
            document = await loop.run_in_executor(
                self.executor,
                load_document,
                file_path
            )

            logger.debug(f"Loaded document: {file_path}")
            return document

        except (FileNotFoundError, PermissionError, ValueError, TypeError, OSError):
            logger.exception(f"Error loading document {file_path}")
            return None

    async def load_documents_async(
        self,
        file_paths: List[Path],
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> List[Document]:
        """Load multiple documents concurrently.

        Args:
            file_paths: List of document paths
            progress_callback: Optional callback(completed, total)

        Returns:
            List of loaded documents
        """
        logger.info(f"Loading {len(file_paths)} documents asynchronously...")

        start_time = time.time()

        # Create tasks for all documents
        tasks = [
            self.load_document_async(file_path)
            for file_path in file_paths
        ]

        # Process with progress tracking
        documents = []
        for i, task in enumerate(asyncio.as_completed(tasks), 1):
            doc = await task
            if doc:
                documents.append(doc)

            if progress_callback:
                progress_callback(i, len(file_paths))

        duration = time.time() - start_time

        logger.info(
            f"Loaded {len(documents)}/{len(file_paths)} documents "
            f"in {duration:.2f}s ({len(documents)/duration:.1f} docs/s)"
        )

        return documents

    async def process_document_async(
        self,
        document: Document,
        chunker: Any,  # RecursiveCharacterTextSplitter or ContextualChunker
        embed_fn: Optional[Callable[..., Any]] = None
    ) -> ProcessingResult:
        """Process single document (chunk + embed) asynchronously.

        Args:
            document: Document to process
            chunker: Chunking strategy
            embed_fn: Optional embedding function

        Returns:
            Processing result
        """
        start_time = time.time()
        loop = asyncio.get_event_loop()

        try:
            # Chunk document in executor
            # Support both ContextualChunker.chunk_document() and RecursiveCharacterTextSplitter.split_text()
            if hasattr(chunker, 'chunk_document'):
                # ContextualChunker
                chunks = await loop.run_in_executor(
                    self.executor,
                    chunker.chunk_document,
                    document
                )
            elif hasattr(chunker, 'split_text'):
                # RecursiveCharacterTextSplitter - returns list of text strings
                text_chunks = await loop.run_in_executor(
                    self.executor,
                    chunker.split_text,
                    document.content
                )
                chunks = text_chunks  # For counting purposes
            else:
                raise ValueError(f"Chunker must have chunk_document or split_text method")

            # Embed chunks if function provided
            if embed_fn and chunks:
                await loop.run_in_executor(
                    self.executor,
                    embed_fn,
                    chunks
                )

            duration = time.time() - start_time

            result = ProcessingResult(
                document_id=document.document_id,
                success=True,
                duration=duration,
                chunks_created=len(chunks) if chunks else 0
            )

            logger.debug(
                f"Processed document {document.document_id}: "
                f"{len(chunks) if chunks else 0} chunks in {duration:.2f}s"
            )

            return result

        except (ValueError, TypeError, AttributeError, KeyError, OSError) as e:
            duration = time.time() - start_time
            logger.exception(
                f"Error processing document {document.document_id}"
            )

            return ProcessingResult(
                document_id=document.document_id,
                success=False,
                duration=duration,
                error=str(e)
            )

    async def process_documents_async(
        self,
        documents: List[Document],
        chunker: Any,
        embed_fn: Optional[Callable[..., Any]] = None,
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> List[ProcessingResult]:
        """Process multiple documents concurrently.

        Args:
            documents: List of documents
            chunker: Chunking strategy
            embed_fn: Optional embedding function
            progress_callback: Optional callback(completed, total)

        Returns:
            List of processing results
        """
        logger.info(
            f"Processing {len(documents)} documents asynchronously..."
        )

        start_time = time.time()

        # Create tasks for all documents
        tasks = [
            self.process_document_async(doc, chunker, embed_fn)
            for doc in documents
        ]

        # Process with progress tracking
        results = []
        for i, task in enumerate(asyncio.as_completed(tasks), 1):
            result = await task
            results.append(result)

            if progress_callback:
                progress_callback(i, len(documents))

        duration = time.time() - start_time

        successful = sum(1 for r in results if r.success)
        total_chunks = sum(r.chunks_created for r in results)

        logger.info(
            f"Processed {successful}/{len(documents)} documents "
            f"in {duration:.2f}s ({successful/duration:.1f} docs/s, "
            f"{total_chunks} chunks created)"
        )

        return results

    async def process_batch_async(
        self,
        file_paths: List[Path],
        chunker: Any,
        embed_fn: Optional[Callable[..., Any]] = None,
        progress_callback: Optional[Callable[[int, int, str], None]] = None
    ) -> List[ProcessingResult]:
        """Load and process documents in one batch operation.

        Args:
            file_paths: List of document paths
            chunker: Chunking strategy
            embed_fn: Optional embedding function
            progress_callback: Optional callback(completed, total, stage)

        Returns:
            List of processing results
        """
        logger.info(
            f"Batch processing {len(file_paths)} documents..."
        )

        start_time = time.time()

        # Stage 1: Load documents
        if progress_callback:
            progress_callback(0, len(file_paths), "Loading")

        documents = await self.load_documents_async(
            file_paths,
            lambda c, t: progress_callback(c, t, "Loading")
            if progress_callback else None
        )

        # Stage 2: Process documents
        if progress_callback:
            progress_callback(0, len(documents), "Processing")

        results = await self.process_documents_async(
            documents,
            chunker,
            embed_fn,
            lambda c, t: progress_callback(c, t, "Processing")
            if progress_callback else None
        )

        duration = time.time() - start_time

        successful = sum(1 for r in results if r.success)
        total_chunks = sum(r.chunks_created for r in results)

        logger.info(
            f"Batch processing complete: {successful}/{len(file_paths)} "
            f"documents in {duration:.2f}s ({successful/duration:.1f} docs/s, "
            f"{total_chunks} chunks created)"
        )

        return results

    def shutdown(self, wait: bool = True) -> None:
        """Shutdown executor.

        Args:
            wait: Wait for pending tasks to complete
        """
        self.executor.shutdown(wait=wait)
        logger.debug("Async processor shutdown")

    def __enter__(self) -> "AsyncDocumentProcessor":
        """Context manager entry."""
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Context manager exit."""
        self.shutdown(wait=True)


# Convenience functions for common patterns

async def load_documents_concurrent(
    file_paths: List[Path],
    max_workers: Optional[int] = None
) -> List[Document]:
    """Load documents concurrently (convenience function).

    Args:
        file_paths: List of document paths
        max_workers: Maximum concurrent workers

    Returns:
        List of loaded documents
    """
    processor = AsyncDocumentProcessor(max_workers=max_workers)
    try:
        return await processor.load_documents_async(file_paths)
    finally:
        processor.shutdown()


async def process_documents_concurrent(
    documents: List[Document],
    chunker: Any,
    max_workers: Optional[int] = None
) -> List[ProcessingResult]:
    """Process documents concurrently (convenience function).

    Args:
        documents: List of documents
        chunker: Chunking strategy
        max_workers: Maximum concurrent workers

    Returns:
        List of processing results
    """
    processor = AsyncDocumentProcessor(max_workers=max_workers)
    try:
        return await processor.process_documents_async(documents, chunker)
    finally:
        processor.shutdown()
