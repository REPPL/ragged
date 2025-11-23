"""Tests for Interaction Tracking.

v0.4.5: Test coverage for interaction history system
"""

import json
import pytest
import tempfile
import shutil
from pathlib import Path
from datetime import datetime

from ragged.memory.interactions import Interaction, InteractionTracker, InteractionModel


class TestInteractionModel:
    """Test Interaction data model validation."""

    def test_valid_interaction_model(self):
        """Test creating valid interaction model."""
        model = InteractionModel(
            persona="researcher",
            query="What is RAG?",
            response="Retrieval-Augmented Generation...",
        )
        assert model.persona == "researcher"
        assert model.query == "What is RAG?"
        assert model.id is not None

    def test_interaction_id_auto_generated(self):
        """Test interaction ID is auto-generated."""
        model1 = InteractionModel(persona="test", query="query1")
        model2 = InteractionModel(persona="test", query="query2")

        assert model1.id != model2.id
        assert len(model1.id) > 0

    def test_feedback_validation(self):
        """Test feedback validation."""
        # Valid feedback values
        InteractionModel(persona="test", query="q", feedback="positive")
        InteractionModel(persona="test", query="q", feedback="negative")
        InteractionModel(persona="test", query="q", feedback="neutral")
        InteractionModel(persona="test", query="q", feedback=None)

        # Invalid feedback
        with pytest.raises(ValueError):
            InteractionModel(persona="test", query="q", feedback="invalid")


class TestInteraction:
    """Test Interaction dataclass."""

    def test_interaction_creation(self):
        """Test creating interaction."""
        interaction = Interaction(
            persona="researcher",
            query="What is RAG?",
            response="Retrieval-Augmented Generation...",
        )
        assert interaction.persona == "researcher"
        assert interaction.query == "What is RAG?"
        assert interaction.id is not None

    def test_interaction_to_dict(self):
        """Test interaction serialization."""
        interaction = Interaction(
            persona="researcher",
            query="What is RAG?",
            response="RAG is...",
            retrieved_doc_ids=["doc1", "doc2"],
            model_used="llama3",
            latency_ms=150.5,
        )
        data = interaction.to_dict()

        assert data["persona"] == "researcher"
        assert data["query"] == "What is RAG?"
        assert json.loads(data["retrieved_doc_ids"]) == ["doc1", "doc2"]
        assert data["model_used"] == "llama3"
        assert data["latency_ms"] == 150.5

    def test_interaction_from_dict(self):
        """Test interaction deserialization."""
        data = {
            "id": "test-id",
            "persona": "researcher",
            "query": "What is RAG?",
            "response": "RAG is...",
            "timestamp": datetime.now().isoformat(),
            "retrieved_doc_ids": json.dumps(["doc1", "doc2"]),
            "model_used": "llama3",
            "latency_ms": 150.5,
            "feedback": "positive",
            "session_id": "session-1",
        }
        interaction = Interaction.from_dict(data)

        assert interaction.id == "test-id"
        assert interaction.persona == "researcher"
        assert interaction.retrieved_doc_ids == ["doc1", "doc2"]
        assert interaction.feedback == "positive"


class TestInteractionTracker:
    """Test InteractionTracker."""

    @pytest.fixture
    def temp_storage(self):
        """Create temporary storage directory."""
        temp_dir = Path(tempfile.mkdtemp())
        yield temp_dir
        shutil.rmtree(temp_dir)

    @pytest.fixture
    def tracker(self, temp_storage):
        """Create InteractionTracker with temp storage."""
        return InteractionTracker(persona="researcher", storage_dir=temp_storage)

    def test_tracker_initialization(self, tracker):
        """Test tracker initialization."""
        assert tracker.persona == "researcher"
        assert tracker.storage_dir.exists()
        assert tracker.db_path.exists()

    def test_record_interaction(self, tracker):
        """Test recording interaction."""
        interaction = tracker.record_interaction(
            query="What is RAG?",
            response="Retrieval-Augmented Generation...",
            retrieved_doc_ids=["doc1", "doc2"],
            model_used="llama3",
            latency_ms=150.5,
        )

        assert interaction.persona == "researcher"
        assert interaction.query == "What is RAG?"
        assert interaction.response == "Retrieval-Augmented Generation..."
        assert interaction.retrieved_doc_ids == ["doc1", "doc2"]
        assert interaction.model_used == "llama3"
        assert interaction.latency_ms == 150.5

    def test_record_interaction_without_persona(self, temp_storage):
        """Test recording requires persona."""
        tracker = InteractionTracker(storage_dir=temp_storage)

        with pytest.raises(ValueError, match="Persona must be provided"):
            tracker.record_interaction(query="test")

    def test_record_interaction_with_override_persona(self, tracker):
        """Test recording with persona override."""
        interaction = tracker.record_interaction(
            query="test query",
            persona="student",
        )

        assert interaction.persona == "student"

    def test_get_interaction(self, tracker):
        """Test getting interaction by ID."""
        recorded = tracker.record_interaction(
            query="What is RAG?",
            response="RAG is...",
        )

        retrieved = tracker.get_interaction(recorded.id)

        assert retrieved.id == recorded.id
        assert retrieved.query == "What is RAG?"
        assert retrieved.response == "RAG is..."

    def test_get_nonexistent_interaction(self, tracker):
        """Test getting nonexistent interaction fails."""
        with pytest.raises(KeyError, match="not found"):
            tracker.get_interaction("nonexistent-id")

    def test_list_interactions(self, tracker):
        """Test listing interactions."""
        # Record multiple interactions
        tracker.record_interaction(query="Query 1", response="Response 1")
        tracker.record_interaction(query="Query 2", response="Response 2")
        tracker.record_interaction(query="Query 3", response="Response 3")

        interactions = tracker.list_interactions(limit=10)

        assert len(interactions) == 3
        # Should be in reverse chronological order
        assert interactions[0].query == "Query 3"
        assert interactions[1].query == "Query 2"
        assert interactions[2].query == "Query 1"

    def test_list_interactions_with_limit(self, tracker):
        """Test listing with limit."""
        for i in range(5):
            tracker.record_interaction(query=f"Query {i}")

        interactions = tracker.list_interactions(limit=2)
        assert len(interactions) == 2

    def test_list_interactions_with_offset(self, tracker):
        """Test listing with offset."""
        for i in range(5):
            tracker.record_interaction(query=f"Query {i}")

        interactions = tracker.list_interactions(limit=2, offset=2)
        assert len(interactions) == 2
        # Should skip first 2 (most recent)
        assert "Query 2" in interactions[0].query or "Query 1" in interactions[0].query

    def test_list_interactions_by_persona(self, temp_storage):
        """Test filtering by persona."""
        tracker = InteractionTracker(storage_dir=temp_storage)

        tracker.record_interaction(query="R1", persona="researcher")
        tracker.record_interaction(query="R2", persona="researcher")
        tracker.record_interaction(query="S1", persona="student")

        researcher_interactions = tracker.list_interactions(persona="researcher")
        assert len(researcher_interactions) == 2

        student_interactions = tracker.list_interactions(persona="student")
        assert len(student_interactions) == 1

    def test_list_interactions_by_session(self, tracker):
        """Test filtering by session ID."""
        tracker.record_interaction(query="Q1", session_id="session-1")
        tracker.record_interaction(query="Q2", session_id="session-1")
        tracker.record_interaction(query="Q3", session_id="session-2")

        session1_interactions = tracker.list_interactions(session_id="session-1")
        assert len(session1_interactions) == 2

    def test_delete_interaction(self, tracker):
        """Test deleting interaction."""
        interaction = tracker.record_interaction(query="test")

        tracker.delete_interaction(interaction.id, confirm=True)

        with pytest.raises(KeyError):
            tracker.get_interaction(interaction.id)

    def test_delete_without_confirmation(self, tracker):
        """Test delete requires confirmation."""
        interaction = tracker.record_interaction(query="test")

        with pytest.raises(ValueError, match="confirm=True"):
            tracker.delete_interaction(interaction.id)

    def test_clear_interactions(self, tracker):
        """Test clearing all interactions for persona."""
        tracker.record_interaction(query="Q1")
        tracker.record_interaction(query="Q2")
        tracker.record_interaction(query="Q3")

        count = tracker.clear_interactions(confirm=True)
        assert count == 3

        interactions = tracker.list_interactions()
        assert len(interactions) == 0

    def test_clear_interactions_by_persona(self, temp_storage):
        """Test clearing only specific persona's interactions."""
        tracker = InteractionTracker(storage_dir=temp_storage)

        tracker.record_interaction(query="R1", persona="researcher")
        tracker.record_interaction(query="R2", persona="researcher")
        tracker.record_interaction(query="S1", persona="student")

        count = tracker.clear_interactions(persona="researcher", confirm=True)
        assert count == 2

        # Student interactions should remain
        student_interactions = tracker.list_interactions(persona="student")
        assert len(student_interactions) == 1

    def test_export_interactions(self, tracker, temp_storage):
        """Test exporting interactions to JSON."""
        tracker.record_interaction(
            query="What is RAG?",
            response="RAG is...",
            retrieved_doc_ids=["doc1"],
            model_used="llama3",
        )
        tracker.record_interaction(query="Another query")

        export_path = temp_storage / "export.json"
        export_data = tracker.export_interactions(output_path=export_path)

        assert export_path.exists()
        assert export_data["persona"] == "researcher"
        assert export_data["interaction_count"] == 2
        assert len(export_data["interactions"]) == 2

        # Verify JSON structure
        with open(export_path) as f:
            loaded_data = json.load(f)
        assert loaded_data["interaction_count"] == 2

    def test_add_feedback(self, tracker):
        """Test adding feedback to interaction."""
        interaction = tracker.record_interaction(query="test")
        assert interaction.feedback is None

        tracker.add_feedback(interaction.id, "positive")

        updated = tracker.get_interaction(interaction.id)
        assert updated.feedback == "positive"

    def test_add_invalid_feedback(self, tracker):
        """Test adding invalid feedback fails."""
        interaction = tracker.record_interaction(query="test")

        with pytest.raises(ValueError, match="positive, negative, or neutral"):
            tracker.add_feedback(interaction.id, "invalid")

    def test_interaction_persistence(self, temp_storage):
        """Test interactions persist across tracker instances."""
        # Record with first tracker
        tracker1 = InteractionTracker(persona="researcher", storage_dir=temp_storage)
        interaction = tracker1.record_interaction(
            query="What is RAG?",
            response="RAG is...",
        )

        # Load with second tracker
        tracker2 = InteractionTracker(persona="researcher", storage_dir=temp_storage)
        retrieved = tracker2.get_interaction(interaction.id)

        assert retrieved.query == "What is RAG?"
        assert retrieved.response == "RAG is..."

    def test_record_interaction_with_session(self, tracker):
        """Test recording with session ID."""
        interaction = tracker.record_interaction(
            query="test",
            session_id="session-123",
        )

        assert interaction.session_id == "session-123"
