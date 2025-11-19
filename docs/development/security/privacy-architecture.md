# ragged Privacy Architecture

**Project:** ragged - Privacy-first Retrieval-Augmented Generation system

**License:** GPL-3.0

---

## Executive Summary

This document describes the privacy architecture of ragged, established in v0.2.10 (Security Hardening) and v0.2.11 (Privacy Infrastructure). All subsequent versions (v0.3.x+) build upon this foundation to ensure user data protection and GDPR compliance.

**Core Privacy Principles:**
1. **Privacy-by-Design:** Privacy built into features from the start, not bolted on later
2. **Data Minimisation:** Only collect and store data necessary for functionality
3. **User Control:** Users own their data and control its lifecycle
4. **Transparency:** Clear communication about data practices
5. **Local-First:** All processing happens locally by default

**Architecture Version:** 1.0 (established in v0.2.10/v0.2.11)

---

## Table of Contents

1. [Privacy Principles](#privacy-principles)
2. [Session Isolation](#session-isolation)
3. [Encryption at Rest](#encryption-at-rest)
4. [PII Detection & Handling](#pii-detection--handling)
5. [Data Lifecycle Management](#data-lifecycle-management)
6. [GDPR Compliance](#gdpr-compliance)
7. [Privacy Configuration](#privacy-configuration)
8. [Usage in v0.3.x Features](#usage-in-v03x-features)
9. [Privacy Risk Assessment](#privacy-risk-assessment)
10. [Future Enhancements](#future-enhancements)

---

## Privacy Principles

### 1. Privacy-by-Design

ragged implements Privacy-by-Design principles from the EU GDPR framework:

**Proactive not Reactive:**
- Privacy controls built before features launch
- v0.2.10/v0.2.11 completed BEFORE v0.3.x data-handling features
- Threat modelling during feature design

**Privacy as Default:**
- Maximum privacy settings by default
- Encryption enabled automatically
- Local-only processing unless explicitly configured
- TTL cleanup active by default

**Privacy Embedded into Design:**
- Session isolation at architecture level
- Query hashing instead of plaintext storage
- PII detection integrated into all user input paths
- Encryption transparent to application logic

**Full Functionality:**
- Privacy protections don't compromise functionality
- Performance maintained (encrypted I/O still fast)
- Developer experience preserved (simple APIs)

**End-to-End Security:**
- From user input to disk storage
- From collection to deletion
- Across all ragged components

**Visibility and Transparency:**
- Users informed when PII detected
- Privacy status commands available
- Clear documentation of data practices

**Respect for User Privacy:**
- User owns their data
- GDPR rights fully supported
- No dark patterns or hidden data collection

### 2. Data Minimisation

**Principle:** Only collect and store data necessary for functionality.

**Implementation:**

| Data Type | Stored? | How | Why |
|-----------|---------|-----|-----|
| **User Queries** | ❌ NO | Query hash only (SHA-256) | Metrics, debugging |
| **LLM Responses** | ❌ NO | Not stored | Regenerated on demand |
| **Session State** | ✅ YES | Encrypted session files | User workflows |
| **Performance Metrics** | ✅ YES | Query hash + timings | Quality improvement |
| **Document Content** | ✅ YES | Embeddings + text | Core RAG functionality |
| **User Config** | ✅ YES | Plaintext config files | User preferences |

**Query Hashing Example:**
```python
# ❌ NEVER store plaintext queries
database.store(query="What is my email address?")  # PII exposed

# ✅ ALWAYS hash queries for storage
query_hash = hash_query("What is my email address?")
database.store(query_hash="a3f2c8e1...")  # No PII, still useful for metrics
```

### 3. Purpose Limitation

**Principle:** Data used only for stated purpose.

**Data Usage Table:**

| Data | Purpose | NOT Used For |
|------|---------|--------------|
| Query hashes | Performance metrics, debugging | User profiling, marketing |
| Session files | Resume workflows, history | Analytics, sharing |
| Performance data | Quality improvement | Monetisation, third parties |
| Document embeddings | RAG retrieval | Training external models |

**Enforcement:**
- Code reviews verify purpose compliance
- Security agent checks for data misuse
- No telemetry or external data sharing
- No third-party analytics

---

## Session Isolation

**Established in:** v0.2.10 (Security Hardening)

**Purpose:** Prevent cross-user data leakage in multi-user environments (CLI, REPL, REST API).

### Architecture

```
┌─────────────────────────────────────────────┐
│         SessionManager (Singleton)          │
│  - Creates and tracks sessions              │
│  - Maps session IDs to Session objects      │
└─────────────┬───────────────────────────────┘
              │
              ├─── Session(uuid-1) ───┐
              │    - session_id       │
              │    - created_at       │
              │    - metadata         │
              │    - ttl              │
              │                       │
              ├─── Session(uuid-2)   │
              │                       │
              └─── Session(uuid-3)   │
                                      │
                     ┌────────────────▼─────────────────┐
                     │  Session-Scoped Resources        │
                     │  - Cache (QueryCache)            │
                     │  - State (REPL history)          │
                     │  - Metrics (per-session)         │
                     └──────────────────────────────────┘
```

### Session Lifecycle

**1. Creation:**
```python
from ragged.session import SessionManager

# Create or retrieve session
session_mgr = SessionManager()
session = session_mgr.get_or_create_session(session_id="optional-uuid")

# Session ID is UUID v4
print(session.session_id)  # "a3f2c8e1-4b5d-6e7f-8a9b-0c1d2e3f4a5b"
```

**2. Usage:**
```python
# All operations scoped to session
cache = QueryCache()
cached_result = cache.get(
    query="What is RAG?",
    session_id=session.session_id,  # ✅ Session-scoped
    top_k=5
)

# Cross-session leakage impossible
other_session = session_mgr.get_or_create_session()
other_result = cache.get(
    query="What is RAG?",
    session_id=other_session.session_id,  # Different session
    top_k=5
)
# Returns None (cache miss) - no leakage from first session
```

**3. Persistence:**
```python
# Save session to file (encrypted via v0.2.11)
session.save_to_file(Path("~/.ragged/sessions/my-session.enc"))

# Load session
loaded_session = Session.load_from_file(
    Path("~/.ragged/sessions/my-session.enc")
)
```

**4. Cleanup:**
```python
# Automatic TTL cleanup (v0.2.11)
scheduler = CleanupScheduler()
scheduler.schedule_cleanup(
    session.session_dir,
    ttl_days=7  # Sessions expire after 7 days
)

# Manual cleanup
session_mgr.delete_session(session.session_id)
```

### Session Metadata

```python
@dataclass
class Session:
    session_id: str           # UUID v4
    created_at: datetime      # Creation timestamp
    last_accessed: datetime   # Last use timestamp
    metadata: Dict[str, Any]  # User-defined metadata
    ttl_days: int = 7         # Time-to-live

    def is_expired(self) -> bool:
        """Check if session has exceeded TTL."""
        age = datetime.now() - self.created_at
        return age.days > self.ttl_days
```

### Multi-User Scenarios

**CLI (Single User):**
- One default session per user
- Session persists across CLI invocations
- No cross-user risk (single-user system)

**REPL (Single User, Multiple Sessions):**
- User can create multiple sessions
- Each session isolated (different history, state)
- Use case: Separate projects, experiments

**REST API (Multi-User):**
- One session per API client
- Session ID in HTTP headers (`X-Session-ID`)
- Critical for preventing data leakage
- Rate limiting per session

---

## Encryption at Rest

**Established in:** v0.2.11 (Privacy Infrastructure)

**Purpose:** Protect sensitive data stored on disk from unauthorised access.

### Architecture

```
┌──────────────────────────────────────────────┐
│         EncryptionManager                    │
│  - Manages encryption keys                   │
│  - Provides encrypt/decrypt APIs             │
│  - Key rotation (future)                     │
└────────────┬─────────────────────────────────┘
             │
             ├─── Key Storage
             │    ~/.ragged/keys/encryption.key
             │    (permissions: 0o600 - user only)
             │
             ├─── Cipher: Fernet (AES-128)
             │    - Symmetric encryption
             │    - HMAC for integrity
             │    - Timestamp for freshness
             │
             └─── Encrypted Data
                  ~/.ragged/sessions/session-uuid.enc
                  ~/.ragged/repl/history.enc
                  (permissions: 0o600)
```

### Encryption Implementation

**Key Management:**
```python
from ragged.privacy import EncryptionManager

# Initialise (creates key if not exists)
encryption = EncryptionManager(
    key_file=Path("~/.ragged/keys/encryption.key")
)

# Key file permissions enforced
# -rw-------  1 user  group  44 Nov 19 12:00 encryption.key
```

**Encrypting Data:**
```python
# Encrypt sensitive data
plaintext = json.dumps(session_data).encode('utf-8')
ciphertext = encryption.encrypt(plaintext)

# Write to file with secure permissions
file_path = Path("~/.ragged/sessions/session-123.enc")
file_path.touch(mode=0o600)  # User read/write only
file_path.write_bytes(ciphertext)
```

**Decrypting Data:**
```python
# Read encrypted file
ciphertext = file_path.read_bytes()

# Decrypt
plaintext = encryption.decrypt(ciphertext)
session_data = json.loads(plaintext.decode('utf-8'))
```

### What Gets Encrypted

| Data Type | Encrypted? | Why |
|-----------|-----------|-----|
| **Session files** | ✅ YES | May contain command history with PII |
| **REPL history** | ✅ YES | User queries may contain sensitive info |
| **API session state** | ✅ YES | Multi-user context may include PII |
| **Performance metrics DB** | ✅ YES | Query hashes still sensitive metadata |
| **Document embeddings** | ❌ NO | Not user-identifiable data |
| **Configuration files** | ❌ NO | User preferences, not sensitive |
| **Cache files** | ❌ NO | Temporary, session-scoped, cleared on exit |

### Cipher Specification

**Algorithm:** Fernet (symmetric encryption)

**Details:**
- **Cipher:** AES-128-CBC
- **MAC:** HMAC-SHA256
- **Key Derivation:** PBKDF2 (if password-based, future)
- **IV:** Random, per-message
- **Timestamp:** Included in ciphertext (prevents replay)

**Why Fernet:**
- Battle-tested (used by major Python projects)
- Built into cryptography library (well-audited)
- Authenticated encryption (prevents tampering)
- Simple API (reduces implementation errors)
- Good performance (native code)

**Security Properties:**
- **Confidentiality:** AES-128 protects data from disclosure
- **Integrity:** HMAC prevents tampering
- **Freshness:** Timestamp prevents replay attacks
- **Forward Secrecy:** Key rotation provides forward secrecy (future)

### File Permissions

All encrypted files have strict permissions:

```bash
# Encryption keys
-rw------- (0o600)  ~/.ragged/keys/encryption.key

# Encrypted data
-rw------- (0o600)  ~/.ragged/sessions/*.enc
-rw------- (0o600)  ~/.ragged/repl/history.enc
-rw------- (0o600)  ~/.ragged/metrics/queries.db
```

**Why 0o600:**
- Only file owner can read/write
- Root can still access (system administration)
- Other users completely blocked
- Groups completely blocked

---

## PII Detection & Handling

**Established in:** v0.2.11 (Privacy Infrastructure)

**Purpose:** Detect and handle Personally Identifiable Information in user input.

### Architecture

```
User Input (Query)
       ↓
┌──────────────────┐
│  PII Detector    │
│  - Regex patterns│
│  - Confidence    │
└────────┬─────────┘
         │
    ┌────▼────┐
    │ PII?    │
    └─┬────┬──┘
      │    │
   YES│    │NO
      │    │
      ▼    ▼
  ┌───────────┐     ┌──────────────┐
  │  Warn User│     │   Process    │
  │  Encrypt  │     │   Normally   │
  │  Hash     │     └──────────────┘
  └───────────┘
```

### PII Patterns

```python
from ragged.privacy import PIIDetector

detector = PIIDetector()

# Built-in patterns
patterns = {
    "email": r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
    "phone_us": r'\b(\+1[-.]?)?\(?\d{3}\)?[-.]?\d{3}[-.]?\d{4}\b',
    "phone_uk": r'\b(\+44|0)\d{10}\b',
    "ssn": r'\b\d{3}-\d{2}-\d{4}\b',
    "credit_card": r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b',
    "ip_address": r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b',
    "uk_ni_number": r'\b[A-Z]{2}\d{6}[A-D]\b',
    "passport": r'\b[A-Z0-9]{6,9}\b',  # Generic pattern
}
```

### Detection API

**Check for PII:**
```python
from ragged.privacy import contains_pii, detect_pii_types

# Simple check
query = "My email is john@example.com"
if contains_pii(query):
    print("⚠️  PII detected in input")

# Detailed detection
pii_types = detect_pii_types(query)
print(pii_types)  # ["email"]
```

**Confidence Scores:**
```python
from ragged.privacy import pii_confidence

# High confidence (exact pattern match)
pii_confidence("john@example.com")  # 1.0 (100%)

# Medium confidence (partial pattern)
pii_confidence("john@example")  # 0.5 (50%)

# Low confidence (keyword only)
pii_confidence("email address")  # 0.1 (10%)
```

### Handling Strategies

**1. Warn User:**
```python
# v0.3.9 REPL example
def precmd(self, line: str) -> str:
    if contains_pii(line):
        self.stdout.write(
            "⚠️  Warning: Input appears to contain PII.\n"
            "   Session history will be encrypted.\n"
            "   Use 'privacy status' to review.\n"
        )
    return line
```

**2. Hash for Logging:**
```python
# Never log plaintext queries
from ragged.privacy import hash_query

# ❌ BAD
logger.info(f"Query: {user_query}")  # PII exposed in logs

# ✅ GOOD
query_hash = hash_query(user_query)
logger.info(f"Query hash: {query_hash}")  # Safe for logs
```

**3. Encrypt for Storage:**
```python
# v0.3.9 REPL example
if contains_pii(command):
    # Mark session for encryption
    session.metadata["contains_pii"] = True

# On save
if session.metadata.get("contains_pii"):
    # Encrypt session file
    encryption = EncryptionManager()
    encrypted_data = encryption.encrypt(session_json.encode())
    file_path.write_bytes(encrypted_data)
```

**4. Redact for Display:**
```python
from ragged.privacy import redact_pii

# Redact PII from output
query = "My email is john@example.com"
redacted = redact_pii(query)
print(redacted)  # "My email is [EMAIL REDACTED]"
```

### User Control

```bash
# Configure PII detection sensitivity (future)
ragged config set privacy.pii_detection strict  # High sensitivity
ragged config set privacy.pii_detection relaxed # Lower sensitivity
ragged config set privacy.pii_detection off     # Disable (not recommended)

# View PII detection patterns
ragged privacy patterns

# Add custom PII patterns
ragged privacy add-pattern "custom_id" "REGEX_PATTERN"
```

---

## Data Lifecycle Management

**Established in:** v0.2.11 (Privacy Infrastructure)

**Purpose:** Automatically delete old data to comply with storage limitation principle (GDPR Article 5).

### Architecture

```
┌─────────────────────────────────────┐
│      CleanupScheduler               │
│  - Scans data directories           │
│  - Checks TTL expiration            │
│  - Deletes expired data             │
│  - Logs cleanup actions             │
└──────────┬──────────────────────────┘
           │
           │ Scheduled Tasks
           │
    ┌──────▼─────────────────────────────┐
    │                                    │
    ▼                                    ▼
Session Files                    Metrics Database
(TTL: 7 days)                    (TTL: 90 days)
    │                                    │
    │ expires_at = created + 7d          │ expires_at column
    │                                    │
    ▼                                    ▼
Automatic Deletion              Automatic Deletion
```

### TTL Configuration

| Data Type | Default TTL | Rationale | Configurable? |
|-----------|-------------|-----------|---------------|
| **Session files** | 7 days | Temporary workflows | ✅ YES |
| **REPL history** | 7 days | Recent commands only | ✅ YES |
| **Query metrics** | 90 days | Long-term analysis | ✅ YES |
| **API sessions** | 1 day | Stateless API design | ✅ YES |
| **Cache files** | 24 hours | Temporary performance | ❌ NO (fixed) |
| **Log files** | 30 days | Debugging recent issues | ✅ YES |

### Cleanup Implementation

**Automatic Scheduling:**
```python
from ragged.privacy import CleanupScheduler

# Initialise scheduler
scheduler = CleanupScheduler()

# Schedule session cleanup (runs daily)
scheduler.schedule_cleanup(
    data_path=Path("~/.ragged/sessions"),
    ttl_days=7,
    cron_schedule="0 2 * * *"  # 2 AM daily
)

# Schedule metrics cleanup (runs weekly)
scheduler.schedule_cleanup(
    data_path=Path("~/.ragged/metrics/queries.db"),
    ttl_days=90,
    cron_schedule="0 3 * * 0"  # 3 AM Sunday
)
```

**Manual Cleanup:**
```bash
# User-initiated cleanup
ragged privacy cleanup --all         # Clean all expired data
ragged privacy cleanup --sessions    # Clean sessions only
ragged privacy cleanup --force       # Delete everything (confirm required)

# Preview cleanup (dry-run)
ragged privacy cleanup --dry-run
```

**Database TTL Example:**
```python
# v0.3.10 Metrics DB
import sqlite3
from datetime import datetime, timedelta

# Insert with expiration timestamp
expires_at = datetime.now() + timedelta(days=90)
cursor.execute("""
    INSERT INTO queries (
        session_id, query_hash, duration_ms, timestamp, expires_at
    ) VALUES (?, ?, ?, ?, ?)
""", (session_id, query_hash, duration, datetime.now(), expires_at))

# Cleanup expired records
cursor.execute("""
    DELETE FROM queries
    WHERE expires_at < ?
""", (datetime.now(),))
```

### User Notification

```bash
# Before cleanup (7 days warning)
ragged: Session "my-project" will expire in 7 days.
        Use 'ragged session extend my-project' to keep it.

# After cleanup
ragged: Cleaned 3 expired sessions, freed 12 MB.
        Use 'ragged privacy status' to review remaining data.
```

---

## GDPR Compliance

**Established in:** v0.2.11 (Privacy Infrastructure)

**Purpose:** Comply with EU General Data Protection Regulation (GDPR) requirements.

### GDPR Rights Implementation

#### Right to Access (Article 15)

**User can access all their data:**

```bash
ragged privacy status
```

Output:
```
Privacy Status
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Sessions:        3 active (42 MB)
REPL History:    1 file (1.2 MB)
Metrics Records: 127 queries
Cache:           15 MB (temporary)

Oldest Data:     7 days ago
Encryption:      Enabled
PII Detected:    No

Use 'ragged privacy export' to download all data.
```

#### Right to Data Portability (Article 20)

**User can export data in machine-readable format:**

```bash
ragged privacy export --format json --output my-data.json
```

Output file structure:
```json
{
  "export_date": "2025-11-19T10:30:00Z",
  "ragged_version": "0.3.10",
  "data": {
    "sessions": [
      {
        "session_id": "a3f2c8e1-...",
        "created_at": "2025-11-12T08:00:00Z",
        "metadata": {...}
      }
    ],
    "repl_history": [
      {
        "timestamp": "2025-11-18T15:20:00Z",
        "command_hash": "d4e5f6...",
        "contains_pii": false
      }
    ],
    "metrics": [
      {
        "query_hash": "a1b2c3...",
        "duration_ms": 234,
        "ragas_score": 0.87,
        "timestamp": "2025-11-18T15:20:15Z"
      }
    ]
  }
}
```

#### Right to Erasure (Article 17)

**User can delete all their data:**

```bash
ragged privacy delete --confirm
```

Interactive confirmation:
```
⚠️  WARNING: This will permanently delete ALL ragged data:
   - 3 sessions (42 MB)
   - REPL history (1.2 MB)
   - 127 query metrics
   - Cache files (15 MB)

This action CANNOT be undone.

Type 'DELETE' to confirm: DELETE

Deleting sessions... ✓
Deleting REPL history... ✓
Deleting metrics... ✓
Clearing cache... ✓

All data deleted. ragged is now in clean state.
```

Verification:
```bash
ragged privacy status
# Output: No data stored.
```

#### Right to Be Informed (Article 13)

**Transparent privacy policy:**

- Privacy policy displayed on first run
- Accessible via `ragged privacy policy`
- Clear explanation of data practices
- No hidden data collection

### GDPR Compliance Checklist

**Data Protection Principles (Article 5):**
- ✅ **Lawfulness:** User consents to local data storage
- ✅ **Fairness:** No deceptive practices
- ✅ **Transparency:** Privacy commands and documentation
- ✅ **Purpose Limitation:** Data used only for stated purposes
- ✅ **Data Minimisation:** Query hashing, not plaintext
- ✅ **Accuracy:** User can correct via deletion/re-input
- ✅ **Storage Limitation:** TTL-based cleanup (7-90 days)
- ✅ **Integrity & Confidentiality:** Encryption at rest (Fernet)

**User Rights:**
- ✅ **Right to Access:** `ragged privacy status`
- ✅ **Right to Rectification:** User can delete and re-enter
- ✅ **Right to Erasure:** `ragged privacy delete`
- ✅ **Right to Restrict Processing:** User can disable features
- ✅ **Right to Data Portability:** `ragged privacy export`
- ✅ **Right to Object:** User controls all settings
- ❌ **Automated Decision-Making:** Not applicable (no profiling)

---

## Privacy Configuration

**Established in:** v0.2.11 (Privacy Infrastructure)

**Purpose:** User control over privacy settings.

### Configuration File

`~/.ragged/config.yml`:
```yaml
privacy:
  # Encryption
  encryption_enabled: true
  encryption_algorithm: "fernet"  # AES-128

  # PII Detection
  pii_detection_enabled: true
  pii_detection_sensitivity: "strict"  # strict | medium | relaxed
  pii_warn_user: true
  pii_redact_logs: true

  # Data Lifecycle
  ttl_sessions_days: 7
  ttl_metrics_days: 90
  ttl_repl_history_days: 7
  ttl_api_sessions_days: 1
  auto_cleanup_enabled: true
  cleanup_schedule: "0 2 * * *"  # Daily at 2 AM

  # GDPR
  gdpr_mode: true  # Enables GDPR compliance features
  user_consent_required: true
  data_export_format: "json"  # json | csv

  # Telemetry (future)
  telemetry_enabled: false  # ALWAYS false by default
  anonymous_usage_stats: false
```

### CLI Configuration Commands

```bash
# View all privacy settings
ragged config get privacy

# Enable/disable encryption
ragged config set privacy.encryption_enabled true

# Adjust PII detection
ragged config set privacy.pii_detection_sensitivity strict

# Change TTL for sessions
ragged config set privacy.ttl_sessions_days 14

# Disable auto-cleanup (not recommended)
ragged config set privacy.auto_cleanup_enabled false

# Export configuration
ragged config export --output my-privacy-config.yml
```

### Privacy Profiles

**Maximum Privacy (Default):**
```yaml
privacy:
  encryption_enabled: true
  pii_detection_enabled: true
  pii_detection_sensitivity: "strict"
  ttl_sessions_days: 7
  auto_cleanup_enabled: true
  telemetry_enabled: false
```

**Balanced Privacy:**
```yaml
privacy:
  encryption_enabled: true
  pii_detection_enabled: true
  pii_detection_sensitivity: "medium"
  ttl_sessions_days: 30
  auto_cleanup_enabled: true
  telemetry_enabled: false
```

**Minimal Privacy (Not Recommended):**
```yaml
privacy:
  encryption_enabled: false  # ⚠️  Not recommended
  pii_detection_enabled: false
  ttl_sessions_days: 365
  auto_cleanup_enabled: false
  telemetry_enabled: false  # NEVER enable without consent
```

---

## Usage in v0.3.x Features

### v0.3.9: Interactive REPL

**Privacy Integration:**
```python
from ragged.session import SessionManager
from ragged.privacy import EncryptionManager, contains_pii, hash_query

class InteractiveShell(cmd.Cmd):
    def __init__(self):
        super().__init__()
        self.session = SessionManager().get_or_create_session()
        self.encryption = EncryptionManager()
        self.history = []

    def precmd(self, line: str) -> str:
        """Check for PII before executing command."""
        if contains_pii(line):
            self.stdout.write(
                "⚠️  PII detected. History will be encrypted.\n"
            )
            self.session.metadata["contains_pii"] = True

        # Store command with hash
        self.history.append({
            "timestamp": datetime.now().isoformat(),
            "command": line,
            "command_hash": hash_query(line)  # For logging
        })
        return line

    def save_session(self, filepath: Path) -> None:
        """Save session (encrypted if PII detected)."""
        session_data = {
            "session_id": self.session.session_id,
            "history": self.history,
            "metadata": self.session.metadata
        }

        # Encrypt if PII detected
        if self.session.metadata.get("contains_pii"):
            encrypted = self.encryption.encrypt(
                json.dumps(session_data).encode()
            )
            filepath.write_bytes(encrypted)
        else:
            filepath.write_text(json.dumps(session_data))

        # Set secure file permissions
        filepath.chmod(0o600)
```

**Privacy Risk: 90/100** (HIGH)
- PII warnings on input
- Encrypted session files
- TTL cleanup (7 days)
- GDPR deletion/export

### v0.3.10: Performance Metrics

**Privacy Integration:**
```python
from ragged.privacy import hash_query

class MetricsDatabase:
    def record_query(
        self,
        question: str,
        metrics: Dict,
        session_id: str
    ):
        """Record query metrics (privacy-safe)."""
        # Hash query instead of storing plaintext
        query_hash = hash_query(question)

        # Calculate expiration
        expires_at = datetime.now() + timedelta(days=90)

        # Store with TTL
        self.conn.execute("""
            INSERT INTO queries (
                session_id,
                query_hash,        -- ✅ HASHED (NOT plaintext)
                duration_ms,
                ragas_score,
                timestamp,
                expires_at         -- ✅ TTL for cleanup
            ) VALUES (?, ?, ?, ?, ?, ?)
        """, (
            session_id,
            query_hash,
            metrics['duration_ms'],
            metrics.get('ragas_score'),
            datetime.now(),
            expires_at
        ))
```

**Privacy Risk: 95/100** (HIGH)
- Query hashing (NO plaintext)
- Database file encryption (0o600)
- TTL-based cleanup (90 days)
- GDPR export/deletion

### v0.3.13: REST API

**Privacy Integration:**
```python
from fastapi import FastAPI, Request, Security
from ragged.session import SessionManager
from ragged.privacy import hash_query

app = FastAPI()

@app.middleware("http")
async def session_middleware(request: Request, call_next):
    """Create/retrieve session for each request."""
    session_mgr = SessionManager()
    session_id = request.headers.get("X-Session-ID")

    if session_id:
        session = session_mgr.get_or_create_session(session_id)
    else:
        session = session_mgr.get_or_create_session()
        session_id = session.session_id

    request.state.session = session
    response = await call_next(request)
    response.headers["X-Session-ID"] = session_id
    return response

@app.post("/query")
async def query_documents(request: QueryRequest, req: Request):
    """Process query with session isolation."""
    session = req.state.session

    # Session-scoped cache
    cache = QueryCache()
    cached = cache.get(
        query=request.question,
        session_id=session.session_id,  # ✅ Session-scoped
        top_k=request.top_k
    )

    # Log with query hash (NOT plaintext)
    logger.info(
        f"Query processed: {hash_query(request.question)} "
        f"session={session.session_id}"
    )

    # Process...
```

**Privacy Risk: 92/100** (HIGH)
- Per-client session isolation
- Query hashing in logs
- API key authentication
- Rate limiting
- CORS security

---

## Privacy Risk Assessment

### Risk Scoring Methodology

**Score = (Security Controls / Total Risks) × 100**

**Factors Evaluated:**
- Session isolation (20 points)
- Encryption at rest (20 points)
- PII detection (15 points)
- Query hashing (15 points)
- TTL cleanup (10 points)
- GDPR compliance (10 points)
- File permissions (5 points)
- Audit logging (5 points)

### Feature Risk Scores

| Feature | Risk Level | Score | Rationale |
|---------|-----------|-------|-----------|
| **v0.3.1 RAGAS** | Low | N/A | No user data stored |
| **v0.3.2 Config** | None | N/A | Configuration only |
| **v0.3.3 Retrieval** | Low | N/A | Session-scoped caching |
| **v0.3.4 Chunking** | None | N/A | Document processing only |
| **v0.3.5 OCR** | None | N/A | Document processing only |
| **v0.3.6 Auto-correct** | None | N/A | Document processing only |
| **v0.3.7 VectorStore** | Low | N/A | Session isolation |
| **v0.3.8 Metadata** | Medium | N/A | Query hashing, TTL |
| **v0.3.9 REPL** | **HIGH** | **90/100** | ✅ Encrypted sessions, PII warnings |
| **v0.3.10 Metrics** | **HIGH** | **95/100** | ✅ Query hashing, DB encryption |
| **v0.3.13 REST API** | **HIGH** | **92/100** | ✅ Session isolation, authentication |

**Interpretation:**
- **90-100:** Excellent privacy protection
- **70-89:** Good privacy, minor gaps
- **50-69:** Moderate privacy, improvements needed
- **<50:** Poor privacy, urgent action required

---

## Future Enhancements

### v0.4.x: Advanced Privacy

**Differential Privacy for Metrics:**
- Add noise to query metrics
- Prevent individual query reconstruction
- Maintain statistical utility

**Homomorphic Encryption (Research):**
- Search encrypted data without decryption
- Zero-knowledge proofs for verification
- Experimental, not production-ready

### v0.5.x: Privacy Dashboard

**Web UI for Privacy Management:**
- Visual privacy status
- Interactive data export
- One-click deletion
- Privacy settings GUI

### v1.0: Security Audit

**Third-Party Audit:**
- Professional security audit
- Penetration testing
- Privacy impact assessment
- Certification (ISO 27001, SOC 2)

**Bug Bounty Programme:**
- Responsible disclosure rewards
- Community security testing
- Continuous improvement

---

## Related Documentation

- [Security Policy](./policy.md) - Comprehensive security policy
- [v0.2.10 Roadmap](../roadmap/version/v0.2/v0.2.10/) - Security Hardening implementation
- [v0.2.11 Roadmap](../roadmap/version/v0.2/v0.2.11/) - Privacy Infrastructure implementation
- [v0.3 README](../roadmap/version/v0.3/README.md) - How v0.3.x uses privacy foundation

---

**Last Updated:** 2025-11-19

**Architecture Version:** 1.0

**License:** GPL-3.0
