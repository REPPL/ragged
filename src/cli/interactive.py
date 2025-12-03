"""
Interactive REPL mode for exploratory RAG workflows.

v0.3.8: Read-Eval-Print Loop interface for ragged.
v0.8.8: Full implementation of all interactive commands.
"""

import cmd
import hashlib
import json
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

from ragged.config.settings import get_settings
from ragged.utils.logging import get_logger

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
        """Initialise interactive shell with lazy service loading."""
        super().__init__()
        self.settings = get_settings()
        self.history: list[str] = []
        self.config_changes: dict[str, Any] = {}
        self.context: dict[str, Any] = {}

        # Lazy-loaded services (initialised on first use)
        self._store = None
        self._retriever = None
        self._embedder = None

        # Disable default cmd features we don't want
        self.use_rawinput = True

    @property
    def store(self):
        """Lazy-load vector store."""
        if self._store is None:
            from ragged.storage.vector_store import VectorStore
            self._store = VectorStore()
            logger.info("Vector store initialised")
        return self._store

    @property
    def retriever(self):
        """Lazy-load retriever."""
        if self._retriever is None:
            from ragged.retrieval.hybrid import HybridRetriever
            from ragged.retrieval.bm25 import BM25Retriever
            from ragged.retrieval.retriever import Retriever
            vector_retriever = Retriever()
            bm25_retriever = BM25Retriever()
            self._retriever = HybridRetriever(
                vector_retriever=vector_retriever,
                bm25_retriever=bm25_retriever
            )
            logger.info("Retriever initialised")
        return self._retriever

    @property
    def embedder(self):
        """Lazy-load embedder."""
        if self._embedder is None:
            from ragged.embeddings.factory import get_embedder
            self._embedder = get_embedder()
            logger.info("Embedder initialised")
        return self._embedder

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
        print("  ragged version: 0.8.8")

        try:
            # Get document count from store
            doc_count = self.store.count()
            health = self.store.health_check()
            print(f"  Documents loaded: {doc_count}")
            print(f"  ChromaDB status: {'✓ Connected' if health else '✗ Disconnected'}")
        except Exception as e:
            print(f"  ChromaDB status: ✗ Error ({e})")

        # Check if custom config
        config_status = "Custom" if self.config_changes else "Default"
        print(f"  Configuration: {config_status}")
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

        file_path = Path(arg.strip()).resolve()

        if not file_path.exists():
            print(f"Error: File not found: {file_path}")
            return

        try:
            from ragged.chunking.splitters import chunk_document
            from ragged.ingestion.loaders import load_document

            print(f"Loading {file_path.name}...")

            # Load document
            document = load_document(file_path)
            if not document:
                print(f"Error: Could not load document: {file_path}")
                return

            print(f"Chunking document...")

            # Chunk document
            chunks = chunk_document(document, strategy="fixed")
            if not chunks:
                print(f"Error: No chunks created from document")
                return

            print(f"Embedding {len(chunks)} chunks...")

            # Generate embeddings
            texts = [chunk.text for chunk in chunks]
            embeddings = self.embedder.embed_documents(texts)

            # Generate IDs and metadata
            import numpy as np
            doc_id = hashlib.sha256(str(file_path).encode()).hexdigest()[:16]
            ids = [f"{doc_id}_{i}" for i in range(len(chunks))]
            metadatas = [
                {
                    "document_id": doc_id,
                    "document_path": str(file_path),
                    "chunk_position": i,
                    "page_number": getattr(chunk, "page_number", 0),
                    "file_name": file_path.name,
                }
                for i, chunk in enumerate(chunks)
            ]

            # Add to store
            self.store.add(
                ids=ids,
                embeddings=np.array(embeddings),
                documents=texts,
                metadatas=metadatas,
            )

            print(f"✓ Added {file_path.name} ({len(chunks)} chunks)")

        except Exception as e:
            print(f"Error adding document: {e}")
            logger.error(f"do_add failed: {e}", exc_info=True)

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

        pattern = arg.strip()

        try:
            # Find documents matching pattern
            results = self.store.list(limit=1000)

            if not results.get("ids"):
                print("No documents in library.")
                return

            # Group chunks by document path
            docs_to_remove: dict[str, list[str]] = defaultdict(list)
            for i, chunk_id in enumerate(results["ids"]):
                metadata = results["metadatas"][i] if results.get("metadatas") else {}
                doc_path = metadata.get("document_path", "")
                file_name = metadata.get("file_name", "")

                if pattern in doc_path or pattern in file_name:
                    docs_to_remove[doc_path].append(chunk_id)

            if not docs_to_remove:
                print(f"No documents matching '{pattern}' found.")
                return

            # Confirm removal
            print(f"\nDocuments matching '{pattern}':")
            for doc_path in docs_to_remove:
                print(f"  - {doc_path} ({len(docs_to_remove[doc_path])} chunks)")

            total_chunks = sum(len(ids) for ids in docs_to_remove.values())
            confirm = input(f"\nRemove {len(docs_to_remove)} document(s) ({total_chunks} chunks)? [y/N] ")

            if confirm.lower() != "y":
                print("Cancelled.")
                return

            # Remove chunks
            all_ids = []
            for ids in docs_to_remove.values():
                all_ids.extend(ids)

            self.store.delete(ids=all_ids)
            print(f"✓ Removed {len(docs_to_remove)} document(s)")

        except Exception as e:
            print(f"Error removing documents: {e}")
            logger.error(f"do_remove failed: {e}", exc_info=True)

    def do_list(self, arg: str) -> None:
        """
        List all documents in library.

        Usage: list
        """
        try:
            results = self.store.list(limit=1000)

            if not results.get("ids"):
                print("\n📄 Documents in Library\n")
                print("  (No documents loaded)")
                print()
                return

            # Group by document
            documents: dict[str, dict[str, Any]] = {}
            for i, chunk_id in enumerate(results["ids"]):
                metadata = results["metadatas"][i] if results.get("metadatas") else {}
                doc_path = metadata.get("document_path", "unknown")

                if doc_path not in documents:
                    documents[doc_path] = {
                        "chunks": 0,
                        "file_name": metadata.get("file_name", Path(doc_path).name),
                    }
                documents[doc_path]["chunks"] += 1

            print(f"\n📄 Documents in Library ({len(documents)} documents, {len(results['ids'])} chunks)\n")

            for doc_path, info in sorted(documents.items()):
                print(f"  • {info['file_name']}")
                print(f"    Path: {doc_path}")
                print(f"    Chunks: {info['chunks']}")
                print()

        except Exception as e:
            print(f"Error listing documents: {e}")
            logger.error(f"do_list failed: {e}", exc_info=True)

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

        pattern = arg.strip()

        try:
            results = self.store.list(limit=1000)

            if not results.get("ids"):
                print("No documents in library.")
                return

            # Find matching document
            doc_chunks: list[tuple[str, str, dict]] = []
            for i, chunk_id in enumerate(results["ids"]):
                metadata = results["metadatas"][i] if results.get("metadatas") else {}
                doc_path = metadata.get("document_path", "")
                file_name = metadata.get("file_name", "")
                text = results["documents"][i] if results.get("documents") else ""

                if pattern in doc_path or pattern in file_name:
                    doc_chunks.append((chunk_id, text, metadata))

            if not doc_chunks:
                print(f"No document matching '{pattern}' found.")
                return

            # Show document info
            first_metadata = doc_chunks[0][2]
            print(f"\n📄 Document Details: {first_metadata.get('file_name', pattern)}\n")
            print(f"  Path: {first_metadata.get('document_path', 'unknown')}")
            print(f"  Document ID: {first_metadata.get('document_id', 'unknown')}")
            print(f"  Chunks: {len(doc_chunks)}")

            # Show first few chunks
            print(f"\n  Preview (first 3 chunks):")
            for i, (chunk_id, text, metadata) in enumerate(doc_chunks[:3]):
                preview = text[:150].replace("\n", " ")
                if len(text) > 150:
                    preview += "..."
                page = metadata.get("page_number", "?")
                print(f"\n  [{i+1}] Page {page}:")
                print(f"      {preview}")

            print()

        except Exception as e:
            print(f"Error showing document: {e}")
            logger.error(f"do_show failed: {e}", exc_info=True)

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

        try:
            from ragged.generation.ollama_client import OllamaClient
            from ragged.generation.prompts import RAG_SYSTEM_PROMPT, build_rag_prompt
            from ragged.generation.citation_formatter import format_response_with_references

            print(f"\n🔍 Querying: {question}\n")
            print("Retrieving relevant chunks...")

            # Retrieve relevant chunks
            top_k = int(self.config_changes.get("retrieval.top_k", 5))
            chunks = self.retriever.retrieve(question, top_k=top_k)

            if not chunks:
                print("No relevant documents found. Have you ingested any documents?")
                print("Use: add <file_path> to ingest documents.")
                return

            print(f"Found {len(chunks)} relevant chunks. Generating answer...")

            # Generate answer
            ollama_client = OllamaClient()
            prompt = build_rag_prompt(question, chunks)
            response_text = ollama_client.generate(prompt, system=RAG_SYSTEM_PROMPT)

            # Format with citations
            formatted_response = format_response_with_references(
                response_text,
                chunks,
                show_file_path=True,
                include_unused_refs=False
            )

            print("\n📝 Answer:\n")
            print(formatted_response)

            print("\n📚 Sources:")
            for i, chunk in enumerate(chunks[:5], 1):
                print(f"  [{i}] {chunk.document_path} (score: {chunk.score:.3f})")

            print()

            # Store in context for follow-up
            self.context["last_query"] = question
            self.context["last_chunks"] = chunks

        except Exception as e:
            print(f"Error running query: {e}")
            logger.error(f"do_query failed: {e}", exc_info=True)

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

        keywords = arg.strip()

        try:
            from ragged.retrieval.retriever import Retriever

            print(f"\n🔍 Searching for: {keywords}\n")

            # Use vector retriever directly for semantic search
            vector_retriever = Retriever()
            top_k = int(self.config_changes.get("retrieval.top_k", 10))
            chunks = vector_retriever.retrieve(keywords, k=top_k)

            if not chunks:
                print("No matching documents found.")
                return

            print(f"Found {len(chunks)} matching chunks:\n")

            for i, chunk in enumerate(chunks, 1):
                preview = chunk.text[:200].replace("\n", " ")
                if len(chunk.text) > 200:
                    preview += "..."

                print(f"[{i}] {chunk.document_path}")
                print(f"    Score: {chunk.score:.3f}")
                print(f"    {preview}")
                print()

        except Exception as e:
            print(f"Error searching: {e}")
            logger.error(f"do_search failed: {e}", exc_info=True)

    # Configuration commands
    def do_set(self, arg: str) -> None:
        """
        Set configuration value.

        Usage: set <key> <value>

        Available keys:
          retrieval.top_k    Number of chunks to retrieve (default: 5)
          retrieval.method   Retrieval method: vector, bm25, hybrid (default: hybrid)

        Example:
          set retrieval.top_k 10
        """
        parts = arg.split(maxsplit=1)

        if len(parts) != 2:
            print("Error: Invalid syntax.")
            print("Usage: set <key> <value>")
            print("\nAvailable keys:")
            print("  retrieval.top_k    Number of chunks to retrieve")
            print("  retrieval.method   Retrieval method (vector, bm25, hybrid)")
            return

        key, value = parts

        # Validate known keys
        valid_keys = {"retrieval.top_k", "retrieval.method"}
        if key not in valid_keys:
            print(f"Warning: Unknown key '{key}'. Setting anyway.")

        # Type conversion for known keys
        if key == "retrieval.top_k":
            try:
                value = int(value)
            except ValueError:
                print(f"Error: '{value}' is not a valid integer")
                return

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
            # Get from actual settings
            defaults = {
                "retrieval.top_k": self.settings.retrieval_k,
                "retrieval.method": self.settings.retrieval_method,
            }
            if key in defaults:
                print(f"{key} = {defaults[key]} (default)")
            else:
                print(f"{key} = (unknown key)")

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

        try:
            session = {
                "version": "0.8.8",
                "history": self.history,
                "config_changes": self.config_changes,
                "context": {
                    k: v for k, v in self.context.items()
                    if k != "last_chunks"  # Don't serialise chunk objects
                },
            }

            with open(filepath, "w") as f:
                json.dump(session, f, indent=2)

            print(f"✓ Session saved to {filepath}")

        except Exception as e:
            print(f"Error saving session: {e}")
            logger.error(f"do_save failed: {e}", exc_info=True)

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

        try:
            with open(filepath) as f:
                session = json.load(f)

            # Restore session state
            self.history = session.get("history", [])
            self.config_changes = session.get("config_changes", {})
            self.context = session.get("context", {})

            print(f"✓ Session loaded from {filepath}")
            print(f"  History: {len(self.history)} commands")
            print(f"  Config changes: {len(self.config_changes)}")

        except json.JSONDecodeError as e:
            print(f"Error: Invalid JSON in session file: {e}")
        except Exception as e:
            print(f"Error loading session: {e}")
            logger.error(f"do_load failed: {e}", exc_info=True)

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

        print("Default Settings:")
        print(f"  retrieval.top_k = {self.settings.retrieval_k}")
        print(f"  retrieval.method = {self.settings.retrieval_method}")
        print(f"  embedding.model = {self.settings.embedding_model}")
        print(f"  llm.model = {self.settings.llm_model}")

        if self.config_changes:
            print("\nSession Overrides:")
            for key, value in self.config_changes.items():
                print(f"  {key} = {value}")

        print()


def start_interactive_mode() -> None:
    """
    Start interactive REPL mode.

    Example:
        >>> from ragged.cli.interactive import start_interactive_mode
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
