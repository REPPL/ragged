"""
Tests for ProcessorFactory.
"""

import pytest

from src.processing.base import BaseProcessor, ProcessorConfig
from src.processing.factory import ProcessorFactory


class TestProcessorFactory:
    """Tests for ProcessorFactory."""

    def test_create_legacy_processor(self):
        """Test creating legacy processor."""
        config = ProcessorConfig(processor_type="legacy")
        processor = ProcessorFactory.create(config)

        assert processor is not None
        assert processor.config.processor_type == "legacy"
        assert isinstance(processor, BaseProcessor)

    def test_create_docling_processor_if_available(self):
        """Test creating Docling processor if available."""
        # This test will pass if Docling is installed, otherwise skip
        if not ProcessorFactory.is_processor_available("docling"):
            pytest.skip("Docling not installed")

        config = ProcessorConfig(processor_type="docling")
        processor = ProcessorFactory.create(config)

        assert processor is not None
        assert processor.config.processor_type == "docling"
        assert isinstance(processor, BaseProcessor)

    def test_create_unknown_processor(self):
        """Test that creating unknown processor raises ValueError."""
        config = ProcessorConfig(processor_type="nonexistent")

        with pytest.raises(ValueError, match="Unknown processor type"):
            ProcessorFactory.create(config)

    def test_get_available_processors(self):
        """Test getting available processors."""
        processors = ProcessorFactory.get_available_processors()

        assert isinstance(processors, dict)
        assert "legacy" in processors
        # Docling may or may not be available depending on installation

    def test_is_processor_available(self):
        """Test checking processor availability."""
        assert ProcessorFactory.is_processor_available("legacy") is True
        assert ProcessorFactory.is_processor_available("nonexistent") is False

    def test_register_custom_processor(self):
        """Test registering a custom processor."""
        from src.processing.base import ProcessedDocument
        from pathlib import Path

        class CustomProcessor(BaseProcessor):
            def process(self, file_path: Path) -> ProcessedDocument:
                return ProcessedDocument(content="custom", processor_type="custom")

            def supports_file_type(self, file_path: Path) -> bool:
                return True

            def get_capabilities(self) -> dict[str, bool]:
                return {}

        # Register the custom processor
        ProcessorFactory.register_processor("custom", CustomProcessor)

        # Verify it's available
        assert ProcessorFactory.is_processor_available("custom")

        # Create instance
        config = ProcessorConfig(processor_type="custom")
        processor = ProcessorFactory.create(config)

        assert isinstance(processor, CustomProcessor)

    def test_register_invalid_processor(self):
        """Test that registering non-BaseProcessor raises ValueError."""

        class NotAProcessor:
            pass

        with pytest.raises(ValueError, match="must inherit from BaseProcessor"):
            ProcessorFactory.register_processor("invalid", NotAProcessor)  # type: ignore
