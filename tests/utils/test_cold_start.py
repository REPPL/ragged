"""Tests for cold start optimisation utilities.

v0.2.9: Tests for connection pooling, lazy loading, and parallel initialization.
"""

import pytest
import asyncio
import time
import threading
from unittest.mock import patch, Mock, MagicMock

from src.utils.cold_start import (
    ChromaDBConnectionPool,
    LazyLoader,
    parallel_init,
    ColdStartOptimizer,
    get_chromadb_pool,
    get_cold_start_optimizer,
)


@pytest.fixture(autouse=True)
def reset_singletons():
    """Reset singleton instances before each test."""
    ChromaDBConnectionPool.reset_instance()
    # Reset optimizer singleton
    import src.utils.cold_start
    src.utils.cold_start._optimizer = None
    yield
    ChromaDBConnectionPool.reset_instance()
    src.utils.cold_start._optimizer = None


@pytest.fixture
def mock_chromadb():
    """Mock chromadb module."""
    with patch('src.utils.cold_start.chromadb') as mock:
        mock_client = Mock()
        mock_client.heartbeat = Mock(return_value=True)
        mock.Client = Mock(return_value=mock_client)
        yield mock


class TestChromaDBConnectionPool:
    """Tests for ChromaDBConnectionPool."""

    def test_initialization(self):
        """Test pool initializes correctly."""
        pool = ChromaDBConnectionPool(pool_size=5)

        assert pool.pool_size == 5
        assert len(pool.connections) == 0
        assert len(pool.in_use) == 0

    def test_singleton_pattern(self):
        """Test singleton pattern works."""
        pool1 = ChromaDBConnectionPool.get_instance()
        pool2 = ChromaDBConnectionPool.get_instance()

        assert pool1 is pool2

    def test_get_singleton_via_function(self):
        """Test get_chromadb_pool() returns singleton."""
        pool1 = get_chromadb_pool()
        pool2 = get_chromadb_pool()

        assert pool1 is pool2

    def test_reset_instance(self, mock_chromadb):
        """Test reset clears singleton."""
        pool1 = ChromaDBConnectionPool.get_instance()
        pool1.get_connection()  # Create a connection

        ChromaDBConnectionPool.reset_instance()

        pool2 = ChromaDBConnectionPool.get_instance()
        assert pool1 is not pool2
        assert len(pool2.connections) == 0

    def test_create_connection(self, mock_chromadb):
        """Test connection creation."""
        pool = ChromaDBConnectionPool()

        conn = pool._create_connection()

        assert conn is not None
        mock_chromadb.Client.assert_called_once()

    def test_get_connection_creates_new(self, mock_chromadb):
        """Test get_connection creates new connection when pool empty."""
        pool = ChromaDBConnectionPool(pool_size=3)

        conn = pool.get_connection()

        assert conn is not None
        assert len(pool.connections) == 1
        assert conn in pool.in_use
        assert conn in pool.connections

    def test_get_connection_reuses_existing(self, mock_chromadb):
        """Test get_connection reuses available connection."""
        pool = ChromaDBConnectionPool(pool_size=3)

        # Get and release a connection
        conn1 = pool.get_connection()
        pool.release_connection(conn1)

        # Get another connection - should reuse
        conn2 = pool.get_connection()

        assert conn2 is conn1
        assert len(pool.connections) == 1

    def test_get_connection_creates_up_to_pool_size(self, mock_chromadb):
        """Test pool creates connections up to pool_size."""
        pool = ChromaDBConnectionPool(pool_size=3)

        conn1 = pool.get_connection()
        conn2 = pool.get_connection()
        conn3 = pool.get_connection()

        assert len(pool.connections) == 3
        assert len(pool.in_use) == 3
        assert conn1 in pool.connections
        assert conn2 in pool.connections
        assert conn3 in pool.connections

    def test_get_connection_exceeds_pool_size(self, mock_chromadb):
        """Test pool creates temporary connection when exhausted."""
        pool = ChromaDBConnectionPool(pool_size=2)

        conn1 = pool.get_connection()
        conn2 = pool.get_connection()
        conn3 = pool.get_connection()  # Exceeds pool size

        # Should have 2 in pool, 3rd is temporary
        assert len(pool.connections) == 2
        assert conn3 not in pool.connections

    def test_release_connection(self, mock_chromadb):
        """Test releasing connection back to pool."""
        pool = ChromaDBConnectionPool()

        conn = pool.get_connection()
        assert conn in pool.in_use

        pool.release_connection(conn)
        assert conn not in pool.in_use

    def test_release_unknown_connection(self, mock_chromadb):
        """Test releasing connection not in pool does nothing."""
        pool = ChromaDBConnectionPool()

        fake_conn = Mock()
        pool.release_connection(fake_conn)  # Should not raise

    def test_context_manager(self, mock_chromadb):
        """Test pool works as context manager."""
        pool = ChromaDBConnectionPool()

        with pool as conn:
            assert conn is not None

        # Connection is temporary (not released back to pool)
        # This is by design as shown in __exit__

    def test_cleanup(self, mock_chromadb):
        """Test cleanup clears all connections."""
        pool = ChromaDBConnectionPool()

        pool.get_connection()
        pool.get_connection()

        pool._cleanup()

        assert len(pool.connections) == 0
        assert len(pool.in_use) == 0

    def test_thread_safety(self, mock_chromadb):
        """Test pool is thread-safe."""
        pool = ChromaDBConnectionPool(pool_size=5)
        connections = []

        def get_conn():
            conn = pool.get_connection()
            connections.append(conn)
            time.sleep(0.01)
            pool.release_connection(conn)

        threads = [threading.Thread(target=get_conn) for _ in range(10)]

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # Should have created multiple connections safely
        assert len(pool.connections) <= 5
        assert len(pool.in_use) == 0  # All released

    def test_connection_creation_failure(self):
        """Test handling of connection creation failure."""
        pool = ChromaDBConnectionPool()

        with patch('src.utils.cold_start.chromadb') as mock_chromadb:
            mock_chromadb.Client.side_effect = Exception("Connection failed")

            with pytest.raises(Exception, match="Connection failed"):
                pool.get_connection()


class TestLazyLoader:
    """Tests for LazyLoader."""

    def test_initialization(self):
        """Test lazy loader initializes correctly."""
        factory = Mock(return_value="test_value")
        loader = LazyLoader(factory)

        assert loader._instance is None
        assert not loader.is_loaded()
        factory.assert_not_called()

    def test_lazy_loading(self):
        """Test instance is created on first get()."""
        factory = Mock(return_value="test_value")
        loader = LazyLoader(factory)

        result = loader.get()

        assert result == "test_value"
        assert loader.is_loaded()
        factory.assert_called_once()

    def test_subsequent_get_reuses_instance(self):
        """Test subsequent get() calls reuse instance."""
        factory = Mock(return_value="test_value")
        loader = LazyLoader(factory)

        result1 = loader.get()
        result2 = loader.get()
        result3 = loader.get()

        assert result1 == result2 == result3 == "test_value"
        factory.assert_called_once()  # Only called once

    def test_reset(self):
        """Test reset forces reload."""
        call_count = 0

        def factory():
            nonlocal call_count
            call_count += 1
            return f"value_{call_count}"

        loader = LazyLoader(factory)

        result1 = loader.get()
        assert result1 == "value_1"

        loader.reset()
        assert not loader.is_loaded()

        result2 = loader.get()
        assert result2 == "value_2"

    def test_thread_safety(self):
        """Test lazy loader is thread-safe."""
        call_count = 0
        lock = threading.Lock()

        def factory():
            nonlocal call_count
            with lock:
                call_count += 1
            time.sleep(0.01)  # Simulate slow initialization
            return "value"

        loader = LazyLoader(factory)
        results = []

        def get_value():
            results.append(loader.get())

        threads = [threading.Thread(target=get_value) for _ in range(10)]

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # Factory should only be called once despite 10 threads
        assert call_count == 1
        assert all(r == "value" for r in results)

    def test_factory_with_timing(self):
        """Test lazy loader logs timing information."""
        def slow_factory():
            time.sleep(0.1)
            return "value"

        loader = LazyLoader(slow_factory)

        start = time.time()
        result = loader.get()
        duration = time.time() - start

        assert result == "value"
        assert duration >= 0.1  # At least as long as factory


class TestParallelInit:
    """Tests for parallel_init function."""

    @pytest.mark.asyncio
    async def test_parallel_init_single_function(self):
        """Test parallel init with single function."""
        def init_func():
            return "result"

        results = await parallel_init(init_func)

        assert len(results) == 1
        assert results[0] == "result"

    @pytest.mark.asyncio
    async def test_parallel_init_multiple_functions(self):
        """Test parallel init with multiple functions."""
        def init_func1():
            return "result1"

        def init_func2():
            return "result2"

        def init_func3():
            return "result3"

        results = await parallel_init(init_func1, init_func2, init_func3)

        assert len(results) == 3
        assert results[0] == "result1"
        assert results[1] == "result2"
        assert results[2] == "result3"

    @pytest.mark.asyncio
    async def test_parallel_init_runs_concurrently(self):
        """Test functions run concurrently, not sequentially."""
        execution_times = []

        def slow_init(duration):
            start = time.time()
            time.sleep(duration)
            execution_times.append(time.time() - start)
            return f"result_{duration}"

        start = time.time()
        results = await parallel_init(
            lambda: slow_init(0.1),
            lambda: slow_init(0.1),
            lambda: slow_init(0.1),
        )
        total_duration = time.time() - start

        # If sequential: 0.3s, if parallel: ~0.1s
        assert total_duration < 0.2  # Should be closer to 0.1
        assert len(results) == 3

    @pytest.mark.asyncio
    async def test_parallel_init_with_exceptions(self):
        """Test parallel init handles exceptions."""
        def good_func():
            return "success"

        def bad_func():
            raise ValueError("Test error")

        results = await parallel_init(good_func, bad_func)

        assert len(results) == 2
        assert results[0] == "success"
        assert isinstance(results[1], ValueError)
        assert str(results[1]) == "Test error"

    @pytest.mark.asyncio
    async def test_parallel_init_all_exceptions(self):
        """Test parallel init when all functions raise."""
        def bad_func1():
            raise ValueError("Error 1")

        def bad_func2():
            raise RuntimeError("Error 2")

        results = await parallel_init(bad_func1, bad_func2)

        assert len(results) == 2
        assert isinstance(results[0], ValueError)
        assert isinstance(results[1], RuntimeError)


class TestColdStartOptimizer:
    """Tests for ColdStartOptimizer."""

    def test_initialization(self):
        """Test optimizer initializes correctly."""
        optimizer = ColdStartOptimizer()

        assert optimizer.warmup_complete is False
        assert optimizer.lazy_embedder is not None
        assert optimizer.lazy_vector_store is not None
        assert optimizer.lazy_retriever is not None
        assert not optimizer.lazy_embedder.is_loaded()
        assert not optimizer.lazy_vector_store.is_loaded()
        assert not optimizer.lazy_retriever.is_loaded()

    def test_singleton_pattern(self):
        """Test optimizer singleton."""
        opt1 = get_cold_start_optimizer()
        opt2 = get_cold_start_optimizer()

        assert opt1 is opt2

    @pytest.mark.asyncio
    async def test_warmup(self):
        """Test warmup initializes components."""
        optimizer = ColdStartOptimizer()

        with patch.object(optimizer, '_init_embedder', return_value=Mock()):
            with patch.object(optimizer, '_init_vector_store', return_value=Mock()):
                await optimizer.warmup()

        assert optimizer.warmup_complete is True

    @pytest.mark.asyncio
    async def test_warmup_idempotent(self):
        """Test warmup can be called multiple times safely."""
        optimizer = ColdStartOptimizer()
        call_count = 0

        def mock_init():
            nonlocal call_count
            call_count += 1
            return Mock()

        with patch.object(optimizer, '_init_embedder', side_effect=mock_init):
            with patch.object(optimizer, '_init_vector_store', side_effect=mock_init):
                await optimizer.warmup()
                await optimizer.warmup()  # Second call

        # Should only initialize once
        assert call_count == 2  # embedder + vector_store

    def test_get_embedder(self):
        """Test get_embedder returns lazy-loaded embedder."""
        optimizer = ColdStartOptimizer()

        with patch.object(optimizer, '_init_embedder', return_value=Mock(name="embedder")):
            embedder = optimizer.get_embedder()

        assert embedder is not None
        assert optimizer.lazy_embedder.is_loaded()

    def test_get_vector_store(self):
        """Test get_vector_store returns lazy-loaded vector store."""
        optimizer = ColdStartOptimizer()

        with patch.object(optimizer, '_init_vector_store', return_value=Mock(name="vector_store")):
            vector_store = optimizer.get_vector_store()

        assert vector_store is not None
        assert optimizer.lazy_vector_store.is_loaded()

    def test_get_retriever(self):
        """Test get_retriever returns lazy-loaded retriever."""
        optimizer = ColdStartOptimizer()

        with patch.object(optimizer, '_init_retriever', return_value=Mock(name="retriever")):
            retriever = optimizer.get_retriever()

        assert retriever is not None
        assert optimizer.lazy_retriever.is_loaded()

    def test_get_stats(self):
        """Test get_stats returns current state."""
        optimizer = ColdStartOptimizer()

        stats = optimizer.get_stats()

        assert stats["warmup_complete"] is False
        assert stats["embedder_loaded"] is False
        assert stats["vector_store_loaded"] is False
        assert stats["retriever_loaded"] is False

    def test_get_stats_after_warmup(self):
        """Test get_stats after warmup."""
        optimizer = ColdStartOptimizer()

        with patch.object(optimizer, '_init_embedder', return_value=Mock()):
            with patch.object(optimizer, '_init_vector_store', return_value=Mock()):
                asyncio.run(optimizer.warmup())

        stats = optimizer.get_stats()

        assert stats["warmup_complete"] is True

    def test_init_embedder(self):
        """Test _init_embedder loads embedder."""
        optimizer = ColdStartOptimizer()

        with patch('src.utils.cold_start.get_embedder', return_value=Mock(name="embedder")):
            embedder = optimizer._init_embedder()

        assert embedder is not None

    def test_init_vector_store(self):
        """Test _init_vector_store loads vector store."""
        optimizer = ColdStartOptimizer()

        with patch('src.utils.cold_start.VectorStore', return_value=Mock(name="vector_store")):
            vector_store = optimizer._init_vector_store()

        assert vector_store is not None

    def test_init_retriever(self):
        """Test _init_retriever loads retriever."""
        optimizer = ColdStartOptimizer()

        with patch('src.utils.cold_start.HybridRetriever', return_value=Mock(name="retriever")):
            retriever = optimizer._init_retriever()

        assert retriever is not None

    @pytest.mark.asyncio
    async def test_warmup_exception_handling(self):
        """Test warmup handles exceptions gracefully."""
        optimizer = ColdStartOptimizer()

        def failing_init():
            raise RuntimeError("Init failed")

        with patch.object(optimizer, '_init_embedder', side_effect=failing_init):
            with patch.object(optimizer, '_init_vector_store', return_value=Mock()):
                await optimizer.warmup()

        # Should not crash, warmup_complete may be False
        assert optimizer.warmup_complete is False


class TestIntegrationScenarios:
    """Integration tests for realistic scenarios."""

    @pytest.mark.asyncio
    async def test_complete_cold_start_workflow(self, mock_chromadb):
        """Test complete cold start optimization workflow."""
        # 1. Get optimizer singleton
        optimizer = get_cold_start_optimizer()

        # 2. Warmup in background
        with patch.object(optimizer, '_init_embedder', return_value=Mock()):
            with patch.object(optimizer, '_init_vector_store', return_value=Mock()):
                await optimizer.warmup()

        # 3. Get ChromaDB connection
        pool = get_chromadb_pool()
        conn = pool.get_connection()
        assert conn is not None

        # 4. Get lazy-loaded components
        embedder = optimizer.get_embedder()
        vector_store = optimizer.get_vector_store()

        assert embedder is not None
        assert vector_store is not None

        # 5. Check stats
        stats = optimizer.get_stats()
        assert stats["warmup_complete"] is True

    def test_lazy_loading_pattern(self):
        """Test lazy loading reduces initial overhead."""
        optimizer = ColdStartOptimizer()

        # Initially nothing loaded
        stats = optimizer.get_stats()
        assert stats["embedder_loaded"] is False

        # Load on demand
        with patch.object(optimizer, '_init_embedder', return_value=Mock()):
            embedder = optimizer.get_embedder()

        # Now loaded
        stats = optimizer.get_stats()
        assert stats["embedder_loaded"] is True

    @pytest.mark.asyncio
    async def test_parallel_vs_sequential_timing(self):
        """Test parallel init is faster than sequential."""
        def slow_init_1():
            time.sleep(0.05)
            return "result1"

        def slow_init_2():
            time.sleep(0.05)
            return "result2"

        # Sequential
        start = time.time()
        r1 = slow_init_1()
        r2 = slow_init_2()
        sequential_duration = time.time() - start

        # Parallel
        start = time.time()
        results = await parallel_init(slow_init_1, slow_init_2)
        parallel_duration = time.time() - start

        # Parallel should be faster
        assert parallel_duration < sequential_duration
        assert parallel_duration < 0.08  # ~0.05s, not 0.10s
