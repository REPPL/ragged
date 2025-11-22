"""Few-shot example storage and retrieval for improved prompting.

Stores high-quality Q&A examples and retrieves relevant ones for few-shot learning.

This module maintains backwards compatibility by importing from the refactored
few_shot submodule. All functionality has been split into logical modules:
- few_shot/models.py: FewShotExample dataclass
- few_shot/store.py: FewShotExampleStore class with search functionality
- few_shot/seeding.py: seed_default_examples function
- few_shot/prompt.py: format_few_shot_prompt function
"""

# Import all public components for backwards compatibility
from src.generation.few_shot.models import FewShotExample
from src.generation.few_shot.prompt import format_few_shot_prompt
from src.generation.few_shot.seeding import seed_default_examples
from src.generation.few_shot.store import FewShotExampleStore

__all__ = [
    "FewShotExample",
    "FewShotExampleStore",
    "seed_default_examples",
    "format_few_shot_prompt",
]
