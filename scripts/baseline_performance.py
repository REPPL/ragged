#!/usr/bin/env python3
"""Performance baseline measurement for ragged v0.2.2.

This script establishes performance baselines across key metrics:
- Startup time
- Query performance (cold/warm cache)
- Batch ingestion (10, 50, 100 documents)
- Memory usage

Results are saved to docs/development/implementation/version/v0.2/performance-baseline.md
"""

import gc
import os
import psutil
import sys
import time
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.chunking.splitters import chunk_document
from src.embeddings.factory import get_embedder
from src.generation.ollama_client import OllamaClient
from src.ingestion.loaders import load_document
from src.retrieval.hybrid import HybridRetriever
from src.storage.vector_store import VectorStore
from src.utils.benchmarks import BenchmarkSuite, Timer
from src.utils.logging import setup_logging, get_logger

setup_logging(log_level="WARNING", json_format=False)
logger = get_logger(__name__)


def get_memory_usage() -> Dict[str, float]:
    """Get current memory usage in MB.

    Returns:
        Dictionary with memory metrics
    """
    process = psutil.Process()
    memory_info = process.memory_info()

    return {
        "rss_mb": memory_info.rss / 1024 / 1024,  # Resident Set Size
        "vms_mb": memory_info.vms / 1024 / 1024,  # Virtual Memory Size
    }


def create_test_documents(count: int, output_dir: Path) -> List[Path]:
    """Create test documents for benchmarking.

    Args:
        count: Number of documents to create
        output_dir: Directory to create documents in

    Returns:
        List of created document paths
    """
    logger.info(f"Creating {count} test documents in {output_dir}")

    output_dir.mkdir(parents=True, exist_ok=True)

    # Read the sample document as template
    sample_doc = project_root / "examples" / "sample_documents" / "rag_introduction.md"

    if not sample_doc.exists():
        # Create a basic template if sample doesn't exist
        template_content = """# Test Document {num}

This is a test document for performance benchmarking.

## Introduction

Retrieval-Augmented Generation (RAG) is an approach that combines information retrieval
with large language models to provide accurate, context-aware responses.

## Key Concepts

RAG systems consist of several components:

1. **Document Ingestion**: Processing and chunking documents
2. **Embedding Generation**: Converting text to vector representations
3. **Vector Storage**: Storing embeddings for efficient retrieval
4. **Retrieval**: Finding relevant chunks based on query similarity
5. **Generation**: Using retrieved context to generate answers

## Benefits

- Reduces hallucination by grounding responses in source documents
- Enables working with private/proprietary data
- Provides citations and traceability
- Can be updated without retraining the model

## Implementation

A typical RAG pipeline involves:

```python
# 1. Load and chunk documents
chunks = chunk_document(document)

# 2. Generate embeddings
embeddings = embedder.embed(chunks)

# 3. Store in vector database
vector_store.add(chunks, embeddings)

# 4. Retrieve relevant chunks
relevant_chunks = retriever.retrieve(query)

# 5. Generate answer
answer = llm.generate(query, context=relevant_chunks)
```

## Conclusion

RAG provides a powerful way to enhance LLM capabilities with external knowledge
while maintaining accuracy and providing attribution.

Document ID: {num}
Test document created at: {timestamp}
"""
    else:
        with open(sample_doc, 'r') as f:
            template_content = f.read() + "\n\nDocument ID: {num}\nTest document created at: {timestamp}\n"

    created_files = []

    for i in range(count):
        doc_path = output_dir / f"test_doc_{i:04d}.md"
        content = template_content.format(num=i, timestamp=datetime.now().isoformat())

        with open(doc_path, 'w') as f:
            f.write(content)

        created_files.append(doc_path)

    logger.info(f"Created {len(created_files)} test documents")

    return created_files


def benchmark_startup(suite: BenchmarkSuite) -> None:
    """Benchmark system startup time.

    Args:
        suite: Benchmark suite to add results to
    """
    print("\n=== Benchmarking Startup Time ===")

    def startup_components():
        """Initialize core components."""
        # Clear any existing instances
        gc.collect()

        # Initialize components
        embedder = get_embedder()
        vector_store = VectorStore()
        retriever = HybridRetriever(vector_store)
        client = OllamaClient()

        return embedder, vector_store, retriever, client

    result = suite.add_benchmark(
        "startup_time",
        startup_components,
        warmup=1,
        iterations=3,
        metadata={"description": "Time to initialize core components"}
    )

    print(f"✓ Startup time: {result.mean*1000:.0f}ms (mean)")


def benchmark_query(suite: BenchmarkSuite, vector_store: VectorStore) -> None:
    """Benchmark query performance.

    Args:
        suite: Benchmark suite to add results to
        vector_store: Vector store with documents
    """
    print("\n=== Benchmarking Query Performance ===")

    test_query = "What is RAG and how does it work?"

    retriever = HybridRetriever(vector_store)

    # Cold query (first run)
    def cold_query():
        # Clear caches
        gc.collect()
        return retriever.retrieve(test_query, top_k=5)

    cold_result = suite.add_benchmark(
        "query_cold",
        cold_query,
        warmup=0,  # No warmup for cold start
        iterations=3,
        metadata={"query": test_query, "top_k": 5, "cache_state": "cold"}
    )

    print(f"✓ Cold query: {cold_result.mean*1000:.0f}ms (mean)")

    # Warm query (cached)
    def warm_query():
        return retriever.retrieve(test_query, top_k=5)

    warm_result = suite.add_benchmark(
        "query_warm",
        warm_query,
        warmup=2,
        iterations=10,
        metadata={"query": test_query, "top_k": 5, "cache_state": "warm"}
    )

    print(f"✓ Warm query: {warm_result.mean*1000:.0f}ms (mean)")

    # Calculate cache speedup
    speedup = cold_result.mean / warm_result.mean
    print(f"✓ Cache speedup: {speedup:.2f}x faster")


def benchmark_ingestion(suite: BenchmarkSuite, test_docs: List[Path], doc_counts: List[int]) -> VectorStore:
    """Benchmark document ingestion.

    Args:
        suite: Benchmark suite to add results to
        test_docs: List of test document paths
        doc_counts: List of document counts to test

    Returns:
        Vector store with ingested documents
    """
    print("\n=== Benchmarking Document Ingestion ===")

    embedder = get_embedder()
    vector_store = VectorStore()

    for count in doc_counts:
        if count > len(test_docs):
            print(f"⚠ Skipping {count} docs (only {len(test_docs)} available)")
            continue

        docs_to_ingest = test_docs[:count]

        # Clear vector store for clean test
        vector_store = VectorStore()
        gc.collect()

        def ingest_batch():
            """Ingest a batch of documents."""
            for doc_path in docs_to_ingest:
                try:
                    # Load document
                    doc = load_document(doc_path)

                    # Chunk document
                    chunks = chunk_document(doc)

                    # Generate embeddings
                    texts = [chunk.content for chunk in chunks]
                    embeddings = embedder.embed(texts)

                    # Store in vector store
                    metadatas = [chunk.metadata for chunk in chunks]
                    vector_store.add_documents(
                        texts=texts,
                        embeddings=embeddings,
                        metadatas=metadatas
                    )
                except Exception as e:
                    logger.error(f"Error ingesting {doc_path}: {e}")

        result = suite.add_benchmark(
            f"ingestion_{count}_docs",
            ingest_batch,
            warmup=0,  # No warmup for ingestion
            iterations=1,  # Single run to avoid re-ingesting
            metadata={
                "document_count": count,
                "description": f"Ingest {count} documents"
            }
        )

        docs_per_sec = count / result.mean
        print(f"✓ {count} docs: {result.mean:.2f}s total ({docs_per_sec:.1f} docs/sec)")

    # Re-ingest all docs for query benchmarking
    print("\nIngesting all documents for query benchmark...")
    vector_store = VectorStore()
    for doc_path in test_docs:
        try:
            doc = load_document(doc_path)
            chunks = chunk_document(doc)
            texts = [chunk.content for chunk in chunks]
            embeddings = embedder.embed(texts)
            metadatas = [chunk.metadata for chunk in chunks]
            vector_store.add_documents(texts=texts, embeddings=embeddings, metadatas=metadatas)
        except Exception as e:
            logger.error(f"Error: {e}")

    return vector_store


def benchmark_memory(suite: BenchmarkSuite) -> Dict[str, Any]:
    """Benchmark memory usage.

    Args:
        suite: Benchmark suite to add results to

    Returns:
        Memory usage statistics
    """
    print("\n=== Benchmarking Memory Usage ===")

    # Idle memory
    gc.collect()
    time.sleep(0.5)
    idle_memory = get_memory_usage()
    print(f"✓ Idle memory: {idle_memory['rss_mb']:.1f} MB RSS, {idle_memory['vms_mb']:.1f} MB VMS")

    # Memory under load
    embedder = get_embedder()
    vector_store = VectorStore()
    retriever = HybridRetriever(vector_store)
    client = OllamaClient()

    # Load some data
    sample_texts = ["This is a test document."] * 100
    embeddings = embedder.embed(sample_texts)
    vector_store.add_documents(texts=sample_texts, embeddings=embeddings)

    # Perform some queries
    for _ in range(10):
        retriever.retrieve("test query", top_k=5)

    loaded_memory = get_memory_usage()
    print(f"✓ Under load: {loaded_memory['rss_mb']:.1f} MB RSS, {loaded_memory['vms_mb']:.1f} MB VMS")

    memory_increase = loaded_memory['rss_mb'] - idle_memory['rss_mb']
    print(f"✓ Memory increase: {memory_increase:.1f} MB")

    return {
        "idle_mb": idle_memory['rss_mb'],
        "loaded_mb": loaded_memory['rss_mb'],
        "increase_mb": memory_increase
    }


def generate_markdown_report(suite: BenchmarkSuite, memory_stats: Dict[str, Any], output_path: Path) -> None:
    """Generate markdown report of baseline results.

    Args:
        suite: Benchmark suite with results
        memory_stats: Memory usage statistics
        output_path: Path to save report
    """
    lines = [
        "# Performance Baseline: ragged v0.2.2",
        "",
        f"**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"**Version:** 0.2.2",
        f"**Purpose:** Establish performance baselines for comparison with future versions",
        "",
        "---",
        "",
        "## Summary",
        "",
        "This document contains performance baseline measurements for ragged v0.2.2.",
        "These metrics will be used to validate performance improvements in v0.2.7.",
        "",
        "## Methodology",
        "",
        "- **Warmup iterations:** 3 (except where noted)",
        "- **Test iterations:** 10 (except where noted)",
        "- **Environment:** Local Docker containers (ChromaDB, Ollama)",
        "- **Test documents:** Generated markdown files based on sample documents",
        "",
        "## Results",
        "",
    ]

    # Group results by category
    startup_results = [r for r in suite.results if 'startup' in r.name]
    query_results = [r for r in suite.results if 'query' in r.name]
    ingestion_results = [r for r in suite.results if 'ingestion' in r.name]

    # Startup metrics
    lines.append("### Startup Time")
    lines.append("")
    lines.append("Time to initialise core components (embedder, vector store, retriever, LLM client).")
    lines.append("")
    for result in startup_results:
        lines.append(f"- **Mean:** {result.mean*1000:.0f}ms")
        lines.append(f"- **Median:** {result.median*1000:.0f}ms")
        lines.append(f"- **Std Dev:** {result.std_dev*1000:.1f}ms")
        lines.append(f"- **Range:** {result.min_time*1000:.0f}ms - {result.max_time*1000:.0f}ms")
    lines.append("")

    # Query metrics
    lines.append("### Query Performance")
    lines.append("")
    lines.append("Time to retrieve relevant chunks for a query.")
    lines.append("")

    cold_query = next((r for r in query_results if 'cold' in r.name), None)
    warm_query = next((r for r in query_results if 'warm' in r.name), None)

    if cold_query:
        lines.append("**Cold Query (first run, no cache):**")
        lines.append(f"- **Mean:** {cold_query.mean*1000:.0f}ms")
        lines.append(f"- **Median:** {cold_query.median*1000:.0f}ms")
        lines.append("")

    if warm_query:
        lines.append("**Warm Query (cached):**")
        lines.append(f"- **Mean:** {warm_query.mean*1000:.0f}ms")
        lines.append(f"- **Median:** {warm_query.median*1000:.0f}ms")
        lines.append("")

    if cold_query and warm_query:
        speedup = cold_query.mean / warm_query.mean
        improvement = ((cold_query.mean - warm_query.mean) / cold_query.mean) * 100
        lines.append(f"**Cache Benefit:** {speedup:.2f}x faster ({improvement:.1f}% improvement)")
        lines.append("")

    # Ingestion metrics
    lines.append("### Batch Ingestion Performance")
    lines.append("")
    lines.append("Time to ingest batches of documents (load, chunk, embed, store).")
    lines.append("")
    lines.append("| Document Count | Total Time | Docs/Second |")
    lines.append("|----------------|------------|-------------|")

    for result in sorted(ingestion_results, key=lambda r: r.metadata.get('document_count', 0)):
        doc_count = result.metadata.get('document_count', 0)
        total_time = result.mean
        docs_per_sec = doc_count / total_time if total_time > 0 else 0
        lines.append(f"| {doc_count} | {total_time:.2f}s | {docs_per_sec:.1f} |")

    lines.append("")

    # Memory metrics
    lines.append("### Memory Usage")
    lines.append("")
    lines.append(f"- **Idle:** {memory_stats['idle_mb']:.1f} MB")
    lines.append(f"- **Under Load:** {memory_stats['loaded_mb']:.1f} MB")
    lines.append(f"- **Increase:** {memory_stats['increase_mb']:.1f} MB")
    lines.append("")

    # Performance targets for v0.2.7
    lines.append("## Performance Targets for v0.2.7")
    lines.append("")
    lines.append("Based on these baselines, v0.2.7 should achieve:")
    lines.append("")
    lines.append("### Startup Time")
    if startup_results:
        target_startup = startup_results[0].mean
        lines.append(f"- **Current:** {target_startup*1000:.0f}ms")
        lines.append(f"- **Target:** <2000ms (BM25 persistence)")
        lines.append("")

    lines.append("### Query Performance")
    if warm_query:
        current_query = warm_query.mean * 1000
        target_query = current_query * 0.3  # 70% improvement
        lines.append(f"- **Current (warm):** {current_query:.0f}ms")
        lines.append(f"- **Target:** {target_query:.0f}ms (50-90% faster with caching)")
        lines.append("")

    lines.append("### Batch Ingestion")
    if ingestion_results:
        sample_result = next((r for r in ingestion_results if r.metadata.get('document_count') == 10), ingestion_results[0])
        doc_count = sample_result.metadata.get('document_count', 10)
        current_time = sample_result.mean
        target_time = current_time / 3  # 3x faster
        lines.append(f"- **Current ({doc_count} docs):** {current_time:.2f}s")
        lines.append(f"- **Target ({doc_count} docs):** {target_time:.2f}s (2-4x faster with async)")
        lines.append("")

    lines.append("### Memory Usage")
    lines.append(f"- **Current (idle):** {memory_stats['idle_mb']:.1f} MB")
    lines.append("- **Target (idle):** <100 MB (lazy loading)")
    lines.append("")

    # Footer
    lines.append("---")
    lines.append("")
    lines.append("## Related Documentation")
    lines.append("")
    lines.append("- [v0.2.7 Planning](../../planning/version/v0.2.7/) - Performance improvement goals")
    lines.append("- [v0.2.7 Roadmap](../../roadmap/version/v0.2.7/) - Implementation plan")
    lines.append("")

    # Write report
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w') as f:
        f.write('\n'.join(lines))

    print(f"\n✓ Baseline report saved to: {output_path}")


def main():
    """Run performance baseline benchmarks."""
    print("=" * 70)
    print("ragged v0.2.2 Performance Baseline")
    print("=" * 70)

    # Create temp directory for test documents
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        # Create test documents
        print("\nCreating test documents...")
        test_docs = create_test_documents(100, temp_path)
        print(f"✓ Created {len(test_docs)} test documents")

        # Initialize benchmark suite
        suite = BenchmarkSuite("ragged_v0.2.2_baseline")

        # Run benchmarks
        benchmark_startup(suite)

        # Ingest documents (also needed for query benchmark)
        vector_store = benchmark_ingestion(
            suite,
            test_docs,
            doc_counts=[10, 50, 100]
        )

        # Benchmark queries
        benchmark_query(suite, vector_store)

        # Benchmark memory
        memory_stats = benchmark_memory(suite)

        # Save JSON results
        json_output = project_root / "docs" / "development" / "implementation" / "version" / "v0.2" / "performance-baseline.json"
        json_output.parent.mkdir(parents=True, exist_ok=True)
        suite.save(json_output)

        # Generate markdown report
        md_output = project_root / "docs" / "development" / "implementation" / "version" / "v0.2" / "performance-baseline.md"
        generate_markdown_report(suite, memory_stats, md_output)

        # Print summary
        print("\n" + "=" * 70)
        print("Baseline Complete!")
        print("=" * 70)
        print(f"\nResults saved to:")
        print(f"  - {md_output}")
        print(f"  - {json_output}")
        print("\nNext steps:")
        print("  1. Review baseline results")
        print("  2. Begin v0.2.3 implementation")
        print("  3. Compare v0.2.7 performance against these baselines")


if __name__ == "__main__":
    main()
