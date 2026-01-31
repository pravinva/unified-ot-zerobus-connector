# SIEM Integration Guide

**NIS2 Compliance**: Article 21.2(b) - Incident Handling
**Version**: 1.0
**Last Updated**: 2025-01-31

This guide explains how to integrate the Unified OT Zerobus Connector with Security Information and Event Management (SIEM) systems for centralized security monitoring and incident response.

---

## Table of Contents

1. [Overview](#overview)
2. [Structured Logging](#structured-logging)
3. [Log Shipping](#log-shipping)
4. [SIEM Platform Integration](#siem-platform-integration)
5. [Security Dashboards](#security-dashboards)
6. [Alert Configuration](#alert-configuration)
7. [Incident Response](#incident-response)
8. [Compliance Reporting](#compliance-reporting)

---

## Overview

### Why SIEM Integration?

SIEM integration is required for:
- **NIS2 Compliance**: Article 21.2(b) mandates incident detection and response capabilities
- **Centralized Monitoring**: Aggregate logs from all systems
- **Real-time Alerting**: Detect security incidents as they occur
- **Forensic Analysis**: Investigate security incidents
- **Compliance Reporting**: Generate audit reports for regulators

### Architecture

```
┌─────────────────────────────────────────┐
│  Unified OT Zerobus Connector           │
│  ┌─────────────────────────────────┐   │
│  │  Structured JSON Logging         │   │
│  │  - Security events               │   │
│  │  - Correlation IDs               │   │
│  │  - User actions                  │   │
│  └──────────────┬──────────────────┘   │
└─────────────────┼───────────────────────┘
                  │
                  ▼
         ┌─────────────────┐
         │  Log Shipping    │
         │  - Filebeat      │
         │  - Rsyslog       │
         │  - Fluentd       │
         └────────┬─────────┘
                  │
                  ▼
    ┌─────────────────────────────┐
    │  SIEM Platform              │
    │  - Splunk                   │
    │  - ELK Stack                │
    │  - Azure Sentinel           │
    │  - QRadar, ArcSight, etc.   │
    └──────────────┬──────────────┘
                   │
                   ▼
         ┌──────────────────────┐
         │  Response Actions     │
         │  - Alerts             │
         │  - Incidents          │
         │  - Dashboards         │
         │  - Reports            │
         └───────────────────────┘
```

---

## Structured Logging

### Log Format

All security events are logged in JSON format for easy parsing:

```json
{
  "timestamp": "2025-01-31T12:34:56.789Z",
  "level": "WARNING",
  "message": "Authentication failed for user john@example.com: Invalid password",
  "event_category": "auth.failure",
  "correlation_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "user": "john@example.com",
  "source_ip": "192.168.1.100",
  "application": "unified-ot-connector",
  "component": "auth",
  "action": "login",
  "result": "failed",
  "details": {
    "reason": "Invalid password",
    "attempts": 3
  }
}
```

### Event Categories

| Category | Description | Severity | Example |
|----------|-------------|----------|---------|
| `auth.success` | Successful authentication | INFO | User logged in |
| `auth.failure` | Failed authentication | WARNING | Invalid password |
| `auth.mfa.failure` | MFA verification failed | WARNING | MFA code incorrect |
| `authz.denied` | Authorization denied | WARNING | Permission denied |
| `security.injection_attempt` | Injection attack detected | CRITICAL | SQL injection attempt |
| `security.path_traversal` | Path traversal attempt | CRITICAL | ../../../etc/passwd |
| `validation.failed` | Input validation failed | WARNING | Invalid input format |
| `config.changed` | Configuration modified | INFO | Source added |
| `source.deleted` | Source deleted | WARNING | Source removed |
| `system.error` | System error occurred | ERROR | Database connection failed |

**Full list**: See `unified_connector/core/structured_logging.py`

### Correlation IDs

Every HTTP request is assigned a unique correlation ID that appears in all related log entries. This enables:
- Request tracing across multiple log entries
- Incident investigation
- Performance analysis

**Example**: Trace a failed API request
```bash
grep '"correlation_id":"a1b2c3d4-e5f6-7890-abcd-ef1234567890"' /var/log/unified-connector/unified_connector.log
```

---

## Log Shipping

### Option 1: Filebeat (ELK Stack)

**Install Filebeat**:
```bash
# Ubuntu/Debian
curl -L -O https://artifacts.elastic.co/downloads/beats/filebeat/filebeat-8.11.0-amd64.deb
sudo dpkg -i filebeat-8.11.0-amd64.deb

# macOS
brew install filebeat
```

**Configure**:
```bash
# Copy configuration
sudo cp config/siem/filebeat.yml /etc/filebeat/filebeat.yml

# Edit credentials
sudo nano /etc/filebeat/filebeat.yml
# Set ELASTICSEARCH_PASSWORD

# Test configuration
sudo filebeat test config

# Start Filebeat
sudo systemctl start filebeat
sudo systemctl enable filebeat
```

**Verify**:
```bash
# Check Filebeat status
sudo systemctl status filebeat

# Test connection to Elasticsearch
curl -u elastic:$ELASTICSEARCH_PASSWORD http://localhost:9200/_cat/indices?v | grep unified-connector
```

### Option 2: Rsyslog (Splunk, QRadar, Azure Sentinel)

**Configure Rsyslog**:
```bash
# Install rsyslog
sudo apt install rsyslog

# Copy configuration
sudo cp config/siem/rsyslog.conf /etc/rsyslog.d/30-unified-connector.conf

# Edit SIEM endpoint
sudo nano /etc/rsyslog.d/30-unified-connector.conf
# Update Target= to your SIEM server

# Restart rsyslog
sudo systemctl restart rsyslog
```

**Test**:
```bash
# Generate test log
logger -t unified-connector-security -p local1.warning "Test security event"

# Check if sent to SIEM
sudo tail -f /var/log/syslog | grep unified-connector
```

### Option 3: Fluentd

**Install Fluentd**:
```bash
curl -fsSL https://toolbelt.treasuredata.com/sh/install-ubuntu-focal-fluent-package5-lts.sh | sh
```

**Configure**:
```yaml
# /etc/fluent/fluent.conf
<source>
  @type tail
  path /var/log/unified-connector/*.log
  pos_file /var/log/fluent/unified-connector.pos
  tag unified-connector
  <parse>
    @type json
    time_key timestamp
    time_format %Y-%m-%dT%H:%M:%S.%LZ
  </parse>
</source>

<match unified-connector>
  @type elasticsearch
  host localhost
  port 9200
  logstash_format true
  logstash_prefix unified-connector
</match>
```

---

## SIEM Platform Integration

### Splunk

**1. Install Splunk Universal Forwarder**:
```bash
wget -O splunkforwarder.tgz 'https://download.splunk.com/...'
tar xvzf splunkforwarder.tgz -C /opt
```

**2. Configure Input**:
```bash
# /opt/splunkforwarder/etc/system/local/inputs.conf
[monitor:///var/log/unified-connector/*.log]
disabled = false
index = unified-connector
sourcetype = _json

[monitor:///var/log/unified-connector/security.log]
disabled = false
index = unified-connector
sourcetype = _json
priority = high
```

**3. Configure Output**:
```bash
# /opt/splunkforwarder/etc/system/local/outputs.conf
[tcpout]
defaultGroup = splunk-indexer

[tcpout:splunk-indexer]
server = splunk.example.com:9997
```

**4. Install Queries**:
- Copy `config/siem/splunk_queries.spl` to Splunk
- Create saved searches for alerts
- Set up dashboards

**5. Create Index**:
```spl
# In Splunk Web UI
Settings > Indexes > New Index
- Index Name: unified-connector
- Max Size: 10GB
- Retention: 90 days
```

### ELK Stack (Elasticsearch, Logstash, Kibana)

**1. Configure Elasticsearch Index Template**:
```bash
curl -X PUT "localhost:9200/_index_template/unified-connector" -H 'Content-Type: application/json' -d'
{
  "index_patterns": ["unified-connector-*"],
  "template": {
    "settings": {
      "number_of_shards": 1,
      "number_of_replicas": 1
    },
    "mappings": {
      "properties": {
        "timestamp": { "type": "date" },
        "level": { "type": "keyword" },
        "event_category": { "type": "keyword" },
        "user": { "type": "keyword" },
        "source_ip": { "type": "ip" },
        "correlation_id": { "type": "keyword" }
      }
    }
  }
}
'
```

**2. Create Kibana Index Pattern**:
```bash
# In Kibana UI
Management > Stack Management > Index Patterns
- Index pattern: unified-connector-*
- Time field: @timestamp
```

**3. Import Dashboards**:
```bash
# Import saved objects
curl -X POST "localhost:5601/api/saved_objects/_import" \
  -H "kbn-xsrf: true" \
  --form file=@kibana-dashboards.ndjson
```

### Azure Sentinel

**1. Configure Log Analytics Workspace**:
```bash
# Create workspace
az monitor log-analytics workspace create \
  --resource-group unified-connector-rg \
  --workspace-name unified-connector-workspace
```

**2. Configure Data Connector**:
- Navigate to Azure Sentinel > Configuration > Data connectors
- Select "Syslog"
- Configure agent to collect from rsyslog

**3. Create Custom Log Table**:
```kql
// In Log Analytics
UnifiedConnectorLogs_CL
| extend
    Timestamp = todatetime(timestamp_s),
    Level = level_s,
    EventCategory = event_category_s,
    User = user_s,
    SourceIP = source_ip_s
```

**4. Create Analytics Rules**:
- Navigate to Azure Sentinel > Configuration > Analytics
- Import rules from `config/siem/alert_rules.yml`

---

## Security Dashboards

### Dashboard Components

**1. Authentication Monitoring**
- Failed login attempts (last 24h)
- Authentication by user/country
- MFA usage rate
- Brute force detection

**2. Authorization Monitoring**
- Permission denials by user
- Admin actions timeline
- Privilege escalation attempts

**3. Threat Detection**
- Injection attempts
- Path traversal attempts
- XSS attempts
- Multiple attack types from same IP

**4. System Health**
- Error rate trend
- System starts/stops
- Configuration changes

**5. User Behavior Analytics**
- User activity summary
- After-hours activity
- Geographic anomalies

### Example: Splunk Dashboard XML

```xml
<dashboard>
  <label>Unified OT Connector - Security Overview</label>
  <row>
    <panel>
      <title>Failed Authentications (24h)</title>
      <chart>
        <search>
          <query>
            index=unified-connector event_category="auth.failure"
            | timechart count by user
          </query>
          <earliest>-24h@h</earliest>
          <latest>now</latest>
        </search>
        <option name="charting.chart">line</option>
      </chart>
    </panel>
  </row>
</dashboard>
```

---

## Alert Configuration

### Alert Priorities

| Priority | Response Time | Examples |
|----------|--------------|----------|
| CRITICAL | Immediate | Injection attempts, system compromise |
| HIGH | 1 hour | Brute force, unauthorized deletions |
| MEDIUM | 4 hours | Config changes, validation failures |
| LOW | Daily review | High error rate, session expirations |

### Setting Up Alerts

**1. Copy Alert Rules**:
```bash
cp config/siem/alert_rules.yml /etc/unified-connector/
```

**2. Configure Notification Channels**:
```yaml
# alert_rules.yml
alert_settings:
  email:
    smtp_server: smtp.example.com
    from_address: alerts@example.com

  slack:
    webhook_url: https://hooks.slack.com/services/YOUR/WEBHOOK/URL

  pagerduty:
    integration_key: YOUR_PAGERDUTY_KEY
```

**3. Test Alerts**:
```bash
# Trigger test injection attempt
curl -X POST http://localhost:8082/api/sources \
  -H "Content-Type: application/json" \
  -d '{"name": "; rm -rf /", "protocol": "opcua", "endpoint": "opc.tcp://host:4840"}'

# Check for alert
tail -f /var/log/unified-connector/security.log | grep injection
```

---

## Incident Response

### Incident Response Workflow

```
1. Alert Triggered
   ↓
2. SIEM Creates Incident
   ↓
3. SOC Analyst Investigates
   - Check correlation ID
   - Review related events
   - Assess impact
   ↓
4. Containment
   - Block IP (if attack)
   - Disable user (if compromised)
   - Isolate system (if needed)
   ↓
5. Remediation
   - Patch vulnerability
   - Update rules
   - Reset credentials
   ↓
6. Recovery
   - Restore service
   - Monitor for recurrence
   ↓
7. Post-Incident Review
   - Document incident
   - Update procedures
   - Report to management
```

### Investigation Playbooks

**Playbook: Injection Attack**
1. Identify correlation ID from alert
2. Trace full request: `grep correlation_id=<ID> *.log`
3. Check user account for compromise
4. Block source IP immediately
5. Review other requests from same IP
6. Check for data exfiltration
7. Update input validation rules
8. Report to security team

**Playbook: Brute Force Attack**
1. Identify user and source IP
2. Count total failed attempts
3. Check if attack is ongoing
4. Block source IP temporarily (1-24 hours)
5. Notify user if legitimate account
6. Review account for compromise
7. Consider MFA enforcement

---

## Compliance Reporting

### NIS2 Required Reports

**1. Monthly Security Report**
```splunk
index=unified-connector earliest=-30d@d latest=now
| stats count by event_category, level
| eval nis2_article="21.2(b)"
```

**2. Incident Response Report**
```splunk
index=unified-connector level IN (WARNING, CRITICAL)
  OR event_category IN (security.*, authz.denied)
| stats count by event_category, result
```

**3. Access Control Audit (Article 21.2(g))**
```splunk
index=unified-connector event_category IN (auth.*, authz.*)
| stats count by user, event_category, result
```

**4. Configuration Change Log**
```splunk
index=unified-connector event_category=config.changed
| table _time, user, config_type, changes
```

### Automated Report Generation

**Weekly Security Summary**:
```bash
#!/bin/bash
# /etc/cron.weekly/security-report.sh

# Generate report
splunk search "index=unified-connector earliest=-7d" \
  -output csv \
  > /tmp/weekly-security-report.csv

# Email to stakeholders
mail -s "Weekly Security Report" \
  -a /tmp/weekly-security-report.csv \
  security-team@example.com < /dev/null
```

---

## Troubleshooting

### Logs Not Appearing in SIEM

**Check 1: Log files exist**
```bash
ls -lh /var/log/unified-connector/
# Should see: unified_connector.log, security.log
```

**Check 2: Log shipping is running**
```bash
# Filebeat
sudo systemctl status filebeat

# Rsyslog
sudo systemctl status rsyslog
```

**Check 3: Network connectivity**
```bash
# Test connection to SIEM
telnet siem.example.com 514
nc -zv siem.example.com 9997
```

**Check 4: JSON parsing**
```bash
# Verify logs are valid JSON
head -1 /var/log/unified-connector/unified_connector.log | jq .
```

### Alerts Not Firing

**Check 1: Alert rules syntax**
```bash
# Validate YAML
python -c "import yaml; yaml.safe_load(open('config/siem/alert_rules.yml'))"
```

**Check 2: SIEM query syntax**
```bash
# Test Splunk query
splunk search "index=unified-connector event_category=auth.failure | stats count"
```

**Check 3: Notification channels**
```bash
# Test email
echo "Test" | mail -s "Test Alert" security-team@example.com

# Test Slack
curl -X POST -H 'Content-type: application/json' \
  --data '{"text":"Test alert"}' \
  YOUR_SLACK_WEBHOOK_URL
```

---

## Best Practices

1. **Log Retention**: Keep logs for 90+ days (NIS2 requirement)
2. **Log Integrity**: Use write-once storage or signing
3. **Regular Reviews**: Review alerts weekly, tune rules monthly
4. **Incident Drills**: Practice incident response quarterly
5. **Documentation**: Document all incidents and lessons learned
6. **Monitoring**: Monitor SIEM health and log ingestion rates
7. **Updates**: Keep SIEM queries updated with new threats

---

## References

- [NIS2 Directive (EU) 2022/2555](https://eur-lex.europa.eu/eli/dir/2022/2555)
- [NIST Incident Response Guide](https://nvlpubs.nist.gov/nistpubs/SpecialPublications/NIST.SP.800-61r2.pdf)
- [Splunk Documentation](https://docs.splunk.com/)
- [ELK Stack Documentation](https://www.elastic.co/guide/)
- [Azure Sentinel Documentation](https://learn.microsoft.com/en-us/azure/sentinel/)

---

**Last Updated**: 2025-01-31
**NIS2 Compliance**: Phase 1, Sprint 1.3 - SIEM Integration
**Status**: Production Ready
