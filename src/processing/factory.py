"""
Processor factory for creating document processors.

This module implements the factory pattern for instantiating the appropriate
document processor based on configuration.
"""


from src.processing.base import BaseProcessor, ProcessorConfig
from src.utils.logging import get_logger

logger = get_logger(__name__)


class ProcessorFactory:
    """
    Factory for creating document processor instances.

    The factory maintains a registry of available processors and instantiates
    the appropriate one based on configuration. This allows easy addition of
    new processors (e.g., PaddleOCR in v0.3.4c) without modifying existing code.

    Example:
        >>> config = ProcessorConfig(processor_type="docling")
        >>> processor = ProcessorFactory.create(config)
        >>> result = processor.process(Path("document.pdf"))
    """

    _processors: dict[str, type[BaseProcessor]] = {}

    @classmethod
    def register_processor(cls, name: str, processor_class: type[BaseProcessor]) -> None:
        """
        Register a new processor type.

        This method allows dynamic registration of processor implementations,
        making it easy to add new processors without modifying the factory.

        Args:
            name: Name to register the processor under (e.g., "docling", "legacy")
            processor_class: Processor class (must inherit from BaseProcessor)

        Raises:
            ValueError: If processor_class doesn't inherit from BaseProcessor

        Example:
            >>> ProcessorFactory.register_processor("custom", CustomProcessor)
        """
        if not issubclass(processor_class, BaseProcessor):
            raise ValueError(
                f"Processor class must inherit from BaseProcessor, got {processor_class}"
            )

        cls._processors[name] = processor_class
        logger.debug(f"Registered processor: {name} -> {processor_class.__name__}")

    @classmethod
    def create(cls, config: ProcessorConfig) -> BaseProcessor:
        """
        Create a processor instance based on configuration.

        Args:
            config: Processor configuration including processor_type

        Returns:
            Instantiated processor ready for use

        Raises:
            ValueError: If processor_type is unknown or not registered

        Example:
            >>> config = ProcessorConfig(processor_type="docling")
            >>> processor = ProcessorFactory.create(config)
        """
        processor_class = cls._processors.get(config.processor_type)

        if processor_class is None:
            available = ", ".join(cls._processors.keys())
            raise ValueError(
                f"Unknown processor type: '{config.processor_type}'. "
                f"Available processors: {available}"
            )

        logger.info(f"Creating processor: {config.processor_type}")
        return processor_class(config)

    @classmethod
    def get_available_processors(cls) -> dict[str, type[BaseProcessor]]:
        """
        Get all registered processors.

        Returns:
            Dictionary mapping processor names to their classes

        Example:
            >>> processors = ProcessorFactory.get_available_processors()
            >>> print(processors.keys())
            dict_keys(['legacy', 'docling'])
        """
        return cls._processors.copy()

    @classmethod
    def is_processor_available(cls, name: str) -> bool:
        """
        Check if a processor is registered and available.

        Args:
            name: Processor name to check

        Returns:
            True if processor is available, False otherwise

        Example:
            >>> if ProcessorFactory.is_processor_available("docling"):
            ...     config = ProcessorConfig(processor_type="docling")
        """
        return name in cls._processors


# Auto-register processors when module is imported
def _register_default_processors() -> None:
    """
    Register default processors.

    This function is called automatically when the module is imported.
    It attempts to import and register available processors, gracefully
    handling missing dependencies.
    """
    # Register legacy processor (always available - no optional deps)
    try:
        from src.processing.legacy_processor import LegacyProcessor

        ProcessorFactory.register_processor("legacy", LegacyProcessor)
    except ImportError as e:
        logger.warning(f"Legacy processor not available: {e}")

    # Register Docling processor (optional dependency)
    try:
        from src.processing.docling_processor import DoclingProcessor

        ProcessorFactory.register_processor("docling", DoclingProcessor)
    except ImportError as e:
        logger.debug(f"Docling processor not available (expected if not installed): {e}")


# Auto-register on module import
_register_default_processors()
