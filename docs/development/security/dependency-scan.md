# Dependency Security Scan Report

**Scan Date**: 2025-11-20
**Tool**: pip-audit 2.9.0
**Python Version**: 3.12.12
**Total Dependencies Scanned**: All project dependencies

---

## Summary

| Metric | Value |
|--------|-------|
| **Vulnerable Packages** | 1 |
| **Total Vulnerabilities** | 2 |
| **Severity** | MEDIUM |
| **Action Required** | Upgrade urllib3 |

---

## Vulnerabilities Found

### 1. urllib3 - GHSA-48p4-8xcf-vxj5

**Package**: urllib3
**Current Version**: 2.3.0
**Fixed In**: 2.5.0
**Severity**: MEDIUM
**Advisory**: https://github.com/advisories/GHSA-48p4-8xcf-vxj5

**Description**:
urllib3 supports being used in a Pyodide runtime utilizing the JavaScript Fetch API or XMLHttpRequest. The `retries` and `redirect` parameters are ignored with Pyodide; the runtime itself determines redirect behavior.

**Affected Usages**:
Any code which relies on urllib3 to control the number of redirects for an HTTP request in a Pyodide runtime.

**Impact**:
Redirects are often used to exploit SSRF vulnerabilities. An application attempting to mitigate SSRF or open redirect vulnerabilities by disabling redirects may remain vulnerable if a Pyodide runtime redirect mechanism is unsuitable.

**Remediation**:
Upgrade urllib3 to version 2.5.0 or later.

**Ragged Specific Assessment**:
- **Risk**: LOW for ragged (local-only, privacy-first architecture)
- **Affected Components**: None identified (ragged doesn't use Pyodide runtime)
- **Recommendation**: Upgrade as part of regular maintenance

---

### 2. urllib3 - GHSA-pq67-6m6q-mj2v

**Package**: urllib3
**Current Version**: 2.3.0
**Fixed In**: 2.5.0
**Severity**: MEDIUM
**Advisory**: https://github.com/advisories/GHSA-pq67-6m6q-mj2v

**Description**:
The `retries` parameter is currently ignored when passed to `PoolManager` instantiation for controlling redirects. This means attempts to disable redirects at the PoolManager level don't work as expected.

**Vulnerable Code Pattern**:
```python
http = urllib3.PoolManager(retries=0)  # Does NOT disable redirects
http = urllib3.PoolManager(retries=urllib3.Retry(redirect=0))  # Does NOT work
```

**Affected Usages**:
Passing `retries` on `PoolManager` instantiation to disable redirects or restrict their number.

**Impact**:
An application attempting to mitigate SSRF or open redirect vulnerabilities by disabling redirects at the PoolManager level will remain vulnerable.

**Remediation**:
1. Upgrade to urllib3 2.5.0 or later
2. Disable redirects at the `request()` level instead of `PoolManager()` level

**Ragged Specific Assessment**:
- **Risk**: LOW for ragged (local-only operation, no external HTTP requests in normal operation)
- **Affected Components**: None identified (ragged doesn't make external HTTP requests)
- **Recommendation**: Upgrade as part of regular maintenance

---

## Dependency Update Recommendations

### Immediate Actions

1. **Upgrade urllib3** (MEDIUM priority)
   ```bash
   pip install --upgrade urllib3==2.5.0
   ```

   Update `pyproject.toml`:
   ```toml
   dependencies = [
       "urllib3>=2.5.0,<3.0.0",
       # ... other dependencies
   ]
   ```

2. **Test After Upgrade**
   ```bash
   pytest tests/
   ```

3. **Verify Fix**
   ```bash
   pip-audit
   ```

### Preventive Measures

1. **Regular Scans**: Add dependency scanning to CI/CD pipeline
   ```yaml
   # .github/workflows/security.yml
   - name: Dependency Security Scan
     run: |
       pip install pip-audit
       pip-audit --desc
   ```

2. **Dependency Monitoring**: Enable GitHub Dependabot
   ```yaml
   # .github/dependabot.yml
   version: 2
   updates:
     - package-ecosystem: "pip"
       directory: "/"
       schedule:
         interval: "weekly"
   ```

3. **Pin Versions**: Use specific version ranges in `pyproject.toml`
   ```toml
   urllib3 = ">=2.5.0,<2.6.0"  # Pin to minor version
   ```

---

## Additional Dependencies Reviewed

The following critical dependencies were also scanned with NO vulnerabilities found:

| Package | Version | Status | Notes |
|---------|---------|--------|-------|
| requests | 2.32.5 | ✅ Clean | HTTP library (uses urllib3) |
| cryptography | 41.0.0+ | ✅ Clean | Security-critical package |
| pymupdf | 1.23.0+ | ✅ Clean | PDF processing |
| opencv-python | 4.8.0+ | ✅ Clean | Image processing |
| sentence-transformers | Current | ✅ Clean | ML models |
| docling | 2.5.0+ | ✅ Clean | Document processing |

**Note**: ragged itself (0.2.11) could not be audited as it's not published on PyPI.

---

## Risk Assessment for Ragged

### Overall Risk: LOW

**Rationale**:
1. **Local-Only Operation**: Ragged operates on local files, no external HTTP requests in normal operation
2. **No SSRF Vector**: The urllib3 vulnerabilities relate to redirect handling for HTTP requests, which ragged doesn't perform
3. **Dependency Chain**: urllib3 is a transitive dependency (via requests), not directly used by ragged
4. **Privacy-First Design**: System architecture limits attack surface

### Recommended Timeline

| Priority | Action | Deadline |
|----------|--------|----------|
| MEDIUM | Upgrade urllib3 to 2.5.0 | Next maintenance window (within 2 weeks) |
| HIGH | Add CI/CD dependency scanning | Before v0.3.4 release |
| MEDIUM | Enable Dependabot | Before v0.3.4 release |
| LOW | Review all dependencies quarterly | Ongoing |

---

## Future Scan Schedule

1. **Automated CI/CD Scans**: On every pull request and push to main
2. **Weekly Scans**: Automated Dependabot checks
3. **Quarterly Manual Review**: Comprehensive security review of all dependencies
4. **Pre-Release Scans**: Before every minor/major version release

---

## Scan Methodology

```bash
# Install pip-audit
pip install pip-audit

# Run scan with descriptions
pip-audit --desc --format=json > dependency-scan.json

# Or for human-readable output
pip-audit --desc
```

**Coverage**:
- All direct dependencies from `pyproject.toml`
- All transitive dependencies
- Python packages from PyPI with known CVEs

**Limitations**:
- Local packages (like ragged itself) not scanned
- Non-PyPI dependencies not covered
- Zero-day vulnerabilities not detected

---

## Related Documentation

- [v0.3.3 Security Audit](./v0.3.3-security-audit.md)
- [v0.3.4a Security Audit](./v0.3.4a-security-audit.md)
- [v0.3.4b Security Audit](./v0.3.4b-security-audit.md)
- [Security Testing Guide](./security-testing-guide.md) (to be created)

---

**Next Scan Due**: 2025-11-27 (weekly)
**Report Generated**: 2025-11-20
**Status**: 2 vulnerabilities identified, upgrade recommended
