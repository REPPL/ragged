"""
Contextual compression for retrieved chunks.

Extracts only relevant sentences from chunks, reducing noise and improving
context quality for LLM generation.
"""

import re
from dataclasses import dataclass

import numpy as np

from src.utils.logging import get_logger

logger = get_logger(__name__)

# Type hint for RetrievedChunk
try:
    from src.retrieval.retriever import RetrievedChunk
except ImportError:
    RetrievedChunk = any  # type: ignore


@dataclass
class CompressionResult:
    """Result of compression operation."""

    original_length: int  # Total characters before compression
    compressed_length: int  # Total characters after compression
    compression_ratio: float  # compressed / original
    chunks_processed: int
    sentences_extracted: int

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"CompressionResult(ratio={self.compression_ratio:.2f}, "
            f"{self.original_length}→{self.compressed_length} chars)"
        )


class ContextualCompressor:
    """
    Compresses retrieved chunks by extracting relevant sentences.

    Reduces noise and token usage by keeping only sentences relevant to the query,
    while preserving surrounding context for coherence.
    """

    def __init__(
        self,
        target_compression_ratio: float = 0.5,
        min_sentence_score: float = 0.3,
        context_sentences: int = 1,
    ):
        """
        Initialise contextual compressor.

        Args:
            target_compression_ratio: Target ratio of output/input (0-1)
            min_sentence_score: Minimum relevance score to include sentence
            context_sentences: Number of surrounding sentences to include for coherence
        """
        self.target_compression_ratio = target_compression_ratio
        self.min_sentence_score = min_sentence_score
        self.context_sentences = context_sentences
        self._model = None  # Lazy load sentence embedder

        logger.info(
            f"ContextualCompressor initialised with target_ratio={target_compression_ratio:.2f}"
        )

    def _load_model(self):
        """Lazy load sentence embedding model for relevance scoring."""
        if self._model is not None:
            return

        try:
            from sentence_transformers import SentenceTransformer

            logger.info("Loading sentence embedding model for compression")
            # Use a lightweight model for sentence embeddings
            self._model = SentenceTransformer('all-MiniLM-L6-v2')
            logger.info("Sentence embedding model loaded")

        except ImportError:
            logger.error(
                "sentence-transformers not installed. Install with: pip install sentence-transformers"
            )
            raise
        except Exception as e:
            logger.error(f"Failed to load sentence model: {e}", exc_info=True)
            raise

    def compress(
        self,
        query: str,
        chunks: list[RetrievedChunk],
    ) -> tuple[list[RetrievedChunk], CompressionResult]:
        """
        Compress chunks by extracting relevant sentences.

        Args:
            query: Original query
            chunks: List of chunks to compress

        Returns:
            Tuple of (compressed_chunks, compression_result)

        Example:
            >>> compressor = ContextualCompressor()
            >>> compressed, result = compressor.compress("What is ML?", chunks)
            >>> print(f"Compressed by {result.compression_ratio:.0%}")
        """
        if not chunks:
            return [], CompressionResult(
                original_length=0,
                compressed_length=0,
                compression_ratio=1.0,
                chunks_processed=0,
                sentences_extracted=0,
            )

        # Ensure model is loaded
        self._load_model()

        if self._model is None:
            logger.error("Sentence model not available, returning original chunks")
            return chunks, CompressionResult(
                original_length=sum(len(c.text) for c in chunks),
                compressed_length=sum(len(c.text) for c in chunks),
                compression_ratio=1.0,
                chunks_processed=len(chunks),
                sentences_extracted=0,
            )

        original_length = sum(len(chunk.text) for chunk in chunks)
        compressed_chunks = []
        total_sentences = 0

        try:
            # Embed query once
            query_embedding = self._model.encode([query])[0]

            for chunk in chunks:
                # Split into sentences
                sentences = self._split_sentences(chunk.text)

                if not sentences:
                    continue

                # Score sentences
                sentence_scores = self._score_sentences(query_embedding, sentences)

                # Select relevant sentences
                selected_indices = self._select_sentences(
                    sentence_scores,
                    target_ratio=self.target_compression_ratio,
                )

                # Add context sentences for coherence
                selected_indices = self._add_context(selected_indices, len(sentences))

                # Reconstruct compressed text
                compressed_text = self._reconstruct_text(sentences, selected_indices)

                if compressed_text:
                    # Create new chunk with compressed text
                    compressed_chunk = RetrievedChunk(
                        text=compressed_text,
                        score=chunk.score,
                        chunk_id=chunk.chunk_id,
                        document_id=chunk.document_id,
                        document_path=chunk.document_path,
                        chunk_position=chunk.chunk_position,
                        metadata=chunk.metadata,
                    )
                    compressed_chunks.append(compressed_chunk)
                    total_sentences += len(selected_indices)

            compressed_length = sum(len(c.text) for c in compressed_chunks)
            compression_ratio = compressed_length / original_length if original_length > 0 else 1.0

            result = CompressionResult(
                original_length=original_length,
                compressed_length=compressed_length,
                compression_ratio=compression_ratio,
                chunks_processed=len(chunks),
                sentences_extracted=total_sentences,
            )

            logger.info(
                f"Compressed {len(chunks)} chunks: {original_length}→{compressed_length} chars "
                f"(ratio={compression_ratio:.2f})"
            )

            return compressed_chunks, result

        except Exception as e:
            logger.error(f"Compression failed: {e}", exc_info=True)
            # Fallback to original chunks
            return chunks, CompressionResult(
                original_length=original_length,
                compressed_length=original_length,
                compression_ratio=1.0,
                chunks_processed=len(chunks),
                sentences_extracted=0,
            )

    def _split_sentences(self, text: str) -> list[str]:
        """
        Split text into sentences.

        Args:
            text: Text to split

        Returns:
            List of sentences
        """
        # Simple sentence splitting (could be enhanced with NLTK)
        # Split on . ! ? followed by space or end
        sentences = re.split(r'(?<=[.!?])\s+', text)
        # Remove empty sentences
        sentences = [s.strip() for s in sentences if s.strip()]
        return sentences

    def _score_sentences(
        self,
        query_embedding: np.ndarray,
        sentences: list[str],
    ) -> np.ndarray:
        """
        Score sentences by relevance to query.

        Args:
            query_embedding: Query embedding vector
            sentences: List of sentences

        Returns:
            Array of relevance scores (0-1)
        """
        if not sentences:
            return np.array([])

        # Embed sentences
        sentence_embeddings = self._model.encode(sentences)

        # Compute cosine similarity with query
        scores = np.dot(sentence_embeddings, query_embedding) / (
            np.linalg.norm(sentence_embeddings, axis=1) * np.linalg.norm(query_embedding)
        )

        # Normalize to 0-1
        scores = (scores + 1) / 2

        return scores

    def _select_sentences(
        self,
        scores: np.ndarray,
        target_ratio: float,
    ) -> list[int]:
        """
        Select most relevant sentences.

        Args:
            scores: Sentence relevance scores
            target_ratio: Target proportion of sentences to keep

        Returns:
            List of selected sentence indices
        """
        if len(scores) == 0:
            return []

        # How many sentences to keep
        num_to_keep = max(1, int(len(scores) * target_ratio))

        # Select top-scoring sentences above threshold
        above_threshold = np.where(scores >= self.min_sentence_score)[0]

        if len(above_threshold) == 0:
            # If no sentences above threshold, take top 1
            selected = [int(np.argmax(scores))]
        else:
            # Take top num_to_keep from those above threshold
            sorted_indices = above_threshold[np.argsort(-scores[above_threshold])]
            selected = sorted_indices[:num_to_keep].tolist()

        # Sort to maintain original order
        selected.sort()

        return selected

    def _add_context(
        self,
        selected_indices: list[int],
        total_sentences: int,
    ) -> list[int]:
        """
        Add surrounding sentences for coherence.

        Args:
            selected_indices: Currently selected sentence indices
            total_sentences: Total number of sentences

        Returns:
            Expanded list of indices including context
        """
        if not selected_indices:
            return []

        expanded = set(selected_indices)

        for idx in selected_indices:
            # Add context_sentences before and after
            for offset in range(-self.context_sentences, self.context_sentences + 1):
                context_idx = idx + offset
                if 0 <= context_idx < total_sentences:
                    expanded.add(context_idx)

        # Return sorted
        return sorted(expanded)

    def _reconstruct_text(
        self,
        sentences: list[str],
        selected_indices: list[int],
    ) -> str:
        """
        Reconstruct text from selected sentences.

        Args:
            sentences: All sentences
            selected_indices: Indices of selected sentences

        Returns:
            Reconstructed text
        """
        if not selected_indices:
            return ""

        selected_sentences = [sentences[i] for i in selected_indices if i < len(sentences)]

        # Join with spaces
        return " ".join(selected_sentences)
