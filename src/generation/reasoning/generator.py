"""
Reasoning generator for chain-of-thought responses.

v0.3.7b: Generate responses with transparent reasoning.
"""

from typing import Any

from src.generation.reasoning.parser import ReasoningParser
from src.generation.reasoning.prompts import build_reasoning_prompt
from src.generation.reasoning.types import ReasonedResponse, ReasoningMode
from src.utils.logging import get_logger

logger = get_logger(__name__)


class ReasoningGenerator:
    """
    Generate responses with transparent reasoning.

    Integrates with existing Ollama client to add chain-of-thought
    capabilities with minimal changes to existing pipeline.

    Example:
        >>> from src.generation.ollama_client import Ollama Client
        >>> client = OllamaClient()
        >>> generator = ReasoningGenerator(
        ...     ollama_client=client,
        ...     mode=ReasoningMode.BASIC,
        ...     show_reasoning=True
        ... )
        >>> response = generator.generate_with_reasoning(
        ...     query="What is machine learning?",
        ...     chunks=retrieved_chunks
        ... )
    """

    def __init__(
        self,
        ollama_client: Any,
        mode: ReasoningMode = ReasoningMode.BASIC,
        show_reasoning: bool = False
    ):
        """
        Initialise reasoning generator.

        Args:
            ollama_client: Configured Ollama client instance
            mode: Reasoning depth level
            show_reasoning: Whether to display reasoning to user
        """
        self.client = ollama_client
        self.mode = mode
        self.show_reasoning = show_reasoning
        self.parser = ReasoningParser()

    def generate_with_reasoning(
        self,
        query: str,
        chunks: list[Any],
        confidence_threshold: float = 0.3
    ) -> ReasonedResponse:
        """
        Generate answer with reasoning trace.

        Args:
            query: User's question
            chunks: Retrieved document chunks
            confidence_threshold: Minimum acceptable confidence (0.0-1.0)

        Returns:
            ReasonedResponse with answer and reasoning

        Example:
            >>> response = generator.generate_with_reasoning(
            ...     "What is ML?",
            ...     chunks,
            ...     confidence_threshold=0.5
            ... )
            >>> print(response.answer)
            >>> if response.overall_confidence < 0.5:
            ...     print("Warning: Low confidence")
        """
        try:
            # Build prompt with reasoning template
            prompt = build_reasoning_prompt(
                query=query,
                chunks=chunks,
                mode=self.mode
            )

            # Generate response using Ollama
            raw_response = self._generate_with_ollama(prompt)

            # Parse reasoning and answer
            response = self.parser.parse_response(raw_response, self.mode)

            # Apply confidence threshold check
            if response.overall_confidence < confidence_threshold:
                from src.generation.reasoning.types import ValidationFlag
                response.validation_flags.append(
                    ValidationFlag(
                        type="low_confidence",
                        description=f"Overall confidence {response.overall_confidence:.2f} below threshold {confidence_threshold}",
                        severity="high",
                        step_numbers=[]
                    )
                )

            logger.info(
                "Generated response with reasoning",
                extra={
                    "mode": self.mode.value,
                    "steps": len(response.reasoning_steps),
                    "confidence": response.overall_confidence,
                    "flags": len(response.validation_flags)
                }
            )

            return response

        except Exception as e:
            logger.error(f"Error generating reasoned response: {e}")
            # Fallback to direct answer
            return self._create_fallback_response(str(e))

    def _generate_with_ollama(self, prompt: str) -> str:
        """
        Generate response using Ollama client.

        Args:
            prompt: Formatted prompt with reasoning template

        Returns:
            Raw LLM response text
        """
        # Check if client has generate method
        if hasattr(self.client, 'generate'):
            return self.client.generate(prompt)
        # Fallback to chat method if available
        elif hasattr(self.client, 'chat'):
            response = self.client.chat([{"role": "user", "content": prompt}])
            return response.get('message', {}).get('content', '')
        else:
            raise AttributeError("Ollama client missing generate() or chat() method")

    def _create_fallback_response(self, error_msg: str) -> ReasonedResponse:
        """
        Create fallback response when generation fails.

        Args:
            error_msg: Error message to include

        Returns:
            Basic ReasonedResponse with error information
        """
        from src.generation.reasoning.types import ValidationFlag

        return ReasonedResponse(
            answer=f"Unable to generate response: {error_msg}",
            citations=[],
            reasoning_steps=[],
            validation_flags=[
                ValidationFlag(
                    type="error",
                    description=f"Generation failed: {error_msg}",
                    severity="high",
                    step_numbers=[]
                )
            ],
            overall_confidence=0.0,
            mode=self.mode,
            raw_response=""
        )

    def format_for_display(
        self,
        response: ReasonedResponse,
        verbose: bool = False
    ) -> str:
        """
        Format response for CLI display.

        Args:
            response: Generated response with reasoning
            verbose: Show additional details

        Returns:
            Formatted string ready for console output

        Example:
            >>> formatted = generator.format_for_display(response, verbose=True)
            >>> print(formatted)
        """
        output = []

        # Reasoning section (if enabled and available)
        if self.show_reasoning and response.mode != ReasoningMode.NONE:
            if response.reasoning_steps:
                output.append("═" * 60)
                output.append("REASONING PROCESS")
                output.append("─" * 60)

                for step in response.reasoning_steps:
                    output.append(f"\nStep {step.step_number}: {step.action.upper()}")
                    output.append(f"  {step.thought}")

                    if step.confidence < 1.0:
                        output.append(f"  Confidence: {step.confidence:.1%}")

                    if step.evidence:
                        evidence_str = ", ".join(f"[{e}]" for e in step.evidence)
                        output.append(f"  Evidence: {evidence_str}")

            # Validation issues
            if response.validation_flags:
                output.append("\n⚠️  VALIDATION ISSUES:")
                severity_emoji = {"high": "🔴", "medium": "🟡", "low": "🟢"}

                for flag in response.validation_flags:
                    emoji = severity_emoji.get(flag.severity, "⚠️")
                    output.append(f"  {emoji} {flag.description}")

            output.append("\n" + "═" * 60)

        # Answer section
        output.append("\nANSWER:")
        output.append(response.answer)

        # Citations (if present)
        if response.citations:
            output.append("\nSOURCES:")
            for citation in response.citations:
                output.append(f"  • {citation}")

        # Confidence indicator (if verbose or low confidence)
        if verbose or response.overall_confidence < 0.5:
            confidence_pct = response.overall_confidence * 100
            confidence_bar = "█" * int(confidence_pct / 10) + "░" * (10 - int(confidence_pct / 10))
            output.append(f"\nConfidence: [{confidence_bar}] {response.overall_confidence:.1%}")

        return "\n".join(output)
