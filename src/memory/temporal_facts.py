"""Temporal fact storage and management.

This module provides storage for facts that change over time, with support for:
- Fact validity periods (valid_from, valid_to)
- Fact versioning and history
- Temporal queries (facts at specific time, current facts)
- Fact updates and rollback

Part of v0.4.10 Advanced Temporal Features implementation.
"""

from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
import sqlite3
import json
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


@dataclass
class TemporalFact:
    """Fact with temporal validity.

    Attributes:
        id: Unique fact identifier
        persona: Associated persona
        fact_type: Category (e.g., "employment", "learning", "location")
        content: Fact content/description
        valid_from: Start of validity period
        valid_to: End of validity period (None = current)
        confidence: Confidence score (0.0-1.0)
        source: How fact was learned
        metadata: Additional metadata
        created_at: Creation timestamp
        updated_at: Last update timestamp
    """

    id: str
    persona: str
    fact_type: str
    content: str
    valid_from: datetime
    valid_to: Optional[datetime] = None
    confidence: float = 1.0
    source: str = "manual"
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def is_valid_at(self, timestamp: datetime) -> bool:
        """Check if fact is valid at given timestamp.

        Args:
            timestamp: Time to check validity at

        Returns:
            True if fact is valid at timestamp
        """
        # Valid from must be before or at timestamp
        if self.valid_from > timestamp:
            return False

        # If no end time, fact is currently valid
        if self.valid_to is None:
            return True

        # Check if timestamp is before end time
        return timestamp <= self.valid_to

    def is_current(self) -> bool:
        """Check if fact is currently valid.

        Returns:
            True if valid_to is None (ongoing)
        """
        return self.valid_to is None

    def overlaps_with(self, other: 'TemporalFact') -> bool:
        """Check if validity periods overlap with another fact.

        Args:
            other: Another temporal fact

        Returns:
            True if validity periods overlap
        """
        # Get end times (use far future for None)
        self_end = self.valid_to or datetime(9999, 12, 31, tzinfo=timezone.utc)
        other_end = other.valid_to or datetime(9999, 12, 31, tzinfo=timezone.utc)

        # Check for overlap
        return (self.valid_from <= other_end and
                other.valid_from <= self_end)


@dataclass
class FactVersion:
    """Version of a fact (for tracking changes).

    Attributes:
        fact_id: Parent fact ID
        version: Version number
        content: Fact content at this version
        valid_from: Start of validity
        valid_to: End of validity
        updated_at: When this version was created
        update_reason: Why fact was updated
        metadata: Version-specific metadata
    """

    fact_id: str
    version: int
    content: str
    valid_from: datetime
    valid_to: datetime
    updated_at: datetime
    update_reason: str
    metadata: Dict[str, Any] = field(default_factory=dict)


class TemporalFactStore:
    """Storage and retrieval for temporal facts.

    Provides:
    - Fact persistence in SQLite
    - Temporal queries (facts at time, current facts)
    - Fact versioning and history
    - Update and deletion operations
    """

    def __init__(self, db_path: Optional[str] = None):
        """Initialise temporal fact store.

        Args:
            db_path: Path to SQLite database (None = in-memory)
        """
        self.db_path = db_path or ":memory:"
        self._init_database()

    def _init_database(self):
        """Initialise database schema."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS temporal_facts (
                    id TEXT PRIMARY KEY,
                    persona TEXT NOT NULL,
                    fact_type TEXT NOT NULL,
                    content TEXT NOT NULL,
                    valid_from TEXT NOT NULL,
                    valid_to TEXT,
                    confidence REAL NOT NULL,
                    source TEXT NOT NULL,
                    metadata TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """)

            conn.execute("""
                CREATE TABLE IF NOT EXISTS fact_versions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    fact_id TEXT NOT NULL,
                    version INTEGER NOT NULL,
                    content TEXT NOT NULL,
                    valid_from TEXT NOT NULL,
                    valid_to TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    update_reason TEXT NOT NULL,
                    metadata TEXT,
                    FOREIGN KEY(fact_id) REFERENCES temporal_facts(id)
                )
            """)

            # Create indexes for performance
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_facts_persona
                ON temporal_facts(persona)
            """)

            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_facts_type
                ON temporal_facts(fact_type)
            """)

            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_facts_validity
                ON temporal_facts(valid_from, valid_to)
            """)

            conn.commit()

    def add_fact(self, fact: TemporalFact) -> None:
        """Add new temporal fact.

        Args:
            fact: Temporal fact to add

        Raises:
            ValueError: If fact with same ID already exists
        """
        with sqlite3.connect(self.db_path) as conn:
            try:
                conn.execute("""
                    INSERT INTO temporal_facts
                    (id, persona, fact_type, content, valid_from, valid_to,
                     confidence, source, metadata, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    fact.id,
                    fact.persona,
                    fact.fact_type,
                    fact.content,
                    fact.valid_from.isoformat(),
                    fact.valid_to.isoformat() if fact.valid_to else None,
                    fact.confidence,
                    fact.source,
                    json.dumps(fact.metadata),
                    fact.created_at.isoformat(),
                    fact.updated_at.isoformat()
                ))
                conn.commit()
                logger.info(f"Added temporal fact {fact.id} for {fact.persona}")
            except sqlite3.IntegrityError as e:
                raise ValueError(f"Fact with ID {fact.id} already exists") from e

    def get_fact(self, fact_id: str) -> Optional[TemporalFact]:
        """Get fact by ID.

        Args:
            fact_id: Fact identifier

        Returns:
            Temporal fact or None if not found
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                "SELECT * FROM temporal_facts WHERE id = ?",
                (fact_id,)
            )
            row = cursor.fetchone()

            if row is None:
                return None

            return self._row_to_fact(row)

    def get_facts_at(
        self,
        persona: str,
        timestamp: datetime,
        fact_type: Optional[str] = None
    ) -> List[TemporalFact]:
        """Get facts valid at specific time.

        Args:
            persona: Persona name
            timestamp: Time to check validity at
            fact_type: Optional fact type filter

        Returns:
            List of facts valid at timestamp
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row

            # Build query
            query = """
                SELECT * FROM temporal_facts
                WHERE persona = ?
                AND valid_from <= ?
                AND (valid_to IS NULL OR valid_to >= ?)
            """
            params = [persona, timestamp.isoformat(), timestamp.isoformat()]

            if fact_type:
                query += " AND fact_type = ?"
                params.append(fact_type)

            cursor = conn.execute(query, params)
            rows = cursor.fetchall()

            return [self._row_to_fact(row) for row in rows]

    def get_current_facts(
        self,
        persona: str,
        fact_type: Optional[str] = None
    ) -> List[TemporalFact]:
        """Get currently valid facts.

        Args:
            persona: Persona name
            fact_type: Optional fact type filter

        Returns:
            List of current facts (valid_to is None)
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row

            query = """
                SELECT * FROM temporal_facts
                WHERE persona = ?
                AND valid_to IS NULL
            """
            params = [persona]

            if fact_type:
                query += " AND fact_type = ?"
                params.append(fact_type)

            cursor = conn.execute(query, params)
            rows = cursor.fetchall()

            return [self._row_to_fact(row) for row in rows]

    def update_fact(
        self,
        fact_id: str,
        content: Optional[str] = None,
        valid_to: Optional[datetime] = None,
        confidence: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None,
        update_reason: str = "manual update"
    ) -> TemporalFact:
        """Update existing fact, creating new version.

        Args:
            fact_id: Fact to update
            content: New content (None = keep current)
            valid_to: New end time (None = keep current)
            confidence: New confidence (None = keep current)
            metadata: New metadata (None = keep current)
            update_reason: Reason for update

        Returns:
            Updated fact

        Raises:
            ValueError: If fact not found
        """
        fact = self.get_fact(fact_id)
        if fact is None:
            raise ValueError(f"Fact {fact_id} not found")

        # Create version entry
        version = self._get_next_version(fact_id)
        self._save_version(FactVersion(
            fact_id=fact_id,
            version=version,
            content=fact.content,
            valid_from=fact.valid_from,
            valid_to=fact.valid_to or datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            update_reason=update_reason,
            metadata=fact.metadata.copy()
        ))

        # Update fact
        if content is not None:
            fact.content = content
        if valid_to is not None:
            fact.valid_to = valid_to
        if confidence is not None:
            fact.confidence = confidence
        if metadata is not None:
            fact.metadata.update(metadata)

        fact.updated_at = datetime.now(timezone.utc)

        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                UPDATE temporal_facts
                SET content = ?, valid_to = ?, confidence = ?,
                    metadata = ?, updated_at = ?
                WHERE id = ?
            """, (
                fact.content,
                fact.valid_to.isoformat() if fact.valid_to else None,
                fact.confidence,
                json.dumps(fact.metadata),
                fact.updated_at.isoformat(),
                fact_id
            ))
            conn.commit()

        logger.info(f"Updated fact {fact_id} (version {version})")
        return fact

    def get_fact_history(self, fact_id: str) -> List[FactVersion]:
        """Get version history for fact.

        Args:
            fact_id: Fact identifier

        Returns:
            List of fact versions, ordered by version number
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT * FROM fact_versions
                WHERE fact_id = ?
                ORDER BY version ASC
            """, (fact_id,))
            rows = cursor.fetchall()

            return [self._row_to_version(row) for row in rows]

    def delete_fact(self, fact_id: str) -> None:
        """Delete fact and all versions.

        Args:
            fact_id: Fact to delete
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("DELETE FROM fact_versions WHERE fact_id = ?", (fact_id,))
            conn.execute("DELETE FROM temporal_facts WHERE id = ?", (fact_id,))
            conn.commit()

        logger.info(f"Deleted fact {fact_id}")

    def _row_to_fact(self, row: sqlite3.Row) -> TemporalFact:
        """Convert database row to TemporalFact."""
        return TemporalFact(
            id=row['id'],
            persona=row['persona'],
            fact_type=row['fact_type'],
            content=row['content'],
            valid_from=datetime.fromisoformat(row['valid_from']),
            valid_to=datetime.fromisoformat(row['valid_to']) if row['valid_to'] else None,
            confidence=row['confidence'],
            source=row['source'],
            metadata=json.loads(row['metadata']) if row['metadata'] else {},
            created_at=datetime.fromisoformat(row['created_at']),
            updated_at=datetime.fromisoformat(row['updated_at'])
        )

    def _row_to_version(self, row: sqlite3.Row) -> FactVersion:
        """Convert database row to FactVersion."""
        return FactVersion(
            fact_id=row['fact_id'],
            version=row['version'],
            content=row['content'],
            valid_from=datetime.fromisoformat(row['valid_from']),
            valid_to=datetime.fromisoformat(row['valid_to']),
            updated_at=datetime.fromisoformat(row['updated_at']),
            update_reason=row['update_reason'],
            metadata=json.loads(row['metadata']) if row['metadata'] else {}
        )

    def _get_next_version(self, fact_id: str) -> int:
        """Get next version number for fact."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT MAX(version) FROM fact_versions WHERE fact_id = ?
            """, (fact_id,))
            max_version = cursor.fetchone()[0]
            return (max_version or 0) + 1

    def _save_version(self, version: FactVersion) -> None:
        """Save fact version to database."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO fact_versions
                (fact_id, version, content, valid_from, valid_to,
                 updated_at, update_reason, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                version.fact_id,
                version.version,
                version.content,
                version.valid_from.isoformat(),
                version.valid_to.isoformat(),
                version.updated_at.isoformat(),
                version.update_reason,
                json.dumps(version.metadata)
            ))
            conn.commit()
