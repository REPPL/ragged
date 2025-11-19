"""
Tests for base processor interface and data models.
"""

import pytest
from pathlib import Path

from src.processing.base import (
    BaseProcessor,
    ProcessedDocument,
    ProcessorConfig,
    ProcessorError,
)


class TestProcessedDocument:
    """Tests for ProcessedDocument dataclass."""

    def test_default_values(self):
        """Test that ProcessedDocument has correct defaults."""
        doc = ProcessedDocument(content="test content")

        assert doc.content == "test content"
        assert doc.tables == []
        assert doc.images == []
        assert doc.metadata == {}
        assert doc.confidence == 1.0
        assert doc.processor_type == "unknown"

    def test_with_all_fields(self):
        """Test ProcessedDocument with all fields populated."""
        doc = ProcessedDocument(
            content="test content",
            tables=[{"data": [["a", "b"]], "page": 1}],
            images=[{"format": "png", "page": 1}],
            metadata={"page_count": 10},
            confidence=0.95,
            processor_type="docling",
        )

        assert doc.content == "test content"
        assert len(doc.tables) == 1
        assert len(doc.images) == 1
        assert doc.metadata["page_count"] == 10
        assert doc.confidence == 0.95
        assert doc.processor_type == "docling"


class TestProcessorConfig:
    """Tests for ProcessorConfig dataclass."""

    def test_default_values(self):
        """Test that ProcessorConfig has correct defaults."""
        config = ProcessorConfig()

        assert config.processor_type == "docling"
        assert config.enable_table_extraction is True
        assert config.enable_layout_analysis is True
        assert config.enable_ocr is False
        assert config.model_cache_dir is None
        assert config.batch_size == 1
        assert config.options == {}

    def test_custom_values(self):
        """Test ProcessorConfig with custom values."""
        config = ProcessorConfig(
            processor_type="legacy",
            enable_table_extraction=False,
            model_cache_dir=Path("/tmp/models"),
            batch_size=10,
            options={"custom": "value"},
        )

        assert config.processor_type == "legacy"
        assert config.enable_table_extraction is False
        assert config.model_cache_dir == Path("/tmp/models")
        assert config.batch_size == 10
        assert config.options["custom"] == "value"


class MockProcessor(BaseProcessor):
    """Mock processor for testing BaseProcessor interface."""

    def process(self, file_path: Path) -> ProcessedDocument:
        """Mock process implementation."""
        return ProcessedDocument(
            content=f"Processed: {file_path.name}",
            processor_type="mock",
        )

    def supports_file_type(self, file_path: Path) -> bool:
        """Mock supports check - only .txt files."""
        return file_path.suffix == ".txt"

    def get_capabilities(self) -> dict[str, bool]:
        """Mock capabilities."""
        return {
            "ocr": False,
            "tables": True,
            "layout_analysis": False,
            "reading_order": False,
            "images": False,
        }


class TestBaseProcessor:
    """Tests for BaseProcessor abstract class."""

    def test_can_instantiate_concrete_processor(self):
        """Test that concrete processor can be instantiated."""
        config = ProcessorConfig()
        processor = MockProcessor(config)

        assert processor.config == config

    def test_validate_file_exists(self, tmp_path):
        """Test that validate_file checks file existence."""
        config = ProcessorConfig()
        processor = MockProcessor(config)

        # Create a test file
        test_file = tmp_path / "test.txt"
        test_file.write_text("test content")

        # Should not raise
        processor.validate_file(test_file)

    def test_validate_file_not_found(self):
        """Test that validate_file raises for missing file."""
        config = ProcessorConfig()
        processor = MockProcessor(config)

        with pytest.raises(FileNotFoundError, match="File not found"):
            processor.validate_file(Path("/nonexistent/file.txt"))

    def test_validate_file_empty(self, tmp_path):
        """Test that validate_file raises for empty file."""
        config = ProcessorConfig()
        processor = MockProcessor(config)

        # Create empty file
        empty_file = tmp_path / "empty.txt"
        empty_file.touch()

        with pytest.raises(ValueError, match="File is empty"):
            processor.validate_file(empty_file)

    def test_validate_file_unsupported_type(self, tmp_path):
        """Test that validate_file raises for unsupported type."""
        config = ProcessorConfig()
        processor = MockProcessor(config)

        # Create file with unsupported extension
        unsupported_file = tmp_path / "test.xyz"
        unsupported_file.write_text("test content")

        with pytest.raises(ValueError, match="Unsupported file type"):
            processor.validate_file(unsupported_file)

    def test_process_method(self, tmp_path):
        """Test that process method works."""
        config = ProcessorConfig()
        processor = MockProcessor(config)

        test_file = tmp_path / "test.txt"
        test_file.write_text("test content")

        result = processor.process(test_file)

        assert result.content == "Processed: test.txt"
        assert result.processor_type == "mock"

    def test_supports_file_type(self, tmp_path):
        """Test supports_file_type method."""
        config = ProcessorConfig()
        processor = MockProcessor(config)

        assert processor.supports_file_type(Path("test.txt")) is True
        assert processor.supports_file_type(Path("test.pdf")) is False

    def test_get_capabilities(self):
        """Test get_capabilities method."""
        config = ProcessorConfig()
        processor = MockProcessor(config)

        caps = processor.get_capabilities()

        assert caps["tables"] is True
        assert caps["ocr"] is False
