"""
Configuration personas for common use cases.

Personas provide pre-configured settings optimised for specific scenarios,
making ragged approachable for users who don't want to manually tune parameters.
"""

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.config.config_manager import RaggedConfig


@dataclass
class PersonaConfig:
    """Persona configuration template."""

    name: str
    description: str
    retrieval_method: str
    top_k: int
    enable_reranking: bool
    rerank_to: int
    enable_query_decomposition: bool
    enable_hyde: bool
    enable_compression: bool
    confidence_threshold: float


class PersonaManager:
    """Manage configuration personas."""

    # Built-in personas
    PERSONAS: dict[str, PersonaConfig] = {
        "accuracy": PersonaConfig(
            name="accuracy",
            description="Maximum quality, slower responses",
            retrieval_method="hybrid",
            top_k=10,
            enable_reranking=True,
            rerank_to=3,
            enable_query_decomposition=True,
            enable_hyde=False,
            enable_compression=True,
            confidence_threshold=0.95,
        ),
        "speed": PersonaConfig(
            name="speed",
            description="Fast answers, good quality",
            retrieval_method="vector",
            top_k=3,
            enable_reranking=False,
            rerank_to=0,
            enable_query_decomposition=False,
            enable_hyde=False,
            enable_compression=False,
            confidence_threshold=0.80,
        ),
        "balanced": PersonaConfig(
            name="balanced",
            description="Default - balanced quality and speed",
            retrieval_method="hybrid",
            top_k=5,
            enable_reranking=True,
            rerank_to=5,
            enable_query_decomposition=False,
            enable_hyde=False,
            enable_compression=False,
            confidence_threshold=0.85,
        ),
        "research": PersonaConfig(
            name="research",
            description="Deep exploration, comprehensive results",
            retrieval_method="hybrid",
            top_k=30,
            enable_reranking=True,
            rerank_to=10,
            enable_query_decomposition=True,
            enable_hyde=True,
            enable_compression=False,
            confidence_threshold=0.90,
        ),
        "quick-answer": PersonaConfig(
            name="quick-answer",
            description="Single best answer, fastest",
            retrieval_method="hybrid",
            top_k=1,
            enable_reranking=False,
            rerank_to=0,
            enable_query_decomposition=False,
            enable_hyde=False,
            enable_compression=False,
            confidence_threshold=0.75,
        ),
    }

    @classmethod
    def get_persona(cls, name: str) -> PersonaConfig:
        """
        Get persona by name.

        Args:
            name: Persona name

        Returns:
            PersonaConfig

        Raises:
            ValueError: If persona not found
        """
        if name not in cls.PERSONAS:
            raise ValueError(f"Unknown persona: {name}")
        return cls.PERSONAS[name]

    @classmethod
    def list_personas(cls) -> dict[str, str]:
        """
        List all personas with descriptions.

        Returns:
            Dict mapping persona names to descriptions
        """
        return {name: persona.description for name, persona in cls.PERSONAS.items()}

    @classmethod
    def apply_persona(cls, config: "RaggedConfig", persona_name: str) -> None:
        """
        Apply persona settings to config.

        Args:
            config: RaggedConfig to modify
            persona_name: Name of persona to apply

        Raises:
            ValueError: If persona not found
        """
        persona = cls.get_persona(persona_name)

        config.retrieval_method = persona.retrieval_method
        config.top_k = persona.top_k
        config.enable_reranking = persona.enable_reranking
        config.rerank_to = persona.rerank_to
        config.enable_query_decomposition = persona.enable_query_decomposition
        config.enable_hyde = persona.enable_hyde
        config.enable_compression = persona.enable_compression
        config.confidence_threshold = persona.confidence_threshold
        config.persona = persona_name
