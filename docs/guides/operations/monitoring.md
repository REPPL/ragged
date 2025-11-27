# Session Monitoring with Prometheus & Grafana

**Version:** v0.6.2 SECURITY-004

**Purpose:** Guide for setting up session monitoring and anomaly detection

---

## Overview

Ragged provides Prometheus-compatible metrics for monitoring session behaviour and detecting potential DoS attacks via session exhaustion.

**Metrics Provided:**
- `ragged_session_created_total` - Total sessions created (labels: status=success|failed)
- `ragged_session_expired_total` - Total sessions expired
- `ragged_session_deleted_total` - Total sessions explicitly deleted
- `ragged_active_sessions` - Current number of active sessions (gauge)
- `ragged_session_creation_rate_per_minute` - Sessions created per minute (gauge)
- `ragged_session_duration_seconds` - Session duration histogram

**Anomaly Detection:**
- Automatic detection of unusual session creation rates (default: >100/min)
- Logged warnings for potential DoS attacks
- Configurable threshold and time window

---

## Quick Start

### 1. Enable Metrics Endpoint

The `/metrics` endpoint is automatically enabled in v0.6.2+.

**Test the endpoint:**
```bash
curl http://localhost:8000/metrics
```

**Expected output:**
```
# HELP ragged_session_created_total Total number of sessions created
# TYPE ragged_session_created_total counter
ragged_session_created_total{status="success"} 42.0
ragged_session_created_total{status="failed"} 0.0

# HELP ragged_active_sessions Number of currently active sessions
# TYPE ragged_active_sessions gauge
ragged_active_sessions 5.0

# HELP ragged_session_creation_rate_per_minute Session creation rate over the last minute
# TYPE ragged_session_creation_rate_per_minute gauge
ragged_session_creation_rate_per_minute 2.3
...
```

### 2. Set Up Prometheus

**prometheus.yml:**
```yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'ragged-api'
    static_configs:
      - targets: ['ragged-api:8000']  # Docker service name
    metrics_path: '/metrics'
```

**Start Prometheus:**
```bash
docker run -d \
  --name prometheus \
  -p 9090:9090 \
  -v $(pwd)/prometheus.yml:/etc/prometheus/prometheus.yml \
  --network ragged-network \
  prom/prometheus
```

**Verify Prometheus is scraping:**
```
http://localhost:9090/targets
```

### 3. Set Up Grafana Dashboard

**Start Grafana:**
```bash
docker run -d \
  --name grafana \
  -p 3000:3000 \
  --network ragged-network \
  grafana/grafana
```

**Import Dashboard:**
1. Open Grafana: `http://localhost:3000` (default: admin/admin)
2. Add Prometheus datasource:
   - Configuration → Data Sources → Add data source
   - Select "Prometheus"
   - URL: `http://prometheus:9090`
   - Save & Test
3. Import dashboard:
   - Dashboards → Import
   - Upload `/path/to/ragged/grafana/session-dashboard.json`
   - Select Prometheus datasource
   - Import

**Dashboard includes:**
- Active session count (gauge)
- Session creation rate (gauge with anomaly threshold)
- Creation rate over time (time series)
- Success vs failed session creation
- Session duration percentiles (p50, p95, p99)
- Active sessions trend

---

## Configuration

### Anomaly Detection Threshold

**Default:** 100 sessions/minute

**Customise in code:**
```python
from ragged.web.middleware.metrics import get_session_metrics

# Get metrics instance with custom threshold
metrics = get_session_metrics(
    anomaly_threshold=200,  # 200 sessions/min
    rate_window_seconds=60   # 1-minute window
)
```

**Behaviour:**
- Anomaly warnings logged when threshold exceeded
- Logs throttled to once per minute (avoid spam)
- Anomaly state tracked for alerting

### Disable Metrics (Testing Only)

**Disable metrics in SessionSecurityMiddleware:**
```python
app.add_middleware(
    SessionSecurityMiddleware,
    enable_metrics=False  # Disable metrics
)
```

---

## Alerting Rules

### Prometheus Alerting

**prometheus-alerts.yml:**
```yaml
groups:
  - name: ragged_session_alerts
    interval: 30s
    rules:
      # High session creation rate (DoS attack indicator)
      - alert: HighSessionCreationRate
        expr: ragged_session_creation_rate_per_minute > 100
        for: 2m
        labels:
          severity: warning
        annotations:
          summary: "High session creation rate detected"
          description: "Session creation rate is {{ $value }}/min (threshold: 100/min)"

      # Session creation failures
      - alert: SessionCreationFailures
        expr: rate(ragged_session_created_total{status="failed"}[5m]) > 1
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "Session creation failures detected"
          description: "{{ $value }} session creation failures per second"

      # Very high active sessions
      - alert: VeryHighActiveSessions
        expr: ragged_active_sessions > 1000
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Very high number of active sessions"
          description: "{{ $value }} active sessions (unusual load or attack)"

      # Session creation spike (rapid increase)
      - alert: SessionCreationSpike
        expr: |
          (rate(ragged_session_created_total{status="success"}[1m])
          / rate(ragged_session_created_total{status="success"}[5m])) > 5
        for: 2m
        labels:
          severity: warning
        annotations:
          summary: "Sudden spike in session creation"
          description: "Session creation rate increased 5x over 5min baseline"
```

**Load alerts into Prometheus:**
```yaml
# prometheus.yml
rule_files:
  - "prometheus-alerts.yml"

alerting:
  alertmanagers:
    - static_configs:
        - targets: ['alertmanager:9093']
```

### Grafana Alerts

**Configure in Grafana UI:**
1. Edit "Session Creation Rate" panel
2. Click "Alert" tab
3. Create alert rule:
   - **Condition:** `WHEN last() OF query(A) IS ABOVE 100`
   - **For:** 2m
   - **Annotations:** "High session creation rate: potential DoS attack"
4. Configure notification channels (email, Slack, PagerDuty)

---

## Monitoring Best Practices

### Baseline Metrics

**Establish normal baselines:**
1. Monitor for 1 week under normal load
2. Note typical patterns:
   - Peak active sessions
   - Average creation rate
   - Typical session duration
3. Set alert thresholds above normal peak (e.g., 2x peak)

**Example baselines:**
- Small deployment (< 100 users): 5-20 active sessions
- Medium deployment (100-1000 users): 20-100 active sessions
- Large deployment (> 1000 users): 100-1000 active sessions

### Regular Review

**Weekly:**
- Review session creation trends
- Check for failed session creation
- Verify anomaly detection thresholds

**Monthly:**
- Adjust alert thresholds based on growth
- Review session duration patterns
- Archive old metrics data

### Security Monitoring

**Watch for:**
- ✅ Sudden spikes in session creation (>5x baseline)
- ✅ High failure rate for session creation
- ✅ Unusually short session durations (bots)
- ✅ Creation rate >100/min sustained for >5 minutes
- ✅ Active sessions growing without corresponding user growth

**Response actions:**
1. Check logs for anomaly warnings
2. Review source IPs for suspicious patterns
3. Enable rate limiting if not already active
4. Consider temporary IP blocking for persistent attackers
5. Scale up infrastructure if legitimate traffic surge

---

## Troubleshooting

### Metrics Not Appearing

**Check 1: Endpoint accessible**
```bash
curl http://localhost:8000/metrics
```

**Check 2: Prometheus scraping**
```bash
# Check Prometheus targets
curl http://localhost:9090/api/v1/targets | jq '.data.activeTargets[] | select(.labels.job=="ragged-api")'
```

**Check 3: Firewall rules**
```bash
# Ensure port 8000 accessible from Prometheus
telnet ragged-api 8000
```

### Grafana Dashboard Not Showing Data

**Check 1: Datasource configured**
- Grafana → Configuration → Data Sources
- Test connection to Prometheus
- Verify URL is `http://prometheus:9090`

**Check 2: Time range**
- Grafana uses relative time ranges (e.g., "Last 1 hour")
- Ensure there's data in the selected time range
- Try "Last 6 hours" or "Today so far"

**Check 3: Metrics exist in Prometheus**
```bash
# Query Prometheus directly
curl 'http://localhost:9090/api/v1/query?query=ragged_active_sessions'
```

### Anomaly Detection Not Triggering

**Check logs for warnings:**
```bash
docker logs ragged-api | grep "anomaly detected"
```

**Verify threshold configuration:**
- Default: 100 sessions/min
- Check if actual rate is below threshold
- Consider lowering threshold for testing

**Simulate high rate (testing):**
```bash
# Create 150 sessions in 30 seconds
for i in {1..150}; do
  curl -c /dev/null http://localhost:8000/api/health &
done
wait
```

---

## Production Deployment

### Docker Compose Configuration

**Complete monitoring stack:**
```yaml
services:
  ragged-api:
    # ... existing config ...
    networks:
      - ragged-network

  prometheus:
    image: prom/prometheus:latest
    container_name: ragged-prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
      - ./prometheus-alerts.yml:/etc/prometheus/prometheus-alerts.yml
      - prometheus-data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--storage.tsdb.retention.time=30d'
    networks:
      - ragged-network
    restart: unless-stopped

  grafana:
    image: grafana/grafana:latest
    container_name: ragged-grafana
    ports:
      - "3000:3000"
    volumes:
      - grafana-data:/var/lib/grafana
      - ./grafana:/etc/grafana/provisioning/dashboards
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=${GRAFANA_ADMIN_PASSWORD:-admin}
      - GF_USERS_ALLOW_SIGN_UP=false
    networks:
      - ragged-network
    restart: unless-stopped
    depends_on:
      - prometheus

volumes:
  prometheus-data:
    name: ragged-prometheus-data
  grafana-data:
    name: ragged-grafana-data
```

### Security Hardening

**Prometheus:**
- ✅ Bind to internal network only
- ✅ Use authentication (basic auth or OAuth)
- ✅ Restrict scrape targets
- ✅ Enable HTTPS

**Grafana:**
- ✅ Change default admin password
- ✅ Disable sign-up
- ✅ Use HTTPS (reverse proxy)
- ✅ Enable audit logging

**Metrics Endpoint:**
- ✅ Consider restricting `/metrics` to internal network
- ✅ Add authentication if exposed publicly
- ✅ Rate limit `/metrics` requests

---

## Related Documentation

- [v0.6.2 Roadmap](../development/roadmap/version/v0.6/v0.6.2.md) - SECURITY-004 implementation plan
- [Session Persistence](../development/implementation/version/v0.6/v0.6.2/session-persistence.md) - SECURITY-003 session storage
- [v0.6.0 Security Audit](../audit/security/baseline/v0.6.0-security-audit.md) - Audit findings

