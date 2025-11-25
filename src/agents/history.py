"""Agent conversation history management.

Provides persistent storage and retrieval of conversation histories,
enabling continuity across sessions.
"""

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class ConversationMetadata:
    """Metadata for a saved conversation.

    Attributes:
        id: Unique conversation identifier
        title: Human-readable title
        created_at: When conversation started
        updated_at: Last activity time
        message_count: Number of messages
        summary: Brief summary
        tags: Conversation tags
    """

    id: str
    title: str
    created_at: datetime
    updated_at: datetime
    message_count: int
    summary: str = ""
    tags: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "title": self.title,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "message_count": self.message_count,
            "summary": self.summary,
            "tags": self.tags,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ConversationMetadata":
        """Create from dictionary."""
        return cls(
            id=data["id"],
            title=data["title"],
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
            message_count=data["message_count"],
            summary=data.get("summary", ""),
            tags=data.get("tags", []),
        )


@dataclass
class HistoryMessage:
    """A message in conversation history.

    Attributes:
        role: Message role (user, assistant, system, tool)
        content: Message content
        timestamp: When message was sent
        metadata: Additional message metadata
    """

    role: str
    content: str
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "role": self.role,
            "content": self.content,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "HistoryMessage":
        """Create from dictionary."""
        return cls(
            role=data["role"],
            content=data["content"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            metadata=data.get("metadata", {}),
        )


@dataclass
class Conversation:
    """A complete conversation with messages.

    Attributes:
        metadata: Conversation metadata
        messages: List of messages
    """

    metadata: ConversationMetadata
    messages: list[HistoryMessage] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "metadata": self.metadata.to_dict(),
            "messages": [m.to_dict() for m in self.messages],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Conversation":
        """Create from dictionary."""
        return cls(
            metadata=ConversationMetadata.from_dict(data["metadata"]),
            messages=[HistoryMessage.from_dict(m) for m in data.get("messages", [])],
        )


class ConversationHistory:
    """Manages conversation history storage and retrieval.

    Provides file-based persistence for conversation histories,
    with indexing for fast lookup and search.
    """

    def __init__(self, storage_path: Path | None = None) -> None:
        """Initialise conversation history.

        Args:
            storage_path: Path to store conversations (default: ~/.ragged/conversations)
        """
        if storage_path is None:
            storage_path = Path.home() / ".ragged" / "conversations"

        self.storage_path = storage_path
        self.storage_path.mkdir(parents=True, exist_ok=True)

        self._index: dict[str, ConversationMetadata] = {}
        self._load_index()

    def _load_index(self) -> None:
        """Load the conversation index from disk."""
        index_path = self.storage_path / "index.json"
        if index_path.exists():
            try:
                with open(index_path) as f:
                    data = json.load(f)
                    self._index = {
                        k: ConversationMetadata.from_dict(v)
                        for k, v in data.items()
                    }
            except (json.JSONDecodeError, KeyError) as e:
                logger.warning(f"Failed to load conversation index: {e}")
                self._index = {}

    def _save_index(self) -> None:
        """Save the conversation index to disk."""
        index_path = self.storage_path / "index.json"
        with open(index_path, "w") as f:
            json.dump(
                {k: v.to_dict() for k, v in self._index.items()},
                f,
                indent=2,
            )

    def _generate_title(self, messages: list[HistoryMessage]) -> str:
        """Generate a title from the first user message."""
        for msg in messages:
            if msg.role == "user":
                # Take first 50 chars of first user message
                content = msg.content.strip()
                if len(content) > 50:
                    return content[:47] + "..."
                return content
        return "Untitled Conversation"

    def create(
        self,
        conversation_id: str,
        title: str | None = None,
        tags: list[str] | None = None,
    ) -> Conversation:
        """Create a new conversation.

        Args:
            conversation_id: Unique conversation ID
            title: Optional title (auto-generated from first message if not provided)
            tags: Optional tags

        Returns:
            The created conversation
        """
        now = datetime.now()
        metadata = ConversationMetadata(
            id=conversation_id,
            title=title or "New Conversation",
            created_at=now,
            updated_at=now,
            message_count=0,
            tags=tags or [],
        )

        conversation = Conversation(metadata=metadata, messages=[])

        # Save to index
        self._index[conversation_id] = metadata
        self._save_index()

        # Save conversation file
        self._save_conversation(conversation)

        return conversation

    def _save_conversation(self, conversation: Conversation) -> None:
        """Save a conversation to disk."""
        conv_path = self.storage_path / f"{conversation.metadata.id}.json"
        with open(conv_path, "w") as f:
            json.dump(conversation.to_dict(), f, indent=2)

    def get(self, conversation_id: str) -> Conversation | None:
        """Get a conversation by ID.

        Args:
            conversation_id: Conversation ID

        Returns:
            The conversation or None if not found
        """
        if conversation_id not in self._index:
            return None

        conv_path = self.storage_path / f"{conversation_id}.json"
        if not conv_path.exists():
            return None

        try:
            with open(conv_path) as f:
                data = json.load(f)
                return Conversation.from_dict(data)
        except (json.JSONDecodeError, KeyError) as e:
            logger.error(f"Failed to load conversation {conversation_id}: {e}")
            return None

    def add_message(
        self,
        conversation_id: str,
        role: str,
        content: str,
        metadata: dict[str, Any] | None = None,
    ) -> HistoryMessage | None:
        """Add a message to a conversation.

        Args:
            conversation_id: Conversation ID
            role: Message role
            content: Message content
            metadata: Optional message metadata

        Returns:
            The added message or None if conversation not found
        """
        conversation = self.get(conversation_id)
        if conversation is None:
            return None

        message = HistoryMessage(
            role=role,
            content=content,
            metadata=metadata or {},
        )
        conversation.messages.append(message)

        # Update metadata
        conversation.metadata.updated_at = datetime.now()
        conversation.metadata.message_count = len(conversation.messages)

        # Auto-generate title if first user message
        if (
            conversation.metadata.title == "New Conversation"
            and role == "user"
        ):
            conversation.metadata.title = self._generate_title(conversation.messages)

        # Save
        self._index[conversation_id] = conversation.metadata
        self._save_index()
        self._save_conversation(conversation)

        return message

    def list_conversations(
        self,
        limit: int = 20,
        offset: int = 0,
        tag: str | None = None,
    ) -> "list[ConversationMetadata]":
        """List conversations.

        Args:
            limit: Maximum results
            offset: Skip first N results
            tag: Filter by tag

        Returns:
            List of conversation metadata
        """
        conversations = [v for v in self._index.values()]

        # Filter by tag
        if tag:
            conversations = [c for c in conversations if tag in c.tags]

        # Sort by updated_at descending
        conversations.sort(key=lambda c: c.updated_at, reverse=True)

        return conversations[offset : offset + limit]

    def search(
        self,
        query: str,
        limit: int = 10,
    ) -> "list[ConversationMetadata]":
        """Search conversations by content.

        Args:
            query: Search query
            limit: Maximum results

        Returns:
            List of matching conversation metadata
        """
        query_lower = query.lower()
        results = []

        for conv_id in self._index:
            conversation = self.get(conv_id)
            if conversation is None:
                continue

            # Search in title and messages
            if query_lower in conversation.metadata.title.lower():
                results.append(conversation.metadata)
                continue

            for message in conversation.messages:
                if query_lower in message.content.lower():
                    results.append(conversation.metadata)
                    break

        # Sort by updated_at descending
        results.sort(key=lambda c: c.updated_at, reverse=True)
        return results[:limit]

    def delete(self, conversation_id: str) -> bool:
        """Delete a conversation.

        Args:
            conversation_id: Conversation ID

        Returns:
            True if deleted, False if not found
        """
        if conversation_id not in self._index:
            return False

        del self._index[conversation_id]
        self._save_index()

        conv_path = self.storage_path / f"{conversation_id}.json"
        if conv_path.exists():
            conv_path.unlink()

        return True

    def update_metadata(
        self,
        conversation_id: str,
        title: str | None = None,
        summary: str | None = None,
        tags: list[str] | None = None,
    ) -> bool:
        """Update conversation metadata.

        Args:
            conversation_id: Conversation ID
            title: New title
            summary: New summary
            tags: New tags

        Returns:
            True if updated, False if not found
        """
        if conversation_id not in self._index:
            return False

        conversation = self.get(conversation_id)
        if conversation is None:
            return False

        if title is not None:
            conversation.metadata.title = title
        if summary is not None:
            conversation.metadata.summary = summary
        if tags is not None:
            conversation.metadata.tags = tags

        conversation.metadata.updated_at = datetime.now()

        self._index[conversation_id] = conversation.metadata
        self._save_index()
        self._save_conversation(conversation)

        return True

    def export(self, conversation_id: str, format: str = "json") -> str | None:
        """Export a conversation.

        Args:
            conversation_id: Conversation ID
            format: Export format (json, markdown)

        Returns:
            Exported content or None if not found
        """
        conversation = self.get(conversation_id)
        if conversation is None:
            return None

        if format == "json":
            return json.dumps(conversation.to_dict(), indent=2)

        elif format == "markdown":
            lines = [
                f"# {conversation.metadata.title}",
                "",
                f"*Created: {conversation.metadata.created_at.strftime('%Y-%m-%d %H:%M')}*",
                "",
                "---",
                "",
            ]

            for msg in conversation.messages:
                role_label = msg.role.capitalize()
                lines.append(f"**{role_label}:** {msg.content}")
                lines.append("")

            return "\n".join(lines)

        return None

    def count(self) -> int:
        """Get total conversation count."""
        return len(self._index)


# Global instance
_history: ConversationHistory | None = None


def get_conversation_history() -> ConversationHistory:
    """Get the global conversation history instance."""
    global _history
    if _history is None:
        _history = ConversationHistory()
    return _history
