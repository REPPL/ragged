"""Tests for metadata serialisation utilities."""

import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from src.storage.metadata_serialiser import (
    deserialise_batch_metadata,
    deserialise_metadata,
    serialise_batch_metadata,
    serialise_metadata,
)


class TestSerialiseMetadata:
    """Tests for serialise_metadata function."""

    def test_serialise_simple_types(self):
        """Test that simple types are unchanged."""
        metadata = {
            "string": "hello",
            "integer": 42,
            "float": 3.14,
            "boolean": True,
        }
        result = serialise_metadata(metadata)

        assert result == metadata
        assert result["string"] == "hello"
        assert result["integer"] == 42
        assert result["float"] == 3.14
        assert result["boolean"] is True

    def test_serialise_path_object(self):
        """Test that Path objects are converted to strings."""
        metadata = {
            "path": Path("/data/documents/file.pdf"),
            "count": 5,
        }
        result = serialise_metadata(metadata)

        assert result["path"] == "/data/documents/file.pdf"
        assert isinstance(result["path"], str)
        assert result["count"] == 5

    def test_serialise_datetime(self):
        """Test that datetime objects are converted to ISO format."""
        dt = datetime(2024, 1, 15, 10, 30, 45, tzinfo=timezone.utc)
        metadata = {"timestamp": dt, "count": 1}
        result = serialise_metadata(metadata)

        assert result["timestamp"] == "2024-01-15T10:30:45+00:00"
        assert isinstance(result["timestamp"], str)
        assert result["count"] == 1

    def test_serialise_list(self):
        """Test that lists are converted to JSON strings."""
        metadata = {
            "tags": ["ML", "AI", "NLP"],
            "scores": [0.9, 0.8, 0.7],
            "count": 3,
        }
        result = serialise_metadata(metadata)

        assert result["tags"].startswith("__json__:")
        assert result["scores"].startswith("__json__:")
        assert result["count"] == 3

        # Verify JSON is valid
        tags_json = result["tags"][len("__json__:"):]
        assert json.loads(tags_json) == ["ML", "AI", "NLP"]

    def test_serialise_dict(self):
        """Test that dicts are converted to JSON strings."""
        metadata = {
            "config": {"model": "llama2", "temperature": 0.7},
            "count": 1,
        }
        result = serialise_metadata(metadata)

        assert result["config"].startswith("__json__:")
        assert result["count"] == 1

        # Verify JSON is valid
        config_json = result["config"][len("__json__:"):]
        assert json.loads(config_json) == {"model": "llama2", "temperature": 0.7}

    def test_serialise_nested_structures(self):
        """Test serialisation of nested lists and dicts."""
        metadata = {
            "nested": {
                "list_in_dict": [1, 2, 3],
                "dict_in_dict": {"key": "value"},
            },
        }
        result = serialise_metadata(metadata)

        assert result["nested"].startswith("__json__:")
        nested_json = result["nested"][len("__json__:"):]
        parsed = json.loads(nested_json)
        assert parsed["list_in_dict"] == [1, 2, 3]
        assert parsed["dict_in_dict"] == {"key": "value"}

    def test_serialise_none_values_removed(self):
        """Test that None values are removed."""
        metadata = {
            "key1": "value1",
            "key2": None,
            "key3": 42,
            "key4": None,
        }
        result = serialise_metadata(metadata)

        assert "key1" in result
        assert "key2" not in result
        assert "key3" in result
        assert "key4" not in result
        assert result == {"key1": "value1", "key3": 42}

    def test_serialise_empty_dict(self):
        """Test serialisation of empty dict."""
        result = serialise_metadata({})
        assert result == {}

    def test_serialise_unicode_strings(self):
        """Test that unicode strings are preserved."""
        metadata = {
            "text": "Hello 世界 🌍",
            "author": "Müller",
        }
        result = serialise_metadata(metadata)

        assert result["text"] == "Hello 世界 🌍"
        assert result["author"] == "Müller"

    def test_serialise_list_with_unicode(self):
        """Test that lists with unicode are serialised correctly."""
        metadata = {
            "tags": ["日本語", "中文", "한글"],
        }
        result = serialise_metadata(metadata)

        tags_json = result["tags"][len("__json__:"):]
        assert json.loads(tags_json) == ["日本語", "中文", "한글"]


class TestDeserialiseMetadata:
    """Tests for deserialise_metadata function."""

    def test_deserialise_simple_types(self):
        """Test that simple types are unchanged."""
        metadata = {
            "string": "hello",
            "integer": 42,
            "float": 3.14,
            "boolean": True,
        }
        result = deserialise_metadata(metadata)

        assert result == metadata

    def test_deserialise_json_list(self):
        """Test that JSON lists are deserialised."""
        metadata = {
            "tags": '__json__:["ML", "AI", "NLP"]',
            "count": 3,
        }
        result = deserialise_metadata(metadata)

        assert result["tags"] == ["ML", "AI", "NLP"]
        assert isinstance(result["tags"], list)
        assert result["count"] == 3

    def test_deserialise_json_dict(self):
        """Test that JSON dicts are deserialised."""
        metadata = {
            "config": '__json__:{"model": "llama2", "temperature": 0.7}',
            "count": 1,
        }
        result = deserialise_metadata(metadata)

        assert result["config"] == {"model": "llama2", "temperature": 0.7}
        assert isinstance(result["config"], dict)
        assert result["count"] == 1

    def test_deserialise_nested_json(self):
        """Test deserialisation of nested structures."""
        metadata = {
            "nested": '__json__:{"list": [1, 2, 3], "dict": {"key": "value"}}',
        }
        result = deserialise_metadata(metadata)

        assert result["nested"]["list"] == [1, 2, 3]
        assert result["nested"]["dict"] == {"key": "value"}

    def test_deserialise_invalid_json_keeps_string(self):
        """Test that invalid JSON is kept as string."""
        metadata = {
            "bad_json": "__json__:invalid json here",
            "good": "value",
        }
        result = deserialise_metadata(metadata)

        # Invalid JSON should be kept as string
        assert result["bad_json"] == "__json__:invalid json here"
        assert result["good"] == "value"

    def test_deserialise_empty_dict(self):
        """Test deserialisation of empty dict."""
        result = deserialise_metadata({})
        assert result == {}

    def test_deserialise_non_json_strings(self):
        """Test that regular strings are unchanged."""
        metadata = {
            "path": "/data/file.pdf",
            "name": "document",
        }
        result = deserialise_metadata(metadata)

        assert result == metadata


class TestRoundTrip:
    """Tests for serialise -> deserialise round trips."""

    def test_roundtrip_complex_metadata(self):
        """Test that complex metadata survives round trip."""
        original = {
            "path": Path("/data/documents/file.pdf"),
            "tags": ["ML", "AI"],
            "config": {"model": "llama2", "temp": 0.7},
            "count": 42,
            "active": True,
            "missing": None,
        }

        serialised = serialise_metadata(original)
        deserialised = deserialise_metadata(serialised)

        # Path becomes string (expected)
        assert deserialised["path"] == "/data/documents/file.pdf"
        assert deserialised["tags"] == ["ML", "AI"]
        assert deserialised["config"] == {"model": "llama2", "temp": 0.7}
        assert deserialised["count"] == 42
        assert deserialised["active"] is True
        assert "missing" not in deserialised  # None removed

    def test_roundtrip_datetime(self):
        """Test datetime round trip."""
        dt = datetime(2024, 1, 15, 10, 30, 45, tzinfo=timezone.utc)
        original = {"timestamp": dt}

        serialised = serialise_metadata(original)
        # Note: deserialise doesn't convert ISO strings back to datetime
        # This is intentional - strings are valid metadata
        assert serialised["timestamp"] == "2024-01-15T10:30:45+00:00"

    def test_roundtrip_nested_structures(self):
        """Test nested structures survive round trip."""
        original = {
            "data": {
                "users": [
                    {"name": "Alice", "age": 30},
                    {"name": "Bob", "age": 25},
                ],
                "settings": {"theme": "dark", "lang": "en"},
            }
        }

        serialised = serialise_metadata(original)
        deserialised = deserialise_metadata(serialised)

        assert deserialised["data"] == original["data"]

    def test_roundtrip_unicode(self):
        """Test unicode data survives round trip."""
        original = {
            "title": "Machine Learning 機械学習",
            "tags": ["日本語", "中文", "한글"],
        }

        serialised = serialise_metadata(original)
        deserialised = deserialise_metadata(serialised)

        assert deserialised["title"] == "Machine Learning 機械学習"
        assert deserialised["tags"] == ["日本語", "中文", "한글"]


class TestBatchFunctions:
    """Tests for batch serialisation/deserialisation."""

    def test_serialise_batch_metadata(self):
        """Test batch serialisation."""
        metadatas = [
            {"tags": ["ML", "AI"], "count": 1},
            {"tags": ["NLP"], "count": 2},
            {"tags": [], "count": 3},
        ]

        result = serialise_batch_metadata(metadatas)

        assert len(result) == 3
        assert all(m["tags"].startswith("__json__:") for m in result)
        assert result[0]["count"] == 1
        assert result[1]["count"] == 2
        assert result[2]["count"] == 3

    def test_deserialise_batch_metadata(self):
        """Test batch deserialisation."""
        metadatas = [
            {"tags": '__json__:["ML", "AI"]', "count": 1},
            {"tags": '__json__:["NLP"]', "count": 2},
        ]

        result = deserialise_batch_metadata(metadatas)

        assert len(result) == 2
        assert result[0]["tags"] == ["ML", "AI"]
        assert result[1]["tags"] == ["NLP"]
        assert result[0]["count"] == 1
        assert result[1]["count"] == 2

    def test_batch_roundtrip(self):
        """Test batch round trip."""
        original = [
            {"path": Path("/data/file1.pdf"), "tags": ["ML"]},
            {"path": Path("/data/file2.pdf"), "tags": ["AI", "NLP"]},
        ]

        serialised = serialise_batch_metadata(original)
        deserialised = deserialise_batch_metadata(serialised)

        assert deserialised[0]["path"] == "/data/file1.pdf"
        assert deserialised[0]["tags"] == ["ML"]
        assert deserialised[1]["path"] == "/data/file2.pdf"
        assert deserialised[1]["tags"] == ["AI", "NLP"]

    def test_empty_batch(self):
        """Test empty batch."""
        assert serialise_batch_metadata([]) == []
        assert deserialise_batch_metadata([]) == []


class TestEdgeCases:
    """Tests for edge cases and error handling."""

    def test_serialise_empty_list(self):
        """Test that empty lists are serialised."""
        metadata = {"tags": []}
        result = serialise_metadata(metadata)

        assert result["tags"].startswith("__json__:")
        tags_json = result["tags"][len("__json__:"):]
        assert json.loads(tags_json) == []

    def test_serialise_empty_dict(self):
        """Test that empty dicts are serialised."""
        metadata = {"config": {}}
        result = serialise_metadata(metadata)

        assert result["config"].startswith("__json__:")
        config_json = result["config"][len("__json__:"):]
        assert json.loads(config_json) == {}

    def test_serialise_numeric_strings(self):
        """Test that numeric strings remain strings."""
        metadata = {
            "id": "12345",
            "code": "001",
        }
        result = serialise_metadata(metadata)

        assert result["id"] == "12345"
        assert result["code"] == "001"
        assert isinstance(result["id"], str)

    def test_serialise_boolean_strings(self):
        """Test that boolean-like strings remain strings."""
        metadata = {
            "value1": "true",
            "value2": "false",
        }
        result = serialise_metadata(metadata)

        assert result["value1"] == "true"
        assert result["value2"] == "false"
        assert isinstance(result["value1"], str)

    def test_deserialise_string_starting_with_json_prefix_but_invalid(self):
        """Test handling of strings that look like JSON prefix but aren't."""
        metadata = {
            "weird": "__json__:",  # Just the prefix
            "normal": "value",
        }
        result = deserialise_metadata(metadata)

        # Empty JSON after prefix should keep as string
        assert result["weird"] == "__json__:"
        assert result["normal"] == "value"
