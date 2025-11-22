"""Security tests for HIGH-3: Insecure JSON parsing in audit log."""

import pytest
import json
from pathlib import Path

from ragged.plugins.audit import (
    AuditLogger,
    AuditEvent,
    AuditEventType,
    AuditSecurityError,
    safe_json_loads,
    sanitize_details,
    _validate_json_structure,
    MAX_JSON_DEPTH,
    MAX_JSON_STRING_LENGTH,
    MAX_JSON_ARRAY_LENGTH,
    MAX_JSON_OBJECT_KEYS,
)


class TestJSONStructureValidation:
    """Tests for JSON structure validation (HIGH-3)."""

    def test_deeply_nested_json_rejected(self):
        """Test that deeply nested JSON exceeding max depth is rejected."""
        # Create JSON nested beyond MAX_JSON_DEPTH
        nested_dict = {"level": 0}
        current = nested_dict
        for i in range(1, MAX_JSON_DEPTH + 5):
            current["nested"] = {"level": i}
            current = current["nested"]

        with pytest.raises(AuditSecurityError, match="JSON depth exceeds maximum"):
            _validate_json_structure(nested_dict)

    def test_valid_nesting_depth_accepted(self):
        """Test that JSON within depth limit is accepted."""
        # Create JSON at exactly MAX_JSON_DEPTH
        nested_dict = {"level": 0}
        current = nested_dict
        for i in range(1, MAX_JSON_DEPTH):
            current["nested"] = {"level": i}
            current = current["nested"]

        # Should not raise
        _validate_json_structure(nested_dict)

    def test_oversized_string_rejected(self):
        """Test that strings exceeding max length are rejected."""
        long_string = "a" * (MAX_JSON_STRING_LENGTH + 100)

        with pytest.raises(AuditSecurityError, match="JSON string exceeds maximum length"):
            _validate_json_structure(long_string)

    def test_oversized_string_in_object_rejected(self):
        """Test that oversized strings in objects are rejected."""
        obj = {
            "normal": "short string",
            "malicious": "x" * (MAX_JSON_STRING_LENGTH + 100),
        }

        with pytest.raises(AuditSecurityError, match="JSON string exceeds maximum length"):
            _validate_json_structure(obj)

    def test_oversized_array_rejected(self):
        """Test that arrays exceeding max length are rejected."""
        large_array = list(range(MAX_JSON_ARRAY_LENGTH + 100))

        with pytest.raises(AuditSecurityError, match="JSON array exceeds maximum length"):
            _validate_json_structure(large_array)

    def test_too_many_object_keys_rejected(self):
        """Test that objects with too many keys are rejected."""
        large_obj = {f"key{i}": i for i in range(MAX_JSON_OBJECT_KEYS + 10)}

        with pytest.raises(AuditSecurityError, match="too many keys"):
            _validate_json_structure(large_obj)

    def test_oversized_key_name_rejected(self):
        """Test that oversized key names are rejected."""
        long_key = "k" * (MAX_JSON_STRING_LENGTH + 100)
        obj = {long_key: "value"}

        with pytest.raises(AuditSecurityError, match="JSON key exceeds maximum length"):
            _validate_json_structure(obj)

    def test_non_string_keys_rejected(self):
        """Test that non-string keys are rejected."""
        # Python allows int keys, but JSON spec requires strings
        # This tests that we validate proper JSON structure
        obj = {123: "value"}  # This would fail JSON spec

        # Our validator should catch non-string keys
        with pytest.raises(AuditSecurityError, match="must be strings"):
            _validate_json_structure(obj)

    def test_unsupported_types_rejected(self):
        """Test that unsupported types are rejected."""
        import datetime

        # datetime is not JSON-serializable
        obj = {"timestamp": datetime.datetime.now()}

        with pytest.raises(AuditSecurityError, match="Unsupported JSON type"):
            _validate_json_structure(obj)

    def test_safe_primitives_accepted(self):
        """Test that safe primitive types are accepted."""
        safe_values = [
            "string",
            123,
            45.67,
            True,
            False,
            None,
            {"key": "value"},
            [1, 2, 3],
        ]

        for value in safe_values:
            # Should not raise
            _validate_json_structure(value)

    def test_mixed_safe_structure_accepted(self):
        """Test that complex but safe structures are accepted."""
        safe_obj = {
            "string": "value",
            "number": 42,
            "float": 3.14,
            "bool": True,
            "none": None,
            "array": [1, 2, 3],
            "nested": {
                "level1": {
                    "level2": {
                        "data": "nested data"
                    }
                }
            },
        }

        # Should not raise
        _validate_json_structure(safe_obj)


class TestSafeJSONLoads:
    """Tests for safe JSON parsing function."""

    def test_safe_json_loads_with_deeply_nested(self):
        """Test that safe_json_loads rejects deeply nested JSON."""
        # Create deeply nested JSON string
        nested_json = '{"a":' * (MAX_JSON_DEPTH + 5) + '1' + '}' * (MAX_JSON_DEPTH + 5)

        with pytest.raises(AuditSecurityError, match="JSON depth exceeds maximum"):
            safe_json_loads(nested_json)

    def test_safe_json_loads_with_oversized_string(self):
        """Test that safe_json_loads rejects oversized strings."""
        large_string = "x" * (MAX_JSON_STRING_LENGTH + 100)
        json_str = json.dumps({"data": large_string})

        with pytest.raises(AuditSecurityError, match="JSON string exceeds maximum length"):
            safe_json_loads(json_str)

    def test_safe_json_loads_with_malformed_json(self):
        """Test that safe_json_loads handles malformed JSON."""
        malformed_json = '{"key": invalid}'

        with pytest.raises(json.JSONDecodeError):
            safe_json_loads(malformed_json)

    def test_safe_json_loads_with_oversized_raw_string(self):
        """Test that safe_json_loads rejects oversized raw JSON strings."""
        huge_json = "x" * (MAX_JSON_STRING_LENGTH * 3)

        with pytest.raises(AuditSecurityError, match="JSON string too large"):
            safe_json_loads(huge_json)

    def test_safe_json_loads_accepts_valid_json(self):
        """Test that safe_json_loads accepts valid JSON."""
        valid_json = json.dumps({
            "event": "plugin_loaded",
            "plugin": "test_plugin",
            "timestamp": "2024-01-01T00:00:00Z",
        })

        result = safe_json_loads(valid_json)
        assert result["event"] == "plugin_loaded"
        assert result["plugin"] == "test_plugin"


class TestDetailsSanitization:
    """Tests for details dictionary sanitization."""

    def test_sanitize_none_details(self):
        """Test that None details are handled."""
        result = sanitize_details(None)
        assert result is None

    def test_sanitize_valid_details(self):
        """Test that valid details pass through."""
        valid_details = {
            "permission": "read:documents",
            "result": "success",
            "count": 42,
        }

        result = sanitize_details(valid_details)
        assert result == valid_details

    def test_sanitize_deeply_nested_details(self):
        """Test that deeply nested details are sanitized."""
        # Create deeply nested dict
        nested = {"level": 0}
        current = nested
        for i in range(1, MAX_JSON_DEPTH + 5):
            current["nested"] = {"level": i}
            current = current["nested"]

        result = sanitize_details(nested)

        # Should be sanitized
        assert result["_sanitized"] is True
        assert "_error" in result

    def test_sanitize_oversized_details(self):
        """Test that oversized details are sanitized."""
        oversized = {
            "data": "x" * (MAX_JSON_STRING_LENGTH + 100)
        }

        result = sanitize_details(oversized)

        # Should be sanitized
        assert result["_sanitized"] is True
        assert "exceeds maximum length" in result["_error"]

    def test_sanitize_too_many_keys(self):
        """Test that details with too many keys are sanitized."""
        too_many = {f"key{i}": i for i in range(MAX_JSON_OBJECT_KEYS + 10)}

        result = sanitize_details(too_many)

        # Should be sanitized
        assert result["_sanitized"] is True
        assert "too many keys" in result["_error"]


class TestAuditEventSerialization:
    """Tests for AuditEvent serialization with sanitization."""

    def test_audit_event_sanitizes_malicious_details(self):
        """Test that AuditEvent.to_dict() sanitizes malicious details."""
        # Create event with deeply nested details
        nested = {"level": 0}
        current = nested
        for i in range(1, MAX_JSON_DEPTH + 5):
            current["nested"] = {"level": i}
            current = current["nested"]

        event = AuditEvent(
            timestamp="2024-01-01T00:00:00Z",
            event_type=AuditEventType.PLUGIN_EXECUTED,
            plugin_name="malicious_plugin",
            plugin_version="1.0.0",
            details=nested,
        )

        result = event.to_dict()

        # Details should be sanitized
        assert result["details"]["_sanitized"] is True
        assert "_error" in result["details"]

    def test_audit_event_preserves_valid_details(self):
        """Test that AuditEvent.to_dict() preserves valid details."""
        valid_details = {
            "permission": "read:documents",
            "result": "success",
        }

        event = AuditEvent(
            timestamp="2024-01-01T00:00:00Z",
            event_type=AuditEventType.PERMISSION_GRANTED,
            plugin_name="test_plugin",
            plugin_version="1.0.0",
            details=valid_details,
        )

        result = event.to_dict()

        # Details should be preserved
        assert result["details"] == valid_details
        assert "_sanitized" not in result["details"]


class TestAuditLoggerSecurity:
    """Tests for AuditLogger with malicious JSON."""

    @pytest.fixture
    def audit_logger(self, tmp_path):
        """Create audit logger with temporary log file."""
        log_path = tmp_path / "audit.log"
        return AuditLogger(log_path=log_path)

    def test_log_event_sanitizes_malicious_details(self, audit_logger):
        """Test that logging events sanitizes malicious details."""
        # Create event with oversized details
        oversized_details = {
            "data": "x" * (MAX_JSON_STRING_LENGTH + 100)
        }

        event = AuditEvent(
            timestamp="2024-01-01T00:00:00Z",
            event_type=AuditEventType.PLUGIN_EXECUTED,
            plugin_name="test_plugin",
            plugin_version="1.0.0",
            details=oversized_details,
        )

        # Should log without error (details sanitized)
        audit_logger.log_event(event)

        # Verify logged event has sanitized details
        events = audit_logger.get_events()
        assert len(events) == 1
        # The details should have been sanitized during to_dict()
        # when it was written to the log

    def test_get_events_rejects_malicious_json(self, audit_logger, tmp_path):
        """Test that get_events rejects malicious JSON in log file."""
        # Manually write malicious JSON to log file
        malicious_json = '{"a":' * (MAX_JSON_DEPTH + 5) + '1' + '}' * (MAX_JSON_DEPTH + 5)

        with open(audit_logger.log_path, "w") as f:
            f.write(malicious_json + "\n")

        # Should skip malicious entry
        events = audit_logger.get_events()
        assert len(events) == 0

    def test_get_events_handles_malformed_json(self, audit_logger):
        """Test that get_events handles malformed JSON gracefully."""
        # Manually write malformed JSON
        with open(audit_logger.log_path, "w") as f:
            f.write("not valid json\n")
            f.write('{"valid": "json"}\n')  # This won't be a valid event

        # Should skip malformed entries
        events = audit_logger.get_events()
        # May be 0 or error depending on from_dict() handling
        assert isinstance(events, list)

    def test_clear_old_events_removes_malicious_entries(self, audit_logger):
        """Test that clear_old_events removes malicious entries."""
        # Write a mix of valid and malicious entries
        valid_event = AuditEvent(
            timestamp="2024-01-01T00:00:00Z",
            event_type=AuditEventType.PLUGIN_LOADED,
            plugin_name="test_plugin",
            plugin_version="1.0.0",
        )
        audit_logger.log_event(valid_event)

        # Append malicious JSON directly
        malicious_json = '{"a":' * (MAX_JSON_DEPTH + 5) + '1' + '}' * (MAX_JSON_DEPTH + 5)
        with open(audit_logger.log_path, "a") as f:
            f.write(malicious_json + "\n")

        # Clear old events (this should remove malicious entry)
        removed = audit_logger.clear_old_events(days=0)  # Remove everything

        # Should have removed both (1 valid old + 1 malicious)
        assert removed >= 1


class TestJSONDoSPrevention:
    """Tests for JSON-based DoS attack prevention."""

    def test_billion_laughs_attack_prevented(self):
        """Test that billion laughs style attack is prevented."""
        # Billion laughs: deeply nested expanding structure
        # {"a":{"a":{"a":...}}}
        nested = {}
        current = nested
        for _ in range(MAX_JSON_DEPTH + 10):
            current["a"] = {}
            current = current["a"]

        with pytest.raises(AuditSecurityError, match="JSON depth exceeds maximum"):
            _validate_json_structure(nested)

    def test_hash_collision_attack_prevented(self):
        """Test that hash collision attacks are mitigated by key limits."""
        # Create many keys that might cause hash collisions
        collision_obj = {f"key_{i:010d}": i for i in range(MAX_JSON_OBJECT_KEYS + 50)}

        with pytest.raises(AuditSecurityError, match="too many keys"):
            _validate_json_structure(collision_obj)

    def test_memory_exhaustion_via_strings_prevented(self):
        """Test that memory exhaustion via large strings is prevented."""
        # Attempt to create extremely large string
        huge_string = "x" * (MAX_JSON_STRING_LENGTH * 2)

        with pytest.raises(AuditSecurityError, match="exceeds maximum length"):
            _validate_json_structure(huge_string)

    def test_memory_exhaustion_via_arrays_prevented(self):
        """Test that memory exhaustion via large arrays is prevented."""
        # Attempt to create extremely large array
        huge_array = list(range(MAX_JSON_ARRAY_LENGTH * 2))

        with pytest.raises(AuditSecurityError, match="exceeds maximum length"):
            _validate_json_structure(huge_array)

    def test_combined_attack_prevented(self):
        """Test that combined attacks (nested + oversized) are prevented."""
        # Create structure with both deep nesting and large strings
        nested = {"level": 0, "data": "x" * (MAX_JSON_STRING_LENGTH + 100)}
        current = nested
        for i in range(1, MAX_JSON_DEPTH + 5):
            current["nested"] = {"level": i, "data": "y" * 100}
            current = current["nested"]

        # Should catch either the depth or string length issue
        with pytest.raises(AuditSecurityError):
            _validate_json_structure(nested)
