"""Tests for Knowledge Graph.

v0.4.5: Test coverage for Kuzu-based knowledge graph system
"""

import shutil
import tempfile
from pathlib import Path

import pytest

from ragged.memory.graph import KnowledgeGraph


@pytest.fixture
def temp_storage():
    """Create temporary storage directory."""
    temp_dir = Path(tempfile.mkdtemp())
    yield temp_dir
    shutil.rmtree(temp_dir)


@pytest.fixture
def graph(temp_storage):
    """Create KnowledgeGraph with temp storage."""
    kg = KnowledgeGraph(persona="researcher", storage_dir=temp_storage)
    yield kg
    kg.close()


class TestKnowledgeGraphInitialisation:
    """Test knowledge graph initialisation."""

    def test_graph_initialisation(self, temp_storage):
        """Test graph initialises correctly."""
        with KnowledgeGraph(persona="researcher", storage_dir=temp_storage) as graph:
            assert graph.persona == "researcher"
            assert graph.storage_dir == temp_storage
            assert graph.db_path.exists()

    def test_graph_without_persona(self, temp_storage):
        """Test graph can be created without default persona."""
        with KnowledgeGraph(storage_dir=temp_storage) as graph:
            assert graph.persona is None
            assert graph.db_path.exists()

    def test_schema_creation(self, graph):
        """Test schema is created on initialisation."""
        # Should not raise errors
        assert graph.db is not None
        assert graph.conn is not None


class TestUserOperations:
    """Test user node operations."""

    def test_ensure_user_exists(self, graph):
        """Test user node creation."""
        graph.ensure_user_exists("researcher")

        # User should exist now
        result = graph.conn.execute(
            "MATCH (u:User {name: $name}) RETURN u.name",
            {"name": "researcher"},
        )
        assert result.has_next()
        assert result.get_next()[0] == "researcher"

    def test_ensure_user_idempotent(self, graph):
        """Test ensuring user multiple times doesn't create duplicates."""
        graph.ensure_user_exists("researcher")
        graph.ensure_user_exists("researcher")

        # Should have exactly one user
        result = graph.conn.execute(
            "MATCH (u:User {name: $name}) RETURN count(u)",
            {"name": "researcher"},
        )
        assert result.get_next()[0] == 1

    def test_ensure_user_requires_persona(self, graph):
        """Test ensure_user_exists requires persona."""
        graph.persona = None
        with pytest.raises(ValueError, match="Persona must be provided"):
            graph.ensure_user_exists()


class TestTopicInterests:
    """Test topic interest tracking."""

    def test_add_topic_interest(self, graph):
        """Test adding topic interest."""
        graph.add_topic_interest("RAG", interest_level=0.9)

        # Topic should exist
        result = graph.conn.execute(
            "MATCH (t:Topic {name: $name}) RETURN t.name, t.interest_level",
            {"name": "RAG"},
        )
        assert result.has_next()
        row = result.get_next()
        assert row[0] == "RAG"
        assert row[1] == 0.9

    def test_add_topic_creates_relationship(self, graph):
        """Test adding topic creates INTERESTED_IN relationship."""
        graph.add_topic_interest("NLP", interest_level=0.8)

        # Relationship should exist
        result = graph.conn.execute(
            """
            MATCH (u:User {name: $user})-[r:INTERESTED_IN]->(t:Topic {name: $topic})
            RETURN r.frequency
            """,
            {"user": "researcher", "topic": "NLP"},
        )
        assert result.has_next()
        assert result.get_next()[0] == 1

    def test_add_topic_updates_frequency(self, graph):
        """Test adding same topic multiple times updates frequency."""
        graph.add_topic_interest("Machine Learning")
        graph.add_topic_interest("Machine Learning")
        graph.add_topic_interest("Machine Learning")

        result = graph.conn.execute(
            """
            MATCH (u:User {name: $user})-[r:INTERESTED_IN]->(t:Topic {name: $topic})
            RETURN r.frequency
            """,
            {"user": "researcher", "topic": "Machine Learning"},
        )
        assert result.get_next()[0] == 3

    def test_add_topic_requires_persona(self, graph):
        """Test add_topic_interest requires persona."""
        graph.persona = None
        with pytest.raises(ValueError, match="Persona must be provided"):
            graph.add_topic_interest("test")


class TestDocumentAccess:
    """Test document access tracking."""

    def test_record_document_access(self, graph):
        """Test recording document access."""
        graph.record_document_access("doc123", title="RAG Paper")

        # Document should exist
        result = graph.conn.execute(
            "MATCH (d:Document {doc_id: $doc_id}) RETURN d.doc_id, d.title",
            {"doc_id": "doc123"},
        )
        assert result.has_next()
        row = result.get_next()
        assert row[0] == "doc123"
        assert row[1] == "RAG Paper"

    def test_record_document_creates_relationship(self, graph):
        """Test recording document creates ACCESSED relationship."""
        graph.record_document_access("doc456", title="NLP Survey")

        # Relationship should exist
        result = graph.conn.execute(
            """
            MATCH (u:User {name: $user})-[r:ACCESSED]->(d:Document {doc_id: $doc_id})
            RETURN r.access_count
            """,
            {"user": "researcher", "doc_id": "doc456"},
        )
        assert result.has_next()
        assert result.get_next()[0] == 1

    def test_record_document_updates_access_count(self, graph):
        """Test accessing same document multiple times updates count."""
        graph.record_document_access("doc789", title="Test Doc")
        graph.record_document_access("doc789", title="Test Doc")

        result = graph.conn.execute(
            """
            MATCH (u:User {name: $user})-[r:ACCESSED]->(d:Document {doc_id: $doc_id})
            RETURN r.access_count
            """,
            {"user": "researcher", "doc_id": "doc789"},
        )
        assert result.get_next()[0] == 2

    def test_record_document_requires_persona(self, graph):
        """Test record_document_access requires persona."""
        graph.persona = None
        with pytest.raises(ValueError, match="Persona must be provided"):
            graph.record_document_access("test-doc")


class TestTopicDocumentLinks:
    """Test topic-document relationship tracking."""

    def test_link_topic_to_document(self, graph):
        """Test linking topic to document."""
        # Create topic and document first
        graph.add_topic_interest("RAG")
        graph.record_document_access("doc123", title="RAG Paper")

        # Link them
        graph.link_topic_to_document("RAG", "doc123", relevance=0.95)

        # Relationship should exist
        result = graph.conn.execute(
            """
            MATCH (t:Topic {name: $topic})-[r:RELATED_TO]->(d:Document {doc_id: $doc_id})
            RETURN r.relevance
            """,
            {"topic": "RAG", "doc_id": "doc123"},
        )
        assert result.has_next()
        assert result.get_next()[0] == 0.95

    def test_link_nonexistent_nodes_fails_gracefully(self, graph):
        """Test linking nonexistent nodes doesn't raise error."""
        # Should not raise error, just log warning
        graph.link_topic_to_document("nonexistent-topic", "nonexistent-doc")


class TestQueries:
    """Test graph query operations."""

    def test_get_user_interests_empty(self, graph):
        """Test getting interests when none exist."""
        interests = graph.get_user_interests()
        assert interests == []

    def test_get_user_interests(self, graph):
        """Test getting user interests."""
        graph.add_topic_interest("RAG", interest_level=0.9)
        graph.add_topic_interest("NLP", interest_level=0.7)
        graph.add_topic_interest("Privacy", interest_level=0.8)

        interests = graph.get_user_interests()

        assert len(interests) == 3
        assert all(
            "topic" in i
            and "interest_level" in i
            and "frequency" in i
            and "last_accessed" in i
            for i in interests
        )

        # Should be ordered by frequency
        topics = [i["topic"] for i in interests]
        assert "RAG" in topics

    def test_get_user_interests_requires_persona(self, graph):
        """Test get_user_interests requires persona."""
        graph.persona = None
        with pytest.raises(ValueError, match="Persona must be provided"):
            graph.get_user_interests()

    def test_get_accessed_documents_empty(self, graph):
        """Test getting documents when none accessed."""
        documents = graph.get_accessed_documents()
        assert documents == []

    def test_get_accessed_documents(self, graph):
        """Test getting accessed documents."""
        graph.record_document_access("doc1", title="Paper 1")
        graph.record_document_access("doc2", title="Paper 2")
        graph.record_document_access("doc3", title="Paper 3")

        documents = graph.get_accessed_documents(limit=10)

        assert len(documents) == 3
        assert all(
            "doc_id" in d
            and "title" in d
            and "access_count" in d
            and "last_accessed" in d
            for d in documents
        )

    def test_get_accessed_documents_limit(self, graph):
        """Test getting documents respects limit."""
        for i in range(5):
            graph.record_document_access(f"doc{i}", title=f"Paper {i}")

        documents = graph.get_accessed_documents(limit=2)
        assert len(documents) == 2

    def test_get_related_documents(self, graph):
        """Test getting documents related to topic."""
        # Setup
        graph.add_topic_interest("RAG")
        graph.record_document_access("doc1", title="RAG Paper 1")
        graph.record_document_access("doc2", title="RAG Paper 2")

        graph.link_topic_to_document("RAG", "doc1", relevance=0.9)
        graph.link_topic_to_document("RAG", "doc2", relevance=0.7)

        # Query
        documents = graph.get_related_documents("RAG")

        assert len(documents) == 2
        assert all("doc_id" in d and "title" in d and "relevance" in d for d in documents)
        # Should be ordered by relevance
        assert documents[0]["relevance"] >= documents[1]["relevance"]


class TestDeletion:
    """Test data deletion operations."""

    def test_delete_user_data(self, graph):
        """Test deleting all user data."""
        # Add data
        graph.add_topic_interest("RAG")
        graph.add_topic_interest("NLP")
        graph.record_document_access("doc1")

        # Delete
        count = graph.delete_user_data("researcher", confirm=True)
        assert count == 1

        # User should be gone
        result = graph.conn.execute(
            "MATCH (u:User {name: $name}) RETURN u",
            {"name": "researcher"},
        )
        assert not result.has_next()

    def test_delete_user_requires_confirmation(self, graph):
        """Test delete requires confirmation."""
        graph.add_topic_interest("test")

        with pytest.raises(ValueError, match="confirm=True"):
            graph.delete_user_data("researcher")

    def test_clear_graph(self, graph):
        """Test clearing entire graph."""
        # Add data for multiple users
        graph.ensure_user_exists("user1")
        graph.ensure_user_exists("user2")

        # Clear
        count = graph.clear_graph(confirm=True)
        assert count >= 2

        # Graph should be empty
        result = graph.conn.execute("MATCH (n) RETURN count(n)")
        assert result.get_next()[0] == 0

    def test_clear_graph_requires_confirmation(self, graph):
        """Test clear requires confirmation."""
        with pytest.raises(ValueError, match="confirm=True"):
            graph.clear_graph()


class TestExport:
    """Test graph export operations."""

    def test_export_graph_empty(self, graph):
        """Test exporting when graph is empty."""
        export = graph.export_graph()

        assert export["persona"] == "researcher"
        assert "export_timestamp" in export
        assert export["interests"] == []
        assert export["documents"] == []
        assert export["topic_document_links"] == []

    def test_export_graph_with_data(self, graph):
        """Test exporting graph with data."""
        # Add data
        graph.add_topic_interest("RAG", interest_level=0.9)
        graph.add_topic_interest("NLP", interest_level=0.7)
        graph.record_document_access("doc1", title="Paper 1")
        graph.record_document_access("doc2", title="Paper 2")
        graph.link_topic_to_document("RAG", "doc1", relevance=0.9)

        # Export
        export = graph.export_graph()

        assert len(export["interests"]) == 2
        assert len(export["documents"]) == 2
        assert len(export["topic_document_links"]) == 1

    def test_export_graph_requires_persona(self, graph):
        """Test export requires persona."""
        graph.persona = None
        with pytest.raises(ValueError, match="Persona must be provided"):
            graph.export_graph()


class TestIntegration:
    """Integration tests for knowledge graph."""

    def test_full_workflow(self, graph):
        """Test complete knowledge graph workflow."""
        # Add interests
        graph.add_topic_interest("RAG", interest_level=0.9)
        graph.add_topic_interest("NLP", interest_level=0.8)

        # Access documents
        graph.record_document_access("doc1", title="RAG Paper")
        graph.record_document_access("doc2", title="NLP Survey")
        graph.record_document_access("doc3", title="Privacy in ML")

        # Link topics to documents
        graph.link_topic_to_document("RAG", "doc1", relevance=0.95)
        graph.link_topic_to_document("NLP", "doc2", relevance=0.90)

        # Query interests
        interests = graph.get_user_interests()
        assert len(interests) == 2

        # Query documents
        documents = graph.get_accessed_documents()
        assert len(documents) == 3

        # Query related documents
        rag_docs = graph.get_related_documents("RAG")
        assert len(rag_docs) == 1
        assert rag_docs[0]["doc_id"] == "doc1"

        # Export
        export = graph.export_graph()
        assert export["persona"] == "researcher"
        assert len(export["interests"]) == 2
        assert len(export["documents"]) == 3

        # Delete
        graph.delete_user_data("researcher", confirm=True)

        # Verify deletion
        interests_after = graph.get_user_interests("researcher")
        assert len(interests_after) == 0

    def test_graph_persistence(self, temp_storage):
        """Test graph data persists across instances."""
        # Create first graph and add data
        with KnowledgeGraph(persona="researcher", storage_dir=temp_storage) as graph1:
            graph1.add_topic_interest("RAG", interest_level=0.9)
            graph1.record_document_access("doc1", title="Test Doc")

        # Create second graph and verify data persists
        with KnowledgeGraph(persona="researcher", storage_dir=temp_storage) as graph2:
            interests = graph2.get_user_interests()
            assert len(interests) == 1
            assert interests[0]["topic"] == "RAG"

            documents = graph2.get_accessed_documents()
            assert len(documents) == 1
            assert documents[0]["doc_id"] == "doc1"

    def test_multiple_personas(self, temp_storage):
        """Test multiple personas in same graph."""
        with KnowledgeGraph(storage_dir=temp_storage) as graph:
            # Add data for researcher
            graph.add_topic_interest("RAG", persona="researcher")
            graph.add_topic_interest("NLP", persona="researcher")

            # Add data for student
            graph.add_topic_interest("Python", persona="student")
            graph.add_topic_interest("Databases", persona="student")

            # Verify isolation
            researcher_interests = graph.get_user_interests("researcher")
            assert len(researcher_interests) == 2
            assert all(i["topic"] in ["RAG", "NLP"] for i in researcher_interests)

            student_interests = graph.get_user_interests("student")
            assert len(student_interests) == 2
            assert all(
                i["topic"] in ["Python", "Databases"] for i in student_interests
            )
