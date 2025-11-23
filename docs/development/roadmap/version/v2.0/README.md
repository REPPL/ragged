# Ragged v2.0 Roadmap - Enterprise & Applications

**Status:** Planned

**Duration:** 150-200 hours (AI implementation)

**Focus:** Enterprise compliance, native applications, and embeddable widgets

**Breaking Changes:** None (mature API with backwards compatibility)

---

## Overview

Version 2.0 completes ragged's evolution into a comprehensive RAG platform suitable for regulated industries and diverse deployment models. This addresses enterprise-grade requirements and application form factors identified in the ecosystem analysis.

**Dependencies:** Requires v1.5 (collaboration features), v0.7 (enterprise foundation)

**Strategic Context:** Achieves enterprise parity with Onyx/Danswer whilst adding AnythingLLM's desktop apps and embeddable widget capabilities. Maintains privacy-first principles with HIPAA/SOC2 compliance.

**Target Users:** Healthcare organisations, legal firms, financial services, enterprises requiring compliance and desktop applications.

---

## ENTERPRISE-001: HIPAA Compliance (30-40 hours)

**Problem:** Cannot be used in healthcare due to lack of HIPAA compliance.

**Inspiration:** Onyx/Danswer's enterprise features, LocalGPT's air-gapped deployments.

**Implementation:**
1. Conduct HIPAA requirements analysis [5-6 hours]
2. Implement encryption at rest (AES-256) [8-10 hours]
3. Add comprehensive audit logging [6-8 hours]
4. Create access control reports [4-5 hours]
5. Implement automatic log retention policies [3-4 hours]
6. Add BAA (Business Associate Agreement) documentation [4-5 hours]

**HIPAA requirements:**
- **Encryption:** Data at rest (AES-256), data in transit (TLS 1.3)
- **Access control:** Role-based, audit trail for all access
- **Audit logs:** Who accessed what, when, comprehensive logging
- **Data integrity:** Checksums, tamper detection
- **Backup & DR:** Automated backups, tested recovery procedures
- **Documentation:** Policies, procedures, BAA template

**Compliance features:**
```python
# Comprehensive audit logging
@audit_log(action="query", phi_access=True)
async def query_documents(user_id: str, query: str):
    # Log: user, timestamp, query, documents accessed, IP address
    log_phi_access(user_id, "query", query)

    # Execute query with permission filtering
    results = await secure_query(user_id, query)

    # Log successful access
    log_successful_query(user_id, results)

    return results
```

**Encryption at rest:**
- ChromaDB data encrypted with AES-256
- Document storage encrypted
- Encryption keys managed via KMS (AWS KMS, HashiCorp Vault)
- Per-workspace encryption keys

**Files:**
- `src/compliance/hipaa.py` (HIPAA features, ~500 lines)
- `src/encryption/at_rest.py` (encryption at rest, ~400 lines)
- `src/audit/comprehensive_logging.py` (audit logs, ~600 lines)
- `docs/compliance/hipaa-compliance.md` (documentation, ~2000 lines)
- `docs/compliance/baa-template.md` (BAA template, ~1500 lines)
- `tests/compliance/test_hipaa.py` (~500 lines)

**Manual Testing:**
- Enable HIPAA mode
- Query documents, verify all access logged
- Verify encryption at rest (check database files)
- Generate audit report for compliance review
- Test backup and restore with encrypted data
- Review BAA documentation

**Success:** HIPAA compliance verified; audit logs comprehensive; encryption bulletproof; documentation complete

**Known Risk:** HIPAA compliance requires ongoing maintenance; legal review recommended

---

## ENTERPRISE-002: SOC2 Type II Compliance (25-35 hours)

**Problem:** Enterprise customers require SOC2 attestation for vendor approval.

**Implementation:**
1. Conduct SOC2 requirements analysis [4-5 hours]
2. Implement security controls (access logging, MFA, etc.) [8-10 hours]
3. Create availability monitoring and SLA tracking [5-6 hours]
4. Implement change management procedures [4-5 hours]
5. Add incident response framework [4-5 hours]
6. Create compliance documentation and evidence collection [1-2 hours]

**SOC2 Trust Service Criteria:**
- **Security:** Access controls, encryption, vulnerability management
- **Availability:** Uptime monitoring, incident response, disaster recovery
- **Processing Integrity:** Data validation, error handling, quality checks
- **Confidentiality:** Access restrictions, data classification, DLP
- **Privacy:** Consent management, data minimisation, privacy controls

**Security controls:**
- Multi-factor authentication (MFA)
- IP allowlisting
- Session timeout and re-authentication
- Security headers (CSP, HSTS, X-Frame-Options)
- Vulnerability scanning (automated)
- Penetration testing procedures

**Files:**
- `src/compliance/soc2.py` (SOC2 features, ~600 lines)
- `src/security/mfa.py` (multi-factor auth, ~400 lines)
- `src/monitoring/availability.py` (uptime tracking, ~300 lines)
- `docs/compliance/soc2-compliance.md` (documentation, ~2500 lines)
- `docs/compliance/incident-response-plan.md` (~1000 lines)
- `tests/compliance/test_soc2.py` (~400 lines)

**Manual Testing:**
- Enable SOC2 controls
- Test MFA enforcement
- Verify security headers present
- Simulate incident, test response procedures
- Generate compliance report
- Review documentation for completeness

**Success:** SOC2 controls implemented; documentation audit-ready; security hardened

**Known Risk:** SOC2 attestation requires external auditor; this provides controls, not certification

---

## ENTERPRISE-003: Air-Gapped Deployment (20-25 hours)

**Problem:** Highly regulated industries (defence, government) require completely offline deployments.

**Inspiration:** LocalGPT's air-gapped capabilities.

**Implementation:**
1. Create offline installer package [6-8 hours]
2. Implement local model caching (no internet required) [5-6 hours]
3. Add offline licence management [4-5 hours]
4. Create air-gap deployment guide [3-4 hours]
5. Add offline update mechanism (manual package import) [2-3 hours]

**Air-gap features:**
- **No internet dependency:** All models cached locally
- **Offline installer:** Single package with all dependencies
- **Manual updates:** Import update packages via USB
- **Local licence:** Activation via offline key
- **Compliance:** Full audit trail without external connections

**Deployment package:**
```bash
ragged-airgap-v2.0.0/
├── installer.sh                 # Offline installer
├── models/
│   ├── all-MiniLM-L6-v2/       # Text embedding model
│   └── vidore-colpali-v1.3/    # Vision model
├── dependencies/
│   └── python-packages.tar.gz  # All pip dependencies
├── docker-images/
│   ├── ragged-api.tar          # Pre-built Docker images
│   └── chromadb.tar
├── docs/                        # Offline documentation
└── licence.key                  # Offline activation
```

**Files:**
- `deployment/air-gap/installer.sh` (offline installer, ~400 lines)
- `src/licence/offline.py` (offline licence management, ~300 lines)
- `scripts/build-airgap-package.sh` (build script, ~200 lines)
- `docs/deployment/air-gap-deployment.md` (~1500 lines)
- `tests/deployment/test_airgap.py` (~300 lines)

**Manual Testing:**
- Build air-gap package
- Deploy on completely offline machine
- Verify all models load from local cache
- Test licence activation offline
- Import update package, verify successful upgrade
- Confirm no internet requests made

**Success:** Ragged deployable on air-gapped networks; all features functional offline

---

## APP-001: Desktop Applications (Electron) (40-50 hours)

**Problem:** Web app requires browser; users want native desktop experience.

**Inspiration:** AnythingLLM's native Mac/Windows/Linux apps.

**Implementation:**
1. Set up Electron project structure [5-6 hours]
2. Integrate SvelteKit web UI with Electron [10-12 hours]
3. Implement native features (tray icon, notifications, auto-update) [8-10 hours]
4. Add local storage and offline mode [6-8 hours]
5. Create installers for Mac/Windows/Linux [6-8 hours]
6. Implement deep linking and file associations [5-6 hours]

**Desktop app features:**
- **Native experience:** System tray, native notifications, OS integration
- **Offline-first:** Full offline functionality
- **Auto-update:** Automatic app updates (optional, user-controlled)
- **Deep linking:** `ragged://query?q=...` URL scheme
- **File associations:** Double-click PDF → open in ragged
- **Multi-platform:** macOS, Windows, Linux (AppImage/deb/rpm)

**Platform-specific features:**
- **macOS:** Menu bar integration, Touch Bar support, Shortcuts app integration
- **Windows:** Taskbar integration, Windows Hello auth, Jump Lists
- **Linux:** System tray (AppIndicator), desktop file integration

**Application architecture:**
```javascript
// Main process (Electron)
- System tray icon and menu
- Auto-updater
- Deep linking handler
- File association handler
- Native notifications

// Renderer process (SvelteKit)
- Full web UI
- IPC communication with main process
- Local storage (IndexedDB)
```

**Files:**
- `desktop-app/` (new directory, Electron project)
  - `src/main/` (main process, ~1500 lines)
  - `src/renderer/` (symlink to web-ui)
  - `build/` (installer scripts, ~800 lines)
  - `package.json`, `electron-builder.yml`
- `~3500 lines total`

**Manual Testing:**
- Build app for all platforms
- Test system tray functionality
- Verify offline mode works
- Test auto-update mechanism
- Deep link from browser → app
- Double-click PDF → opens in ragged
- Test native notifications

**Success:** Desktop apps available for macOS/Windows/Linux; native features functional; auto-update working

---

## APP-002: Browser Extension (20-25 hours)

**Problem:** Users want to save web pages and articles directly to ragged.

**Inspiration:** Notion Web Clipper, Pocket, Instapaper.

**Implementation:**
1. Create browser extension manifest (Chrome/Firefox) [3-4 hours]
2. Implement page capture (article extraction) [6-8 hours]
3. Add selection capture (highlight to save) [4-5 hours]
4. Create extension UI (popup, settings) [5-6 hours]
5. Implement sync with ragged instance [2-3 hours]

**Extension features:**
- **Full page capture:** Save entire web page as document
- **Article extraction:** Extract main content (remove ads, nav)
- **Selection capture:** Highlight text → save as note
- **Screenshot capture:** Save visible area as image
- **Tags and metadata:** Add tags, notes during capture
- **Sync:** Automatic upload to ragged instance

**Browser extension UI:**
```javascript
// Popup menu (click extension icon)
- Save page (full or article mode)
- Save selection
- Take screenshot
- Recent captures
- Settings (ragged instance URL, API key)

// Context menu (right-click)
- "Save to ragged" (for links, images, selections)

// Toolbar badge
- Shows sync status (✓ synced, ↻ syncing, ✗ error)
```

**Files:**
- `browser-extension/` (new directory)
  - `manifest.json` (extension config)
  - `src/popup/` (popup UI, ~600 lines)
  - `src/content/` (page capture, ~800 lines)
  - `src/background/` (sync service, ~500 lines)
- `~2000 lines total`

**Manual Testing:**
- Install extension in Chrome and Firefox
- Save full web page
- Extract article from news site
- Highlight text, save selection
- Take screenshot
- Verify uploads to ragged instance
- Test offline queuing (save offline, sync when online)

**Success:** Browser extension available for Chrome/Firefox; captures working; sync reliable

---

## APP-003: Embeddable Widget (25-30 hours)

**Problem:** Users want to embed ragged chat in their websites/apps.

**Inspiration:** AnythingLLM's embeddable chat widget.

**Implementation:**
1. Create widget SDK (JavaScript) [8-10 hours]
2. Design customisable widget UI [6-8 hours]
3. Implement iframe-based embedding [4-5 hours]
4. Add authentication and access control [4-5 hours]
5. Create widget configuration and theming [3-4 hours]

**Widget features:**
- **Embeddable:** Single `<script>` tag to add to website
- **Customisable:** Colours, logo, welcome message, position
- **Secure:** API key authentication, CORS configuration
- **Responsive:** Works on mobile and desktop
- **Privacy:** Can disable analytics, logging

**Widget integration:**
```html
<!-- Add to any website -->
<script src="https://ragged.example.com/widget.js"></script>
<script>
  RaggedWidget.init({
    apiKey: 'YOUR_API_KEY',
    workspaceId: 'workspace-uuid',
    theme: 'dark',
    position: 'bottom-right',
    welcomeMessage: 'Ask me anything about our docs!',
    collections: ['documentation', 'faqs']
  });
</script>
```

**Widget UI:**
- **Button:** Floating chat button (bottom-right by default)
- **Chat window:** Expandable chat interface
- **Query input:** Text input with suggestions
- **Results:** Chat-like response display
- **Branding:** Customisable logo, colours, "Powered by ragged"

**Files:**
- `widget/` (new directory)
  - `src/widget.ts` (widget SDK, ~800 lines)
  - `src/ui/` (widget UI components, ~1000 lines)
  - `src/embed.ts` (iframe communication, ~400 lines)
- `~2500 lines total`

**Manual Testing:**
- Embed widget on test website
- Customise theme and position
- Test queries via widget
- Verify authentication works
- Test on mobile and desktop browsers
- Verify CORS security

**Success:** Widget embeddable in any website; secure; customisable; performs well

---

## ENTERPRISE-004: Advanced Observability (15-20 hours)

**Problem:** Enterprise operations require comprehensive monitoring beyond basic metrics.

**Implementation:**
1. Expand Prometheus metrics (v0.7 foundation) [4-5 hours]
2. Add distributed tracing (Jaeger/Zipkin) [5-6 hours]
3. Create pre-built Grafana dashboards [4-5 hours]
4. Implement alerting rules [2-3 hours]

**Observability stack:**
- **Metrics:** Prometheus (request rate, latency, errors, GPU usage)
- **Tracing:** OpenTelemetry → Jaeger (distributed request tracing)
- **Dashboards:** Grafana (pre-built dashboards for operators)
- **Alerting:** Prometheus Alertmanager (threshold alerts, PagerDuty integration)

**Pre-built dashboards:**
- **System Overview:** Request rate, latency, error rate, resource usage
- **GPU Performance:** Utilisation, memory, batch sizes, queue depth
- **Query Analytics:** Popular queries, slow queries, cache hit rate
- **User Activity:** Active users, queries per user, collaboration metrics

**Files:**
- `deployment/observability/grafana-dashboards/` (~1000 lines JSON)
- `deployment/observability/alerting-rules.yml` (~300 lines)
- `src/monitoring/tracing.py` (distributed tracing, ~400 lines)
- `docs/operations/observability.md` (~1500 lines)

**Manual Testing:**
- Deploy observability stack (Prometheus, Grafana, Jaeger)
- Generate load, view metrics in Grafana
- Trigger alert, verify PagerDuty notification
- Trace distributed query through system
- Review dashboards for completeness

**Success:** Comprehensive observability stack; operators can troubleshoot issues quickly

---

## Success Criteria

**Automated Tests:**
- [ ] HIPAA encryption at rest functional
- [ ] SOC2 security controls enforced
- [ ] Air-gap package installs without internet
- [ ] Desktop app builds for all platforms
- [ ] Browser extension syncs correctly
- [ ] Embeddable widget authenticates securely
- [ ] Distributed tracing captures all requests
- [ ] All existing tests pass

**Manual Testing:**
- [ ] Deploy HIPAA-compliant instance, verify audit logs
- [ ] Enable SOC2 controls, test MFA and security headers
- [ ] Install air-gap package on offline machine
- [ ] Build and install desktop app on macOS/Windows/Linux
- [ ] Install browser extension, save web page to ragged
- [ ] Embed widget on website, test queries
- [ ] Deploy observability stack, review dashboards

**Quality Gates:**
- [ ] HIPAA audit logs capture 100% of PHI access
- [ ] SOC2 security controls verified by external auditor (recommended)
- [ ] Air-gap deployment functional with zero internet requests
- [ ] Desktop app installers <200MB (macOS/Windows/Linux)
- [ ] Browser extension works in Chrome, Firefox, Edge, Safari
- [ ] Widget loads in <2 seconds, works on mobile
- [ ] Observability dashboards comprehensive and actionable
- [ ] Zero compliance violations in testing

---

## Known Risks

- **Compliance complexity:** HIPAA/SOC2 require ongoing maintenance and expertise; consider hiring compliance consultant
- **Legal liability:** Incorrect HIPAA implementation could result in fines; legal review strongly recommended
- **Desktop app maintenance:** Supporting multiple platforms (macOS/Windows/Linux) is significant ongoing effort
- **Browser extension fragmentation:** Different browsers have different extension APIs; testing burden high
- **Widget security:** Embedding in untrusted websites requires careful security design
- **Observability overhead:** Comprehensive monitoring may impact performance; optimise instrumentation
- **Enterprise sales:** Enterprise features may require enterprise support and sales process

**Critical Decision:** v2.0 represents enterprise pivot. Validate market demand before full implementation. Consider offering "Enterprise Edition" as separate product to fund development.

---

## Next Steps

After v2.0 completion, ragged is a comprehensive, enterprise-ready RAG platform suitable for:
- Healthcare organisations (HIPAA)
- Financial services (SOC2, air-gap)
- Government and defence (air-gap, compliance)
- Enterprises (desktop apps, widget, observability)
- Personal users (desktop app for convenience)

**Future considerations (v3.0+):**
- Mobile apps (iOS, Android)
- Advanced analytics and BI integrations
- Marketplace for plugins and extensions
- Multi-region deployment and CDN
- GraphQL API alongside REST
- Advanced compliance (GDPR automation, data residency controls)

---

## Related Documentation

- [Previous Version](../v1.5/README.md) - Collaboration and multi-user
- [Version Overview](../README.md) - Complete version comparison
- [Projects to Learn From](../../../../research/projects-to-learn-from.md) - Enterprise features inspiration

---

**Status:** Planned (enterprise pivot - validate demand)

**Note:** v2.0 represents significant enterprise investment. Recommend validating market demand and considering separate "Enterprise Edition" packaging to fund development and provide enterprise support.

---
