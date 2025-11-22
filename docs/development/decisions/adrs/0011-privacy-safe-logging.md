# ADR-0011: Privacy-Safe Logging

**Status:** Accepted

**Date:** 2025-11-09

**Deciders:** Development Team

**Area:** Logging, Security

## Context

Logs may inadvertently capture sensitive information including:
- Passwords and API keys in configuration
- Document content in error messages
- User queries and responses
- File paths revealing private information

Need to prevent PII leakage whilst maintaining useful debugging information.

## Decision

Implement privacy-safe logging with automatic PII filtering:
- Filter sensitive keys (password, token, api_key, secret, etc.)
- Redact document content in error messages
- Use structured logging for better filtering control
- Different redaction levels based on log level

## Rationale

- **Privacy-First**: Core principle of ragged must extend to logging
- **Compliance**: Prevents accidental logging of sensitive data (GDPR, etc.)
- **Security**: Logs can be safely shared for debugging without exposing secrets
- **Best Practice**: Industry standard for secure applications
- **Trust**: Users can trust ragged won't leak their data

## Implementation

```python
import logging

class PrivacyFilter(logging.Filter):
    """Filter sensitive information from logs."""

    SENSITIVE_KEYS = {
        "password", "token", "api_key", "secret",
        "auth", "credential", "content", "text",
        "query", "response", "document"
    }

    def filter(self, record: logging.LogRecord) -> bool:
        """Redact sensitive information from log record."""
        msg_lower = str(record.msg).lower()

        # Check for sensitive keys
        for key in self.SENSITIVE_KEYS:
            if key in msg_lower:
                record.msg = f"[REDACTED: potentially sensitive - {key}]"
                break

        return True

# Apply to all loggers
logging.basicConfig()
for handler in logging.root.handlers:
    handler.addFilter(PrivacyFilter())
```

## Alternatives Considered

### 1. No Filtering

**Pros:**
- Simplest implementation
- Maximum debugging information

**Cons:**
- Violates privacy-first principle
- Risk of leaking sensitive data
- Compliance issues

**Rejected:** Unacceptable risk for privacy-first system

### 2. Manual Redaction

**Pros:**
- Fine-grained control
- No false positives

**Cons:**
- Error-prone (easy to forget)
- Inconsistent application
- Requires discipline from all developers

**Rejected:** Human error is too likely

### 3. Disable Logging Entirely

**Pros:**
- No risk of leakage
- Simple

**Cons:**
- Logs are valuable for debugging
- Production troubleshooting becomes very difficult
- No visibility into errors

**Rejected:** Logs are essential for production support

### 4. Log to Encrypted Storage Only

**Pros:**
- Logs protected at rest

**Cons:**
- Doesn't prevent initial capture of sensitive data
- Complex key management
- Doesn't help with console logs

**Rejected:** Doesn't address root cause

## Consequences

### Positive

- Logs are safe to share with support/community
- Automatic protection (can't forget to redact)
- Maintains privacy-first principle
- Compliance-friendly (GDPR, data protection laws)
- Users can trust the system

### Negative

- May redact too aggressively (false positives)
- Slightly slower logging (filter overhead)
- Debugging harder if needed information is redacted
- Developers must be aware of limitations

### Neutral

- Trade-off between debuggability and privacy leans toward privacy
- Can adjust sensitivity based on log level if needed

## Lessons Learned

Consider log levels for different redaction strategies:
- **DEBUG**: Less aggressive (local development)
- **INFO**: Moderate filtering
- **WARN/ERROR**: More aggressive (production)

## Future Enhancements

v0.2+:
- Configurable sensitivity levels
- Separate privacy filters per log level
- Structured logging with automatic field redaction
- Audit log of what was redacted (metadata only)

## Related

- [ADR-0001: Local-Only Processing](./0001-local-only-processing.md)
- [Core Concepts: Privacy Architecture](../../planning/core-concepts/privacy-architecture.md)
- [Security Considerations](../../planning/architecture/security.md)

---

## Related Documentation

- [Local-Only Processing (ADR-0001)](./0001-local-only-processing.md) - Privacy foundation
- [Privacy Design](../../../explanation/privacy-design.md) - Privacy architecture
- [Security Practices](../../security/) - Security documentation

---
