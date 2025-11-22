"""
Interactive REPL mode for exploratory RAG workflows.

v0.3.8: Read-Eval-Print Loop interface for ragged.
"""

import cmd
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

from src.config.settings import get_settings
from src.utils.logging import get_logger

logger = get_logger(__name__)


class InteractiveShell(cmd.Cmd):
    """
    Interactive REPL shell for ragged.

    Provides exploratory workflow with document management, queries,
    and configuration in a persistent session.
    """

    intro = """
🔍 ragged Interactive Mode

Type 'help' for commands, 'help <command>' for detailed help, 'exit' to quit.

Quick Start:
  add <file>           Add document to library
  query <question>     Ask a question
  list                 List all documents
  help                 Show all commands
"""

    prompt = "ragged> "

    def __init__(self):
        """Initialise interactive shell."""
        super().__init__()
        self.settings = get_settings()
        self.history: List[str] = []
        self.config_changes: Dict[str, Any] = {}
        self.context: Dict[str, Any] = {}

        # Disable default cmd features we don't want
        self.use_rawinput = True

    def precmd(self, line: str) -> str:
        """
        Pre-process command before execution.

        Args:
            line: Command line

        Returns:
            Processed command line
        """
        # Store in history (for session save)
        if line and line not in ("EOF", "exit", "quit"):
            self.history.append(line)

        return line

    def emptyline(self) -> bool:
        """
        Handle empty line (do nothing).

        Returns:
            False to continue REPL
        """
        return False

    def default(self, line: str) -> None:
        """
        Handle unknown commands.

        Args:
            line: Unknown command line
        """
        print(f"Unknown command: {line}")
        print("Type 'help' for available commands.")

    # Exit commands
    def do_exit(self, arg: str) -> bool:
        """Exit interactive mode."""
        print("Goodbye!")
        return True

    def do_quit(self, arg: str) -> bool:
        """Exit interactive mode (alias for 'exit')."""
        return self.do_exit(arg)

    def do_EOF(self, arg: str) -> bool:
        """Handle Ctrl+D (EOF)."""
        print()  # New line before exit
        return self.do_exit(arg)

    # Help and information commands
    def do_help(self, arg: str) -> None:
        """
        Show help for commands.

        Usage: help [command]
        """
        if not arg:
            # Show all commands grouped by category
            print("\n📚 Available Commands\n")

            print("Document Management:")
            print("  add <file>           Add document to library")
            print("  remove <pattern>     Remove documents")
            print("  list                 List all documents")
            print("  show <document>      Show document details")

            print("\nQuery Commands:")
            print("  query <question>     Ask a question")
            print("  search <keywords>    Keyword search")

            print("\nConfiguration:")
            print("  set <key> <value>    Set configuration value")
            print("  get <key>            Get configuration value")
            print("  show config          Display current configuration")
            print("  reset config         Reset to defaults")

            print("\nSession Management:")
            print("  history              Show command history")
            print("  save session <file>  Save session state")
            print("  load session <file>  Restore session")
            print("  clear                Clear screen")

            print("\nOther:")
            print("  help [command]       Show help")
            print("  status               Show system status")
            print("  exit                 Exit interactive mode")
            print()
        else:
            # Show help for specific command
            super().do_help(arg)

    def do_status(self, arg: str) -> None:
        """
        Show system status.

        Usage: status
        """
        print("\n📊 System Status\n")
        print(f"  ragged version: 0.3.8")
        print(f"  Documents loaded: 0")  # TODO: Get from actual library
        print(f"  Configuration: Default")  # TODO: Check if custom config
        print(f"  Commands executed: {len(self.history)}")
        print()

    # Document management commands
    def do_add(self, arg: str) -> None:
        """
        Add document to library.

        Usage: add <file>

        Example:
          add documents/paper.pdf
        """
        if not arg:
            print("Error: Please specify a file to add.")
            print("Usage: add <file>")
            return

        file_path = Path(arg.strip())

        if not file_path.exists():
            print(f"Error: File not found: {file_path}")
            return

        # TODO: Implement actual document addition
        print(f"✓ Would add {file_path} (not implemented)")

    def do_remove(self, arg: str) -> None:
        """
        Remove documents from library.

        Usage: remove <pattern>

        Example:
          remove paper.pdf
        """
        if not arg:
            print("Error: Please specify a pattern.")
            print("Usage: remove <pattern>")
            return

        # TODO: Implement actual document removal
        print(f"✓ Would remove documents matching '{arg}' (not implemented)")

    def do_list(self, arg: str) -> None:
        """
        List all documents in library.

        Usage: list
        """
        # TODO: Implement actual document listing
        print("\n📄 Documents in Library\n")
        print("  (No documents loaded)")
        print()

    def do_show(self, arg: str) -> None:
        """
        Show document details.

        Usage: show <document>

        Example:
          show paper.pdf
        """
        if not arg:
            print("Error: Please specify a document.")
            print("Usage: show <document>")
            return

        # TODO: Implement actual document details
        print(f"\n📄 Document Details: {arg}\n")
        print("  (Not implemented)")
        print()

    # Query commands
    def do_query(self, arg: str) -> None:
        """
        Ask a question about your documents.

        Usage: query <question>

        Example:
          query what are the main findings?
        """
        if not arg:
            print("Error: Please provide a question.")
            print("Usage: query <question>")
            return

        question = arg.strip()

        # TODO: Implement actual query
        print(f"\n🔍 Querying: {question}\n")
        print("  (Query not implemented - this is MVP)")
        print()

    def do_search(self, arg: str) -> None:
        """
        Keyword search in documents.

        Usage: search <keywords>

        Example:
          search machine learning
        """
        if not arg:
            print("Error: Please provide search keywords.")
            print("Usage: search <keywords>")
            return

        # TODO: Implement actual search
        print(f"\n🔍 Searching for: {arg}\n")
        print("  (Search not implemented)")
        print()

    # Configuration commands
    def do_set(self, arg: str) -> None:
        """
        Set configuration value.

        Usage: set <key> <value>

        Example:
          set retrieval.top_k 10
        """
        parts = arg.split(maxsplit=1)

        if len(parts) != 2:
            print("Error: Invalid syntax.")
            print("Usage: set <key> <value>")
            return

        key, value = parts

        # TODO: Implement actual configuration setting
        self.config_changes[key] = value
        print(f"✓ {key} = {value}")

    def do_get(self, arg: str) -> None:
        """
        Get configuration value.

        Usage: get <key>

        Example:
          get retrieval.top_k
        """
        if not arg:
            print("Error: Please specify a configuration key.")
            print("Usage: get <key>")
            return

        key = arg.strip()

        # Check if we have a local change
        if key in self.config_changes:
            print(f"{key} = {self.config_changes[key]}")
        else:
            # TODO: Get from actual settings
            print(f"{key} = (default)")

    # Session management commands
    def do_history(self, arg: str) -> None:
        """
        Show command history.

        Usage: history
        """
        if not self.history:
            print("No command history.")
            return

        print("\n📜 Command History\n")
        for i, cmd in enumerate(self.history, 1):
            print(f"  {i}. {cmd}")
        print()

    def do_save(self, arg: str) -> None:
        """
        Save session state.

        Usage: save session <file>

        Example:
          save session my_session.json
        """
        parts = arg.split(maxsplit=1)

        if len(parts) != 2 or parts[0] != "session":
            print("Error: Invalid syntax.")
            print("Usage: save session <file>")
            return

        filepath = Path(parts[1])

        # TODO: Implement actual session save
        print(f"✓ Session would be saved to {filepath} (not implemented)")

    def do_load(self, arg: str) -> None:
        """
        Load session state.

        Usage: load session <file>

        Example:
          load session my_session.json
        """
        parts = arg.split(maxsplit=1)

        if len(parts) != 2 or parts[0] != "session":
            print("Error: Invalid syntax.")
            print("Usage: load session <file>")
            return

        filepath = Path(parts[1])

        if not filepath.exists():
            print(f"Error: Session file not found: {filepath}")
            return

        # TODO: Implement actual session load
        print(f"✓ Session would be loaded from {filepath} (not implemented)")

    def do_clear(self, arg: str) -> None:
        """
        Clear the screen.

        Usage: clear
        """
        # ANSI clear screen
        print("\033[2J\033[H", end="")

    # Special command for showing configuration
    def do_config(self, arg: str) -> None:
        """
        Show current configuration.

        Usage: config
        """
        print("\n⚙️  Current Configuration\n")

        if self.config_changes:
            print("Session Changes:")
            for key, value in self.config_changes.items():
                print(f"  {key} = {value}")
        else:
            print("  (No configuration changes in this session)")

        print()


def start_interactive_mode() -> None:
    """
    Start interactive REPL mode.

    Example:
        >>> from src.cli.interactive import start_interactive_mode
        >>> start_interactive_mode()
    """
    try:
        shell = InteractiveShell()
        shell.cmdloop()
    except KeyboardInterrupt:
        print("\nInterrupted. Goodbye!")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Interactive mode error: {e}")
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    start_interactive_mode()
