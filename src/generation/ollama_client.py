"""
Ollama LLM client for text generation.

Provides interface to Ollama for generating answers using local LLMs.
"""

from typing import TYPE_CHECKING, Generator, Optional

if TYPE_CHECKING:
    import ollama as ollama_module
else:
    try:
        import ollama as ollama_module
    except ImportError:
        ollama_module = None  # type: ignore[assignment]

from src.config.constants import DEFAULT_API_TIMEOUT, DEFAULT_LLM_TEMPERATURE
from src.config.settings import get_settings
from src.utils.logging import get_logger

logger = get_logger(__name__)


class OllamaClient:
    """
    Client for Ollama LLM API.

    Handles chat completions with timeout and error handling.
    """

    def __init__(
        self,
        model: Optional[str] = None,
        base_url: Optional[str] = None,
        timeout: int = DEFAULT_API_TIMEOUT,
    ):
        """
        Initialize Ollama client.

        Args:
            model: Model name (uses config if None)
            base_url: Ollama API URL (uses config if None)
            timeout: Request timeout in seconds
        """
        if ollama_module is None:
            raise ImportError("ollama required: pip install ollama")

        settings = get_settings()
        self.model = model or settings.llm_model
        self.base_url = base_url or settings.ollama_url
        self.timeout = timeout

        # Create client
        self.client = ollama_module.Client(host=self.base_url)

        # Verify model exists
        self._verify_model_available()

        logger.info(f"OllamaClient initialized with model: {self.model}")

    def _verify_model_available(self) -> None:
        """
        Verify model is available in Ollama with helpful error messages.

        Raises:
            RuntimeError: If model not found, with actionable suggestions
        """
        try:
            from src.config.model_manager import ModelManager

            manager = ModelManager(self.base_url)

            if not manager.verify_model(self.model):
                available = manager.list_available_models()

                if not available:
                    raise RuntimeError(
                        f"No models available in Ollama.\n\n"
                        f"Install a model with:\n"
                        f"  ollama pull llama3.2:latest\n\n"
                        f"See available models at: https://ollama.com/library"
                    )

                recommended = manager.get_recommended_model()
                model_list = "\n  ".join([m.name for m in available[:3]])

                raise RuntimeError(
                    f"Model '{self.model}' not found in Ollama.\n\n"
                    f"Available models:\n  {model_list}\n\n"
                    f"Recommended for RAG: {recommended}\n\n"
                    f"To use a different model:\n"
                    f"  1. Set environment variable: export RAGGED_LLM_MODEL={recommended}\n"
                    f"  2. Or run: ragged config set-model {recommended}\n"
                    f"  3. Or install this model: ollama pull {self.model}"
                )

        except ImportError:
            # Fall back to simple warning if ModelManager not available
            logger.warning(
                f"Model {self.model} not found. "
                f"Install with: ollama pull {self.model}"
            )
        except RuntimeError:
            # Re-raise RuntimeError to propagate helpful error messages
            raise
        except Exception:  # noqa: BLE001 - Non-critical verification, service continues
            logger.warning("Could not verify model availability", exc_info=True)

    def generate(
        self,
        prompt: str,
        system: Optional[str] = None,
        temperature: float = DEFAULT_LLM_TEMPERATURE,
        max_tokens: Optional[int] = None,
    ) -> str:
        """
        Generate text completion.

        Args:
            prompt: User prompt
            system: Optional system prompt
            temperature: Sampling temperature (0.0-1.0)
            max_tokens: Maximum tokens to generate

        Returns:
            Generated text
        """
        # Build messages list
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        # Prepare options
        options = {"temperature": temperature}
        if max_tokens:
            options["num_predict"] = max_tokens

        try:
            response = self.client.chat(
                model=self.model,
                messages=messages,
                options=options,
            )
            return str(response["message"]["content"])
        except Exception as e:  # noqa: BLE001 - Re-raised with context
            logger.exception("Generation failed")
            raise RuntimeError(f"Failed to generate response: {e}") from e  # noqa: TRY003

    def generate_stream(
        self,
        prompt: str,
        system: Optional[str] = None,
        temperature: float = DEFAULT_LLM_TEMPERATURE,
    ) -> Generator[str, None, None]:
        """
        Generate text with streaming response.

        Args:
            prompt: User prompt
            system: Optional system prompt
            temperature: Sampling temperature

        Yields:
            Response chunks as they arrive
        """
        # Build messages list
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        try:
            stream = self.client.chat(
                model=self.model,
                messages=messages,
                stream=True,
                options={"temperature": temperature},
            )
            for chunk in stream:
                if "message" in chunk and "content" in chunk["message"]:
                    yield chunk["message"]["content"]
        except Exception as e:  # noqa: BLE001 - Re-raised with context
            logger.exception("Streaming generation failed")
            raise RuntimeError(f"Failed to generate streaming response: {e}") from e  # noqa: TRY003

    def health_check(self) -> bool:
        """
        Check if Ollama is accessible.

        Returns:
            True if healthy, False otherwise
        """
        try:
            self.client.list()
            return True
        except Exception:  # noqa: BLE001 - Health check returns False on any error
            logger.exception("Ollama health check failed")
            return False
