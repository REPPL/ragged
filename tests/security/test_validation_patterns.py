"""Security tests for MEDIUM-2: Enhanced validation patterns."""

import pytest
from pathlib import Path

from src.utils.validation import (
    ValidationError,
    validate_string,
    validate_integer,
    validate_float,
    validate_list,
    validate_email,
    validate_url,
    validate_path,
    validate_filename,
    validate_version,
    validate_plugin_name,
    validate_enum,
)


class TestStringValidation:
    """Tests for string validation."""

    def test_valid_string(self):
        """Test valid string passes validation."""
        result = validate_string("test string", min_length=5, max_length=20)
        assert result == "test string"

    def test_string_too_short(self):
        """Test string below minimum length fails."""
        with pytest.raises(ValidationError, match="at least 10 characters"):
            validate_string("short", min_length=10)

    def test_string_too_long(self):
        """Test string exceeding maximum length fails."""
        with pytest.raises(ValidationError, match="must not exceed 5 characters"):
            validate_string("too long", max_length=5)

    def test_null_bytes_rejected(self):
        """Test strings with null bytes are rejected."""
        with pytest.raises(ValidationError, match="null bytes"):
            validate_string("test\x00string")

    def test_non_string_rejected(self):
        """Test non-string values are rejected."""
        with pytest.raises(ValidationError, match="must be a string"):
            validate_string(123)


class TestIntegerValidation:
    """Tests for integer validation."""

    def test_valid_integer(self):
        """Test valid integer passes validation."""
        result = validate_integer(42, min_value=0, max_value=100)
        assert result == 42

    def test_integer_below_minimum(self):
        """Test integer below minimum fails."""
        with pytest.raises(ValidationError, match="at least 10"):
            validate_integer(5, min_value=10)

    def test_integer_above_maximum(self):
        """Test integer above maximum fails."""
        with pytest.raises(ValidationError, match="not exceed 100"):
            validate_integer(150, max_value=100)

    def test_boolean_rejected(self):
        """Test boolean is not accepted as integer."""
        with pytest.raises(ValidationError, match="must be an integer"):
            validate_integer(True)

    def test_float_rejected(self):
        """Test float is rejected for integer validation."""
        with pytest.raises(ValidationError, match="must be an integer"):
            validate_integer(3.14)


class TestFloatValidation:
    """Tests for float validation."""

    def test_valid_float(self):
        """Test valid float passes validation."""
        result = validate_float(3.14, min_value=0.0, max_value=10.0)
        assert result == 3.14

    def test_integer_accepted_as_float(self):
        """Test integer is accepted and converted to float."""
        result = validate_float(5, min_value=0.0, max_value=10.0)
        assert result == 5.0
        assert isinstance(result, float)

    def test_float_below_minimum(self):
        """Test float below minimum fails."""
        with pytest.raises(ValidationError, match="at least 1.0"):
            validate_float(0.5, min_value=1.0)

    def test_float_above_maximum(self):
        """Test float above maximum fails."""
        with pytest.raises(ValidationError, match="not exceed 1.0"):
            validate_float(1.5, max_value=1.0)


class TestListValidation:
    """Tests for list validation."""

    def test_valid_list(self):
        """Test valid list passes validation."""
        result = validate_list([1, 2, 3], min_length=1, max_length=10)
        assert result == [1, 2, 3]

    def test_list_too_short(self):
        """Test list below minimum length fails."""
        with pytest.raises(ValidationError, match="at least 3 items"):
            validate_list([1], min_length=3)

    def test_list_too_long(self):
        """Test list exceeding maximum length fails."""
        with pytest.raises(ValidationError, match="not exceed 5 items"):
            validate_list([1, 2, 3, 4, 5, 6], max_length=5)

    def test_item_type_validation(self):
        """Test list item type validation."""
        with pytest.raises(ValidationError, match="must be str"):
            validate_list([1, 2, "three"], item_type=str)

    def test_valid_item_types(self):
        """Test list with valid item types passes."""
        result = validate_list(["one", "two", "three"], item_type=str)
        assert result == ["one", "two", "three"]


class TestEmailValidation:
    """Tests for email validation."""

    def test_valid_email(self):
        """Test valid email passes validation."""
        result = validate_email("user@example.com")
        assert result == "user@example.com"

    def test_email_normalized_to_lowercase(self):
        """Test email is normalized to lowercase."""
        result = validate_email("User@Example.COM")
        assert result == "user@example.com"

    def test_invalid_email_format(self):
        """Test invalid email format fails."""
        invalid_emails = [
            "notanemail",
            "@example.com",
            "user@",
            "user@@example.com",
            "user@example",
        ]

        for email in invalid_emails:
            with pytest.raises(ValidationError, match="not a valid email"):
                validate_email(email)


class TestURLValidation:
    """Tests for URL validation."""

    def test_valid_http_url(self):
        """Test valid HTTP URL passes validation."""
        result = validate_url("http://example.com")
        assert result == "http://example.com"

    def test_valid_https_url(self):
        """Test valid HTTPS URL passes validation."""
        result = validate_url("https://example.com/path?query=value")
        assert result == "https://example.com/path?query=value"

    def test_url_with_custom_scheme(self):
        """Test URL with custom allowed scheme."""
        result = validate_url("ftp://example.com", allowed_schemes=["ftp"])
        assert result == "ftp://example.com"

    def test_disallowed_scheme_rejected(self):
        """Test URL with disallowed scheme is rejected."""
        with pytest.raises(ValidationError, match="scheme must be one of"):
            validate_url("ftp://example.com")  # ftp not in default schemes

    def test_invalid_url_rejected(self):
        """Test invalid URL is rejected."""
        with pytest.raises(ValidationError, match="not a valid URL"):
            validate_url("not-a-url")


class TestPathValidation:
    """Tests for path validation."""

    def test_valid_path_string(self):
        """Test valid path string is converted to Path."""
        result = validate_path("/tmp/test.txt", allow_absolute=True)
        assert isinstance(result, Path)

    def test_valid_path_object(self):
        """Test valid Path object passes."""
        path = Path("/tmp/test.txt")
        result = validate_path(path, allow_absolute=True)
        assert result == path.resolve()

    def test_absolute_path_rejected_when_not_allowed(self):
        """Test absolute path is rejected when not allowed."""
        with pytest.raises(ValidationError, match="must be a relative path"):
            validate_path("/tmp/test.txt", allow_absolute=False)

    def test_relative_path_rejected_when_not_allowed(self):
        """Test relative path is rejected when not allowed."""
        with pytest.raises(ValidationError, match="must be an absolute path"):
            validate_path("test.txt", allow_relative=False)

    def test_nonexistent_path_rejected_when_must_exist(self, tmp_path):
        """Test non-existent path is rejected when must_exist=True."""
        nonexistent = tmp_path / "does_not_exist.txt"
        with pytest.raises(ValidationError, match="does not exist"):
            validate_path(nonexistent, must_exist=True)

    def test_existing_path_passes(self, tmp_path):
        """Test existing path passes when must_exist=True."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("test")

        result = validate_path(test_file, must_exist=True)
        assert result.exists()


class TestFilenameValidation:
    """Tests for filename validation."""

    def test_valid_filename(self):
        """Test valid filename passes validation."""
        result = validate_filename("test.txt")
        assert result == "test.txt"

    def test_filename_with_dashes_and_underscores(self):
        """Test filename with dashes and underscores is accepted."""
        result = validate_filename("test_file-name.txt")
        assert result == "test_file-name.txt"

    def test_filename_with_path_separator_rejected(self):
        """Test filename with path separator is rejected."""
        with pytest.raises(ValidationError, match="must not contain path separators"):
            validate_filename("path/to/file.txt")

        with pytest.raises(ValidationError, match="must not contain path separators"):
            validate_filename("path\\to\\file.txt")

    def test_hidden_file_rejected(self):
        """Test hidden file (starting with dot) is rejected."""
        with pytest.raises(ValidationError, match="must not be a hidden"):
            validate_filename(".hidden")

    def test_special_names_rejected(self):
        """Test special file names are rejected."""
        with pytest.raises(ValidationError, match="must not be a hidden or special"):
            validate_filename(".")

        with pytest.raises(ValidationError, match="must not be a hidden or special"):
            validate_filename("..")

    def test_filename_with_invalid_characters_rejected(self):
        """Test filename with invalid characters is rejected."""
        invalid_names = [
            "file@name.txt",
            "file name.txt",  # space
            "file?name.txt",
        ]

        for name in invalid_names:
            with pytest.raises(ValidationError, match="invalid characters"):
                validate_filename(name)


class TestVersionValidation:
    """Tests for version validation."""

    def test_valid_semantic_version(self):
        """Test valid semantic version passes."""
        valid_versions = ["1.0.0", "1.2.3", "10.20.30"]

        for version in valid_versions:
            result = validate_version(version)
            assert result == version

    def test_valid_prerelease_version(self):
        """Test valid prerelease version passes."""
        result = validate_version("1.0.0-beta")
        assert result == "1.0.0-beta"

        result = validate_version("2.1.0-alpha1")
        assert result == "2.1.0-alpha1"

    def test_invalid_version_format_rejected(self):
        """Test invalid version formats are rejected."""
        # Versions that fail pattern check
        invalid_versions = [
            "v1.0.0",  # prefix not allowed
            "1.0.0.0",  # too many parts
            "1.x.0",  # non-numeric
        ]

        for version in invalid_versions:
            with pytest.raises(ValidationError, match="semantic versioning"):
                validate_version(version)

        # Version that's too short (fails length check first)
        with pytest.raises(ValidationError, match="at least 5 characters"):
            validate_version("1.0")


class TestPluginNameValidation:
    """Tests for plugin name validation."""

    def test_valid_plugin_name(self):
        """Test valid plugin name passes."""
        result = validate_plugin_name("embedder.custom_embedder")
        assert result == "embedder.custom_embedder"

    def test_plugin_name_with_numbers(self):
        """Test plugin name with numbers is accepted."""
        result = validate_plugin_name("retriever.bm25_retriever")
        assert result == "retriever.bm25_retriever"

    def test_invalid_plugin_name_format_rejected(self):
        """Test invalid plugin name formats are rejected."""
        invalid_names = [
            "PluginName",  # uppercase
            "plugin",  # missing type prefix
            "plugin.Name",  # uppercase in name
            "plugin.name-with-dash",  # hyphen not allowed
            "plugin.name.extra",  # too many parts
        ]

        for name in invalid_names:
            with pytest.raises(ValidationError, match="must follow format"):
                validate_plugin_name(name)


class TestEnumValidation:
    """Tests for enum validation."""

    def test_valid_enum_value(self):
        """Test valid enum value passes."""
        result = validate_enum("option1", ["option1", "option2", "option3"])
        assert result == "option1"

    def test_invalid_enum_value_rejected(self):
        """Test invalid enum value is rejected."""
        with pytest.raises(ValidationError, match="must be one of"):
            validate_enum("invalid", ["option1", "option2"])

    def test_enum_with_different_types(self):
        """Test enum with different types."""
        result = validate_enum(42, [10, 20, 42, 100])
        assert result == 42

        with pytest.raises(ValidationError, match="must be one of"):
            validate_enum(50, [10, 20, 42, 100])


class TestValidationErrorMessages:
    """Tests for validation error messages."""

    def test_custom_field_name_in_error(self):
        """Test custom field name appears in error messages."""
        try:
            validate_string("", min_length=5, field_name="Username")
            assert False, "Should have raised ValidationError"
        except ValidationError as e:
            assert "Username" in str(e)
            assert "at least 5 characters" in str(e)

    def test_error_provides_helpful_context(self):
        """Test error messages provide helpful context."""
        try:
            validate_integer(150, max_value=100, field_name="Age")
            assert False, "Should have raised ValidationError"
        except ValidationError as e:
            assert "Age" in str(e)
            assert "100" in str(e)
            assert "not exceed" in str(e)


class TestSecurityValidation:
    """Tests for security-critical validations."""

    def test_sql_injection_patterns_in_strings(self):
        """Test SQL injection patterns are handled as regular strings."""
        # Validation shouldn't specifically block SQL patterns,
        # but length/null byte checks should catch most issues
        malicious_strings = [
            "'; DROP TABLE users; --",
            "1' OR '1'='1",
        ]

        for s in malicious_strings:
            # Should pass basic validation (no null bytes, within length)
            result = validate_string(s, max_length=1000)
            assert result == s

    def test_path_traversal_in_filename(self):
        """Test path traversal attempts are blocked in filenames."""
        with pytest.raises(ValidationError, match="path separators"):
            validate_filename("../../../etc/passwd")

        with pytest.raises(ValidationError, match="path separators"):
            validate_filename("..\\..\\..\\windows\\system32")

    def test_javascript_injection_in_strings(self):
        """Test JavaScript injection patterns."""
        # Similar to SQL, we don't specifically block JS patterns
        js_pattern = "<script>alert('XSS')</script>"
        result = validate_string(js_pattern, max_length=1000)
        assert result == js_pattern

    def test_command_injection_patterns(self):
        """Test command injection patterns."""
        # Validation should handle as regular strings
        cmd_patterns = [
            "test; rm -rf /",
            "test && malicious_command",
            "test | cat /etc/passwd",
        ]

        for pattern in cmd_patterns:
            # Should pass (context-specific validation needed for actual command execution)
            result = validate_string(pattern, max_length=1000)
            assert result == pattern
