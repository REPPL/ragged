"""Audit logging for plugin security events.

Comprehensive logging of all plugin actions for security monitoring
and forensic analysis.

SECURITY FIX (HIGH-3): Safe JSON parsing with depth and size limits
"""

import json
import logging
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# SECURITY FIX (HIGH-3): JSON parsing limits to prevent DoS
MAX_JSON_DEPTH = 10  # Maximum nesting depth for JSON structures
MAX_JSON_STRING_LENGTH = 10000  # Maximum length for string values
MAX_JSON_ARRAY_LENGTH = 1000  # Maximum array length
MAX_JSON_OBJECT_KEYS = 100  # Maximum keys in object


class AuditSecurityError(Exception):
    """Raised when audit log parsing encounters malicious data."""

    pass


def _validate_json_structure(obj: Any, depth: int = 0) -> None:
    """Validate JSON structure against security limits.

    SECURITY FIX (HIGH-3): Prevents DoS via deeply nested or oversized JSON.

    Args:
        obj: Object to validate
        depth: Current nesting depth

    Raises:
        AuditSecurityError: If structure violates security limits
    """
    if depth > MAX_JSON_DEPTH:
        raise AuditSecurityError(f"JSON depth exceeds maximum of {MAX_JSON_DEPTH}")

    if isinstance(obj, dict):
        if len(obj) > MAX_JSON_OBJECT_KEYS:
            raise AuditSecurityError(f"JSON object has too many keys (max {MAX_JSON_OBJECT_KEYS})")
        for key, value in obj.items():
            if not isinstance(key, str):
                raise AuditSecurityError("JSON object keys must be strings")
            if len(key) > MAX_JSON_STRING_LENGTH:
                raise AuditSecurityError(f"JSON key exceeds maximum length of {MAX_JSON_STRING_LENGTH}")
            _validate_json_structure(value, depth + 1)

    elif isinstance(obj, list):
        if len(obj) > MAX_JSON_ARRAY_LENGTH:
            raise AuditSecurityError(f"JSON array exceeds maximum length of {MAX_JSON_ARRAY_LENGTH}")
        for item in obj:
            _validate_json_structure(item, depth + 1)

    elif isinstance(obj, str):
        if len(obj) > MAX_JSON_STRING_LENGTH:
            raise AuditSecurityError(f"JSON string exceeds maximum length of {MAX_JSON_STRING_LENGTH}")

    elif isinstance(obj, (int, float, bool, type(None))):
        # Primitives are safe
        pass

    else:
        raise AuditSecurityError(f"Unsupported JSON type: {type(obj).__name__}")


def safe_json_loads(json_str: str) -> dict[str, Any]:
    """Safely parse JSON with structure validation.

    SECURITY FIX (HIGH-3): Validates JSON structure before and after parsing.

    Args:
        json_str: JSON string to parse

    Returns:
        Parsed and validated JSON object

    Raises:
        AuditSecurityError: If JSON is malicious or violates limits
        json.JSONDecodeError: If JSON is malformed
    """
    # Pre-validation: check raw string length
    if len(json_str) > MAX_JSON_STRING_LENGTH * 2:
        raise AuditSecurityError("JSON string too large")

    # Parse JSON
    try:
        obj = json.loads(json_str)
    except json.JSONDecodeError as e:
        raise json.JSONDecodeError(f"Invalid JSON: {e.msg}", e.doc, e.pos)

    # Post-validation: validate structure
    _validate_json_structure(obj)

    return obj


def sanitize_details(details: dict[str, Any] | None) -> dict[str, Any] | None:
    """Sanitize details dictionary for safe logging.

    SECURITY FIX (HIGH-3): Validates and sanitizes details before logging.

    Args:
        details: Details dictionary to sanitize

    Returns:
        Sanitized details or None if invalid
    """
    if details is None:
        return None

    try:
        # Validate structure
        _validate_json_structure(details)
        return details
    except AuditSecurityError as e:
        logger.warning(f"Sanitizing malicious details: {e}")
        return {"_sanitized": True, "_error": str(e)}


class AuditEventType(Enum):
    """Types of audit events."""

    PLUGIN_LOADED = "plugin_loaded"
    PLUGIN_EXECUTED = "plugin_executed"
    PLUGIN_FAILED = "plugin_failed"
    PERMISSION_REQUESTED = "permission_requested"
    PERMISSION_GRANTED = "permission_granted"
    PERMISSION_DENIED = "permission_denied"
    PERMISSION_REVOKED = "permission_revoked"
    PERMISSION_VIOLATION = "permission_violation"
    SANDBOX_VIOLATION = "sandbox_violation"
    NETWORK_ACCESS_ATTEMPTED = "network_access_attempted"
    FILE_ACCESS = "file_access"
    MEMORY_ACCESS = "memory_access"
    CONFIG_CHANGE = "config_change"


@dataclass
class AuditEvent:
    """Individual audit event.

    SECURITY FIX (HIGH-3): Sanitizes details field to prevent malicious JSON.
    """

    timestamp: str
    event_type: AuditEventType
    plugin_name: str
    plugin_version: str
    user_id: str | None = None
    details: dict[str, Any] | None = None
    result: str = "success"
    duration_ms: int = 0

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialisation (with sanitization).

        SECURITY FIX (HIGH-3): Sanitizes details before serialisation.
        """
        data = {
            "timestamp": self.timestamp,
            "event": self.event_type.value,
            "plugin": self.plugin_name,
            "version": self.plugin_version,
            "result": self.result,
        }
        if self.user_id:
            data["user_id"] = self.user_id
        if self.details:
            # SECURITY FIX (HIGH-3): Sanitize details before logging
            data["details"] = sanitize_details(self.details)
        if self.duration_ms > 0:
            data["duration_ms"] = self.duration_ms
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "AuditEvent":
        """Create from dictionary."""
        return cls(
            timestamp=data["timestamp"],
            event_type=AuditEventType(data["event"]),
            plugin_name=data["plugin"],
            plugin_version=data["version"],
            user_id=data.get("user_id"),
            details=data.get("details"),
            result=data.get("result", "success"),
            duration_ms=data.get("duration_ms", 0),
        )


class AuditLogger:
    """Manages audit logging for plugins."""

    def __init__(self, log_path: Path | None = None):
        """Initialise audit logger.

        Args:
            log_path: Path to audit log file (defaults to ~/.ragged/plugins/audit.log)
        """
        if log_path is None:
            log_path = Path.home() / ".ragged" / "plugins" / "audit.log"
        self.log_path = log_path
        self.log_path.parent.mkdir(parents=True, exist_ok=True)

    def log_event(self, event: AuditEvent) -> None:
        """Log an audit event.

        Args:
            event: Event to log
        """
        try:
            with open(self.log_path, "a") as f:
                f.write(json.dumps(event.to_dict()) + "\n")
            logger.debug(f"Logged audit event: {event.event_type.value} for {event.plugin_name}")
        except Exception as e:
            logger.error(f"Failed to log audit event: {e}")

    def log_plugin_loaded(
        self, plugin_name: str, plugin_version: str, user_id: str | None = None
    ) -> None:
        """Log plugin loaded event.

        Args:
            plugin_name: Name of plugin
            plugin_version: Plugin version
            user_id: User loading the plugin
        """
        event = AuditEvent(
            timestamp=datetime.utcnow().isoformat() + "Z",
            event_type=AuditEventType.PLUGIN_LOADED,
            plugin_name=plugin_name,
            plugin_version=plugin_version,
            user_id=user_id,
        )
        self.log_event(event)

    def log_plugin_executed(
        self,
        plugin_name: str,
        plugin_version: str,
        result: str,
        duration_ms: int,
        permissions_used: list[str],
        user_id: str | None = None,
    ) -> None:
        """Log plugin execution event.

        Args:
            plugin_name: Name of plugin
            plugin_version: Plugin version
            result: Execution result (success/failed)
            duration_ms: Execution duration in milliseconds
            permissions_used: List of permissions used during execution
            user_id: User who executed the plugin
        """
        event = AuditEvent(
            timestamp=datetime.utcnow().isoformat() + "Z",
            event_type=AuditEventType.PLUGIN_EXECUTED,
            plugin_name=plugin_name,
            plugin_version=plugin_version,
            user_id=user_id,
            result=result,
            duration_ms=duration_ms,
            details={"permissions_used": permissions_used},
        )
        self.log_event(event)

    def log_permission_event(
        self,
        event_type: AuditEventType,
        plugin_name: str,
        plugin_version: str,
        permission: str,
        user_id: str | None = None,
    ) -> None:
        """Log permission-related event.

        Args:
            event_type: Type of permission event
            plugin_name: Name of plugin
            plugin_version: Plugin version
            permission: Permission involved
            user_id: User involved in permission change
        """
        event = AuditEvent(
            timestamp=datetime.utcnow().isoformat() + "Z",
            event_type=event_type,
            plugin_name=plugin_name,
            plugin_version=plugin_version,
            user_id=user_id,
            details={"permission": permission},
        )
        self.log_event(event)

    def log_security_violation(
        self,
        plugin_name: str,
        plugin_version: str,
        violation_type: str,
        details: dict[str, Any],
        user_id: str | None = None,
    ) -> None:
        """Log security violation event.

        Args:
            plugin_name: Name of plugin
            plugin_version: Plugin version
            violation_type: Type of violation
            details: Additional violation details
            user_id: User during whose session violation occurred
        """
        event = AuditEvent(
            timestamp=datetime.utcnow().isoformat() + "Z",
            event_type=AuditEventType.SANDBOX_VIOLATION,
            plugin_name=plugin_name,
            plugin_version=plugin_version,
            user_id=user_id,
            result="violation",
            details={"violation_type": violation_type, **details},
        )
        self.log_event(event)
        logger.warning(f"Security violation: {violation_type} by {plugin_name}")

    def get_events(
        self,
        plugin_name: str | None = None,
        event_type: AuditEventType | None = None,
        since: datetime | None = None,
        limit: int = 100,
    ) -> list[AuditEvent]:
        """Retrieve audit events with filtering.

        SECURITY FIX (HIGH-3): Uses safe JSON parsing with structure validation.

        Args:
            plugin_name: Filter by plugin name
            event_type: Filter by event type
            since: Filter events after this timestamp
            limit: Maximum number of events to return

        Returns:
            List of matching audit events
        """
        events = []
        try:
            if not self.log_path.exists():
                return events

            with open(self.log_path) as f:
                for line in f:
                    try:
                        # SECURITY FIX (HIGH-3): Use safe JSON parsing
                        data = safe_json_loads(line.strip())
                        event = AuditEvent.from_dict(data)

                        # Apply filters
                        if plugin_name and event.plugin_name != plugin_name:
                            continue
                        if event_type and event.event_type != event_type:
                            continue
                        if since:
                            event_time = datetime.fromisoformat(event.timestamp.replace("Z", "+00:00"))
                            if event_time < since:
                                continue

                        events.append(event)

                        if len(events) >= limit:
                            break
                    except (json.JSONDecodeError, AuditSecurityError) as e:
                        logger.warning(f"Invalid/malicious JSON in audit log: {e}")
                        continue

        except Exception as e:
            logger.error(f"Failed to read audit log: {e}")

        return events

    def get_security_violations(self, plugin_name: str | None = None) -> list[AuditEvent]:
        """Get all security violations.

        Args:
            plugin_name: Filter by plugin name

        Returns:
            List of security violation events
        """
        return self.get_events(plugin_name=plugin_name, event_type=AuditEventType.SANDBOX_VIOLATION)

    def clear_old_events(self, days: int = 90) -> int:
        """Clear events older than specified days.

        SECURITY FIX (HIGH-3): Uses safe JSON parsing during cleanup.

        Args:
            days: Number of days to retain

        Returns:
            Number of events removed
        """
        if not self.log_path.exists():
            return 0

        cutoff = datetime.utcnow().timestamp() - (days * 24 * 60 * 60)
        kept_events = []
        removed_count = 0

        try:
            with open(self.log_path) as f:
                for line in f:
                    try:
                        # SECURITY FIX (HIGH-3): Use safe JSON parsing
                        data = safe_json_loads(line.strip())
                        event_time = datetime.fromisoformat(data["timestamp"].replace("Z", "+00:00"))
                        if event_time.timestamp() >= cutoff:
                            kept_events.append(line)
                        else:
                            removed_count += 1
                    except (json.JSONDecodeError, AuditSecurityError):
                        # Skip malicious/malformed entries
                        logger.warning("Removing malicious/malformed audit entry during cleanup")
                        removed_count += 1
                    except Exception:
                        # Keep entries with other errors (e.g., timestamp issues)
                        kept_events.append(line)

            # Rewrite file with kept events
            with open(self.log_path, "w") as f:
                f.writelines(kept_events)

            logger.info(f"Cleared {removed_count} audit events older than {days} days")
            return removed_count

        except Exception as e:
            logger.error(f"Failed to clear old events: {e}")
            return 0
