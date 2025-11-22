"""
Token counting using tiktoken for accurate measurement.
"""

from functools import lru_cache
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    import tiktoken as tiktoken_module
else:
    try:
        import tiktoken as tiktoken_module
    except ImportError:
        tiktoken_module = None  # type: ignore[assignment]


@lru_cache(maxsize=1)
def get_tokenizer(model: str = "cl100k_base") -> Any:
    """Get a cached tokenizer instance."""
    if tiktoken_module is None:
        raise ImportError("tiktoken required: pip install tiktoken")
    return tiktoken_module.get_encoding(model)


def count_tokens(text: str, model: str = "cl100k_base") -> int:
    """Count the number of tokens in a text string."""
    if not text:
        return 0
    tokenizer = get_tokenizer(model)
    tokens = tokenizer.encode(text)
    return len(tokens)


def estimate_tokens(text: str) -> int:
    """Estimate token count without full tokenization (faster, less accurate)."""
    if not text:
        return 0
    # Rough approximation: ~4 characters per token
    char_estimate = len(text) / 4
    word_estimate = len(text.split()) / 1.3
    return int((char_estimate + word_estimate) / 2)


def split_by_tokens(
    text: str,
    max_tokens: int,
    model: str = "cl100k_base",
    overlap_tokens: int = 0,
) -> list[str]:
    """Split text into chunks by token count."""
    if not text:
        return []

    tokenizer = get_tokenizer(model)
    tokens = tokenizer.encode(text)

    chunks = []
    start = 0

    while start < len(tokens):
        # Get chunk of max_tokens
        end = start + max_tokens
        chunk_tokens = tokens[start:end]

        # Decode back to text
        chunk_text = tokenizer.decode(chunk_tokens)
        chunks.append(chunk_text)

        # Move start forward, accounting for overlap
        start = end - overlap_tokens
        if start <= 0:
            start = end

    return chunks


def tokens_to_chars(num_tokens: int) -> int:
    """Estimate character count from token count."""
    return num_tokens * 4  # ~4 chars per token
