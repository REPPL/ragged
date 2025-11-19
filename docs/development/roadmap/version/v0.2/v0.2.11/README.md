# v0.2.11 - Privacy Infrastructure

**Category:** Privacy & Data Protection

**Estimated Time:** 20-26 hours

**Status:** Planned

**Priority:** CRITICAL - Must complete before v0.3.x

---

## Overview

Build comprehensive privacy infrastructure to protect user data and enable GDPR compliance. This version implements encryption, PII detection, data lifecycle management, and user privacy controls—establishing privacy-first foundations for all future features.

**Why Critical:** Current implementation has HIGH-RISK privacy gaps:
1. **Unencrypted query history** stores PII in plaintext on disk
2. **No PII redaction** in logs exposes sensitive data
3. **Unlimited data retention** violates privacy-by-design principles
4. **No user controls** for privacy/data collection

**Impact:** Privacy infrastructure required before v0.3.x features (metrics DB, REPL, API) can safely handle user data.

---

## Privacy Issues Addressed

### Critical Privacy Gaps (Must Fix)

**PRIV-001: Unencrypted Sensitive Data at Rest**
- **Location:** `src/cli/commands/history.py:58-65` (query history), future session files, caches
- **Risk:** CRITICAL - PII stored in plaintext, accessible to filesystem attackers
- **Attack Vector:** Attacker gains filesystem access → reads `~/.ragged/query_history.json` → extracts all historical queries and answers
- **Impact:** Complete privacy violation, potential GDPR breach

**PRIV-002: PII Leakage in Logs**
- **Location:** Multiple files logging partial queries (`query[:50]`)
- **Risk:** HIGH - Sensitive data exposed in log files
- **Attack Vector:** Query contains PII in first 50 characters → logged to disk → PII exposure
- **Impact:** Privacy violation, log aggregation exposes sensitive data

**PRIV-003: Unlimited Data Retention**
- **Location:** Query history, caches, metrics (future)
- **Risk:** HIGH - Data retained indefinitely violates data minimization principle
- **Attack Vector:** System accumulates years of user data → attack surface grows → privacy risk compounds
- **Impact:** GDPR non-compliance (no retention limits), increased exposure

**PRIV-004: No User Privacy Controls**
- **Location:** Entire system - no opt-out mechanisms
- **Risk:** MEDIUM - Users cannot control data collection
- **Attack Vector:** User wants to disable history/caching → no mechanism exists → forced data collection
- **Impact:** User autonomy violation, potential regulatory issues

**PRIV-005: No Data Deletion Capability**
- **Location:** No deletion APIs exist
- **Risk:** HIGH - GDPR "right to deletion" impossible to implement
- **Attack Vector:** User requests data deletion (GDPR Article 17) → no mechanism to comply
- **Impact:** GDPR non-compliance, potential fines

---

## Features

### FEAT-PRIV-001: Encryption at Rest (4-5h)

**Priority:** CRITICAL
**Dependencies:** v0.2.10 (secure serialization foundation)
**Security Agent:** Invoke before AND after implementation

#### Scope

Encrypt all persistent sensitive data to protect against filesystem-level attacks.

**Data to Encrypt:**
1. Query history file (`~/.ragged/query_history.json`)
2. Session files (future v0.3.9 REPL)
3. Sensitive cache values
4. Configuration with secrets (API keys, tokens)

**Encryption Method:** Fernet (symmetric encryption via `cryptography` library)
**Key Management:** Per-user encryption keys stored in OS-specific secure locations

#### Implementation

**Phase 1: Encryption Library (1-2h)**

```python
# src/security/encryption.py (NEW FILE)
"""Encryption utilities for ragged.

Provides secure encryption at rest for sensitive user data.
Uses Fernet (AES-128 in CBC mode with HMAC for integrity).
"""
from cryptography.fernet import Fernet, InvalidToken
from pathlib import Path
import logging
import sys
import os

logger = logging.getLogger(__name__)


class EncryptionManager:
    """Manages encryption/decryption of sensitive data at rest."""

    def __init__(self, key_file: Path = None):
        """Initialize encryption manager.

        Args:
            key_file: Path to encryption key file
                     (default: OS-specific secure location)
        """
        if key_file is None:
            key_file = self._get_default_key_path()

        self.key_file = key_file
        self.cipher = self._get_or_create_cipher()

    @staticmethod
    def _get_default_key_path() -> Path:
        """Get OS-specific secure key storage location."""
        if sys.platform == "darwin":  # macOS
            base = Path.home() / "Library" / "Application Support" / "ragged"
        elif sys.platform == "win32":  # Windows
            base = Path(os.getenv("APPDATA", Path.home())) / "ragged"
        else:  # Linux/Unix
            # Follow XDG Base Directory Specification
            base = Path(os.getenv("XDG_DATA_HOME", Path.home() / ".local" / "share")) / "ragged"

        base.mkdir(parents=True, exist_ok=True, mode=0o700)  # User-only permissions
        return base / "encryption.key"

    def _get_or_create_cipher(self) -> Fernet:
        """Get or create Fernet cipher with encryption key."""
        if self.key_file.exists():
            # Load existing key
            with open(self.key_file, 'rb') as f:
                key = f.read()
            logger.debug(f"Loaded encryption key from {self.key_file}")
        else:
            # Generate new key
            key = Fernet.generate_key()

            # Save with restrictive permissions
            self.key_file.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
            with open(self.key_file, 'wb') as f:
                f.write(key)

            # Set file permissions (user read/write only)
            os.chmod(self.key_file, 0o600)

            logger.info(f"Generated new encryption key: {self.key_file}")

        return Fernet(key)

    def encrypt(self, data: bytes) -> bytes:
        """Encrypt data.

        Args:
            data: Plaintext bytes to encrypt

        Returns:
            Encrypted ciphertext bytes
        """
        try:
            encrypted = self.cipher.encrypt(data)
            logger.debug(f"Encrypted {len(data)} bytes → {len(encrypted)} bytes")
            return encrypted
        except Exception as e:
            logger.error(f"Encryption failed: {e}")
            raise

    def decrypt(self, ciphertext: bytes) -> bytes:
        """Decrypt data.

        Args:
            ciphertext: Encrypted bytes to decrypt

        Returns:
            Decrypted plaintext bytes

        Raises:
            InvalidToken: If ciphertext is corrupted or key is wrong
        """
        try:
            decrypted = self.cipher.decrypt(ciphertext)
            logger.debug(f"Decrypted {len(ciphertext)} bytes → {len(decrypted)} bytes")
            return decrypted
        except InvalidToken:
            logger.error("Decryption failed: Invalid token (corrupted data or wrong key)")
            raise
        except Exception as e:
            logger.error(f"Decryption failed: {e}")
            raise

    def encrypt_file(self, plaintext_path: Path, encrypted_path: Path = None) -> Path:
        """Encrypt a file.

        Args:
            plaintext_path: Source file to encrypt
            encrypted_path: Destination encrypted file
                          (default: plaintext_path + .enc)

        Returns:
            Path to encrypted file
        """
        if encrypted_path is None:
            encrypted_path = plaintext_path.with_suffix(plaintext_path.suffix + ".enc")

        # Read plaintext
        with open(plaintext_path, 'rb') as f:
            plaintext = f.read()

        # Encrypt
        ciphertext = self.encrypt(plaintext)

        # Write encrypted
        with open(encrypted_path, 'wb') as f:
            f.write(ciphertext)

        # Set restrictive permissions
        os.chmod(encrypted_path, 0o600)

        logger.info(f"Encrypted file: {plaintext_path} → {encrypted_path}")
        return encrypted_path

    def decrypt_file(self, encrypted_path: Path, decrypted_path: Path = None) -> Path:
        """Decrypt a file.

        Args:
            encrypted_path: Source encrypted file
            decrypted_path: Destination decrypted file
                          (default: encrypted_path without .enc)

        Returns:
            Path to decrypted file
        """
        if decrypted_path is None:
            if encrypted_path.suffix == ".enc":
                decrypted_path = encrypted_path.with_suffix("")
            else:
                decrypted_path = encrypted_path.with_suffix(".dec")

        # Read ciphertext
        with open(encrypted_path, 'rb') as f:
            ciphertext = f.read()

        # Decrypt
        plaintext = self.decrypt(ciphertext)

        # Write decrypted
        with open(decrypted_path, 'wb') as f:
            f.write(plaintext)

        logger.info(f"Decrypted file: {encrypted_path} → {decrypted_path}")
        return decrypted_path

    def rotate_key(self, new_key_file: Path = None) -> None:
        """Rotate encryption key (re-encrypt all data with new key).

        WARNING: This is a destructive operation. Backup data first.

        Args:
            new_key_file: Path for new key (default: generate new in default location)
        """
        logger.warning("Key rotation initiated - this will re-encrypt all data")

        # Generate new key
        new_key = Fernet.generate_key()
        new_cipher = Fernet(new_key)

        # Save new key
        if new_key_file is None:
            new_key_file = self.key_file

        with open(new_key_file, 'wb') as f:
            f.write(new_key)
        os.chmod(new_key_file, 0o600)

        # Update cipher (note: existing encrypted data needs manual re-encryption)
        self.cipher = new_cipher

        logger.info(f"Encryption key rotated: {new_key_file}")
        logger.warning("Existing encrypted files must be re-encrypted with new key")


# Global encryption manager (singleton)
_encryption_manager = None


def get_encryption_manager() -> EncryptionManager:
    """Get global encryption manager (singleton)."""
    global _encryption_manager
    if _encryption_manager is None:
        _encryption_manager = EncryptionManager()
    return _encryption_manager
```

**Phase 2: Encrypt Query History (1-2h)**

```python
# src/cli/commands/history.py (MODIFY)

from src.security.encryption import get_encryption_manager
import json

# BEFORE (VULNERABLE):
def _save_history(self, history: List[Dict]) -> None:
    """Save history to file."""
    with open(self.history_file, 'w') as f:
        json.dump(history, f, indent=2, ensure_ascii=False)  # ⚠️ PLAINTEXT

def _load_history(self) -> List[Dict]:
    """Load history from file."""
    if not self.history_file.exists():
        return []
    with open(self.history_file, 'r') as f:
        return json.load(f)  # ⚠️ PLAINTEXT


# AFTER (SECURE):
def _save_history(self, history: List[Dict]) -> None:
    """Save history to encrypted file."""
    encryption = get_encryption_manager()

    # Serialize to JSON
    json_data = json.dumps(history, indent=2, ensure_ascii=False)

    # Encrypt
    encrypted = encryption.encrypt(json_data.encode('utf-8'))

    # Write encrypted file
    with open(self.history_file, 'wb') as f:
        f.write(encrypted)

    # Set restrictive permissions
    import os
    os.chmod(self.history_file, 0o600)

    logger.debug(f"Saved encrypted history: {len(history)} entries")


def _load_history(self) -> List[Dict]:
    """Load history from encrypted file."""
    if not self.history_file.exists():
        return []

    encryption = get_encryption_manager()

    try:
        # Read encrypted file
        with open(self.history_file, 'rb') as f:
            encrypted = f.read()

        # Decrypt
        decrypted = encryption.decrypt(encrypted)

        # Parse JSON
        history = json.loads(decrypted.decode('utf-8'))

        logger.debug(f"Loaded encrypted history: {len(history)} entries")
        return history

    except Exception as e:
        logger.error(f"Failed to load encrypted history: {e}")
        # Try legacy plaintext migration
        return self._migrate_plaintext_history()


def _migrate_plaintext_history(self) -> List[Dict]:
    """One-time migration from plaintext to encrypted history."""
    legacy_file = self.history_file.with_suffix('.json.legacy')

    # Check if legacy plaintext file exists
    if self.history_file.exists():
        try:
            # Try reading as plaintext
            with open(self.history_file, 'r') as f:
                history = json.load(f)

            logger.warning(f"Migrating plaintext history to encrypted format")

            # Backup plaintext
            import shutil
            shutil.copy(self.history_file, legacy_file)

            # Save encrypted
            self._save_history(history)

            logger.info(f"Migration complete. Legacy backup: {legacy_file}")
            return history

        except (json.JSONDecodeError, UnicodeDecodeError):
            # File already encrypted or corrupted
            logger.error("History file corrupted or already encrypted")
            return []

    return []
```

**Phase 3: Encrypt Session Files (1h - future-proofing for v0.3.9)**

```python
# src/core/session.py (ADD methods)

class Session:
    # ... existing code ...

    def save_to_file(self, filepath: Path) -> None:
        """Save session state to encrypted file.

        Args:
            filepath: Destination file path
        """
        from src.security.encryption import get_encryption_manager
        import json

        encryption = get_encryption_manager()

        # Serialize session data
        session_data = {
            "session_id": self.session_id,
            "created_at": self.created_at,
            "last_activity": self.last_activity,
            "metadata": self.metadata
        }

        json_data = json.dumps(session_data, indent=2)

        # Encrypt
        encrypted = encryption.encrypt(json_data.encode('utf-8'))

        # Write encrypted file
        with open(filepath, 'wb') as f:
            f.write(encrypted)

        import os
        os.chmod(filepath, 0o600)

        logger.debug(f"Saved encrypted session: {filepath}")

    @classmethod
    def load_from_file(cls, filepath: Path) -> 'Session':
        """Load session from encrypted file.

        Args:
            filepath: Source file path

        Returns:
            Loaded session instance
        """
        from src.security.encryption import get_encryption_manager
        import json

        encryption = get_encryption_manager()

        # Read encrypted file
        with open(filepath, 'rb') as f:
            encrypted = f.read()

        # Decrypt
        decrypted = encryption.decrypt(encrypted)

        # Parse JSON
        session_data = json.loads(decrypted.decode('utf-8'))

        # Reconstruct session
        session = cls(session_id=session_data["session_id"])
        session.created_at = session_data["created_at"]
        session.last_activity = session_data["last_activity"]
        session.metadata = session_data["metadata"]

        logger.debug(f"Loaded encrypted session: {filepath}")
        return session
```

#### Testing Requirements

```python
# tests/security/test_encryption.py (NEW FILE)
"""Security test: Verify encryption at rest."""
import pytest
from pathlib import Path
from src.security.encryption import EncryptionManager
import tempfile
import os


def test_encryption_roundtrip():
    """Verify encrypt/decrypt roundtrip preserves data."""
    manager = EncryptionManager()

    plaintext = b"sensitive user data: SSN 123-45-6789"
    ciphertext = manager.encrypt(plaintext)

    # Ciphertext should differ from plaintext
    assert ciphertext != plaintext, "Encryption did nothing"

    # Decrypt should recover plaintext
    decrypted = manager.decrypt(ciphertext)
    assert decrypted == plaintext, "Decryption failed to recover plaintext"


def test_encrypted_file_not_readable():
    """Verify encrypted files don't contain plaintext."""
    with tempfile.TemporaryDirectory() as tmpdir:
        manager = EncryptionManager(key_file=Path(tmpdir) / "test.key")

        plaintext_path = Path(tmpdir) / "secret.txt"
        plaintext_path.write_text("SECRET PASSWORD: hunter2")

        # Encrypt file
        encrypted_path = manager.encrypt_file(plaintext_path)

        # Read encrypted file as text
        encrypted_content = encrypted_path.read_bytes()

        # Plaintext should NOT appear in encrypted file
        assert b"SECRET PASSWORD" not in encrypted_content
        assert b"hunter2" not in encrypted_content


def test_file_permissions_restrictive():
    """Verify encrypted files have user-only permissions."""
    with tempfile.TemporaryDirectory() as tmpdir:
        manager = EncryptionManager(key_file=Path(tmpdir) / "test.key")

        plaintext_path = Path(tmpdir) / "data.txt"
        plaintext_path.write_text("sensitive data")

        encrypted_path = manager.encrypt_file(plaintext_path)

        # Check permissions (should be 0o600 = user read/write only)
        stat = os.stat(encrypted_path)
        perms = stat.st_mode & 0o777

        assert perms == 0o600, f"Insecure permissions: {oct(perms)} (expected 0o600)"


def test_key_file_permissions():
    """Verify encryption key file has restrictive permissions."""
    with tempfile.TemporaryDirectory() as tmpdir:
        key_file = Path(tmpdir) / "encryption.key"
        manager = EncryptionManager(key_file=key_file)

        # Check key file permissions
        stat = os.stat(key_file)
        perms = stat.st_mode & 0o777

        assert perms == 0o600, f"Insecure key permissions: {oct(perms)}"


def test_wrong_key_fails_decryption():
    """Verify decryption fails with wrong key."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Encrypt with key 1
        manager1 = EncryptionManager(key_file=Path(tmpdir) / "key1.key")
        ciphertext = manager1.encrypt(b"secret data")

        # Try to decrypt with key 2
        manager2 = EncryptionManager(key_file=Path(tmpdir) / "key2.key")

        from cryptography.fernet import InvalidToken
        with pytest.raises(InvalidToken):
            manager2.decrypt(ciphertext)


def test_query_history_encrypted():
    """Verify query history is encrypted on disk."""
    from src.cli.commands.history import HistoryManager
    import tempfile

    with tempfile.TemporaryDirectory() as tmpdir:
        history_file = Path(tmpdir) / "history.enc"
        manager = HistoryManager(history_file=history_file)

        # Add sensitive query
        manager.add_entry(
            query="What is John Doe's SSN?",
            answer="John Doe's SSN is 123-45-6789"
        )

        # Read file content
        file_content = history_file.read_bytes()

        # Sensitive data should NOT appear in plaintext
        assert b"SSN" not in file_content, "Query history not encrypted (SSN visible)"
        assert b"123-45-6789" not in file_content, "Answer not encrypted (SSN visible)"
        assert b"John Doe" not in file_content, "Name not encrypted"
```

#### Security Agent Workflow

**Before Implementation:**
```bash
Task(
    subagent_type="codebase-security-auditor",
    prompt="Audit storage of sensitive data in ragged.
            Check: query history, session files, caches, configuration.
            Report: files storing sensitive data unencrypted, privacy risk level."
)
```

**After Implementation:**
```bash
Task(
    subagent_type="codebase-security-auditor",
    prompt="Verify encryption at rest implementation.
            Check: src/security/encryption.py, query history encryption, key management.
            Confirm: all sensitive data encrypted, key storage secure, tests validate encryption.
            Report: encryption coverage, any unencrypted sensitive data remaining."
)
```

#### Acceptance Criteria

- ✅ Encryption library implemented (Fernet)
- ✅ Query history encrypted at rest
- ✅ Session files encrypted (ready for v0.3.9)
- ✅ Encryption keys stored securely (OS-specific locations, 0o600 permissions)
- ✅ Legacy plaintext data migrated automatically
- ✅ Encryption tests pass
- ✅ Security agent confirms encryption coverage

---

### FEAT-PRIV-002: PII Detection & Redaction (3-4h)

**Priority:** HIGH
**Dependencies:** None
**Security Agent:** Invoke after implementation

#### Scope

Detect and redact PII before logging, storage, or transmission to prevent privacy leaks.

**PII Categories:**
1. **Identifiers:** SSN, credit card numbers, phone numbers, email addresses
2. **Personal Names:** First name + last name patterns
3. **Locations:** Full addresses
4. **Medical:** Health information indicators
5. **Financial:** Account numbers, routing numbers

**Redaction Strategy:**
- **Logs:** Hash queries before logging (irreversible)
- **Metrics:** Store query hashes, not plaintext (future v0.3.10)
- **Debug Output:** Redact PII in verbose mode

#### Implementation

**Phase 1: PII Detection (1-2h)**

```python
# src/security/pii.py (NEW FILE)
"""PII detection and redaction utilities.

Detects and redacts Personally Identifiable Information to protect privacy.
"""
import re
import hashlib
from typing import List, Tuple, Optional
import logging

logger = logging.getLogger(__name__)


class PIIDetector:
    """Detects PII patterns in text."""

    # Regex patterns for common PII types
    PATTERNS = {
        "ssn": re.compile(r'\b\d{3}-\d{2}-\d{4}\b'),  # US SSN: 123-45-6789
        "credit_card": re.compile(r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b'),  # Credit card
        "phone": re.compile(r'\b(\+\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b'),  # Phone
        "email": re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'),  # Email
        "ip_address": re.compile(r'\b(?:\d{1,3}\.){3}\d{1,3}\b'),  # IPv4
        "date_of_birth": re.compile(r'\b\d{1,2}/\d{1,2}/\d{4}\b'),  # DOB: MM/DD/YYYY
    }

    def detect(self, text: str) -> List[Tuple[str, str]]:
        """Detect PII in text.

        Args:
            text: Text to scan for PII

        Returns:
            List of (pii_type, matched_value) tuples
        """
        findings = []

        for pii_type, pattern in self.PATTERNS.items():
            matches = pattern.findall(text)
            for match in matches:
                findings.append((pii_type, match if isinstance(match, str) else match[0]))

        if findings:
            logger.warning(f"Detected {len(findings)} PII instances in text")

        return findings

    def contains_pii(self, text: str) -> bool:
        """Check if text contains any PII.

        Args:
            text: Text to check

        Returns:
            True if PII detected
        """
        return len(self.detect(text)) > 0


class PIIRedactor:
    """Redacts PII from text."""

    def __init__(self):
        """Initialize redactor with detector."""
        self.detector = PIIDetector()

    def redact(self, text: str, replacement: str = "[REDACTED]") -> str:
        """Redact PII from text.

        Args:
            text: Text to redact
            replacement: Replacement string for PII (default: [REDACTED])

        Returns:
            Text with PII redacted
        """
        redacted = text

        findings = self.detector.detect(text)

        for pii_type, value in findings:
            # Replace with type-specific marker
            marker = f"[REDACTED-{pii_type.upper()}]"
            redacted = redacted.replace(value, marker)

            logger.debug(f"Redacted {pii_type}: {value[:4]}...")

        return redacted

    def hash_for_logging(self, text: str, salt: str = "ragged-logging") -> str:
        """Hash text for logging (one-way, cannot recover original).

        Args:
            text: Text to hash
            salt: Salt for hash (prevents rainbow table attacks)

        Returns:
            Hex digest of SHA-256 hash
        """
        salted = f"{salt}:{text}".encode('utf-8')
        hash_digest = hashlib.sha256(salted).hexdigest()

        # Return first 16 chars for readability
        return hash_digest[:16]


# Global instances
_pii_detector = PIIDetector()
_pii_redactor = PIIRedactor()


def detect_pii(text: str) -> List[Tuple[str, str]]:
    """Detect PII in text (convenience function)."""
    return _pii_detector.detect(text)


def contains_pii(text: str) -> bool:
    """Check if text contains PII (convenience function)."""
    return _pii_detector.contains_pii(text)


def redact_pii(text: str) -> str:
    """Redact PII from text (convenience function)."""
    return _pii_redactor.redact(text)


def hash_query(query: str) -> str:
    """Hash query for logging (convenience function)."""
    return _pii_redactor.hash_for_logging(query)
```

**Phase 2: Update Logging to Use PII Redaction (1-2h)**

```python
# src/utils/logging.py (MODIFY)

from src.security.pii import hash_query, redact_pii

# BEFORE (VULNERABLE):
logger.debug(f"Cache miss for query: {query[:50]}...")  # ⚠️ LOGS PARTIAL QUERY

# AFTER (SECURE):
query_hash = hash_query(query)
logger.debug(f"Cache miss for query hash: {query_hash}")  # ✅ ONLY LOGS HASH


# Update all logging statements across codebase
# Example pattern:

# src/retrieval/cache.py
def get(self, query: str, **kwargs) -> Optional[List]:
    # OLD: logger.debug(f"Cache lookup for query: {query[:50]}...")
    # NEW:
    query_hash = hash_query(query)
    logger.debug(f"Cache lookup for query hash: {query_hash}")

# src/cli/commands/history.py
def add_entry(self, query: str, answer: str) -> None:
    # OLD: logger.debug(f"Added query to history: {query[:50]}...")
    # NEW:
    query_hash = hash_query(query)
    logger.debug(f"Added query hash to history: {query_hash}")

# src/cli/commands/query.py
def execute_query(self, query: str) -> None:
    # OLD: logger.info(f"Processing query: {query}")
    # NEW:
    query_hash = hash_query(query)
    logger.info(f"Processing query hash: {query_hash}")

    # For verbose/debug output to user (not logs), use redaction:
    if verbose:
        redacted = redact_pii(query)
        print(f"Query: {redacted}")
```

**Phase 3: Add PII Warning for User Input (30min)**

```python
# src/cli/commands/query.py (ADD warning)

def query_command(question: str, ...):
    """Execute query with PII detection warning."""
    from src.security.pii import contains_pii

    # Warn user if query contains PII
    if contains_pii(question):
        logger.warning(
            "⚠️  Query appears to contain personally identifiable information (PII). "
            "Consider using generic terms for privacy."
        )

    # Proceed with query
    result = execute_query(question, ...)
    # ...
```

#### Testing Requirements

```python
# tests/security/test_pii.py (NEW FILE)
"""Security test: Verify PII detection and redaction."""
import pytest
from src.security.pii import PIIDetector, PIIRedactor, hash_query


def test_detect_ssn():
    """Verify SSN detection."""
    detector = PIIDetector()

    text = "User's SSN is 123-45-6789"
    findings = detector.detect(text)

    assert len(findings) > 0, "SSN not detected"
    assert findings[0][0] == "ssn"
    assert findings[0][1] == "123-45-6789"


def test_detect_credit_card():
    """Verify credit card detection."""
    detector = PIIDetector()

    text = "Card number: 4532-1234-5678-9010"
    findings = detector.detect(text)

    assert len(findings) > 0, "Credit card not detected"
    assert findings[0][0] == "credit_card"


def test_detect_email():
    """Verify email detection."""
    detector = PIIDetector()

    text = "Contact: john.doe@example.com"
    findings = detector.detect(text)

    assert len(findings) > 0, "Email not detected"
    assert findings[0][0] == "email"
    assert findings[0][1] == "john.doe@example.com"


def test_redact_pii():
    """Verify PII redaction."""
    redactor = PIIRedactor()

    text = "User john.doe@example.com has SSN 123-45-6789"
    redacted = redactor.redact(text)

    # PII should be replaced
    assert "john.doe@example.com" not in redacted
    assert "123-45-6789" not in redacted

    # Redaction markers should be present
    assert "[REDACTED-EMAIL]" in redacted
    assert "[REDACTED-SSN]" in redacted


def test_hash_query_irreversible():
    """Verify query hashing is one-way."""
    query = "What is John Doe's credit card number?"

    hash1 = hash_query(query)

    # Hash should not contain original text
    assert "John Doe" not in hash1
    assert "credit card" not in hash1

    # Same query should produce same hash
    hash2 = hash_query(query)
    assert hash1 == hash2

    # Different query should produce different hash
    hash3 = hash_query("Different query")
    assert hash1 != hash3


def test_no_pii_in_logs(caplog):
    """Verify logs don't contain PII."""
    from src.cli.commands.query import query_command

    # Execute query with PII
    query = "What is employee SSN 123-45-6789?"

    # (Execute query logic - mocked for test)
    from src.security.pii import hash_query
    import logging
    logger = logging.getLogger("test")
    query_hash = hash_query(query)
    logger.info(f"Processing query hash: {query_hash}")

    # Check logs
    log_output = caplog.text

    # PII should NOT appear in logs
    assert "SSN" not in log_output, "PII keyword in logs"
    assert "123-45-6789" not in log_output, "SSN number in logs"
    assert "employee" not in log_output, "Query content in logs"

    # Hash should appear
    assert query_hash in log_output, "Query hash not logged"
```

#### Security Agent Workflow

**After Implementation:**
```bash
Task(
    subagent_type="codebase-security-auditor",
    prompt="Verify PII detection and redaction implementation.
            Check: src/security/pii.py, logging statements across codebase.
            Scan logs for potential PII leakage (test with sample queries).
            Confirm: all logger calls use hash_query(), no partial query logging.
            Report: PII coverage, any leakage vectors remaining."
)
```

#### Acceptance Criteria

- ✅ PII detector identifies common PII types (SSN, credit cards, emails, phones)
- ✅ PII redactor replaces PII with type-specific markers
- ✅ All logging uses query hashing (no partial queries logged)
- ✅ User warned when inputting PII
- ✅ Tests validate PII detection accuracy
- ✅ Security agent confirms no PII in logs

---

### FEAT-PRIV-003: Data Lifecycle Management (4-5h)

**Priority:** HIGH
**Dependencies:** FEAT-PRIV-001 (encryption)
**Security Agent:** Invoke after implementation

#### Scope

Implement Time-To-Live (TTL) and automatic deletion for all persistent user data.

**Data with TTL:**
1. Query history (default: 30 days)
2. Cached query results (default: 1 hour - already implemented in v0.2.9)
3. Session files (default: 7 days)
4. Metrics data (future v0.3.10, default: 90 days)

**Lifecycle Management:**
- Automatic expiration based on TTL
- Manual cleanup commands
- Configurable retention policies

#### Implementation

**Phase 1: TTL Configuration (30min)**

```python
# src/config/settings.py (ADD)

class Settings(BaseSettings):
    # ... existing settings ...

    # Data Lifecycle Management
    query_history_ttl_days: int = 30
    session_ttl_days: int = 7
    cache_ttl_seconds: int = 3600  # 1 hour (already exists)
    metrics_ttl_days: int = 90  # For future v0.3.10

    # Cleanup schedule
    auto_cleanup_enabled: bool = True
    cleanup_interval_hours: int = 24
```

**Phase 2: Query History TTL (1-2h)**

```python
# src/cli/commands/history.py (MODIFY)

from datetime import datetime, timedelta
from src.config.settings import get_settings

def _load_history(self) -> List[Dict]:
    """Load history with TTL filtering."""
    history = self._load_history_raw()  # Loads all entries

    # Filter expired entries
    settings = get_settings()
    ttl_days = settings.query_history_ttl_days

    if ttl_days > 0:  # 0 = unlimited retention
        cutoff = datetime.now() - timedelta(days=ttl_days)

        filtered = [
            entry for entry in history
            if datetime.fromisoformat(entry['timestamp']) > cutoff
        ]

        removed = len(history) - len(filtered)
        if removed > 0:
            logger.info(f"Filtered {removed} expired history entries (TTL: {ttl_days} days)")
            # Save filtered history (automatic cleanup)
            self._save_history(filtered)

        return filtered

    return history


def cleanup_expired(self) -> int:
    """Explicitly clean up expired history entries.

    Returns:
        Number of entries removed
    """
    history = self._load_history_raw()
    settings = get_settings()
    cutoff = datetime.now() - timedelta(days=settings.query_history_ttl_days)

    before_count = len(history)

    filtered = [
        entry for entry in history
        if datetime.fromisoformat(entry['timestamp']) > cutoff
    ]

    after_count = len(filtered)
    removed = before_count - after_count

    if removed > 0:
        self._save_history(filtered)
        logger.info(f"Cleaned up {removed} expired history entries")

    return removed
```

**Phase 3: Automatic Cleanup Scheduler (2-3h)**

```python
# src/core/cleanup.py (NEW FILE)
"""Automatic data cleanup scheduler.

Periodically removes expired data based on TTL policies.
"""
import threading
import time
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class CleanupScheduler:
    """Schedules automatic cleanup of expired data."""

    def __init__(self, interval_seconds: int = 86400):  # Default: 24 hours
        """Initialize cleanup scheduler.

        Args:
            interval_seconds: Cleanup interval in seconds
        """
        self.interval_seconds = interval_seconds
        self.running = False
        self._thread = None

    def start(self) -> None:
        """Start cleanup scheduler in background thread."""
        if self.running:
            logger.warning("Cleanup scheduler already running")
            return

        self.running = True
        self._thread = threading.Thread(target=self._cleanup_loop, daemon=True)
        self._thread.start()

        logger.info(f"Cleanup scheduler started (interval: {self.interval_seconds}s)")

    def stop(self) -> None:
        """Stop cleanup scheduler."""
        self.running = False
        if self._thread:
            self._thread.join(timeout=5)

        logger.info("Cleanup scheduler stopped")

    def _cleanup_loop(self) -> None:
        """Main cleanup loop (runs in background thread)."""
        while self.running:
            try:
                logger.debug("Running scheduled cleanup...")
                self._perform_cleanup()
                logger.debug("Scheduled cleanup complete")
            except Exception as e:
                logger.error(f"Cleanup failed: {e}")

            # Sleep until next cleanup
            time.sleep(self.interval_seconds)

    def _perform_cleanup(self) -> None:
        """Perform cleanup of all expired data."""
        from src.cli.commands.history import HistoryManager
        from src.core.session import get_session_manager
        from src.config.settings import get_settings

        settings = get_settings()
        total_removed = 0

        # 1. Clean query history
        try:
            history_mgr = HistoryManager()
            removed = history_mgr.cleanup_expired()
            total_removed += removed
            logger.debug(f"Query history: removed {removed} expired entries")
        except Exception as e:
            logger.error(f"Failed to cleanup query history: {e}")

        # 2. Clean expired sessions
        try:
            session_mgr = get_session_manager()
            timeout_seconds = settings.session_ttl_days * 86400
            removed = session_mgr.cleanup_expired_sessions(timeout_seconds)
            total_removed += removed
            logger.debug(f"Sessions: removed {removed} expired sessions")
        except Exception as e:
            logger.error(f"Failed to cleanup sessions: {e}")

        # 3. Future: Clean metrics (v0.3.10)
        # 4. Future: Clean temporary files

        if total_removed > 0:
            logger.info(f"Cleanup complete: removed {total_removed} expired items")


# Global scheduler
_cleanup_scheduler = None


def get_cleanup_scheduler() -> CleanupScheduler:
    """Get global cleanup scheduler (singleton)."""
    global _cleanup_scheduler
    if _cleanup_scheduler is None:
        from src.config.settings import get_settings
        settings = get_settings()

        interval = settings.cleanup_interval_hours * 3600
        _cleanup_scheduler = CleanupScheduler(interval_seconds=interval)

    return _cleanup_scheduler


def start_automatic_cleanup() -> None:
    """Start automatic cleanup scheduler."""
    from src.config.settings import get_settings
    settings = get_settings()

    if settings.auto_cleanup_enabled:
        scheduler = get_cleanup_scheduler()
        scheduler.start()
```

**Phase 4: CLI Cleanup Command (30min)**

```python
# src/cli/commands/cleanup.py (NEW FILE)
"""Data cleanup CLI commands."""
import click
from src.cli.commands.history import HistoryManager
from src.core.session import get_session_manager
from src.core.cleanup import get_cleanup_scheduler


@click.group()
def cleanup():
    """Manage data cleanup and retention."""
    pass


@cleanup.command()
def expired():
    """Clean up all expired data based on TTL policies."""
    from rich.console import Console
    console = Console()

    console.print("[yellow]Cleaning up expired data...[/yellow]")

    # Query history
    history_mgr = HistoryManager()
    removed_history = history_mgr.cleanup_expired()
    console.print(f"  Query history: {removed_history} entries removed")

    # Sessions
    session_mgr = get_session_manager()
    from src.config.settings import get_settings
    settings = get_settings()
    timeout = settings.session_ttl_days * 86400
    removed_sessions = session_mgr.cleanup_expired_sessions(timeout)
    console.print(f"  Sessions: {removed_sessions} sessions removed")

    total = removed_history + removed_sessions
    console.print(f"[green]✓ Cleanup complete: {total} items removed[/green]")


@cleanup.command()
@click.confirmation_option(prompt="Clear ALL query history?")
def clear_history():
    """Clear all query history (requires confirmation)."""
    history_mgr = HistoryManager()
    history_mgr.clear()
    click.echo("✓ Query history cleared")


@cleanup.command()
def schedule():
    """Show automatic cleanup schedule."""
    from src.config.settings import get_settings
    from rich.console import Console
    from rich.table import Table

    settings = get_settings()
    console = Console()

    table = Table(title="Data Retention Policies")
    table.add_column("Data Type", style="cyan")
    table.add_column("TTL", style="magenta")
    table.add_column("Auto-Cleanup", style="green")

    table.add_row("Query History", f"{settings.query_history_ttl_days} days", "✓")
    table.add_row("Sessions", f"{settings.session_ttl_days} days", "✓")
    table.add_row("Cache", f"{settings.cache_ttl_seconds // 3600}h", "✓")
    table.add_row("Metrics (future)", f"{settings.metrics_ttl_days} days", "✓")

    console.print(table)
    console.print(f"\nAuto-cleanup: {'Enabled' if settings.auto_cleanup_enabled else 'Disabled'}")
    console.print(f"Cleanup interval: {settings.cleanup_interval_hours} hours")
```

#### Testing Requirements

```python
# tests/security/test_lifecycle.py (NEW FILE)
"""Test data lifecycle management and TTL."""
import pytest
from datetime import datetime, timedelta
from src.cli.commands.history import HistoryManager
import tempfile
from pathlib import Path


def test_query_history_ttl():
    """Verify query history respects TTL."""
    with tempfile.TemporaryDirectory() as tmpdir:
        history_file = Path(tmpdir) / "history.enc"
        mgr = HistoryManager(history_file=history_file)

        # Add old entry (expired)
        old_entry = {
            "id": 1,
            "timestamp": (datetime.now() - timedelta(days=40)).isoformat(),
            "query": "old query",
            "answer": "old answer"
        }

        # Add recent entry (valid)
        recent_entry = {
            "id": 2,
            "timestamp": datetime.now().isoformat(),
            "query": "recent query",
            "answer": "recent answer"
        }

        # Save both
        mgr._save_history([old_entry, recent_entry])

        # Load (should filter expired with TTL=30 days)
        loaded = mgr._load_history()

        # Only recent entry should remain
        assert len(loaded) == 1, "Expired entry not filtered"
        assert loaded[0]["query"] == "recent query"


def test_cleanup_removes_expired():
    """Verify explicit cleanup removes expired data."""
    with tempfile.TemporaryDirectory() as tmpdir:
        history_file = Path(tmpdir) / "history.enc"
        mgr = HistoryManager(history_file=history_file)

        # Add 10 expired entries
        expired = [
            {
                "id": i,
                "timestamp": (datetime.now() - timedelta(days=40)).isoformat(),
                "query": f"query {i}",
                "answer": f"answer {i}"
            }
            for i in range(10)
        ]

        mgr._save_history(expired)

        # Run cleanup
        removed = mgr.cleanup_expired()

        assert removed == 10, "Not all expired entries removed"

        # Verify file updated
        loaded = mgr._load_history()
        assert len(loaded) == 0, "Expired entries still present after cleanup"
```

#### Security Agent Workflow

**After Implementation:**
```bash
Task(
    subagent_type="codebase-security-auditor",
    prompt="Verify data lifecycle management implementation.
            Check: TTL enforcement, automatic cleanup, manual cleanup commands.
            Test: data older than TTL is actually deleted.
            Confirm: no indefinite data retention (except where explicitly configured).
            Report: lifecycle coverage, any data without TTL protection."
)
```

#### Acceptance Criteria

- ✅ TTL configuration for all persistent data types
- ✅ Query history automatically filters expired entries
- ✅ Automatic cleanup scheduler runs in background
- ✅ Manual cleanup CLI commands work
- ✅ TTL tests pass (old data removed, recent data preserved)
- ✅ Security agent confirms no indefinite retention

---

### FEAT-PRIV-004: GDPR Compliance Foundations (3-4h)

**Priority:** MEDIUM
**Dependencies:** FEAT-PRIV-001, FEAT-PRIV-003
**Security Agent:** Invoke after implementation

#### Scope

Implement foundations for GDPR compliance, focusing on user rights.

**GDPR Rights Implemented:**
1. **Right to Deletion** (Article 17) - Delete all user data
2. **Right to Data Portability** (Article 20) - Export user data
3. **Right to Access** (Article 15) - View stored data

**Future:** Full GDPR compliance requires additional features (consent management, privacy policy, DPO contact) - to be completed in production deployment.

#### Implementation

**Phase 1: Data Deletion API (1-2h)**

```python
# src/privacy/gdpr.py (NEW FILE)
"""GDPR compliance utilities.

Implements user rights under GDPR:
- Right to deletion (Article 17)
- Right to data portability (Article 20)
- Right to access (Article 15)
"""
from pathlib import Path
from typing import Dict, List
import logging
import shutil

logger = logging.getLogger(__name__)


class GDPRManager:
    """Manages GDPR compliance operations."""

    def delete_all_user_data(self, confirm: bool = False) -> Dict[str, int]:
        """Delete ALL user data (Right to Deletion - GDPR Article 17).

        WARNING: This is destructive and irreversible.

        Args:
            confirm: Must be True to proceed (safety check)

        Returns:
            Dictionary of deleted items by category

        Raises:
            ValueError: If confirm is False
        """
        if not confirm:
            raise ValueError(
                "Data deletion requires explicit confirmation. "
                "Set confirm=True to proceed."
            )

        logger.warning("GDPR data deletion initiated - THIS IS IRREVERSIBLE")

        deleted = {
            "query_history": 0,
            "sessions": 0,
            "caches": 0,
            "configurations": 0,
            "encryption_keys": 0,
        }

        # 1. Delete query history
        try:
            from src.cli.commands.history import HistoryManager
            history_mgr = HistoryManager()
            history_mgr.clear()
            deleted["query_history"] = 1
            logger.info("Deleted query history")
        except Exception as e:
            logger.error(f"Failed to delete query history: {e}")

        # 2. Delete all sessions
        try:
            from src.core.session import get_session_manager
            session_mgr = get_session_manager()
            session_count = len(session_mgr.sessions)
            for sid in list(session_mgr.sessions.keys()):
                session_mgr.clear_session(sid)
            deleted["sessions"] = session_count
            logger.info(f"Deleted {session_count} sessions")
        except Exception as e:
            logger.error(f"Failed to delete sessions: {e}")

        # 3. Delete cache directory
        try:
            cache_dir = Path.home() / ".ragged" / "cache"
            if cache_dir.exists():
                shutil.rmtree(cache_dir)
                deleted["caches"] = 1
                logger.info("Deleted cache directory")
        except Exception as e:
            logger.error(f"Failed to delete cache: {e}")

        # 4. Delete user configuration (optional - keep system defaults)
        # Not implemented: Users may want to keep configuration

        # 5. Delete encryption keys (makes encrypted data unrecoverable)
        try:
            from src.security.encryption import get_encryption_manager
            encryption = get_encryption_manager()
            if encryption.key_file.exists():
                encryption.key_file.unlink()
                deleted["encryption_keys"] = 1
                logger.warning("Deleted encryption keys - encrypted data now unrecoverable")
        except Exception as e:
            logger.error(f"Failed to delete encryption keys: {e}")

        total_deleted = sum(deleted.values())
        logger.warning(f"GDPR deletion complete: {total_deleted} items deleted")

        return deleted

    def export_user_data(self, output_path: Path) -> Path:
        """Export all user data (Right to Data Portability - GDPR Article 20).

        Args:
            output_path: Destination file for export (.json)

        Returns:
            Path to exported data file
        """
        import json
        from datetime import datetime

        logger.info(f"Exporting user data to {output_path}")

        export_data = {
            "export_timestamp": datetime.now().isoformat(),
            "ragged_version": "v0.2.11",
            "data_categories": {}
        }

        # 1. Export query history
        try:
            from src.cli.commands.history import HistoryManager
            history_mgr = HistoryManager()
            history = history_mgr._load_history()
            export_data["data_categories"]["query_history"] = history
            logger.info(f"Exported {len(history)} query history entries")
        except Exception as e:
            logger.error(f"Failed to export query history: {e}")
            export_data["data_categories"]["query_history"] = []

        # 2. Export session data
        try:
            from src.core.session import get_session_manager
            session_mgr = get_session_manager()
            sessions = [
                {
                    "session_id": s.session_id,
                    "created_at": s.created_at,
                    "last_activity": s.last_activity,
                    "metadata": s.metadata
                }
                for s in session_mgr.sessions.values()
            ]
            export_data["data_categories"]["sessions"] = sessions
            logger.info(f"Exported {len(sessions)} sessions")
        except Exception as e:
            logger.error(f"Failed to export sessions: {e}")
            export_data["data_categories"]["sessions"] = []

        # 3. Export configuration
        try:
            from src.config.settings import get_settings
            settings = get_settings()
            # Only export non-sensitive settings
            config = {
                k: v for k, v in settings.dict().items()
                if not k.endswith("_key") and not k.endswith("_token")
            }
            export_data["data_categories"]["configuration"] = config
            logger.info("Exported configuration")
        except Exception as e:
            logger.error(f"Failed to export configuration: {e}")
            export_data["data_categories"]["configuration"] = {}

        # Write export file
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)

        logger.info(f"User data exported to {output_path}")
        return output_path

    def list_stored_data(self) -> Dict[str, any]:
        """List all stored user data (Right to Access - GDPR Article 15).

        Returns:
            Summary of stored data by category
        """
        summary = {}

        # Query history
        try:
            from src.cli.commands.history import HistoryManager
            history_mgr = HistoryManager()
            history = history_mgr._load_history()
            summary["query_history"] = {
                "count": len(history),
                "oldest": history[0]["timestamp"] if history else None,
                "newest": history[-1]["timestamp"] if history else None,
            }
        except Exception:
            summary["query_history"] = {"count": 0}

        # Sessions
        try:
            from src.core.session import get_session_manager
            session_mgr = get_session_manager()
            summary["sessions"] = {
                "count": len(session_mgr.sessions),
                "active": [
                    s.session_id for s in session_mgr.sessions.values()
                    if not s.is_expired()
                ]
            }
        except Exception:
            summary["sessions"] = {"count": 0}

        # Cache
        cache_dir = Path.home() / ".ragged" / "cache"
        if cache_dir.exists():
            cache_files = list(cache_dir.rglob("*"))
            summary["cache"] = {
                "files": len(cache_files),
                "size_bytes": sum(f.stat().st_size for f in cache_files if f.is_file())
            }
        else:
            summary["cache"] = {"files": 0, "size_bytes": 0}

        return summary
```

**Phase 2: CLI GDPR Commands (1-2h)**

```python
# src/cli/commands/privacy.py (NEW FILE)
"""Privacy and GDPR compliance CLI commands."""
import click
from pathlib import Path


@click.group()
def privacy():
    """Privacy and GDPR compliance commands."""
    pass


@privacy.command()
@click.confirmation_option(
    prompt="⚠️  This will DELETE ALL your data permanently. Continue?"
)
def delete_all_data():
    """Delete all user data (GDPR Right to Deletion).

    This command permanently deletes:
    - Query history
    - Sessions
    - Caches
    - Encryption keys (makes encrypted data unrecoverable)

    WARNING: THIS IS IRREVERSIBLE.
    """
    from src.privacy.gdpr import GDPRManager
    from rich.console import Console

    console = Console()

    console.print("[red]DELETING ALL USER DATA...[/red]")

    gdpr = GDPRManager()
    deleted = gdpr.delete_all_user_data(confirm=True)

    console.print("\n[green]Data deletion complete:[/green]")
    for category, count in deleted.items():
        if count > 0:
            console.print(f"  ✓ {category}: {count} items deleted")

    console.print("\n[yellow]All user data has been permanently deleted.[/yellow]")


@privacy.command()
@click.argument("output_file", type=click.Path(), default="ragged_data_export.json")
def export_data(output_file):
    """Export all user data (GDPR Right to Data Portability).

    Creates a JSON file containing all your ragged data.
    """
    from src.privacy.gdpr import GDPRManager
    from rich.console import Console

    console = Console()

    output_path = Path(output_file)

    console.print(f"[cyan]Exporting user data to {output_path}...[/cyan]")

    gdpr = GDPRManager()
    export_path = gdpr.export_user_data(output_path)

    console.print(f"[green]✓ Data exported to {export_path}[/green]")


@privacy.command()
def show_data():
    """Show summary of stored user data (GDPR Right to Access)."""
    from src.privacy.gdpr import GDPRManager
    from rich.console import Console
    from rich.table import Table

    console = Console()
    gdpr = GDPRManager()

    summary = gdpr.list_stored_data()

    table = Table(title="Stored User Data")
    table.add_column("Category", style="cyan")
    table.add_column("Details", style="white")

    for category, details in summary.items():
        if isinstance(details, dict):
            detail_str = ", ".join(f"{k}: {v}" for k, v in details.items())
        else:
            detail_str = str(details)

        table.add_row(category, detail_str)

    console.print(table)
```

#### Testing Requirements

```python
# tests/privacy/test_gdpr.py (NEW FILE)
"""Test GDPR compliance features."""
import pytest
from src.privacy.gdpr import GDPRManager
from pathlib import Path
import tempfile
import json


def test_delete_all_data_requires_confirmation():
    """Verify deletion requires explicit confirmation."""
    gdpr = GDPRManager()

    with pytest.raises(ValueError, match="confirmation"):
        gdpr.delete_all_user_data(confirm=False)


def test_delete_all_data_removes_everything():
    """Verify all user data is deleted."""
    gdpr = GDPRManager()

    # Create some data
    from src.cli.commands.history import HistoryManager
    history_mgr = HistoryManager()
    history_mgr.add_entry("test query", "test answer")

    # Delete all data
    deleted = gdpr.delete_all_user_data(confirm=True)

    # Verify deletion
    assert deleted["query_history"] > 0, "History not deleted"

    # Verify history is empty
    history = history_mgr._load_history()
    assert len(history) == 0, "History not empty after deletion"


def test_export_data_creates_file():
    """Verify data export creates valid JSON file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "export.json"

        gdpr = GDPRManager()
        result_path = gdpr.export_user_data(output_path)

        # Verify file created
        assert result_path.exists(), "Export file not created"

        # Verify valid JSON
        with open(result_path) as f:
            data = json.load(f)

        # Verify structure
        assert "export_timestamp" in data
        assert "data_categories" in data
        assert "query_history" in data["data_categories"]


def test_list_stored_data():
    """Verify data listing shows accurate counts."""
    gdpr = GDPRManager()

    # Create some data
    from src.cli.commands.history import HistoryManager
    history_mgr = HistoryManager()
    history_mgr.add_entry("query 1", "answer 1")
    history_mgr.add_entry("query 2", "answer 2")

    # List data
    summary = gdpr.list_stored_data()

    # Verify counts
    assert summary["query_history"]["count"] == 2, "Incorrect query history count"
```

#### Security Agent Workflow

**After Implementation:**
```bash
Task(
    subagent_type="codebase-security-auditor",
    prompt="Verify GDPR compliance implementation.
            Check: deletion API completeness, export accuracy, data listing.
            Test: all user data actually deleted when requested.
            Evaluate: GDPR compliance level (Articles 15, 17, 20).
            Report: compliance assessment, any data not covered by deletion/export."
)
```

#### Acceptance Criteria

- ✅ Delete all data API implemented (Right to Deletion)
- ✅ Export data API implemented (Right to Data Portability)
- ✅ List stored data API implemented (Right to Access)
- ✅ CLI commands for GDPR rights work
- ✅ Deletion is confirmed to be complete (no residual data)
- ✅ Export includes all user data categories
- ✅ Security agent confirms GDPR compliance

---

### FEAT-PRIV-005: Privacy Configuration (2-3h)

**Priority:** LOW
**Dependencies:** FEAT-PRIV-001, FEAT-PRIV-002, FEAT-PRIV-003
**Security Agent:** Invoke after implementation

#### Scope

User-facing privacy controls for data collection and retention.

**Configuration Options:**
1. Enable/disable query history
2. Enable/disable caching
3. Enable/disable metrics collection (future v0.3.10)
4. Customize TTL values
5. Enable/disable automatic cleanup

#### Implementation

**Phase 1: Privacy Settings (1h)**

```python
# src/config/settings.py (ADD)

class Settings(BaseSettings):
    # ... existing settings ...

    # Privacy Controls (user-configurable)
    enable_query_history: bool = True
    enable_query_caching: bool = True
    enable_metrics_collection: bool = True  # For future v0.3.10

    # TTL Customization (already added in FEAT-PRIV-003)
    query_history_ttl_days: int = 30
    session_ttl_days: int = 7
    cache_ttl_seconds: int = 3600
    metrics_ttl_days: int = 90

    # Automatic Cleanup (already added in FEAT-PRIV-003)
    auto_cleanup_enabled: bool = True
    cleanup_interval_hours: int = 24

    # PII Detection
    warn_on_pii_input: bool = True  # Warn user when inputting PII
```

**Phase 2: Privacy Config CLI (1-2h)**

```python
# src/cli/commands/config.py (ADD subcommands)

@config.group()
def privacy():
    """Manage privacy settings."""
    pass


@privacy.command()
def show():
    """Show current privacy settings."""
    from src.config.settings import get_settings
    from rich.console import Console
    from rich.table import Table

    settings = get_settings()
    console = Console()

    table = Table(title="Privacy Settings")
    table.add_column("Setting", style="cyan")
    table.add_column("Value", style="green")

    table.add_row("Query History", "✓" if settings.enable_query_history else "✗")
    table.add_row("Query Caching", "✓" if settings.enable_query_caching else "✗")
    table.add_row("Metrics Collection", "✓" if settings.enable_metrics_collection else "✗")
    table.add_row("PII Warnings", "✓" if settings.warn_on_pii_input else "✗")
    table.add_row("", "")  # Separator
    table.add_row("History TTL", f"{settings.query_history_ttl_days} days")
    table.add_row("Session TTL", f"{settings.session_ttl_days} days")
    table.add_row("Cache TTL", f"{settings.cache_ttl_seconds // 3600} hours")
    table.add_row("", "")  # Separator
    table.add_row("Auto-Cleanup", "✓" if settings.auto_cleanup_enabled else "✗")
    table.add_row("Cleanup Interval", f"{settings.cleanup_interval_hours} hours")

    console.print(table)


@privacy.command()
@click.option("--history/--no-history", default=True, help="Enable/disable query history")
@click.option("--cache/--no-cache", default=True, help="Enable/disable caching")
@click.option("--metrics/--no-metrics", default=True, help="Enable/disable metrics")
@click.option("--pii-warnings/--no-pii-warnings", default=True, help="Enable/disable PII warnings")
def set_options(history, cache, metrics, pii_warnings):
    """Set privacy options."""
    from src.config.settings import update_settings

    updates = {
        "enable_query_history": history,
        "enable_query_caching": cache,
        "enable_metrics_collection": metrics,
        "warn_on_pii_input": pii_warnings,
    }

    update_settings(updates)
    click.echo("✓ Privacy settings updated")


@privacy.command()
@click.argument("ttl_days", type=int)
def set_history_ttl(ttl_days):
    """Set query history TTL in days (0 = unlimited)."""
    from src.config.settings import update_settings

    update_settings({"query_history_ttl_days": ttl_days})
    click.echo(f"✓ Query history TTL set to {ttl_days} days")
```

#### Testing Requirements

```python
# tests/config/test_privacy_config.py (NEW FILE)
"""Test privacy configuration."""
import pytest
from src.config.settings import Settings


def test_default_privacy_settings():
    """Verify default privacy settings are privacy-friendly."""
    settings = Settings()

    # History enabled by default (user convenience)
    assert settings.enable_query_history is True

    # But with reasonable TTL (not unlimited)
    assert settings.query_history_ttl_days == 30

    # Auto-cleanup enabled by default
    assert settings.auto_cleanup_enabled is True

    # PII warnings enabled by default
    assert settings.warn_on_pii_input is True


def test_disable_query_history():
    """Verify disabling query history works."""
    settings = Settings(enable_query_history=False)

    assert settings.enable_query_history is False


def test_customize_ttl():
    """Verify TTL can be customized."""
    settings = Settings(query_history_ttl_days=7)

    assert settings.query_history_ttl_days == 7
```

#### Security Agent Workflow

**After Implementation:**
```bash
Task(
    subagent_type="codebase-security-auditor",
    prompt="Review privacy configuration implementation.
            Check: default settings favor privacy, user controls comprehensive.
            Evaluate: privacy-by-default principle, ease of opt-out.
            Report: privacy configuration assessment, recommendations for defaults."
)
```

#### Acceptance Criteria

- ✅ Privacy settings configurable via CLI
- ✅ Default settings favor privacy (short TTLs, auto-cleanup enabled)
- ✅ User can disable history/caching entirely
- ✅ Privacy settings display command works
- ✅ Configuration tests pass
- ✅ Security agent approves default privacy stance

---

## Implementation Phases

### Phase 1: Encryption at Rest (4-5h)
1. Implement encryption library (Fernet)
2. Encrypt query history
3. Add session file encryption (future-proofing)
4. Test encryption roundtrip
5. **Security agent validation**

### Phase 2: PII Detection & Redaction (3-4h)
1. Implement PII detector
2. Implement PII redactor
3. Update all logging to use query hashing
4. Add PII warnings for user input
5. **Security agent validation**

### Phase 3: Data Lifecycle Management (4-5h)
1. Add TTL configuration
2. Implement query history TTL filtering
3. Create automatic cleanup scheduler
4. Add CLI cleanup commands
5. **Security agent validation**

### Phase 4: GDPR Compliance (3-4h)
1. Implement data deletion API
2. Implement data export API
3. Implement data listing API
4. Add CLI GDPR commands
5. **Security agent validation**

### Phase 5: Privacy Configuration (2-3h)
1. Add privacy settings
2. Create privacy config CLI
3. Test configuration
4. **Security agent validation**

**Total:** 16-21h implementation + 4-5h testing/documentation = **20-26h**

---

## Risk Analysis

### Technical Risks

**RISK-001: Encryption Key Loss**
- **Likelihood:** LOW
- **Impact:** CRITICAL (all encrypted data unrecoverable)
- **Mitigation:**
  - Clear documentation about key location
  - Warning when deleting encryption keys
  - Consider backup/recovery mechanism in future version

**RISK-002: PII Detection False Negatives**
- **Likelihood:** MEDIUM (PII patterns vary widely)
- **Impact:** MEDIUM (some PII may leak into logs)
- **Mitigation:**
  - Hash queries by default (doesn't rely on detection)
  - Regularly update PII patterns
  - Allow custom patterns in configuration

**RISK-003: Performance Impact of Encryption**
- **Likelihood:** LOW
- **Impact:** LOW (encryption is fast for small data)
- **Mitigation:**
  - Fernet is fast (AES hardware acceleration)
  - Benchmark before/after
  - Encryption only on save/load, not in-memory

**RISK-004: GDPR Compliance Gaps**
- **Likelihood:** MEDIUM (full GDPR compliance is complex)
- **Impact:** MEDIUM (potential regulatory issues)
- **Mitigation:**
  - Document current compliance level
  - List future requirements in roadmap
  - Legal review recommended before production deployment

---

## Quality Gates

### Functional Requirements
- ✅ All sensitive data encrypted at rest
- ✅ PII redacted from logs
- ✅ TTL enforced on all persistent data
- ✅ GDPR rights (deletion, export, access) implemented
- ✅ Privacy configuration works

### Security Requirements
- ✅ No plaintext PII on disk
- ✅ Encryption keys stored securely
- ✅ Encryption tests pass
- ✅ PII detection tests pass
- ✅ Security agent audit passes

### Privacy Requirements
- ✅ Data minimization (short TTLs)
- ✅ User control (privacy settings)
- ✅ Transparency (data listing works)
- ✅ Deletion mechanism (GDPR compliance)

### Performance Requirements
- ✅ Encryption overhead: <5% of save/load time
- ✅ PII detection overhead: <1ms per query
- ✅ Cleanup scheduler: <1% CPU usage

---

## Execution Checklist

### Pre-Implementation
- [ ] Read complete v0.2.11 roadmap
- [ ] Review PRIV-001 through PRIV-005 details
- [ ] Understand encryption requirements
- [ ] Create feature branch: `feature/v0.2.11-privacy-infrastructure`
- [ ] **Run security agent: "before implementation" privacy audit**

### During Implementation
- [ ] Implement FEAT-PRIV-001 (Encryption)
  - [ ] Encryption library
  - [ ] Query history encryption
  - [ ] Session file encryption
  - [ ] **Run security agent: validate encryption**
- [ ] Implement FEAT-PRIV-002 (PII Detection)
  - [ ] PII detector
  - [ ] PII redactor
  - [ ] Update logging
  - [ ] **Run security agent: validate PII protection**
- [ ] Implement FEAT-PRIV-003 (Lifecycle Management)
  - [ ] TTL configuration
  - [ ] Automatic cleanup
  - [ ] CLI commands
  - [ ] **Run security agent: validate lifecycle**
- [ ] Implement FEAT-PRIV-004 (GDPR)
  - [ ] Deletion API
  - [ ] Export API
  - [ ] CLI commands
  - [ ] **Run security agent: validate GDPR compliance**
- [ ] Implement FEAT-PRIV-005 (Privacy Config)
  - [ ] Privacy settings
  - [ ] CLI commands
  - [ ] **Run security agent: validate configuration**

### Testing & Validation
- [ ] All unit tests pass
- [ ] All security tests pass
- [ ] All privacy tests pass
- [ ] Integration tests pass
- [ ] Manual testing: encryption/decryption
- [ ] Manual testing: GDPR deletion/export
- [ ] Performance benchmarks meet requirements
- [ ] Security agent audit passes

### Documentation
- [ ] Update CHANGELOG.md
- [ ] Update privacy documentation
- [ ] Add encryption key management guide
- [ ] Document GDPR compliance level
- [ ] Create privacy policy template

### Pre-Commit
- [ ] Run security audit script
- [ ] All quality gates passed
- [ ] Documentation complete
- [ ] Final security agent audit

### Commit & Release
- [ ] Create PR with privacy audit results
- [ ] Code review (privacy focus)
- [ ] Merge to main
- [ ] Tag release: `v0.2.11`
- [ ] Update roadmap status to "Completed"

---

## Agent Workflow

### Security Agent Invocations

**Total:** 6-7 invocations

1. **Before Implementation:** Baseline privacy audit
2. **After FEAT-PRIV-001:** Validate encryption
3. **After FEAT-PRIV-002:** Validate PII protection
4. **After FEAT-PRIV-003:** Validate lifecycle management
5. **After FEAT-PRIV-004:** Validate GDPR compliance
6. **After FEAT-PRIV-005:** Validate privacy configuration
7. **Final:** Comprehensive privacy audit

### Agent Usage Pattern

```python
# Example security agent invocation for privacy
Task(
    subagent_type="codebase-security-auditor",
    model="sonnet",  # Use sonnet for privacy (comprehensive analysis)
    prompt="""
    Audit ragged v0.2.11 for privacy compliance.

    Focus areas:
    - Encryption at rest implementation
    - PII detection and redaction
    - Data lifecycle management (TTL)
    - GDPR compliance (deletion, export, access)
    - User privacy controls

    Evaluate:
    - Privacy-by-design principles
    - GDPR compliance level (Articles 15, 17, 20)
    - Data minimization
    - User autonomy

    Report:
    - Privacy score (0-100)
    - Compliance assessment
    - Recommended improvements
    - Comparison with v0.2.10 (baseline)
    """,
    description="Privacy audit: [area]"
)
```

---

## Success Criteria

### Privacy Objectives
- ✅ All sensitive data encrypted at rest
- ✅ No PII in logs
- ✅ All data has TTL (no indefinite retention)
- ✅ GDPR user rights implemented
- ✅ User privacy controls work

### Technical Objectives
- ✅ Encryption library integrated
- ✅ PII detection accurate
- ✅ Automatic cleanup scheduler works
- ✅ Data deletion complete (no residual data)
- ✅ Performance impact <5%

### Compliance Objectives
- ✅ GDPR Articles 15, 17, 20 implemented
- ✅ Privacy-by-default configuration
- ✅ User can control data collection
- ✅ Privacy policy ready for deployment

### Process Objectives
- ✅ Security agent validates each feature
- ✅ Comprehensive privacy tests pass
- ✅ Documentation complete
- ✅ Foundation ready for v0.3.x (builds on privacy infrastructure)

---

## Dependencies

### Prerequisites
- ✅ v0.2.9 completed
- ✅ v0.2.10 (Security Hardening) completed - builds on secure serialization and session isolation

### Enables
- ➡️ v0.3.9 (REPL) - can safely store session history (encrypted)
- ➡️ v0.3.10 (Metrics DB) - can safely store queries (hashed, encrypted, with TTL)
- ➡️ v0.3.13 (REST API) - multi-user privacy isolation ready

### External Dependencies
- `cryptography` (Fernet encryption) - MIT License
- No additional dependencies required

---

## Related Documentation

- [v0.2.10 - Security Hardening](./v0.2.10/) - Previous version (security foundation)
- [v0.3.9 - REPL](../v0.3/v0.3.9.md) - Builds on encrypted session storage
- [v0.3.10 - Metrics](../v0.3/v0.3.10.md) - Builds on PII redaction and TTL
- [Security Policy](../../security/policy.md) - Overall security policy
- [Privacy Architecture](../../security/privacy-architecture.md) - Privacy design

---

**Status:** Planned

**License:** GPL-3.0
