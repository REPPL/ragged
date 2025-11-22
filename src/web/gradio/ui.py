"""Gradio UI creation and layout."""

import json
import logging
from collections.abc import Generator
from typing import cast

import gradio as gr
import requests  # type: ignore[import-untyped]

from src.web.gradio.api import check_api_health, get_api_status_display, get_collections
from src.web.gradio.query import query_non_streaming, query_with_streaming
from src.web.gradio.upload import upload_document

logger = logging.getLogger(__name__)


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
        def respond(
            message: str,
            history: list[tuple[str, str]],
            collection: str,
            method: str,
            k: int,
            stream: bool
        ) -> Generator[tuple[list[tuple[str, str]], str], None, None] | tuple[list[tuple[str, str]], str]:
            """Handle query submission with error handling."""
            try:
                if stream:
                    # Use streaming generator
                    return query_with_streaming(message, history, collection, method, k)
                else:
                    # Use non-streaming
                    return query_non_streaming(message, history, collection, method, k)
            except requests.exceptions.RequestException as e:
                error_msg = f"❌ API Error: {str(e)}"
                logger.error(f"API request failed in respond: {e}", exc_info=True)
                # Append error to history
                if history:
                    history.append((message, error_msg))
                else:
                    history = [(message, error_msg)]
                return history, ""
            except json.JSONDecodeError as e:
                error_msg = f"❌ Stream parsing error: {str(e)}"
                logger.error(f"JSON decode failed in respond: {e}", exc_info=True)
                if history:
                    history.append((message, error_msg))
                else:
                    history = [(message, error_msg)]
                return history, ""
            except Exception as e:
                error_msg = f"❌ Error: {str(e)}"
                logger.error(f"Query failed in respond: {e}", exc_info=True)
                if history:
                    history.append((message, error_msg))
                else:
                    history = [(message, error_msg)]
                return history, ""

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

    return cast(gr.Blocks, app)
