"""Query functionality for Gradio UI."""

import json
import logging
from collections.abc import Generator
from typing import Any

import requests  # type: ignore[import-untyped]

from src.config.constants import LONG_API_TIMEOUT
from src.web.gradio.api import API_QUERY

logger = logging.getLogger(__name__)


def format_sources(sources: list[dict[str, Any]]) -> str:
    """Format sources as markdown.

    Args:
        sources: List of source dictionaries

    Returns:
        Markdown formatted sources
    """
    if not sources:
        return "No sources found."

    md = "## Sources\n\n"

    for i, source in enumerate(sources, 1):
        filename = source.get("filename", "Unknown")
        score = source.get("score", 0.0)
        excerpt = source.get("excerpt", "")
        chunk_index = source.get("chunk_index", 0)

        md += f"### {i}. {filename} (chunk {chunk_index})\n"
        md += f"**Relevance**: {score:.3f}\n\n"
        md += f"> {excerpt}\n\n"
        md += "---\n\n"

    return md


def query_with_streaming(
    message: str,
    history: list[tuple[str, str]],
    collection: str = "default",
    retrieval_method: str = "hybrid",
    top_k: int = 5,
) -> Generator[tuple[list[tuple[str, str]], str], None, None]:
    """Query the API with streaming response.

    Args:
        message: User query
        history: Chat history as list of (user_msg, assistant_msg) tuples
        collection: Collection name
        retrieval_method: Retrieval method (vector, bm25, hybrid)
        top_k: Number of sources to retrieve

    Yields:
        Tuple of (updated_history, sources_markdown)
    """
    if not message.strip():
        yield history, ""
        return

    # Add user message to history
    history.append((message, ""))

    try:
        # Make streaming request
        response = requests.post(
            API_QUERY,
            json={
                "query": message,
                "collection": collection,
                "top_k": top_k,
                "retrieval_method": retrieval_method,
                "stream": True
            },
            stream=True,
            timeout=LONG_API_TIMEOUT
        )
        response.raise_for_status()

        # Process SSE stream
        event_type = None  # Initialize to avoid UnboundLocalError
        answer_tokens = []
        sources = []

        for line in response.iter_lines():
            if not line:
                continue

            line = line.decode('utf-8')

            # Parse SSE format
            if line.startswith('event: '):
                event_type = line[7:].strip()
            elif line.startswith('data: '):
                # Skip data lines if we don't have an event type yet
                if event_type is None:
                    continue

                data = json.loads(line[6:])

                if event_type == 'token':
                    # Append token to answer
                    token = data.get('token', '')
                    answer_tokens.append(token)

                    # Update history with accumulated answer
                    current_answer = ''.join(answer_tokens)
                    history[-1] = (message, current_answer)

                    # Yield updated history
                    yield history, ""

                elif event_type == 'sources':
                    # Store sources
                    sources = data

        # Format sources as markdown
        sources_md = format_sources(sources)

        # Final yield with sources
        yield history, sources_md

    except requests.exceptions.RequestException as e:
        error_msg = f"❌ API Error: {str(e)}"
        logger.error(f"API request failed: {e}", exc_info=True)
        history[-1] = (message, error_msg)
        yield history, ""
    except json.JSONDecodeError as e:
        error_msg = f"❌ Stream parsing error: {str(e)}"
        logger.error(f"JSON decode failed: {e}", exc_info=True)
        history[-1] = (message, error_msg)
        yield history, ""
    except Exception as e:
        error_msg = f"❌ Unexpected error ({type(e).__name__}): {str(e)}"
        logger.error(f"Query failed: {e}", exc_info=True)
        history[-1] = (message, error_msg)
        yield history, ""


def query_non_streaming(
    message: str,
    history: list[tuple[str, str]],
    collection: str = "default",
    retrieval_method: str = "hybrid",
    top_k: int = 5,
) -> tuple[list[tuple[str, str]], str]:
    """Query the API without streaming.

    Args:
        message: User query
        history: Chat history
        collection: Collection name
        retrieval_method: Retrieval method
        top_k: Number of sources

    Returns:
        Tuple of (updated_history, sources_markdown)
    """
    if not message.strip():
        return history, ""

    try:
        response = requests.post(
            API_QUERY,
            json={
                "query": message,
                "collection": collection,
                "top_k": top_k,
                "retrieval_method": retrieval_method,
                "stream": False
            },
            timeout=LONG_API_TIMEOUT
        )
        response.raise_for_status()
        data = response.json()

        # Extract answer and sources
        answer = data.get("answer", "No answer received")
        sources = data.get("sources", [])

        # Update history
        history.append((message, answer))

        # Format sources
        sources_md = format_sources(sources)

        return history, sources_md

    except Exception as e:  # noqa: BLE001 - Show error to user
        error_msg = f"❌ Error: {str(e)}"
        history.append((message, error_msg))
        return history, ""
