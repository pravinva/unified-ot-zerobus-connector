# NIS2 Quick Reference Guide
## Unified OT Zerobus Connector - Operations Cheat Sheet

**Version:** 1.0
**Last Updated:** 2026-01-31
**Compliance Status:** ✅ 100% COMPLIANT (24/24 controls)

---

## Daily Operations

### Check System Status
```bash
# Check for active incidents
python scripts/incident_report.py --active

# View recent anomalies
tail -f logs/anomalies.log

# Check system health
tail -f logs/performance.log
```

### Monitor Dashboards
- Web UI: https://localhost:8443/dashboard
- Incident Dashboard: https://localhost:8443/incidents
- Compliance Dashboard: https://localhost:8443/compliance

---

## Weekly Operations

### Run Vulnerability Scan
```bash
# Full vulnerability scan
python scripts/vuln_scan.py --full

# View prioritized vulnerabilities
python scripts/vuln_scan.py --priority

# Get summary
python scripts/vuln_scan.py --summary
```

### Analyze Security Logs
```bash
# Security events (last 7 days)
python scripts/analyze_logs.py --security --days 7

# Audit trail (last 7 days)
python scripts/analyze_logs.py --audit --days 7

# Error patterns
python scripts/analyze_logs.py --errors --days 7
```

---

## Monthly Operations

### Generate Compliance Report
```bash
# Summary report
python scripts/nis2_compliance_report.py --summary

# Full report
python scripts/nis2_compliance_report.py --full

# Export to JSON
python scripts/nis2_compliance_report.py --json --output compliance_$(date +%Y%m).json
```

### Incident Response Summary
```bash
# Last 30 days
python scripts/incident_report.py --list --days 30

# Compliance report (72-hour tracking)
python scripts/incident_report.py --compliance --days 30
```

### Test Incident Response Playbooks
```bash
# Review playbooks
cat config/incident_playbooks.yml

# Test notification channels
# (Manual test: trigger test incident via web UI)
```

---

## Quarterly Operations

### Security Audit
```bash
# Run all security tests
pytest tests/security/test_security_controls.py -v

# Generate test report
pytest tests/security/ -v --html=security_audit_$(date +%Y%m).html
```

### Access Control Review
```bash
# Review user roles and permissions
# (Via web UI: Settings > Users > Roles)

# Check session configurations
grep -A 10 "session:" unified_connector/config/config.yaml
```

---

## Incident Response

### Incident Lifecycle Commands
```bash
# List active incidents
python scripts/incident_report.py --active

# Get incident details
python scripts/incident_report.py --details --incident-id INC-20260131-0001

# Update incident status (via web UI or API)
curl -X PATCH https://localhost:8443/api/incidents/INC-20260131-0001 \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"status": "investigating"}'
```

### Incident Severity Levels
- **CRITICAL:** Immediate PagerDuty alert + Email + Slack
- **HIGH:** Email + Slack (within 15 minutes)
- **MEDIUM:** Email + Slack (within 1 hour)
- **LOW:** Email (within 4 hours)

### Response Playbooks
1. **Injection Attack Response** (15 steps)
2. **Brute Force Attack Response** (9 steps)
3. **Privilege Escalation Response** (10 steps)
4. **Unauthorized Config Change** (7 steps)
5. **System Compromise** (12 steps)

Location: `config/incident_playbooks.yml`

---

## Vulnerability Management

### Vulnerability Workflow
```
DETECTED → ASSESSED → PATCHING_AVAILABLE → PATCHING_SCHEDULED → PATCHED
                  ↓
          MITIGATED / ACCEPTED_RISK / FALSE_POSITIVE
```

### Update Vulnerability Status
```bash
# Mark as patched
python scripts/vuln_scan.py --update \
  --vuln-id CVE-2024-1234 \
  --status patched \
  --notes "Updated package to v2.1.0"

# Get vulnerability details
python scripts/vuln_scan.py --details --vuln-id CVE-2024-1234
```

### Severity Levels (CVSS)
- **CRITICAL:** 9.0-10.0 (patch within 24 hours)
- **HIGH:** 7.0-8.9 (patch within 7 days)
- **MEDIUM:** 4.0-6.9 (patch within 30 days)
- **LOW:** 0.1-3.9 (patch within 90 days)

---

## Log Management

### Log Locations
- **Main Log:** `logs/app.log`
- **Audit Log:** `logs/audit.log`
- **Performance Log:** `logs/performance.log`
- **Incident Log:** `logs/incidents.log`
- **Anomaly Log:** `logs/anomalies.log`
- **Archived Logs:** `logs/archive/`

### Log Rotation
- **Max Size:** 100MB per file
- **Backups:** 10 files
- **Compression:** Gzip (80-90% savings)
- **Retention:** 90 days
- **Archive:** Logs >30 days

### Search Logs
```bash
# Search for specific user
grep "user_id.*john.doe" logs/audit.log

# Search for failed logins
grep "authentication.*failed" logs/audit.log

# Search for critical events
grep "\"severity\":\"critical\"" logs/app.log

# Search archived logs
zgrep "error" logs/archive/app.log.2026-01-01.gz
```

---

## Anomaly Detection

### Anomaly Types
1. **Authentication:** Unusual login times, geographic anomalies
2. **Traffic:** Unexpected traffic patterns
3. **Performance:** CPU/memory/throughput spikes
4. **Behavioral:** Deviation from normal user behavior
5. **Geographic:** Access from unusual locations
6. **Time:** Activity at unusual times
7. **Volume:** Unexpected data volume changes

### Anomaly Severity (Z-Score)
- **CRITICAL:** >3 standard deviations
- **HIGH:** 2-3 standard deviations
- **MEDIUM:** 1.5-2 standard deviations

### View Anomalies
```bash
# Recent anomalies
tail -n 50 logs/anomalies.log | jq .

# Anomalies by type
grep "\"anomaly_type\":\"authentication\"" logs/anomalies.log

# Critical anomalies only
grep "\"severity\":\"critical\"" logs/anomalies.log
```

---

## Authentication & Authorization

### User Roles
- **Admin:** Full access (all operations)
- **Operator:** Operations only (start/stop connectors, view data)
- **Viewer:** Read-only access

### Permission Types
- read, write, execute, delete, configure, discover, manage_users, view_logs, manage_security

### Session Management
- **Timeout:** 8 hours (configurable)
- **Max Sessions per User:** 5
- **Session Storage:** Encrypted with AES-256

### MFA Requirements
- **Algorithm:** TOTP (RFC 6238)
- **QR Code:** For provisioning
- **Backup Codes:** 8 codes, 12 characters each

---

## Encryption

### Data at Rest
- **Credentials:** AES-256-CBC with PBKDF2 (100,000 iterations)
- **Config Fields:** Field-level encryption with `ENC[...]` syntax
- **Key Storage:** File permissions 0600

### Data in Transit
- **Web UI:** HTTPS with TLS 1.2/1.3
- **OPC-UA:** SignAndEncrypt security mode
- **MQTT:** TLS/mTLS with certificate validation
- **Cipher Suites:** Strong ciphers only (no weak ciphers)

### Certificate Locations
- Web UI: `certs/server.crt`, `certs/server.key`
- OPC-UA: `certs/opcua_server.der`, `certs/opcua_server_key.pem`
- MQTT: `certs/mqtt_ca.crt`, `certs/mqtt_client.crt`, `certs/mqtt_client.key`

---

## NIS2 Compliance Articles

### Article 21.2(g): Authentication & Authorization
- ✅ OAuth2 authentication
- ✅ MFA enforcement
- ✅ RBAC
- ✅ Session management

### Article 21.2(h): Encryption
- ✅ AES-256 for credentials
- ✅ Config field encryption
- ✅ TLS 1.2/1.3 for HTTPS
- ✅ OPC-UA SignAndEncrypt
- ✅ MQTT TLS/mTLS

### Article 21.2(b): Incident Handling
- ✅ Automated detection
- ✅ Incident management
- ✅ Multi-channel notifications
- ✅ Response playbooks
- ✅ 72-hour tracking

### Article 21.2(f): Logging and Monitoring
- ✅ Structured logging
- ✅ Log rotation/compression
- ✅ Tamper-evident audit trail
- ✅ Performance metrics
- ✅ 90-day retention
- ✅ Anomaly detection

### Article 21.2(c): Vulnerability Handling
- ✅ Automated scanning
- ✅ CVE tracking
- ✅ Patch management
- ✅ Vulnerability prioritization

---

## Emergency Procedures

### CRITICAL Incident Response
1. **Acknowledge:** Log into web UI, acknowledge incident
2. **Assess:** Review incident details, timeline, affected systems
3. **Notify:** Automatic (PagerDuty + Email + Slack)
4. **Execute Playbook:** Follow step-by-step procedure
5. **Document:** Add notes to incident timeline
6. **Resolve:** Mark as resolved when fixed
7. **Close:** Add final summary and lessons learned

### System Compromise
1. **Isolate:** Disconnect affected systems
2. **Preserve Evidence:** Capture logs, memory dumps
3. **Analyze:** Determine scope and impact
4. **Remediate:** Follow System Compromise Playbook
5. **Verify:** Confirm all malicious artifacts removed
6. **Monitor:** Enhanced monitoring for 30 days
7. **Report:** Generate incident report for management

### Data Breach
1. **Contain:** Stop data exfiltration
2. **Assess:** Determine what data was accessed
3. **Notify:** Legal team + compliance officer (72-hour deadline)
4. **Remediate:** Close security gap
5. **Monitor:** Enhanced monitoring
6. **Report:** NIS2 notification within 72 hours

---

## Useful Commands

### System Status
```bash
# Service status
systemctl status unified-connector

# View running processes
ps aux | grep unified_connector

# Check disk space
df -h

# Check memory usage
free -h
```

### Configuration
```bash
# Validate configuration
python -m unified_connector validate-config

# Encrypt sensitive config value
python -m unified_connector encrypt-config "sensitive-value"

# Decrypt config value
python -m unified_connector decrypt-config "ENC[...]"
```

### Testing
```bash
# Run all tests
pytest tests/ -v

# Security tests only
pytest tests/security/ -v

# Specific test class
pytest tests/security/test_security_controls.py::TestAuthentication -v
```

### Logs
```bash
# Follow main log
tail -f logs/app.log

# Follow with JSON formatting
tail -f logs/app.log | jq .

# Search logs by level
jq 'select(.level=="ERROR")' logs/app.log

# Count errors by type
jq -r .error_type logs/app.log | sort | uniq -c
```

---

## Contact Information

### Support Contacts
- **Security Team:** security@company.com
- **Incident Response:** incident-response@company.com (24/7)
- **Compliance Officer:** compliance@company.com
- **Emergency Hotline:** +1-XXX-XXX-XXXX (24/7)

### Escalation Path
1. **Level 1:** Operator → Security Team
2. **Level 2:** Security Team → Security Manager
3. **Level 3:** Security Manager → CISO
4. **Level 4:** CISO → CEO (critical incidents only)

---

## Quick Links

### Documentation
- Full Implementation Summary: `docs/NIS2_IMPLEMENTATION_SUMMARY.md`
- Incident Response: `docs/INCIDENT_RESPONSE.md`
- Advanced Logging: `docs/ADVANCED_LOGGING.md`
- Encryption Overview: `docs/ENCRYPTION_OVERVIEW.md`
- Authentication: `docs/AUTHENTICATION.md`

### Configuration Files
- Main Config: `unified_connector/config/config.yaml`
- Incident Playbooks: `config/incident_playbooks.yml`
- Alert Rules: `config/siem/alert_rules.yml`

### Scripts
- Compliance Report: `scripts/nis2_compliance_report.py`
- Vulnerability Scan: `scripts/vuln_scan.py`
- Incident Report: `scripts/incident_report.py`
- Log Analysis: `scripts/analyze_logs.py`

---

## Maintenance Schedule

### Daily
- ☐ Monitor dashboards
- ☐ Review active incidents
- ☐ Check anomaly alerts

### Weekly
- ☐ Run vulnerability scan
- ☐ Analyze security logs
- ☐ Review and prioritize vulnerabilities

### Monthly
- ☐ Generate compliance report
- ☐ Test incident response playbooks
- ☐ Review access controls
- ☐ Incident response summary

### Quarterly
- ☐ Security audit
- ☐ Run comprehensive security tests
- ☐ Review and update RBAC permissions
- ☐ Security awareness training
- ☐ Review and update incident playbooks

### Annual
- ☐ Third-party penetration testing
- ☐ Comprehensive security architecture review
- ☐ Update risk assessment
- ☐ Review and update security policies

---

**Last Updated:** 2026-01-31
**Version:** 1.0
**Compliance Status:** ✅ 100% NIS2 COMPLIANT
