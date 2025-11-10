"""Tests for few-shot example storage and retrieval."""

import pytest
import tempfile
from pathlib import Path
from src.generation.few_shot import (
    FewShotExample,
    FewShotExampleStore,
    seed_default_examples,
    format_few_shot_prompt
)


class TestFewShotExample:
    """Test FewShotExample dataclass."""

    def test_create_example(self):
        """Test creating a few-shot example."""
        example = FewShotExample(
            query="What is AI?",
            context="AI is artificial intelligence...",
            answer="AI stands for artificial intelligence.",
            category="definition",
            tags=["AI", "basics"]
        )

        assert example.query == "What is AI?"
        assert example.category == "definition"
        assert len(example.tags) == 2

    def test_to_dict(self):
        """Test converting example to dict."""
        example = FewShotExample(
            query="Test query",
            context="Test context",
            answer="Test answer"
        )

        data = example.to_dict()

        assert data["query"] == "Test query"
        assert data["context"] == "Test context"
        assert data["answer"] == "Test answer"

    def test_from_dict(self):
        """Test creating example from dict."""
        data = {
            "query": "Query here",
            "context": "Context here",
            "answer": "Answer here",
            "category": "test",
            "tags": ["tag1", "tag2"]
        }

        example = FewShotExample.from_dict(data)

        assert example.query == "Query here"
        assert example.category == "test"
        assert len(example.tags) == 2

    def test_to_prompt_format(self):
        """Test formatting example for prompting."""
        example = FewShotExample(
            query="What is ML?",
            context="ML is machine learning.",
            answer="ML stands for machine learning."
        )

        formatted = example.to_prompt_format()

        assert "Query: What is ML?" in formatted
        assert "Context:" in formatted
        assert "Answer: ML stands for machine learning." in formatted


class TestFewShotExampleStore:
    """Test FewShotExampleStore."""

    @pytest.fixture
    def temp_storage(self):
        """Temporary storage path."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir) / "examples.json"

    @pytest.fixture
    def store(self, temp_storage):
        """Empty example store."""
        return FewShotExampleStore(storage_path=temp_storage)

    def test_init_empty(self, store):
        """Test initializing empty store."""
        assert len(store.get_all_examples()) == 0

    def test_add_example(self, store):
        """Test adding an example."""
        example = store.add_example(
            query="Test query",
            context="Test context",
            answer="Test answer",
            category="test"
        )

        assert isinstance(example, FewShotExample)
        assert len(store.get_all_examples()) == 1

    def test_add_multiple_examples(self, store):
        """Test adding multiple examples."""
        store.add_example("Q1", "C1", "A1")
        store.add_example("Q2", "C2", "A2")
        store.add_example("Q3", "C3", "A3")

        assert len(store.get_all_examples()) == 3

    def test_save_and_load(self, temp_storage):
        """Test saving and loading examples."""
        # Create store and add examples
        store1 = FewShotExampleStore(storage_path=temp_storage)
        store1.add_example("Query 1", "Context 1", "Answer 1")
        store1.add_example("Query 2", "Context 2", "Answer 2")

        # Create new store instance (should load saved examples)
        store2 = FewShotExampleStore(storage_path=temp_storage)

        assert len(store2.get_all_examples()) == 2
        assert store2.get_all_examples()[0].query == "Query 1"

    def test_get_by_category(self, store):
        """Test getting examples by category."""
        store.add_example("Q1", "C1", "A1", category="definition")
        store.add_example("Q2", "C2", "A2", category="comparison")
        store.add_example("Q3", "C3", "A3", category="definition")

        definitions = store.get_by_category("definition")

        assert len(definitions) == 2
        assert all(ex.category == "definition" for ex in definitions)

    def test_get_by_tags(self, store):
        """Test getting examples by tags."""
        store.add_example("Q1", "C1", "A1", tags=["AI", "ML"])
        store.add_example("Q2", "C2", "A2", tags=["NLP"])
        store.add_example("Q3", "C3", "A3", tags=["AI", "vision"])

        ai_examples = store.get_by_tags(["AI"])

        assert len(ai_examples) == 2

    def test_search_similar(self, store):
        """Test searching for similar examples."""
        store.add_example("What is machine learning?", "ML context", "ML answer")
        store.add_example("What is deep learning?", "DL context", "DL answer")
        store.add_example("What is Python?", "Python context", "Python answer")

        # Search for machine learning question
        results = store.search_similar("machine learning applications", top_k=2)

        assert len(results) <= 2
        # Should find the ML example as most similar
        assert "machine learning" in results[0].query.lower()

    def test_search_similar_with_category(self, store):
        """Test searching with category filter."""
        store.add_example("Q1", "C1", "A1", category="definition")
        store.add_example("Q2", "C2", "A2", category="comparison")

        results = store.search_similar("test query", category="definition")

        assert all(ex.category == "definition" for ex in results)

    def test_search_similar_empty_store(self, store):
        """Test searching in empty store."""
        results = store.search_similar("test query")

        assert results == []

    def test_clear(self, store):
        """Test clearing all examples."""
        store.add_example("Q1", "C1", "A1")
        store.add_example("Q2", "C2", "A2")

        assert len(store.get_all_examples()) == 2

        store.clear()

        assert len(store.get_all_examples()) == 0


class TestSeedDefaultExamples:
    """Test seeding default examples."""

    def test_seed_default_examples(self, tmp_path):
        """Test seeding with default examples."""
        storage_path = tmp_path / "examples.json"
        store = FewShotExampleStore(storage_path=storage_path)

        assert len(store.get_all_examples()) == 0

        seed_default_examples(store)

        # Should have added default examples
        assert len(store.get_all_examples()) > 0

        # Check examples have required fields
        for example in store.get_all_examples():
            assert example.query
            assert example.context
            assert example.answer


class TestFormatFewShotPrompt:
    """Test few-shot prompt formatting."""

    def test_format_with_examples(self):
        """Test formatting prompt with examples."""
        examples = [
            FewShotExample(
                query="What is AI?",
                context="AI context",
                answer="AI is artificial intelligence."
            ),
            FewShotExample(
                query="What is ML?",
                context="ML context",
                answer="ML is machine learning."
            )
        ]

        prompt = format_few_shot_prompt(
            query="What is DL?",
            context="DL context here",
            examples=examples,
            max_examples=2
        )

        assert "What is AI?" in prompt
        assert "What is ML?" in prompt
        assert "What is DL?" in prompt
        assert "DL context here" in prompt

    def test_format_without_examples(self):
        """Test formatting prompt without examples."""
        prompt = format_few_shot_prompt(
            query="Test query",
            context="Test context",
            examples=[],
            max_examples=3
        )

        # Should still have query and context
        assert "Test query" in prompt
        assert "Test context" in prompt

    def test_format_respects_max_examples(self):
        """Test max_examples limit."""
        examples = [
            FewShotExample(f"Q{i}", f"C{i}", f"A{i}")
            for i in range(10)
        ]

        prompt = format_few_shot_prompt(
            query="Test",
            context="Context",
            examples=examples,
            max_examples=2
        )

        # Should only include first 2 examples
        assert "Q0" in prompt
        assert "Q1" in prompt
        assert "Q2" not in prompt
