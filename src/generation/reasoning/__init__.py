"""
Chain-of-thought reasoning for transparent AI responses.

v0.3.7b: Provides multiple levels of reasoning transparency.
"""

from ragged.generation.reasoning.generator import ReasoningGenerator
from ragged.generation.reasoning.parser import ReasoningParser
from ragged.generation.reasoning.prompts import build_reasoning_prompt
from ragged.generation.reasoning.types import (
    ReasonedResponse,
    ReasoningMode,
    ReasoningStep,
    ValidationFlag,
)

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
