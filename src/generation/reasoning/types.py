"""
Data types for chain-of-thought reasoning.

v0.3.7b: Transparent reasoning process with validation.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional, Dict, Any


class ReasoningMode(Enum):
    """Reasoning depth levels.

    Controls the level of reasoning transparency shown to users.
    Higher modes provide more detail but increase latency and token usage.
    """
    NONE = "none"           # No reasoning (fastest, production default)
    BASIC = "basic"         # Simple step-by-step (good for most users)
    STRUCTURED = "structured"  # Detailed with validation (important queries)
    CHAIN = "chain"         # Full chain-of-thought (critical decisions)


@dataclass
class ReasoningStep:
    """Individual reasoning step in the thought process.

    Represents one discrete step in the LLM's reasoning, with metadata
    about confidence, evidence used, and the type of reasoning performed.

    Attributes:
        step_number: Sequential step number (1, 2, 3, ...)
        thought: The actual reasoning content
        action: Type of reasoning action performed
        confidence: Confidence in this step (0.0-1.0)
        evidence: Citation indices that support this step
    """
    step_number: int
    thought: str
    action: str  # "understand", "retrieve", "analyze", "synthesize", "conclude"
    confidence: float = 1.0  # 0.0-1.0
    evidence: List[int] = field(default_factory=list)  # Citation indices


@dataclass
class ValidationFlag:
    """Reasoning validation issue detected by automatic validation.

    Represents potential problems in the reasoning process, such as
    contradictions, unsupported claims, or uncertainty markers.

    Attributes:
        type: Category of issue (contradiction, uncertainty, assumption)
        description: Human-readable explanation of the issue
        severity: Impact level (low, medium, high)
        step_numbers: Which reasoning steps are affected
    """
    type: str  # "contradiction", "uncertainty", "assumption", "low_confidence"
    description: str
    severity: str  # "low", "medium", "high"
    step_numbers: List[int] = field(default_factory=list)


@dataclass
class ReasonedResponse:
    """Complete response with reasoning trace and validation.

    Contains both the final answer and the complete reasoning process
    that led to it, along with validation flags and confidence scores.

    Attributes:
        answer: The final answer text
        citations: List of citation strings
        reasoning_steps: Step-by-step reasoning trace
        validation_flags: Issues detected during validation
        overall_confidence: Aggregate confidence score (0.0-1.0)
        mode: Reasoning mode that was used
        raw_response: Unparsed LLM output (for debugging)

    Example:
        >>> response = ReasonedResponse(
        ...     answer="Machine learning is...",
        ...     citations=["Source: paper.pdf, Page 42"],
        ...     reasoning_steps=[
        ...         ReasoningStep(1, "Understanding the query...", "understand", 1.0),
        ...         ReasoningStep(2, "Found 3 relevant chunks", "retrieve", 0.95, [0, 1, 2])
        ...     ],
        ...     validation_flags=[],
        ...     overall_confidence=0.92,
        ...     mode=ReasoningMode.BASIC,
        ...     raw_response="<reasoning>...</reasoning>"
        ... )
    """
    answer: str
    citations: List[str]
    reasoning_steps: List[ReasoningStep]
    validation_flags: List[ValidationFlag]
    overall_confidence: float
    mode: ReasoningMode
    raw_response: str
    metadata: Dict[str, Any] = field(default_factory=dict)

    def has_critical_issues(self) -> bool:
        """Check if response has high-severity validation issues.

        Returns:
            True if any validation flag has severity "high"
        """
        return any(flag.severity == "high" for flag in self.validation_flags)

    def get_step_by_action(self, action: str) -> Optional[ReasoningStep]:
        """Get first reasoning step matching the specified action.

        Args:
            action: Action type to search for

        Returns:
            First matching ReasoningStep, or None if not found
        """
        for step in self.reasoning_steps:
            if step.action == action:
                return step
        return None


# Action types for reasoning steps
REASONING_ACTIONS = {
    "understand": "Understanding the query and identifying requirements",
    "retrieve": "Retrieving relevant information from sources",
    "analyze": "Analyzing retrieved information for relevance and accuracy",
    "synthesize": "Combining information to form comprehensive answer",
    "conclude": "Drawing final conclusion with confidence assessment",
    "validate": "Validating reasoning logic and checking for contradictions",
}


# Severity levels for validation flags
SEVERITY_LEVELS = {
    "low": "Minor issue that doesn't affect answer quality",
    "medium": "Moderate issue that may affect answer partially",
    "high": "Critical issue that significantly affects answer reliability",
}


# Flag types and their descriptions
FLAG_TYPES = {
    "contradiction": "Information from sources contradicts itself",
    "uncertainty": "LLM expresses uncertainty about answer",
    "assumption": "Answer relies on unstated assumptions",
    "low_confidence": "Overall confidence below acceptable threshold",
    "missing_evidence": "Claims made without supporting citations",
    "logical_fallacy": "Reasoning contains logical errors",
}
