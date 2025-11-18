# ragged v2.0 Planning - Multi-User & Regulatory Compliance

**Status**: Strategic Planning
**Total Estimated Hours**: 270-340 hours
**Target Timeline**: After v1.0 stable and user-validated
**Focus**: Enterprise collaboration with privacy-preserving compliance

---

## Vision Statement

ragged v2.0 extends the personal knowledge platform to **small-medium teams** (10-500 users) with collaborative features and regulatory compliance, while maintaining ragged's core privacy-first values.

**Positioning**: Self-hosted enterprise knowledge management with state-of-the-art AI, modern UX, and compliance frameworks (GDPR, HIPAA, SOC 2).

---

## Strategic Context

### v1.0 → v2.0 Transition

**What v1.0 delivers**:
- ✅ State-of-the-art personal knowledge management
- ✅ Modern web UI (block editor, graph viz, command palette)
- ✅ Privacy-first architecture
- ✅ AI-powered organization and retrieval

**What v2.0 adds**:
- Multi-user authentication and authorization
- Real-time collaboration
- Enterprise-grade compliance (audit logging, encryption, data governance)
- Team workspaces and permissions
- SSO and directory integrations

---

## Feature Priorities

### Core Features (270-340 hours)

**1. Multi-User Foundation** (40-50h)
- User registration, profiles, directory
- Email/password + SSO/SAML + OAuth
- JWT session management
- API keys for programmatic access

**2. Collaboration** (60-80h)
- Real-time editing (Yjs CRDT)
- In-line commenting and threads
- @mentions and notifications
- Sharing (collections, documents, links)
- Version control with diff view

**3. Advanced RBAC** (40-50h)
- Granular permissions (collection, document, feature-level)
- Teams/groups with nested hierarchies
- Permission templates and delegation
- Approval workflows

**4. Compliance & Audit** (50-60h)
- Immutable audit trail (all user actions)
- Data governance (classification, retention, legal hold)
- Privacy controls (GDPR export/deletion, consent management)
- Per-user and per-document encryption

**5. Enterprise Integration** (40-50h)
- LDAP/Active Directory sync
- SAML 2.0 / OpenID Connect
- Slack, Microsoft Teams notifications
- GraphQL API + webhooks

**6. Admin Dashboard** (40-50h)
- User/team management
- System monitoring (usage, storage, query volume)
- Compliance reports
- Configuration (feature flags, resource limits)

---

## Compliance Frameworks

### Regulatory Support

**GDPR (European)**:
- Right to access (export all data)
- Right to deletion (complete removal)
- Data portability
- Consent management
- Breach notification (72 hours)

**HIPAA (US Healthcare)**:
- Encryption (at rest and in transit)
- Access controls
- Audit logging
- Breach notification

**SOC 2**:
- Security controls
- Availability guarantees
- Confidentiality
- Processing integrity

**Implementation**: Build once, certify for multiple frameworks (common requirements).

---

## Architecture Model

### Deployment Options

**1. Self-Hosted** (Primary)
- Docker Compose for small teams (<50 users)
- Kubernetes for large deployments
- On-premise (customer controls infrastructure and data)

**2. Managed Self-Hosted** (Optional)
- ragged deploys on customer's cloud (AWS/Azure/GCP)
- ragged manages updates/monitoring
- Customer owns data

**3. Cloud SaaS** (Future - v2.5+)
- Multi-tenant hosted version
- Instant setup, subscription pricing

**Recommendation**: Start with (1), offer (2) for revenue, evaluate (3) based on demand.

---

## Success Criteria

### Feature Completeness
- [ ] All 6 core feature areas implemented
- [ ] GDPR compliance validated
- [ ] Real-time collaboration tested with 50+ concurrent users
- [ ] SSO working with major providers (Google, Microsoft, Okta)

### Performance
- [ ] Support 100+ concurrent users
- [ ] Real-time latency < 100ms
- [ ] Audit log queries < 2s

### Compliance
- [ ] GDPR audit passed
- [ ] HIPAA compliance documented
- [ ] SOC 2 audit preparation complete

---

## Related Documentation

- [v1.0 Planning](../v1.0/README.md) - Personal knowledge platform
- [v3.0 Planning](../v3.0/README.md) - Future ecosystem
- [Strategic Roadmap](../../vision/strategic-roadmap.md) - v1-v3 overview

---

**Status**: Strategic Planning
**Last Updated**: 2025-11-18
