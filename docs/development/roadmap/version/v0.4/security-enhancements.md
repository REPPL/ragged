# v0.4.x Security Hardening Enhancements

**Purpose**: Optional security enhancements beyond v0.4.3 security baseline

**Status**: Enhancement opportunities for consideration

**Audience**: Security engineers, developers, security-conscious users

---

## Overview

This document identifies **optional security hardening** opportunities for v0.4.x beyond the mandatory security baseline established in v0.4.2-v0.4.3.

**Baseline Security** (v0.4.2-v0.4.3):
- ✅ Security audit passed (v0.4.3 gate)
- ✅ Encryption at rest (AES-256-GCM)
- ✅ Local-only operation (zero network calls)
- ✅ Privacy controls (GDPR Articles 15, 17, 20)
- ✅ PII detection and redaction
- ✅ Security scanning (bandit, safety, pip-audit)

**Enhancement Philosophy**: The baseline provides strong security. These enhancements offer **defense-in-depth** for high-security environments.

---

## Security Enhancement Categories

### Category 1: Advanced Encryption & Key Management

**Priority**: MEDIUM (baseline encryption sufficient for most users)

**Target Users**: High-security environments, compliance-heavy industries

---

#### Enhancement 1.1: Hardware Security Module (HSM) Support

**Current State**: Encryption keys stored in system keyring

**Enhancement**: Add HSM support for key storage and cryptographic operations

**Benefits**:
- Keys never leave HSM
- FIPS 140-2 Level 3+ compliance
- Physical tamper protection
- Centralised key management for enterprises

**Implementation** (estimated 12-15 hours):

**Files to Create/Modify**:
- `ragged/security/hsm.py` (~200 lines) - HSM interface abstraction
- `ragged/security/key_management.py` (~150 lines) - Key management refactor

**Design**:
```python
from abc import ABC, abstractmethod
from typing import Optional

class KeyStore(ABC):
    """Abstract key storage interface."""

    @abstractmethod
    def store_key(self, key_id: str, key_data: bytes) -> bool:
        """Store encryption key securely."""

    @abstractmethod
    def retrieve_key(self, key_id: str) -> Optional[bytes]:
        """Retrieve encryption key."""

    @abstractmethod
    def delete_key(self, key_id: str) -> bool:
        """Permanently delete key."""


class SystemKeyringStore(KeyStore):
    """Current implementation: System keyring storage."""
    # Existing implementation


class HSMStore(KeyStore):
    """Hardware Security Module storage (optional)."""

    def __init__(self, hsm_config: Dict[str, Any]):
        """
        Initialize HSM connection.

        Args:
            hsm_config: HSM configuration (PKCS#11 slot, PIN, etc.)
        """
        self.pkcs11_lib = hsm_config.get("pkcs11_library")
        self.slot_id = hsm_config.get("slot_id")
        # Initialize PKCS#11 connection

    def store_key(self, key_id: str, key_data: bytes) -> bool:
        """Store key in HSM."""
        # Use PKCS#11 to store key in HSM
        pass

    def retrieve_key(self, key_id: str) -> Optional[bytes]:
        """Retrieve key from HSM (or reference for operations)."""
        # Return key handle (not actual key - never leaves HSM)
        pass
```

**Configuration** (`~/.ragged/security.yaml`):
```yaml
key_storage:
  backend: "hsm"  # or "keyring" (default)
  hsm:
    pkcs11_library: "/usr/lib/softhsm/libsofthsm2.so"
    slot_id: 0
    pin_env_var: "RAGGED_HSM_PIN"  # Read PIN from environment
```

**Testing Requirements**:
- Unit tests with mock HSM
- Integration tests with SoftHSM (software HSM for testing)
- Performance tests (HSM operations slower than keyring)

**Dependencies**:
- `python-pkcs11` or `PyKCS11` library
- HSM hardware or SoftHSM for testing

**Trade-offs**:
- **Pro**: Maximum key security, compliance-ready
- **Con**: Complexity, performance overhead, hardware dependency
- **Con**: Most users don't need this level of security

**Recommendation**: Implement as **opt-in** feature for enterprise users

---

#### Enhancement 1.2: Key Rotation & Versioning

**Current State**: Keys generated once, no rotation mechanism

**Enhancement**: Automatic key rotation with versioned encryption

**Benefits**:
- Limit exposure if key compromised
- Compliance requirements (rotate keys quarterly/annually)
- Graceful key migration

**Implementation** (estimated 8-10 hours):

**Design**:
```python
class VersionedEncryption:
    """Encryption with key versioning and rotation support."""

    def __init__(self, key_store: KeyStore):
        self.key_store = key_store
        self.current_version = self._get_current_key_version()

    def encrypt(self, data: bytes) -> bytes:
        """Encrypt with current key version."""
        key = self.key_store.retrieve_key(f"ragged_key_v{self.current_version}")
        encrypted = self._encrypt_aes_gcm(data, key)

        # Prepend version header
        return self._encode_version(self.current_version) + encrypted

    def decrypt(self, data: bytes) -> bytes:
        """Decrypt using key version from header."""
        version = self._decode_version(data)
        key = self.key_store.retrieve_key(f"ragged_key_v{version}")
        encrypted_data = data[self._version_header_size:]

        return self._decrypt_aes_gcm(encrypted_data, key)

    def rotate_keys(self) -> None:
        """Generate new key version and re-encrypt all data."""
        new_version = self.current_version + 1

        # Generate new key
        new_key = self._generate_key()
        self.key_store.store_key(f"ragged_key_v{new_version}", new_key)

        # Re-encrypt all data with new key
        self._reencrypt_all_data(old_version=self.current_version,
                                  new_version=new_version)

        # Update current version
        self.current_version = new_version
```

**CLI Commands**:
```bash
# Manual key rotation
ragged security rotate-keys --confirm

# Check key status
ragged security key-status
# Output:
# Current key version: v3
# Last rotation: 2026-01-15
# Next rotation: 2026-04-15 (in 45 days)

# Auto-rotation configuration
ragged config set security.key_rotation.enabled true
ragged config set security.key_rotation.interval_days 90
```

**Testing Requirements**:
- Key rotation correctness (all data still decryptable)
- Performance impact of re-encryption
- Rollback mechanism if rotation fails

**Trade-offs**:
- **Pro**: Best practice for key management, compliance-ready
- **Con**: Re-encryption expensive for large datasets
- **Con**: Complexity in key lifecycle management

**Recommendation**: Implement for **v0.5.x** if user demand exists

---

### Category 2: Plugin Security Hardening

**Priority**: HIGH (plugins are third-party code - high risk)

**Target Users**: All users (once plugin ecosystem grows)

---

#### Enhancement 2.1: Plugin Sandboxing

**Current State**: Plugins run with full ragged permissions (v0.4.0)

**Enhancement**: Restrict plugin capabilities via sandboxing

**Benefits**:
- Prevent malicious plugins from accessing memory data
- Limit file system access to plugin-specific directories
- Restrict network access (enforce local-only)
- Prevent privilege escalation

**Implementation** (estimated 20-25 hours):

**Approach 1: Python Sandboxing (RestrictedPython)**

**Pros**:
- Pure Python solution
- No external dependencies
- Fine-grained control

**Cons**:
- Can be bypassed by determined attackers
- Performance overhead
- Complex to maintain

**Approach 2: Process Isolation (multiprocessing)**

**Pros**:
- True isolation (separate process)
- OS-level security
- Cannot access parent memory

**Cons**:
- Higher overhead (IPC required)
- More complex error handling
- May break some plugin use cases

**Recommended Approach**: Process isolation for untrusted plugins

**Design**:
```python
from multiprocessing import Process, Queue
from typing import Any, Dict

class SandboxedPlugin:
    """Run plugin in isolated process with restricted permissions."""

    def __init__(self, plugin_path: str, permissions: PluginPermissions):
        self.plugin_path = plugin_path
        self.permissions = permissions
        self.process = None
        self.input_queue = Queue()
        self.output_queue = Queue()

    def execute(self, method: str, *args, **kwargs) -> Any:
        """Execute plugin method in sandboxed environment."""
        # Send request to sandboxed process
        self.input_queue.put({
            "method": method,
            "args": args,
            "kwargs": kwargs
        })

        # Start sandboxed process if not running
        if self.process is None or not self.process.is_alive():
            self.process = Process(target=self._sandbox_worker)
            self.process.start()

        # Wait for result (with timeout)
        try:
            result = self.output_queue.get(timeout=30)
            if isinstance(result, Exception):
                raise result
            return result
        except Empty:
            self.process.terminate()
            raise PluginTimeoutError(f"Plugin '{self.plugin_path}' timed out")

    def _sandbox_worker(self):
        """Worker process with restricted permissions."""
        # Drop privileges
        self._restrict_file_system_access()
        self._restrict_network_access()
        self._restrict_memory_access()

        # Load plugin
        plugin = self._load_plugin_safely(self.plugin_path)

        # Process requests
        while True:
            request = self.input_queue.get()
            try:
                method = getattr(plugin, request["method"])
                result = method(*request["args"], **request["kwargs"])
                self.output_queue.put(result)
            except Exception as e:
                self.output_queue.put(e)

    def _restrict_file_system_access(self):
        """Restrict plugin to specific directories."""
        allowed_paths = [
            Path.home() / ".ragged" / "plugins" / self.plugin_path,
            # Plugin can only access its own directory
        ]
        # Use chroot or mount namespace (Linux) or equivalent

    def _restrict_network_access(self):
        """Block all network access."""
        if self.permissions.allow_network:
            return  # User explicitly allowed network

        # Use network namespace (Linux) or firewall rules
        # Block all outgoing connections

    def _restrict_memory_access(self):
        """Prevent access to ragged's memory data."""
        # Memory data not accessible (separate process)
        # Could add additional restrictions (e.g., memory limits)
```

**Plugin Manifest** (`plugin.yaml`):
```yaml
name: "example-plugin"
version: "1.0.0"
permissions:
  file_system:
    - "~/.ragged/plugins/example-plugin"  # Own directory only
  network: false  # No network access
  memory_access: false  # Cannot read memory data
  max_execution_time: 30  # seconds
  max_memory: 512  # MB
```

**CLI Commands**:
```bash
# Review plugin permissions before installing
ragged plugin inspect my-plugin.whl
# Output:
# Plugin: my-plugin v1.0.0
# Permissions requested:
#   - File system: ~/.ragged/plugins/my-plugin/ (read/write)
#   - Network: NONE
#   - Memory access: NONE
#   - Max execution time: 30s
#
# Install? [y/N]:

# Check installed plugin permissions
ragged plugin permissions list

# Revoke permission (disable plugin)
ragged plugin revoke my-plugin --permission network
```

**Testing Requirements**:
- Malicious plugin tests (try to escape sandbox)
- Permission enforcement tests
- Performance impact measurement

**Trade-offs**:
- **Pro**: Critical for plugin ecosystem security
- **Con**: Complex implementation
- **Con**: Performance overhead
- **Con**: Some legitimate use cases may be restricted

**Recommendation**: **ESSENTIAL** for v0.4.0 plugin system before ecosystem grows

---

#### Enhancement 2.2: Plugin Code Signing & Verification

**Current State**: No code signing (v0.4.0)

**Enhancement**: Cryptographic signatures for plugin authenticity

**Benefits**:
- Verify plugin author identity
- Detect tampering
- Trust model (verified vs unverified plugins)
- Prevent supply chain attacks

**Implementation** (estimated 10-12 hours):

**Design**:
```python
import hashlib
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from pathlib import Path

class PluginSigner:
    """Sign and verify plugin packages."""

    def sign_plugin(self, plugin_path: Path, private_key_path: Path) -> Path:
        """
        Sign plugin with developer's private key.

        Creates plugin.sig file alongside plugin package.
        """
        # Load private key
        with open(private_key_path, "rb") as f:
            private_key = serialization.load_pem_private_key(f.read(), password=None)

        # Compute hash of plugin package
        plugin_hash = self._compute_plugin_hash(plugin_path)

        # Sign hash
        signature = private_key.sign(
            plugin_hash,
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )

        # Write signature file
        sig_path = plugin_path.with_suffix(plugin_path.suffix + ".sig")
        with open(sig_path, "wb") as f:
            f.write(signature)

        return sig_path

    def verify_plugin(self, plugin_path: Path, public_key_path: Path) -> bool:
        """
        Verify plugin signature with developer's public key.

        Returns:
            True if signature valid, False otherwise
        """
        sig_path = plugin_path.with_suffix(plugin_path.suffix + ".sig")
        if not sig_path.exists():
            return False

        # Load public key
        with open(public_key_path, "rb") as f:
            public_key = serialization.load_pem_public_key(f.read())

        # Load signature
        with open(sig_path, "rb") as f:
            signature = f.read()

        # Compute plugin hash
        plugin_hash = self._compute_plugin_hash(plugin_path)

        # Verify signature
        try:
            public_key.verify(
                signature,
                plugin_hash,
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.MAX_LENGTH
                ),
                hashes.SHA256()
            )
            return True
        except Exception:
            return False

    def _compute_plugin_hash(self, plugin_path: Path) -> bytes:
        """Compute SHA-256 hash of plugin package."""
        sha256 = hashlib.sha256()
        with open(plugin_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256.update(chunk)
        return sha256.digest()
```

**CLI Commands**:
```bash
# Developer: Sign plugin
ragged plugin sign my-plugin.whl --key ~/.ragged/dev-keys/private.pem
# Creates: my-plugin.whl.sig

# User: Install with signature verification
ragged plugin install my-plugin.whl --verify --pubkey developer-pubkey.pem
# Output:
# ✅ Signature valid (developer: John Doe <john@example.com>)
# Install plugin? [y/N]:

# User: Configure trust policy
ragged config set plugins.require_signature true
ragged config set plugins.trust_policy "verified_only"  # or "prompt" or "allow_unsigned"

# User: Trust developer's key
ragged plugin trust-key developer-pubkey.pem --name "John Doe"
```

**Trust Model**:
```yaml
# ~/.ragged/plugins/trusted_keys.yaml
trusted_developers:
  - name: "John Doe"
    email: "john@example.com"
    public_key_fingerprint: "SHA256:abc123..."
    trust_level: "full"  # full, partial, untrusted

  - name: "Ragged Official"
    email: "plugins@ragged.dev"
    public_key_fingerprint: "SHA256:def456..."
    trust_level: "full"
```

**Testing Requirements**:
- Signature generation and verification correctness
- Tamper detection (modified plugin fails verification)
- Key revocation handling

**Trade-offs**:
- **Pro**: Essential for trustworthy plugin ecosystem
- **Con**: Requires key management infrastructure
- **Con**: Barrier to entry for plugin developers

**Recommendation**: **HIGHLY RECOMMENDED** for v0.4.0 before plugin ecosystem grows

---

### Category 3: Audit Logging & Monitoring

**Priority**: MEDIUM (useful for forensics and compliance)

**Target Users**: Enterprise users, compliance-heavy environments

---

#### Enhancement 3.1: Comprehensive Audit Logging

**Current State**: Basic audit log for privacy operations (v0.4.3)

**Enhancement**: Detailed security event logging with tamper-proof storage

**Benefits**:
- Forensic analysis after security incident
- Compliance requirements (SOC 2, ISO 27001)
- Detect anomalous behaviour

**Implementation** (estimated 8-10 hours):

**Design**:
```python
import json
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

class AuditLogger:
    """Tamper-evident audit logging for security events."""

    def __init__(self, log_path: Path):
        self.log_path = log_path
        self.previous_hash = self._get_last_entry_hash()

    def log_event(self, event_type: str, details: Dict[str, Any],
                  severity: str = "INFO") -> None:
        """
        Log security event with chained hashing for tamper evidence.

        Args:
            event_type: Type of event (e.g., "memory_access", "plugin_install")
            details: Event details (sanitised - no PII)
            severity: INFO, WARNING, ERROR, CRITICAL
        """
        entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "event_type": event_type,
            "severity": severity,
            "details": details,
            "previous_hash": self.previous_hash
        }

        # Compute hash of this entry
        entry_json = json.dumps(entry, sort_keys=True)
        entry_hash = hashlib.sha256(entry_json.encode()).hexdigest()
        entry["hash"] = entry_hash

        # Write to log
        with open(self.log_path, "a") as f:
            f.write(json.dumps(entry) + "\n")

        # Update previous hash for next entry
        self.previous_hash = entry_hash

    def verify_integrity(self) -> bool:
        """
        Verify audit log integrity (no tampering).

        Returns:
            True if log intact, False if tampered
        """
        previous_hash = None
        with open(self.log_path) as f:
            for line in f:
                entry = json.loads(line)

                # Verify previous hash matches
                if entry["previous_hash"] != previous_hash:
                    return False

                # Recompute hash
                entry_copy = entry.copy()
                entry_hash = entry_copy.pop("hash")
                recomputed_hash = hashlib.sha256(
                    json.dumps(entry_copy, sort_keys=True).encode()
                ).hexdigest()

                if recomputed_hash != entry_hash:
                    return False

                previous_hash = entry_hash

        return True
```

**Events to Log**:

**Authentication & Access**:
- Persona switches
- Failed authentication attempts (if auth added)
- Privilege escalation attempts

**Data Operations**:
- Memory data access (read, write, delete)
- Data exports
- Bulk deletions

**Plugin Operations**:
- Plugin installations
- Plugin permission changes
- Plugin sandbox violations

**Security Operations**:
- Key rotation
- Configuration changes (security settings)
- Security scans initiated

**CLI Commands**:
```bash
# View audit log
ragged security audit-log --since "-7d" --severity WARNING

# Verify log integrity
ragged security verify-audit-log
# Output:
# ✅ Audit log integrity verified (10,342 entries, no tampering detected)

# Export audit log for compliance
ragged security export-audit-log --format csv --output audit-2026-q1.csv
```

**Testing Requirements**:
- Integrity verification correctness
- Tamper detection (modified log detected)
- Performance impact (logging overhead)

**Trade-offs**:
- **Pro**: Critical for forensics and compliance
- **Con**: Disk space usage (logs can grow large)
- **Con**: Slight performance overhead

**Recommendation**: Implement as **opt-in** for enterprise users

---

#### Enhancement 3.2: Anomaly Detection

**Current State**: No behaviour analysis

**Enhancement**: Detect unusual patterns indicating security issues

**Benefits**:
- Early detection of compromised accounts
- Identify malicious plugins
- Alert on suspicious behaviour

**Implementation** (estimated 15-18 hours):

**Anomaly Types**:

**Usage Anomalies**:
- Sudden spike in memory access
- Unusual query patterns (e.g., bulk data extraction)
- Access at unusual times (if user has regular pattern)

**Plugin Anomalies**:
- Plugin attempting restricted operations
- Plugin making unexpected network calls
- Plugin accessing memory data without permission

**Data Anomalies**:
- Large bulk deletions
- Frequent persona switches (possible account sharing)
- Data export to unusual locations

**Design**:
```python
from typing import List, Dict
import numpy as np

class AnomalyDetector:
    """Detect anomalous behaviour patterns."""

    def __init__(self):
        self.baseline_profile = self._load_baseline()

    def analyse_event(self, event: Dict) -> Optional[SecurityAlert]:
        """
        Analyse event for anomalies.

        Returns:
            SecurityAlert if anomaly detected, None otherwise
        """
        anomaly_score = 0.0

        # Check query frequency
        if event["type"] == "memory_query":
            query_rate = self._get_recent_query_rate()
            if query_rate > self.baseline_profile["query_rate_p95"] * 3:
                anomaly_score += 0.5
                reason = f"Query rate spike: {query_rate} queries/min (baseline: {self.baseline_profile['query_rate_p95']})"

        # Check bulk operations
        if event["type"] == "memory_delete" and event["count"] > 100:
            anomaly_score += 0.7
            reason = f"Bulk deletion: {event['count']} interactions"

        # Check time-based anomalies
        if self._is_unusual_time(event["timestamp"]):
            anomaly_score += 0.3
            reason = "Access at unusual time"

        # Threshold for alert
        if anomaly_score >= 0.7:
            return SecurityAlert(
                severity="WARNING" if anomaly_score < 1.0 else "CRITICAL",
                event_type=event["type"],
                anomaly_score=anomaly_score,
                reason=reason,
                recommended_action="Review recent activity, consider password reset"
            )

        return None

    def _load_baseline(self) -> Dict:
        """Load user's normal behaviour baseline."""
        # Analyse past 30 days of audit logs
        # Compute:
        #   - Typical query rate (queries/min)
        #   - Active hours (when user usually active)
        #   - Typical operation patterns
        pass
```

**CLI Commands**:
```bash
# View security alerts
ragged security alerts --since "-7d"
# Output:
# ⚠️  WARNING: Unusual bulk deletion detected
#     Time: 2026-03-15 02:30:18
#     Event: 150 interactions deleted
#     Anomaly score: 0.85
#     Recommended action: Review recent activity
#
# 🔴 CRITICAL: Query rate spike detected
#     Time: 2026-03-15 14:22:45
#     Event: 500 queries in 5 minutes (baseline: 10/min)
#     Anomaly score: 1.2
#     Recommended action: Review recent activity, consider password reset

# Configure anomaly detection
ragged config set security.anomaly_detection.enabled true
ragged config set security.anomaly_detection.sensitivity "high"  # or "medium", "low"
```

**Testing Requirements**:
- False positive rate acceptable (<5%)
- True positive rate high (>80% for known attacks)
- Performance impact minimal

**Trade-offs**:
- **Pro**: Proactive security monitoring
- **Con**: Requires baseline learning period (30 days)
- **Con**: False positives may annoy users
- **Con**: Computational overhead

**Recommendation**: Implement as **opt-in** for v0.5.x, gather user feedback

---

### Category 4: Supply Chain Security

**Priority**: HIGH (dependencies are attack vector)

**Target Users**: All users

---

#### Enhancement 4.1: Dependency Pinning & Verification

**Current State**: Dependencies specified in `pyproject.toml` with version ranges

**Enhancement**: Pin exact versions with cryptographic hash verification

**Benefits**:
- Prevent dependency confusion attacks
- Detect compromised packages
- Reproducible builds

**Implementation** (estimated 4-5 hours):

**Current** (`pyproject.toml`):
```toml
[project]
dependencies = [
    "chromadb>=0.4.0,<0.5.0",
    "sentence-transformers>=2.0.0",
    # Version ranges (flexible but risky)
]
```

**Enhanced** (`pyproject.toml` + `requirements.lock`):

**`pyproject.toml`** (unchanged - for flexibility):
```toml
[project]
dependencies = [
    "chromadb>=0.4.0,<0.5.0",
    "sentence-transformers>=2.0.0",
]
```

**`requirements.lock`** (pinned versions with hashes):
```
# Generated by: pip-compile --generate-hashes
chromadb==0.4.15 \
    --hash=sha256:abc123... \
    --hash=sha256:def456...  # Multiple hashes for different platforms
sentence-transformers==2.2.2 \
    --hash=sha256:789ghi...
# All transitive dependencies pinned too
torch==2.0.1 \
    --hash=sha256:jkl012...
```

**Installation**:
```bash
# Production: Use locked dependencies with hash verification
pip install --require-hashes -r requirements.lock

# Development: Use flexible dependencies
pip install -e .
```

**CI/CD Integration**:
```yaml
# .github/workflows/ci.yml
- name: Install dependencies (with hash verification)
  run: pip install --require-hashes -r requirements.lock
```

**Dependency Update Workflow**:
```bash
# 1. Update requirements.lock
pip-compile --generate-hashes --upgrade

# 2. Run security scan on new dependencies
pip-audit -r requirements.lock

# 3. Run full test suite
pytest

# 4. Commit updated requirements.lock
git add requirements.lock
git commit -m "chore(deps): update dependencies with hash verification"
```

**Testing Requirements**:
- Hash mismatch detected and rejected
- Installation successful with valid hashes
- CI/CD pipeline enforces hash verification

**Trade-offs**:
- **Pro**: Strong protection against supply chain attacks
- **Con**: Slightly more complex dependency management
- **Con**: Need to regenerate lock file when updating

**Recommendation**: **IMPLEMENT IMMEDIATELY** (v0.4.2 or earlier)

---

#### Enhancement 4.2: Automated Vulnerability Scanning

**Current State**: Manual security scans in v0.4.2

**Enhancement**: Automated continuous vulnerability scanning

**Benefits**:
- Early detection of vulnerable dependencies
- Automated pull requests for fixes
- Compliance with security policies

**Implementation** (estimated 2-3 hours - mostly configuration):

**GitHub Actions Workflow** (`.github/workflows/security-scan.yml`):
```yaml
name: Security Vulnerability Scan

on:
  schedule:
    - cron: '0 2 * * *'  # Daily at 2 AM
  pull_request:
  push:
    branches: [main, develop]

jobs:
  security-scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install pip-audit safety bandit

      - name: Run pip-audit (known CVEs)
        run: pip-audit -r requirements.lock --desc

      - name: Run safety (vulnerability database)
        run: safety check -r requirements.lock --json

      - name: Run bandit (code security)
        run: bandit -r src/ -ll -f json

      - name: Upload results
        uses: github/codeql-action/upload-sarif@v2
        with:
          sarif_file: security-scan-results.sarif

      - name: Fail on high/critical findings
        run: |
          # Parse results and fail if high/critical vulnerabilities found
          python scripts/check_security_results.py
```

**Dependabot Configuration** (`.github/dependabot.yml`):
```yaml
version: 2
updates:
  - package-ecosystem: "pip"
    directory: "/"
    schedule:
      interval: "weekly"
    open-pull-requests-limit: 10
    reviewers:
      - "security-team"
    labels:
      - "dependencies"
      - "security"

    # Security updates get priority
    allow:
      - dependency-type: "all"
    security-updates-only: false

    # Automatically approve and merge security updates
    auto-merge:
      enabled: true
      strategy: "squash"
      security-updates-only: true
```

**Testing Requirements**:
- Workflow runs successfully on schedule
- Known vulnerabilities detected
- Pull requests created for updates

**Trade-offs**:
- **Pro**: Automated, continuous protection
- **Con**: Noise from frequent updates
- **Con**: May break compatibility

**Recommendation**: **IMPLEMENT IMMEDIATELY** (v0.4.2)

---

## Implementation Priority Matrix

| Enhancement | Priority | Effort | Impact | Recommended Timeline |
|-------------|----------|--------|--------|---------------------|
| **Dependency Pinning & Verification** | CRITICAL | Low (4-5h) | High | v0.4.2 (immediate) |
| **Automated Vulnerability Scanning** | HIGH | Low (2-3h) | High | v0.4.2 (immediate) |
| **Plugin Code Signing** | HIGH | Medium (10-12h) | High | v0.4.0 (before ecosystem grows) |
| **Plugin Sandboxing** | HIGH | High (20-25h) | Critical | v0.4.0 (essential for plugins) |
| **Audit Logging** | MEDIUM | Medium (8-10h) | Medium | v0.4.5 or v0.5.0 |
| **HSM Support** | MEDIUM | Medium (12-15h) | Low | v0.5.x (enterprise feature) |
| **Key Rotation** | MEDIUM | Medium (8-10h) | Medium | v0.5.x (if demand exists) |
| **Anomaly Detection** | LOW | High (15-18h) | Medium | v0.5.x (experimental) |

---

## Security Testing Enhancements

Beyond v0.4.x's standard security testing, consider:

### Penetration Testing

**Timeline**: After v0.4.9 release

**Scope**:
- Plugin sandbox escape attempts
- Memory data exfiltration attempts
- Privilege escalation testing
- Supply chain attack simulations

**Provider**: External security firm or internal red team

**Cost**: £5,000-£15,000 depending on scope

---

### Security Code Review

**Timeline**: During v0.4.3 (memory system)

**Focus**:
- Cryptographic implementations
- Key management
- Access control logic
- Input validation

**Provider**: Security expert with Python/cryptography background

---

### Threat Modeling Workshop

**Timeline**: Before v0.4.0 (plugin architecture)

**Methodology**: STRIDE (Spoofing, Tampering, Repudiation, Information Disclosure, Denial of Service, Elevation of Privilege)

**Output**: Comprehensive threat model document

---

## Security Monitoring & Incident Response

### Security Monitoring Setup

**Tools to Consider**:
- **Sentry**: Error tracking with security filtering
- **Datadog**: Application performance monitoring
- **AWS GuardDuty**: Threat detection (if cloud deployment)

**Metrics to Track**:
- Failed authentication attempts (if auth added)
- Anomalous memory access patterns
- Plugin sandbox violations
- Unusual network activity

---

### Incident Response Plan

**Preparation** (before incidents):
1. Define security incident categories
2. Establish response team roles
3. Create communication templates
4. Set up secure disclosure process

**Response Workflow**:
1. **Detection**: Automated alerts or user report
2. **Triage**: Assess severity and impact
3. **Containment**: Limit damage
4. **Eradication**: Remove threat
5. **Recovery**: Restore normal operation
6. **Lessons Learned**: Post-mortem and improvements

**Documentation**: `docs/security/incident-response-plan.md`

---

## Secure Disclosure Policy

**For Security Researchers**:

**How to Report**:
- Email: `security@ragged.dev` (PGP key available)
- GitHub Security Advisory (private disclosure)

**What to Include**:
- Vulnerability description
- Steps to reproduce
- Impact assessment
- Proof of concept (if applicable)

**Response Timeline**:
- Initial response: Within 48 hours
- Vulnerability assessment: Within 7 days
- Fix timeline: Depends on severity (critical: 7 days, high: 30 days)
- Public disclosure: After fix deployed (or 90 days, whichever first)

**Bug Bounty**: Consider after v1.0 (scope TBD)

---

## Compliance Considerations

For users with compliance requirements:

### GDPR (Already Covered in v0.4.3)

- ✅ Right to access (Article 15)
- ✅ Right to erasure (Article 17)
- ✅ Right to portability (Article 20)
- ✅ Privacy by design (Article 25)

---

### SOC 2 (For Enterprise)

**Requirements**:
- Audit logging (Enhancement 3.1)
- Access controls (baseline + plugin sandboxing)
- Change management (git history)
- Incident response plan (documented)
- Security monitoring (Enhancement 3.2)

**Timeline**: v0.5.x (if enterprise demand)

---

### ISO 27001 (Information Security)

**Requirements**:
- Risk assessment (threat modeling)
- Security policies (documented)
- Access control (baseline + sandboxing)
- Cryptography (baseline + key rotation)
- Audit logging (Enhancement 3.1)

**Timeline**: v0.5.x (if enterprise demand)

---

## Related Documentation

- [v0.4.2 Security Baseline](v0.4.2.md) - Code quality and security audit preparation
- [v0.4.3 Security Audit](v0.4.5/security-audit.md) - Memory system security requirements
- [v0.4.3 Privacy Framework](v0.4.5/privacy-framework.md) - User privacy controls
- [v0.4.0 Plugin Architecture](v0.4.0.md) - Plugin system foundation
- [Testing Guide](testing-guide.md) - Security testing standards

---

**Status**: Enhancement opportunities documented (ready for prioritisation)
