"""
Ollama LLM client for text generation.

Provides interface to Ollama for generating answers using local LLMs.
"""

from typing import Optional

try:
    import ollama
except ImportError:
    ollama = None

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
        model: str = None,
        base_url: str = None,
        timeout: int = 30,
    ):
        """
        Initialize Ollama client.

        Args:
            model: Model name (uses config if None)
            base_url: Ollama API URL (uses config if None)
            timeout: Request timeout in seconds
        """
        if ollama is None:
            raise ImportError("ollama required: pip install ollama")

        settings = get_settings()
        self.model = model or settings.llm_model
        self.base_url = base_url or settings.ollama_url
        self.timeout = timeout

        # Create client
        self.client = ollama.Client(host=self.base_url)

        # Verify model exists
        self._verify_model_available()

        logger.info(f"OllamaClient initialized with model: {self.model}")

    def _verify_model_available(self) -> None:
        """
        Verify model is available in Ollama.
        """
        try:
            models = self.client.list()
            model_names = [m.model for m in models.models]

            if not any(self.model in name for name in model_names):
                logger.warning(
                    f"Model {self.model} not found. "
                    f"Install with: ollama pull {self.model}"
                )
        except Exception as e:
            logger.warning(f"Could not verify model availability: {e}")

    def generate(
        self,
        prompt: str,
        system: Optional[str] = None,
        temperature: float = 0.7,
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
            return response["message"]["content"]
        except Exception as e:
            logger.error(f"Generation failed: {e}")
            raise RuntimeError(f"Failed to generate response: {e}")

    def generate_stream(
        self,
        prompt: str,
        system: Optional[str] = None,
        temperature: float = 0.7,
    ):
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
        except Exception as e:
            logger.error(f"Streaming generation failed: {e}")
            raise RuntimeError(f"Failed to generate streaming response: {e}")

    def health_check(self) -> bool:
        """
        Check if Ollama is accessible.

        Returns:
            True if healthy, False otherwise
        """
        try:
            self.client.list()
            return True
        except Exception as e:
            logger.error(f"Ollama health check failed: {e}")
            return False
