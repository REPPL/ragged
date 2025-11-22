"""Recursive character text splitter implementation."""


from src.chunking.token_counter import count_tokens
from src.config.settings import get_settings


class RecursiveCharacterTextSplitter:
    """Recursively split text into chunks, trying different separators."""

    def __init__(
        self,
        chunk_size: int | None = None,
        chunk_overlap: int | None = None,
        separators: list[str] | None = None,
    ):
        """Initialise the text splitter."""
        settings = get_settings()
        self.chunk_size = chunk_size if chunk_size is not None else settings.chunk_size
        self.chunk_overlap = chunk_overlap if chunk_overlap is not None else settings.chunk_overlap

        if self.chunk_overlap >= self.chunk_size:
            raise ValueError(f"chunk_overlap ({self.chunk_overlap}) must be less than chunk_size ({self.chunk_size})")

        self.separators = separators or ["\n\n", "\n", ". ", " ", ""]

    def split_text(self, text: str) -> list[str]:
        """Split text into chunks using recursive splitting."""
        if not text:
            return []

        return self._split_recursive(text, self.separators)

    def _split_recursive(self, text: str, separators: list[str]) -> list[str]:
        """Recursively split text by trying separators in order."""
        if not separators:
            # No more separators, split by character
            return self._split_by_characters(text)

        separator = separators[0]
        remaining_separators = separators[1:]

        # Split by current separator
        if separator:
            splits = text.split(separator)
        else:
            # Empty separator means split by character
            return self._split_by_characters(text)

        # Process splits
        chunks = []
        current_chunk = ""

        for split in splits:
            # Check token count
            test_chunk = current_chunk + (separator if current_chunk else "") + split
            token_count = count_tokens(test_chunk)

            if token_count <= self.chunk_size:
                current_chunk = test_chunk
            else:
                # Current chunk is ready
                if current_chunk:
                    chunks.append(current_chunk)

                # Check if split itself is too large
                if count_tokens(split) > self.chunk_size:
                    # Recursively split this piece
                    sub_chunks = self._split_recursive(split, remaining_separators)
                    chunks.extend(sub_chunks)
                    current_chunk = ""
                else:
                    current_chunk = split

        # Add remaining
        if current_chunk:
            chunks.append(current_chunk)

        # Add overlap
        return self._add_overlap(chunks)

    def _split_by_characters(self, text: str) -> list[str]:
        """Split text by character count."""
        chunks = []
        start = 0
        text_length = len(text)

        while start < text_length:
            # Estimate character count for chunk_size tokens
            char_estimate = self.chunk_size * 4  # ~4 chars per token

            end = min(start + char_estimate, text_length)
            chunk = text[start:end]

            # Adjust if we exceeded token limit
            while count_tokens(chunk) > self.chunk_size and len(chunk) > 1:
                end = start + int(len(chunk) * 0.9)
                chunk = text[start:end]

            chunks.append(chunk)
            start = end

        return self._add_overlap(chunks)

    def _add_overlap(self, chunks: list[str]) -> list[str]:
        """Add overlap between chunks."""
        if len(chunks) <= 1 or self.chunk_overlap == 0:
            return chunks

        overlapped = [chunks[0]]

        for i in range(1, len(chunks)):
            prev_chunk = chunks[i - 1]
            curr_chunk = chunks[i]

            # Get overlap from previous chunk
            overlap_chars = self.chunk_overlap * 4  # Rough estimate
            overlap_text = prev_chunk[-overlap_chars:] if len(prev_chunk) > overlap_chars else prev_chunk

            # Prepend overlap to current chunk
            overlapped_chunk = overlap_text + " " + curr_chunk
            overlapped.append(overlapped_chunk)

        return overlapped
