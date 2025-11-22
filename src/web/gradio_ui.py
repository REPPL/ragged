"""Gradio web UI for ragged v0.2.

Privacy-first local RAG system with streaming responses and document upload.

This module maintains backwards compatibility by importing from the refactored
gradio submodule. All functionality has been split into logical modules:
- gradio/api.py: API communication
- gradio/query.py: Query functions
- gradio/upload.py: Document upload
- gradio/ui.py: UI creation
- gradio/launcher.py: Launch logic
"""

# Import all public functions for backwards compatibility
from src.web.gradio.api import (
    API_BASE_URL,
    API_COLLECTIONS,
    API_HEALTH,
    API_QUERY,
    API_UPLOAD,
    check_api_health,
    get_api_status_display,
    get_collections,
)
from src.web.gradio.launcher import launch
from src.web.gradio.query import (
    format_sources,
    query_non_streaming,
    query_with_streaming,
)
from src.web.gradio.ui import create_ui
from src.web.gradio.upload import upload_document

__all__ = [
    # API
    "API_BASE_URL",
    "API_HEALTH",
    "API_QUERY",
    "API_UPLOAD",
    "API_COLLECTIONS",
    "check_api_health",
    "get_api_status_display",
    "get_collections",
    # Query
    "format_sources",
    "query_with_streaming",
    "query_non_streaming",
    # Upload
    "upload_document",
    # UI
    "create_ui",
    # Launcher
    "launch",
]

# Maintain __main__ compatibility
if __name__ == "__main__":
    launch()
