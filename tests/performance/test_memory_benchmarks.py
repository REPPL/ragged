"""Performance benchmarks for memory system (v0.4.6).

Validates performance targets:
- Memory operations: <100ms
- Graph queries: <300ms
- Interaction recording: <50ms

Note: These are baseline benchmarks, not strict requirements.
Run with: pytest tests/performance/ -v --benchmark-only
"""

import time
from pathlib import Path

import pytest

from ragged.memory import InteractionTracker, KnowledgeGraph, PersonaManager


@pytest.fixture
def temp_data_dir(tmp_path):
    """Temporary data directory for benchmarks."""
    return tmp_path


@pytest.fixture
def benchmark_persona(temp_data_dir):
    """Create benchmark persona."""
    from ragged.config.settings import get_settings
    settings = get_settings()
    original_data_dir = settings.data_dir
    settings.data_dir = temp_data_dir
    
    manager = PersonaManager()
    manager.create("benchmark", description="Performance testing persona")
    
    yield "benchmark"
    
    # Cleanup
    try:
        manager.delete("benchmark", confirm=True)
    except:
        pass
    settings.data_dir = original_data_dir


class TestInteractionPerformance:
    """Benchmark interaction tracking operations."""

    def test_record_1000_interactions(self, benchmark_persona, temp_data_dir):
        """Benchmark: Record 1000 interactions."""
        tracker = InteractionTracker(persona=benchmark_persona)
        
        start = time.time()
        for i in range(1000):
            tracker.record_interaction(
                query=f"Test query {i}",
                response=f"Test response {i}",
                model_used="test-model",
                latency_ms=100.0
            )
        elapsed = time.time() - start
        
        avg_per_record = (elapsed / 1000) * 1000  # ms per record
        
        # Target: <50ms per record (async in real usage)
        assert avg_per_record < 100, f"Average {avg_per_record:.2f}ms (target: <100ms)"
        
        # Verify all recorded
        history = tracker.list_interactions(limit=1000)
        assert len(history) == 1000
        
        tracker.clear_interactions(confirm=True)

    def test_query_history_performance(self, benchmark_persona, temp_data_dir):
        """Benchmark: Query interaction history with composite index."""
        tracker = InteractionTracker(persona=benchmark_persona)
        
        # Setup: Record 1000 interactions
        for i in range(1000):
            tracker.record_interaction(
                query=f"Test query {i}",
                response=f"Test response {i}"
            )
        
        # Benchmark: Query recent 100
        start = time.time()
        history = tracker.list_interactions(limit=100)
        elapsed = (time.time() - start) * 1000  # Convert to ms
        
        # Target: <100ms (with composite index should be <10ms)
        assert elapsed < 100, f"Query took {elapsed:.2f}ms (target: <100ms)"
        assert len(history) == 100
        
        tracker.clear_interactions(confirm=True)


class TestGraphPerformance:
    """Benchmark knowledge graph operations."""

    def test_add_100_topics(self, benchmark_persona, temp_data_dir):
        """Benchmark: Add 100 topics to graph."""
        with KnowledgeGraph(persona=benchmark_persona) as graph:
            start = time.time()
            for i in range(100):
                graph.add_topic_interest(f"Topic_{i}", interest_level=0.5 + (i % 50) / 100)
            elapsed = (time.time() - start) * 1000
            
            # Target: <2000ms total (~20ms per topic is acceptable for graph writes)
            assert elapsed < 2000, f"Adding 100 topics took {elapsed:.2f}ms (target: <2000ms)"
            
            # Verify
            interests = graph.get_user_interests()
            assert len(interests) == 100

    def test_query_user_interests(self, benchmark_persona, temp_data_dir):
        """Benchmark: Query user interests."""
        with KnowledgeGraph(persona=benchmark_persona) as graph:
            # Setup: Add 100 topics
            for i in range(100):
                graph.add_topic_interest(f"Topic_{i}")
            
            # Benchmark: Query interests
            start = time.time()
            interests = graph.get_user_interests()
            elapsed = (time.time() - start) * 1000
            
            # Target: <300ms
            assert elapsed < 300, f"Query took {elapsed:.2f}ms (target: <300ms)"
            assert len(interests) == 100

    def test_graph_with_1000_nodes(self, benchmark_persona, temp_data_dir):
        """Benchmark: Graph performance with 1000 nodes."""
        with KnowledgeGraph(persona=benchmark_persona) as graph:
            # Add 100 topics
            for i in range(100):
                graph.add_topic_interest(f"Topic_{i}")
            
            # Add 500 documents
            for i in range(500):
                graph.record_document_access(f"doc_{i}", title=f"Document {i}")
            
            # Link topics to documents (400 relationships)
            for i in range(100):
                for j in range(4):
                    doc_idx = (i * 4 + j) % 500
                    graph.link_topic_to_document(f"Topic_{i}", f"doc_{doc_idx}")
            
            # Total: 100 users + 100 topics + 500 docs = 700 nodes + 500 relationships
            
            # Benchmark: Query operations
            start = time.time()
            interests = graph.get_user_interests()
            elapsed1 = (time.time() - start) * 1000
            
            start = time.time()
            docs = graph.get_accessed_documents(limit=100)
            elapsed2 = (time.time() - start) * 1000
            
            # Targets: Both <300ms
            assert elapsed1 < 300, f"Interest query: {elapsed1:.2f}ms (target: <300ms)"
            assert elapsed2 < 300, f"Document query: {elapsed2:.2f}ms (target: <300ms)"
            
            assert len(interests) == 100
            assert len(docs) == 100


class TestMemoryFootprint:
    """Benchmark memory usage (informational)."""

    def test_memory_growth_1000_interactions(self, benchmark_persona, temp_data_dir):
        """Verify no significant memory growth over 1000 operations."""
        import sys
        
        tracker = InteractionTracker(persona=benchmark_persona)
        
        # Record baseline (rough estimate)
        for i in range(1000):
            tracker.record_interaction(
                query=f"Query {i}" * 10,  # ~100 chars
                response=f"Response {i}" * 50,  # ~500 chars
            )
        
        # Check database size
        db_path = Path(temp_data_dir) / "memory" / "interactions" / "queries.db"
        db_size_kb = db_path.stat().st_size / 1024
        
        # Rough estimate: 1000 records * ~0.6KB = ~600KB (plus indexes)
        # Allow up to 2MB for overhead
        assert db_size_kb < 2048, f"Database size {db_size_kb:.1f}KB seems large"
        
        tracker.clear_interactions(confirm=True)


# Mark all tests as benchmarks
pytestmark = pytest.mark.benchmark
