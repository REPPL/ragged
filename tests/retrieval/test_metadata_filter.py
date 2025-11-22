"""Tests for metadata filtering and faceted search.

v0.3.7d: Test filter parsing, query building, and faceted search.
"""

import pytest
from datetime import datetime

from src.retrieval.metadata_filter import (
    FilterCondition,
    MetadataFilter,
    FilterParser,
    FacetedSearch,
    create_filter,
)


class TestFilterCondition:
    """Test FilterCondition dataclass."""

    def test_equality_condition(self):
        """Test equality condition creation."""
        condition = FilterCondition(field="tag", operator="==", value="python")

        assert condition.field == "tag"
        assert condition.operator == "=="
        assert condition.value == "python"
        assert "tag == python" in str(condition)

    def test_comparison_condition(self):
        """Test comparison condition."""
        condition = FilterCondition(field="confidence", operator=">", value=0.9)

        assert condition.field == "confidence"
        assert condition.operator == ">"
        assert condition.value == 0.9
        assert "confidence > 0.9" in str(condition)

    def test_in_condition(self):
        """Test 'in' condition."""
        condition = FilterCondition(field="tag", operator="in", value=["python", "java"])

        assert condition.operator == "in"
        assert condition.value == ["python", "java"]
        assert "tag in" in str(condition)

    def test_contains_condition(self):
        """Test 'contains' condition."""
        condition = FilterCondition(field="content", operator="contains", value="machine")

        assert condition.operator == "contains"
        assert "contains 'machine'" in str(condition)


class TestMetadataFilter:
    """Test MetadataFilter class."""

    def test_empty_filter(self):
        """Test empty filter creation."""
        filter = MetadataFilter()

        assert len(filter.conditions) == 0
        assert filter.logic == "AND"
        assert filter.to_dict() == {}
        assert str(filter) == "No filters"

    def test_single_condition(self):
        """Test filter with single condition."""
        filter = MetadataFilter()
        filter.add_condition("tag", "==", "python")

        assert len(filter.conditions) == 1
        filter_dict = filter.to_dict()
        assert filter_dict == {"tag": "python"}

    def test_multiple_conditions_and(self):
        """Test multiple conditions with AND logic."""
        filter = MetadataFilter()
        filter.add_condition("tag", "==", "python")
        filter.add_condition("confidence", ">", 0.9)

        assert len(filter.conditions) == 2
        assert filter.logic == "AND"

        filter_dict = filter.to_dict()
        assert "$and" in filter_dict
        assert len(filter_dict["$and"]) == 2

    def test_multiple_conditions_or(self):
        """Test multiple conditions with OR logic."""
        filter = MetadataFilter(logic="OR")
        filter.add_condition("tag", "==", "python")
        filter.add_condition("tag", "==", "java")

        assert filter.logic == "OR"
        filter_dict = filter.to_dict()
        assert "$or" in filter_dict

    def test_comparison_operators(self):
        """Test all comparison operators."""
        filter = MetadataFilter()
        filter.add_condition("score", ">", 0.8)

        filter_dict = filter.to_dict()
        assert filter_dict == {"score": {"$gt": 0.8}}

        filter2 = MetadataFilter()
        filter2.add_condition("score", ">=", 0.9)
        assert filter2.to_dict() == {"score": {"$gte": 0.9}}

        filter3 = MetadataFilter()
        filter3.add_condition("score", "<", 0.5)
        assert filter3.to_dict() == {"score": {"$lt": 0.5}}

        filter4 = MetadataFilter()
        filter4.add_condition("score", "<=", 0.6)
        assert filter4.to_dict() == {"score": {"$lte": 0.6}}

    def test_inequality_operator(self):
        """Test inequality operator."""
        filter = MetadataFilter()
        filter.add_condition("tag", "!=", "deprecated")

        filter_dict = filter.to_dict()
        assert filter_dict == {"tag": {"$ne": "deprecated"}}

    def test_in_operator(self):
        """Test 'in' operator."""
        filter = MetadataFilter()
        filter.add_condition("tag", "in", ["python", "java", "rust"])

        filter_dict = filter.to_dict()
        assert filter_dict == {"tag": {"$in": ["python", "java", "rust"]}}

    def test_not_in_operator(self):
        """Test 'not in' operator."""
        filter = MetadataFilter()
        filter.add_condition("tag", "not_in", ["deprecated", "archived"])

        filter_dict = filter.to_dict()
        assert filter_dict == {"tag": {"$nin": ["deprecated", "archived"]}}

    def test_string_representation(self):
        """Test string representation of filter."""
        filter = MetadataFilter()
        filter.add_condition("tag", "==", "python")
        filter.add_condition("confidence", ">", 0.9)

        str_repr = str(filter)
        assert "tag == python" in str_repr
        assert "confidence > 0.9" in str_repr
        assert "AND" in str_repr


class TestFilterParser:
    """Test FilterParser class."""

    def test_parse_empty_string(self):
        """Test parsing empty filter string."""
        filter = FilterParser.parse("")

        assert len(filter.conditions) == 0

    def test_parse_single_equality(self):
        """Test parsing single equality filter."""
        filter = FilterParser.parse("tag=python")

        assert len(filter.conditions) == 1
        assert filter.conditions[0].field == "tag"
        assert filter.conditions[0].operator == "=="
        assert filter.conditions[0].value == "python"

    def test_parse_double_equals(self):
        """Test parsing == operator."""
        filter = FilterParser.parse("tag==python")

        assert filter.conditions[0].operator == "=="

    def test_parse_comparison(self):
        """Test parsing comparison operators."""
        filter = FilterParser.parse("confidence>0.9")

        assert filter.conditions[0].field == "confidence"
        assert filter.conditions[0].operator == ">"
        assert filter.conditions[0].value == 0.9

    def test_parse_multiple_filters(self):
        """Test parsing multiple filters (AND logic)."""
        filter = FilterParser.parse("tag=python confidence>0.9 author=Smith")

        assert len(filter.conditions) == 3
        assert filter.conditions[0].field == "tag"
        assert filter.conditions[1].field == "confidence"
        assert filter.conditions[2].field == "author"

    def test_parse_comma_separated_values(self):
        """Test parsing comma-separated values (OR within field)."""
        filter = FilterParser.parse("tag=python,java,rust")

        assert len(filter.conditions) == 1
        assert filter.conditions[0].operator == "in"
        assert filter.conditions[0].value == ["python", "java", "rust"]

    def test_parse_date_value(self):
        """Test parsing date values."""
        filter = FilterParser.parse("date>=2023-01-01")

        assert filter.conditions[0].field == "date"
        assert filter.conditions[0].operator == ">="
        # Value should be ISO format datetime string
        assert "2023-01-01" in filter.conditions[0].value

    def test_parse_boolean_value(self):
        """Test parsing boolean values."""
        filter = FilterParser.parse("archived=false")

        assert filter.conditions[0].value is False

        filter2 = FilterParser.parse("active=true")
        assert filter2.conditions[0].value is True

    def test_parse_integer_value(self):
        """Test parsing integer values."""
        filter = FilterParser.parse("page=42")

        assert filter.conditions[0].value == 42
        assert isinstance(filter.conditions[0].value, int)

    def test_parse_float_value(self):
        """Test parsing float values."""
        filter = FilterParser.parse("confidence=0.95")

        assert filter.conditions[0].value == 0.95
        assert isinstance(filter.conditions[0].value, float)

    def test_parse_cli_filters_single_tag(self):
        """Test parsing CLI filters with single tag."""
        filter = FilterParser.parse_cli_filters(tag="python")

        assert len(filter.conditions) == 1
        assert filter.conditions[0].field == "tag"
        assert filter.conditions[0].value == "python"

    def test_parse_cli_filters_multiple_tags(self):
        """Test parsing CLI filters with multiple tags."""
        filter = FilterParser.parse_cli_filters(tag="python,java,rust")

        assert len(filter.conditions) == 1
        assert filter.conditions[0].operator == "in"
        assert filter.conditions[0].value == ["python", "java", "rust"]

    def test_parse_cli_filters_author(self):
        """Test parsing CLI filters with author."""
        filter = FilterParser.parse_cli_filters(author="Smith")

        assert filter.conditions[0].field == "author"
        assert filter.conditions[0].value == "Smith"

    def test_parse_cli_filters_file_type(self):
        """Test parsing CLI filters with file type."""
        filter = FilterParser.parse_cli_filters(file_type="pdf")

        assert filter.conditions[0].field == "file_type"
        assert filter.conditions[0].value == "pdf"

        # Test with leading dot
        filter2 = FilterParser.parse_cli_filters(file_type=".txt")
        assert filter2.conditions[0].value == "txt"

    def test_parse_cli_filters_date_range(self):
        """Test parsing CLI filters with date range."""
        filter = FilterParser.parse_cli_filters(
            date_after="2023-01-01",
            date_before="2023-12-31"
        )

        assert len(filter.conditions) == 2
        assert filter.conditions[0].field == "date"
        assert filter.conditions[0].operator == ">="
        assert filter.conditions[1].field == "date"
        assert filter.conditions[1].operator == "<="

    def test_parse_cli_filters_confidence_comparison(self):
        """Test parsing CLI filters with confidence comparison."""
        filter = FilterParser.parse_cli_filters(confidence=">0.9")

        assert filter.conditions[0].field == "confidence"
        assert filter.conditions[0].operator == ">"
        assert filter.conditions[0].value == 0.9

        # Test other operators
        filter2 = FilterParser.parse_cli_filters(confidence=">=0.95")
        assert filter2.conditions[0].operator == ">="
        assert filter2.conditions[0].value == 0.95

    def test_parse_cli_filters_confidence_equality(self):
        """Test parsing CLI filters with confidence equality."""
        filter = FilterParser.parse_cli_filters(confidence="0.9")

        assert filter.conditions[0].operator == "=="
        assert filter.conditions[0].value == 0.9

    def test_parse_cli_filters_combined(self):
        """Test parsing CLI filters with multiple parameters."""
        filter = FilterParser.parse_cli_filters(
            tag="python,java",
            author="Smith",
            confidence=">0.9",
            file_type="pdf",
            date_after="2023-01-01"
        )

        assert len(filter.conditions) == 5
        # Check fields are all present
        fields = [c.field for c in filter.conditions]
        assert "tag" in fields
        assert "author" in fields
        assert "confidence" in fields
        assert "file_type" in fields
        assert "date" in fields

    def test_parse_cli_filters_custom_kwargs(self):
        """Test parsing CLI filters with custom kwargs."""
        filter = FilterParser.parse_cli_filters(
            tag="python",
            language="en",
            category="research"
        )

        assert len(filter.conditions) == 3
        fields = [c.field for c in filter.conditions]
        assert "tag" in fields
        assert "language" in fields
        assert "category" in fields

    def test_parse_invalid_filter(self):
        """Test parsing invalid filter expression."""
        # Should log warning but not crash
        filter = FilterParser.parse("invalid_filter_without_operator")

        # Should have no conditions
        assert len(filter.conditions) == 0


class TestFacetedSearch:
    """Test FacetedSearch class."""

    def test_get_facets_placeholder(self):
        """Test get_facets method (placeholder)."""
        # Mock vector store
        mock_store = None

        facets = FacetedSearch.get_facets(mock_store, fields=["tag", "author"])

        # Should return empty dict for now (placeholder)
        assert isinstance(facets, dict)
        assert "tag" in facets
        assert "author" in facets

    def test_count_facet_values_placeholder(self):
        """Test count_facet_values method (placeholder)."""
        # Mock vector store
        mock_store = None

        counts = FacetedSearch.count_facet_values(mock_store, "tag")

        # Should return empty dict for now (placeholder)
        assert isinstance(counts, dict)


class TestConvenienceFunction:
    """Test convenience functions."""

    def test_create_filter(self):
        """Test create_filter convenience function."""
        filter = create_filter(tag="python", confidence=0.9)

        assert len(filter.conditions) == 2
        fields = [c.field for c in filter.conditions]
        assert "tag" in fields
        assert "confidence" in fields

    def test_create_filter_with_comparison(self):
        """Test create_filter with comparison operator."""
        filter = create_filter(confidence=">0.95")

        assert filter.conditions[0].operator == ">"
        assert filter.conditions[0].value == 0.95
