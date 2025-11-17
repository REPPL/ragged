"""Few-shot example data models."""

from dataclasses import dataclass, asdict
from typing import Dict, Any, List, Optional


@dataclass
class FewShotExample:
    """A few-shot Q&A example."""

    query: str
    context: str  # Retrieved context that was used
    answer: str  # High-quality answer
    category: Optional[str] = None  # Category for organisation
    tags: Optional[List[str]] = None  # Tags for filtering

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "FewShotExample":
        """Create from dictionary."""
        return cls(**data)

    def to_prompt_format(self) -> str:
        """Format as few-shot prompt example.

        Returns:
            Formatted example for prompting
        """
        return f"""Example:
Query: {self.query}

Context:
{self.context}

Answer: {self.answer}
"""
