# Security Guidelines

**Purpose**: Security best practices, vulnerability reporting, and security checklist for ragged development.

**Audience**: Developers, contributors, security auditors

---

## Table of Contents

1. [Security Principles](#security-principles)
2. [Plugin Security](#plugin-security)
3. [Data Security](#data-security)
4. [Input Validation](#input-validation)
5. [Dependency Security](#dependency-security)
6. [Vulnerability Reporting](#vulnerability-reporting)
7. [Security Checklist](#security-checklist)
8. [Security Tools](#security-tools)

---

## Security Principles

### Privacy-First Architecture

Ragged is designed with **privacy as the foundation**:

- **Local-only by default**: No cloud dependencies, no telemetry
- **User data never leaves device**: Unless explicitly configured by user
- **Transparent data handling**: All data collection must be explicit and documented
- **User control**: Users must be able to view, edit, delete, and export their data

### Defence in Depth

Security is implemented in layers:

1. **Input validation** at system boundaries
2. **Sandboxing** for untrusted code (plugins)
3. **Least privilege** for file system access
4. **Encryption** for sensitive data at rest
5. **Audit logging** for security-relevant events

---

## Plugin Security

### Sandbox Execution

All plugins must run in isolated sandboxes:

```python
from src.plugins.sandbox import PluginSandbox

sandbox = PluginSandbox(
    allowed_imports=['numpy', 'pandas'],
    allowed_paths=[Path('/data/allowed')],
    disallowed_paths=[Path('/etc'), Path.home()]
)

result = sandbox.execute_plugin(plugin_code, timeout=30)
```

### Permission System

Plugins require explicit permissions:

- **File Read/Write**: Limited to specific directories
- **Network Access**: Generally prohibited
- **System Commands**: Prohibited
- **Import Restrictions**: Only approved modules

### Plugin Validation

All plugins must pass validation before loading:

```bash
# Validate plugin manifest
ragged plugin validate my-plugin

# Check plugin permissions
ragged plugin permissions my-plugin

# Review plugin audit log
ragged plugin audit my-plugin
```

---

## Data Security

### Encryption

Sensitive data must be encrypted at rest:

- **Query history**: Encrypted with Fernet (symmetric encryption)
- **Session data**: Encrypted with user-derived key
- **API keys** (if used): Stored in encrypted configuration

```python
from cryptography.fernet import Fernet
from src.security.encryption import encrypt_data, decrypt_data

# Encrypt sensitive data
encrypted = encrypt_data(data, key)

# Decrypt when needed
decrypted = decrypt_data(encrypted, key)
```

### File System Access

- **Never trust file paths from user input** - validate and sanitize
- **Prevent path traversal**: Use `Path.resolve()` and check ancestors
- **Restrict access**: Limit to designated data directories

```python
from pathlib import Path

def validate_path(user_path: str, allowed_base: Path) -> Path:
    """Validate user-provided path is within allowed directory."""
    path = Path(user_path).resolve()

    # Check if path is within allowed base
    try:
        path.relative_to(allowed_base.resolve())
    except ValueError:
        raise SecurityError(f"Path {path} is outside allowed directory")

    return path
```

### No Pickle Usage

**Never use `pickle` for data serialisation** - it allows arbitrary code execution.

**Use instead**:
- JSON for structured data
- MessagePack for binary efficiency
- Pydantic for validated serialisation

---

## Input Validation

### User Input

All user input must be validated before processing:

```python
from pydantic import BaseModel, Field, validator

class QueryRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=10000)
    k: int = Field(10, ge=1, le=100)

    @validator('query')
    def validate_query(cls, v):
        # Remove potential injection attempts
        if any(char in v for char in ['<', '>', ';', '&']):
            raise ValueError("Invalid characters in query")
        return v.strip()
```

### SQL Injection Prevention

Even though we primarily use ChromaDB/LEANN, metadata filters can be vulnerable:

```python
# BAD - String interpolation
filter = f"metadata.author = '{author}'"  # VULNERABLE

# GOOD - Parameterised filters
filter = {"author": author}  # SAFE
```

### Command Injection Prevention

**Never pass user input directly to shell commands**:

```python
# BAD
os.system(f"grep {user_input} file.txt")  # VULNERABLE

# GOOD
subprocess.run(['grep', user_input, 'file.txt'],
               check=True, capture_output=True)
```

---

## Dependency Security

### Vulnerability Scanning

Regularly scan dependencies for known vulnerabilities:

```bash
# Check for vulnerabilities
safety check

# Audit with pip-audit
pip-audit

# Security linting
bandit -r src/
```

### Dependency Updates

- **Keep dependencies up to date** - especially security patches
- **Pin exact versions** in production
- **Review changelogs** before upgrading major versions
- **Test after updates** to catch breaking changes

### License Compliance

Ensure all dependencies are GPL-3.0 compatible:

- **Permissive licenses OK**: MIT, Apache 2.0, BSD
- **Copyleft compatible**: GPL-3.0, LGPL
- **Incompatible**: Proprietary, some restrictive licenses

---

## Vulnerability Reporting

### Reporting Process

If you discover a security vulnerability:

1. **Do NOT open a public issue**
2. **Email security contact** (to be established)
3. **Provide details**:
   - Vulnerability description
   - Steps to reproduce
   - Potential impact
   - Suggested fix (if available)

### Responsible Disclosure

- **Give us reasonable time** to fix before public disclosure (90 days)
- **Coordinate disclosure** timing if you plan to publish
- **Credit**: We will acknowledge your contribution (if desired)

### Security Updates

Security fixes are released as:

- **Patch releases** for supported versions
- **Security advisories** published with fix details
- **CVE assignment** for significant vulnerabilities

---

## Security Checklist

### Development

Before committing code:

- [ ] All user input validated
- [ ] No hardcoded secrets
- [ ] No `pickle` usage
- [ ] Path traversal prevented
- [ ] SQL/command injection prevented
- [ ] Sensitive data encrypted
- [ ] Security-relevant actions logged
- [ ] Bandit scan passes (no high/critical)
- [ ] Dependency scan passes (no high/critical vulnerabilities)

### Pre-Release

Before releasing a version:

- [ ] Full security audit completed
- [ ] All dependencies up to date
- [ ] License compliance verified
- [ ] Security documentation updated
- [ ] Threat model reviewed
- [ ] Penetration testing (for major releases)

### Plugin Review

Before approving a plugin:

- [ ] Manifest validated
- [ ] Permissions reviewed and minimal
- [ ] No network access (unless justified)
- [ ] File access restricted
- [ ] Code review completed
- [ ] Security testing performed

---

## Security Tools

### Static Analysis

```bash
# Security linting with bandit
bandit -r src/ --severity-level high

# Type checking (catches some security issues)
mypy src/ --strict

# Code quality (includes security rules)
ruff check src/ --select S
```

### Dependency Scanning

```bash
# Vulnerability scanning
safety check
pip-audit

# License checking
pip-licenses --summary
```

### Runtime Protection

```python
# Plugin sandbox (process isolation)
from src.plugins.sandbox import PluginSandbox

# Rate limiting
from src.plugins.rate_limiter import RateLimiter

# Audit logging
from src.plugins.audit import AuditLogger
```

---

## Related Documentation

- [Plugin Security Architecture](../development/roadmap/version/v0.4/v0.4.0.md) - Plugin security design
- [Privacy Framework](../development/roadmap/version/v0.4/v0.4.5/privacy-framework.md) - Privacy principles
- [Security Audit Requirements](../development/roadmap/version/v0.4/v0.4.5/security-audit.md) - Audit process

---
