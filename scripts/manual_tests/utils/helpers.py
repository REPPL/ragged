"""
Test helper functions for manual tests.

Provides common setup, teardown, and data generation functions.
"""

import json
import os
import tempfile
import time
from functools import wraps
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

import requests


# ============================================================================
# Service Utilities
# ============================================================================

def wait_for_service(
    service: str,
    timeout: int = 30,
    interval: float = 1.0
) -> bool:
    """
    Wait for a service to become available.

    Args:
        service: Service name ("ollama" or "chromadb")
        timeout: Maximum time to wait in seconds
        interval: Check interval in seconds

    Returns:
        True if service is available, False if timeout

    Example:
        wait_for_service("ollama", timeout=30)
    """
    endpoints = {
        "ollama": "http://localhost:11434/api/tags",
        "chromadb": "http://localhost:8001/api/v1/heartbeat",
    }

    if service not in endpoints:
        raise ValueError(f"Unknown service: {service}")

    endpoint = endpoints[service]
    start_time = time.time()

    while time.time() - start_time < timeout:
        try:
            response = requests.get(endpoint, timeout=5)
            if response.status_code == 200:
                return True
        except requests.exceptions.RequestException:
            pass

        time.sleep(interval)

    return False


def check_service_health(service: str) -> Dict[str, Any]:
    """
    Check service health status.

    Args:
        service: Service name ("ollama" or "chromadb")

    Returns:
        Health status dictionary with keys:
        - status: "healthy" | "unhealthy" | "unknown"
        - details: Additional information

    Example:
        health = check_service_health("ollama")
        assert health["status"] == "healthy"
    """
    endpoints = {
        "ollama": "http://localhost:11434/api/tags",
        "chromadb": "http://localhost:8001/api/v1/heartbeat",
    }

    if service not in endpoints:
        return {"status": "unknown", "details": f"Unknown service: {service}"}

    try:
        response = requests.get(endpoints[service], timeout=5)
        if response.status_code == 200:
            return {
                "status": "healthy",
                "details": "Service is responding",
            }
        else:
            return {
                "status": "unhealthy",
                "details": f"HTTP {response.status_code}",
            }
    except requests.exceptions.RequestException as e:
        return {
            "status": "unhealthy",
            "details": str(e),
        }


# ============================================================================
# Timing and Performance Utilities
# ============================================================================

def measure_time(func: Callable) -> Callable:
    """
    Decorator to measure function execution time.

    Args:
        func: Function to measure

    Returns:
        Wrapped function that prints execution time

    Example:
        @measure_time
        def slow_function():
            time.sleep(1)
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        duration = end_time - start_time
        print(f"{func.__name__} took {duration:.3f} seconds")
        return result
    return wrapper


def benchmark(
    func: Callable,
    iterations: int = 100,
    warmup: int = 10
) -> Dict[str, float]:
    """
    Benchmark a function with multiple iterations.

    Args:
        func: Function to benchmark
        iterations: Number of iterations
        warmup: Number of warmup iterations (not counted)

    Returns:
        Dictionary with timing statistics:
        - mean: Mean execution time
        - p50: 50th percentile (median)
        - p95: 95th percentile
        - p99: 99th percentile

    Example:
        results = benchmark(lambda: ragged.query("test"), iterations=100)
        print(f"Mean: {results['mean']:.3f}s")
    """
    import statistics

    # Warmup
    for _ in range(warmup):
        func()

    # Benchmark
    times = []
    for _ in range(iterations):
        start_time = time.time()
        func()
        end_time = time.time()
        times.append(end_time - start_time)

    times.sort()

    return {
        "mean": statistics.mean(times),
        "p50": times[int(len(times) * 0.50)],
        "p95": times[int(len(times) * 0.95)],
        "p99": times[int(len(times) * 0.99)],
    }


class memory_profile:
    """
    Context manager for profiling memory usage.

    Args:
        label: Label for the profiled operation

    Example:
        with memory_profile("ingestion"):
            ragged.add_documents(docs)
        # Prints: "ingestion: 245.6 MB peak memory"
    """

    def __init__(self, label: str = "operation"):
        self.label = label
        self.start_memory = 0
        self.peak_memory = 0

    def __enter__(self):
        try:
            import psutil
            process = psutil.Process()
            self.start_memory = process.memory_info().rss / 1024 / 1024  # MB
        except ImportError:
            print("Warning: psutil not installed, memory profiling disabled")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        try:
            import psutil
            process = psutil.Process()
            self.peak_memory = process.memory_info().rss / 1024 / 1024  # MB
            print(f"{self.label}: {self.peak_memory:.1f} MB peak memory "
                  f"(+{self.peak_memory - self.start_memory:.1f} MB)")
        except ImportError:
            pass


# ============================================================================
# File Utilities
# ============================================================================

def create_temp_file(content: bytes, suffix: str = ".txt") -> Path:
    """
    Create a temporary file with given content.

    Args:
        content: File content (bytes)
        suffix: File suffix (e.g., ".pdf", ".txt")

    Returns:
        Path to temporary file

    Example:
        temp_file = create_temp_file(pdf_bytes, suffix=".pdf")
        ragged.add(str(temp_file))
    """
    fd, path = tempfile.mkstemp(suffix=suffix, prefix="ragged_test_")
    os.write(fd, content)
    os.close(fd)
    return Path(path)


def cleanup_temp_files():
    """
    Clean up temporary files created by create_temp_file().

    Example:
        cleanup_temp_files()
    """
    temp_dir = tempfile.gettempdir()
    for file in Path(temp_dir).glob("ragged_test_*"):
        try:
            file.unlink()
        except OSError:
            pass


def load_test_data(filename: str) -> Any:
    """
    Load test data from JSON file.

    Args:
        filename: Filename in test_data/ directory

    Returns:
        Loaded data (dict, list, etc.)

    Example:
        docs = load_test_data("sample_documents.json")
    """
    test_data_dir = Path(__file__).parent.parent / "test_data"
    file_path = test_data_dir / filename

    with open(file_path) as f:
        return json.load(f)


def save_test_data(data: Any, filename: str):
    """
    Save test data to JSON file.

    Args:
        data: Data to save
        filename: Filename in test_data/ directory

    Example:
        save_test_data(results, "test_results.json")
    """
    test_data_dir = Path(__file__).parent.parent / "test_data"
    file_path = test_data_dir / filename

    with open(file_path, "w") as f:
        json.dump(data, f, indent=2)


# ============================================================================
# Document Generation Utilities
# ============================================================================

def generate_sample_documents(count: int = 10, formats: Optional[List[str]] = None) -> List[Path]:
    """
    Generate sample documents for testing.

    Args:
        count: Number of documents to generate
        formats: List of formats (["txt", "md", "html"]) or None for all

    Returns:
        List of document paths

    Example:
        docs = generate_sample_documents(count=20, formats=["txt", "md"])
    """
    if formats is None:
        formats = ["txt", "md", "html"]

    temp_dir = Path(tempfile.mkdtemp(prefix="ragged_docs_"))
    docs = []

    for i in range(count):
        format_idx = i % len(formats)
        file_format = formats[format_idx]

        content = f"""
Document {i}

This is sample document number {i}.
It contains information about retrieval-augmented generation
and various testing scenarios.

Key points:
- Point 1: Information retrieval
- Point 2: Language model generation
- Point 3: Context augmentation
"""

        if file_format == "txt":
            file_path = temp_dir / f"document_{i}.txt"
            file_path.write_text(content)
        elif file_format == "md":
            file_path = temp_dir / f"document_{i}.md"
            file_path.write_text(f"# Document {i}\n\n{content}")
        elif file_format == "html":
            file_path = temp_dir / f"document_{i}.html"
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head><title>Document {i}</title></head>
            <body>
            <h1>Document {i}</h1>
            <p>{content}</p>
            </body>
            </html>
            """
            file_path.write_text(html_content)

        docs.append(file_path)

    return docs


def generate_test_queries(
    categories: Optional[List[str]] = None,
    count_per_category: int = 10
) -> Dict[str, List[str]]:
    """
    Generate test queries in different categories.

    Args:
        categories: List of categories (["simple", "complex", "filtered"])
        count_per_category: Number of queries per category

    Returns:
        Dictionary mapping category to list of queries

    Example:
        queries = generate_test_queries(categories=["simple", "complex"], count_per_category=5)
        for query in queries["simple"]:
            results = ragged.query(query)
    """
    if categories is None:
        categories = ["simple", "complex", "filtered"]

    queries = {}

    for category in categories:
        if category == "simple":
            queries[category] = [
                f"What is RAG?",
                f"How does retrieval work?",
                f"Explain embeddings",
                f"What is a vector database?",
                f"Define semantic search",
            ][:count_per_category]
        elif category == "complex":
            queries[category] = [
                f"How do hybrid retrieval systems combine BM25 and vector search?",
                f"What are the trade-offs between different chunking strategies?",
                f"Explain the role of embeddings in semantic search",
                f"How can RAG systems reduce hallucinations?",
                f"What factors affect retrieval quality?",
            ][:count_per_category]
        elif category == "filtered":
            queries[category] = [
                f"Find documents about RAG published after 2023",
                f"Search for papers by author Smith",
                f"Get documents tagged with 'machine learning'",
                f"Find documents in the 'research' category",
                f"Retrieve documents with more than 1000 words",
            ][:count_per_category]

    return queries


# ============================================================================
# Ragged Instance Utilities (to be implemented when ragged is available)
# ============================================================================

# Note: These functions assume ragged can be imported and instantiated
# Uncomment and adapt when ready to use

# def create_test_ragged_instance(config: Optional[Dict] = None):
#     """Create a fresh ragged instance for testing."""
#     from ragged import Ragged
#
#     temp_dir = tempfile.mkdtemp(prefix="ragged_test_")
#
#     if config is None:
#         config = {
#             "data_dir": temp_dir,
#             "chroma_host": "localhost",
#             "chroma_port": 8001,
#         }
#
#     return Ragged(**config)


# def cleanup_test_instance(ragged):
#     """Clean up test ragged instance."""
#     ragged.clear()
#     import shutil
#     if os.path.exists(ragged.data_dir):
#         shutil.rmtree(ragged.data_dir)
