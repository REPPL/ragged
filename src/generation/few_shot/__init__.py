"""Few-shot example storage and retrieval for improved prompting.

Stores high-quality Q&A examples and retrieves relevant ones for few-shot learning.
"""

from src.generation.few_shot.models import FewShotExample
from src.generation.few_shot.store import FewShotExampleStore
from src.generation.few_shot.seeding import seed_default_examples
from src.generation.few_shot.prompt import format_few_shot_prompt

__all__ = [
    "FewShotExample",
    "FewShotExampleStore",
    "seed_default_examples",
    "format_few_shot_prompt",
]
