# Security Monitoring Guide

**Version:** v0.5.7 HIGH-6
**Purpose:** Automated dependency vulnerability monitoring

---

## Overview

ragged implements automated security monitoring to detect and alert on dependency vulnerabilities. This guide explains how the monitoring system works and how to respond to security alerts.

## Automated Monitoring

### GitHub Actions Workflow

The security monitoring workflow (`.github/workflows/security.yml`) runs:

1. **Weekly scans**: Every Monday at 9:00 UTC
2. **On dependency changes**: When `pyproject.toml` is modified
3. **Pull request checks**: Automated security review for all PRs
4. **Manual triggers**: Via GitHub Actions UI

### Tools Used

**pip-audit**: Checks Python dependencies against the PyPI Advisory Database
- Detects known CVEs in dependencies
- Suggests fix versions when available
- Generates JSON reports for tracking

**CodeQL**: GitHub's semantic code analysis engine
- Scans for security vulnerabilities in Python code
- Detects common security issues (SQL injection, XSS, etc.)
- Integrates with GitHub Security tab

## Local Security Checks

### Running pip-audit Locally

```bash
# Activate virtual environment
source .venv/bin/activate

# Install pip-audit (if not installed)
pip install pip-audit

# Run basic scan
pip-audit

# Run with detailed descriptions
pip-audit --desc

# Generate JSON report
pip-audit --format json > security-report.json

# Check specific package
pip-audit --package <package-name>
```

### Interpreting Results

**Example output:**

```
Found 1 known vulnerability in 1 package
Name Version ID               Fix Versions Description
---- ------- ---------------- ------------ -----------
py   1.11.0  PYSEC-2022-42969              ReDoS attack via Subversion repository
```

**Fields:**
- **Name**: Package name
- **Version**: Installed version
- **ID**: CVE or PYSEC identifier
- **Fix Versions**: Versions that fix the vulnerability
- **Description**: Vulnerability details

## Responding to Vulnerabilities

### Severity Assessment

1. **Critical/High**: Production dependencies with active exploits
   - **Action**: Immediate update required
   - **Timeline**: Within 24 hours

2. **Medium**: Production dependencies, no active exploits
   - **Action**: Update in next release
   - **Timeline**: Within 1 week

3. **Low**: Dev dependencies or unlikely scenarios
   - **Action**: Update when convenient
   - **Timeline**: Next minor version

### Update Process

```bash
# 1. Check current version
pip show <package-name>

# 2. Check available versions
pip index versions <package-name>

# 3. Update pyproject.toml
# Change: package>=1.0.0
# To:     package>=1.1.0  # Fixed version

# 4. Reinstall
pip install -e .

# 5. Verify fix
pip-audit --package <package-name>

# 6. Run tests
pytest

# 7. Commit
git add pyproject.toml
git commit -m "security: update <package> to fix CVE-XXXX"
```

### When Update Isn't Available

If no fix version exists:

1. **Assess risk**: Is the vulnerability exploitable in our use case?
2. **Check alternatives**: Can we use a different package?
3. **Implement workarounds**: Can we mitigate the risk?
4. **Document decision**: Add to `docs/decisions/adrs/`
5. **Monitor upstream**: Watch for security releases

## GitHub Security Advisories

### Subscribing to Alerts

1. Navigate to repository **Settings → Security → Dependabot**
2. Enable **Dependabot alerts**
3. Enable **Dependabot security updates** (optional)
4. Configure notification preferences:
   - **Watch → Custom → Security alerts**
   - Receive email notifications for new vulnerabilities

### Reviewing Alerts

Alerts appear in:
- **Security tab**: Full list with details
- **Email notifications**: Immediate alerts
- **Pull requests**: Dependabot auto-fix PRs (if enabled)

## Security Dashboard

### Viewing Reports

**GitHub Actions artifacts:**
```
Repository → Actions → Security workflow → Latest run → Artifacts → pip-audit-report
```

**Security tab:**
```
Repository → Security → Dependabot alerts
```

**Local reports:**
```bash
pip-audit --format json > reports/security-$(date +%Y-%m-%d).json
```

### Tracking Over Time

Keep historical reports to track:
- New vulnerabilities introduced
- Time-to-fix metrics
- Dependency health trends

## Current Vulnerabilities

### Known Issues (as of 2025-11-23)

| Package | Version | Vulnerability | Severity | Status |
|---------|---------|---------------|----------|--------|
| py      | 1.11.0  | PYSEC-2022-42969 (ReDoS) | Low | Dev dependency, low risk |

**Assessment**: `py` library is only used by `interrogate` (dev dependency). ReDoS requires crafted Subversion repository, unlikely in our context. Update planned for v0.6.0.

## Best Practices

### Dependency Management

1. **Pin minimum versions**: Use `package>=1.2.3` not `package>=1.0.0`
2. **Review updates**: Don't blindly accept all updates
3. **Test thoroughly**: Run full test suite after updates
4. **Document changes**: Note security fixes in commit messages

### Security Culture

1. **Regular reviews**: Check security tab weekly
2. **Prompt updates**: Don't let vulnerabilities accumulate
3. **Share knowledge**: Discuss security in team meetings
4. **Stay informed**: Follow security mailing lists

## Integration with Development Workflow

### Pre-Commit Hook

Add to `.pre-commit-config.yaml`:

```yaml
- repo: https://github.com/pypa/pip-audit
  rev: v2.6.1
  hooks:
    - id: pip-audit
      args: [--desc]
```

### CI/CD Pipeline

The security workflow runs automatically:
- **Blocks merges**: If critical vulnerabilities found (configurable)
- **Comments on PRs**: Shows vulnerability count
- **Uploads reports**: 90-day retention

## Troubleshooting

### pip-audit Fails

**Issue**: `pip-audit` exits with error

**Solutions:**
```bash
# Update pip-audit
pip install --upgrade pip-audit

# Clear cache
pip-audit --cache-dir /tmp/pip-audit-cache

# Ignore package (last resort)
pip-audit --ignore-vuln <VULN-ID>
```

### False Positives

If `pip-audit` reports a vulnerability that doesn't apply:

1. **Verify context**: Does our usage trigger the vulnerability?
2. **Check version**: Is the vulnerable code path used?
3. **Document exception**: Create ADR explaining why it's safe
4. **Suppress warning**: Add to `.pip-audit.toml` (if needed)

## Related Documentation

- Security Framework - v0.5.7 security features
- Dependency Policy - Dependency selection criteria

---

**Introduced:** v0.5.7 HIGH-6
