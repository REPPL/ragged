"""Unit tests for agent memory module."""

import pytest
from datetime import datetime
from pathlib import Path
import tempfile
import shutil

from ragged.agents.memory import (
    MemoryEntry,
    ConversationTurn,
    InMemoryStore,
    FileStore,
    AgentMemory,
)


class TestMemoryEntry:
    """Tests for MemoryEntry dataclass."""

    def test_create_memory_entry(self):
        """Test creating a memory entry."""
        entry = MemoryEntry(
            id="test-1",
            content="Test content",
            entry_type="fact",
        )
        assert entry.id == "test-1"
        assert entry.content == "Test content"
        assert entry.entry_type == "fact"
        assert entry.importance == 0.5  # default

    def test_entry_with_metadata(self):
        """Test entry with metadata."""
        entry = MemoryEntry(
            id="test-2",
            content="Test",
            entry_type="summary",
            metadata={"source": "conversation"},
            importance=0.8,
        )
        assert entry.metadata == {"source": "conversation"}
        assert entry.importance == 0.8

    def test_to_dict(self):
        """Test serialisation to dictionary."""
        entry = MemoryEntry(
            id="test-3",
            content="Test",
            entry_type="fact",
            importance=0.7,
        )
        d = entry.to_dict()
        assert d["id"] == "test-3"
        assert d["content"] == "Test"
        assert d["entry_type"] == "fact"
        assert d["importance"] == 0.7
        assert "timestamp" in d

    def test_from_dict(self):
        """Test deserialisation from dictionary."""
        data = {
            "id": "test-4",
            "content": "Test content",
            "entry_type": "preference",
            "timestamp": "2024-01-01T12:00:00",
            "metadata": {"key": "value"},
            "importance": 0.9,
        }
        entry = MemoryEntry.from_dict(data)
        assert entry.id == "test-4"
        assert entry.content == "Test content"
        assert entry.entry_type == "preference"
        assert entry.importance == 0.9


class TestConversationTurn:
    """Tests for ConversationTurn dataclass."""

    def test_create_turn(self):
        """Test creating a conversation turn."""
        turn = ConversationTurn(role="user", content="Hello")
        assert turn.role == "user"
        assert turn.content == "Hello"
        assert turn.tool_calls == []
        assert turn.tool_results == []

    def test_turn_with_tools(self):
        """Test turn with tool calls."""
        turn = ConversationTurn(
            role="assistant",
            content="Let me search for that.",
            tool_calls=[{"name": "search", "args": {"query": "test"}}],
            tool_results=[{"output": "Found 5 results"}],
        )
        assert len(turn.tool_calls) == 1
        assert len(turn.tool_results) == 1

    def test_to_dict(self):
        """Test serialisation to dictionary."""
        turn = ConversationTurn(role="system", content="You are helpful.")
        d = turn.to_dict()
        assert d["role"] == "system"
        assert d["content"] == "You are helpful."
        assert "timestamp" in d

    def test_from_dict(self):
        """Test deserialisation from dictionary."""
        data = {
            "role": "user",
            "content": "Test message",
            "timestamp": "2024-01-01T12:00:00",
            "tool_calls": [],
            "tool_results": [],
        }
        turn = ConversationTurn.from_dict(data)
        assert turn.role == "user"
        assert turn.content == "Test message"


class TestInMemoryStore:
    """Tests for InMemoryStore."""

    @pytest.fixture
    def store(self):
        """Create an in-memory store."""
        return InMemoryStore()

    @pytest.mark.asyncio
    async def test_save_and_load(self, store):
        """Test saving and loading entries."""
        entry = MemoryEntry(id="test", content="Test", entry_type="fact")
        await store.save("test", entry)
        loaded = await store.load("test")
        assert loaded is not None
        assert loaded.id == "test"

    @pytest.mark.asyncio
    async def test_load_nonexistent(self, store):
        """Test loading nonexistent key."""
        result = await store.load("nonexistent")
        assert result is None

    @pytest.mark.asyncio
    async def test_search(self, store):
        """Test searching entries."""
        await store.save("1", MemoryEntry(id="1", content="Python programming", entry_type="fact"))
        await store.save("2", MemoryEntry(id="2", content="JavaScript basics", entry_type="fact"))
        await store.save("3", MemoryEntry(id="3", content="Python web development", entry_type="fact"))

        results = await store.search("Python")
        assert len(results) == 2

    @pytest.mark.asyncio
    async def test_search_with_type_filter(self, store):
        """Test searching with type filter."""
        await store.save("1", MemoryEntry(id="1", content="Test fact", entry_type="fact"))
        await store.save("2", MemoryEntry(id="2", content="Test summary", entry_type="summary"))

        results = await store.search("Test", entry_type="fact")
        assert len(results) == 1
        assert results[0].entry_type == "fact"

    @pytest.mark.asyncio
    async def test_delete(self, store):
        """Test deleting entries."""
        entry = MemoryEntry(id="test", content="Test", entry_type="fact")
        await store.save("test", entry)
        assert await store.delete("test") is True
        assert await store.load("test") is None

    @pytest.mark.asyncio
    async def test_delete_nonexistent(self, store):
        """Test deleting nonexistent entry."""
        result = await store.delete("nonexistent")
        assert result is False

    @pytest.mark.asyncio
    async def test_clear(self, store):
        """Test clearing all entries."""
        await store.save("1", MemoryEntry(id="1", content="A", entry_type="fact"))
        await store.save("2", MemoryEntry(id="2", content="B", entry_type="fact"))
        await store.clear()
        assert len(store) == 0


class TestFileStore:
    """Tests for FileStore."""

    @pytest.fixture
    def store(self):
        """Create a file store with temp directory."""
        temp_dir = Path(tempfile.mkdtemp())
        store = FileStore(temp_dir)
        yield store
        shutil.rmtree(temp_dir)

    @pytest.mark.asyncio
    async def test_save_and_load(self, store):
        """Test saving and loading entries."""
        entry = MemoryEntry(id="file-test", content="File test", entry_type="fact")
        await store.save("file-test", entry)
        loaded = await store.load("file-test")
        assert loaded is not None
        assert loaded.id == "file-test"

    @pytest.mark.asyncio
    async def test_persistence(self, store):
        """Test that entries persist."""
        entry = MemoryEntry(id="persist", content="Persistent", entry_type="fact")
        await store.save("persist", entry)

        # Create new store instance with same path
        new_store = FileStore(store.base_path)
        loaded = await new_store.load("persist")
        assert loaded is not None
        assert loaded.content == "Persistent"

    @pytest.mark.asyncio
    async def test_delete(self, store):
        """Test deleting entries from file store."""
        entry = MemoryEntry(id="delete-me", content="Delete", entry_type="fact")
        await store.save("delete-me", entry)
        assert await store.delete("delete-me") is True
        assert await store.load("delete-me") is None


class TestAgentMemory:
    """Tests for AgentMemory."""

    @pytest.fixture
    def memory(self):
        """Create an agent memory instance."""
        return AgentMemory()

    def test_start_conversation(self, memory):
        """Test starting a conversation."""
        conv_id = memory.start_conversation()
        assert conv_id is not None
        assert memory.conversation_id == conv_id

    def test_start_conversation_with_id(self, memory):
        """Test starting conversation with custom ID."""
        conv_id = memory.start_conversation("custom-id")
        assert conv_id == "custom-id"

    def test_add_turn(self, memory):
        """Test adding turns to conversation."""
        memory.start_conversation()
        turn = memory.add_turn("user", "Hello")
        assert turn.role == "user"
        assert turn.content == "Hello"
        assert len(memory.conversation) == 1

    def test_add_turn_with_tools(self, memory):
        """Test adding turn with tool calls."""
        memory.start_conversation()
        turn = memory.add_turn(
            role="assistant",
            content="Searching...",
            tool_calls=[{"name": "search"}],
            tool_results=[{"result": "found"}],
        )
        assert len(turn.tool_calls) == 1
        assert len(turn.tool_results) == 1

    def test_get_context_window(self, memory):
        """Test getting context window."""
        memory.start_conversation()
        memory.add_turn("user", "Message 1")
        memory.add_turn("assistant", "Response 1")
        memory.add_turn("user", "Message 2")

        context = memory.get_context_window(max_turns=2)
        assert len(context) == 2
        assert context[0]["content"] == "Response 1"
        assert context[1]["content"] == "Message 2"

    def test_get_context_window_exclude_system(self, memory):
        """Test excluding system messages from context."""
        memory.start_conversation()
        memory.add_turn("system", "System prompt")
        memory.add_turn("user", "User message")

        context = memory.get_context_window(include_system=False)
        assert len(context) == 1
        assert context[0]["role"] == "user"

    @pytest.mark.asyncio
    async def test_remember(self, memory):
        """Test remembering content."""
        entry = await memory.remember(
            content="User prefers dark mode",
            entry_type="preference",
            importance=0.8,
        )
        assert entry.content == "User prefers dark mode"
        assert entry.entry_type == "preference"
        assert entry.importance == 0.8

    @pytest.mark.asyncio
    async def test_recall(self, memory):
        """Test recalling memories."""
        await memory.remember("Python is great", entry_type="fact")
        await memory.remember("JavaScript is popular", entry_type="fact")

        results = await memory.recall("Python")
        assert len(results) >= 1
        assert any("Python" in r.content for r in results)

    @pytest.mark.asyncio
    async def test_forget(self, memory):
        """Test forgetting memories."""
        entry = await memory.remember("Temporary fact", entry_type="fact")
        result = await memory.forget(entry.id)
        assert result is True

    @pytest.mark.asyncio
    async def test_summarize_conversation(self, memory):
        """Test conversation summarisation."""
        memory.start_conversation()
        memory.add_turn("user", "Hello, how are you?")
        memory.add_turn("assistant", "I'm doing well, thank you!")
        memory.add_turn("user", "Can you help me with Python?")

        summary = await memory.summarize_conversation()
        assert "user" in summary.lower()
        assert "assistant" in summary.lower()

    @pytest.mark.asyncio
    async def test_summarize_empty_conversation(self, memory):
        """Test summarising empty conversation."""
        summary = await memory.summarize_conversation()
        assert "no conversation" in summary.lower()

    def test_to_dict(self, memory):
        """Test serialisation."""
        memory.start_conversation("test-conv")
        memory.add_turn("user", "Test message")

        d = memory.to_dict()
        assert d["conversation_id"] == "test-conv"
        assert len(d["conversation"]) == 1

    def test_from_dict(self, memory):
        """Test deserialisation."""
        data = {
            "conversation_id": "restored",
            "conversation": [
                {
                    "role": "user",
                    "content": "Restored message",
                    "timestamp": "2024-01-01T12:00:00",
                    "tool_calls": [],
                    "tool_results": [],
                }
            ],
        }
        restored = AgentMemory.from_dict(data)
        assert restored.conversation_id == "restored"
        assert len(restored.conversation) == 1
