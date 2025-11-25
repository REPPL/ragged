# Operations Documentation

**Purpose:** Operational guides for deploying, monitoring, and maintaining ragged in production environments.

**Status:** Active (v0.6.2+)

---

## Overview

This directory contains documentation for production operations, including monitoring, deployment, security hardening, and troubleshooting.

## Documentation Contents

### Monitoring & Metrics

- **[monitoring.md](./monitoring.md)** - Session monitoring and metrics (v0.6.2)
  - Prometheus metrics endpoint configuration
  - Grafana dashboard setup
  - Alerting rules for anomaly detection
  - Production deployment best practices
  - Troubleshooting guide

## Planned Documentation

### Deployment

- **deployment.md** - Production deployment guides
  - Docker deployment
  - Kubernetes configuration
  - Environment configuration
  - Scaling considerations

### Security

- **security-hardening.md** - Production security guidelines
  - Network security
  - Authentication and authorisation
  - Rate limiting
  - Audit logging

### Backup & Recovery

- **backup-recovery.md** - Data backup and disaster recovery
  - Database backup strategies
  - Session state recovery
  - Configuration backup

### Troubleshooting

- **troubleshooting.md** - Common issues and solutions
  - Performance issues
  - Connection problems
  - Resource exhaustion
  - Plugin failures

## Related Documentation

- [Session Monitoring](./monitoring.md) - Prometheus/Grafana setup (v0.6.2)
- [v0.6.2 Roadmap](../development/roadmap/version/v0.6/v0.6.2.md) - Security enhancements
- [Security Audit](../audit/security/baseline/v0.6.0-security-audit.md) - Security assessment

---

**Last Updated:** v0.6.2 (2025-11-25)

**Maintained By:** ragged operations team
