"""Performance benchmarks for behaviour learning system (v0.4.7)."""

import time
from pathlib import Path
from tempfile import TemporaryDirectory

from ragged.memory.behaviour import create_behaviour_learner
from ragged.memory.interactions import Interaction


def benchmark_topic_extraction():
    """Benchmark topic extraction performance."""
    from ragged.memory.topics import TopicExtractor

    extractor = TopicExtractor()

    queries = [
        "What is RAG?",
        "How does retrieval augmented generation work with vector databases?",
        "Best practices for implementing privacy-preserving RAG systems with embeddings",
        "Latest techniques for improving retrieval accuracy in hybrid search",
    ]

    iterations = 100
    start = time.perf_counter()

    for _ in range(iterations):
        for query in queries:
            extractor.extract_topics(query)

    elapsed = time.perf_counter() - start
    avg_per_query = (elapsed / (iterations * len(queries))) * 1000  # ms

    print(f"Topic Extraction: {avg_per_query:.2f}ms per query (avg over {iterations * len(queries)} queries)")
    return avg_per_query


def benchmark_profile_update():
    """Benchmark profile update performance."""
    with TemporaryDirectory() as tmpdir:
        learner = create_behaviour_learner(Path(tmpdir))

        interactions = [
            Interaction(
                persona="benchmark-user",
                query=f"Query {i} about RAG and vector databases",
                retrieved_doc_ids=[f"doc_{j}.pdf" for j in range(3)]
            )
            for i in range(50)
        ]

        iterations = 10
        start = time.perf_counter()

        for _ in range(iterations):
            for interaction in interactions:
                learner.process_interaction(interaction)

        elapsed = time.perf_counter() - start
        avg_per_interaction = (elapsed / (iterations * len(interactions))) * 1000  # ms

        print(f"Profile Update: {avg_per_interaction:.2f}ms per interaction (avg over {iterations * len(interactions)} interactions)")
        return avg_per_interaction


def benchmark_confidence_calculation():
    """Benchmark confidence calculation performance."""
    from datetime import datetime, timedelta
    from ragged.memory.confidence import ConfidenceCalculator

    calc = ConfidenceCalculator()

    iterations = 1000
    start = time.perf_counter()

    for i in range(iterations):
        calc.calculate_confidence(
            frequency=10 + (i % 50),
            last_seen=datetime.now() - timedelta(days=i % 30),
            first_seen=datetime.now() - timedelta(days=60),
            related_documents=[f"doc_{j}" for j in range(i % 10)],
            timestamps=[datetime.now() - timedelta(days=j) for j in range(i % 20)]
        )

    elapsed = time.perf_counter() - start
    avg_per_calc = (elapsed / iterations) * 1000  # ms

    print(f"Confidence Calculation: {avg_per_calc:.3f}ms per calculation (avg over {iterations} calculations)")
    return avg_per_calc


def benchmark_full_pipeline():
    """Benchmark full interaction processing pipeline."""
    with TemporaryDirectory() as tmpdir:
        from ragged.memory.interactions import InteractionTracker

        learner = create_behaviour_learner(Path(tmpdir) / "memory")
        tracker = InteractionTracker(
            persona="benchmark-user",
            storage_dir=Path(tmpdir) / "interactions",
            behaviour_learner=learner
        )

        queries = [
            "What is RAG?",
            "How does vector search work?",
            "Privacy in machine learning systems",
            "Best practices for embeddings",
        ]

        iterations = 50
        start = time.perf_counter()

        for _ in range(iterations):
            for query in queries:
                tracker.record_interaction(
                    query=query,
                    response="Test response",
                    retrieved_doc_ids=["doc1.pdf", "doc2.pdf"],
                    model_used="test-model",
                    latency_ms=100.0
                )

        elapsed = time.perf_counter() - start
        avg_per_interaction = (elapsed / (iterations * len(queries))) * 1000  # ms

        print(f"Full Pipeline: {avg_per_interaction:.2f}ms per interaction (avg over {iterations * len(queries)} interactions)")
        return avg_per_interaction


if __name__ == "__main__":
    print("=" * 60)
    print("Behaviour Learning Performance Benchmarks (v0.4.7)")
    print("=" * 60)
    print()

    results = {}

    print("Running benchmarks...")
    print()

    results["topic_extraction"] = benchmark_topic_extraction()
    results["profile_update"] = benchmark_profile_update()
    results["confidence_calc"] = benchmark_confidence_calculation()
    results["full_pipeline"] = benchmark_full_pipeline()

    print()
    print("=" * 60)
    print("Summary")
    print("=" * 60)
    print(f"Topic Extraction:        {results['topic_extraction']:.2f}ms")
    print(f"Profile Update:          {results['profile_update']:.2f}ms")
    print(f"Confidence Calculation:  {results['confidence_calc']:.3f}ms")
    print(f"Full Pipeline:           {results['full_pipeline']:.2f}ms")
    print()
    print(f"Estimated overhead per query: ~{results['full_pipeline']:.0f}ms")
    print("=" * 60)
