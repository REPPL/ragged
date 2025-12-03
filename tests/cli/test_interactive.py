"""Tests for interactive REPL mode.

v0.8.8: Test interactive shell functionality with full implementations.
"""

import json
import tempfile
from io import StringIO
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import numpy as np
import pytest

from ragged.cli.interactive import InteractiveShell, start_interactive_mode


class TestInteractiveShell:
    """Test InteractiveShell REPL."""

    @pytest.fixture
    def shell(self):
        """Create interactive shell for testing."""
        return InteractiveShell()

    def test_shell_init(self, shell):
        """Test shell initialisation."""
        assert shell.prompt == "ragged> "
        assert len(shell.history) == 0
        assert len(shell.config_changes) == 0
        assert isinstance(shell.context, dict)

    def test_intro_message(self, shell):
        """Test intro message is set."""
        assert "ragged Interactive Mode" in shell.intro
        assert "help" in shell.intro
        assert "exit" in shell.intro

    def test_precmd_adds_to_history(self, shell):
        """Test precmd adds commands to history."""
        assert len(shell.history) == 0

        shell.precmd("test command")

        assert len(shell.history) == 1
        assert shell.history[0] == "test command"

    def test_precmd_ignores_exit_commands(self, shell):
        """Test precmd ignores exit commands in history."""
        shell.precmd("exit")
        shell.precmd("quit")
        shell.precmd("EOF")

        # None should be in history
        assert len(shell.history) == 0

    def test_emptyline(self, shell):
        """Test empty line handling."""
        result = shell.emptyline()

        # Should return False to continue REPL
        assert result is False

    def test_do_exit(self, shell):
        """Test exit command."""
        with patch("sys.stdout", new=StringIO()) as fake_out:
            result = shell.do_exit("")

        # Should return True to exit REPL
        assert result is True

    def test_do_quit(self, shell):
        """Test quit command (alias for exit)."""
        with patch("sys.stdout", new=StringIO()) as fake_out:
            result = shell.do_quit("")

        assert result is True

    def test_do_EOF(self, shell):
        """Test EOF handling (Ctrl+D)."""
        with patch("sys.stdout", new=StringIO()) as fake_out:
            result = shell.do_EOF("")

        assert result is True

    def test_do_help_general(self, shell):
        """Test general help command."""
        with patch("sys.stdout", new=StringIO()) as fake_out:
            shell.do_help("")
            output = fake_out.getvalue()

        # Should show all command categories
        assert "Available Commands" in output
        assert "Document Management" in output
        assert "Query Commands" in output
        assert "Configuration" in output
        assert "Session Management" in output

    def test_do_status(self, shell):
        """Test status command."""
        # Add some history first
        shell.history = ["cmd1", "cmd2", "cmd3"]

        with patch("sys.stdout", new=StringIO()) as fake_out:
            shell.do_status("")
            output = fake_out.getvalue()

        assert "System Status" in output
        assert "0.8.8" in output
        assert "3" in output  # Command count

    def test_do_add_valid_file(self, shell):
        """Test add command with valid file."""
        # Mock the required modules (import path must match where they're imported)
        mock_document = Mock()
        mock_document.text = "Test document content"
        mock_document.metadata = {"source": "test.txt"}

        mock_chunk = Mock()
        mock_chunk.text = "Test chunk"
        mock_chunk.metadata = {"source": "test.txt"}

        with patch("sys.stdout", new=StringIO()) as fake_out:
            with patch("pathlib.Path.exists", return_value=True):
                with patch(
                    "ragged.ingestion.loaders.load_document",
                    return_value=mock_document,
                ):
                    with patch(
                        "ragged.chunking.splitters.chunk_document",
                        return_value=[mock_chunk],
                    ):
                        # Mock the embedder and store via shell properties
                        shell._embedder = Mock()
                        shell._embedder.embed_documents.return_value = [
                            [0.1] * 384
                        ]
                        shell._store = Mock()
                        shell._store.add.return_value = None

                        shell.do_add("test.txt")
                        output = fake_out.getvalue()

        assert "✓" in output or "Added" in output

    def test_do_add_missing_file(self, shell):
        """Test add command with missing file."""
        with patch("sys.stdout", new=StringIO()) as fake_out:
            with patch("pathlib.Path.exists", return_value=False):
                shell.do_add("missing.pdf")
                output = fake_out.getvalue()

        assert "Error" in output or "not found" in output

    def test_do_add_no_arg(self, shell):
        """Test add command without argument."""
        with patch("sys.stdout", new=StringIO()) as fake_out:
            shell.do_add("")
            output = fake_out.getvalue()

        assert "Error" in output or "Usage" in output

    def test_do_remove(self, shell):
        """Test remove command."""
        # Mock the store with documents (flat lists, not nested)
        shell._store = Mock()
        shell._store.list.return_value = {
            "ids": ["doc_test_1", "doc_test_2"],
            "metadatas": [
                {"document_path": "/path/test.pdf", "file_name": "test.pdf"},
                {"document_path": "/path/test.pdf", "file_name": "test.pdf"},
            ],
        }
        shell._store.delete.return_value = None

        with patch("sys.stdout", new=StringIO()) as fake_out:
            with patch("builtins.input", return_value="y"):
                shell.do_remove("test.pdf")
                output = fake_out.getvalue()

        assert "✓" in output or "Removed" in output

    def test_do_remove_no_arg(self, shell):
        """Test remove command without argument."""
        with patch("sys.stdout", new=StringIO()) as fake_out:
            shell.do_remove("")
            output = fake_out.getvalue()

        assert "Error" in output or "Usage" in output

    def test_do_list(self, shell):
        """Test list command."""
        # Mock the store with documents (flat lists)
        shell._store = Mock()
        shell._store.list.return_value = {
            "ids": ["doc1", "doc2"],
            "metadatas": [
                {"document_path": "/path/file1.pdf", "file_name": "file1.pdf"},
                {"document_path": "/path/file2.pdf", "file_name": "file2.pdf"},
            ],
        }

        with patch("sys.stdout", new=StringIO()) as fake_out:
            shell.do_list("")
            output = fake_out.getvalue()

        assert "Documents" in output or "file1.pdf" in output

    def test_do_list_empty(self, shell):
        """Test list command with empty store."""
        shell._store = Mock()
        shell._store.list.return_value = {"ids": [], "metadatas": []}

        with patch("sys.stdout", new=StringIO()) as fake_out:
            shell.do_list("")
            output = fake_out.getvalue()

        assert "No documents" in output or "empty" in output.lower()

    def test_do_show(self, shell):
        """Test show command."""
        shell._store = Mock()
        shell._store.list.return_value = {
            "ids": ["doc1", "doc2"],
            "metadatas": [
                {"document_path": "/path/test.pdf", "file_name": "test.pdf"},
                {"document_path": "/path/test.pdf", "file_name": "test.pdf"},
            ],
            "documents": ["chunk 1 content", "chunk 2 content"],
        }

        with patch("sys.stdout", new=StringIO()) as fake_out:
            shell.do_show("test.pdf")
            output = fake_out.getvalue()

        assert "Document Details" in output or "test.pdf" in output

    def test_do_show_no_arg(self, shell):
        """Test show command without argument."""
        with patch("sys.stdout", new=StringIO()) as fake_out:
            shell.do_show("")
            output = fake_out.getvalue()

        assert "Error" in output or "Usage" in output

    def test_do_query(self, shell):
        """Test query command."""
        # Mock retriever
        mock_chunk = Mock()
        mock_chunk.text = "This is relevant content"
        mock_chunk.metadata = {"source": "doc.pdf"}
        mock_chunk.score = 0.95

        shell._retriever = Mock()
        shell._retriever.retrieve.return_value = [mock_chunk]

        with patch("sys.stdout", new=StringIO()) as fake_out:
            with patch(
                "ragged.generation.ollama_client.OllamaClient"
            ) as mock_client_class:
                mock_client = Mock()
                mock_client.generate.return_value = "Based on the documents, the answer is..."
                mock_client_class.return_value = mock_client

                with patch(
                    "ragged.generation.prompts.build_rag_prompt",
                    return_value="prompt",
                ):
                    with patch(
                        "ragged.generation.citation_formatter.format_response_with_references",
                        return_value="Formatted answer",
                    ):
                        shell.do_query("what are the main findings?")
                        output = fake_out.getvalue()

        assert "Answer" in output or "Formatted" in output

    def test_do_query_no_arg(self, shell):
        """Test query command without argument."""
        with patch("sys.stdout", new=StringIO()) as fake_out:
            shell.do_query("")
            output = fake_out.getvalue()

        assert "Error" in output or "Usage" in output

    def test_do_search(self, shell):
        """Test search command."""
        # Mock retriever
        mock_chunk = Mock()
        mock_chunk.text = "Machine learning content"
        mock_chunk.metadata = {"source": "ml_paper.pdf"}
        mock_chunk.score = 0.92

        shell._retriever = Mock()
        shell._retriever.retrieve.return_value = [mock_chunk]

        with patch("sys.stdout", new=StringIO()) as fake_out:
            shell.do_search("machine learning")
            output = fake_out.getvalue()

        assert "Search Results" in output or "machine learning" in output.lower()

    def test_do_search_no_arg(self, shell):
        """Test search command without argument."""
        with patch("sys.stdout", new=StringIO()) as fake_out:
            shell.do_search("")
            output = fake_out.getvalue()

        assert "Error" in output or "Usage" in output

    def test_do_set(self, shell):
        """Test set configuration command."""
        with patch("sys.stdout", new=StringIO()) as fake_out:
            shell.do_set("retrieval.top_k 10")
            output = fake_out.getvalue()

        # Should be stored in config changes (as int after parsing)
        assert shell.config_changes["retrieval.top_k"] == 10
        assert "✓" in output or "retrieval.top_k" in output

    def test_do_set_invalid_syntax(self, shell):
        """Test set command with invalid syntax."""
        with patch("sys.stdout", new=StringIO()) as fake_out:
            shell.do_set("invalid")
            output = fake_out.getvalue()

        assert "Error" in output or "Usage" in output

    def test_do_get_existing_change(self, shell):
        """Test get command for locally changed config."""
        shell.config_changes["test.key"] = "test_value"

        with patch("sys.stdout", new=StringIO()) as fake_out:
            shell.do_get("test.key")
            output = fake_out.getvalue()

        assert "test_value" in output

    def test_do_get_default(self, shell):
        """Test get command for default config."""
        with patch("sys.stdout", new=StringIO()) as fake_out:
            shell.do_get("some.key")
            output = fake_out.getvalue()

        assert "default" in output or "some.key" in output

    def test_do_get_no_arg(self, shell):
        """Test get command without argument."""
        with patch("sys.stdout", new=StringIO()) as fake_out:
            shell.do_get("")
            output = fake_out.getvalue()

        assert "Error" in output or "Usage" in output

    def test_do_history(self, shell):
        """Test history command."""
        shell.history = ["cmd1", "cmd2", "cmd3"]

        with patch("sys.stdout", new=StringIO()) as fake_out:
            shell.do_history("")
            output = fake_out.getvalue()

        assert "Command History" in output
        assert "cmd1" in output
        assert "cmd2" in output
        assert "cmd3" in output

    def test_do_history_empty(self, shell):
        """Test history command with no history."""
        with patch("sys.stdout", new=StringIO()) as fake_out:
            shell.do_history("")
            output = fake_out.getvalue()

        assert "No command history" in output

    def test_do_save_session(self, shell):
        """Test save session command."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False
        ) as f:
            temp_path = f.name

        try:
            # Add some state to save
            shell.history = ["cmd1", "cmd2"]
            shell.config_changes = {"key": "value"}

            with patch("sys.stdout", new=StringIO()) as fake_out:
                shell.do_save(f"session {temp_path}")
                output = fake_out.getvalue()

            assert "✓" in output or "saved" in output.lower()

            # Verify file content
            with open(temp_path) as f:
                saved = json.load(f)
            assert saved["history"] == ["cmd1", "cmd2"]
            assert saved["config_changes"] == {"key": "value"}
        finally:
            Path(temp_path).unlink(missing_ok=True)

    def test_do_save_invalid_syntax(self, shell):
        """Test save command with invalid syntax."""
        with patch("sys.stdout", new=StringIO()) as fake_out:
            shell.do_save("invalid")
            output = fake_out.getvalue()

        assert "Error" in output or "Usage" in output

    def test_do_load_session(self, shell):
        """Test load session command."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False
        ) as f:
            session_data = {
                "version": "0.8.8",
                "history": ["loaded_cmd1", "loaded_cmd2"],
                "config_changes": {"loaded_key": "loaded_value"},
                "context": {},
            }
            json.dump(session_data, f)
            temp_path = f.name

        try:
            with patch("sys.stdout", new=StringIO()) as fake_out:
                shell.do_load(f"session {temp_path}")
                output = fake_out.getvalue()

            assert "✓" in output or "loaded" in output.lower()
            assert shell.history == ["loaded_cmd1", "loaded_cmd2"]
            assert shell.config_changes == {"loaded_key": "loaded_value"}
        finally:
            Path(temp_path).unlink(missing_ok=True)

    def test_do_load_missing_file(self, shell):
        """Test load session with missing file."""
        with patch("sys.stdout", new=StringIO()) as fake_out:
            shell.do_load("session /nonexistent/path/missing.json")
            output = fake_out.getvalue()

        assert "Error" in output or "not found" in output

    def test_do_load_invalid_syntax(self, shell):
        """Test load command with invalid syntax."""
        with patch("sys.stdout", new=StringIO()) as fake_out:
            shell.do_load("invalid")
            output = fake_out.getvalue()

        assert "Error" in output or "Usage" in output

    def test_do_clear(self, shell):
        """Test clear screen command."""
        with patch("sys.stdout", new=StringIO()) as fake_out:
            shell.do_clear("")
            output = fake_out.getvalue()

        # Should output ANSI clear codes
        assert "\033[2J" in output

    def test_do_config(self, shell):
        """Test config command."""
        shell.config_changes = {"key1": "value1", "key2": "value2"}

        with patch("sys.stdout", new=StringIO()) as fake_out:
            shell.do_config("")
            output = fake_out.getvalue()

        assert "Current Configuration" in output
        assert "key1" in output
        assert "value1" in output

    def test_do_config_no_changes(self, shell):
        """Test config command with no changes shows defaults."""
        with patch("sys.stdout", new=StringIO()) as fake_out:
            shell.do_config("")
            output = fake_out.getvalue()

        # Config always shows defaults, even with no session changes
        assert "Current Configuration" in output or "Default Settings" in output

    def test_default_unknown_command(self, shell):
        """Test default handler for unknown commands."""
        with patch("sys.stdout", new=StringIO()) as fake_out:
            shell.default("unknown_command")
            output = fake_out.getvalue()

        assert "Unknown command" in output
        assert "help" in output


class TestStartInteractiveMode:
    """Test start_interactive_mode function."""

    def test_start_interactive_mode(self):
        """Test starting interactive mode."""
        with patch("ragged.cli.interactive.InteractiveShell") as MockShell:
            mock_shell = Mock()
            MockShell.return_value = mock_shell

            start_interactive_mode()

            # Should create shell and call cmdloop
            MockShell.assert_called_once()
            mock_shell.cmdloop.assert_called_once()

    def test_start_interactive_mode_keyboard_interrupt(self):
        """Test handling keyboard interrupt."""
        with patch("ragged.cli.interactive.InteractiveShell") as MockShell:
            mock_shell = Mock()
            mock_shell.cmdloop.side_effect = KeyboardInterrupt()
            MockShell.return_value = mock_shell

            with pytest.raises(SystemExit) as exc_info:
                start_interactive_mode()

            assert exc_info.value.code == 0

    def test_start_interactive_mode_exception(self):
        """Test handling general exceptions."""
        with patch("ragged.cli.interactive.InteractiveShell") as MockShell:
            mock_shell = Mock()
            mock_shell.cmdloop.side_effect = Exception("Test error")
            MockShell.return_value = mock_shell

            with pytest.raises(SystemExit) as exc_info:
                start_interactive_mode()

            assert exc_info.value.code == 1


class TestLazyLoading:
    """Test lazy loading of services."""

    @pytest.fixture
    def shell(self):
        """Create interactive shell for testing."""
        return InteractiveShell()

    def test_store_not_loaded_on_init(self, shell):
        """Test store is not loaded on initialisation."""
        assert shell._store is None

    def test_retriever_not_loaded_on_init(self, shell):
        """Test retriever is not loaded on initialisation."""
        assert shell._retriever is None

    def test_embedder_not_loaded_on_init(self, shell):
        """Test embedder is not loaded on initialisation."""
        assert shell._embedder is None

    def test_store_lazy_loads(self, shell):
        """Test store loads lazily on first access."""
        with patch("ragged.storage.vector_store.VectorStore") as MockStore:
            mock_store = Mock()
            MockStore.return_value = mock_store

            # Access store property
            _ = shell.store

            MockStore.assert_called_once()
            assert shell._store is mock_store

    def test_retriever_lazy_loads(self, shell):
        """Test retriever loads lazily on first access."""
        with patch("ragged.retrieval.hybrid.HybridRetriever") as MockHybrid:
            with patch("ragged.retrieval.bm25.BM25Retriever") as MockBM25:
                with patch("ragged.retrieval.retriever.Retriever") as MockVector:
                    mock_retriever = Mock()
                    MockHybrid.return_value = mock_retriever

                    # Access retriever property
                    _ = shell.retriever

                    MockHybrid.assert_called_once()
                    MockBM25.assert_called_once()
                    MockVector.assert_called_once()
                    assert shell._retriever is mock_retriever

    def test_embedder_lazy_loads(self, shell):
        """Test embedder loads lazily on first access."""
        with patch("ragged.embeddings.factory.get_embedder") as mock_get:
            mock_embedder = Mock()
            mock_get.return_value = mock_embedder

            # Access embedder property
            _ = shell.embedder

            mock_get.assert_called_once()
            assert shell._embedder is mock_embedder

    def test_services_cached_after_first_load(self, shell):
        """Test services are cached after first load."""
        with patch("ragged.storage.vector_store.VectorStore") as MockStore:
            mock_store = Mock()
            MockStore.return_value = mock_store

            # Access store multiple times
            _ = shell.store
            _ = shell.store
            _ = shell.store

            # Should only be created once
            MockStore.assert_called_once()


class TestSessionRoundTrip:
    """Test full session save/load workflow."""

    @pytest.fixture
    def shell(self):
        """Create interactive shell for testing."""
        return InteractiveShell()

    def test_session_round_trip(self, shell):
        """Test saving and loading session preserves state."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False
        ) as f:
            temp_path = f.name

        try:
            # Set up initial state
            shell.history = ["add doc.pdf", "query what is this?", "search AI"]
            shell.config_changes = {
                "retrieval.top_k": "10",
                "generation.temperature": "0.7",
            }
            shell.context = {"last_query": "what is this?"}

            # Save session
            with patch("sys.stdout", new=StringIO()):
                shell.do_save(f"session {temp_path}")

            # Create new shell and load session
            new_shell = InteractiveShell()
            with patch("sys.stdout", new=StringIO()):
                new_shell.do_load(f"session {temp_path}")

            # Verify state preserved
            assert new_shell.history == shell.history
            assert new_shell.config_changes == shell.config_changes
            assert new_shell.context.get("last_query") == "what is this?"
        finally:
            Path(temp_path).unlink(missing_ok=True)
