"""Agent memory and context persistence.

Provides short-term and long-term memory for agent conversations,
enabling context awareness across interactions.

Memory Types:
- Working Memory: Current conversation context (ephemeral)
- Episodic Memory: Past conversation summaries (persistent)
- Semantic Memory: Learned facts and preferences (persistent)
"""

import json
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class MemoryEntry:
    """A single memory entry.

    Attributes:
        id: Unique entry identifier
        content: The memory content
        entry_type: Type of memory (message, fact, summary)
        timestamp: When the memory was created
        metadata: Additional context
        importance: Importance score (0.0-1.0)
    """

    id: str
    content: str
    entry_type: str
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: dict[str, Any] = field(default_factory=dict)
    importance: float = 0.5

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialisation."""
        return {
            "id": self.id,
            "content": self.content,
            "entry_type": self.entry_type,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata,
            "importance": self.importance,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "MemoryEntry":
        """Create from dictionary."""
        return cls(
            id=data["id"],
            content=data["content"],
            entry_type=data["entry_type"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            metadata=data.get("metadata", {}),
            importance=data.get("importance", 0.5),
        )


@dataclass
class ConversationTurn:
    """A single turn in a conversation.

    Attributes:
        role: Speaker role (user, assistant, system)
        content: Message content
        timestamp: When the message was sent
        tool_calls: Any tool calls made in this turn
        tool_results: Results from tool calls
    """

    role: str
    content: str
    timestamp: datetime = field(default_factory=datetime.now)
    tool_calls: list[dict[str, Any]] = field(default_factory=list)
    tool_results: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialisation."""
        return {
            "role": self.role,
            "content": self.content,
            "timestamp": self.timestamp.isoformat(),
            "tool_calls": self.tool_calls,
            "tool_results": self.tool_results,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ConversationTurn":
        """Create from dictionary."""
        return cls(
            role=data["role"],
            content=data["content"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            tool_calls=data.get("tool_calls", []),
            tool_results=data.get("tool_results", []),
        )


class MemoryStore(ABC):
    """Abstract base class for memory storage backends."""

    @abstractmethod
    async def save(self, key: str, entry: MemoryEntry) -> None:
        """Save a memory entry."""
        pass

    @abstractmethod
    async def load(self, key: str) -> MemoryEntry | None:
        """Load a memory entry by key."""
        pass

    @abstractmethod
    async def search(
        self,
        query: str,
        limit: int = 10,
        entry_type: str | None = None,
    ) -> list[MemoryEntry]:
        """Search memories by content similarity."""
        pass

    @abstractmethod
    async def delete(self, key: str) -> bool:
        """Delete a memory entry."""
        pass

    @abstractmethod
    async def clear(self) -> None:
        """Clear all memories."""
        pass


class InMemoryStore(MemoryStore):
    """In-memory storage for working memory."""

    def __init__(self) -> None:
        self._store: dict[str, MemoryEntry] = {}

    async def save(self, key: str, entry: MemoryEntry) -> None:
        """Save a memory entry."""
        self._store[key] = entry

    async def load(self, key: str) -> MemoryEntry | None:
        """Load a memory entry by key."""
        return self._store.get(key)

    async def search(
        self,
        query: str,
        limit: int = 10,
        entry_type: str | None = None,
    ) -> list[MemoryEntry]:
        """Search memories by content (simple substring match)."""
        results = []
        query_lower = query.lower()

        for entry in self._store.values():
            if entry_type and entry.entry_type != entry_type:
                continue
            if query_lower in entry.content.lower():
                results.append(entry)

        # Sort by importance and timestamp
        results.sort(
            key=lambda e: (e.importance, e.timestamp),
            reverse=True,
        )
        return results[:limit]

    async def delete(self, key: str) -> bool:
        """Delete a memory entry."""
        if key in self._store:
            del self._store[key]
            return True
        return False

    async def clear(self) -> None:
        """Clear all memories."""
        self._store.clear()

    def __len__(self) -> int:
        return len(self._store)


class FileStore(MemoryStore):
    """File-based storage for persistent memory."""

    def __init__(self, base_path: Path) -> None:
        self.base_path = base_path
        self.base_path.mkdir(parents=True, exist_ok=True)
        self._index: dict[str, MemoryEntry] = {}
        self._load_index()

    def _load_index(self) -> None:
        """Load the memory index from disk."""
        index_path = self.base_path / "index.json"
        if index_path.exists():
            try:
                with open(index_path) as f:
                    data = json.load(f)
                    self._index = {
                        k: MemoryEntry.from_dict(v)
                        for k, v in data.items()
                    }
            except (json.JSONDecodeError, KeyError) as e:
                logger.warning(f"Failed to load memory index: {e}")
                self._index = {}

    def _save_index(self) -> None:
        """Save the memory index to disk."""
        index_path = self.base_path / "index.json"
        with open(index_path, "w") as f:
            json.dump(
                {k: v.to_dict() for k, v in self._index.items()},
                f,
                indent=2,
            )

    async def save(self, key: str, entry: MemoryEntry) -> None:
        """Save a memory entry."""
        self._index[key] = entry
        self._save_index()

        # Also save full content to separate file
        entry_path = self.base_path / f"{key}.json"
        with open(entry_path, "w") as f:
            json.dump(entry.to_dict(), f, indent=2)

    async def load(self, key: str) -> MemoryEntry | None:
        """Load a memory entry by key."""
        return self._index.get(key)

    async def search(
        self,
        query: str,
        limit: int = 10,
        entry_type: str | None = None,
    ) -> list[MemoryEntry]:
        """Search memories by content (simple substring match)."""
        results = []
        query_lower = query.lower()

        for entry in self._index.values():
            if entry_type and entry.entry_type != entry_type:
                continue
            if query_lower in entry.content.lower():
                results.append(entry)

        results.sort(
            key=lambda e: (e.importance, e.timestamp),
            reverse=True,
        )
        return results[:limit]

    async def delete(self, key: str) -> bool:
        """Delete a memory entry."""
        if key in self._index:
            del self._index[key]
            self._save_index()

            entry_path = self.base_path / f"{key}.json"
            if entry_path.exists():
                entry_path.unlink()
            return True
        return False

    async def clear(self) -> None:
        """Clear all memories."""
        self._index.clear()
        self._save_index()

        # Remove all entry files
        for entry_file in self.base_path.glob("*.json"):
            if entry_file.name != "index.json":
                entry_file.unlink()


class AgentMemory:
    """Agent memory manager combining working and long-term memory.

    Provides unified access to:
    - Working memory: Current conversation context
    - Episodic memory: Past conversation summaries
    - Semantic memory: Learned facts and user preferences
    """

    def __init__(
        self,
        working_store: MemoryStore | None = None,
        long_term_store: MemoryStore | None = None,
        max_working_memory: int = 100,
    ) -> None:
        """Initialise agent memory.

        Args:
            working_store: Store for working memory (default: in-memory)
            long_term_store: Store for long-term memory (default: None)
            max_working_memory: Maximum working memory entries
        """
        self.working = working_store or InMemoryStore()
        self.long_term = long_term_store
        self.max_working_memory = max_working_memory

        # Current conversation
        self._conversation: list[ConversationTurn] = []
        self._conversation_id: str = ""

    @property
    def conversation(self) -> list[ConversationTurn]:
        """Get current conversation history."""
        return self._conversation

    @property
    def conversation_id(self) -> str:
        """Get current conversation ID."""
        return self._conversation_id

    def start_conversation(self, conversation_id: str | None = None) -> str:
        """Start a new conversation.

        Args:
            conversation_id: Optional ID for the conversation

        Returns:
            The conversation ID
        """
        import uuid

        self._conversation = []
        self._conversation_id = conversation_id or str(uuid.uuid4())[:12]
        return self._conversation_id

    def add_turn(
        self,
        role: str,
        content: str,
        tool_calls: list[dict[str, Any]] | None = None,
        tool_results: list[dict[str, Any]] | None = None,
    ) -> ConversationTurn:
        """Add a turn to the current conversation.

        Args:
            role: Speaker role (user, assistant, system)
            content: Message content
            tool_calls: Any tool calls made
            tool_results: Results from tool calls

        Returns:
            The created conversation turn
        """
        turn = ConversationTurn(
            role=role,
            content=content,
            tool_calls=tool_calls or [],
            tool_results=tool_results or [],
        )
        self._conversation.append(turn)
        return turn

    def get_context_window(
        self,
        max_turns: int = 10,
        include_system: bool = True,
    ) -> list[dict[str, Any]]:
        """Get recent conversation context for LLM.

        Args:
            max_turns: Maximum number of turns to include
            include_system: Whether to include system messages

        Returns:
            List of message dictionaries for LLM
        """
        messages = []
        turns = self._conversation[-max_turns:]

        for turn in turns:
            if not include_system and turn.role == "system":
                continue

            message = {"role": turn.role, "content": turn.content}

            if turn.tool_calls:
                message["tool_calls"] = turn.tool_calls
            if turn.tool_results:
                message["tool_results"] = turn.tool_results

            messages.append(message)

        return messages

    async def remember(
        self,
        content: str,
        entry_type: str = "fact",
        importance: float = 0.5,
        metadata: dict[str, Any] | None = None,
    ) -> MemoryEntry:
        """Store something in memory.

        Args:
            content: The content to remember
            entry_type: Type of memory (fact, summary, preference)
            importance: Importance score (0.0-1.0)
            metadata: Additional context

        Returns:
            The created memory entry
        """
        import uuid

        entry = MemoryEntry(
            id=str(uuid.uuid4())[:12],
            content=content,
            entry_type=entry_type,
            importance=importance,
            metadata=metadata or {},
        )

        await self.working.save(entry.id, entry)

        # Also store in long-term if available
        if self.long_term:
            await self.long_term.save(entry.id, entry)

        return entry

    async def recall(
        self,
        query: str,
        limit: int = 5,
        entry_type: str | None = None,
    ) -> list[MemoryEntry]:
        """Recall memories related to a query.

        Args:
            query: Search query
            limit: Maximum results
            entry_type: Filter by type

        Returns:
            List of relevant memory entries
        """
        # Search working memory first
        results = await self.working.search(query, limit, entry_type)

        # Also search long-term if available
        if self.long_term and len(results) < limit:
            long_term_results = await self.long_term.search(
                query, limit - len(results), entry_type
            )
            # Deduplicate by ID
            seen_ids = {r.id for r in results}
            for entry in long_term_results:
                if entry.id not in seen_ids:
                    results.append(entry)

        return results[:limit]

    async def forget(self, memory_id: str) -> bool:
        """Remove a memory.

        Args:
            memory_id: ID of memory to forget

        Returns:
            True if memory was found and removed
        """
        deleted = await self.working.delete(memory_id)
        if self.long_term:
            deleted = await self.long_term.delete(memory_id) or deleted
        return deleted

    async def summarize_conversation(self) -> str:
        """Create a summary of the current conversation.

        Returns:
            Summary text
        """
        if not self._conversation:
            return "No conversation to summarise."

        # Simple summary: count turns and extract key topics
        user_turns = [t for t in self._conversation if t.role == "user"]
        assistant_turns = [t for t in self._conversation if t.role == "assistant"]

        summary_parts = [
            f"Conversation with {len(user_turns)} user messages "
            f"and {len(assistant_turns)} assistant responses.",
        ]

        # Extract first and last user messages
        if user_turns:
            summary_parts.append(f"Started with: {user_turns[0].content[:100]}...")
            if len(user_turns) > 1:
                summary_parts.append(f"Ended with: {user_turns[-1].content[:100]}...")

        return " ".join(summary_parts)

    async def save_conversation(self) -> None:
        """Save current conversation to long-term memory."""
        if not self.long_term or not self._conversation:
            return

        summary = await self.summarize_conversation()
        entry = MemoryEntry(
            id=f"conv_{self._conversation_id}",
            content=summary,
            entry_type="conversation",
            metadata={
                "conversation_id": self._conversation_id,
                "turn_count": len(self._conversation),
                "turns": [t.to_dict() for t in self._conversation],
            },
            importance=0.7,
        )
        await self.long_term.save(entry.id, entry)

    def clear_working_memory(self) -> None:
        """Clear working memory but preserve long-term."""
        import asyncio

        asyncio.get_event_loop().run_until_complete(self.working.clear())
        self._conversation = []

    def to_dict(self) -> dict[str, Any]:
        """Serialise memory state."""
        return {
            "conversation_id": self._conversation_id,
            "conversation": [t.to_dict() for t in self._conversation],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "AgentMemory":
        """Restore memory from serialised state."""
        memory = cls()
        memory._conversation_id = data.get("conversation_id", "")
        memory._conversation = [
            ConversationTurn.from_dict(t)
            for t in data.get("conversation", [])
        ]
        return memory
