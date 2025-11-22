"""
Semantic chunking using sentence embeddings and similarity.

Splits documents based on topic/semantic similarity rather than fixed character counts.
Identifies topic boundaries by detecting drops in cosine similarity between consecutive
sentences.
"""

import re

import numpy as np

from src.config.settings import get_settings
from src.utils.logging import get_logger

logger = get_logger(__name__)


class SemanticChunker:
    """
    Chunker that splits text based on semantic topic boundaries.

    Uses sentence embeddings to identify when topics change, creating chunks
    that contain complete, coherent thoughts rather than arbitrary character splits.
    """

    def __init__(
        self,
        similarity_threshold: float = 0.75,
        min_chunk_size: int = 200,
        max_chunk_size: int = 1500,
        min_sentences_per_chunk: int = 2,
    ):
        """
        Initialise semantic chunker.

        Args:
            similarity_threshold: Minimum similarity to keep sentences together (0-1)
                                Lower = more chunks (stricter boundaries)
                                Higher = fewer chunks (looser boundaries)
            min_chunk_size: Minimum characters per chunk
            max_chunk_size: Maximum characters per chunk
            min_sentences_per_chunk: Minimum sentences per chunk
        """
        self.similarity_threshold = similarity_threshold
        self.min_chunk_size = min_chunk_size
        self.max_chunk_size = max_chunk_size
        self.min_sentences_per_chunk = min_sentences_per_chunk
        self._model = None  # Lazy load

        # Get chunk_overlap from settings for compatibility
        settings = get_settings()
        self.chunk_overlap = settings.chunk_overlap

        logger.info(
            f"SemanticChunker initialised with threshold={similarity_threshold:.2f}"
        )

    def _load_model(self):
        """Lazy load sentence embedding model."""
        if self._model is not None:
            return

        try:
            from sentence_transformers import SentenceTransformer

            logger.info("Loading sentence embedding model for semantic chunking")
            # Use same lightweight model as compression
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

    def split_text(self, text: str) -> list[str]:
        """
        Split text into semantic chunks.

        Args:
            text: Text to split

        Returns:
            List of text chunks

        Example:
            >>> chunker = SemanticChunker()
            >>> chunks = chunker.split_text(document_text)
            >>> print(f"Created {len(chunks)} semantic chunks")
        """
        if not text or len(text.strip()) == 0:
            return []

        # Ensure model is loaded
        self._load_model()

        if self._model is None:
            logger.warning("Sentence model not available, using simple splitting")
            return self._fallback_split(text)

        try:
            # Split into sentences
            sentences = self._split_sentences(text)

            if len(sentences) == 0:
                return []
            if len(sentences) == 1:
                return [text]

            # Embed all sentences
            embeddings = self._model.encode(sentences, show_progress_bar=False)

            # Calculate similarity between consecutive sentences
            similarities = self._calculate_similarities(embeddings)

            # Identify topic boundaries (low similarity points)
            boundaries = self._identify_boundaries(similarities)

            # Group sentences into chunks based on boundaries
            chunks = self._create_chunks(sentences, boundaries)

            # Validate and adjust chunk sizes
            chunks = self._validate_chunks(chunks)

            logger.info(
                f"Created {len(chunks)} semantic chunks from {len(sentences)} sentences"
            )

            return chunks

        except Exception as e:
            logger.error(f"Semantic chunking failed: {e}", exc_info=True)
            return self._fallback_split(text)

    def _split_sentences(self, text: str) -> list[str]:
        """
        Split text into sentences.

        Args:
            text: Text to split

        Returns:
            List of sentences
        """
        # Simple sentence splitting - same approach as compression module
        # Split on . ! ? followed by space or end
        sentences = re.split(r'(?<=[.!?])\s+', text)
        # Remove empty sentences
        sentences = [s.strip() for s in sentences if s.strip()]
        return sentences

    def _calculate_similarities(self, embeddings: np.ndarray) -> list[float]:
        """
        Calculate cosine similarity between consecutive sentence embeddings.

        Args:
            embeddings: Array of sentence embeddings

        Returns:
            List of similarity scores (one less than number of sentences)
        """
        similarities = []

        for i in range(len(embeddings) - 1):
            # Cosine similarity between consecutive sentences
            similarity = np.dot(embeddings[i], embeddings[i + 1]) / (
                np.linalg.norm(embeddings[i]) * np.linalg.norm(embeddings[i + 1])
            )
            similarities.append(float(similarity))

        return similarities

    def _identify_boundaries(self, similarities: list[float]) -> list[int]:
        """
        Identify topic boundaries based on similarity drops.

        Args:
            similarities: List of consecutive sentence similarities

        Returns:
            List of boundary indices (where to split)
        """
        boundaries = [0]  # Always start at 0

        for i, similarity in enumerate(similarities):
            # Low similarity = topic change = boundary
            if similarity < self.similarity_threshold:
                boundaries.append(i + 1)  # Split after sentence i

        return boundaries

    def _create_chunks(self, sentences: list[str], boundaries: list[int]) -> list[str]:
        """
        Create chunks from sentences and boundaries.

        Args:
            sentences: List of sentences
            boundaries: List of boundary indices

        Returns:
            List of text chunks
        """
        chunks = []

        for i in range(len(boundaries)):
            start = boundaries[i]
            end = boundaries[i + 1] if i + 1 < len(boundaries) else len(sentences)

            # Get sentences for this chunk
            chunk_sentences = sentences[start:end]

            if len(chunk_sentences) >= self.min_sentences_per_chunk:
                chunk_text = " ".join(chunk_sentences)
                chunks.append(chunk_text)
            elif chunks:
                # Merge small chunks with previous chunk
                chunks[-1] = chunks[-1] + " " + " ".join(chunk_sentences)
            else:
                # First chunk, keep even if small
                chunk_text = " ".join(chunk_sentences)
                chunks.append(chunk_text)

        return chunks

    def _validate_chunks(self, chunks: list[str]) -> list[str]:
        """
        Validate chunk sizes and split/merge as needed.

        Args:
            chunks: List of chunks

        Returns:
            List of validated chunks
        """
        validated = []

        for chunk in chunks:
            chunk_len = len(chunk)

            # Chunk too large - split it
            if chunk_len > self.max_chunk_size:
                # Split into smaller pieces (using character count)
                sub_chunks = self._split_large_chunk(chunk)
                validated.extend(sub_chunks)

            # Chunk too small - try to merge with previous
            elif chunk_len < self.min_chunk_size and validated:
                # Check if merging with previous would exceed max
                if len(validated[-1]) + chunk_len + 1 <= self.max_chunk_size:
                    validated[-1] = validated[-1] + " " + chunk
                else:
                    # Can't merge, keep as is
                    validated.append(chunk)
            else:
                # Chunk size OK
                validated.append(chunk)

        return validated

    def _split_large_chunk(self, chunk: str) -> list[str]:
        """
        Split a too-large chunk into smaller pieces.

        Args:
            chunk: Large chunk to split

        Returns:
            List of smaller chunks
        """
        # Simple character-based split for large chunks
        sub_chunks = []
        start = 0
        chunk_len = len(chunk)

        while start < chunk_len:
            end = min(start + self.max_chunk_size, chunk_len)

            # Try to find a sentence boundary near the end
            if end < chunk_len:
                # Look for . ! ? near end
                boundary_match = re.search(r'[.!?]\s', chunk[end - 100:end])
                if boundary_match:
                    end = end - 100 + boundary_match.end()

            sub_chunks.append(chunk[start:end].strip())
            start = end

        return sub_chunks

    def _fallback_split(self, text: str) -> list[str]:
        """
        Fallback to simple splitting if semantic chunking fails.

        Args:
            text: Text to split

        Returns:
            List of chunks using simple character-based splitting
        """
        logger.warning("Using fallback chunking")

        # Simple chunking by characters
        chunks = []
        start = 0
        text_len = len(text)

        while start < text_len:
            end = min(start + self.max_chunk_size, text_len)

            # Try to break at sentence boundary
            if end < text_len:
                boundary_match = re.search(r'[.!?]\s', text[end - 100:end])
                if boundary_match:
                    end = end - 100 + boundary_match.end()

            chunks.append(text[start:end].strip())
            start = end

        return chunks
