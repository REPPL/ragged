"""Unit tests for agent history module."""

import pytest
from datetime import datetime
from pathlib import Path
import tempfile
import shutil

from ragged.agents.history import (
    ConversationMetadata,
    HistoryMessage,
    Conversation,
    ConversationHistory,
)


class TestConversationMetadata:
    """Tests for ConversationMetadata dataclass."""

    def test_create_metadata(self):
        """Test creating conversation metadata."""
        now = datetime.now()
        metadata = ConversationMetadata(
            id="conv-1",
            title="Test Conversation",
            created_at=now,
            updated_at=now,
            message_count=5,
        )
        assert metadata.id == "conv-1"
        assert metadata.title == "Test Conversation"
        assert metadata.message_count == 5

    def test_metadata_defaults(self):
        """Test default values."""
        now = datetime.now()
        metadata = ConversationMetadata(
            id="conv-2",
            title="Test",
            created_at=now,
            updated_at=now,
            message_count=0,
        )
        assert metadata.summary == ""
        assert metadata.tags == []

    def test_to_dict(self):
        """Test serialisation to dictionary."""
        now = datetime.now()
        metadata = ConversationMetadata(
            id="conv-3",
            title="Test",
            created_at=now,
            updated_at=now,
            message_count=3,
            summary="A test conversation",
            tags=["test", "unit"],
        )
        d = metadata.to_dict()
        assert d["id"] == "conv-3"
        assert d["title"] == "Test"
        assert d["summary"] == "A test conversation"
        assert d["tags"] == ["test", "unit"]

    def test_from_dict(self):
        """Test deserialisation from dictionary."""
        data = {
            "id": "conv-4",
            "title": "Restored",
            "created_at": "2024-01-01T12:00:00",
            "updated_at": "2024-01-01T13:00:00",
            "message_count": 10,
            "summary": "Restored summary",
            "tags": ["restored"],
        }
        metadata = ConversationMetadata.from_dict(data)
        assert metadata.id == "conv-4"
        assert metadata.title == "Restored"
        assert metadata.message_count == 10


class TestHistoryMessage:
    """Tests for HistoryMessage dataclass."""

    def test_create_message(self):
        """Test creating a history message."""
        message = HistoryMessage(
            role="user",
            content="Hello, world!",
        )
        assert message.role == "user"
        assert message.content == "Hello, world!"

    def test_message_with_metadata(self):
        """Test message with metadata."""
        message = HistoryMessage(
            role="assistant",
            content="Response",
            metadata={"tokens": 50, "model": "test"},
        )
        assert message.metadata["tokens"] == 50

    def test_to_dict(self):
        """Test serialisation to dictionary."""
        message = HistoryMessage(role="user", content="Test")
        d = message.to_dict()
        assert d["role"] == "user"
        assert d["content"] == "Test"
        assert "timestamp" in d

    def test_from_dict(self):
        """Test deserialisation from dictionary."""
        data = {
            "role": "assistant",
            "content": "Restored message",
            "timestamp": "2024-01-01T12:00:00",
            "metadata": {"key": "value"},
        }
        message = HistoryMessage.from_dict(data)
        assert message.role == "assistant"
        assert message.content == "Restored message"


class TestConversation:
    """Tests for Conversation dataclass."""

    @pytest.fixture
    def sample_conversation(self):
        """Create a sample conversation."""
        now = datetime.now()
        metadata = ConversationMetadata(
            id="conv-test",
            title="Test Conv",
            created_at=now,
            updated_at=now,
            message_count=2,
        )
        messages = [
            HistoryMessage(role="user", content="Hello"),
            HistoryMessage(role="assistant", content="Hi there!"),
        ]
        return Conversation(metadata=metadata, messages=messages)

    def test_create_conversation(self, sample_conversation):
        """Test creating a conversation."""
        assert sample_conversation.metadata.id == "conv-test"
        assert len(sample_conversation.messages) == 2

    def test_to_dict(self, sample_conversation):
        """Test serialisation to dictionary."""
        d = sample_conversation.to_dict()
        assert "metadata" in d
        assert "messages" in d
        assert len(d["messages"]) == 2

    def test_from_dict(self):
        """Test deserialisation from dictionary."""
        data = {
            "metadata": {
                "id": "restored-conv",
                "title": "Restored",
                "created_at": "2024-01-01T12:00:00",
                "updated_at": "2024-01-01T12:00:00",
                "message_count": 1,
            },
            "messages": [
                {
                    "role": "user",
                    "content": "Restored message",
                    "timestamp": "2024-01-01T12:00:00",
                }
            ],
        }
        conv = Conversation.from_dict(data)
        assert conv.metadata.id == "restored-conv"
        assert len(conv.messages) == 1


class TestConversationHistory:
    """Tests for ConversationHistory."""

    @pytest.fixture
    def history(self):
        """Create a conversation history with temp directory."""
        temp_dir = Path(tempfile.mkdtemp())
        hist = ConversationHistory(storage_path=temp_dir)
        yield hist
        shutil.rmtree(temp_dir)

    def test_create_conversation(self, history):
        """Test creating a new conversation."""
        conv = history.create("test-conv", title="Test Conversation")
        assert conv.metadata.id == "test-conv"
        assert conv.metadata.title == "Test Conversation"

    def test_create_with_tags(self, history):
        """Test creating conversation with tags."""
        conv = history.create("tagged-conv", tags=["test", "unit"])
        assert conv.metadata.tags == ["test", "unit"]

    def test_get_conversation(self, history):
        """Test getting a conversation."""
        history.create("get-test")
        conv = history.get("get-test")
        assert conv is not None
        assert conv.metadata.id == "get-test"

    def test_get_nonexistent(self, history):
        """Test getting nonexistent conversation."""
        conv = history.get("nonexistent")
        assert conv is None

    def test_add_message(self, history):
        """Test adding messages to conversation."""
        history.create("msg-test")
        msg = history.add_message("msg-test", "user", "Hello!")
        assert msg is not None
        assert msg.role == "user"
        assert msg.content == "Hello!"

        # Verify message was added
        conv = history.get("msg-test")
        assert len(conv.messages) == 1

    def test_add_message_updates_count(self, history):
        """Test that adding messages updates count."""
        history.create("count-test")
        history.add_message("count-test", "user", "Message 1")
        history.add_message("count-test", "assistant", "Message 2")

        conv = history.get("count-test")
        assert conv.metadata.message_count == 2

    def test_auto_generate_title(self, history):
        """Test auto-generating title from first message."""
        history.create("title-test")
        history.add_message("title-test", "user", "How do I configure the settings?")

        conv = history.get("title-test")
        assert conv.metadata.title == "How do I configure the settings?"

    def test_title_truncation(self, history):
        """Test that long titles are truncated."""
        history.create("long-title")
        long_message = "A" * 100
        history.add_message("long-title", "user", long_message)

        conv = history.get("long-title")
        assert len(conv.metadata.title) == 50
        assert conv.metadata.title.endswith("...")

    def test_list_conversations(self, history):
        """Test listing conversations."""
        history.create("list-1")
        history.create("list-2")
        history.create("list-3")

        conversations = history.list_conversations()
        assert len(conversations) == 3

    def test_list_with_limit(self, history):
        """Test listing with limit."""
        for i in range(5):
            history.create(f"limit-{i}")

        conversations = history.list_conversations(limit=3)
        assert len(conversations) == 3

    def test_list_with_tag_filter(self, history):
        """Test listing with tag filter."""
        history.create("tagged-1", tags=["important"])
        history.create("tagged-2", tags=["important"])
        history.create("untagged")

        conversations = history.list_conversations(tag="important")
        assert len(conversations) == 2

    def test_search_by_title(self, history):
        """Test searching by title."""
        history.create("search-1", title="Python Programming")
        history.create("search-2", title="JavaScript Basics")

        results = history.search("Python")
        assert len(results) == 1
        assert results[0].title == "Python Programming"

    def test_search_by_content(self, history):
        """Test searching by message content."""
        history.create("content-1")
        history.add_message("content-1", "user", "How do I use async await?")
        history.create("content-2")
        history.add_message("content-2", "user", "What is a variable?")

        results = history.search("async")
        assert len(results) == 1

    def test_delete_conversation(self, history):
        """Test deleting a conversation."""
        history.create("delete-test")
        assert history.delete("delete-test") is True
        assert history.get("delete-test") is None

    def test_delete_nonexistent(self, history):
        """Test deleting nonexistent conversation."""
        result = history.delete("nonexistent")
        assert result is False

    def test_update_metadata(self, history):
        """Test updating conversation metadata."""
        history.create("update-test")
        result = history.update_metadata(
            "update-test",
            title="Updated Title",
            summary="New summary",
            tags=["updated"],
        )
        assert result is True

        conv = history.get("update-test")
        assert conv.metadata.title == "Updated Title"
        assert conv.metadata.summary == "New summary"
        assert conv.metadata.tags == ["updated"]

    def test_export_json(self, history):
        """Test exporting to JSON."""
        history.create("export-json", title="Export Test")
        history.add_message("export-json", "user", "Test message")

        export = history.export("export-json", format="json")
        assert export is not None
        assert "Export Test" in export
        assert "Test message" in export

    def test_export_markdown(self, history):
        """Test exporting to Markdown."""
        history.create("export-md", title="Markdown Export")
        history.add_message("export-md", "user", "User message")
        history.add_message("export-md", "assistant", "Assistant response")

        export = history.export("export-md", format="markdown")
        assert export is not None
        assert "# Markdown Export" in export
        assert "**User:**" in export
        assert "**Assistant:**" in export

    def test_export_invalid_format(self, history):
        """Test exporting with invalid format."""
        history.create("export-invalid")
        export = history.export("export-invalid", format="invalid")
        assert export is None

    def test_count(self, history):
        """Test counting conversations."""
        assert history.count() == 0
        history.create("count-1")
        history.create("count-2")
        assert history.count() == 2

    def test_persistence(self, history):
        """Test that conversations persist across instances."""
        history.create("persist-test", title="Persistent")
        history.add_message("persist-test", "user", "Message")

        # Create new instance with same path
        new_history = ConversationHistory(storage_path=history.storage_path)
        conv = new_history.get("persist-test")
        assert conv is not None
        assert conv.metadata.title == "Persistent"
        assert len(conv.messages) == 1
