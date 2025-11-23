"""Integration tests for memory system workflows (v0.4.6).

Tests end-to-end multi-persona workflows including:
- Persona creation and switching
- Data isolation between personas
- Knowledge graph and interaction tracking integration
- Cross-component memory operations

These tests validate real-world usage scenarios.
"""

import time
from datetime import datetime
from pathlib import Path

import pytest

from ragged.memory import InteractionTracker, KnowledgeGraph, PersonaManager


@pytest.fixture
def temp_data_dir(tmp_path):
    """Temporary data directory for integration tests."""
    return tmp_path


@pytest.fixture
def persona_manager(temp_data_dir):
    """Create persona manager with temporary storage."""
    from ragged.config.settings import get_settings
    settings = get_settings()
    original_data_dir = settings.data_dir
    settings.data_dir = temp_data_dir

    manager = PersonaManager()

    yield manager

    # Cleanup
    settings.data_dir = original_data_dir


class TestMultiPersonaWorkflows:
    """Integration tests for multi-persona workflows."""

    def test_complete_persona_lifecycle(self, persona_manager, temp_data_dir):
        """Test: Complete persona lifecycle from creation to deletion."""
        # Create persona
        persona = persona_manager.create(
            "researcher",
            description="ML Research persona",
            focus=["RAG", "NLP", "ML"],
            preferences={"model": "llama3"},
        )

        assert persona.name == "researcher"
        assert persona.description == "ML Research persona"
        assert "RAG" in persona.focus_areas

        # Use persona - record interactions
        tracker = InteractionTracker(persona="researcher")
        interaction = tracker.record_interaction(
            query="What is RAG?",
            response="Retrieval-Augmented Generation combines...",
            model_used="llama3",
            latency_ms=150.0,
        )

        assert interaction.persona == "researcher"

        # Use persona - add topics to graph
        with KnowledgeGraph(persona="researcher") as graph:
            graph.add_topic_interest("RAG", interest_level=0.9)
            graph.add_topic_interest("NLP", interest_level=0.8)

            interests = graph.get_user_interests()
            assert len(interests) == 2
            assert any(i["topic"] == "RAG" for i in interests)

        # Switch to persona (updates usage stats)
        persona_manager.switch("researcher")
        updated_persona = persona_manager.get("researcher")
        assert updated_persona.usage_count == 1

        # Export persona data
        export_path = persona_manager.export_persona("researcher")
        assert export_path.exists()

        # Delete persona (cleanup)
        tracker.clear_interactions(confirm=True)
        with KnowledgeGraph(persona="researcher") as graph:
            graph.delete_user_data("researcher", confirm=True)
        persona_manager.delete("researcher", confirm=True)

        # Verify deletion
        assert "researcher" not in persona_manager.list()

    def test_persona_switching_workflow(self, persona_manager, temp_data_dir):
        """Test: Switching between multiple personas with isolated data."""
        # Create two personas
        persona_manager.create("student", description="Learning Python", focus=["Python", "Basics"])
        persona_manager.create("developer", description="Professional dev", focus=["FastAPI", "SQL"])

        # Student workflow
        student_tracker = InteractionTracker(persona="student")
        student_tracker.record_interaction(
            query="How do I print in Python?",
            response="Use print() function",
        )
        student_tracker.record_interaction(
            query="What are lists?",
            response="Lists are ordered collections",
        )

        with KnowledgeGraph(persona="student") as graph:
            graph.add_topic_interest("Python")
            graph.add_topic_interest("Basics")

        # Developer workflow
        dev_tracker = InteractionTracker(persona="developer")
        dev_tracker.record_interaction(
            query="FastAPI async best practices?",
            response="Use async/await with asyncio...",
        )

        with KnowledgeGraph(persona="developer") as graph:
            graph.add_topic_interest("FastAPI")
            graph.add_topic_interest("SQL")

        # Verify data isolation
        student_interactions = student_tracker.list_interactions(limit=100)
        dev_interactions = dev_tracker.list_interactions(limit=100)

        assert len(student_interactions) == 2
        assert len(dev_interactions) == 1

        # Verify no cross-contamination
        assert all(i.persona == "student" for i in student_interactions)
        assert all(i.persona == "developer" for i in dev_interactions)

        # Verify graph isolation
        with KnowledgeGraph(persona="student") as graph:
            student_interests = graph.get_user_interests()
            assert len(student_interests) == 2
            assert all(i["topic"] in ["Python", "Basics"] for i in student_interests)

        with KnowledgeGraph(persona="developer") as graph:
            dev_interests = graph.get_user_interests()
            assert len(dev_interests) == 2
            assert all(i["topic"] in ["FastAPI", "SQL"] for i in dev_interests)

        # Switch active persona
        persona_manager.switch("student")
        assert persona_manager.get_active().name == "student"

        persona_manager.switch("developer")
        assert persona_manager.get_active().name == "developer"

        # Cleanup
        student_tracker.clear_interactions(confirm=True)
        dev_tracker.clear_interactions(confirm=True)
        with KnowledgeGraph(persona="student") as graph:
            graph.delete_user_data("student", confirm=True)
        with KnowledgeGraph(persona="developer") as graph:
            graph.delete_user_data("developer", confirm=True)
        persona_manager.delete("student", confirm=True)
        persona_manager.delete("developer", confirm=True)

    def test_cross_component_memory_workflow(self, persona_manager, temp_data_dir):
        """Test: Integration between interactions, graph, and persona management."""
        # Create persona with focus areas
        persona_manager.create(
            "data_scientist",
            description="Data science researcher",
            focus=["ML", "Statistics", "RAG"],
            active_projects=["project_alpha", "project_beta"],
        )

        tracker = InteractionTracker(persona="data_scientist")

        # Simulate research session
        queries = [
            ("What is RAG?", "Retrieval-Augmented Generation..."),
            ("How does embedding work?", "Embeddings map text to vectors..."),
            ("Best practices for chunking?", "Chunk size affects retrieval..."),
        ]

        for query, response in queries:
            tracker.record_interaction(
                query=query,
                response=response,
                retrieved_doc_ids=[f"doc_{i}" for i in range(3)],
                model_used="llama3",
            )

        # Build knowledge graph from interaction data
        with KnowledgeGraph(persona="data_scientist") as graph:
            # Add topics from focus areas
            graph.add_topic_interest("ML", interest_level=0.9)
            graph.add_topic_interest("RAG", interest_level=0.95)
            graph.add_topic_interest("Embeddings", interest_level=0.8)

            # Record document access
            for i in range(6):
                graph.record_document_access(
                    f"doc_{i}",
                    title=f"Research Paper {i}",
                )

            # Link topics to documents
            graph.link_topic_to_document("RAG", "doc_0", relevance=0.9)
            graph.link_topic_to_document("RAG", "doc_1", relevance=0.8)
            graph.link_topic_to_document("Embeddings", "doc_2", relevance=0.85)

            # Query integrated data
            interests = graph.get_user_interests()
            assert len(interests) == 3

            docs = graph.get_accessed_documents(limit=10)
            assert len(docs) == 6

            rag_docs = graph.get_related_documents("RAG", limit=10)
            assert len(rag_docs) == 2

        # Verify interactions recorded
        history = tracker.list_interactions(limit=10)
        assert len(history) == 3

        # Export complete persona data
        export_data = tracker.export_interactions()
        assert export_data["interaction_count"] == 3

        with KnowledgeGraph(persona="data_scientist") as graph:
            graph_export = graph.export_graph()
            assert len(graph_export["interests"]) == 3
            assert len(graph_export["documents"]) == 6
            assert len(graph_export["topic_document_links"]) == 3

        # Cleanup
        tracker.clear_interactions(confirm=True)
        with KnowledgeGraph(persona="data_scientist") as graph:
            graph.delete_user_data("data_scientist", confirm=True)
        persona_manager.delete("data_scientist", confirm=True)

    def test_high_volume_persona_workflow(self, persona_manager, temp_data_dir):
        """Test: High-volume workflow with many interactions and graph nodes."""
        persona_manager.create("power_user", description="Heavy usage scenario")

        tracker = InteractionTracker(persona="power_user")

        # Record 100 interactions
        for i in range(100):
            tracker.record_interaction(
                query=f"Query {i}",
                response=f"Response {i}",
                retrieved_doc_ids=[f"doc_{j}" for j in range(i % 5)],
                model_used="llama3",
                latency_ms=100.0 + (i % 50),
            )

        # Build large knowledge graph
        with KnowledgeGraph(persona="power_user") as graph:
            # Add 50 topics
            for i in range(50):
                graph.add_topic_interest(f"Topic_{i}", interest_level=0.5 + (i % 5) / 10)

            # Add 50 documents
            for i in range(50):
                graph.record_document_access(f"doc_{i}", title=f"Document {i}")

            # Create topic-document relationships
            for i in range(50):
                for j in range(2):  # 2 docs per topic
                    doc_idx = (i * 2 + j) % 50
                    graph.link_topic_to_document(f"Topic_{i}", f"doc_{doc_idx}", relevance=0.7)

            # Verify data volume
            interests = graph.get_user_interests()
            assert len(interests) == 50

            docs = graph.get_accessed_documents(limit=100)
            assert len(docs) == 50

        # Query performance check
        start = time.time()
        history = tracker.list_interactions(limit=50)
        query_time = (time.time() - start) * 1000  # ms

        assert len(history) == 50
        assert query_time < 100  # Should be fast with composite index

        # Cleanup
        tracker.clear_interactions(confirm=True)
        with KnowledgeGraph(persona="power_user") as graph:
            graph.delete_user_data("power_user", confirm=True)
        persona_manager.delete("power_user", confirm=True)


class TestDataIsolationUnderLoad:
    """Tests for data isolation between personas under concurrent load."""

    def test_isolated_sessions(self, persona_manager, temp_data_dir):
        """Test: Multiple personas with simultaneous sessions maintain isolation."""
        # Create 3 personas
        personas = ["alice", "bob", "charlie"]
        for name in personas:
            persona_manager.create(name, description=f"User {name}")

        # Create trackers and graphs for each
        trackers = {name: InteractionTracker(persona=name) for name in personas}

        # Each persona performs unique operations
        for i, name in enumerate(personas):
            # Record unique interactions
            for j in range(10):
                trackers[name].record_interaction(
                    query=f"{name}_query_{j}",
                    response=f"{name}_response_{j}",
                    session_id=f"{name}_session",
                )

            # Add unique topics
            with KnowledgeGraph(persona=name) as graph:
                for j in range(5):
                    graph.add_topic_interest(f"{name}_topic_{j}")

        # Verify complete isolation
        for name in personas:
            # Check interactions
            interactions = trackers[name].list_interactions(limit=100)
            assert len(interactions) == 10
            assert all(name in i.query for i in interactions)
            assert all(i.session_id == f"{name}_session" for i in interactions)

            # Check graph
            with KnowledgeGraph(persona=name) as graph:
                interests = graph.get_user_interests()
                assert len(interests) == 5
                assert all(name in interest["topic"] for interest in interests)

        # Cleanup
        for name in personas:
            trackers[name].clear_interactions(confirm=True)
            with KnowledgeGraph(persona=name) as graph:
                graph.delete_user_data(name, confirm=True)
            persona_manager.delete(name, confirm=True)


# Mark all tests as integration tests
pytestmark = pytest.mark.integration
