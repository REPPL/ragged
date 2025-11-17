"""Gradio UI components for ragged.

This module provides a modular Gradio web interface for the ragged RAG system.
"""

from src.web.gradio.launcher import launch
from src.web.gradio.ui import create_ui

__all__ = ["launch", "create_ui"]
