"""Interest profile management (v0.4.7).

Builds and maintains user interest profiles based on behaviour patterns.

Privacy: All profiles stored locally, persona-scoped, GDPR compliant.
"""

import json
import sqlite3
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional

from ragged.memory.topics import Topic
from ragged.utils.logging import get_logger

logger = get_logger(__name__)


@dataclass
class TopicInterest:
    """Single topic interest with behaviour metrics.

    Attributes:
        topic: Topic name
        frequency: How many times topic appeared
        recency: Time decay factor (0.0-1.0, 1.0 = just seen)
        confidence: Interest confidence (0.0-1.0)
        first_seen: First occurrence timestamp
        last_seen: Most recent occurrence timestamp
        related_documents: Document IDs associated with this topic
        co_occurring_topics: Related topics that appear together (topic -> count)
    """

    topic: str
    frequency: int = 1
    recency: float = 1.0
    confidence: float = 0.5
    first_seen: datetime = field(default_factory=datetime.now)
    last_seen: datetime = field(default_factory=datetime.now)
    related_documents: List[str] = field(default_factory=list)
    co_occurring_topics: Dict[str, int] = field(default_factory=dict)

    def __post_init__(self):
        """Validate topic interest data."""
        if not 0.0 <= self.recency <= 1.0:
            raise ValueError(f"Recency must be 0.0-1.0, got {self.recency}")
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError(f"Confidence must be 0.0-1.0, got {self.confidence}")
        if self.frequency < 1:
            raise ValueError(f"Frequency must be >= 1, got {self.frequency}")

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "topic": self.topic,
            "frequency": self.frequency,
            "recency": self.recency,
            "confidence": self.confidence,
            "first_seen": self.first_seen.isoformat(),
            "last_seen": self.last_seen.isoformat(),
            "related_documents": self.related_documents,
            "co_occurring_topics": self.co_occurring_topics,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "TopicInterest":
        """Create from dictionary (JSON deserialization)."""
        return cls(
            topic=data["topic"],
            frequency=data["frequency"],
            recency=data["recency"],
            confidence=data["confidence"],
            first_seen=datetime.fromisoformat(data["first_seen"]),
            last_seen=datetime.fromisoformat(data["last_seen"]),
            related_documents=data.get("related_documents", []),
            co_occurring_topics=data.get("co_occurring_topics", {}),
        )


@dataclass
class InterestProfile:
    """User interest profile with behaviour patterns.

    Attributes:
        persona: Persona name
        topics: Topic interests (topic_name -> TopicInterest)
        created_at: Profile creation timestamp
        updated_at: Last update timestamp
    """

    persona: str
    topics: Dict[str, TopicInterest] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def update_topic_interest(
        self,
        topic: Topic,
        doc_ids: Optional[List[str]] = None,
        related_topics: Optional[List[str]] = None,
    ) -> None:
        """Update interest for a topic.

        Args:
            topic: Extracted topic to update
            doc_ids: Optional document IDs related to this topic
            related_topics: Optional co-occurring topics

        Example:
            >>> profile = InterestProfile(persona="user")
            >>> topic = Topic(name="RAG", confidence=0.9)
            >>> profile.update_topic_interest(topic, doc_ids=["doc1.pdf"])
            >>> profile.topics["RAG"].frequency
            1
        """
        topic_name = topic.name.lower()  # Normalize

        if topic_name in self.topics:
            # Update existing topic
            interest = self.topics[topic_name]
            interest.frequency += 1
            interest.last_seen = datetime.now()
            interest.recency = 1.0  # Reset recency (just seen)

            # Add related documents (deduplicate)
            if doc_ids:
                for doc_id in doc_ids:
                    if doc_id not in interest.related_documents:
                        interest.related_documents.append(doc_id)

            # Update co-occurring topics
            if related_topics:
                for related in related_topics:
                    related_lower = related.lower()
                    if related_lower != topic_name:  # Don't self-reference
                        interest.co_occurring_topics[related_lower] = (
                            interest.co_occurring_topics.get(related_lower, 0) + 1
                        )
        else:
            # Create new topic interest
            interest = TopicInterest(
                topic=topic_name,
                frequency=1,
                recency=1.0,
                confidence=topic.confidence,
                first_seen=datetime.now(),
                last_seen=datetime.now(),
                related_documents=doc_ids or [],
                co_occurring_topics={t.lower(): 1 for t in (related_topics or []) if t.lower() != topic_name},
            )
            self.topics[topic_name] = interest

        self.updated_at = datetime.now()

        logger.debug(
            f"Updated topic '{topic_name}' for persona '{self.persona}': "
            f"frequency={interest.frequency}, confidence={interest.confidence:.2f}"
        )

    def get_top_topics(self, limit: int = 10, min_confidence: float = 0.3) -> List[TopicInterest]:
        """Get top topics by confidence.

        Args:
            limit: Maximum number of topics to return
            min_confidence: Minimum confidence threshold

        Returns:
            List of TopicInterest sorted by confidence (highest first)

        Example:
            >>> profile = InterestProfile(persona="user")
            >>> # ... add some topics ...
            >>> top = profile.get_top_topics(limit=5)
            >>> len(top) <= 5
            True
        """
        filtered = [t for t in self.topics.values() if t.confidence >= min_confidence]
        sorted_topics = sorted(filtered, key=lambda t: t.confidence, reverse=True)
        return sorted_topics[:limit]

    def get_topic(self, topic_name: str) -> Optional[TopicInterest]:
        """Get topic interest by name.

        Args:
            topic_name: Topic name (case-insensitive)

        Returns:
            TopicInterest if found, None otherwise
        """
        return self.topics.get(topic_name.lower())

    def remove_topic(self, topic_name: str) -> bool:
        """Remove topic from profile (GDPR right to erasure).

        Args:
            topic_name: Topic name to remove (case-insensitive)

        Returns:
            True if topic was removed, False if not found
        """
        topic_name_lower = topic_name.lower()
        if topic_name_lower in self.topics:
            del self.topics[topic_name_lower]
            self.updated_at = datetime.now()
            logger.info(f"Removed topic '{topic_name}' from persona '{self.persona}'")
            return True
        return False

    def apply_time_decay(self, decay_rate: float = 0.1, decay_days: int = 30) -> None:
        """Apply time decay to all topics.

        Recent topics maintain high recency, older topics decay exponentially.

        Args:
            decay_rate: Decay rate (0.0-1.0, default: 0.1 = 10% decay per period)
            decay_days: Days per decay period (default: 30)

        Example:
            >>> profile = InterestProfile(persona="user")
            >>> # ... add topics ...
            >>> profile.apply_time_decay()  # Decay old topics
        """
        now = datetime.now()

        for interest in self.topics.values():
            days_since = (now - interest.last_seen).days
            periods_passed = days_since / decay_days

            # Exponential decay: recency = e^(-decay_rate * periods)
            import math
            interest.recency = math.exp(-decay_rate * periods_passed)

        self.updated_at = now
        logger.debug(f"Applied time decay to {len(self.topics)} topics (persona: {self.persona})")

    def to_dict(self) -> dict:
        """Convert profile to dictionary for JSON export.

        Returns:
            Dictionary representation
        """
        return {
            "persona": self.persona,
            "topics": {name: interest.to_dict() for name, interest in self.topics.items()},
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "InterestProfile":
        """Create profile from dictionary (JSON import).

        Args:
            data: Dictionary representation

        Returns:
            InterestProfile instance
        """
        return cls(
            persona=data["persona"],
            topics={
                name: TopicInterest.from_dict(interest_data)
                for name, interest_data in data.get("topics", {}).items()
            },
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
        )

    def export_to_json(self) -> str:
        """Export profile to JSON string (GDPR data portability).

        Returns:
            JSON string representation
        """
        return json.dumps(self.to_dict(), indent=2)

    @classmethod
    def import_from_json(cls, json_str: str) -> "InterestProfile":
        """Import profile from JSON string.

        Args:
            json_str: JSON string representation

        Returns:
            InterestProfile instance
        """
        data = json.loads(json_str)
        return cls.from_dict(data)


class ProfileManager:
    """Manage interest profiles for all personas.

    Stores profiles in SQLite database with persona isolation.
    """

    def __init__(self, storage_path: Path):
        """Initialize profile manager.

        Args:
            storage_path: Path to SQLite database file
        """
        self.storage_path = storage_path
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)

        self._init_database()

        logger.debug(f"ProfileManager initialized: {storage_path}")

    def _init_database(self) -> None:
        """Initialize SQLite database with schema."""
        with sqlite3.connect(self.storage_path) as conn:
            conn.execute(
                """CREATE TABLE IF NOT EXISTS profiles (
                    persona TEXT PRIMARY KEY,
                    profile_data TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )"""
            )

            # Index for faster lookups
            conn.execute(
                """CREATE INDEX IF NOT EXISTS idx_persona
                   ON profiles(persona)"""
            )

            conn.commit()

    def get_profile(self, persona: str) -> InterestProfile:
        """Get or create interest profile for persona.

        Args:
            persona: Persona name

        Returns:
            InterestProfile instance
        """
        with sqlite3.connect(self.storage_path) as conn:
            cursor = conn.execute(
                "SELECT profile_data FROM profiles WHERE persona = ?",
                (persona,),
            )
            row = cursor.fetchone()

            if row:
                # Load existing profile
                profile_json = row[0]
                profile = InterestProfile.import_from_json(profile_json)
                logger.debug(f"Loaded profile for persona '{persona}' ({len(profile.topics)} topics)")
                return profile
            else:
                # Create new profile
                profile = InterestProfile(persona=persona)
                logger.debug(f"Created new profile for persona '{persona}'")
                return profile

    def save_profile(self, profile: InterestProfile) -> None:
        """Save interest profile to database.

        Args:
            profile: InterestProfile to save
        """
        profile_json = profile.export_to_json()

        with sqlite3.connect(self.storage_path) as conn:
            conn.execute(
                """INSERT OR REPLACE INTO profiles (persona, profile_data, created_at, updated_at)
                   VALUES (?, ?, ?, ?)""",
                (
                    profile.persona,
                    profile_json,
                    profile.created_at.isoformat(),
                    profile.updated_at.isoformat(),
                ),
            )
            conn.commit()

        logger.debug(f"Saved profile for persona '{profile.persona}' ({len(profile.topics)} topics)")

    def delete_profile(self, persona: str) -> bool:
        """Delete profile for persona (GDPR right to erasure).

        Args:
            persona: Persona name

        Returns:
            True if profile was deleted, False if not found
        """
        with sqlite3.connect(self.storage_path) as conn:
            cursor = conn.execute(
                "DELETE FROM profiles WHERE persona = ?",
                (persona,),
            )
            conn.commit()

            deleted = cursor.rowcount > 0

        if deleted:
            logger.info(f"Deleted profile for persona '{persona}'")
        else:
            logger.warning(f"No profile found for persona '{persona}' to delete")

        return deleted

    def list_personas(self) -> List[str]:
        """List all personas with profiles.

        Returns:
            List of persona names
        """
        with sqlite3.connect(self.storage_path) as conn:
            cursor = conn.execute("SELECT persona FROM profiles ORDER BY persona")
            personas = [row[0] for row in cursor.fetchall()]

        return personas

    def export_all_profiles(self, export_path: Path) -> None:
        """Export all profiles to JSON file (GDPR data portability).

        Args:
            export_path: Path to export JSON file
        """
        personas = self.list_personas()
        all_profiles = {}

        for persona in personas:
            profile = self.get_profile(persona)
            all_profiles[persona] = profile.to_dict()

        export_path.parent.mkdir(parents=True, exist_ok=True)
        with open(export_path, "w") as f:
            json.dump(all_profiles, f, indent=2)

        logger.info(f"Exported {len(all_profiles)} profiles to {export_path}")
