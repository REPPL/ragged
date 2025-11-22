"""
LLM integration and response generation.

Provides Ollama client for LLM generation, prompt templates,
and response parsing with citation extraction.
"""

from src.generation.ollama_client import OllamaClient
from src.generation.prompts import RAG_SYSTEM_PROMPT, build_few_shot_prompt, build_rag_prompt
from src.generation.response_parser import (
    GeneratedResponse,
    format_response_for_cli,
    parse_response,
)

__all__ = [
    "OllamaClient",
    "RAG_SYSTEM_PROMPT",
    "build_rag_prompt",
    "build_few_shot_prompt",
    "GeneratedResponse",
    "parse_response",
    "format_response_for_cli",
]
