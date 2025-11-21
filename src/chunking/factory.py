"""
Chunker factory for instantiating different chunking strategies.

v0.3.3: Intelligent Chunking integration
"""

from typing import Union

from src.chunking.hierarchical_chunker import HierarchicalChunker
from src.chunking.semantic_chunker import SemanticChunker
from src.chunking.splitters.recursive_splitter import RecursiveCharacterTextSplitter
from src.config.settings import get_settings
from src.utils.logging import get_logger

logger = get_logger(__name__)


# Type alias for all chunker types
Chunker = Union[RecursiveCharacterTextSplitter, SemanticChunker, HierarchicalChunker]


class ChunkerFactory:
    """
    Factory for creating chunker instances based on strategy configuration.

    Supports three chunking strategies:
    - "fixed": Traditional recursive character splitting (default, fast)
    - "semantic": Topic boundary detection using sentence embeddings (higher quality)
    - "hierarchical": Parent-child chunk relationships (context-aware)
    """

    @staticmethod
    def create_chunker(strategy: str | None = None) -> Chunker:
        """
        Create a chunker instance based on the specified strategy.

        Args:
            strategy: Chunking strategy ("fixed", "semantic", or "hierarchical")
                     If None, uses settings.chunking_strategy

        Returns:
            Chunker instance configured with settings parameters

        Raises:
            ValueError: If strategy is not recognised

        Example:
            >>> factory = ChunkerFactory()
            >>> chunker = factory.create_chunker("semantic")
            >>> chunks = chunker.split_text(document_text)
        """
        settings = get_settings()

        # Use provided strategy or fall back to settings
        if strategy is None:
            strategy = settings.chunking_strategy

        logger.info(f"Creating chunker with strategy: {strategy}")

        if strategy == "fixed":
            return ChunkerFactory._create_fixed_chunker()
        elif strategy == "semantic":
            return ChunkerFactory._create_semantic_chunker()
        elif strategy == "hierarchical":
            return ChunkerFactory._create_hierarchical_chunker()
        else:
            raise ValueError(
                f"Unknown chunking strategy: '{strategy}'. "
                f"Valid strategies: fixed, semantic, hierarchical"
            )

    @staticmethod
    def _create_fixed_chunker() -> RecursiveCharacterTextSplitter:
        """Create fixed-size recursive character splitter."""
        settings = get_settings()

        return RecursiveCharacterTextSplitter(
            chunk_size=settings.chunk_size,
            chunk_overlap=settings.chunk_overlap,
        )

    @staticmethod
    def _create_semantic_chunker() -> SemanticChunker:
        """Create semantic chunker with sentence embeddings."""
        settings = get_settings()

        return SemanticChunker(
            similarity_threshold=settings.semantic_similarity_threshold,
            min_chunk_size=settings.semantic_min_chunk_size,
            max_chunk_size=settings.semantic_max_chunk_size,
            min_sentences_per_chunk=2,
        )

    @staticmethod
    def _create_hierarchical_chunker() -> HierarchicalChunker:
        """Create hierarchical chunker with parent-child relationships."""
        settings = get_settings()

        return HierarchicalChunker(
            parent_chunk_size=settings.hierarchical_parent_size,
            child_chunk_size=settings.hierarchical_child_size,
            parent_overlap=settings.hierarchical_parent_overlap,
            child_overlap=settings.hierarchical_child_overlap,
        )
