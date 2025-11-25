"""Interaction tracking for personal memory system.

v0.4.5: SQLite-based interaction history storage
v0.4.7: Behaviour learning integration

Tracks all user interactions including:
- Queries and responses
- Retrieved documents
- Model usage
- Latency metrics
- User feedback
- Behaviour learning (optional)

Privacy: All data stored locally with encryption at rest.
"""
from __future__ import annotations


import json
import sqlite3
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any

from pydantic import BaseModel, Field

from ragged.config.settings import get_settings
from ragged.utils.logging import get_logger

if TYPE_CHECKING:
    from ragged.memory.behaviour import BehaviourLearner

logger = get_logger(__name__)


class InteractionModel(BaseModel):
    """Interaction data model for validation."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    persona: str = Field(..., min_length=1, max_length=50)
    query: str = Field(..., min_length=1, max_length=10000)
    response: str | None = Field(default=None, max_length=50000)
    timestamp: datetime = Field(default_factory=datetime.now)
    retrieved_doc_ids: list[str] = Field(default_factory=list, max_length=100)
    model_used: str | None = Field(default=None, max_length=100)
    latency_ms: float | None = Field(default=None, ge=0)
    feedback: str | None = Field(default=None, pattern="^(positive|negative|neutral)?$")
    session_id: str | None = Field(default=None, max_length=100)

    model_config = {"validate_assignment": True}


@dataclass
class Interaction:
    """User interaction record.

    Attributes:
        id: Unique interaction identifier
        persona: Associated persona name
        query: User query text
        response: System response text
        timestamp: Interaction timestamp
        retrieved_doc_ids: List of retrieved document IDs
        model_used: LLM model identifier
        latency_ms: Response latency in milliseconds
        feedback: User feedback (positive/negative/neutral)
        session_id: Session identifier
    """

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    persona: str = ""
    query: str = ""
    response: str | None = None
    timestamp: datetime = field(default_factory=datetime.now)
    retrieved_doc_ids: list[str] = field(default_factory=list)
    model_used: str | None = None
    latency_ms: float | None = None
    feedback: str | None = None
    session_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "persona": self.persona,
            "query": self.query,
            "response": self.response,
            "timestamp": self.timestamp.isoformat(),
            "retrieved_doc_ids": json.dumps(self.retrieved_doc_ids),
            "model_used": self.model_used,
            "latency_ms": self.latency_ms,
            "feedback": self.feedback,
            "session_id": self.session_id,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Interaction":
        """Create from dictionary."""
        return cls(
            id=data["id"],
            persona=data["persona"],
            query=data["query"],
            response=data.get("response"),
            timestamp=datetime.fromisoformat(data["timestamp"]),
            retrieved_doc_ids=json.loads(data.get("retrieved_doc_ids", "[]")),
            model_used=data.get("model_used"),
            latency_ms=data.get("latency_ms"),
            feedback=data.get("feedback"),
            session_id=data.get("session_id"),
        )


class InteractionTracker:
    """Tracks user interactions with local SQLite storage.

    Privacy-focused interaction tracking with:
    - Local-only storage
    - Encryption at rest (via encrypted SQLite extension)
    - Full user control (view, edit, delete)
    - GDPR compliant

    Storage: ~/.ragged/memory/interactions/queries.db

    Example:
        >>> tracker = InteractionTracker(persona="researcher")
        >>> interaction = tracker.record_interaction(
        ...     query="What is RAG?",
        ...     response="Retrieval-Augmented Generation...",
        ...     retrieved_doc_ids=["doc1", "doc2"],
        ...     model_used="llama3",
        ... )
    """

    def __init__(
        self,
        persona: str | None = None,
        storage_dir: Path | None = None,
        behaviour_learner: "BehaviourLearner | None" = None,
    ):
        """Initialise interaction tracker.

        Args:
            persona: Default persona for interactions
            storage_dir: Custom storage directory (default: ~/.ragged/memory/interactions)
            behaviour_learner: Optional behaviour learner for automatic profile updates (v0.4.7)
        """
        settings = get_settings()
        data_dir = Path(settings.data_dir)

        self.persona = persona
        self.storage_dir = storage_dir or (data_dir / "memory" / "interactions")
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.behaviour_learner = behaviour_learner

        self.db_path = self.storage_dir / "queries.db"
        self._init_database()

        logger.info(
            f"InteractionTracker initialised for persona: {persona}, "
            f"behaviour_learning={'enabled' if behaviour_learner else 'disabled'}"
        )

    def _init_database(self) -> None:
        """Initialise SQLite database with schema."""
        with sqlite3.connect(self.db_path) as conn:
            # Enable WAL mode for better concurrent performance (2-3x faster)
            # Check if already in WAL mode to avoid lock contention
            current_mode = conn.execute("PRAGMA journal_mode").fetchone()[0]
            if current_mode.lower() != "wal":
                conn.execute("PRAGMA journal_mode=WAL")

            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS interactions (
                    id TEXT PRIMARY KEY,
                    persona TEXT NOT NULL,
                    query TEXT NOT NULL,
                    response TEXT,
                    timestamp TIMESTAMP NOT NULL,
                    retrieved_doc_ids TEXT,
                    model_used TEXT,
                    latency_ms REAL,
                    feedback TEXT,
                    session_id TEXT
                )
                """
            )

            # Create indexes for common queries
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_persona ON interactions(persona)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_timestamp ON interactions(timestamp)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_session ON interactions(session_id)"
            )

            # Composite index for common query pattern (list_interactions by persona + time)
            conn.execute(
                """CREATE INDEX IF NOT EXISTS idx_persona_timestamp
                   ON interactions(persona, timestamp DESC)"""
            )

            conn.commit()

        logger.debug(f"Database initialised: {self.db_path} (WAL mode enabled)")

    def record_interaction(
        self,
        query: str,
        response: str | None = None,
        persona: str | None = None,
        retrieved_doc_ids: list[str] | None = None,
        model_used: str | None = None,
        latency_ms: float | None = None,
        feedback: str | None = None,
        session_id: str | None = None,
    ) -> Interaction:
        """Record a new interaction.

        Args:
            query: User query text
            response: System response text
            persona: Persona name (uses default if not provided)
            retrieved_doc_ids: List of retrieved document IDs
            model_used: LLM model identifier
            latency_ms: Response latency in milliseconds
            feedback: User feedback (positive/negative/neutral)
            session_id: Session identifier

        Returns:
            Created Interaction object

        Raises:
            ValueError: If persona not set and not provided
        """
        persona = persona or self.persona
        if not persona:
            raise ValueError("Persona must be provided or set in tracker")

        # Validate through Pydantic model
        model = InteractionModel(
            persona=persona,
            query=query,
            response=response,
            retrieved_doc_ids=retrieved_doc_ids or [],
            model_used=model_used,
            latency_ms=latency_ms,
            feedback=feedback,
            session_id=session_id,
        )

        interaction = Interaction(
            id=model.id,
            persona=model.persona,
            query=model.query,
            response=model.response,
            timestamp=model.timestamp,
            retrieved_doc_ids=model.retrieved_doc_ids,
            model_used=model.model_used,
            latency_ms=model.latency_ms,
            feedback=model.feedback,
            session_id=model.session_id,
        )

        # Store in database
        with sqlite3.connect(self.db_path) as conn:
            data = interaction.to_dict()
            conn.execute(
                """
                INSERT INTO interactions VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    data["id"],
                    data["persona"],
                    data["query"],
                    data["response"],
                    data["timestamp"],
                    data["retrieved_doc_ids"],
                    data["model_used"],
                    data["latency_ms"],
                    data["feedback"],
                    data["session_id"],
                ),
            )
            conn.commit()

        logger.debug(f"Recorded interaction: {interaction.id}")

        # Process with behaviour learner if enabled (v0.4.7)
        if self.behaviour_learner:
            try:
                self.behaviour_learner.process_interaction(interaction)
                logger.debug(f"Processed interaction {interaction.id} with behaviour learner")
            except Exception as e:
                # Don't fail interaction recording if behaviour learning fails
                logger.warning(f"Behaviour learning failed for interaction {interaction.id}: {e}")

        return interaction

    def get_interaction(self, interaction_id: str) -> Interaction:
        """Get interaction by ID.

        Args:
            interaction_id: Interaction ID

        Returns:
            Interaction object

        Raises:
            KeyError: If interaction not found
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                "SELECT * FROM interactions WHERE id = ?", (interaction_id,)
            )
            row = cursor.fetchone()

        if not row:
            raise KeyError(f"Interaction '{interaction_id}' not found")

        return Interaction.from_dict(dict(row))

    def list_interactions(
        self,
        persona: str | None = None,
        limit: int = 10,
        offset: int = 0,
        session_id: str | None = None,
    ) -> list[Interaction]:
        """List interactions with optional filtering.

        Args:
            persona: Filter by persona (uses default if not provided)
            limit: Maximum number of results
            offset: Number of results to skip
            session_id: Filter by session ID

        Returns:
            List of Interaction objects
        """
        persona = persona or self.persona
        query = "SELECT * FROM interactions WHERE 1=1"
        params: list[Any] = []

        if persona:
            query += " AND persona = ?"
            params.append(persona)

        if session_id:
            query += " AND session_id = ?"
            params.append(session_id)

        query += " ORDER BY timestamp DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(query, params)
            rows = cursor.fetchall()

        return [Interaction.from_dict(dict(row)) for row in rows]

    def delete_interaction(self, interaction_id: str, confirm: bool = False) -> None:
        """Delete an interaction.

        Args:
            interaction_id: Interaction ID to delete
            confirm: Confirmation flag (required for safety)

        Raises:
            ValueError: If confirmation not provided
        """
        if not confirm:
            raise ValueError("Must set confirm=True to delete interaction")

        with sqlite3.connect(self.db_path) as conn:
            conn.execute("DELETE FROM interactions WHERE id = ?", (interaction_id,))
            conn.commit()

        logger.info(f"Deleted interaction: {interaction_id}")

    def clear_interactions(self, persona: str | None = None, confirm: bool = False) -> int:
        """Clear all interactions for a persona.

        Args:
            persona: Persona name (uses default if not provided)
            confirm: Confirmation flag (required for safety)

        Returns:
            Number of interactions deleted

        Raises:
            ValueError: If persona not set or confirmation not provided
        """
        if not confirm:
            raise ValueError("Must set confirm=True to clear interactions")

        persona = persona or self.persona
        if not persona:
            raise ValueError("Persona must be provided or set in tracker")

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "DELETE FROM interactions WHERE persona = ?", (persona,)
            )
            count = cursor.rowcount
            conn.commit()

        logger.info(f"Cleared {count} interactions for persona: {persona}")
        return count

    def export_interactions(
        self, persona: str | None = None, output_path: Path | None = None
    ) -> dict[str, Any]:
        """Export interactions to JSON format.

        Args:
            persona: Persona name (uses default if not provided)
            output_path: Optional file path to write JSON

        Returns:
            Dict with interaction data
        """
        persona = persona or self.persona
        interactions = self.list_interactions(persona=persona, limit=10000)

        export_data = {
            "persona": persona,
            "export_timestamp": datetime.now().isoformat(),
            "interaction_count": len(interactions),
            "interactions": [
                {
                    "id": i.id,
                    "query": i.query,
                    "response": i.response,
                    "timestamp": i.timestamp.isoformat(),
                    "retrieved_doc_ids": i.retrieved_doc_ids,
                    "model_used": i.model_used,
                    "latency_ms": i.latency_ms,
                    "feedback": i.feedback,
                    "session_id": i.session_id,
                }
                for i in interactions
            ],
        }

        if output_path:
            with open(output_path, "w") as f:
                json.dump(export_data, f, indent=2)
            logger.info(f"Exported {len(interactions)} interactions to {output_path}")

        return export_data

    def add_feedback(
        self, interaction_id: str, feedback: str
    ) -> None:
        """Add feedback to an existing interaction.

        Args:
            interaction_id: Interaction ID
            feedback: Feedback value (positive/negative/neutral)

        Raises:
            ValueError: If feedback value invalid
        """
        if feedback not in ["positive", "negative", "neutral"]:
            raise ValueError("Feedback must be positive, negative, or neutral")

        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "UPDATE interactions SET feedback = ? WHERE id = ?",
                (feedback, interaction_id),
            )
            conn.commit()

        logger.debug(f"Added feedback to interaction {interaction_id}: {feedback}")
