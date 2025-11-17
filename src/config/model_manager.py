"""Model selection and management for Ollama.

Provides functionality to discover available models, calculate suitability scores
for RAG tasks, and recommend the best model for the user's needs.
"""

import ollama
from dataclasses import dataclass
from typing import List, Optional

from src.utils.logging import get_logger

logger = get_logger(__name__)


@dataclass
class ModelInfo:
    """Information about an available model."""

    name: str
    size: int  # bytes
    context_length: int
    family: str  # llama, mistral, etc.
    modified_at: str
    suitability_score: int  # 1-100 for RAG tasks


class ModelManager:
    """Manage Ollama model selection and recommendations."""

    def __init__(self, ollama_url: str = "http://localhost:11434"):
        """Initialize model manager.

        Args:
            ollama_url: URL of the Ollama service
        """
        self.client = ollama.Client(host=ollama_url)

    def list_available_models(self) -> List[ModelInfo]:
        """Get list of locally available models with RAG suitability scores.

        Returns:
            List of ModelInfo objects sorted by suitability score (highest first)
        """
        try:
            response = self.client.list()
            models = []

            for m in response.models:
                # Skip models without a name
                if not m.model:
                    continue

                # Parse model info
                info = ModelInfo(
                    name=m.model,
                    size=getattr(m, "size", 0),
                    context_length=self._estimate_context_length(m.model),
                    family=self._get_model_family(m.model),
                    modified_at=str(getattr(m, "modified_at", "")),
                    suitability_score=self._calculate_rag_suitability(m.model),
                )
                models.append(info)

            # Sort by suitability (highest first)
            models.sort(key=lambda x: x.suitability_score, reverse=True)
            return models

        except Exception:  # noqa: BLE001 - Return empty list on any error
            logger.exception("Failed to list models")
            return []

    def get_recommended_model(self) -> Optional[str]:
        """Get the best available model for RAG tasks.

        Returns:
            Model name if available, None otherwise
        """
        models = self.list_available_models()
        if models:
            return models[0].name
        return None

    def verify_model(self, model_name: str) -> bool:
        """Check if a specific model is available.

        Args:
            model_name: Name of the model to check

        Returns:
            True if model is available, False otherwise
        """
        models = self.list_available_models()
        return any(m.name == model_name for m in models)

    def _estimate_context_length(self, model_name: str) -> int:
        """Estimate context length from model name.

        Args:
            model_name: Name of the model

        Returns:
            Estimated context length in tokens
        """
        # Known context lengths for popular models
        context_map = {
            "llama3.1": 128000,
            "llama3.3": 128000,
            "llama3.2": 8192,
            "qwen2.5": 32768,
            "mistral": 8192,
            "mixtral": 32768,
            "phi3": 4096,
            "gemma": 8192,
        }

        name_lower = model_name.lower()
        for key, length in context_map.items():
            if key in name_lower:
                return length

        # Conservative default
        return 4096

    def _get_model_family(self, model_name: str) -> str:
        """Extract model family from name.

        Args:
            model_name: Name of the model

        Returns:
            Model family name
        """
        name = model_name.lower()

        if "llama" in name:
            return "llama"
        elif "mistral" in name or "mixtral" in name:
            return "mistral"
        elif "qwen" in name:
            return "qwen"
        elif "phi" in name:
            return "phi"
        elif "gemma" in name:
            return "gemma"

        return "unknown"

    def _calculate_rag_suitability(self, model_name: str) -> int:
        """Calculate suitability score (1-100) for RAG tasks.

        Higher scores indicate better suitability for RAG use cases.
        Scoring considers:
        - Context window size (larger is better for RAG)
        - Model quality/capability
        - Model size (balance between quality and speed)

        Args:
            model_name: Name of the model

        Returns:
            Suitability score from 1 to 100
        """
        score = 50  # Base score

        name = model_name.lower()

        # Bonus for large context (critical for RAG)
        context = self._estimate_context_length(model_name)
        if context >= 100000:
            score += 30
        elif context >= 32000:
            score += 20
        elif context >= 8000:
            score += 10

        # Bonus for proven RAG-capable models
        if "llama3" in name:
            score += 15
        elif "mixtral" in name or "qwen" in name:
            score += 10
        elif "mistral" in name or "gemma" in name:
            score += 5

        # Penalty for very small models (may lack reasoning capability)
        if "3b" in name or "mini" in name or "1b" in name:
            score -= 15
        elif "7b" in name:
            score -= 5

        # Bonus for latest/recent versions
        if "latest" in name:
            score += 5

        # Bonus for instruction-tuned variants
        if "instruct" in name:
            score += 5

        # Ensure score stays in valid range
        return max(1, min(100, score))
