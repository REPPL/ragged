"""Privacy-focused integration tests for memory system.

v0.4.5: Memory Foundation - Privacy & Security Validation

Tests privacy guarantees across the entire memory system:
- Network isolation (no external connections)
- Data locality (all data in ~/.ragged/memory/)
- Persona isolation (no cross-contamination)
- User control (view, edit, delete, export)
- GDPR compliance (Articles 15, 17, 20)
"""

import json
import shutil
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from ragged.memory import (
    InteractionTracker,
    KnowledgeGraph,
    Persona,
    PersonaManager,
)


@pytest.fixture
def temp_storage():
    """Create temporary storage directory."""
    temp_dir = Path(tempfile.mkdtemp())
    yield temp_dir
    shutil.rmtree(temp_dir)


@pytest.fixture
def mock_settings(temp_storage, monkeypatch):
    """Mock settings to use temp storage."""
    from ragged.config.settings import Settings

    def mock_get_settings():
        settings = Settings()
        settings.data_dir = str(temp_storage)
        return settings

    monkeypatch.setattr("ragged.memory.persona.get_settings", mock_get_settings)
    monkeypatch.setattr("ragged.memory.interactions.get_settings", mock_get_settings)
    monkeypatch.setattr("ragged.memory.graph.get_settings", mock_get_settings)

    return temp_storage


class TestNetworkIsolation:
    """Verify memory system makes no external network connections."""

    def test_persona_manager_no_network_calls(self, mock_settings):
        """Test PersonaManager makes no network calls during operations."""
        with patch("socket.socket") as mock_socket:
            manager = PersonaManager()

            # Perform all major operations
            manager.create("researcher", description="ML researcher", focus=["RAG", "NLP"])
            manager.switch("researcher")
            manager.get("researcher")
            manager.list()
            manager.delete("researcher", confirm=True)

            # Verify no socket connections attempted
            assert not mock_socket.called, "PersonaManager should not create network sockets"

    def test_interaction_tracker_no_network_calls(self, mock_settings):
        """Test InteractionTracker makes no network calls during operations."""
        with patch("socket.socket") as mock_socket:
            tracker = InteractionTracker(persona="researcher")

            # Perform all major operations
            tracker.record_interaction(
                query="What is RAG?",
                response="RAG is...",
                retrieved_doc_ids=["doc1", "doc2"],
            )
            tracker.list_interactions(limit=10)
            tracker.clear_interactions(confirm=True)

            # Verify no socket connections attempted
            assert not mock_socket.called, "InteractionTracker should not create network sockets"

    def test_knowledge_graph_no_network_calls(self, mock_settings):
        """Test KnowledgeGraph makes no network calls during operations."""
        with patch("socket.socket") as mock_socket:
            graph = KnowledgeGraph(persona="researcher")

            # Perform all major operations
            graph.add_topic_interest("RAG", interest_level=0.9)
            graph.record_document_access("doc123", title="RAG Paper")
            graph.link_topic_to_document("RAG", "doc123", relevance=0.95)
            graph.get_user_interests()
            graph.get_accessed_documents()
            graph.get_related_documents("RAG")
            graph.export_graph()
            graph.delete_user_data("researcher", confirm=True)

            graph.close()

            # Verify no socket connections attempted
            assert not mock_socket.called, "KnowledgeGraph should not create network sockets"

    def test_full_memory_workflow_network_isolation(self, mock_settings):
        """Test complete memory workflow with network monitoring."""
        with patch("socket.socket") as mock_socket:
            # Create complete memory workflow
            manager = PersonaManager()
            manager.create("researcher", description="ML researcher", focus=["RAG"])

            tracker = InteractionTracker(persona="researcher")
            tracker.record_interaction(query="Test query", response="Test response")

            graph = KnowledgeGraph(persona="researcher")
            graph.add_topic_interest("RAG")
            graph.record_document_access("doc1")

            # Export all data
            manager.export_persona("researcher")
            tracker.export_interactions()
            graph.export_graph()

            # Cleanup
            tracker.clear_interactions(confirm=True)
            graph.delete_user_data("researcher", confirm=True)
            manager.delete("researcher", confirm=True)
            graph.close()

            # Verify no network activity throughout entire workflow
            assert not mock_socket.called, "Memory system should be fully local"


class TestDataLocality:
    """Verify all data is stored locally in correct directories."""

    def test_persona_data_locality(self, mock_settings):
        """Test persona data is stored in correct local directory."""
        manager = PersonaManager()
        manager.create("researcher")

        # Verify data directory exists
        persona_dir = mock_settings / "memory" / "profiles"
        assert persona_dir.exists(), "Persona directory should exist"

        # Verify personas file exists
        personas_file = persona_dir / "personas.yaml"
        assert personas_file.exists(), "Personas file should exist"

        # Active persona file is created when persona is switched
        manager.switch("researcher")
        active_file = persona_dir / "active_persona.txt"
        assert active_file.exists(), "Active persona file should exist after switch"

    def test_interaction_data_locality(self, mock_settings):
        """Test interaction data is stored in correct local directory."""
        tracker = InteractionTracker(persona="researcher")

        # Database is created on first record
        tracker.record_interaction(query="test", response="test")

        # Verify data directory exists
        memory_dir = mock_settings / "memory"
        assert memory_dir.exists(), "Memory directory should exist"

        # Verify database file exists
        db_file = memory_dir / "interactions.db"
        assert db_file.exists(), "Interactions database should exist"

        # Verify it's a valid SQLite database
        import sqlite3
        conn = sqlite3.connect(db_file)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = {row[0] for row in cursor.fetchall()}
        assert "interactions" in tables, "Interactions table should exist"
        conn.close()

    def test_graph_data_locality(self, mock_settings):
        """Test graph data is stored in correct local directory."""
        graph = KnowledgeGraph(persona="researcher")
        graph.add_topic_interest("RAG")

        # Verify graph directory exists
        graph_dir = mock_settings / "memory" / "graph"
        assert graph_dir.exists(), "Graph directory should exist"

        # Verify Kuzu database directory exists
        kuzu_db = graph_dir / "kuzu_db"
        assert kuzu_db.exists(), "Kuzu database should exist"

        graph.close()

    def test_no_data_outside_local_storage(self, mock_settings):
        """Test that no data is written outside local storage directory."""
        # Track all file operations
        original_open = open
        files_opened = []

        def tracked_open(file, *args, **kwargs):
            files_opened.append(str(file))
            return original_open(file, *args, **kwargs)

        with patch("builtins.open", tracked_open):
            # Perform all memory operations
            manager = PersonaManager()
            manager.create("researcher")

            tracker = InteractionTracker(persona="researcher")
            tracker.record_interaction(query="test", response="test")

            graph = KnowledgeGraph(persona="researcher")
            graph.add_topic_interest("RAG")
            graph.close()

        # Verify all file operations are within temp storage
        for file_path in files_opened:
            if not file_path.startswith("<"):  # Ignore special file descriptors
                path = Path(file_path)
                try:
                    # Check if path is relative to temp storage
                    path.relative_to(mock_settings)
                except ValueError:
                    # Also allow system config files
                    if ".ragged" not in str(path):
                        # Allow config files in /etc, /usr, etc.
                        if not any(
                            str(path).startswith(p)
                            for p in ["/etc", "/usr", "/System", "/Library"]
                        ):
                            pytest.fail(f"File operation outside storage: {file_path}")


class TestPersonaIsolation:
    """Verify complete isolation between different personas."""

    def test_interaction_history_isolation(self, mock_settings):
        """Test interaction histories are isolated between personas."""
        # Create interactions for researcher
        researcher_tracker = InteractionTracker(persona="researcher")
        researcher_tracker.record_interaction(
            query="What is RAG?",
            response="RAG is Retrieval-Augmented Generation",
        )

        # Create interactions for student
        student_tracker = InteractionTracker(persona="student")
        student_tracker.record_interaction(
            query="What is Python?",
            response="Python is a programming language",
        )

        # Verify researcher only sees their history
        researcher_history = researcher_tracker.list_interactions()
        assert len(researcher_history) == 1
        assert researcher_history[0].query == "What is RAG?"

        # Verify student only sees their history
        student_history = student_tracker.list_interactions()
        assert len(student_history) == 1
        assert student_history[0].query == "What is Python?"

        # Verify no cross-contamination
        assert researcher_history[0].query != student_history[0].query

    def test_knowledge_graph_isolation(self, mock_settings):
        """Test knowledge graphs are isolated between personas."""
        # Create graph for researcher
        researcher_graph = KnowledgeGraph(persona="researcher")
        researcher_graph.add_topic_interest("RAG", interest_level=0.9)
        researcher_graph.record_document_access("doc1", title="RAG Paper")

        # Create graph for student
        student_graph = KnowledgeGraph(persona="student")
        student_graph.add_topic_interest("Python", interest_level=0.8)
        student_graph.record_document_access("doc2", title="Python Guide")

        # Verify researcher only sees their interests
        researcher_interests = researcher_graph.get_user_interests()
        assert len(researcher_interests) == 1
        assert researcher_interests[0]["topic"] == "RAG"

        # Verify student only sees their interests
        student_interests = student_graph.get_user_interests()
        assert len(student_interests) == 1
        assert student_interests[0]["topic"] == "Python"

        # Verify researcher only sees their documents
        researcher_docs = researcher_graph.get_accessed_documents()
        assert len(researcher_docs) == 1
        assert researcher_docs[0]["doc_id"] == "doc1"

        # Verify student only sees their documents
        student_docs = student_graph.get_accessed_documents()
        assert len(student_docs) == 1
        assert student_docs[0]["doc_id"] == "doc2"

        # Cleanup
        researcher_graph.close()
        student_graph.close()

    def test_no_data_leakage_after_deletion(self, mock_settings):
        """Test deleted persona data doesn't leak to other personas."""
        # Create two personas with data
        tracker1 = InteractionTracker(persona="persona1")
        tracker1.record_interaction(query="Query 1", response="Response 1")

        tracker2 = InteractionTracker(persona="persona2")
        tracker2.record_interaction(query="Query 2", response="Response 2")

        # Delete persona1
        tracker1.clear_interactions(confirm=True)

        # Verify persona2 data still intact
        history2 = tracker2.list_interactions()
        assert len(history2) == 1
        assert history2[0].query == "Query 2"

        # Verify persona1 data is gone
        history1 = tracker1.list_interactions()
        assert len(history1) == 0

    def test_concurrent_persona_operations(self, mock_settings):
        """Test multiple personas can be used concurrently without interference."""
        # Create multiple personas simultaneously
        personas = ["researcher", "student", "developer"]
        trackers = {p: InteractionTracker(persona=p) for p in personas}
        graphs = {p: KnowledgeGraph(persona=p) for p in personas}

        # Perform operations for each persona
        for i, persona in enumerate(personas):
            trackers[persona].record_interaction(
                query=f"Query for {persona}",
                response=f"Response for {persona}",
            )
            graphs[persona].add_topic_interest(f"Topic-{i}")

        # Verify each persona has correct data
        for i, persona in enumerate(personas):
            history = trackers[persona].list_interactions()
            assert len(history) == 1
            assert persona in history[0].query

            interests = graphs[persona].get_user_interests()
            assert len(interests) == 1
            assert interests[0]["topic"] == f"Topic-{i}"

        # Cleanup
        for graph in graphs.values():
            graph.close()


class TestUserControl:
    """Verify users have complete control over their data (GDPR)."""

    def test_view_all_persona_data(self, mock_settings):
        """Test users can view all their persona data (Article 15)."""
        manager = PersonaManager()
        manager.create(
            "researcher",
            description="ML researcher",
            focus=["RAG", "NLP"],
            active_projects=["thesis"],
        )

        # Export persona data
        export_path = manager.export_persona("researcher")
        assert export_path.exists(), "Export file should exist"

        # Verify export contains all data
        with open(export_path) as f:
            data = json.load(f)

        # Data is wrapped in "persona" key
        persona_data = data["persona"]
        assert persona_data["name"] == "researcher"
        assert persona_data["description"] == "ML researcher"
        assert "RAG" in persona_data["focus_areas"]
        assert "NLP" in persona_data["focus_areas"]
        assert "thesis" in persona_data["active_projects"]

    def test_view_all_interaction_data(self, mock_settings):
        """Test users can view all their interaction history (Article 15)."""
        tracker = InteractionTracker(persona="researcher")

        # Record multiple interactions
        for i in range(5):
            tracker.record_interaction(
                query=f"Query {i}",
                response=f"Response {i}",
                retrieved_doc_ids=[f"doc{i}"],
            )

        # Export history
        data = tracker.export_interactions()

        # Verify export contains all interactions
        assert len(data["interactions"]) == 5
        assert data["persona"] == "researcher"
        # Interactions might be in reverse order (newest first)
        queries_present = {interaction["query"] for interaction in data["interactions"]}
        for i in range(5):
            assert f"Query {i}" in queries_present

    def test_view_all_graph_data(self, mock_settings):
        """Test users can view all their graph data (Article 15)."""
        graph = KnowledgeGraph(persona="researcher")

        # Add various data
        graph.add_topic_interest("RAG", interest_level=0.9)
        graph.add_topic_interest("NLP", interest_level=0.8)
        graph.record_document_access("doc1", title="RAG Paper")
        graph.record_document_access("doc2", title="NLP Survey")
        graph.link_topic_to_document("RAG", "doc1", relevance=0.95)

        # Export graph
        export = graph.export_graph()

        # Verify export contains all data
        assert export["persona"] == "researcher"
        assert len(export["interests"]) == 2
        assert len(export["documents"]) == 2
        assert len(export["topic_document_links"]) == 1

        graph.close()

    def test_delete_all_persona_data(self, mock_settings):
        """Test users can delete all their data (Article 17)."""
        manager = PersonaManager()
        manager.create("researcher")

        # Verify persona exists
        assert manager.get("researcher") is not None

        # Delete persona
        manager.delete("researcher", confirm=True)

        # Verify persona is gone
        with pytest.raises(KeyError, match="not found"):
            manager.get("researcher")

    def test_delete_all_interaction_data(self, mock_settings):
        """Test users can delete all interaction history (Article 17)."""
        tracker = InteractionTracker(persona="researcher")
        tracker.record_interaction(query="test", response="test")

        # Verify history exists
        assert len(tracker.list_interactions()) == 1

        # Delete history
        tracker.clear_interactions(confirm=True)

        # Verify history is gone
        assert len(tracker.list_interactions()) == 0

    def test_delete_all_graph_data(self, mock_settings):
        """Test users can delete all graph data (Article 17)."""
        graph = KnowledgeGraph(persona="researcher")
        graph.add_topic_interest("RAG")

        # Verify data exists
        assert len(graph.get_user_interests()) == 1

        # Delete all user data
        count = graph.delete_user_data("researcher", confirm=True)
        assert count == 1

        # Verify data is gone
        assert len(graph.get_user_interests("researcher")) == 0

        graph.close()

    def test_export_all_data_portability(self, mock_settings):
        """Test complete data portability (Article 20)."""
        # Create complete memory system
        manager = PersonaManager()
        manager.create("researcher", description="ML researcher")

        tracker = InteractionTracker(persona="researcher")
        tracker.record_interaction(query="What is RAG?", response="RAG is...")

        graph = KnowledgeGraph(persona="researcher")
        graph.add_topic_interest("RAG")

        # Export all data
        persona_export_path = manager.export_persona("researcher")
        history_data = tracker.export_interactions()
        graph_export_data = graph.export_graph()

        # Verify all exports are valid JSON (portable format)
        with open(persona_export_path) as f:
            persona_data = json.load(f)
        assert "persona" in persona_data  # Contains persona data

        # history_data is already a dict
        assert len(history_data["interactions"]) == 1

        # graph_export_data is already a dict
        assert graph_export_data["persona"] == "researcher"
        assert len(graph_export_data["interests"]) == 1

        graph.close()


class TestDataDeletionGuarantees:
    """Verify data deletion is complete and irreversible."""

    def test_persona_deletion_removes_files(self, mock_settings):
        """Test persona deletion removes persona from storage."""
        manager = PersonaManager()
        manager.create("researcher")

        # Verify persona exists in YAML file
        personas_file = mock_settings / "memory" / "profiles" / "personas.yaml"
        assert personas_file.exists()

        manager.delete("researcher", confirm=True)

        # Verify persona is removed from manager
        with pytest.raises((ValueError, KeyError)):
            manager.get("researcher")

    def test_interaction_deletion_removes_records(self, mock_settings):
        """Test interaction deletion removes database records."""
        tracker = InteractionTracker(persona="researcher")
        tracker.record_interaction(query="test", response="test")

        # Verify record exists
        import sqlite3
        db_file = mock_settings / "memory" / "interactions.db"
        conn = sqlite3.connect(db_file)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM interactions WHERE persona = ?", ("researcher",))
        count_before = cursor.fetchone()[0]
        conn.close()
        assert count_before == 1

        # Delete
        tracker.clear_interactions(confirm=True)

        # Verify record is gone
        conn = sqlite3.connect(db_file)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM interactions WHERE persona = ?", ("researcher",))
        count_after = cursor.fetchone()[0]
        conn.close()
        assert count_after == 0

    def test_graph_deletion_removes_nodes(self, mock_settings):
        """Test graph deletion removes all nodes and relationships."""
        graph = KnowledgeGraph(persona="researcher")
        graph.add_topic_interest("RAG")
        graph.record_document_access("doc1")

        # Verify data exists
        assert len(graph.get_user_interests()) == 1
        assert len(graph.get_accessed_documents()) == 1

        # Delete
        count = graph.delete_user_data("researcher", confirm=True)
        assert count == 1

        # Verify all data is gone
        assert len(graph.get_user_interests("researcher")) == 0
        assert len(graph.get_accessed_documents("researcher")) == 0

        graph.close()

    def test_deletion_requires_confirmation(self, mock_settings):
        """Test destructive operations require explicit confirmation."""
        manager = PersonaManager()
        manager.create("researcher")

        tracker = InteractionTracker(persona="researcher")
        tracker.record_interaction(query="test", response="test")

        graph = KnowledgeGraph(persona="researcher")
        graph.add_topic_interest("RAG")

        # All should raise without confirmation
        with pytest.raises(ValueError, match="confirm"):
            tracker.clear_interactions(confirm=False)

        with pytest.raises(ValueError, match="confirm"):
            graph.delete_user_data("researcher", confirm=False)

        with pytest.raises(ValueError, match="confirm"):
            graph.clear_graph(confirm=False)

        graph.close()


class TestGDPRCompliance:
    """Verify GDPR compliance across memory system."""

    def test_article_15_right_of_access(self, mock_settings):
        """Test Article 15: Right of access by the data subject."""
        # Users must be able to access all their data
        manager = PersonaManager()
        manager.create("researcher")

        tracker = InteractionTracker(persona="researcher")
        tracker.record_interaction(query="test", response="test")

        graph = KnowledgeGraph(persona="researcher")
        graph.add_topic_interest("RAG")

        # Verify all data is accessible
        persona = manager.get("researcher")
        assert persona is not None

        history = tracker.list_interactions()
        assert len(history) == 1

        interests = graph.get_user_interests()
        assert len(interests) == 1

        graph.close()

    def test_article_17_right_to_erasure(self, mock_settings):
        """Test Article 17: Right to erasure ('right to be forgotten')."""
        # Users must be able to delete all their data
        manager = PersonaManager()
        manager.create("researcher")

        tracker = InteractionTracker(persona="researcher")
        tracker.record_interaction(query="test", response="test")

        graph = KnowledgeGraph(persona="researcher")
        graph.add_topic_interest("RAG")

        # Delete all data
        tracker.clear_interactions(confirm=True)
        graph.delete_user_data("researcher", confirm=True)
        manager.delete("researcher", confirm=True)

        # Verify complete erasure
        with pytest.raises(KeyError):
            manager.get("researcher")

        assert len(tracker.list_interactions()) == 0
        assert len(graph.get_user_interests("researcher")) == 0

        graph.close()

    def test_article_20_right_to_data_portability(self, mock_settings):
        """Test Article 20: Right to data portability."""
        # Users must receive data in structured, commonly used, machine-readable format
        manager = PersonaManager()
        manager.create("researcher")

        tracker = InteractionTracker(persona="researcher")
        tracker.record_interaction(query="test", response="test")

        graph = KnowledgeGraph(persona="researcher")
        graph.add_topic_interest("RAG")

        # Export in machine-readable format (JSON)
        persona_export_path = manager.export_persona("researcher")
        history_export_data = tracker.export_interactions()
        graph_export_data = graph.export_graph()

        # Verify JSON format
        with open(persona_export_path) as f:
            json.load(f)  # Should parse without error

        # history_export is already a dict (machine-readable)
        assert isinstance(history_export_data, dict)

        # graph_export is already a dict (machine-readable)
        assert isinstance(graph_export_data, dict)

        graph.close()


class TestMemorySystemIntegration:
    """Integration tests for complete memory system workflows."""

    def test_complete_user_journey(self, mock_settings):
        """Test complete user journey through memory system."""
        # 1. Create persona
        manager = PersonaManager()
        manager.create("researcher", description="ML researcher", focus=["RAG", "NLP"])

        # 2. Start tracking interactions
        tracker = InteractionTracker(persona="researcher")
        tracker.record_interaction(
            query="What is RAG?",
            response="RAG is Retrieval-Augmented Generation",
            retrieved_doc_ids=["doc1"],
        )

        # 3. Build knowledge graph
        graph = KnowledgeGraph(persona="researcher")
        graph.add_topic_interest("RAG", interest_level=0.9)
        graph.record_document_access("doc1", title="RAG Paper")
        graph.link_topic_to_document("RAG", "doc1", relevance=0.95)

        # 4. Verify all data is connected
        persona = manager.get("researcher")
        assert "RAG" in persona.focus_areas

        history = tracker.list_interactions()
        assert len(history) == 1
        assert "RAG" in history[0].query

        interests = graph.get_user_interests()
        assert len(interests) == 1
        assert interests[0]["topic"] == "RAG"

        # 5. Export everything
        persona_export = manager.export_persona("researcher")
        history_export = tracker.export_interactions()
        graph_export = graph.export_graph()

        assert persona_export.exists()
        assert "interactions" in history_export  # Dict not Path
        assert "interests" in graph_export

        # 6. Delete everything
        tracker.clear_interactions(confirm=True)
        graph.delete_user_data("researcher", confirm=True)
        manager.delete("researcher", confirm=True)

        # 7. Verify complete cleanup
        with pytest.raises(KeyError):
            manager.get("researcher")
        assert len(tracker.list_interactions()) == 0

        graph.close()

    def test_privacy_preserved_across_operations(self, mock_settings):
        """Test privacy guarantees are maintained throughout operations."""
        with patch("socket.socket") as mock_socket:
            # Complete workflow with network monitoring
            manager = PersonaManager()
            manager.create("researcher")

            tracker = InteractionTracker(persona="researcher")
            for i in range(10):
                tracker.record_interaction(
                    query=f"Query {i}",
                    response=f"Response {i}",
                )

            graph = KnowledgeGraph(persona="researcher")
            for topic in ["RAG", "NLP", "Privacy", "Security"]:
                graph.add_topic_interest(topic)

            # Export, query - all operations
            manager.export_persona("researcher")
            tracker.list_interactions(limit=10)
            graph.get_user_interests()
            graph.get_accessed_documents()

            # Cleanup
            tracker.clear_interactions(confirm=True)
            graph.delete_user_data("researcher", confirm=True)
            manager.delete("researcher", confirm=True)
            graph.close()

            # Verify no network calls throughout
            assert not mock_socket.called

    def test_multi_persona_privacy_isolation(self, mock_settings):
        """Test privacy isolation with multiple concurrent personas."""
        # Create three distinct personas with different data
        personas_data = {
            "researcher": {"topics": ["RAG", "NLP"], "queries": ["What is RAG?"]},
            "student": {"topics": ["Python", "Databases"], "queries": ["Learn Python"]},
            "developer": {"topics": ["FastAPI", "Docker"], "queries": ["Deploy app"]},
        }

        trackers = {}
        graphs = {}

        # Setup all personas
        for persona, data in personas_data.items():
            trackers[persona] = InteractionTracker(persona=persona)
            graphs[persona] = KnowledgeGraph(persona=persona)

            for query in data["queries"]:
                trackers[persona].record_interaction(query=query, response="...")

            for topic in data["topics"]:
                graphs[persona].add_topic_interest(topic)

        # Verify complete isolation
        for persona, data in personas_data.items():
            # Check interaction isolation
            history = trackers[persona].list_interactions()
            assert len(history) == len(data["queries"])
            for interaction in history:
                assert any(q in interaction.query for q in data["queries"])

            # Check graph isolation
            interests = graphs[persona].get_user_interests()
            assert len(interests) == len(data["topics"])
            for interest in interests:
                assert interest["topic"] in data["topics"]

        # Cleanup
        manager = PersonaManager()
        for persona in personas_data:
            trackers[persona].clear_interactions(confirm=True)
            graphs[persona].delete_user_data(persona, confirm=True)
            graphs[persona].close()
            manager.delete(persona, confirm=True)


# Mark all tests as privacy and integration tests
pytestmark = [pytest.mark.privacy, pytest.mark.integration]
