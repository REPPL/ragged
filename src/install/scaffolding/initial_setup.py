"""
Initial Setup.

PREREQ-005: Runs initial setup tasks including database initialisation,
default collection creation, and example data seeding.
"""

import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


def run_initial_setup(
    ragged_home: Path | None = None,
    create_collection: bool = True,
    seed_examples: bool = False,
    collection_name: str = "ragged_documents",
) -> dict[str, Any]:
    """
    Run initial setup after installation.

    Args:
        ragged_home: Path to ragged home directory.
        create_collection: Whether to create default collection.
        seed_examples: Whether to seed example documents.
        collection_name: Name of the default collection.

    Returns:
        Dictionary with setup results.
    """
    import os

    if ragged_home is None:
        ragged_home = Path(os.environ.get("RAGGED_HOME", Path.home() / ".ragged"))

    result: dict[str, Any] = {
        "success": True,
        "collection_created": False,
        "examples_seeded": False,
        "errors": [],
        "warnings": [],
    }

    # Create default collection
    if create_collection:
        try:
            collection_result = _create_default_collection(collection_name)
            result["collection_created"] = collection_result
            if not collection_result:
                result["warnings"].append("Could not create default collection")
        except Exception as e:
            result["warnings"].append(f"Collection creation failed: {e}")
            logger.warning(f"Failed to create collection: {e}")

    # Seed example documents
    if seed_examples:
        try:
            seed_result = _seed_example_documents(ragged_home)
            result["examples_seeded"] = seed_result
        except Exception as e:
            result["warnings"].append(f"Example seeding failed: {e}")
            logger.warning(f"Failed to seed examples: {e}")

    return result


def _create_default_collection(collection_name: str) -> bool:
    """
    Create the default ChromaDB collection.

    Args:
        collection_name: Name of the collection to create.

    Returns:
        True if successful.
    """
    try:
        # Try to connect to ChromaDB
        import httpx

        response = httpx.post(
            "http://localhost:8001/api/v1/collections",
            json={
                "name": collection_name,
                "metadata": {
                    "description": "Default ragged document collection",
                    "created_by": "installer",
                },
            },
            timeout=10.0,
        )

        if response.status_code in (200, 201):
            logger.info(f"Created collection: {collection_name}")
            return True
        elif response.status_code == 409:
            # Collection already exists
            logger.info(f"Collection already exists: {collection_name}")
            return True
        else:
            logger.warning(f"Failed to create collection: {response.status_code}")
            return False

    except httpx.ConnectError:
        logger.warning("ChromaDB not available, skipping collection creation")
        return False
    except ImportError:
        logger.warning("httpx not available, skipping collection creation")
        return False
    except Exception as e:
        logger.warning(f"Collection creation error: {e}")
        return False


def _seed_example_documents(ragged_home: Path) -> bool:
    """
    Seed example documents for testing.

    Args:
        ragged_home: Path to ragged home directory.

    Returns:
        True if successful.
    """
    documents_dir = ragged_home / "documents"
    examples_dir = documents_dir / "examples"

    try:
        examples_dir.mkdir(parents=True, exist_ok=True)

        # Create a simple example markdown file
        example_file = examples_dir / "getting-started.md"

        if not example_file.exists():
            content = """# Getting Started with ragged

Welcome to ragged! This is an example document to help you get started.

## What is ragged?

ragged is a privacy-first local RAG (Retrieval-Augmented Generation) system
for document question-answering. All your data stays on your machine.

## Quick Start

1. **Upload Documents**: Drag and drop documents into the WebUI, or use the CLI:
   ```bash
   ragged add document.pdf
   ```

2. **Ask Questions**: Query your documents:
   ```bash
   ragged query "What is this document about?"
   ```

3. **Explore**: Use the WebUI at http://localhost:5173 for a visual interface.

## Features

- **Privacy First**: All processing happens locally
- **Multiple Formats**: PDF, Word, Markdown, HTML, and more
- **Smart Retrieval**: Hybrid search combining semantic and keyword search
- **Local LLMs**: Uses Ollama for inference

## Learn More

- Documentation: https://ragged.ai/docs
- GitHub: https://github.com/ragged/ragged
- Issues: https://github.com/ragged/ragged/issues

---

*This is an example document created during installation.*
"""
            with open(example_file, "w") as f:
                f.write(content)

            logger.info(f"Created example document: {example_file}")

        return True

    except OSError as e:
        logger.warning(f"Failed to seed examples: {e}")
        return False


def generate_default_user(
    username: str = "admin",
    email: str = "admin@localhost",
) -> dict[str, Any]:
    """
    Generate default admin user credentials.

    Args:
        username: Username for the admin.
        email: Email for the admin.

    Returns:
        Dictionary with user credentials.
    """
    import secrets
    import string

    # Generate secure random password
    alphabet = string.ascii_letters + string.digits + string.punctuation
    password = "".join(secrets.choice(alphabet) for _ in range(16))

    return {
        "username": username,
        "email": email,
        "password": password,
        "role": "admin",
    }


def display_next_steps(ragged_home: Path) -> str:
    """
    Generate next steps message for user.

    Args:
        ragged_home: Path to ragged home directory.

    Returns:
        Formatted next steps message.
    """
    return f"""
╔══════════════════════════════════════════════════════════════════╗
║                   ragged Installation Complete!                   ║
╚══════════════════════════════════════════════════════════════════╝

Your ragged installation is ready at: {ragged_home}

🚀 QUICK START
──────────────────────────────────────────────────────────────────

1. Start ragged:
   $ ragged serve

2. Open the WebUI:
   http://localhost:5173

3. Add your first document:
   $ ragged add /path/to/document.pdf

4. Ask a question:
   $ ragged query "What is this document about?"

📚 USEFUL COMMANDS
──────────────────────────────────────────────────────────────────

  ragged --help           Show all available commands
  ragged status           Check service status
  ragged add <file>       Add a document
  ragged query "<text>"   Query your documents
  ragged config show      View current configuration

📖 DOCUMENTATION
──────────────────────────────────────────────────────────────────

  Local docs:     {ragged_home}/README.md
  Online docs:    https://ragged.ai/docs
  GitHub:         https://github.com/ragged/ragged

Need help? Open an issue: https://github.com/ragged/ragged/issues

Happy querying! 🎉
"""
