# NIS2 Implementation - Phase 1, Sprint 1.3: Incident Response System (SIEM Integration)

## Context
NIS2 Article 21.2(b) requires incident handling processes with 24-hour notification timelines. This requires SIEM integration for real-time security event monitoring and alerting.

## Target State
- Security events sent to SIEM (Splunk, ELK, Azure Sentinel, or syslog)
- Automatic alerting for security incidents
- Structured logging in CEF or JSON format
- Integration with incident response workflow

---

## Task 1: Implement SIEM Logging Handler

### Prompt for AI Assistant

```
Create SIEM integration for the Unified OT Connector to send security events to external SIEM systems.

REQUIREMENTS:
1. Support multiple SIEM types: syslog (RFC 5424), HTTP webhook, Splunk HEC
2. Send only security-relevant events (WARNING+)
3. Format events in CEF (Common Event Format) or JSON
4. Configurable alerting rules
5. Failover and buffering if SIEM unavailable

CREATE unified_connector/monitoring/siem_handler.py:
```python
import logging
import json
import socket
import ssl
from datetime import datetime
from typing import Dict, Any, Optional
from enum import Enum
import requests
from pathlib import Path

class SIEMType(Enum):
    SYSLOG = "syslog"
    HTTP = "http"
    SPLUNK_HEC = "splunk_hec"

class SecurityEventType(Enum):
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    CONFIGURATION = "configuration"
    NETWORK = "network"
    CREDENTIAL_ACCESS = "credential_access"
    AVAILABILITY = "availability"
    OPERATIONAL = "operational"

class SIEMHandler(logging.Handler):
    """Send security events to SIEM systems"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__()
        self.siem_type = SIEMType(config.get('type', 'syslog'))
        self.host = config['host']
        self.port = config.get('port', 514)
        self.protocol = config.get('protocol', 'tcp')  # tcp, udp, or tls
        self.format = config.get('format', 'cef')  # cef or json
        
        # Splunk HEC specific
        self.hec_token = config.get('hec_token')
        
        # HTTP specific
        self.http_endpoint = config.get('http_endpoint')
        self.http_headers = config.get('http_headers', {})
        
        # Buffering
        self.buffer_size = config.get('buffer_size', 1000)
        self.buffer = []
        self.buffer_file = Path(config.get('buffer_file', '~/.unified_connector/siem_buffer.json')).expanduser()
        
        # TLS
        self.tls_verify = config.get('tls_verify', True)
        self.tls_ca_cert = config.get('tls_ca_cert')
        
        # Initialize connection
        self._setup_connection()
        self._load_buffer()
    
    def _setup_connection(self):
        """Initialize SIEM connection"""
        if self.siem_type == SIEMType.SYSLOG:
            if self.protocol == 'tcp':
                self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                if self.protocol == 'tls':
                    context = ssl.create_default_context()
                    if not self.tls_verify:
                        context.check_hostname = False
                        context.verify_mode = ssl.CERT_NONE
                    elif self.tls_ca_cert:
                        context.load_verify_locations(self.tls_ca_cert)
                    self.socket = context.wrap_socket(self.socket, server_hostname=self.host)
                self.socket.connect((self.host, self.port))
            elif self.protocol == 'udp':
                self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        
        elif self.siem_type == SIEMType.HTTP or self.siem_type == SIEMType.SPLUNK_HEC:
            self.session = requests.Session()
            self.session.verify = self.tls_verify
            if self.tls_ca_cert:
                self.session.verify = self.tls_ca_cert
    
    def emit(self, record: logging.LogRecord):
        """Send log record to SIEM"""
        try:
            # Only send WARNING+ events
            if record.levelno < logging.WARNING:
                return
            
            # Format event
            event = self._format_event(record)
            
            # Send to SIEM
            self._send_event(event)
            
            # Flush buffer if accumulated
            if len(self.buffer) > 0:
                self._flush_buffer()
        
        except Exception as e:
            # Buffer event if SIEM unavailable
            self._buffer_event(event)
            logging.error(f"Failed to send event to SIEM: {e}")
    
    def _format_event(self, record: logging.LogRecord) -> Dict[str, Any]:
        """Format event in CEF or JSON"""
        event_type = self._classify_event(record)
        
        base_event = {
            'timestamp': datetime.utcnow().isoformat(),
            'severity': record.levelname,
            'source': 'unified-ot-connector',
            'event_type': event_type.value,
            'message': record.getMessage(),
            'user': getattr(record, 'user', 'system'),
            'action': getattr(record, 'action', 'unknown'),
            'result': getattr(record, 'result', 'unknown'),
            'source_ip': getattr(record, 'source_ip', None),
            'target': getattr(record, 'target', None),
            'details': getattr(record, 'details', {}),
        }
        
        if self.format == 'cef':
            return self._to_cef(base_event)
        else:
            return base_event
    
    def _to_cef(self, event: Dict[str, Any]) -> str:
        """Convert event to CEF (Common Event Format)"""
        # CEF Format: CEF:Version|Device Vendor|Device Product|Device Version|Signature ID|Name|Severity|Extension
        cef_header = (
            f"CEF:0|"
            f"Databricks|"
            f"Unified OT Connector|"
            f"1.0|"
            f"{event['event_type']}|"
            f"{event['action']}|"
            f"{self._severity_to_cef(event['severity'])}|"
        )
        
        # CEF Extensions
        extensions = [
            f"rt={event['timestamp']}",
            f"msg={event['message']}",
            f"outcome={event['result']}",
        ]
        
        if event.get('user'):
            extensions.append(f"suser={event['user']}")
        if event.get('source_ip'):
            extensions.append(f"src={event['source_ip']}")
        if event.get('target'):
            extensions.append(f"dst={event['target']}")
        
        return cef_header + " ".join(extensions)
    
    def _severity_to_cef(self, severity: str) -> int:
        """Convert Python log level to CEF severity (0-10)"""
        mapping = {
            'DEBUG': 0,
            'INFO': 3,
            'WARNING': 5,
            'ERROR': 7,
            'CRITICAL': 10,
        }
        return mapping.get(severity, 5)
    
    def _classify_event(self, record: logging.LogRecord) -> SecurityEventType:
        """Classify event type for SIEM"""
        msg = record.getMessage().lower()
        
        if 'authentication' in msg or 'login' in msg or 'logout' in msg:
            return SecurityEventType.AUTHENTICATION
        elif 'authorization' in msg or 'permission' in msg or 'forbidden' in msg:
            return SecurityEventType.AUTHORIZATION
        elif 'configuration' in msg or 'config' in msg:
            return SecurityEventType.CONFIGURATION
        elif 'circuit breaker' in msg or 'failure' in msg or 'degraded' in msg:
            return SecurityEventType.AVAILABILITY
        elif 'connection' in msg and ('failed' in msg or 'refused' in msg):
            return SecurityEventType.NETWORK
        elif 'credential' in msg or 'secret' in msg or 'token' in msg:
            return SecurityEventType.CREDENTIAL_ACCESS
        else:
            return SecurityEventType.OPERATIONAL
    
    def _send_event(self, event: Any):
        """Send event to SIEM"""
        if self.siem_type == SIEMType.SYSLOG:
            self._send_syslog(event)
        elif self.siem_type == SIEMType.HTTP:
            self._send_http(event)
        elif self.siem_type == SIEMType.SPLUNK_HEC:
            self._send_splunk_hec(event)
    
    def _send_syslog(self, event: str):
        """Send event via syslog"""
        message = f"<134>1 {event}\n"  # Priority 134 = Facility 16 (local0), Severity 6 (info)
        
        if self.protocol == 'udp':
            self.socket.sendto(message.encode('utf-8'), (self.host, self.port))
        else:
            self.socket.sendall(message.encode('utf-8'))
    
    def _send_http(self, event: Dict[str, Any]):
        """Send event via HTTP webhook"""
        self.session.post(
            self.http_endpoint,
            json=event,
            headers=self.http_headers,
            timeout=5
        )
    
    def _send_splunk_hec(self, event: Dict[str, Any]):
        """Send event to Splunk HTTP Event Collector"""
        splunk_event = {
            'time': datetime.utcnow().timestamp(),
            'source': 'unified-ot-connector',
            'sourcetype': '_json',
            'event': event
        }
        
        self.session.post(
            f"https://{self.host}:{self.port}/services/collector/event",
            json=splunk_event,
            headers={
                'Authorization': f'Splunk {self.hec_token}',
                'Content-Type': 'application/json'
            },
            timeout=5
        )
    
    def _buffer_event(self, event: Any):
        """Buffer event if SIEM unavailable"""
        self.buffer.append(event)
        
        if len(self.buffer) >= self.buffer_size:
            # Persist buffer to disk
            self._save_buffer()
    
    def _save_buffer(self):
        """Save buffer to disk"""
        self.buffer_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.buffer_file, 'w') as f:
            json.dump(self.buffer, f)
        logging.info(f"Saved {len(self.buffer)} events to buffer file")
    
    def _load_buffer(self):
        """Load buffered events from disk"""
        if self.buffer_file.exists():
            with open(self.buffer_file, 'r') as f:
                self.buffer = json.load(f)
            logging.info(f"Loaded {len(self.buffer)} buffered events")
    
    def _flush_buffer(self):
        """Flush buffered events to SIEM"""
        while self.buffer:
            event = self.buffer.pop(0)
            try:
                self._send_event(event)
            except Exception as e:
                # Re-buffer on failure
                self.buffer.insert(0, event)
                raise e
        
        # Clear buffer file
        if self.buffer_file.exists():
            self.buffer_file.unlink()
    
    def close(self):
        """Close SIEM connection"""
        if hasattr(self, 'socket'):
            self.socket.close()
        if hasattr(self, 'session'):
            self.session.close()
        
        super().close()
```

CREATE unified_connector/monitoring/alerts.py:
```python
from enum import Enum
from dataclasses import dataclass
from typing import List, Callable
import time

class AlertSeverity(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class AlertRule:
    name: str
    condition: str  # Event condition (e.g., "event_type=authentication AND result=failure")
    threshold: int  # Number of occurrences
    window_seconds: int  # Time window
    severity: AlertSeverity
    callback: Callable  # Function to call when alert triggers

class AlertManager:
    """Manage security alerting rules"""
    
    def __init__(self):
        self.rules: List[AlertRule] = []
        self.event_counts = {}  # Track event counts per rule
    
    def add_rule(self, rule: AlertRule):
        """Add alerting rule"""
        self.rules.append(rule)
        self.event_counts[rule.name] = []
    
    def process_event(self, event: dict):
        """Process event against alerting rules"""
        current_time = time.time()
        
        for rule in self.rules:
            if self._matches_condition(event, rule.condition):
                # Add to event count
                self.event_counts[rule.name].append(current_time)
                
                # Remove events outside window
                self.event_counts[rule.name] = [
                    t for t in self.event_counts[rule.name]
                    if current_time - t <= rule.window_seconds
                ]
                
                # Check threshold
                if len(self.event_counts[rule.name]) >= rule.threshold:
                    self._trigger_alert(rule, event)
                    # Reset counter
                    self.event_counts[rule.name] = []
    
    def _matches_condition(self, event: dict, condition: str) -> bool:
        """Check if event matches condition"""
        # Simple condition parser (could be enhanced with proper parser)
        conditions = condition.split(' AND ')
        
        for cond in conditions:
            key, value = cond.split('=')
            key = key.strip()
            value = value.strip()
            
            if event.get(key) != value:
                return False
        
        return True
    
    def _trigger_alert(self, rule: AlertRule, event: dict):
        """Trigger alert"""
        logging.critical(
            f"SECURITY ALERT: {rule.name} - {rule.severity.value}",
            extra={
                'alert_rule': rule.name,
                'alert_severity': rule.severity.value,
                'triggering_event': event
            }
        )
        
        # Call callback
        if rule.callback:
            rule.callback(rule, event)
```

UPDATE unified_connector/core/logging_setup.py:
```python
import logging
from unified_connector.monitoring.siem_handler import SIEMHandler
from unified_connector.monitoring.alerts import AlertManager, AlertRule, AlertSeverity

def setup_logging(config: dict):
    """Setup logging with SIEM integration"""
    
    # Standard logging
    logging.basicConfig(
        level=config.get('log_level', 'INFO'),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('unified_connector.log'),
            logging.StreamHandler()
        ]
    )
    
    # Add SIEM handler if configured
    if config.get('monitoring', {}).get('siem', {}).get('enabled'):
        siem_config = config['monitoring']['siem']
        siem_handler = SIEMHandler(siem_config)
        siem_handler.setLevel(logging.WARNING)  # Only security events
        logging.getLogger().addHandler(siem_handler)
        logging.info("SIEM integration enabled")
    
    # Setup alert manager
    alert_manager = AlertManager()
    
    # Add default alerting rules
    if config.get('monitoring', {}).get('siem', {}).get('alerts'):
        for alert_config in config['monitoring']['siem']['alerts']:
            rule = AlertRule(
                name=alert_config['name'],
                condition=alert_config['condition'],
                threshold=alert_config['threshold'],
                window_seconds=alert_config['window_seconds'],
                severity=AlertSeverity(alert_config['severity']),
                callback=lambda rule, event: logging.critical(f"Alert triggered: {rule.name}")
            )
            alert_manager.add_rule(rule)
    
    return alert_manager
```

UPDATE config.yaml:
```yaml
monitoring:
  siem:
    enabled: true
    type: syslog  # or 'http', 'splunk_hec'
    host: siem.company.com
    port: 514
    protocol: tls  # tcp, udp, or tls
    format: cef  # or 'json'
    
    # TLS settings
    tls_verify: true
    tls_ca_cert: /etc/connector/certs/siem-ca.pem
    
    # Buffering
    buffer_size: 1000
    buffer_file: ~/.unified_connector/siem_buffer.json
    
    # Alerting rules
    alerts:
      - name: "Multiple failed logins"
        condition: "event_type=authentication AND result=failure"
        threshold: 5
        window_seconds: 300
        severity: high
      
      - name: "Circuit breaker open"
        condition: "event_type=availability AND action=circuit_breaker_open"
        threshold: 1
        window_seconds: 60
        severity: critical
      
      - name: "Unauthorized access attempts"
        condition: "event_type=authorization AND result=denied"
        threshold: 3
        window_seconds: 300
        severity: medium
      
      - name: "Configuration changes"
        condition: "event_type=configuration AND action=modify"
        threshold: 1
        window_seconds: 1
        severity: medium
```

UPDATE docker-compose.yml:
```yaml
services:
  unified-connector:
    # ... existing config ...
    environment:
      # ... existing env vars ...
      - SIEM_HOST=siem.company.com
      - SIEM_PORT=514
```

TESTING:
```python
# Test SIEM integration
import logging

# Trigger security event
logger = logging.getLogger(__name__)
logger.warning(
    "Failed login attempt",
    extra={
        'user': 'test@example.com',
        'action': 'login',
        'result': 'failure',
        'source_ip': '192.168.1.100',
        'event_type': 'authentication'
    }
)

# Check SIEM received event
```

Implement complete SIEM integration with buffering, alerting, and multiple SIEM type support.
```

---

## Task 2: Add Security Event Logging Throughout Application

### Prompt for AI Assistant

```
Add comprehensive security event logging to all security-relevant operations in the connector.

LOCATIONS TO ADD SECURITY LOGGING:

1. Authentication events (unified_connector/web/auth.py):
```python
# Successful login
logger.info(
    f"User {user_email} authenticated successfully",
    extra={
        'user': user_email,
        'action': 'login',
        'result': 'success',
        'source_ip': request.remote,
        'event_type': 'authentication',
        'mfa_completed': mfa_status
    }
)

# Failed login
logger.warning(
    f"Failed login attempt for {username}",
    extra={
        'user': username,
        'action': 'login',
        'result': 'failure',
        'source_ip': request.remote,
        'event_type': 'authentication',
        'failure_reason': 'invalid_credentials'
    }
)

# Logout
logger.info(
    f"User {user_email} logged out",
    extra={
        'user': user_email,
        'action': 'logout',
        'result': 'success',
        'event_type': 'authentication'
    }
)
```

2. Authorization events (unified_connector/web/rbac.py):
```python
# Permission denied
logger.warning(
    f"Permission denied: {user.email} lacks {permission.value}",
    extra={
        'user': user.email,
        'action': 'access',
        'result': 'denied',
        'target': request.path,
        'required_permission': permission.value,
        'user_role': user.role.value,
        'event_type': 'authorization'
    }
)

# Permission granted for sensitive operation
logger.info(
    f"User {user.email} performed privileged operation",
    extra={
        'user': user.email,
        'action': 'privileged_operation',
        'result': 'success',
        'target': request.path,
        'permission': permission.value,
        'event_type': 'authorization'
    }
)
```

3. Configuration changes (unified_connector/web/web_server.py):
```python
# ZeroBus config modified
logger.info(
    f"ZeroBus configuration modified by {user.email}",
    extra={
        'user': user.email,
        'action': 'modify_config',
        'result': 'success',
        'target': 'zerobus_config',
        'event_type': 'configuration',
        'changes': json.dumps(changes)
    }
)

# Source added/modified/deleted
logger.info(
    f"Source {source_name} {action} by {user.email}",
    extra={
        'user': user.email,
        'action': action,  # 'add', 'modify', 'delete'
        'result': 'success',
        'target': source_name,
        'event_type': 'configuration'
    }
)
```

4. Network/connectivity events (unified_connector/zerobus/zerobus_client.py):
```python
# Connection failure
logger.error(
    f"Failed to connect to {self.workspace_host}",
    extra={
        'action': 'connect',
        'result': 'failure',
        'target': self.workspace_host,
        'event_type': 'network',
        'failure_reason': str(e)
    }
)

# Circuit breaker opened
logger.error(
    f"Circuit breaker opened - potential service disruption",
    extra={
        'action': 'circuit_breaker_open',
        'result': 'degraded_service',
        'target': self.workspace_host,
        'failure_count': self.failure_count,
        'event_type': 'availability'
    }
)
```

5. Credential access (unified_connector/core/credential_manager.py):
```python
# Credential accessed
logger.debug(
    f"Credential accessed: {key}",
    extra={
        'action': 'credential_access',
        'result': 'success',
        'target': key,
        'event_type': 'credential_access'
    }
)

# Credential updated
logger.info(
    f"Credential updated: {key}",
    extra={
        'action': 'credential_update',
        'result': 'success',
        'target': key,
        'event_type': 'credential_access'
    }
)

# Failed credential access
logger.warning(
    f"Failed to decrypt credential: {key}",
    extra={
        'action': 'credential_access',
        'result': 'failure',
        'target': key,
        'event_type': 'credential_access',
        'failure_reason': 'decryption_failed'
    }
)
```

6. Discovery/scanning events (unified_connector/discovery/discovery.py):
```python
# Network scan initiated
logger.info(
    f"Network discovery scan initiated: {network_range}",
    extra={
        'action': 'network_scan',
        'result': 'initiated',
        'target': network_range,
        'event_type': 'operational'
    }
)

# Suspicious connection attempt
logger.warning(
    f"Repeated connection failures to {endpoint}",
    extra={
        'action': 'connect',
        'result': 'repeated_failure',
        'target': endpoint,
        'failure_count': count,
        'event_type': 'network'
    }
)
```

VERIFICATION:
```bash
# Trigger various security events
# Check that they appear in SIEM
grep "event_type" unified_connector.log | jq .
```

Add comprehensive security logging to all security-relevant operations.
```

---

## Verification Checklist

After completing Sprint 1.3:

- [ ] SIEM handler implemented (syslog, HTTP, Splunk HEC)
- [ ] Security events formatted in CEF or JSON
- [ ] Event buffering when SIEM unavailable
- [ ] Alerting rules configured
- [ ] Security logging added to:
  - [ ] Authentication (login/logout/failures)
  - [ ] Authorization (permission checks)
  - [ ] Configuration changes
  - [ ] Network connectivity
  - [ ] Credential access
  - [ ] Discovery/scanning
- [ ] Test alerts trigger correctly
- [ ] Integration with corporate SIEM verified

---

## Success Criteria

✅ Sprint 1.3 Complete When:
1. SIEM integration working (events flowing)
2. All security events logged with proper structure
3. Alerting rules configured for critical events
4. 24-hour incident notification capability enabled
5. Buffer/failover works when SIEM unavailable
6. Documentation for incident response procedures
