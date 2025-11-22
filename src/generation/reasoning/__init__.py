"""
Chain-of-thought reasoning for transparent AI responses.

v0.3.7b: Provides multiple levels of reasoning transparency.
"""

from src.generation.reasoning.types import (
    ReasoningMode,
    ReasoningStep,
    ValidationFlag,
    ReasonedResponse,
)
from src.generation.reasoning.generator import ReasoningGenerator
from src.generation.reasoning.parser import ReasoningParser
from src.generation.reasoning.prompts import build_reasoning_prompt

__all__ = [
    # Core types
    "ReasoningMode",
    "ReasoningStep",
    "ValidationFlag",
    "ReasonedResponse",
    # Main classes
    "ReasoningGenerator",
    "ReasoningParser",
    # Utilities
    "build_reasoning_prompt",
]
