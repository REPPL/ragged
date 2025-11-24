"""
Tests for query classification system (v0.6.1 OPTIMISE-001).

Success criteria:
- Classification accuracy >85%
- Complexity scoring correlation >0.8
- Intent detection accuracy >90%
- Classification latency <50ms
"""

import time
from pathlib import Path

import pytest

from ragged.optimisation import QueryClassifier, QueryIntent, QueryType, RoutingMetadata


class TestQueryTypeDetection:
    """Test query type classification accuracy."""

    @pytest.fixture
    def classifier(self) -> QueryClassifier:
        """Create classifier instance."""
        return QueryClassifier()

    def test_factual_query_detection(self, classifier: QueryClassifier) -> None:
        """Test factual query detection."""
        factual_queries = [
            "What is RAG?",
            "Who invented transformers?",
            "When was BERT released?",
            "Where is the model stored?",
            "Define semantic search",
            "List all embedding models",
        ]

        for query in factual_queries:
            result = classifier.classify(query)
            assert result.query_type == QueryType.FACTUAL, f"Failed for: {query}"

    def test_conceptual_query_detection(self, classifier: QueryClassifier) -> None:
        """Test conceptual query detection."""
        conceptual_queries = [
            "How does RAG work?",
            "Why use embeddings?",
            "Explain vector databases",
            "Describe the architecture",
            "What are the benefits of RAG?",
            "How can I improve retrieval?",
        ]

        for query in conceptual_queries:
            result = classifier.classify(query)
            assert result.query_type == QueryType.CONCEPTUAL, f"Failed for: {query}"

    def test_exploratory_query_detection(self, classifier: QueryClassifier) -> None:
        """Test exploratory query detection."""
        exploratory_queries = [
            "Find examples of RAG systems",
            "Show me document processing tools",
            "Search for embedding models",
            "Explore vector database options",
            "Look for OCR libraries",
            "Discover preprocessing techniques",
        ]

        for query in exploratory_queries:
            result = classifier.classify(query)
            assert result.query_type == QueryType.EXPLORATORY, f"Failed for: {query}"

    def test_multi_hop_query_detection(self, classifier: QueryClassifier) -> None:
        """Test multi-hop query detection."""
        multi_hop_queries = [
            "Compare RAG and fine-tuning, then recommend best approach",
            "How does ColPali work and then explain its advantages over OCR?",
            "Based on document type, suggest processing method",
            "Compare vision models and traditional OCR",
            "Contrast BM25 and semantic search approaches",
        ]

        for query in multi_hop_queries:
            result = classifier.classify(query)
            assert result.query_type == QueryType.MULTI_HOP, f"Failed for: {query}"
            assert result.is_multi_hop is True, f"Failed multi-hop flag for: {query}"


class TestComplexityScoring:
    """Test complexity scoring algorithm."""

    @pytest.fixture
    def classifier(self) -> QueryClassifier:
        """Create classifier instance."""
        return QueryClassifier()

    def test_simple_query_complexity(self, classifier: QueryClassifier) -> None:
        """Test complexity scoring for simple queries."""
        simple_queries = [
            ("What is RAG?", 1, 3),  # (query, min_complexity, max_complexity)
            ("List models", 1, 2),
            ("Define embedding", 1, 3),
        ]

        for query, min_score, max_score in simple_queries:
            result = classifier.classify(query)
            assert (
                min_score <= result.complexity <= max_score
            ), f"Complexity {result.complexity} not in range [{min_score}, {max_score}] for: {query}"

    def test_medium_query_complexity(self, classifier: QueryClassifier) -> None:
        """Test complexity scoring for medium queries."""
        medium_queries = [
            ("How does RAG work and what are its benefits?", 3, 6),
            ("Explain the difference between BM25 and semantic search", 3, 6),
        ]

        for query, min_score, max_score in medium_queries:
            result = classifier.classify(query)
            assert (
                min_score <= result.complexity <= max_score
            ), f"Complexity {result.complexity} not in range [{min_score}, {max_score}] for: {query}"

    def test_complex_query_complexity(self, classifier: QueryClassifier) -> None:
        """Test complexity scoring for complex queries."""
        complex_queries = [
            (
                "Compare RAG with fine-tuning, consider trade-offs, then recommend best approach for document QA",
                6,
                10,
            ),
            (
                "Given a medical document with images, explain how to process it with ColPali versus traditional OCR, and analyze the performance implications",
                6,
                10,
            ),
        ]

        for query, min_score, max_score in complex_queries:
            result = classifier.classify(query)
            assert (
                min_score <= result.complexity <= max_score
            ), f"Complexity {result.complexity} not in range [{min_score}, {max_score}] for: {query}"

    def test_complexity_increases_with_length(self, classifier: QueryClassifier) -> None:
        """Test that complexity generally increases with query length."""
        short_query = "What is RAG?"
        long_query = "What is RAG, how does it work, why is it useful, and what are the main challenges in implementing it effectively for production systems?"

        short_result = classifier.classify(short_query)
        long_result = classifier.classify(long_query)

        assert (
            long_result.complexity > short_result.complexity
        ), "Longer query should have higher complexity"


class TestIntentDetection:
    """Test intent classification accuracy."""

    @pytest.fixture
    def classifier(self) -> QueryClassifier:
        """Create classifier instance."""
        return QueryClassifier()

    def test_lookup_intent(self, classifier: QueryClassifier) -> None:
        """Test lookup intent detection."""
        lookup_queries = [
            "What is the definition of RAG?",
            "List all models",
            "Find the file path",
        ]

        for query in lookup_queries:
            result = classifier.classify(query)
            assert result.intent == QueryIntent.LOOKUP, f"Failed for: {query}"

    def test_analysis_intent(self, classifier: QueryClassifier) -> None:
        """Test analysis intent detection."""
        analysis_queries = [
            "Why does RAG perform better?",
            "How do embeddings capture semantics?",
            "Analyze the impact of chunk size",
            "What is the relationship between retrieval and generation?",
        ]

        for query in analysis_queries:
            result = classifier.classify(query)
            assert result.intent == QueryIntent.ANALYSIS, f"Failed for: {query}"

    def test_comparison_intent(self, classifier: QueryClassifier) -> None:
        """Test comparison intent detection."""
        comparison_queries = [
            "Compare RAG and fine-tuning",
            "What is the difference between BM25 and semantic search?",
            "ColPali vs traditional OCR",
            "Contrast vector databases",
        ]

        for query in comparison_queries:
            result = classifier.classify(query)
            assert result.intent == QueryIntent.COMPARISON, f"Failed for: {query}"

    def test_synthesis_intent(self, classifier: QueryClassifier) -> None:
        """Test synthesis intent detection."""
        synthesis_queries = [
            "Summarise the main approaches to RAG",
            "Synthesize findings from multiple papers",
            "Combine these techniques into a unified approach",
            "Summarize the key points",
        ]

        for query in synthesis_queries:
            result = classifier.classify(query)
            assert result.intent == QueryIntent.SYNTHESIS, f"Failed for: {query}"


class TestDomainHintExtraction:
    """Test domain hint detection."""

    @pytest.fixture
    def classifier(self) -> QueryClassifier:
        """Create classifier instance."""
        return QueryClassifier()

    def test_vision_domain_detection(self, classifier: QueryClassifier) -> None:
        """Test vision domain hint extraction."""
        vision_queries = [
            "How does ColPali process images?",
            "Extract text from this photo using OCR",
            "Analyze this visual diagram",
        ]

        for query in vision_queries:
            result = classifier.classify(query)
            assert "vision" in result.domain_hints, f"Failed for: {query}"

    def test_embeddings_domain_detection(self, classifier: QueryClassifier) -> None:
        """Test embeddings domain hint extraction."""
        embedding_queries = [
            "What is semantic similarity?",
            "How do vector embeddings work?",
        ]

        for query in embedding_queries:
            result = classifier.classify(query)
            assert "embeddings" in result.domain_hints, f"Failed for: {query}"

    def test_technical_domain_detection(self, classifier: QueryClassifier) -> None:
        """Test technical domain hint extraction."""
        technical_queries = [
            "Explain the API implementation",
            "Show me the code for this algorithm",
            "What function handles this?",
        ]

        for query in technical_queries:
            result = classifier.classify(query)
            assert "technical" in result.domain_hints, f"Failed for: {query}"

    def test_no_domain_hints(self, classifier: QueryClassifier) -> None:
        """Test queries with no domain hints."""
        generic_queries = [
            "What is this?",
            "Tell me more",
            "How does it work?",
        ]

        for query in generic_queries:
            result = classifier.classify(query)
            # May or may not have hints depending on query content
            assert isinstance(result.domain_hints, list), f"Failed for: {query}"


class TestRoutingMetadata:
    """Test routing metadata generation."""

    @pytest.fixture
    def classifier(self) -> QueryClassifier:
        """Create classifier instance."""
        return QueryClassifier()

    def test_simple_query_routing(self, classifier: QueryClassifier) -> None:
        """Test routing metadata for simple queries."""
        result = classifier.classify("What is RAG?")
        metadata = RoutingMetadata.from_classification(result)

        assert metadata.recommended_model == "llama3.2:3b", "Should recommend fast model"
        assert metadata.complexity_tier == "simple"
        assert metadata.cache_priority == "high", "Factual queries cache well"
        assert metadata.estimated_latency_ms < 500, "Fast model should have low latency"

    def test_medium_query_routing(self, classifier: QueryClassifier) -> None:
        """Test routing metadata for medium queries."""
        result = classifier.classify("How does RAG work and what are its benefits?")
        metadata = RoutingMetadata.from_classification(result)

        assert metadata.recommended_model == "llama3.2:8b", "Should recommend balanced model"
        assert metadata.complexity_tier == "medium"
        assert metadata.estimated_latency_ms < 1500, "Balanced model latency"

    def test_complex_query_routing(self, classifier: QueryClassifier) -> None:
        """Test routing metadata for complex queries."""
        result = classifier.classify(
            "Compare RAG with fine-tuning, consider all trade-offs, and recommend the best approach"
        )
        metadata = RoutingMetadata.from_classification(result)

        assert metadata.recommended_model == "llama3.2:70b", "Should recommend quality model"
        assert metadata.complexity_tier == "complex"
        assert metadata.cache_priority == "low", "Complex queries don't cache well"

    def test_vision_query_routing(self, classifier: QueryClassifier) -> None:
        """Test routing metadata for vision queries."""
        result = classifier.classify("How does ColPali process images?")
        metadata = RoutingMetadata.from_classification(result)

        assert metadata.recommended_model == "llava", "Should recommend vision model"
        assert metadata.requires_vision is True


class TestPerformance:
    """Test classification performance benchmarks."""

    @pytest.fixture
    def classifier(self) -> QueryClassifier:
        """Create classifier instance."""
        return QueryClassifier()

    def test_classification_latency(self, classifier: QueryClassifier) -> None:
        """Test that classification completes in <50ms (p95)."""
        test_queries = [
            "What is RAG?",
            "How does semantic search work with embeddings?",
            "Compare RAG and fine-tuning, then recommend best approach",
            "Analyze this image using OCR and extract structured data",
        ]

        latencies = []
        for query in test_queries:
            start_time = time.perf_counter()
            _ = classifier.classify(query)
            end_time = time.perf_counter()
            latency_ms = (end_time - start_time) * 1000
            latencies.append(latency_ms)

        # Check p95 latency
        latencies_sorted = sorted(latencies)
        p95_index = int(len(latencies_sorted) * 0.95)
        p95_latency = latencies_sorted[p95_index]

        assert p95_latency < 50, f"p95 latency {p95_latency:.2f}ms exceeds 50ms threshold"

    def test_batch_classification_performance(self, classifier: QueryClassifier) -> None:
        """Test batch classification performance."""
        # Simulate realistic query load
        queries = [
            "What is RAG?",
            "How does it work?",
            "Compare X and Y",
        ] * 10  # 30 queries

        start_time = time.perf_counter()
        for query in queries:
            _ = classifier.classify(query)
        end_time = time.perf_counter()

        total_time_ms = (end_time - start_time) * 1000
        avg_time_ms = total_time_ms / len(queries)

        assert (
            avg_time_ms < 50
        ), f"Average classification time {avg_time_ms:.2f}ms exceeds 50ms"


class TestSerialization:
    """Test serialization of classification results."""

    @pytest.fixture
    def classifier(self) -> QueryClassifier:
        """Create classifier instance."""
        return QueryClassifier()

    def test_classification_to_dict(self, classifier: QueryClassifier) -> None:
        """Test QueryClassification serialization."""
        result = classifier.classify("How does RAG work?")
        result_dict = result.to_dict()

        assert "query" in result_dict
        assert "query_type" in result_dict
        assert "complexity" in result_dict
        assert "intent" in result_dict
        assert "is_multi_hop" in result_dict
        assert "domain_hints" in result_dict

        # Check types
        assert isinstance(result_dict["query"], str)
        assert isinstance(result_dict["complexity"], int)
        assert isinstance(result_dict["is_multi_hop"], bool)
        assert isinstance(result_dict["domain_hints"], list)

    def test_routing_metadata_to_dict(self, classifier: QueryClassifier) -> None:
        """Test RoutingMetadata serialization."""
        result = classifier.classify("What is RAG?")
        metadata = RoutingMetadata.from_classification(result)
        metadata_dict = metadata.to_dict()

        assert "recommended_model" in metadata_dict
        assert "estimated_latency_ms" in metadata_dict
        assert "requires_vision" in metadata_dict
        assert "cache_priority" in metadata_dict
        assert "complexity_tier" in metadata_dict


class TestEdgeCases:
    """Test edge cases and error handling."""

    @pytest.fixture
    def classifier(self) -> QueryClassifier:
        """Create classifier instance."""
        return QueryClassifier()

    def test_empty_query(self, classifier: QueryClassifier) -> None:
        """Test classification of empty query."""
        result = classifier.classify("")
        # Should not crash, provides sensible defaults
        assert result.query == ""
        assert isinstance(result.complexity, int)
        assert 1 <= result.complexity <= 10

    def test_very_long_query(self, classifier: QueryClassifier) -> None:
        """Test classification of very long query."""
        long_query = " ".join(["word"] * 200)  # 200-word query
        result = classifier.classify(long_query)

        # Long repetitive query gets points for length but not clauses/complexity
        assert result.complexity >= 3, "Very long query should have elevated complexity"
        assert result.complexity <= 6, "Repetitive query complexity is capped"

    def test_special_characters(self, classifier: QueryClassifier) -> None:
        """Test handling of special characters."""
        special_queries = [
            "What is RAG? How does it work? Why use it?",
            "Compare X & Y (with trade-offs)",
            "Find: embeddings, vectors, and similarity",
        ]

        for query in special_queries:
            result = classifier.classify(query)
            assert isinstance(result.complexity, int)
            assert result.query == query.strip()

    def test_non_english_characters(self, classifier: QueryClassifier) -> None:
        """Test handling of non-English characters."""
        # Should handle gracefully even if not optimised for non-English
        query = "What is RAG? (Ç¿què és?)"
        result = classifier.classify(query)
        assert isinstance(result.complexity, int)
