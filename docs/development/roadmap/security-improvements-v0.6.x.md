# Security Improvements Roadmap: v0.6.x

**Based on**: Security Audit Report v0.6.0 (2025-11-24)
**Target Versions**: v0.6.1, v0.6.2, v0.6.3
**Priority**: Security enhancements and hardening

---

## Overview

This roadmap documents security improvements identified in the v0.6.0 security audit. Changes are prioritised by risk severity and implementation effort, distributed across minor version releases.

**Change Request Summary**:
- **HIGH Priority**: 2 items (v0.6.1)
- **MEDIUM Priority**: 3 items (v0.6.2)
- **LOW Priority**: 3 items (v0.6.3+)

---

## v0.6.1: High-Priority Security Fixes

**Target Release**: 2-4 weeks after v0.6.0
**Theme**: Critical security hardening

---

### CR-SEC-001: Enhanced MIME Type Validation

**Priority**: HIGH
**Effort**: LOW (2-4 hours)
**Risk Addressed**: MEDIUM (malicious file upload)
**Audit Reference**: Section 3.2 H-3

#### Problem Statement

Current MIME type validation (`src/utils/security.py:98-155`) uses basic magic byte detection with only 8-byte header inspection. This approach has limitations:

1. Limited signature database (only 6-7 file types)
2. No deep inspection (exploits can hide beyond first 8 bytes)
3. ZIP-based formats treated generically (potential for macro exploits in DOCX/XLSX)

**Current Code**:
```python
def validate_mime_type(file_path: Path, expected_types: list[str] | None = None) -> str:
    with open(file_path, "rb") as f:
        header = f.read(8)  # Only 8 bytes!

    if header.startswith(b"%PDF"):
        mime_type = "application/pdf"
    # ... limited coverage
```

#### Proposed Solution

Integrate `python-magic` library for comprehensive MIME type detection.

**Implementation**:

**1. Update dependencies** (`pyproject.toml`):
```toml
[project]
dependencies = [
    # ... existing dependencies
    "python-magic>=0.4.27",
]

[project.optional-dependencies]
dev = [
    # ... existing dev dependencies
]
```

**2. Rewrite `validate_mime_type()` function** (`src/utils/security.py`):

```python
"""Security utilities for input validation and sanitisation."""

import os
from pathlib import Path

try:
    import magic
    MAGIC_AVAILABLE = True
except ImportError:
    MAGIC_AVAILABLE = False

from ragged.config.settings import get_settings


class SecurityError(Exception):
    """Raised when a security violation is detected."""
    pass


def validate_mime_type(
    file_path: Path,
    expected_types: list[str] | None = None,
    fallback_to_basic: bool = True
) -> str:
    """Validate file MIME type using python-magic library.

    Args:
        file_path: Path to file
        expected_types: List of expected MIME types
        fallback_to_basic: Use basic detection if python-magic unavailable

    Returns:
        Detected MIME type

    Raises:
        SecurityError: If MIME type doesn't match expected types
        ImportError: If python-magic unavailable and fallback disabled
    """
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    # Use python-magic if available
    if MAGIC_AVAILABLE:
        mime = magic.Magic(mime=True)
        detected_type = mime.from_file(str(file_path))

        # Validate against expected types
        if expected_types and detected_type not in expected_types:
            raise SecurityError(
                f"File type {detected_type} not in allowed types {expected_types}: {file_path}"
            )

        return detected_type

    # Fallback to basic detection
    elif fallback_to_basic:
        return _validate_mime_type_basic(file_path, expected_types)

    # No detection available
    else:
        raise ImportError(
            "python-magic library required for robust MIME type detection. "
            "Install with: pip install python-magic"
        )


def _validate_mime_type_basic(
    file_path: Path,
    expected_types: list[str] | None = None
) -> str:
    """Basic MIME type detection (fallback).

    Note: This is the legacy implementation kept for backwards compatibility.
    It has known limitations and should not be used for security-critical validation.
    """
    # Read first 16 bytes (increased from 8 for better detection)
    with open(file_path, "rb") as f:
        header = f.read(16)

    # Basic magic byte detection (expanded)
    mime_type = "application/octet-stream"  # Default

    # PDF
    if header.startswith(b"%PDF"):
        mime_type = "application/pdf"

    # ZIP-based formats
    elif header.startswith(b"PK\x03\x04"):
        mime_type = "application/zip"

    # Images
    elif header.startswith(b"\x89PNG\r\n\x1a\n"):
        mime_type = "image/png"
    elif header.startswith(b"\xFF\xD8\xFF"):
        mime_type = "image/jpeg"
    elif header.startswith(b"GIF87a") or header.startswith(b"GIF89a"):
        mime_type = "image/gif"

    # HTML/XML
    elif header[:5] in (b"<?xml", b"<!DOC", b"<html", b"<HTML"):
        mime_type = "text/html"

    # Plain text (heuristic)
    else:
        try:
            content = file_path.read_bytes()[:512]
            content.decode("utf-8")
            mime_type = "text/plain"
        except (UnicodeDecodeError, OSError):
            pass

    # Validate against expected types if provided
    if expected_types and mime_type not in expected_types:
        raise SecurityError(
            f"File type {mime_type} not in allowed types {expected_types}: {file_path}"
        )

    return mime_type
```

**3. Update file upload endpoint** (`src/web/api.py`):

```python
@app.post("/api/upload", response_model=UploadResponse)
async def upload(file: UploadFile = File(...)) -> UploadResponse:
    """Document upload endpoint with enhanced MIME validation."""

    # ... existing code ...

    # Save to temporary file
    with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as temp_file:
        temp_file.write(content)
        temp_path = Path(temp_file.name)

    try:
        # SECURITY: Validate MIME type matches extension
        expected_mimes = {
            ".pdf": "application/pdf",
            ".txt": "text/plain",
            ".md": "text/plain",  # Markdown is plain text
            ".html": "text/html",
        }

        expected_type = expected_mimes.get(file_ext)
        if expected_type:
            from ragged.utils.security import validate_mime_type
            detected_type = validate_mime_type(temp_path, expected_types=[expected_type])
            logger.info(f"Validated MIME type: {detected_type}")

        # ... continue with existing processing ...
```

**4. Add tests** (`tests/security/test_mime_validation.py`):

```python
"""Tests for enhanced MIME type validation."""

import pytest
from pathlib import Path
from ragged.utils.security import validate_mime_type, SecurityError


def test_validate_mime_type_pdf(tmp_path):
    """Test PDF MIME type detection."""
    pdf_file = tmp_path / "test.pdf"
    pdf_file.write_bytes(b"%PDF-1.4\n...")

    mime_type = validate_mime_type(pdf_file, expected_types=["application/pdf"])
    assert mime_type == "application/pdf"


def test_validate_mime_type_rejects_mismatch(tmp_path):
    """Test MIME type mismatch detection."""
    fake_pdf = tmp_path / "fake.pdf"
    fake_pdf.write_bytes(b"This is not a PDF")

    with pytest.raises(SecurityError, match="not in allowed types"):
        validate_mime_type(fake_pdf, expected_types=["application/pdf"])


def test_mime_validation_detects_renamed_executable(tmp_path):
    """Test detection of executable renamed as PDF."""
    fake_pdf = tmp_path / "malicious.pdf"
    # ELF magic bytes (Linux executable)
    fake_pdf.write_bytes(b"\x7fELF\x02\x01\x01\x00")

    with pytest.raises(SecurityError):
        validate_mime_type(fake_pdf, expected_types=["application/pdf"])
```

#### Acceptance Criteria

- [ ] `python-magic` dependency added to `pyproject.toml`
- [ ] `validate_mime_type()` function rewritten with python-magic
- [ ] Basic fallback detection preserved for backwards compatibility
- [ ] File upload endpoint uses new validation
- [ ] 100% test coverage for MIME validation
- [ ] Tests pass for: PDF, TXT, HTML, renamed executables, ZIP bombs
- [ ] Documentation updated with MIME validation security

#### Migration Notes

**For Users**:
- Install `python-magic`: `pip install ragged[dev]` or `pip install python-magic`
- macOS may require `brew install libmagic`
- Linux: `apt-get install libmagic1` or equivalent

**For Developers**:
- Legacy `_validate_mime_type_basic()` preserved for backwards compatibility
- Automatic fallback if `python-magic` not installed
- No breaking changes to API

---

### CR-SEC-002: Fix Path Validation Test Failures

**Priority**: HIGH
**Effort**: MEDIUM (4-8 hours)
**Risk Addressed**: MEDIUM (path traversal)
**Audit Reference**: Section 6.2

#### Problem Statement

Four path validation tests are failing, indicating potential edge cases in path traversal prevention:

```
FAILED test_path_validation.py::TestPathValidator::test_validate_safe_relative_path
FAILED test_path_validation.py::TestPathValidator::test_validate_path_outside_base_rejected
FAILED test_path_validation.py::TestPathValidator::test_validate_symlink_blocked_when_not_allowed
FAILED test_path_validation.py::TestConvenienceFunctions::test_validate_path_convenience_function
```

These failures suggest issues with:
1. Relative path handling
2. Base directory constraint enforcement
3. Symlink validation
4. Convenience function implementation

#### Proposed Solution

1. **Review and debug failing tests**
2. **Fix path validation logic in `src/utils/security.py` and `src/utils/validation.py`**
3. **Ensure comprehensive coverage of edge cases**

**Investigation Steps**:

```bash
# Run failing tests with verbose output
pytest tests/security/test_path_validation.py::TestPathValidator::test_validate_safe_relative_path -vv

# Check implementation
rg "validate_file_path|validate_path" src/utils/
```

**Expected Issues**:
1. **Relative path resolution**: May not be correctly resolved relative to base directory
2. **Symlink handling**: `resolve()` follows symlinks, which may bypass base directory checks
3. **Race conditions**: TOCTOU (Time-of-Check-Time-of-Use) between validation and usage

**Proposed Fixes**:

**1. Enhance `validate_file_path()` in `src/utils/security.py`**:

```python
def validate_file_path(
    file_path: Path,
    allowed_base: Path | None = None,
    allow_symlinks: bool = False
) -> Path:
    """Validate a file path to prevent path traversal attacks.

    Args:
        file_path: Path to validate
        allowed_base: Optional base directory that file must be within
        allow_symlinks: Whether to allow symlinks (default: False for security)

    Returns:
        Resolved absolute path

    Raises:
        SecurityError: If path is invalid or outside allowed base
        FileNotFoundError: If file doesn't exist
    """
    # Check if path is a symlink BEFORE resolving
    if not allow_symlinks and file_path.is_symlink():
        raise SecurityError(f"Symlinks not allowed: {file_path}")

    # Resolve to absolute path (follows symlinks if allow_symlinks=True)
    try:
        resolved = file_path.resolve(strict=True)  # strict=True ensures file exists
    except (OSError, RuntimeError, FileNotFoundError) as e:
        raise SecurityError(f"Invalid file path: {e}") from e

    # Check if it's a file (not a directory)
    if not resolved.is_file():
        raise SecurityError(f"Path is not a regular file: {resolved}")

    # If allowed_base is specified, ensure file is within it
    if allowed_base is not None:
        allowed_base_resolved = allowed_base.resolve()

        # Check if resolved path is within allowed base
        try:
            # This will raise ValueError if not a subpath
            resolved.relative_to(allowed_base_resolved)
        except ValueError:
            raise SecurityError(
                f"Path {resolved} is outside allowed directory {allowed_base_resolved}"
            ) from None

        # Additional check: ensure no symbolic links in path components lead outside base
        # This prevents attacks like: /allowed/link -> /etc/passwd
        if not allow_symlinks:
            current = resolved
            while current != allowed_base_resolved:
                if current.is_symlink():
                    raise SecurityError(
                        f"Symlink in path components not allowed: {current}"
                    )
                current = current.parent
                if current == current.parent:  # Reached filesystem root
                    break

    return resolved
```

**2. Add comprehensive test coverage**:

```python
def test_symlink_attack_prevention(tmp_path):
    """Test prevention of symlink attacks that escape allowed directory."""
    allowed_dir = tmp_path / "allowed"
    forbidden_dir = tmp_path / "forbidden"
    allowed_dir.mkdir()
    forbidden_dir.mkdir()

    secret_file = forbidden_dir / "secret.txt"
    secret_file.write_text("secret data")

    # Create symlink inside allowed_dir pointing to forbidden_dir
    symlink = allowed_dir / "link_to_secret"
    symlink.symlink_to(secret_file)

    # Should be rejected
    with pytest.raises(SecurityError, match="Symlinks not allowed"):
        validate_file_path(symlink, allowed_base=allowed_dir, allow_symlinks=False)


def test_relative_path_resolution(tmp_path):
    """Test relative path resolution within allowed base."""
    base = tmp_path / "base"
    base.mkdir()
    subdir = base / "subdir"
    subdir.mkdir()
    file = subdir / "file.txt"
    file.write_text("data")

    # Test with relative path
    relative_path = Path("subdir/file.txt")
    resolved = validate_file_path(base / relative_path, allowed_base=base)

    assert resolved == file
    assert resolved.is_relative_to(base)
```

#### Acceptance Criteria

- [ ] All 4 failing path validation tests pass
- [ ] No regressions in passing tests
- [ ] Additional test coverage for edge cases:
  - [ ] Symlink attacks
  - [ ] Relative path resolution
  - [ ] Path traversal attempts (`../../../etc/passwd`)
  - [ ] Unicode normalization attacks
  - [ ] Null byte injection
- [ ] Security review confirms no bypasses
- [ ] Documentation updated with path validation security

#### Testing

```bash
# Run all path validation tests
pytest tests/security/test_path_validation.py -v

# Run path validation CLI integration tests
pytest tests/security/test_path_validation_cli.py -v

# Ensure no regressions
pytest tests/security/ -k "path" -v
```

---

## v0.6.2: Medium-Priority Security Enhancements

**Target Release**: 6-8 weeks after v0.6.0
**Theme**: Scalability and monitoring

---

### CR-SEC-003: Session Persistence with Redis Backend

**Priority**: MEDIUM
**Effort**: HIGH (8-16 hours)
**Risk Addressed**: MEDIUM (session loss, scalability)
**Audit Reference**: Section 3.2 H-2

#### Problem Statement

Sessions currently stored in-memory in `SessionSecurityMiddleware`. This causes:

1. **Session loss on restart**: Users must re-authenticate after service restart
2. **No horizontal scaling**: Can't run multiple API instances with shared sessions
3. **Memory exhaustion risk**: Unbounded session storage in production

**Current Implementation** (`src/web/middleware/security.py:160`):
```python
class SessionSecurityMiddleware(BaseHTTPMiddleware):
    def __init__(self, ...):
        self._sessions: dict[str, dict[str, Any]] = {}  # In-memory only
```

#### Proposed Solution

Implement optional Redis backend for session storage with graceful fallback to in-memory for development.

**Architecture**:
```
┌─────────────────────────────────────────┐
│   SessionSecurityMiddleware             │
├─────────────────────────────────────────┤
│  __init__(redis_url: str | None)       │
│    ├─ If redis_url provided:           │
│    │    → Use RedisSessionStore         │
│    └─ Else:                             │
│         → Use InMemorySessionStore      │
└─────────────────────────────────────────┘
```

**Implementation**:

**1. Create session store interface** (`src/web/session/store.py`):

```python
"""Session storage backends for SessionSecurityMiddleware."""

from abc import ABC, abstractmethod
from typing import Any
import time


class SessionStore(ABC):
    """Abstract base class for session storage backends."""

    @abstractmethod
    def get(self, session_id: str) -> dict[str, Any] | None:
        """Get session data by ID."""
        pass

    @abstractmethod
    def set(self, session_id: str, session_data: dict[str, Any]) -> None:
        """Store session data."""
        pass

    @abstractmethod
    def delete(self, session_id: str) -> None:
        """Delete session by ID."""
        pass

    @abstractmethod
    def cleanup_expired(self, timeout_seconds: int) -> int:
        """Remove expired sessions. Returns count of deleted sessions."""
        pass


class InMemorySessionStore(SessionStore):
    """In-memory session storage (development/single-instance)."""

    def __init__(self):
        self._sessions: dict[str, dict[str, Any]] = {}

    def get(self, session_id: str) -> dict[str, Any] | None:
        return self._sessions.get(session_id)

    def set(self, session_id: str, session_data: dict[str, Any]) -> None:
        self._sessions[session_id] = session_data

    def delete(self, session_id: str) -> None:
        self._sessions.pop(session_id, None)

    def cleanup_expired(self, timeout_seconds: int) -> int:
        current_time = time.time()
        expired = [
            sid for sid, data in self._sessions.items()
            if current_time - data.get("last_activity", 0) > timeout_seconds
        ]
        for sid in expired:
            del self._sessions[sid]
        return len(expired)


class RedisSessionStore(SessionStore):
    """Redis-backed session storage (production/multi-instance)."""

    def __init__(self, redis_url: str):
        try:
            import redis
        except ImportError:
            raise ImportError("redis library required: pip install redis")

        self.redis = redis.from_url(redis_url, decode_responses=True)
        self._prefix = "ragged:session:"

    def get(self, session_id: str) -> dict[str, Any] | None:
        import json
        key = f"{self._prefix}{session_id}"
        data = self.redis.get(key)
        if data:
            return json.loads(data)
        return None

    def set(self, session_id: str, session_data: dict[str, Any]) -> None:
        import json
        key = f"{self._prefix}{session_id}"
        # Store with TTL for automatic expiry
        ttl_seconds = 3600  # 1 hour
        self.redis.setex(key, ttl_seconds, json.dumps(session_data))

    def delete(self, session_id: str) -> None:
        key = f"{self._prefix}{session_id}"
        self.redis.delete(key)

    def cleanup_expired(self, timeout_seconds: int) -> int:
        # Redis handles expiry automatically with TTL
        return 0
```

**2. Update `SessionSecurityMiddleware`** (`src/web/middleware/security.py`):

```python
from ragged.web.session.store import SessionStore, InMemorySessionStore, RedisSessionStore

class SessionSecurityMiddleware(BaseHTTPMiddleware):
    def __init__(
        self,
        app: ASGIApp,
        session_timeout: int = 3600,
        enable_csrf: bool = True,
        redis_url: str | None = None,
    ):
        """Initialise session security middleware.

        Args:
            app: ASGI application
            session_timeout: Session timeout in seconds
            enable_csrf: Enable CSRF token validation
            redis_url: Optional Redis URL for session persistence
                      (e.g., "redis://localhost:6379/0")
                      If None, uses in-memory storage
        """
        super().__init__(app)
        self.session_timeout = session_timeout
        self.enable_csrf = enable_csrf

        # Choose session store backend
        if redis_url:
            self._sessions: SessionStore = RedisSessionStore(redis_url)
            logger.info(f"Using Redis session storage: {redis_url}")
        else:
            self._sessions = InMemorySessionStore()
            logger.info("Using in-memory session storage")

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Get session ID from cookie
        session_id = request.cookies.get("session_id")

        if session_id:
            # Check session timeout
            session = self._sessions.get(session_id)
            if session:
                last_activity = session.get("last_activity", 0)
                if time.time() - last_activity > self.session_timeout:
                    # Session expired
                    logger.warning(f"Session {session_id[:8]}... expired")
                    self._sessions.delete(session_id)
                    session_id = None
                else:
                    # Update last activity
                    session["last_activity"] = time.time()
                    self._sessions.set(session_id, session)

        # Create new session if needed
        if not session_id:
            session_id = secrets.token_urlsafe(32)
            session_data = {
                "created_at": time.time(),
                "last_activity": time.time(),
                "csrf_token": secrets.token_urlsafe(32) if self.enable_csrf else None,
            }
            self._sessions.set(session_id, session_data)
            logger.info(f"Created new session: {session_id[:8]}...")

        # Add session to request state
        request.state.session_id = session_id
        request.state.session = self._sessions.get(session_id) or {}

        # Process request
        response = await call_next(request)

        # Set session cookie
        response.set_cookie(
            key="session_id",
            value=session_id,
            httponly=True,
            secure=True,
            samesite="strict",
            max_age=self.session_timeout,
        )

        return response
```

**3. Update `docker-compose.yml`**:

```yaml
services:
  # Add Redis service
  redis:
    image: redis:7-alpine
    container_name: ragged-redis
    ports:
      - "${REDIS_PORT:-6379}:6379"
    volumes:
      - redis-data:/data
    command: redis-server --appendonly yes  # Persistence
    networks:
      - ragged-network
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 3s
      retries: 3

  ragged-api:
    # ... existing config ...
    environment:
      - REDIS_URL=${REDIS_URL:-redis://redis:6379/0}
    depends_on:
      chromadb:
        condition: service_healthy
      redis:
        condition: service_healthy

volumes:
  redis-data:
    name: ragged-redis-data
```

**4. Update settings** (`src/config/settings.py`):

```python
class Settings(BaseSettings):
    # ... existing settings ...

    # Session storage
    redis_url: str | None = None  # If None, uses in-memory sessions

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
```

**5. Add tests** (`tests/security/test_session_persistence.py`):

```python
"""Tests for session persistence with Redis backend."""

import pytest
from ragged.web.session.store import InMemorySessionStore, RedisSessionStore


def test_inmemory_store_basic_operations():
    store = InMemorySessionStore()

    # Test set and get
    store.set("session1", {"user_id": "user1", "last_activity": 1234567890})
    session = store.get("session1")
    assert session["user_id"] == "user1"

    # Test delete
    store.delete("session1")
    assert store.get("session1") is None


@pytest.mark.integration
def test_redis_store_basic_operations():
    """Integration test requiring Redis instance."""
    store = RedisSessionStore("redis://localhost:6379/15")  # Use test DB

    # Test set and get
    store.set("session1", {"user_id": "user1", "last_activity": 1234567890})
    session = store.get("session1")
    assert session["user_id"] == "user1"

    # Test delete
    store.delete("session1")
    assert store.get("session1") is None


def test_session_expiry_with_redis():
    """Test automatic expiry with Redis TTL."""
    store = RedisSessionStore("redis://localhost:6379/15")

    # Set session with short TTL
    store.redis.setex("ragged:session:test", 1, "{\"data\": \"value\"}")

    # Should exist immediately
    assert store.get("test") is not None

    # Should expire after 2 seconds
    import time
    time.sleep(2)
    assert store.get("test") is None
```

#### Acceptance Criteria

- [ ] `SessionStore` abstract interface implemented
- [ ] `InMemorySessionStore` for development (existing behaviour)
- [ ] `RedisSessionStore` for production
- [ ] Graceful fallback to in-memory if Redis unavailable
- [ ] Redis service added to `docker-compose.yml`
- [ ] Environment variable `REDIS_URL` for configuration
- [ ] 100% test coverage for both backends
- [ ] Integration tests with Redis container
- [ ] Documentation for production deployment with Redis
- [ ] Session persistence verified across service restarts

#### Migration Notes

**For Development**:
- No changes required - in-memory storage remains default
- Optional: Use Redis locally with `REDIS_URL=redis://localhost:6379/0`

**For Production**:
- Deploy Redis instance or use managed service (AWS ElastiCache, Redis Cloud)
- Set `REDIS_URL` environment variable
- Sessions will persist across API restarts
- Supports horizontal scaling (multiple API instances)

---

### CR-SEC-004: Session Monitoring & Metrics

**Priority**: MEDIUM
**Effort**: LOW (2-4 hours)
**Risk Addressed**: LOW (DoS detection, capacity planning)
**Audit Reference**: Section 8.1 R-4

#### Problem Statement

No visibility into session creation rates, active session counts, or potential DoS attacks via session exhaustion.

#### Proposed Solution

Add Prometheus-compatible metrics for session monitoring.

**Metrics to Track**:
1. `ragged_sessions_active` - Current number of active sessions
2. `ragged_sessions_created_total` - Total sessions created (counter)
3. `ragged_sessions_expired_total` - Total sessions expired (counter)
4. `ragged_sessions_creation_rate` - Sessions created per minute (gauge)

**Implementation**:

```python
# src/web/middleware/metrics.py
from prometheus_client import Counter, Gauge

# Session metrics
sessions_active = Gauge('ragged_sessions_active', 'Number of active sessions')
sessions_created = Counter('ragged_sessions_created_total', 'Total sessions created')
sessions_expired = Counter('ragged_sessions_expired_total', 'Total sessions expired')

# Rate tracking
from collections import deque
import time

class SessionMetrics:
    def __init__(self):
        self._creation_times = deque(maxlen=1000)

    def record_creation(self):
        sessions_created.inc()
        self._creation_times.append(time.time())
        self._update_active_count()

    def record_expiry(self):
        sessions_expired.inc()
        self._update_active_count()

    def get_creation_rate(self) -> float:
        """Get sessions created per minute (last 60 seconds)."""
        cutoff = time.time() - 60
        recent = sum(1 for t in self._creation_times if t > cutoff)
        return recent

    def _update_active_count(self):
        active = sessions_created._value.get() - sessions_expired._value.get()
        sessions_active.set(active)

    def check_anomaly(self) -> bool:
        """Detect unusual session creation rates."""
        rate = self.get_creation_rate()
        if rate > 100:  # Alert threshold
            logger.warning(f"High session creation rate: {rate}/min")
            return True
        return False
```

#### Acceptance Criteria

- [ ] Prometheus metrics endpoint `/metrics`
- [ ] Session creation/expiry counters
- [ ] Active session gauge
- [ ] Anomaly detection for unusual rates
- [ ] Grafana dashboard template
- [ ] Documentation for monitoring setup

---

### CR-SEC-005: Plugin Sandbox Enforcement Verification

**Priority**: MEDIUM
**Effort**: MEDIUM (4-8 hours)
**Risk Addressed**: MEDIUM (plugin escape)
**Audit Reference**: Section 3.3 M-3

#### Problem Statement

Plugin sandbox implements resource limits (`setrlimit`) and permission checks, but actual enforcement has not been verified with real test plugins.

**Missing Verification**:
1. Memory limits actually enforced?
2. CPU limits trigger SIGXCPU?
3. Network isolation works on Linux?
4. Process limits prevent fork bombs?
5. File system restrictions effective?

#### Proposed Solution

Create comprehensive test plugins that attempt to violate sandbox constraints, verify they are blocked.

**Test Plugins**:

**1. Memory Hog** (`tests/plugins/memory_hog.py`):
```python
#!/usr/bin/env python3
"""Test plugin that attempts to exceed memory limit."""

import sys

def allocate_memory():
    """Allocate memory until killed."""
    data = []
    try:
        while True:
            # Allocate 10MB chunks
            data.append(b"A" * (10 * 1024 * 1024))
            print(f"Allocated {len(data) * 10}MB", file=sys.stderr)
    except MemoryError:
        print("MemoryError caught", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    allocate_memory()
```

**2. CPU Burner** (`tests/plugins/cpu_burner.py`):
```python
#!/usr/bin/env python3
"""Test plugin that attempts to exceed CPU limit."""

import time

def burn_cpu():
    """Infinite loop to burn CPU time."""
    start = time.time()
    counter = 0
    while True:
        counter += 1
        if counter % 1000000 == 0:
            elapsed = time.time() - start
            print(f"Running for {elapsed:.2f}s", flush=True)

if __name__ == "__main__":
    burn_cpu()
```

**3. Network Accessor** (`tests/plugins/network_accessor.py`):
```python
#!/usr/bin/env python3
"""Test plugin that attempts network access."""

import socket
import sys

def access_network():
    """Attempt to make network connection."""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect(("8.8.8.8", 53))
        print("Network access succeeded", file=sys.stderr)
        sock.close()
        sys.exit(0)
    except Exception as e:
        print(f"Network access blocked: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    access_network()
```

**Enforcement Tests** (`tests/security/test_plugin_sandbox_enforcement.py`):

```python
"""Comprehensive plugin sandbox enforcement tests."""

import pytest
from pathlib import Path
from ragged.plugins.sandbox import PluginSandbox, SandboxConfig, SandboxResult


@pytest.fixture
def test_plugins_dir():
    return Path(__file__).parent.parent / "plugins"


def test_memory_limit_enforced(test_plugins_dir):
    """Verify memory limit kills plugin exceeding limit."""
    config = SandboxConfig(
        max_memory_mb=50,  # 50MB limit
        execution_timeout_seconds=30
    )
    sandbox = PluginSandbox("memory_hog", config)

    result = sandbox.execute(
        executable=str(test_plugins_dir / "memory_hog.py"),
        args=[]
    )

    # Should be killed for exceeding memory
    assert result.result in [SandboxResult.MEMORY_LIMIT, SandboxResult.CRASHED]
    assert result.error  # Should have error output


def test_cpu_limit_enforced(test_plugins_dir):
    """Verify CPU limit kills plugin exceeding limit."""
    config = SandboxConfig(
        max_cpu_seconds=2,  # 2 second CPU limit
        execution_timeout_seconds=30
    )
    sandbox = PluginSandbox("cpu_burner", config)

    result = sandbox.execute(
        executable=str(test_plugins_dir / "cpu_burner.py"),
        args=[]
    )

    # Should be killed for exceeding CPU time
    assert result.result == SandboxResult.TIMEOUT
    assert result.duration_ms < 30000  # Should die before execution timeout


@pytest.mark.skipif(sys.platform != "linux", reason="Network isolation Linux-only")
def test_network_isolation_enforced(test_plugins_dir):
    """Verify network access is blocked."""
    config = SandboxConfig(
        block_network=True,
        execution_timeout_seconds=10
    )
    sandbox = PluginSandbox("network_accessor", config)

    result = sandbox.execute(
        executable=str(test_plugins_dir / "network_accessor.py"),
        args=[]
    )

    # Should fail to access network
    assert result.result != SandboxResult.SUCCESS
    assert "blocked" in result.error.lower() or result.exit_code != 0
```

#### Acceptance Criteria

- [ ] Test plugins created for each resource limit
- [ ] Memory limit enforcement verified
- [ ] CPU limit enforcement verified
- [ ] Network isolation verified (Linux)
- [ ] Process limit (fork bomb prevention) verified
- [ ] File system restriction tests
- [ ] Tests run in CI/CD pipeline
- [ ] Documentation updated with sandbox capabilities/limitations

---

## v0.6.3: Low-Priority Improvements

**Target Release**: 10-12 weeks after v0.6.0
**Theme**: Polish and hardening

---

### CR-SEC-006: Structured Error Responses

**Priority**: LOW
**Effort**: MEDIUM (4-8 hours)
**Risk Addressed**: LOW (information disclosure)
**Audit Reference**: Section 3.3 M-4

#### Implementation

Create error response schema with error codes, no sensitive information.

**Example**:
```json
{
  "error": {
    "code": "ERR_FILE_TOO_LARGE",
    "message": "File exceeds maximum size",
    "details": {
      "max_size_mb": 100
    },
    "request_id": "req_abc123"
  }
}
```

---

### CR-SEC-007: Enhanced Rate Limiting

**Priority**: LOW
**Effort**: MEDIUM (4-8 hours)
**Risk Addressed**: LOW (targeted abuse)

#### Implementation

Per-endpoint rate limits with customisable tiers:

```python
rate_limits = {
    "/api/query": RateLimit(requests_per_minute=30),
    "/api/upload": RateLimit(requests_per_minute=10, size_per_minute_mb=100),
    "/api/health": RateLimit(requests_per_minute=1000),
}
```

---

### CR-SEC-008: Docker Security Hardening

**Priority**: LOW
**Effort**: LOW (1-2 hours)
**Risk Addressed**: LOW (resource exhaustion)

#### Implementation

Add resource limits and pin ChromaDB version:

```yaml
services:
  ragged-api:
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 2048M

  chromadb:
    image: chromadb/chroma:0.4.18  # Pin version
```

---

## Implementation Tracking

### Version Assignment

| CR ID | Title | Priority | Version | Status |
|-------|-------|----------|---------|--------|
| CR-SEC-001 | Enhanced MIME validation | HIGH | v0.6.1 | Planned |
| CR-SEC-002 | Fix path validation tests | HIGH | v0.6.1 | Planned |
| CR-SEC-003 | Redis session persistence | MEDIUM | v0.6.2 | Planned |
| CR-SEC-004 | Session monitoring | MEDIUM | v0.6.2 | Planned |
| CR-SEC-005 | Sandbox enforcement tests | MEDIUM | v0.6.2 | Planned |
| CR-SEC-006 | Structured errors | LOW | v0.6.3 | Planned |
| CR-SEC-007 | Enhanced rate limiting | LOW | v0.6.3 | Planned |
| CR-SEC-008 | Docker hardening | LOW | v0.6.3 | Planned |

---

## Related Documentation

- [Security Audit Report v0.6.0](../../audit/security/baseline/v0.6.0-security-audit.md) - Full audit findings
- [Security Monitoring Guide](../../guides/security-monitoring.md) - Operations guide
- [Security Policy](../../security/policy.md) - Project security policy

---

**Status**: Planned

