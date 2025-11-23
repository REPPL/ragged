"""Knowledge graph for personal memory system.

v0.4.5: Kuzu-based graph database for user-topic-document relationships

Tracks relationships between:
- Users (personas) and topics they're interested in
- Users and documents they've accessed
- Topic co-occurrence and temporal information

Privacy: All data stored locally with full user control.
"""

import shutil
from datetime import datetime
from pathlib import Path
from typing import Any

import kuzu

from ragged.config.settings import get_settings
from ragged.utils.logging import get_logger

logger = get_logger(__name__)


class KnowledgeGraph:
    """Knowledge graph for personal memory using Kuzu.

    Stores relationships between personas, topics, and documents with
    temporal information for personalization and recommendation.

    Privacy-focused features:
    - 100% local storage (embedded database)
    - Full user control (view, query, delete, export)
    - No external connections
    - Data deletion guarantees

    Storage: ~/.ragged/memory/graph/kuzu_db/

    Example:
        >>> graph = KnowledgeGraph(persona="researcher")
        >>> graph.add_topic_interest("RAG", interest_level=0.9)
        >>> graph.record_document_access("doc123", title="RAG Paper")
        >>> interests = graph.get_user_interests()
    """

    def __init__(self, persona: str | None = None, storage_dir: Path | None = None):
        """Initialise knowledge graph.

        Args:
            persona: Default persona for operations
            storage_dir: Custom storage directory (default: ~/.ragged/memory/graph)
        """
        settings = get_settings()
        data_dir = Path(settings.data_dir)

        self.persona = persona
        self.storage_dir = storage_dir or (data_dir / "memory" / "graph")
        self.storage_dir.mkdir(parents=True, exist_ok=True)

        self.db_path = self.storage_dir / "kuzu_db"
        self._init_database()

        logger.info(f"KnowledgeGraph initialised for persona: {persona}")

    def _init_database(self) -> None:
        """Initialise Kuzu database with schema."""
        # Create database
        self.db = kuzu.Database(str(self.db_path))
        self.conn = kuzu.Connection(self.db)

        # Create node tables if they don't exist
        try:
            # Check if tables exist by trying to query them
            self.conn.execute("MATCH (u:User) RETURN u LIMIT 1")
        except Exception:
            # Tables don't exist, create them
            self._create_schema()

        logger.debug(f"Knowledge graph database initialised: {self.db_path}")

    def _create_schema(self) -> None:
        """Create graph schema (nodes and relationships)."""
        # Create User node table
        self.conn.execute(
            """
            CREATE NODE TABLE IF NOT EXISTS User(
                name STRING,
                created_at TIMESTAMP,
                PRIMARY KEY (name)
            )
            """
        )

        # Create Topic node table
        self.conn.execute(
            """
            CREATE NODE TABLE IF NOT EXISTS Topic(
                name STRING,
                interest_level DOUBLE,
                created_at TIMESTAMP,
                PRIMARY KEY (name)
            )
            """
        )

        # Create Document node table
        self.conn.execute(
            """
            CREATE NODE TABLE IF NOT EXISTS Document(
                doc_id STRING,
                title STRING,
                created_at TIMESTAMP,
                PRIMARY KEY (doc_id)
            )
            """
        )

        # Create INTERESTED_IN relationship
        self.conn.execute(
            """
            CREATE REL TABLE IF NOT EXISTS INTERESTED_IN(
                FROM User TO Topic,
                frequency INT64,
                last_accessed TIMESTAMP
            )
            """
        )

        # Create ACCESSED relationship
        self.conn.execute(
            """
            CREATE REL TABLE IF NOT EXISTS ACCESSED(
                FROM User TO Document,
                access_count INT64,
                last_accessed TIMESTAMP,
                first_accessed TIMESTAMP
            )
            """
        )

        # Create RELATED_TO relationship (topics to documents)
        self.conn.execute(
            """
            CREATE REL TABLE IF NOT EXISTS RELATED_TO(
                FROM Topic TO Document,
                relevance DOUBLE
            )
            """
        )

        logger.info("Created knowledge graph schema")

    def ensure_user_exists(self, persona: str | None = None) -> None:
        """Ensure user node exists for persona.

        Args:
            persona: Persona name (uses default if not provided)
        """
        persona = persona or self.persona
        if not persona:
            raise ValueError("Persona must be provided")

        # Check if user exists
        result = self.conn.execute(
            "MATCH (u:User {name: $name}) RETURN u",
            {"name": persona},
        )
        if not result.has_next():
            # Create user node
            self.conn.execute(
                "CREATE (u:User {name: $name, created_at: $created_at})",
                {"name": persona, "created_at": datetime.now()},
            )
            logger.debug(f"Created user node: {persona}")

    def add_topic_interest(
        self,
        topic: str,
        interest_level: float = 0.5,
        persona: str | None = None,
    ) -> None:
        """Add or update topic interest for persona.

        Args:
            topic: Topic name
            interest_level: Interest level (0.0-1.0)
            persona: Persona name (uses default if not provided)
        """
        persona = persona or self.persona
        if not persona:
            raise ValueError("Persona must be provided")

        self.ensure_user_exists(persona)

        # Create topic node if it doesn't exist
        result = self.conn.execute(
            "MATCH (t:Topic {name: $name}) RETURN t",
            {"name": topic},
        )
        if not result.has_next():
            self.conn.execute(
                "CREATE (t:Topic {name: $name, interest_level: $level, created_at: $created_at})",
                {"name": topic, "level": interest_level, "created_at": datetime.now()},
            )

        # Create or update INTERESTED_IN relationship
        self.conn.execute(
            """
            MATCH (u:User {name: $user}), (t:Topic {name: $topic})
            MERGE (u)-[r:INTERESTED_IN]->(t)
            ON CREATE SET r.frequency = 1, r.last_accessed = $timestamp
            ON MATCH SET r.frequency = r.frequency + 1, r.last_accessed = $timestamp
            """,
            {"user": persona, "topic": topic, "timestamp": datetime.now()},
        )

        logger.debug(f"Updated topic interest: {persona} -> {topic}")

    def record_document_access(
        self,
        doc_id: str,
        title: str = "",
        persona: str | None = None,
    ) -> None:
        """Record document access for persona.

        Args:
            doc_id: Document identifier
            title: Document title
            persona: Persona name (uses default if not provided)
        """
        persona = persona or self.persona
        if not persona:
            raise ValueError("Persona must be provided")

        self.ensure_user_exists(persona)

        # Create document node if it doesn't exist
        result = self.conn.execute(
            "MATCH (d:Document {doc_id: $doc_id}) RETURN d",
            {"doc_id": doc_id},
        )
        if not result.has_next():
            self.conn.execute(
                "CREATE (d:Document {doc_id: $doc_id, title: $title, created_at: $created_at})",
                {"doc_id": doc_id, "title": title, "created_at": datetime.now()},
            )

        # Create or update ACCESSED relationship
        timestamp = datetime.now()
        self.conn.execute(
            """
            MATCH (u:User {name: $user}), (d:Document {doc_id: $doc_id})
            MERGE (u)-[r:ACCESSED]->(d)
            ON CREATE SET r.access_count = 1, r.first_accessed = $timestamp, r.last_accessed = $timestamp
            ON MATCH SET r.access_count = r.access_count + 1, r.last_accessed = $timestamp
            """,
            {"user": persona, "doc_id": doc_id, "timestamp": timestamp},
        )

        logger.debug(f"Recorded document access: {persona} -> {doc_id}")

    def link_topic_to_document(
        self,
        topic: str,
        doc_id: str,
        relevance: float = 0.5,
    ) -> None:
        """Link a topic to a document.

        Args:
            topic: Topic name
            doc_id: Document identifier
            relevance: Relevance score (0.0-1.0)
        """
        # Ensure both nodes exist
        topic_exists = self.conn.execute(
            "MATCH (t:Topic {name: $name}) RETURN t",
            {"name": topic},
        ).has_next()

        doc_exists = self.conn.execute(
            "MATCH (d:Document {doc_id: $doc_id}) RETURN d",
            {"doc_id": doc_id},
        ).has_next()

        if not topic_exists or not doc_exists:
            logger.warning(
                f"Cannot link {topic} to {doc_id}: one or both nodes don't exist"
            )
            return

        # Create relationship
        self.conn.execute(
            """
            MATCH (t:Topic {name: $topic}), (d:Document {doc_id: $doc_id})
            MERGE (t)-[r:RELATED_TO]->(d)
            ON CREATE SET r.relevance = $relevance
            ON MATCH SET r.relevance = $relevance
            """,
            {"topic": topic, "doc_id": doc_id, "relevance": relevance},
        )

        logger.debug(f"Linked topic to document: {topic} -> {doc_id}")

    def get_user_interests(self, persona: str | None = None) -> list[dict[str, Any]]:
        """Get topics of interest for persona.

        Args:
            persona: Persona name (uses default if not provided)

        Returns:
            List of topic dictionaries with interest data
        """
        persona = persona or self.persona
        if not persona:
            raise ValueError("Persona must be provided")

        result = self.conn.execute(
            """
            MATCH (u:User {name: $user})-[r:INTERESTED_IN]->(t:Topic)
            RETURN t.name as topic, t.interest_level as interest_level,
                   r.frequency as frequency, r.last_accessed as last_accessed
            ORDER BY r.frequency DESC
            """,
            {"user": persona},
        )

        interests = []
        while result.has_next():
            row = result.get_next()
            interests.append(
                {
                    "topic": row[0],
                    "interest_level": row[1],
                    "frequency": row[2],
                    "last_accessed": row[3],
                }
            )

        return interests

    def get_accessed_documents(
        self, persona: str | None = None, limit: int = 10
    ) -> list[dict[str, Any]]:
        """Get recently accessed documents for persona.

        Args:
            persona: Persona name (uses default if not provided)
            limit: Maximum number of documents to return

        Returns:
            List of document dictionaries with access data
        """
        persona = persona or self.persona
        if not persona:
            raise ValueError("Persona must be provided")

        result = self.conn.execute(
            """
            MATCH (u:User {name: $user})-[r:ACCESSED]->(d:Document)
            RETURN d.doc_id as doc_id, d.title as title,
                   r.access_count as access_count, r.last_accessed as last_accessed
            ORDER BY r.last_accessed DESC
            LIMIT $limit
            """,
            {"user": persona, "limit": limit},
        )

        documents = []
        while result.has_next():
            row = result.get_next()
            documents.append(
                {
                    "doc_id": row[0],
                    "title": row[1],
                    "access_count": row[2],
                    "last_accessed": row[3],
                }
            )

        return documents

    def get_related_documents(
        self, topic: str, limit: int = 10
    ) -> list[dict[str, Any]]:
        """Get documents related to a topic.

        Args:
            topic: Topic name
            limit: Maximum number of documents to return

        Returns:
            List of document dictionaries with relevance data
        """
        result = self.conn.execute(
            """
            MATCH (t:Topic {name: $topic})-[r:RELATED_TO]->(d:Document)
            RETURN d.doc_id as doc_id, d.title as title, r.relevance as relevance
            ORDER BY r.relevance DESC
            LIMIT $limit
            """,
            {"topic": topic, "limit": limit},
        )

        documents = []
        while result.has_next():
            row = result.get_next()
            documents.append(
                {"doc_id": row[0], "title": row[1], "relevance": row[2]}
            )

        return documents

    def delete_user_data(self, persona: str, confirm: bool = False) -> int:
        """Delete all data for a persona.

        Args:
            persona: Persona name to delete
            confirm: Confirmation flag (required for safety)

        Returns:
            Number of nodes deleted

        Raises:
            ValueError: If confirmation not provided
        """
        if not confirm:
            raise ValueError("Must set confirm=True to delete user data")

        # Count nodes before deletion
        result = self.conn.execute(
            """
            MATCH (u:User {name: $user})
            OPTIONAL MATCH (u)-[r]-()
            RETURN count(r) as rel_count
            """,
            {"user": persona},
        )

        # Delete user and all relationships
        self.conn.execute(
            """
            MATCH (u:User {name: $user})
            DETACH DELETE u
            """,
            {"user": persona},
        )

        logger.info(f"Deleted user data for persona: {persona}")
        return 1  # User node deleted

    def export_graph(self, persona: str | None = None) -> dict[str, Any]:
        """Export graph data for a persona.

        Args:
            persona: Persona name (uses default if not provided)

        Returns:
            Dictionary with nodes and relationships
        """
        persona = persona or self.persona
        if not persona:
            raise ValueError("Persona must be provided")

        # Export interests
        interests = self.get_user_interests(persona)

        # Export documents
        documents = self.get_accessed_documents(persona, limit=1000)

        # Export topic-document relationships
        topic_docs = []
        for interest in interests:
            topic = interest["topic"]
            related = self.get_related_documents(topic, limit=100)
            for doc in related:
                topic_docs.append(
                    {
                        "topic": topic,
                        "doc_id": doc["doc_id"],
                        "relevance": doc["relevance"],
                    }
                )

        return {
            "persona": persona,
            "export_timestamp": datetime.now().isoformat(),
            "interests": interests,
            "documents": documents,
            "topic_document_links": topic_docs,
        }

    def clear_graph(self, confirm: bool = False) -> int:
        """Clear entire graph database.

        WARNING: This deletes ALL data for ALL personas.

        Args:
            confirm: Confirmation flag (required for safety)

        Returns:
            Number of nodes deleted

        Raises:
            ValueError: If confirmation not provided
        """
        if not confirm:
            raise ValueError("Must set confirm=True to clear entire graph")

        # Count nodes
        result = self.conn.execute("MATCH (n) RETURN count(n) as count")
        count = 0
        if result.has_next():
            count = result.get_next()[0]

        # Delete all nodes and relationships
        self.conn.execute("MATCH (n) DETACH DELETE n")

        logger.warning(f"Cleared entire knowledge graph: {count} nodes deleted")
        return count

    def close(self) -> None:
        """Close database connection."""
        if hasattr(self, "conn"):
            del self.conn
        if hasattr(self, "db"):
            del self.db
        logger.debug("Knowledge graph connection closed")

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()

    def __del__(self):
        """Finalizer to ensure connection is closed."""
        try:
            self.close()
        except Exception:
            # Silently ignore errors during cleanup
            pass
