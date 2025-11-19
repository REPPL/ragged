# v0.2.10 - Security Hardening

**Category:** Security Infrastructure

**Estimated Time:** 15-21 hours

**Status:** Planned

**Priority:** CRITICAL - Must complete before v0.3.x

---

## Overview

Eliminate critical security vulnerabilities discovered in privacy audit, establishing secure foundations for all future features. This version focuses on removing arbitrary code execution risks and implementing session isolation to prevent cross-user data leakage.

**Why Critical:** Current implementation has HIGH-RISK vulnerabilities:
1. **Pickle deserialization** enables arbitrary code execution
2. **Global query cache** leaks PII between users/sessions
3. **No security testing** framework to prevent regression

**Impact:** Foundational security layer required before v0.3.x implementation can proceed safely.

---

## Security Issues Addressed

### Critical Vulnerabilities (Must Fix)

**VULN-001: Pickle Arbitrary Code Execution**
- **Location:** `src/retrieval/incremental_index.py:341`
- **Risk:** CRITICAL - Arbitrary code execution via malicious `.pkl` files
- **Attack Vector:** User loads crafted checkpoint → `pickle.load()` executes embedded code
- **Impact:** Complete system compromise (file deletion, data exfiltration, malware installation)

**VULN-002: Cross-Session Cache Pollution**
- **Location:** `src/retrieval/cache.py:72-80, 122-154`
- **Risk:** HIGH - PII leakage between users/sessions
- **Attack Vector:** User A's sensitive query cached → User B's similar query retrieves User A's PII
- **Impact:** Privacy violation, GDPR non-compliance

**VULN-003: No Security Testing**
- **Location:** Entire codebase
- **Risk:** MEDIUM - Vulnerabilities can be reintroduced without detection
- **Attack Vector:** Future code changes inadvertently introduce security issues
- **Impact:** Regression of security fixes, new vulnerability introduction

---

## Features

### FEAT-SEC-001: Replace Pickle with JSON (4-6h)

**Priority:** CRITICAL
**Dependencies:** None
**Security Agent:** Invoke before AND after implementation

#### Scope

Replace all Pickle usage with JSON serialization to eliminate arbitrary code execution risk.

**Files Affected:**
1. `src/retrieval/incremental_index.py` - BM25 checkpoint persistence
2. `docs/development/roadmap/version/v0.2.7/features/performance-optimisations.md` - Planned embedding cache (NOT YET IMPLEMENTED)

**Risk Eliminated:** Arbitrary code execution via malicious serialized data

#### Implementation

**Phase 1: BM25 Checkpoint Migration (2-3h)**

```python
# src/retrieval/incremental_index.py

# BEFORE (VULNERABLE):
import pickle

def _save_checkpoint(self) -> None:
    checkpoint = IndexCheckpoint(...)
    checkpoint_path = self.checkpoint_dir / f"bm25_checkpoint_v{self.version}.pkl"

    with open(checkpoint_path, 'wb') as f:
        pickle.dump(checkpoint, f)  # ⚠️ SECURITY RISK

def load_checkpoint(self, version: Optional[int] = None) -> bool:
    with open(checkpoint_path, 'rb') as f:
        checkpoint: IndexCheckpoint = pickle.load(f)  # ⚠️ ARBITRARY CODE EXECUTION

# AFTER (SECURE):
import json
from pathlib import Path

def _save_checkpoint(self) -> None:
    """Save checkpoint to disk using JSON (secure serialization)."""
    if not self.enable_checkpoints:
        return

    checkpoint_data = {
        "documents": self.documents,
        "doc_ids": self.doc_ids,
        "metadatas": self.metadatas,
        "deleted_ids": list(self.deleted_ids),  # Convert set to list
        "timestamp": time.time(),
        "version": self.version,
    }

    checkpoint_path = self.checkpoint_dir / f"bm25_checkpoint_v{self.version}.json"

    try:
        with open(checkpoint_path, 'w', encoding='utf-8') as f:
            json.dump(checkpoint_data, f, indent=2, ensure_ascii=False)

        logger.debug(f"Saved checkpoint (JSON): {checkpoint_path}")

        # Clean old checkpoints (keep last 3)
        self._cleanup_old_checkpoints(keep=3)

    except Exception as e:
        logger.error(f"Failed to save checkpoint: {e}")


def load_checkpoint(self, version: Optional[int] = None) -> bool:
    """Load checkpoint from disk using JSON (secure deserialization)."""
    if not self.enable_checkpoints:
        logger.warning("Checkpoints disabled, cannot load")
        return False

    try:
        # Find checkpoint file
        if version is not None:
            checkpoint_path = self.checkpoint_dir / f"bm25_checkpoint_v{version}.json"
        else:
            # Load latest JSON checkpoint
            checkpoints = sorted(
                self.checkpoint_dir.glob("bm25_checkpoint_v*.json"),
                key=lambda p: p.stat().st_mtime,
                reverse=True
            )
            if not checkpoints:
                logger.warning("No JSON checkpoints found")
                # Try legacy .pkl migration (one-time)
                return self._migrate_legacy_pickle_checkpoint()
            checkpoint_path = checkpoints[0]

        # Load checkpoint (JSON is safe - no code execution)
        with open(checkpoint_path, 'r', encoding='utf-8') as f:
            checkpoint_data = json.load(f)

        with self._lock:
            self.documents = checkpoint_data["documents"]
            self.doc_ids = checkpoint_data["doc_ids"]
            self.metadatas = checkpoint_data["metadatas"]
            self.deleted_ids = set(checkpoint_data["deleted_ids"])  # Convert list back to set
            self.version = checkpoint_data["version"]

            # Rebuild index
            if self.documents:
                tokenized_corpus = [doc.lower().split() for doc in self.documents]
                self.index = BM25Okapi(tokenized_corpus)
            else:
                self.index = None

        logger.info(
            f"Loaded checkpoint v{checkpoint_data['version']} from {checkpoint_path} "
            f"({len(self.documents)} documents, {len(self.deleted_ids)} deleted)"
        )

        return True

    except Exception as e:
        logger.error(f"Failed to load checkpoint: {e}")
        return False


def _migrate_legacy_pickle_checkpoint(self) -> bool:
    """One-time migration from legacy .pkl to .json format."""
    logger.info("Attempting legacy .pkl checkpoint migration...")

    try:
        import pickle  # Only for migration

        # Find latest .pkl checkpoint
        pkl_checkpoints = sorted(
            self.checkpoint_dir.glob("bm25_checkpoint_v*.pkl"),
            key=lambda p: p.stat().st_mtime,
            reverse=True
        )

        if not pkl_checkpoints:
            logger.warning("No legacy .pkl checkpoints to migrate")
            return False

        pkl_path = pkl_checkpoints[0]
        logger.warning(f"Migrating legacy checkpoint: {pkl_path}")

        # Load old format
        with open(pkl_path, 'rb') as f:
            checkpoint = pickle.load(f)

        # Restore data
        with self._lock:
            self.documents = checkpoint.documents
            self.doc_ids = checkpoint.doc_ids
            self.metadatas = checkpoint.metadatas
            self.deleted_ids = checkpoint.deleted_ids
            self.version = checkpoint.version

            # Rebuild index
            if self.documents:
                tokenized_corpus = [doc.lower().split() for doc in self.documents]
                self.index = BM25Okapi(tokenized_corpus)

        # Save in new JSON format
        self._save_checkpoint()

        # Delete old .pkl file
        pkl_path.unlink()
        logger.info(f"Migration complete. Deleted legacy checkpoint: {pkl_path}")

        return True

    except Exception as e:
        logger.error(f"Legacy migration failed: {e}")
        return False


def _cleanup_old_checkpoints(self, keep: int = 3) -> None:
    """Remove old checkpoint files."""
    try:
        # Only clean JSON checkpoints (.pkl cleaned during migration)
        checkpoints = sorted(
            self.checkpoint_dir.glob("bm25_checkpoint_v*.json"),
            key=lambda p: p.stat().st_mtime,
            reverse=True
        )

        for old_checkpoint in checkpoints[keep:]:
            old_checkpoint.unlink()
            logger.debug(f"Removed old checkpoint: {old_checkpoint}")

    except Exception as e:
        logger.error(f"Failed to cleanup checkpoints: {e}")
```

**Phase 2: Prevent Future Pickle Usage (1-2h)**

```python
# src/utils/serialization.py (NEW FILE)
"""Secure serialization utilities.

This module provides safe serialization methods for ragged.

SECURITY POLICY: Pickle is BANNED from ragged codebase due to arbitrary
code execution risk. Use JSON for all serialization needs.
"""
import json
from typing import Any, Dict, List
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


def save_json(data: Dict[str, Any], filepath: Path) -> None:
    """Save data to JSON file (secure serialization).

    Args:
        data: Dictionary to serialize
        filepath: Destination file path

    Raises:
        ValueError: If data contains non-serializable types
        IOError: If file write fails
    """
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        logger.debug(f"Saved JSON: {filepath}")
    except TypeError as e:
        raise ValueError(f"Data contains non-JSON-serializable types: {e}")


def load_json(filepath: Path) -> Dict[str, Any]:
    """Load data from JSON file (secure deserialization).

    Args:
        filepath: Source file path

    Returns:
        Deserialized dictionary

    Raises:
        FileNotFoundError: If file doesn't exist
        ValueError: If file contains invalid JSON
    """
    if not filepath.exists():
        raise FileNotFoundError(f"File not found: {filepath}")

    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        logger.debug(f"Loaded JSON: {filepath}")
        return data
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in {filepath}: {e}")


# SECURITY: Explicitly ban pickle
def _banned_pickle_import():
    """This function exists to make pickle import fail in pre-commit hooks."""
    raise ImportError(
        "Pickle is BANNED in ragged due to security vulnerabilities. "
        "Use json serialization instead (see src/utils/serialization.py)"
    )

# Prevent accidental pickle usage (will be caught by tests)
# import pickle  # ← This should NEVER appear in production code
```

**Phase 3: Update Documentation (1h)**

Update all roadmap references to Pickle:
- `docs/development/roadmap/version/v0.2.7/features/performance-optimisations.md` - Remove Pickle-based embedding cache (replace with JSON)
- Add security notice in all documentation

#### Testing Requirements

```python
# tests/security/test_no_pickle.py (NEW FILE)
"""Security test: Verify no Pickle usage in production code."""
import pytest
from pathlib import Path
import re


def test_no_pickle_imports():
    """Verify no 'import pickle' statements in src/."""
    src_dir = Path("src")
    pickle_pattern = re.compile(r'^\s*import\s+pickle', re.MULTILINE)

    violations = []
    for py_file in src_dir.rglob("*.py"):
        content = py_file.read_text()
        if pickle_pattern.search(content):
            violations.append(str(py_file))

    assert not violations, f"Pickle imports found in: {violations}"


def test_no_pickle_usage():
    """Verify no 'pickle.dump' or 'pickle.load' calls in src/."""
    src_dir = Path("src")
    usage_pattern = re.compile(r'pickle\.(dump|load|dumps|loads)')

    violations = []
    for py_file in src_dir.rglob("*.py"):
        content = py_file.read_text()
        matches = usage_pattern.findall(content)
        if matches:
            violations.append(str(py_file))

    assert not violations, f"Pickle usage found in: {violations}"


def test_checkpoints_use_json():
    """Verify BM25 checkpoints are JSON, not Pickle."""
    from src.retrieval.incremental_index import IncrementalBM25Retriever
    import tempfile
    import json

    with tempfile.TemporaryDirectory() as tmpdir:
        retriever = IncrementalBM25Retriever(checkpoint_dir=Path(tmpdir))

        # Index some documents
        retriever.index_documents(
            documents=["test doc 1", "test doc 2"],
            doc_ids=["id1", "id2"]
        )

        # Save checkpoint
        retriever._save_checkpoint()

        # Verify JSON file created (not .pkl)
        json_files = list(Path(tmpdir).glob("*.json"))
        pkl_files = list(Path(tmpdir).glob("*.pkl"))

        assert len(json_files) > 0, "No JSON checkpoint created"
        assert len(pkl_files) == 0, "Pickle checkpoint created (SECURITY VIOLATION)"

        # Verify JSON is valid
        with open(json_files[0]) as f:
            data = json.load(f)

        assert "documents" in data
        assert "doc_ids" in data
        assert data["documents"] == ["test doc 1", "test doc 2"]


def test_legacy_pickle_migration():
    """Verify legacy .pkl files are migrated to .json."""
    from src.retrieval.incremental_index import IncrementalBM25Retriever
    import tempfile
    import pickle
    from dataclasses import dataclass

    @dataclass
    class LegacyCheckpoint:
        documents: list
        doc_ids: list
        metadatas: list
        deleted_ids: set
        timestamp: float
        version: int

    with tempfile.TemporaryDirectory() as tmpdir:
        checkpoint_dir = Path(tmpdir)

        # Create legacy .pkl file
        legacy_checkpoint = LegacyCheckpoint(
            documents=["legacy doc"],
            doc_ids=["legacy_id"],
            metadatas=[{}],
            deleted_ids=set(),
            timestamp=1234567890.0,
            version=1
        )

        legacy_path = checkpoint_dir / "bm25_checkpoint_v1.pkl"
        with open(legacy_path, 'wb') as f:
            pickle.dump(legacy_checkpoint, f)

        # Load via migration
        retriever = IncrementalBM25Retriever(checkpoint_dir=checkpoint_dir)
        success = retriever.load_checkpoint()

        assert success, "Migration failed"
        assert retriever.documents == ["legacy doc"]

        # Verify .pkl deleted and .json created
        assert not legacy_path.exists(), ".pkl not deleted after migration"
        json_files = list(checkpoint_dir.glob("*.json"))
        assert len(json_files) > 0, "JSON checkpoint not created during migration"
```

#### Security Agent Workflow

**Before Implementation:**
```bash
# Run security audit on current codebase
Task(
    subagent_type="codebase-security-auditor",
    prompt="Audit codebase for Pickle usage and deserialization vulnerabilities.
            Focus on src/retrieval/incremental_index.py and any files using pickle module.
            Report: file paths, line numbers, risk level, attack vectors."
)
```

**After Implementation:**
```bash
# Verify Pickle eliminated
Task(
    subagent_type="codebase-security-auditor",
    prompt="Verify zero Pickle usage in production code (src/).
            Confirm all serialization uses JSON.
            Check tests/security/test_no_pickle.py validates security.
            Report: confirmation or any remaining issues."
)
```

#### Acceptance Criteria

- ✅ Zero Pickle imports in `src/` directory
- ✅ BM25 checkpoints saved as `.json` (not `.pkl`)
- ✅ Legacy `.pkl` files migrated to `.json` automatically
- ✅ Security tests pass (`test_no_pickle.py`)
- ✅ Documentation updated (no Pickle references)
- ✅ Security agent confirms no deserialization vulnerabilities

---

### FEAT-SEC-002: Session Isolation for Caches (3-4h)

**Priority:** HIGH
**Dependencies:** None
**Security Agent:** Invoke before AND after implementation

#### Scope

Implement session-scoped caching to prevent PII leakage between users/sessions.

**Risk Mitigated:** Cross-user cache pollution leading to PII exposure

#### Implementation

**Phase 1: Session Management (1-2h)**

```python
# src/core/session.py (NEW FILE)
"""Session management for ragged.

Sessions isolate user data (caches, history, temporary state) to prevent
cross-user information leakage.
"""
import uuid
import time
from typing import Optional, Dict, Any
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class Session:
    """Represents a user session with isolated state."""

    def __init__(self, session_id: Optional[str] = None):
        """Initialize session.

        Args:
            session_id: Explicit session ID (or generate new UUID)
        """
        self.session_id = session_id or self._generate_session_id()
        self.created_at = time.time()
        self.last_activity = time.time()
        self.metadata: Dict[str, Any] = {}

        logger.debug(f"Session created: {self.session_id}")

    @staticmethod
    def _generate_session_id() -> str:
        """Generate cryptographically secure session ID."""
        return str(uuid.uuid4())

    def touch(self) -> None:
        """Update last activity timestamp."""
        self.last_activity = time.time()

    def is_expired(self, timeout_seconds: int = 3600) -> bool:
        """Check if session expired.

        Args:
            timeout_seconds: Inactivity timeout (default: 1 hour)

        Returns:
            True if session inactive for longer than timeout
        """
        return (time.time() - self.last_activity) > timeout_seconds

    def __repr__(self) -> str:
        return f"Session({self.session_id[:8]}...)"


class SessionManager:
    """Manages active sessions and cleanup."""

    def __init__(self):
        """Initialize session manager."""
        self.sessions: Dict[str, Session] = {}
        self._current_session: Optional[Session] = None

    def get_or_create_session(self, session_id: Optional[str] = None) -> Session:
        """Get existing session or create new one.

        Args:
            session_id: Optional explicit session ID

        Returns:
            Session instance
        """
        if session_id and session_id in self.sessions:
            session = self.sessions[session_id]
            session.touch()
            return session

        session = Session(session_id)
        self.sessions[session.session_id] = session
        return session

    def get_current_session(self) -> Session:
        """Get current session (create if none).

        Returns:
            Current session instance
        """
        if self._current_session is None:
            self._current_session = self.get_or_create_session()

        self._current_session.touch()
        return self._current_session

    def set_current_session(self, session: Session) -> None:
        """Set current session."""
        self._current_session = session

    def cleanup_expired_sessions(self, timeout_seconds: int = 3600) -> int:
        """Remove expired sessions and their caches.

        Args:
            timeout_seconds: Inactivity timeout

        Returns:
            Number of sessions cleaned up
        """
        expired = [
            sid for sid, session in self.sessions.items()
            if session.is_expired(timeout_seconds)
        ]

        for sid in expired:
            del self.sessions[sid]
            logger.info(f"Cleaned up expired session: {sid[:8]}...")

        return len(expired)

    def clear_session(self, session_id: str) -> None:
        """Explicitly clear a session.

        Args:
            session_id: Session to clear
        """
        if session_id in self.sessions:
            del self.sessions[session_id]
            logger.info(f"Cleared session: {session_id[:8]}...")


# Global session manager
_session_manager = SessionManager()


def get_session_manager() -> SessionManager:
    """Get global session manager."""
    return _session_manager
```

**Phase 2: Session-Scoped Query Cache (1-2h)**

```python
# src/retrieval/cache.py (MODIFY)

# BEFORE (VULNERABLE):
def _make_key(self, query: str, **kwargs: Any) -> str:
    """Create cache key from query and parameters."""
    key_parts = [query]  # ⚠️ GLOBAL KEY - NO SESSION ISOLATION
    for k in sorted(kwargs.keys()):
        key_parts.append(f"{k}={kwargs[k]}")
    key_string = "|".join(key_parts)
    return hash_content(key_string)

# AFTER (SECURE):
from src.core.session import get_session_manager

def _make_key(self, query: str, session_id: Optional[str] = None, **kwargs: Any) -> str:
    """Create session-scoped cache key.

    Args:
        query: Search query
        session_id: Session ID (or use current session)
        **kwargs: Additional cache key parameters

    Returns:
        Cache key unique to session
    """
    # Get session ID
    if session_id is None:
        session = get_session_manager().get_current_session()
        session_id = session.session_id

    # Build session-scoped key
    key_parts = [
        f"session={session_id}",  # ✅ SESSION ISOLATION
        query
    ]
    for k in sorted(kwargs.keys()):
        key_parts.append(f"{k}={kwargs[k]}")

    key_string = "|".join(key_parts)
    return hash_content(key_string)


def get(
    self,
    query: str,
    session_id: Optional[str] = None,
    **kwargs: Any
) -> Optional[List[Dict[str, Any]]]:
    """Get cached results for query (session-scoped).

    Args:
        query: Search query
        session_id: Session ID (optional, uses current session)
        **kwargs: Additional cache parameters

    Returns:
        Cached results or None if miss
    """
    key = self._make_key(query, session_id=session_id, **kwargs)

    if key in self.cache:
        entry = self.cache[key]

        # Check TTL
        if time.time() - entry['timestamp'] > self.ttl:
            del self.cache[key]
            logger.debug(f"Cache expired for session-scoped query: {query[:50]}...")
            return None

        logger.debug(f"Cache hit for session {session_id[:8] if session_id else 'current'}...")
        return entry['results']

    logger.debug(f"Cache miss for session-scoped query")
    return None
```

**Phase 3: Cleanup on Exit (30min)**

```python
# src/cli/main.py (MODIFY)

def main():
    """Main CLI entry point with session cleanup."""
    from src.core.session import get_session_manager

    try:
        # CLI logic here
        cli()
    finally:
        # Clean up current session on exit
        manager = get_session_manager()
        current = manager.get_current_session()
        manager.clear_session(current.session_id)
        logger.debug("Session cleaned up on exit")
```

#### Testing Requirements

```python
# tests/security/test_session_isolation.py (NEW FILE)
"""Security test: Verify session isolation prevents cache pollution."""
import pytest
from src.core.session import Session, SessionManager
from src.retrieval.cache import QueryCache


def test_sessions_isolated():
    """Verify different sessions have different cache namespaces."""
    cache = QueryCache()

    # Session 1: Cache sensitive data
    session1 = Session()
    cache.set(
        query="sensitive query",
        results=[{"content": "PII data for user A"}],
        session_id=session1.session_id
    )

    # Session 2: Try to access Session 1's cache
    session2 = Session()
    result = cache.get(query="sensitive query", session_id=session2.session_id)

    # SECURITY: Session 2 should NOT see Session 1's data
    assert result is None, "SESSION ISOLATION VIOLATED: Cache leaked between sessions"


def test_same_session_cache_hit():
    """Verify cache works within same session."""
    cache = QueryCache()
    session = Session()

    # Cache data
    cache.set(
        query="test query",
        results=[{"content": "test result"}],
        session_id=session.session_id
    )

    # Retrieve from same session
    result = cache.get(query="test query", session_id=session.session_id)

    assert result is not None, "Cache miss within same session"
    assert result[0]["content"] == "test result"


def test_session_cleanup_clears_cache():
    """Verify session cleanup removes cached data."""
    cache = QueryCache()
    manager = SessionManager()

    session = manager.get_or_create_session()

    # Cache data
    cache.set(
        query="cleanup test",
        results=[{"content": "should be deleted"}],
        session_id=session.session_id
    )

    # Clear session
    manager.clear_session(session.session_id)

    # Cache should be gone
    result = cache.get(query="cleanup test", session_id=session.session_id)
    assert result is None, "Cache not cleared after session cleanup"
```

#### Security Agent Workflow

**Before Implementation:**
```bash
Task(
    subagent_type="codebase-security-auditor",
    prompt="Audit src/retrieval/cache.py for cross-session data leakage risks.
            Check if cache keys include session isolation.
            Report: current isolation mechanism (if any), potential leakage vectors."
)
```

**After Implementation:**
```bash
Task(
    subagent_type="codebase-security-auditor",
    prompt="Verify session isolation implementation prevents cache pollution.
            Check src/core/session.py and src/retrieval/cache.py.
            Confirm tests/security/test_session_isolation.py validates isolation.
            Report: confirmation or any remaining privacy risks."
)
```

#### Acceptance Criteria

- ✅ All cache operations are session-scoped
- ✅ Different sessions cannot access each other's cached data
- ✅ Session cleanup removes all associated cache entries
- ✅ Security tests pass (`test_session_isolation.py`)
- ✅ Security agent confirms no cross-session leakage

---

### FEAT-SEC-003: Security Testing Framework (3-4h)

**Priority:** MEDIUM
**Dependencies:** FEAT-SEC-001, FEAT-SEC-002
**Security Agent:** Invoke after implementation

#### Scope

Establish automated security testing to prevent regression and catch new vulnerabilities.

**Coverage:**
1. Pickle usage detection (prevent reintroduction)
2. Session isolation validation
3. Dependency vulnerability scanning
4. Code pattern security analysis

#### Implementation

**Phase 1: Security Test Suite (2-3h)**

```python
# tests/security/conftest.py (NEW FILE)
"""Security testing fixtures and utilities."""
import pytest
from pathlib import Path


@pytest.fixture
def src_files():
    """Get all Python files in src/."""
    return list(Path("src").rglob("*.py"))


@pytest.fixture
def security_policy():
    """Load security policy configuration."""
    return {
        "banned_imports": ["pickle", "marshal", "shelve"],
        "dangerous_functions": ["eval", "exec", "__import__"],
        "sensitive_data_patterns": [
            r"\bpassword\s*=\s*['\"].*['\"]",
            r"\bapi_key\s*=\s*['\"].*['\"]",
            r"\btoken\s*=\s*['\"].*['\"]",
        ]
    }


# tests/security/test_banned_imports.py (NEW FILE)
"""Test for banned security-risky imports."""
import pytest
import re
from pathlib import Path


def test_no_banned_imports(src_files, security_policy):
    """Verify no banned imports in production code."""
    banned = security_policy["banned_imports"]
    pattern = re.compile(r'^\s*import\s+(' + '|'.join(banned) + r')', re.MULTILINE)

    violations = {}
    for py_file in src_files:
        content = py_file.read_text()
        matches = pattern.findall(content)
        if matches:
            violations[str(py_file)] = matches

    assert not violations, (
        f"Banned imports found:\n" +
        "\n".join(f"  {file}: {imports}" for file, imports in violations.items())
    )


def test_no_dangerous_functions(src_files, security_policy):
    """Verify no dangerous functions in production code."""
    dangerous = security_policy["dangerous_functions"]
    pattern = re.compile(r'\b(' + '|'.join(dangerous) + r')\s*\(')

    violations = {}
    for py_file in src_files:
        # Skip test files (they may use dangerous functions legitimately)
        if "test_" in py_file.name:
            continue

        content = py_file.read_text()
        matches = pattern.findall(content)
        if matches:
            violations[str(py_file)] = matches

    assert not violations, (
        f"Dangerous functions found:\n" +
        "\n".join(f"  {file}: {funcs}" for file, funcs in violations.items())
    )


# tests/security/test_secrets.py (NEW FILE)
"""Test for hardcoded secrets."""
import pytest
import re


def test_no_hardcoded_secrets(src_files, security_policy):
    """Verify no hardcoded secrets in code."""
    violations = {}

    for py_file in src_files:
        content = py_file.read_text()

        for pattern in security_policy["sensitive_data_patterns"]:
            matches = re.findall(pattern, content, re.IGNORECASE)
            if matches:
                if str(py_file) not in violations:
                    violations[str(py_file)] = []
                violations[str(py_file)].extend(matches)

    assert not violations, (
        f"Potential hardcoded secrets found:\n" +
        "\n".join(f"  {file}: {matches}" for file, matches in violations.items())
    )
```

**Phase 2: Dependency Vulnerability Scanning (1h)**

```python
# tests/security/test_dependencies.py (NEW FILE)
"""Test for vulnerable dependencies."""
import pytest
import subprocess
import json


def test_no_vulnerable_dependencies():
    """Check for known vulnerabilities in dependencies using pip-audit."""
    try:
        # Run pip-audit (requires: pip install pip-audit)
        result = subprocess.run(
            ["pip-audit", "--format", "json"],
            capture_output=True,
            text=True,
            check=False
        )

        if result.returncode != 0:
            vulnerabilities = json.loads(result.stdout)

            # Format vulnerability report
            report = []
            for vuln in vulnerabilities.get("dependencies", []):
                report.append(
                    f"  {vuln['name']} {vuln['version']}: "
                    f"{vuln['vulns'][0]['id']} ({vuln['vulns'][0]['severity']})"
                )

            pytest.fail(
                f"Vulnerable dependencies found:\n" + "\n".join(report)
            )

    except FileNotFoundError:
        pytest.skip("pip-audit not installed (run: pip install pip-audit)")


def test_dependencies_are_gpl_compatible():
    """Verify all dependencies are GPL-3.0 compatible."""
    # TODO: Implement license compatibility check
    # For now, manual verification required
    pass
```

**Phase 3: Pre-commit Hook (30min)**

```bash
# .pre-commit-config.yaml (CREATE/UPDATE)
repos:
  - repo: local
    hooks:
      - id: security-tests
        name: Security Tests
        entry: pytest tests/security/ -v
        language: system
        pass_filenames: false
        always_run: true
```

#### Testing Requirements

All security tests must pass:
```bash
pytest tests/security/ -v
```

#### Security Agent Workflow

**After Implementation:**
```bash
Task(
    subagent_type="codebase-security-auditor",
    prompt="Review security testing framework implementation.
            Verify tests/security/ covers critical vulnerabilities.
            Check pre-commit hook prevents security regressions.
            Evaluate: test coverage, false positive rate, maintenance burden.
            Report: assessment and recommendations."
)
```

#### Acceptance Criteria

- ✅ Security test suite created (`tests/security/`)
- ✅ Tests cover: Pickle, session isolation, secrets, dependencies
- ✅ Pre-commit hook runs security tests
- ✅ All security tests pass
- ✅ CI/CD pipeline includes security testing
- ✅ Security agent validates framework effectiveness

---

### FEAT-SEC-004: Security Audit & Documentation (2-3h)

**Priority:** MEDIUM
**Dependencies:** FEAT-SEC-001, FEAT-SEC-002, FEAT-SEC-003
**Security Agent:** Invoke for comprehensive audit

#### Scope

Comprehensive security audit of entire codebase and creation of security documentation.

#### Implementation

**Phase 1: Automated Security Audit (1-2h)**

```python
# scripts/security_audit.py (NEW FILE)
"""Automated security audit script."""
import subprocess
from pathlib import Path
import sys


def run_audit():
    """Run comprehensive security audit."""
    print("🔒 Ragged Security Audit\n")

    failures = []

    # 1. Security tests
    print("1️⃣  Running security tests...")
    result = subprocess.run(["pytest", "tests/security/", "-v"], check=False)
    if result.returncode != 0:
        failures.append("Security tests failed")

    # 2. Dependency vulnerabilities
    print("\n2️⃣  Scanning dependencies for vulnerabilities...")
    result = subprocess.run(["pip-audit"], check=False)
    if result.returncode != 0:
        failures.append("Vulnerable dependencies found")

    # 3. Code quality
    print("\n3️⃣  Checking code quality (ruff)...")
    result = subprocess.run(["ruff", "check", "src/"], check=False)
    if result.returncode != 0:
        failures.append("Code quality issues found")

    # 4. Type checking
    print("\n4️⃣  Running type checks (mypy)...")
    result = subprocess.run(["mypy", "src/"], check=False)
    if result.returncode != 0:
        failures.append("Type errors found")

    # Report
    print("\n" + "="*50)
    if failures:
        print("❌ SECURITY AUDIT FAILED\n")
        for failure in failures:
            print(f"  - {failure}")
        sys.exit(1)
    else:
        print("✅ SECURITY AUDIT PASSED")
        print("   All security checks passed successfully.")
        sys.exit(0)


if __name__ == "__main__":
    run_audit()
```

**Phase 2: Security Documentation (1h)**

Create comprehensive security documentation (handled in Phase 4 of main plan).

#### Security Agent Workflow

**Comprehensive Audit:**
```bash
Task(
    subagent_type="codebase-security-auditor",
    prompt="Perform comprehensive security audit of ragged v0.2.10.

            Check for:
            1. Arbitrary code execution vulnerabilities
            2. Cross-session data leakage
            3. Hardcoded secrets
            4. Insecure dependencies
            5. Insufficient input validation
            6. Insecure file operations
            7. Missing authentication/authorization
            8. Cryptographic weaknesses

            Provide:
            - Vulnerability report with severity ratings
            - Recommended fixes for any findings
            - Security score (0-100)
            - Comparison with v0.2.9 (before fixes)"
)
```

#### Acceptance Criteria

- ✅ Automated audit script created
- ✅ All audit checks pass
- ✅ Security documentation complete
- ✅ Security agent audit passes with score >90
- ✅ Zero CRITICAL or HIGH severity vulnerabilities

---

## Implementation Phases

### Phase 1: Pickle Elimination (4-6h)
1. Implement JSON serialization for BM25 checkpoints
2. Create migration from legacy .pkl files
3. Add security tests to prevent Pickle reintroduction
4. Update documentation
5. **Security agent validation**

### Phase 2: Session Isolation (3-4h)
1. Implement session management system
2. Update query cache for session scoping
3. Add session cleanup on exit
4. Test session isolation
5. **Security agent validation**

### Phase 3: Security Testing (3-4h)
1. Create security test suite
2. Implement pre-commit hooks
3. Add CI/CD security checks
4. **Security agent validation**

### Phase 4: Audit & Documentation (2-3h)
1. Run comprehensive security audit
2. Create security documentation
3. **Security agent comprehensive audit**

**Total:** 12-17h implementation + 3-4h testing/documentation = **15-21h**

---

## Risk Analysis

### Technical Risks

**RISK-001: JSON Performance Impact**
- **Likelihood:** MEDIUM
- **Impact:** LOW
- **Mitigation:**
  - JSON is faster for small data (BM25 checkpoints are small)
  - Benchmark before/after to verify
  - If needed, use msgpack (still safer than Pickle)

**RISK-002: Legacy Checkpoint Migration Failures**
- **Likelihood:** LOW
- **Impact:** MEDIUM (data loss if migration fails)
- **Mitigation:**
  - Backup .pkl files before deletion
  - Extensive migration testing
  - Graceful fallback if migration fails

**RISK-003: Session Management Overhead**
- **Likelihood:** LOW
- **Impact:** LOW
- **Mitigation:**
  - Session operations are lightweight (UUID generation, dict lookups)
  - Cleanup is background task
  - Monitor performance metrics

---

## Quality Gates

### Functional Requirements
- ✅ All existing functionality preserved (no breaking changes)
- ✅ Zero Pickle usage in production code
- ✅ Cache operations are session-scoped
- ✅ Legacy checkpoints migrate successfully

### Security Requirements
- ✅ No arbitrary code execution vulnerabilities
- ✅ No cross-session data leakage
- ✅ Security test suite passes
- ✅ Security agent audit score >90

### Performance Requirements
- ✅ Checkpoint save/load time: ±10% of Pickle baseline
- ✅ Cache hit latency: <1ms additional overhead
- ✅ Session management overhead: <0.1% of total query time

### Quality Requirements
- ✅ Test coverage: >80% for new security code
- ✅ All security tests passing
- ✅ Documentation complete and accurate
- ✅ Zero regressions in existing functionality

---

## Execution Checklist

### Pre-Implementation
- [ ] Read complete v0.2.10 roadmap
- [ ] Review VULN-001, VULN-002, VULN-003 details
- [ ] Understand current Pickle and cache implementation
- [ ] Create feature branch: `feature/v0.2.10-security-hardening`
- [ ] **Run security agent: "before implementation" audit**

### During Implementation
- [ ] Implement FEAT-SEC-001 (Pickle → JSON)
  - [ ] JSON serialization for BM25
  - [ ] Legacy migration
  - [ ] Security tests
  - [ ] **Run security agent: validate Pickle elimination**
- [ ] Implement FEAT-SEC-002 (Session Isolation)
  - [ ] Session management
  - [ ] Session-scoped cache
  - [ ] Cleanup on exit
  - [ ] **Run security agent: validate session isolation**
- [ ] Implement FEAT-SEC-003 (Security Testing)
  - [ ] Security test suite
  - [ ] Pre-commit hooks
  - [ ] **Run security agent: validate testing framework**
- [ ] Implement FEAT-SEC-004 (Audit)
  - [ ] Audit script
  - [ ] **Run security agent: comprehensive audit**

### Testing & Validation
- [ ] All unit tests pass
- [ ] All security tests pass
- [ ] Integration tests pass
- [ ] Manual testing: checkpoint save/load
- [ ] Manual testing: session isolation
- [ ] Performance benchmarks meet requirements
- [ ] Security agent audit score >90

### Documentation
- [ ] Update CHANGELOG.md
- [ ] Update security documentation
- [ ] Add migration guide (Pickle → JSON)
- [ ] Document session management for developers

### Pre-Commit
- [ ] Run security audit script: `python scripts/security_audit.py`
- [ ] All quality gates passed
- [ ] Documentation complete
- [ ] Final security agent audit

### Commit & Release
- [ ] Create PR with security audit results
- [ ] Code review (security focus)
- [ ] Merge to main
- [ ] Tag release: `v0.2.10`
- [ ] Update roadmap status to "Completed"

---

## Agent Workflow

### Security Agent Invocations

**Total:** 6-8 invocations

1. **Before Implementation:** Baseline security audit
2. **After FEAT-SEC-001:** Validate Pickle elimination
3. **After FEAT-SEC-002:** Validate session isolation
4. **After FEAT-SEC-003:** Validate testing framework
5. **After FEAT-SEC-004:** Comprehensive final audit
6. **Optional:** Additional audits if issues found

### Agent Usage Pattern

```python
# Example security agent invocation
Task(
    subagent_type="codebase-security-auditor",
    model="sonnet",  # Use sonnet for security (thoroughness > speed)
    prompt="""
    Audit ragged v0.2.10 for [SPECIFIC SECURITY CONCERN].

    Focus areas:
    - [File/module to audit]
    - [Specific vulnerability pattern]

    Report:
    - Findings with severity (CRITICAL/HIGH/MEDIUM/LOW)
    - File paths and line numbers
    - Recommended fixes
    - Security score (0-100)
    """,
    description="Security audit: [area]"
)
```

---

## Success Criteria

### Security Objectives
- ✅ Zero arbitrary code execution vulnerabilities
- ✅ Zero cross-session data leakage vulnerabilities
- ✅ Security testing framework prevents regressions
- ✅ Security agent audit passes with score >90

### Technical Objectives
- ✅ All Pickle usage eliminated from production code
- ✅ All caches are session-scoped
- ✅ Legacy data migrated successfully
- ✅ Performance impact <10%

### Process Objectives
- ✅ Security agent validates each feature
- ✅ Comprehensive security tests in place
- ✅ Documentation complete
- ✅ Foundation ready for v0.2.11 (Privacy Infrastructure)

---

## Dependencies

### Prerequisites
- ✅ v0.2.9 completed

### Enables
- ➡️ v0.2.11 (Privacy Infrastructure) - builds on secure foundation
- ➡️ v0.3.x - all features depend on security hardening

### External Dependencies
- `pip-audit` - Dependency vulnerability scanning
- Pre-commit hooks - Automated security testing

---

## Related Documentation

- [v0.2.11 - Privacy Infrastructure](../v0.2.11/) - Next version (builds on v0.2.10)
- [Security Policy](../../../../security/policy.md) - Overall security policy
- [Privacy Architecture](../../../../security/privacy-architecture.md) - Privacy design

---

**Status:** Planned

**License:** GPL-3.0
