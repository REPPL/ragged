"""Tests for interactive REPL mode.

v0.3.8: Test interactive shell functionality.
"""

from io import StringIO
from unittest.mock import Mock, patch

import pytest

from src.cli.interactive import InteractiveShell, start_interactive_mode


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
        assert "0.3.8" in output
        assert "3" in output  # Command count

    def test_do_add_valid_file(self, shell):
        """Test add command with valid file."""
        with patch("sys.stdout", new=StringIO()) as fake_out:
            with patch("pathlib.Path.exists", return_value=True):
                shell.do_add("test.pdf")
                output = fake_out.getvalue()

        assert "Would add" in output or "✓" in output

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
        with patch("sys.stdout", new=StringIO()) as fake_out:
            shell.do_remove("test.pdf")
            output = fake_out.getvalue()

        assert "Would remove" in output or "✓" in output

    def test_do_remove_no_arg(self, shell):
        """Test remove command without argument."""
        with patch("sys.stdout", new=StringIO()) as fake_out:
            shell.do_remove("")
            output = fake_out.getvalue()

        assert "Error" in output or "Usage" in output

    def test_do_list(self, shell):
        """Test list command."""
        with patch("sys.stdout", new=StringIO()) as fake_out:
            shell.do_list("")
            output = fake_out.getvalue()

        assert "Documents" in output

    def test_do_show(self, shell):
        """Test show command."""
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
        with patch("sys.stdout", new=StringIO()) as fake_out:
            shell.do_query("what are the main findings?")
            output = fake_out.getvalue()

        assert "Querying" in output or "what are the main findings?" in output

    def test_do_query_no_arg(self, shell):
        """Test query command without argument."""
        with patch("sys.stdout", new=StringIO()) as fake_out:
            shell.do_query("")
            output = fake_out.getvalue()

        assert "Error" in output or "Usage" in output

    def test_do_search(self, shell):
        """Test search command."""
        with patch("sys.stdout", new=StringIO()) as fake_out:
            shell.do_search("machine learning")
            output = fake_out.getvalue()

        assert "Searching" in output or "machine learning" in output

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

        # Should be stored in config changes
        assert shell.config_changes["retrieval.top_k"] == "10"
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
        with patch("sys.stdout", new=StringIO()) as fake_out:
            shell.do_save("session test.json")
            output = fake_out.getvalue()

        assert "saved" in output or "✓" in output

    def test_do_save_invalid_syntax(self, shell):
        """Test save command with invalid syntax."""
        with patch("sys.stdout", new=StringIO()) as fake_out:
            shell.do_save("invalid")
            output = fake_out.getvalue()

        assert "Error" in output or "Usage" in output

    def test_do_load_session(self, shell):
        """Test load session command."""
        with patch("sys.stdout", new=StringIO()) as fake_out:
            with patch("pathlib.Path.exists", return_value=True):
                shell.do_load("session test.json")
                output = fake_out.getvalue()

        assert "loaded" in output or "✓" in output

    def test_do_load_missing_file(self, shell):
        """Test load session with missing file."""
        with patch("sys.stdout", new=StringIO()) as fake_out:
            with patch("pathlib.Path.exists", return_value=False):
                shell.do_load("session missing.json")
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
        """Test config command with no changes."""
        with patch("sys.stdout", new=StringIO()) as fake_out:
            shell.do_config("")
            output = fake_out.getvalue()

        assert "No configuration changes" in output

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
        with patch("src.cli.interactive.InteractiveShell") as MockShell:
            mock_shell = Mock()
            MockShell.return_value = mock_shell

            start_interactive_mode()

            # Should create shell and call cmdloop
            MockShell.assert_called_once()
            mock_shell.cmdloop.assert_called_once()

    def test_start_interactive_mode_keyboard_interrupt(self):
        """Test handling keyboard interrupt."""
        with patch("src.cli.interactive.InteractiveShell") as MockShell:
            mock_shell = Mock()
            mock_shell.cmdloop.side_effect = KeyboardInterrupt()
            MockShell.return_value = mock_shell

            with pytest.raises(SystemExit) as exc_info:
                start_interactive_mode()

            assert exc_info.value.code == 0

    def test_start_interactive_mode_exception(self):
        """Test handling general exceptions."""
        with patch("src.cli.interactive.InteractiveShell") as MockShell:
            mock_shell = Mock()
            mock_shell.cmdloop.side_effect = Exception("Test error")
            MockShell.return_value = mock_shell

            with pytest.raises(SystemExit) as exc_info:
                start_interactive_mode()

            assert exc_info.value.code == 1
