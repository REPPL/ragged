"""Gradio web UI for ragged v0.2.

Privacy-first local RAG system with streaming responses and document upload.
"""

import gradio as gr
import requests
import json
import os
from typing import Generator, List, Tuple
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

# API configuration
API_BASE_URL = os.getenv("RAGGED_API_URL", "http://localhost:8000")
API_HEALTH = f"{API_BASE_URL}/api/health"
API_QUERY = f"{API_BASE_URL}/api/query"
API_UPLOAD = f"{API_BASE_URL}/api/upload"
API_COLLECTIONS = f"{API_BASE_URL}/api/collections"


def check_api_health(max_retries: int = 10, retry_delay: float = 2.0) -> dict:
    """Check if API is healthy with retry logic.

    Args:
        max_retries: Maximum number of retry attempts (default: 10)
        retry_delay: Delay in seconds between retries (default: 2.0)

    Returns:
        API health status dict
    """
    import time

    for attempt in range(max_retries):
        try:
            response = requests.get(API_HEALTH, timeout=5)
            response.raise_for_status()
            health_data = response.json()
            logger.info(f"API health check successful on attempt {attempt + 1}")
            return health_data
        except Exception as e:
            if attempt < max_retries - 1:
                logger.warning(f"API health check failed (attempt {attempt + 1}/{max_retries}): {e}. Retrying in {retry_delay}s...")
                time.sleep(retry_delay)
            else:
                logger.error(f"API health check failed after {max_retries} attempts: {e}")
                return {"status": "unhealthy", "error": str(e)}

    return {"status": "unhealthy", "error": "Max retries exceeded"}


def get_api_status_display() -> str:
    """Get formatted API status for display.

    Returns:
        Formatted markdown string with API status
    """
    health = check_api_health(max_retries=1, retry_delay=0.5)
    status = health.get("status", "unknown")

    if status == "healthy" or status == "degraded":
        return "**API Status**: ✅ Connected"
    else:
        error = health.get("error", "Unknown error")
        return f"**API Status**: ❌ Unavailable ({error[:50]}...)"


def query_with_streaming(
    message: str,
    history: List[Tuple[str, str]],
    collection: str = "default",
    retrieval_method: str = "hybrid",
    top_k: int = 5,
) -> Generator[Tuple[List[Tuple[str, str]], str], None, None]:
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
            timeout=60
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
    history: List[Tuple[str, str]],
    collection: str = "default",
    retrieval_method: str = "hybrid",
    top_k: int = 5,
) -> Tuple[List[Tuple[str, str]], str]:
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
            timeout=60
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

    except Exception as e:
        error_msg = f"❌ Error: {str(e)}"
        history.append((message, error_msg))
        return history, ""


def format_sources(sources: List[dict]) -> str:
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


def upload_document(file) -> str:
    """Upload a document to the API.

    Args:
        file: Gradio file upload object

    Returns:
        Status message
    """
    if file is None:
        return "❌ No file selected"

    try:
        # Read file
        file_path = Path(file.name)

        with open(file_path, 'rb') as f:
            files = {'file': (file_path.name, f, 'application/octet-stream')}
            response = requests.post(API_UPLOAD, files=files, timeout=60)
            response.raise_for_status()

        data = response.json()
        status = data.get("status", "unknown")
        message = data.get("message", "")

        if status == "success":
            return f"✅ {message}"
        else:
            return f"⚠️ {message}"

    except Exception as e:
        return f"❌ Upload failed: {str(e)}"


def get_collections() -> List[str]:
    """Get list of available collections.

    Returns:
        List of collection names
    """
    try:
        response = requests.get(API_COLLECTIONS, timeout=5)
        response.raise_for_status()
        data = response.json()
        return data.get("collections", ["default"])
    except Exception:
        return ["default"]


def create_ui() -> gr.Blocks:
    """Create Gradio UI.

    Returns:
        Gradio Blocks app
    """
    # Check API health on startup (with retries)
    health = check_api_health(max_retries=10, retry_delay=2.0)
    api_status = health.get("status", "unknown")
    initial_status = "✅ Connected" if api_status in ["healthy", "degraded"] else "❌ Unavailable"

    with gr.Blocks(
        title="ragged - Privacy-First RAG",
        theme=gr.themes.Soft(primary_hue="indigo")
    ) as app:
        gr.Markdown(
            """
            # 🔍 ragged - Privacy-First Local RAG

            Ask questions about your documents using hybrid retrieval (vector + keyword search).
            """
        )

        # API Status indicator with refresh button
        with gr.Row():
            api_status_display = gr.Markdown(
                f"**API Status**: {initial_status}"
            )
            refresh_btn = gr.Button("🔄 Refresh Status", scale=0, size="sm")

        with gr.Row():
            # Left column: Chat
            with gr.Column(scale=2):
                chatbot = gr.Chatbot(
                    label="Chat",
                    height=500,
                    show_copy_button=True
                )

                with gr.Row():
                    msg = gr.Textbox(
                        label="Your Question",
                        placeholder="Ask a question about your documents...",
                        scale=4
                    )
                    submit_btn = gr.Button("Send", variant="primary", scale=1)

                with gr.Row():
                    clear_btn = gr.Button("Clear Chat")

            # Right column: Settings & Upload
            with gr.Column(scale=1):
                gr.Markdown("### ⚙️ Settings")

                collection = gr.Dropdown(
                    choices=get_collections(),
                    value="default",
                    label="Collection",
                    interactive=True
                )

                retrieval_method = gr.Radio(
                    choices=["hybrid", "vector", "bm25"],
                    value="hybrid",
                    label="Retrieval Method",
                    info="Hybrid combines vector and keyword search"
                )

                top_k = gr.Slider(
                    minimum=1,
                    maximum=20,
                    value=5,
                    step=1,
                    label="Number of Sources",
                    info="How many document chunks to retrieve"
                )

                streaming = gr.Checkbox(
                    value=True,
                    label="Enable Streaming",
                    info="Stream responses token-by-token"
                )

                gr.Markdown("### 📤 Upload Document")

                file_upload = gr.File(
                    label="Upload PDF, TXT, MD, or HTML",
                    file_types=[".pdf", ".txt", ".md", ".html"]
                )

                upload_btn = gr.Button("Upload", variant="secondary")
                upload_status = gr.Textbox(
                    label="Upload Status",
                    interactive=False
                )

        # Sources display (below chat)
        with gr.Row():
            sources_display = gr.Markdown(label="Sources", value="")

        # Event handlers
        def respond(message, history, collection, method, k, stream):
            """Handle query submission."""
            if stream:
                # Use streaming generator
                return query_with_streaming(message, history, collection, method, k)
            else:
                # Use non-streaming
                return query_non_streaming(message, history, collection, method, k)

        # Submit message (Enter or click)
        submit_event = msg.submit(
            respond,
            inputs=[msg, chatbot, collection, retrieval_method, top_k, streaming],
            outputs=[chatbot, sources_display]
        )
        submit_event.then(lambda: "", outputs=[msg])  # Clear input

        submit_btn.click(
            respond,
            inputs=[msg, chatbot, collection, retrieval_method, top_k, streaming],
            outputs=[chatbot, sources_display]
        ).then(lambda: "", outputs=[msg])

        # Clear chat
        clear_btn.click(
            lambda: ([], ""),
            outputs=[chatbot, sources_display]
        )

        # Refresh API status
        refresh_btn.click(
            get_api_status_display,
            outputs=[api_status_display]
        )

        # Upload document
        upload_btn.click(
            upload_document,
            inputs=[file_upload],
            outputs=[upload_status]
        )

    return app


def launch(
    server_name: str = "0.0.0.0",
    server_port: int = 7860,
    share: bool = False
):
    """Launch Gradio UI.

    Args:
        server_name: Host to bind to
        server_port: Port to run on
        share: Whether to create public share link
    """
    app = create_ui()
    app.launch(
        server_name=server_name,
        server_port=server_port,
        share=share
    )


if __name__ == "__main__":
    launch()
