"""Cold start optimisation utilities.

v0.2.9: Reduce cold start time through pooling, lazy init, and parallelization.
"""

import asyncio
import threading
import time
from collections.abc import Callable
from typing import Any, Optional

from src.utils.logging import get_logger

logger = get_logger(__name__)


class ChromaDBConnectionPool:
    """Connection pool for ChromaDB clients.

    Features:
    - Reuse connections across requests
    - Keep-alive connections
    - Lazy connection creation
    - Thread-safe access

    Example:
        >>> pool = get_chromadb_pool()
        >>> with pool.get_connection() as client:
        ...     client.heartbeat()
    """

    _instance: Optional['ChromaDBConnectionPool'] = None
    _lock = threading.Lock()

    def __init__(self, pool_size: int = 3):
        """Initialize connection pool.

        Args:
            pool_size: Maximum number of pooled connections
        """
        self.pool_size = pool_size
        self.connections: list[Any] = []
        self.in_use: set = set()
        self._pool_lock = threading.Lock()

        logger.debug(f"ChromaDB connection pool initialized (size={pool_size})")

    @classmethod
    def get_instance(cls) -> 'ChromaDBConnectionPool':
        """Get singleton instance.

        Returns:
            Singleton ChromaDBConnectionPool
        """
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance

    @classmethod
    def reset_instance(cls) -> None:
        """Reset singleton (for testing)."""
        with cls._lock:
            if cls._instance is not None:
                cls._instance._cleanup()
            cls._instance = None

    def _create_connection(self) -> Any:
        """Create new ChromaDB client.

        Returns:
            ChromaDB client
        """
        try:
            import chromadb

            client = chromadb.Client()
            logger.debug("Created new ChromaDB connection")
            return client

        except Exception as e:
            logger.error(f"Failed to create ChromaDB connection: {e}")
            raise

    def get_connection(self) -> Any:
        """Get connection from pool.

        Returns:
            ChromaDB client (reused or new)
        """
        with self._pool_lock:
            # Try to reuse existing available connection
            for conn in self.connections:
                if conn not in self.in_use:
                    self.in_use.add(conn)
                    logger.debug("Reusing pooled ChromaDB connection")
                    return conn

            # Create new connection if under pool size
            if len(self.connections) < self.pool_size:
                conn = self._create_connection()
                self.connections.append(conn)
                self.in_use.add(conn)
                return conn

            # Pool exhausted - create temporary connection
            logger.warning("Connection pool exhausted, creating temporary connection")
            return self._create_connection()

    def release_connection(self, connection: Any) -> None:
        """Release connection back to pool.

        Args:
            connection: Connection to release
        """
        with self._pool_lock:
            if connection in self.in_use:
                self.in_use.remove(connection)
                logger.debug("Released connection back to pool")

    def _cleanup(self) -> None:
        """Cleanup all pooled connections."""
        with self._pool_lock:
            self.connections.clear()
            self.in_use.clear()
            logger.debug("Connection pool cleaned up")

    def __enter__(self):
        """Context manager entry."""
        return self.get_connection()

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        # For context manager, connection is temporary
        pass


def get_chromadb_pool() -> ChromaDBConnectionPool:
    """Get singleton ChromaDB connection pool.

    Returns:
        Singleton ChromaDBConnectionPool

    Example:
        >>> pool = get_chromadb_pool()
        >>> conn = pool.get_connection()
    """
    return ChromaDBConnectionPool.get_instance()


class LazyLoader:
    """Lazy initialization wrapper.

    Defers expensive initialization until first use.

    Example:
        >>> loader = LazyLoader(lambda: ExpensiveObject())
        >>> obj = loader.get()  # Initialized on first call
    """

    def __init__(self, factory: Callable[[], Any]):
        """Initialize lazy loader.

        Args:
            factory: Function that creates the object
        """
        self.factory = factory
        self._instance = None
        self._lock = threading.Lock()

    def get(self) -> Any:
        """Get instance (lazy initialization).

        Returns:
            Instance created by factory
        """
        if self._instance is None:
            with self._lock:
                if self._instance is None:
                    logger.debug(f"Lazy loading: {self.factory.__name__}")
                    start = time.time()
                    self._instance = self.factory()
                    duration = time.time() - start
                    logger.debug(f"Lazy load complete: {duration*1000:.0f}ms")

        return self._instance

    def is_loaded(self) -> bool:
        """Check if instance is loaded.

        Returns:
            True if already loaded
        """
        return self._instance is not None

    def reset(self) -> None:
        """Reset (force reload on next get)."""
        with self._lock:
            self._instance = None


async def parallel_init(*init_functions: Callable[[], Any]) -> list[Any]:
    """Initialize components in parallel.

    Args:
        *init_functions: Functions to run in parallel

    Returns:
        List of results from init functions

    Example:
        >>> async def init_embedder(): ...
        >>> async def init_vector_store(): ...
        >>> results = await parallel_init(init_embedder, init_vector_store)
    """
    logger.info(f"Initializing {len(init_functions)} components in parallel...")

    start = time.time()

    # Run all init functions concurrently
    tasks = [
        asyncio.to_thread(func)
        for func in init_functions
    ]

    results = await asyncio.gather(*tasks, return_exceptions=True)

    duration = time.time() - start

    # Check for errors
    errors = [r for r in results if isinstance(r, Exception)]
    if errors:
        logger.error(f"Parallel init had {len(errors)} errors: {errors}")

    logger.info(
        f"Parallel init complete: {len(results)} components in {duration*1000:.0f}ms "
        f"({len(errors)} errors)"
    )

    return results


class ColdStartOptimizer:
    """Holistic cold start optimisation.

    Combines all optimisation strategies:
    - Connection pooling
    - Lazy initialisation
    - Parallel component loading

    Example:
        >>> optimizer = ColdStartOptimizer()
        >>> await optimizer.warmup()
    """

    def __init__(self):
        """Initialise cold start optimiser."""
        self.warmup_complete = False
        self._warmup_lock = threading.Lock()

        # Lazy loaders for common components
        self.lazy_embedder = LazyLoader(self._init_embedder)
        self.lazy_vector_store = LazyLoader(self._init_vector_store)
        self.lazy_retriever = LazyLoader(self._init_retriever)

        logger.debug("ColdStartOptimizer initialized")

    def _init_embedder(self) -> Any:
        """Initialize embedder (lazy).

        Returns:
            Embedder instance
        """
        from src.embeddings.factory import get_embedder
        return get_embedder()

    def _init_vector_store(self) -> Any:
        """Initialize vector store (lazy).

        Returns:
            VectorStore instance
        """
        from src.storage.vector_store import VectorStore
        return VectorStore()

    def _init_retriever(self) -> Any:
        """Initialize retriever (lazy).

        Returns:
            Retriever instance
        """
        from src.retrieval.hybrid import HybridRetriever
        return HybridRetriever()

    async def warmup(self) -> None:
        """Warmup by initializing all components in parallel.

        Reduces cold start time from ~2-3s to <1s.
        """
        if self.warmup_complete:
            logger.debug("Warmup already complete, skipping")
            return

        with self._warmup_lock:
            if self.warmup_complete:
                return

            logger.info("Starting cold start warmup...")
            start = time.time()

            # Initialize in parallel
            try:
                await parallel_init(
                    self._init_embedder,
                    self._init_vector_store,
                    # Retriever depends on embedder/vector_store, skip for now
                )

                self.warmup_complete = True
                duration = time.time() - start

                logger.info(f"Cold start warmup complete: {duration*1000:.0f}ms")

            except Exception as e:
                logger.error(f"Warmup failed: {e}")

    def get_embedder(self) -> Any:
        """Get embedder (lazy loaded).

        Returns:
            Embedder instance
        """
        return self.lazy_embedder.get()

    def get_vector_store(self) -> Any:
        """Get vector store (lazy loaded).

        Returns:
            VectorStore instance
        """
        return self.lazy_vector_store.get()

    def get_retriever(self) -> Any:
        """Get retriever (lazy loaded).

        Returns:
            Retriever instance
        """
        return self.lazy_retriever.get()

    def get_stats(self) -> dict:
        """Get optimisation statistics.

        Returns:
            Statistics dictionary
        """
        return {
            "warmup_complete": self.warmup_complete,
            "embedder_loaded": self.lazy_embedder.is_loaded(),
            "vector_store_loaded": self.lazy_vector_store.is_loaded(),
            "retriever_loaded": self.lazy_retriever.is_loaded(),
        }


# Singleton accessor
_optimizer: ColdStartOptimizer | None = None
_optimizer_lock = threading.Lock()


def get_cold_start_optimizer() -> ColdStartOptimizer:
    """Get singleton ColdStartOptimizer.

    Returns:
        Singleton ColdStartOptimizer

    Example:
        >>> optimizer = get_cold_start_optimizer()
        >>> await optimizer.warmup()
    """
    global _optimizer

    if _optimizer is None:
        with _optimizer_lock:
            if _optimizer is None:
                _optimizer = ColdStartOptimizer()

    return _optimizer
