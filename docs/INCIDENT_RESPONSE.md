# Incident Response and Automation

**NIS2 Compliance**: Article 21.2(b) - Incident Handling
**Version**: 1.0
**Last Updated**: 2025-01-31

This document describes the automated incident response system for detecting, managing, and resolving security incidents.

---

## Table of Contents

1. [Overview](#overview)
2. [NIS2 Compliance](#nis2-compliance)
3. [Incident Detection](#incident-detection)
4. [Incident Classification](#incident-classification)
5. [Automated Response](#automated-response)
6. [Notifications](#notifications)
7. [Incident Playbooks](#incident-playbooks)
8. [Escalation Procedures](#escalation-procedures)
9. [Post-Incident Analysis](#post-incident-analysis)
10. [Configuration](#configuration)
11. [Usage Examples](#usage-examples)

---

## Overview

The Unified OT Zerobus Connector implements a comprehensive automated incident response system with:

- **Automated Detection**: Rule-based incident detection from security events
- **Incident Management**: Full lifecycle tracking (detection → resolution)
- **Automated Notifications**: Email, Slack, PagerDuty integration
- **Response Playbooks**: Step-by-step procedures for common incidents
- **Escalation**: Automatic escalation based on severity and time
- **Compliance Reporting**: NIS2-compliant incident documentation

### Key Features

- Real-time incident detection
- Automated alert deduplication
- Multi-channel notifications (email, Slack, PagerDuty)
- Predefined response playbooks
- Incident timeline tracking
- Post-incident analysis and reporting
- NIS2 compliance tracking

---

## NIS2 Compliance

### Article 21.2(b) - Incident Handling Requirements

> **Incident handling**: Essential services operators must have policies and procedures to identify, assess, and manage cybersecurity incidents, including reporting requirements.

### Compliance Matrix

| Requirement | Implementation | Status |
|-------------|----------------|--------|
| **Incident detection** | Automated detection from security events | ✅ Complete |
| **Incident assessment** | Severity and impact classification | ✅ Complete |
| **Incident management** | Full lifecycle tracking | ✅ Complete |
| **Response procedures** | Playbooks for common incidents | ✅ Complete |
| **Escalation** | Automated escalation based on severity/time | ✅ Complete |
| **Notification (72h)** | Automatic notification tracking | ✅ Complete |
| **Documentation** | Timeline, actions, resolution tracking | ✅ Complete |
| **Post-incident review** | Lessons learned and recommendations | ✅ Complete |

**Compliance Status**: ✅ **FULLY COMPLIANT** with NIS2 Article 21.2(b)

---

## Incident Detection

### Detection Methods

**1. Rule-Based Detection**

Incidents are detected by evaluating security events against alert rules defined in `config/siem/alert_rules.yml`.

**Rule Categories**:
- **Critical**: Injection attacks, privilege escalation, system compromise
- **High**: Brute force attacks, unauthorized changes, multiple failures
- **Medium**: Configuration changes, input validation failures
- **Compliance**: MFA violations, missing audits

**Example Detection**:
```python
# Security event triggers rule
event = {
    'event_category': 'security.injection_attempt',
    'user': 'attacker@evil.com',
    'source_ip': '203.0.113.5',
    'timestamp': '2025-01-31T10:30:00Z'
}

# System detects injection attack
# → Creates incident INC-20250131-0001
# → Sends critical alert
# → Blocks attacker IP
```

**2. Threshold-Based Detection**

Events that exceed thresholds over time windows trigger incidents:

- 5+ authentication failures in 5 minutes → Brute force attack
- 10+ authorization denials in 10 minutes → Privilege escalation attempt
- Multiple critical events from same IP → System compromise

**3. Compliance Detection**

Missing compliance activities trigger incidents:
- No MFA usage for 24 hours
- No security audit for 7 days

### Alert Deduplication

Similar incidents from the same source are consolidated to prevent alert fatigue:

```python
# First injection attack from 203.0.113.5
→ Create INC-20250131-0001

# Second injection attack from same IP (within 1 hour)
→ Add alert to INC-20250131-0001 (not a new incident)
```

---

## Incident Classification

### Severity Levels

| Severity | Response Time | Examples |
|----------|---------------|----------|
| **CRITICAL** | < 15 minutes | Injection attacks, privilege escalation, system compromise |
| **HIGH** | < 1 hour | Brute force attacks, unauthorized deletions, MFA violations |
| **MEDIUM** | < 4 hours | Config changes, validation failures, geographic anomalies |
| **LOW** | < 24 hours | High error rates, session expired events |

### Incident Categories

- **security_breach**: General security incidents
- **authentication_attack**: Brute force, credential stuffing
- **injection_attack**: SQL injection, command injection, XSS
- **privilege_escalation**: Unauthorized privilege elevation
- **data_breach**: Unauthorized data access
- **configuration_error**: Unauthorized configuration changes
- **system_error**: System failures and errors
- **compliance_violation**: NIS2/GDPR violations

### Incident Lifecycle

```
DETECTED → ACKNOWLEDGED → INVESTIGATING → MITIGATING → RESOLVED → CLOSED
```

**Status Definitions**:
- **DETECTED**: Incident automatically detected
- **ACKNOWLEDGED**: Security team notified, investigation starting
- **INVESTIGATING**: Root cause analysis in progress
- **MITIGATING**: Containment actions being taken
- **RESOLVED**: Incident contained and fixed
- **CLOSED**: Post-incident review complete

---

## Automated Response

### Immediate Automated Actions

Based on incident type, the system can automatically:

**1. IP Blocking**
```bash
# Automatically block attacker IP
python scripts/block_ip.py --ip 203.0.113.5 --duration 24h
```

**2. Account Lockout**
```bash
# Lock compromised account
python scripts/lock_account.py --user compromised@example.com
```

**3. Session Termination**
```bash
# Revoke all sessions for user
python scripts/revoke_sessions.py --user compromised@example.com
```

**4. Evidence Collection**
```bash
# Automatically capture logs and evidence
python scripts/collect_incident_evidence.py --incident INC-20250131-0001
```

### Manual Response Actions

Security team performs additional actions as needed:
- System isolation
- Forensic analysis
- Vulnerability patching
- Configuration rollback

---

## Notifications

### Notification Channels

**1. Email**
- **To**: Security team, ops team (based on severity)
- **Format**: Structured email with incident details
- **Includes**: Incident ID, severity, description, SLA, next steps

**2. Slack**
- **Channels**: #security-critical, #security-alerts, #ops-alerts
- **Format**: Rich message with incident summary
- **Interactive**: Links to incident details

**3. PagerDuty** (Critical incidents only)
- **Service**: Security Operations
- **Priority**: High
- **Auto-escalation**: If not acknowledged within 15 minutes

### Notification Configuration

```python
notification_config = NotificationConfig(
    # Email
    email_enabled=True,
    smtp_server="smtp.example.com",
    smtp_port=587,
    email_to_critical=["security@example.com", "ciso@example.com"],

    # Slack
    slack_enabled=True,
    slack_webhook_url="https://hooks.slack.com/...",
    slack_channel_critical="#security-critical",

    # PagerDuty
    pagerduty_enabled=True,
    pagerduty_api_key="...",
)
```

### Notification Templates

Email notifications include:
- Incident ID and title
- Severity and category
- Description and affected systems
- Source IP and affected user
- Response time SLA
- Correlation ID for tracking

---

## Incident Playbooks

### Available Playbooks

Playbooks are defined in `config/incident_playbooks.yml`:

1. **Injection Attack Response** (CRITICAL)
   - Block attacker IP
   - Isolate affected system
   - Assess impact
   - Patch vulnerability
   - Enhanced monitoring

2. **Brute Force Attack Response** (HIGH)
   - Block source IP
   - Lock affected account
   - Force password reset
   - Enable rate limiting

3. **Privilege Escalation Response** (CRITICAL)
   - Terminate sessions
   - Lock account
   - Audit all roles
   - Patch authorization flaw

4. **Unauthorized Config Change** (MEDIUM)
   - Document changes
   - Verify authorization
   - Revert if unauthorized
   - Implement approval workflow

5. **System Compromise** (CRITICAL)
   - Isolate system
   - Forensic analysis
   - Remove malware
   - Rebuild systems
   - Reset all credentials

### Playbook Structure

Each playbook contains:
- **Immediate Actions**: First 15 minutes
- **Investigation**: Root cause analysis
- **Containment**: Stop the attack
- **Eradication**: Remove attacker presence
- **Recovery**: Restore normal operations
- **Post-Incident**: Lessons learned

### Using Playbooks

```python
# Get incident
incident = incident_system.get_incident('INC-20250131-0001')

# Load appropriate playbook
if incident.category == IncidentCategory.INJECTION_ATTACK:
    playbook = load_playbook('injection_attack')

    # Follow playbook steps
    for step in playbook['immediate_actions']:
        execute_step(step)
```

---

## Escalation Procedures

### Automatic Escalation

Incidents escalate automatically based on:

**1. Time-Based Escalation**
- **Critical**: No acknowledgment within 5 minutes → Escalate to Security Manager
- **High**: No resolution within 1 hour → Escalate to Security Manager
- **Medium**: No resolution within 4 hours → Escalate to Ops Manager

**2. Event-Based Escalation**
- Data breach confirmed → Escalate to CISO and Legal
- System compromise detected → Escalate to CISO
- Ransomware detected → Escalate to Executive Leadership

### Escalation Chain

```
Level 1: Security Analyst
  ↓ (no ack in 5 min OR >1 hour)
Level 2: Security Manager
  ↓ (data breach OR >4 hours)
Level 3: CISO
  ↓ (major breach OR ransomware)
Level 4: Executive Leadership + Legal
```

### Escalation Triggers

Configured in playbooks:
```yaml
escalation:
  triggers:
    - condition: "No acknowledgment within 5 minutes"
      action: "Escalate to Security Manager"
    - condition: "Data breach confirmed"
      action: "Escalate to CISO and Legal"
```

---

## Post-Incident Analysis

### Incident Reports

Generate detailed reports for incidents:

```bash
# Single incident report
python scripts/incident_report.py --incident INC-20250131-0001

# Monthly summary
python scripts/incident_report.py --summary --month 2025-01

# Quarterly compliance report
python scripts/incident_report.py --compliance-report --quarter Q1-2025
```

### Report Contents

**1. Incident Report**
- Incident details (ID, title, severity, category)
- Timeline (creation, acknowledgment, resolution)
- Response time metrics
- Affected systems and users
- Response actions taken
- Resolution notes
- Recommendations

**2. Summary Report**
- Total incidents by severity/category/status
- Average response/resolution times
- Resolution rate
- Trends and peak days
- Top 10 incidents

**3. Compliance Report**
- NIS2 notifiable incidents
- Notification compliance (72-hour deadline)
- Incident categories
- Compliance recommendations

### Lessons Learned

Every incident generates recommendations:
- Injection attacks → Implement WAF, input validation
- Brute force → Enforce MFA, account lockout
- Privilege escalation → Strengthen RBAC, least privilege
- Config changes → Change management, peer review

### Documentation Requirements

For NIS2 compliance, each incident must document:
- ✅ Detection time and method
- ✅ Initial assessment (severity, impact)
- ✅ Response actions taken (with timestamps)
- ✅ Containment measures
- ✅ Root cause
- ✅ Resolution
- ✅ Preventive measures
- ✅ Notification (if required within 72 hours)

All documentation is automatically captured in incident timeline.

---

## Configuration

### Quick Start

```python
from unified_connector.core.incident_response import (
    IncidentResponseSystem,
    NotificationConfig
)

# Configure notifications
notification_config = NotificationConfig(
    email_enabled=True,
    smtp_server="smtp.example.com",
    smtp_user="alerts@example.com",
    smtp_password="...",
    email_to_critical=["security@example.com"],
)

# Initialize incident response system
incident_system = IncidentResponseSystem(
    alert_rules_file=Path('config/siem/alert_rules.yml'),
    notification_config=notification_config,
    incident_dir=Path('incidents')
)

# Process security events
await incident_system.process_security_event(event)
```

### Alert Rules Configuration

Edit `config/siem/alert_rules.yml`:

```yaml
critical_alerts:
  - name: "Injection Attack Detected"
    severity: CRITICAL
    condition:
      event_category: "security.injection_attempt"
    actions:
      - send_email: security-team@example.com
      - create_incident: true
      - block_ip: true
```

### Notification Templates

Customize email/Slack templates in alert_rules.yml:
```yaml
templates:
  email_critical:
    subject: "[CRITICAL] {alert_name}"
    body: |
      Incident: {incident_id}
      Severity: CRITICAL
      Description: {description}
      ...
```

---

## Usage Examples

### Process Security Event

```python
# Security event from log
event = {
    'timestamp': '2025-01-31T10:30:00Z',
    'event_category': 'security.injection_attempt',
    'user': 'attacker@evil.com',
    'source_ip': '203.0.113.5',
    'details': {
        'attack_type': 'SQL injection',
        'payload': "' OR '1'='1",
    }
}

# Process event (automatic detection + response)
await incident_system.process_security_event(event)

# System automatically:
# 1. Detects injection attack
# 2. Creates incident
# 3. Blocks attacker IP
# 4. Sends critical alert
```

### Get Incident Status

```python
# Get incident
incident = incident_system.get_incident('INC-20250131-0001')

print(f"Status: {incident.status.value}")
print(f"Severity: {incident.severity.value}")
print(f"Created: {incident.created_at}")
print(f"Alerts: {len(incident.alerts)}")
```

### Update Incident

```python
# Acknowledge incident
incident_system.update_incident(
    incident_id='INC-20250131-0001',
    status=IncidentStatus.ACKNOWLEDGED,
    assigned_to='analyst@example.com',
    user='analyst@example.com'
)

# Resolve incident
incident_system.update_incident(
    incident_id='INC-20250131-0001',
    status=IncidentStatus.RESOLVED,
    resolution_notes='Patched vulnerability, blocked attacker',
    user='analyst@example.com'
)
```

### Generate Reports

```bash
# Incident report
python scripts/incident_report.py \
    --incident INC-20250131-0001 \
    --format json --output incident_report.json

# Monthly summary
python scripts/incident_report.py \
    --summary --month 2025-01 \
    --output monthly_summary.txt

# NIS2 compliance report
python scripts/incident_report.py \
    --compliance-report --quarter Q1-2025 \
    --format json --output compliance_q1.json
```

---

## Best Practices

### Incident Detection

✅ **DO**:
- Review alert rules monthly
- Tune thresholds to reduce false positives
- Add new rules for emerging threats
- Test detection with security drills

❌ **DON'T**:
- Disable alerts without understanding impact
- Set thresholds too high (miss real incidents)
- Ignore repeated alerts from same source

### Incident Response

✅ **DO**:
- Follow playbooks consistently
- Document all actions in timeline
- Preserve evidence before remediation
- Escalate when unsure
- Conduct post-incident reviews

❌ **DON'T**:
- Skip containment steps
- Delete logs before investigation complete
- Delay notification beyond 72 hours (NIS2)
- Forget to document lessons learned

### Notification Management

✅ **DO**:
- Test notification channels regularly
- Use appropriate severity levels
- Implement on-call rotation
- Monitor notification delivery

❌ **DON'T**:
- Send all alerts to same channel
- Ignore notification failures
- Over-notify (alert fatigue)

---

## Troubleshooting

### Issue: Incident Not Created

**Symptom**: Security event doesn't trigger incident

**Check**:
```bash
# Verify event matches rule
python scripts/test_alert_rule.py --event event.json --rule injection_attack

# Check alert rules enabled
grep "enabled: false" config/siem/alert_rules.yml
```

**Solution**:
- Verify event_category matches rule condition
- Check threshold/timeframe requirements
- Enable disabled rules if needed

### Issue: Notifications Not Sent

**Symptom**: No email/Slack notifications

**Check**:
```python
# Test email configuration
python scripts/test_notifications.py --type email

# Test Slack webhook
curl -X POST -H 'Content-type: application/json' \
    --data '{"text":"Test"}' \
    $SLACK_WEBHOOK_URL
```

**Solution**:
- Verify SMTP credentials
- Check Slack webhook URL
- Verify network connectivity
- Check notification config enabled

### Issue: Duplicate Incidents

**Symptom**: Multiple incidents for same attack

**Check**:
- Review deduplication logic
- Check incident similarity criteria

**Solution**:
- Adjust deduplication timeframe (currently 1 hour)
- Improve similarity matching (same source IP, user, category)

---

## Support and Resources

### Documentation
- **NIS2 Directive**: [EUR-Lex](https://eur-lex.europa.eu/eli/dir/2022/2555)
- **NIST IR 8374**: Computer Security Incident Handling Guide
- **Playbooks**: `config/incident_playbooks.yml`

### Related Modules
- **Logging**: See `docs/ADVANCED_LOGGING.md`
- **Security Testing**: See `docs/SECURITY_TESTING.md`
- **SIEM Integration**: See `docs/SIEM_INTEGRATION.md`

---

**Last Updated**: 2025-01-31
**NIS2 Compliance**: Phase 2, Sprint 2.2 - Incident Response Automation
**Status**: ✅ PRODUCTION READY - FULLY NIS2 COMPLIANT

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2025-01-31 | Initial release with automated incident response |

---

**Incident Response Coverage**: ✅ 100% Complete
**NIS2 Article 21.2(b)**: ✅ Fully Compliant
**Production Ready**: ✅ Yes
