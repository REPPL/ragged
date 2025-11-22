"""Security tests for HIGH-4: SQL/NoSQL injection in metadata filters."""

import pytest
from src.retrieval.metadata_filter import (
    FilterCondition,
    MetadataFilter,
    FilterParser,
    MetadataFilterSecurityError,
    validate_field_name,
    validate_operator,
    sanitize_value,
    ALLOWED_METADATA_FIELDS,
    ALLOWED_OPERATORS,
)


class TestFieldNameValidation:
    """Tests for field name validation (HIGH-4)."""

    def test_valid_field_names_accepted(self):
        """Test that valid field names are accepted."""
        valid_fields = ["tag", "author", "file_type", "confidence", "date"]

        for field in valid_fields:
            # Should not raise
            result = validate_field_name(field)
            assert result == field.lower()

    def test_field_names_normalized_to_lowercase(self):
        """Test that field names are normalized to lowercase."""
        assert validate_field_name("TAG") == "tag"
        assert validate_field_name("Author") == "author"
        assert validate_field_name("File_Type") == "file_type"

    def test_empty_field_name_rejected(self):
        """Test that empty field names are rejected."""
        with pytest.raises(MetadataFilterSecurityError, match="must be a non-empty string"):
            validate_field_name("")

    def test_none_field_name_rejected(self):
        """Test that None field names are rejected."""
        with pytest.raises(MetadataFilterSecurityError, match="must be a non-empty string"):
            validate_field_name(None)

    def test_mongodb_operator_in_field_rejected(self):
        """Test that MongoDB operators in field names are rejected."""
        malicious_fields = [
            "$where",
            "$regex",
            "$gt",
            "$lt",
            "$and",
            "$or",
            "$exists",
            "$text",
        ]

        for field in malicious_fields:
            with pytest.raises(MetadataFilterSecurityError, match="forbidden operator"):
                validate_field_name(field)

    def test_field_not_in_whitelist_rejected(self):
        """Test that fields not in whitelist are rejected."""
        invalid_fields = ["malicious_field", "unknown", "custom_field"]

        for field in invalid_fields:
            with pytest.raises(MetadataFilterSecurityError, match="not in allowed fields"):
                validate_field_name(field)

    def test_field_with_invalid_characters_rejected(self):
        """Test that fields with invalid characters are rejected."""
        invalid_fields = [
            "field-name",  # hyphen
            "field.name",  # dot
            "field name",  # space
            "field@name",  # @
            "field$name",  # $
        ]

        for field in invalid_fields:
            # These will be rejected at whitelist check (not in allowed fields)
            with pytest.raises(MetadataFilterSecurityError, match="not in allowed fields"):
                validate_field_name(field)

    def test_case_insensitive_matching(self):
        """Test that field validation is case-insensitive."""
        # All these should be accepted and normalized
        assert validate_field_name("tag") == "tag"
        assert validate_field_name("TAG") == "tag"
        assert validate_field_name("Tag") == "tag"


class TestOperatorValidation:
    """Tests for operator validation."""

    def test_valid_operators_accepted(self):
        """Test that valid operators are accepted."""
        for op in ALLOWED_OPERATORS:
            # Should not raise
            result = validate_operator(op)
            assert result == op

    def test_invalid_operator_rejected(self):
        """Test that invalid operators are rejected."""
        invalid_ops = ["$gt", "$lt", "$eq", "LIKE", "REGEXP", "~", "!~"]

        for op in invalid_ops:
            with pytest.raises(MetadataFilterSecurityError, match="not allowed"):
                validate_operator(op)


class TestValueSanitization:
    """Tests for value sanitization."""

    def test_string_values_accepted(self):
        """Test that string values are accepted."""
        value = sanitize_value("python", "tag")
        assert value == "python"

    def test_numeric_values_accepted(self):
        """Test that numeric values are accepted."""
        assert sanitize_value(42, "page") == 42
        assert sanitize_value(3.14, "confidence") == 3.14

    def test_boolean_values_accepted(self):
        """Test that boolean values are accepted."""
        assert sanitize_value(True, "status") is True
        assert sanitize_value(False, "status") is False

    def test_none_value_accepted(self):
        """Test that None values are accepted."""
        assert sanitize_value(None, "description") is None

    def test_list_values_accepted(self):
        """Test that list values with primitives are accepted."""
        value = sanitize_value(["python", "java", "rust"], "tag")
        assert value == ["python", "java", "rust"]

    def test_dict_values_rejected(self):
        """Test that dict values are rejected (operator injection)."""
        malicious_value = {"$gt": 10}

        with pytest.raises(MetadataFilterSecurityError, match="Dictionary values not allowed"):
            sanitize_value(malicious_value, "confidence")

    def test_oversized_string_rejected(self):
        """Test that oversized strings are rejected."""
        huge_string = "x" * 10001

        with pytest.raises(MetadataFilterSecurityError, match="limited to 10000 characters"):
            sanitize_value(huge_string, "description")

    def test_oversized_list_rejected(self):
        """Test that oversized lists are rejected."""
        huge_list = list(range(1001))

        with pytest.raises(MetadataFilterSecurityError, match="limited to 1000 items"):
            sanitize_value(huge_list, "tag")

    def test_list_with_non_primitives_rejected(self):
        """Test that lists with non-primitive items are rejected."""
        malicious_list = ["python", {"$gt": 10}]

        with pytest.raises(MetadataFilterSecurityError, match="must be primitive types"):
            sanitize_value(malicious_list, "tag")

    def test_null_bytes_in_string_rejected(self):
        """Test that strings with null bytes are rejected."""
        malicious_string = "python\x00injection"

        with pytest.raises(MetadataFilterSecurityError, match="Null bytes not allowed"):
            sanitize_value(malicious_string, "tag")

    def test_unsupported_types_rejected(self):
        """Test that unsupported types are rejected."""
        import datetime

        with pytest.raises(MetadataFilterSecurityError, match="not allowed"):
            sanitize_value(datetime.datetime.now(), "date")

        with pytest.raises(MetadataFilterSecurityError, match="not allowed"):
            sanitize_value(object(), "field")


class TestFilterConditionValidation:
    """Tests for FilterCondition validation."""

    def test_valid_filter_condition_created(self):
        """Test that valid filter conditions are created."""
        condition = FilterCondition("tag", "==", "python")
        assert condition.field == "tag"
        assert condition.operator == "=="
        assert condition.value == "python"

    def test_field_normalized_to_lowercase(self):
        """Test that field names are normalized."""
        condition = FilterCondition("TAG", "==", "python")
        assert condition.field == "tag"

    def test_malicious_field_rejected(self):
        """Test that malicious field names are rejected."""
        with pytest.raises(MetadataFilterSecurityError, match="forbidden operator"):
            FilterCondition("$where", "==", "value")

    def test_invalid_operator_rejected(self):
        """Test that invalid operators are rejected."""
        with pytest.raises(MetadataFilterSecurityError, match="not allowed"):
            FilterCondition("tag", "$gt", "value")

    def test_malicious_value_rejected(self):
        """Test that malicious values are rejected."""
        with pytest.raises(MetadataFilterSecurityError, match="Dictionary values not allowed"):
            FilterCondition("confidence", ">", {"$gt": 0.9})


class TestMetadataFilterValidation:
    """Tests for MetadataFilter validation."""

    def test_add_valid_condition(self):
        """Test adding valid conditions."""
        filter_obj = MetadataFilter()
        filter_obj.add_condition("tag", "==", "python")
        filter_obj.add_condition("confidence", ">", 0.9)

        assert len(filter_obj.conditions) == 2

    def test_add_malicious_field_rejected(self):
        """Test that adding malicious field is rejected."""
        filter_obj = MetadataFilter()

        with pytest.raises(MetadataFilterSecurityError, match="forbidden operator"):
            filter_obj.add_condition("$where", "==", "value")

    def test_add_malicious_operator_rejected(self):
        """Test that adding malicious operator is rejected."""
        filter_obj = MetadataFilter()

        with pytest.raises(MetadataFilterSecurityError, match="not allowed"):
            filter_obj.add_condition("tag", "$gt", "value")

    def test_to_dict_with_valid_conditions(self):
        """Test to_dict() with valid conditions."""
        filter_obj = MetadataFilter()
        filter_obj.add_condition("tag", "==", "python")
        filter_obj.add_condition("confidence", ">", 0.9)

        result = filter_obj.to_dict()

        # Should produce valid ChromaDB query
        assert "$and" in result
        assert len(result["$and"]) == 2


class TestFilterParserValidation:
    """Tests for FilterParser validation."""

    def test_parse_valid_filter_string(self):
        """Test parsing valid filter strings."""
        filter_obj = FilterParser.parse("tag=python confidence>0.9")

        assert len(filter_obj.conditions) == 2
        assert filter_obj.conditions[0].field == "tag"
        assert filter_obj.conditions[1].field == "confidence"

    def test_parse_malicious_field_skipped(self):
        """Test that malicious fields are skipped with warning."""
        # Should skip malicious field and only parse valid one
        filter_obj = FilterParser.parse("$where=malicious tag=python")

        # Should only have one condition (tag=python)
        assert len(filter_obj.conditions) == 1
        assert filter_obj.conditions[0].field == "tag"

    def test_parse_invalid_operator_skipped(self):
        """Test that invalid operators are skipped."""
        filter_obj = FilterParser.parse("tag$gt=python")

        # Invalid filter should be skipped entirely
        assert len(filter_obj.conditions) == 0

    def test_parse_cli_filters_valid(self):
        """Test parsing valid CLI filters."""
        filter_obj = FilterParser.parse_cli_filters(
            tag="python,java",
            author="Smith",
            confidence=">0.9"
        )

        assert len(filter_obj.conditions) == 3

    def test_parse_cli_filters_with_invalid_field(self):
        """Test that CLI filters with invalid custom fields are rejected."""
        # Using kwargs to pass a malicious field name
        with pytest.raises(MetadataFilterSecurityError, match="not in allowed fields"):
            FilterParser.parse_cli_filters(
                tag="python",
                malicious_field="value"  # Custom field not in whitelist
            )


class TestNoSQLInjectionPrevention:
    """Tests for NoSQL injection attack prevention."""

    def test_mongodb_where_injection_prevented(self):
        """Test that MongoDB $where injection is prevented."""
        with pytest.raises(MetadataFilterSecurityError, match="forbidden operator"):
            FilterCondition("$where", "==", "this.password == 'secret'")

    def test_mongodb_operator_in_value_prevented(self):
        """Test that MongoDB operators in values are prevented."""
        with pytest.raises(MetadataFilterSecurityError, match="Dictionary values not allowed"):
            FilterCondition("confidence", "==", {"$gt": 0})

    def test_regex_injection_prevented(self):
        """Test that regex injection via field names is prevented."""
        with pytest.raises(MetadataFilterSecurityError, match="forbidden operator"):
            FilterCondition("$regex", "==", ".*")

    def test_field_name_whitelist_enforced(self):
        """Test that field name whitelist is strictly enforced."""
        # Try to inject via custom field not in whitelist
        with pytest.raises(MetadataFilterSecurityError, match="not in allowed fields"):
            FilterCondition("admin", "==", "true")

    def test_operator_whitelist_enforced(self):
        """Test that operator whitelist is strictly enforced."""
        # Try to use MongoDB-specific operators
        with pytest.raises(MetadataFilterSecurityError, match="not allowed"):
            FilterCondition("tag", "$regex", "python.*")

    def test_complex_injection_attempt_prevented(self):
        """Test that complex injection attempts are prevented."""
        # Attempt 1: Nested operators in list value
        with pytest.raises(MetadataFilterSecurityError, match="must be primitive types"):
            FilterCondition("confidence", "in", [0.9, {"$gt": 0}])

        # Attempt 2: Forbidden field with valid operator
        with pytest.raises(MetadataFilterSecurityError, match="forbidden operator"):
            FilterCondition("$exists", "==", True)

        # Attempt 3: Valid field with forbidden operator
        with pytest.raises(MetadataFilterSecurityError, match="not allowed"):
            FilterCondition("tag", "$in", ["python"])

    def test_dos_via_oversized_values_prevented(self):
        """Test that DoS via oversized values is prevented."""
        # Oversized string
        with pytest.raises(MetadataFilterSecurityError, match="limited to 10000 characters"):
            FilterCondition("description", "==", "x" * 10001)

        # Oversized list
        with pytest.raises(MetadataFilterSecurityError, match="limited to 1000 items"):
            FilterCondition("tag", "in", list(range(1001)))

    def test_null_byte_injection_prevented(self):
        """Test that null byte injection is prevented."""
        with pytest.raises(MetadataFilterSecurityError, match="Null bytes not allowed"):
            FilterCondition("tag", "==", "python\x00admin")

    def test_filter_combination_attack_prevented(self):
        """Test that combined filter attacks are prevented."""
        filter_obj = MetadataFilter()

        # Add valid condition
        filter_obj.add_condition("tag", "==", "python")

        # Attempt to add malicious condition
        with pytest.raises(MetadataFilterSecurityError):
            filter_obj.add_condition("$where", "==", "malicious")

        # Should still have only one valid condition
        assert len(filter_obj.conditions) == 1
        assert filter_obj.conditions[0].field == "tag"


class TestEdgeCases:
    """Tests for edge cases and boundary conditions."""

    def test_maximum_valid_string_length_accepted(self):
        """Test that maximum valid string length is accepted."""
        max_string = "x" * 10000
        value = sanitize_value(max_string, "description")
        assert len(value) == 10000

    def test_maximum_valid_list_length_accepted(self):
        """Test that maximum valid list length is accepted."""
        max_list = list(range(1000))
        value = sanitize_value(max_list, "tag")
        assert len(value) == 1000

    def test_empty_string_value_accepted(self):
        """Test that empty string values are accepted."""
        value = sanitize_value("", "tag")
        assert value == ""

    def test_empty_list_value_accepted(self):
        """Test that empty list values are accepted."""
        value = sanitize_value([], "tag")
        assert value == []

    def test_unicode_values_accepted(self):
        """Test that unicode values are accepted."""
        value = sanitize_value("日本語", "tag")
        assert value == "日本語"

    def test_mixed_case_field_names_normalized(self):
        """Test that mixed case field names are normalized consistently."""
        conditions = [
            FilterCondition("TAG", "==", "python"),
            FilterCondition("tag", "==", "java"),
            FilterCondition("Tag", "==", "rust"),
        ]

        # All should be normalized to lowercase
        for condition in conditions:
            assert condition.field == "tag"
