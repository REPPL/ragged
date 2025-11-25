"""Plugin interfaces for ragged extensibility.

Defines the core plugin types that can be implemented to extend ragged's
functionality: Embedder, Retriever, Processor, and Command plugins.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any


@dataclass
class PluginMetadata:
    """Metadata for a plugin."""

    name: str
    version: str
    author: str
    description: str
    plugin_type: str  # "embedder", "retriever", "processor", "command"
    entry_point: str  # e.g., "my_plugin.embedder:CustomEmbedder"
    dependencies: list[str] = None
    config_schema: dict[str, Any] | None = None

    def __post_init__(self):
        """Initialise default dependencies."""
        if self.dependencies is None:
            self.dependencies = []


class Plugin(ABC):
    """Base class for all plugins."""

    def __init__(self, config: dict[str, Any] | None = None):
        """Initialise plugin with optional configuration.

        Args:
            config: Plugin-specific configuration
        """
        self.config = config or {}
        self._metadata: PluginMetadata | None = None

    @abstractmethod
    def get_metadata(self) -> PluginMetadata:
        """Get plugin metadata.

        Returns:
            PluginMetadata instance
        """
        pass

    @abstractmethod
    def initialize(self) -> None:
        """Initialise the plugin.

        Called once after the plugin is loaded and before first use.
        Can be used for setup like loading models, establishing connections, etc.
        """
        pass

    @abstractmethod
    def shutdown(self) -> None:
        """Shutdown the plugin.

        Called when the plugin is being unloaded.
        Should clean up resources like model memory, connections, etc.
        """
        pass


class EmbedderPlugin(Plugin):
    """Plugin for custom embedding models."""

    @abstractmethod
    def embed_text(self, text: str) -> list[float]:
        """Generate embedding for text.

        Args:
            text: Text to embed

        Returns:
            Embedding vector as list of floats
        """
        pass

    @abstractmethod
    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for batch of texts.

        Args:
            texts: List of texts to embed

        Returns:
            List of embedding vectors
        """
        pass

    @abstractmethod
    def get_dimension(self) -> int:
        """Get the dimensionality of embeddings.

        Returns:
            Embedding dimension
        """
        pass


class RetrieverPlugin(Plugin):
    """Plugin for custom retrieval strategies."""

    @abstractmethod
    def retrieve(
        self,
        query: str,
        n_results: int = 10,
        filters: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        """Retrieve documents for a query.

        Args:
            query: Query text
            n_results: Number of results to return
            filters: Optional metadata filters

        Returns:
            List of documents with metadata and scores
        """
        pass

    @abstractmethod
    def rerank(
        self,
        query: str,
        documents: list[dict[str, Any]],
        n_results: int = 10,
    ) -> list[dict[str, Any]]:
        """Rerank retrieved documents.

        Args:
            query: Original query
            documents: Documents to rerank
            n_results: Number of results to return

        Returns:
            Reranked list of documents
        """
        pass


class ProcessorPlugin(Plugin):
    """Plugin for custom document processors."""

    @abstractmethod
    def process(self, document: dict[str, Any]) -> dict[str, Any]:
        """Process a document.

        Args:
            document: Document to process with 'content' and 'metadata' keys

        Returns:
            Processed document
        """
        pass

    @abstractmethod
    def process_batch(self, documents: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Process a batch of documents.

        Args:
            documents: List of documents to process

        Returns:
            List of processed documents
        """
        pass

    @abstractmethod
    def supports_file_type(self, file_type: str) -> bool:
        """Check if this processor supports a file type.

        Args:
            file_type: File extension (e.g., "pdf", "docx")

        Returns:
            True if supported, False otherwise
        """
        pass


class CommandPlugin(Plugin):
    """Plugin for custom CLI commands."""

    @abstractmethod
    def get_command_name(self) -> str:
        """Get the command name.

        Returns:
            Command name (e.g., "export", "analyze")
        """
        pass

    @abstractmethod
    def get_command_help(self) -> str:
        """Get help text for the command.

        Returns:
            Help text describing the command
        """
        pass

    @abstractmethod
    def execute(self, args: list[str], context: dict[str, Any]) -> int:
        """Execute the command.

        Args:
            args: Command arguments
            context: Execution context (config, paths, etc.)

        Returns:
            Exit code (0 for success, non-zero for failure)
        """
        pass


# Plugin type registry
PLUGIN_TYPES = {
    "embedder": EmbedderPlugin,
    "retriever": RetrieverPlugin,
    "processor": ProcessorPlugin,
    "command": CommandPlugin,
}
