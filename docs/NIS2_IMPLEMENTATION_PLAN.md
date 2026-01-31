# NIS2 Compliance Implementation Plan
## Unified OT Zerobus Connector - Full Compliance Roadmap

**Plan Version**: 1.0
**Created**: 2025-01-31
**Target Completion**: 2025-07-31 (6 months)
**Total Effort**: ~38-50 person-weeks
**Team Size**: 4-5 engineers + 1 security specialist

---

## Executive Summary

This implementation plan outlines the path to achieve **full NIS2 Directive compliance** for the Unified OT Zerobus Connector. The plan is structured in 4 phases over 6 months, addressing all identified gaps from critical security controls to documentation and certification.

**Current State**: 70% compliant (4/10 fully compliant, 5/10 partially compliant, 1/10 non-compliant)
**Target State**: 100% compliant (10/10 fully compliant)
**Investment**: ~$150,000-200,000 (assuming blended rate of $150/hour)

---

## Phase 1: Critical Security Controls (Weeks 1-6)

**Goal**: Address Priority 1 gaps that pose immediate compliance risks
**Effort**: 12-15 person-weeks
**Team**: 2-3 engineers + 1 security specialist

### Sprint 1.1: Web UI Authentication & Authorization (Weeks 1-3)

#### Epic 1.1.1: Implement OAuth2/SAML Authentication
**Owner**: Senior Backend Engineer
**Effort**: 2 weeks
**Priority**: CRITICAL

**Tasks**:
1. **Design authentication architecture** (2 days)
   - Choose authentication method (OAuth2 + SAML support recommended)
   - Design session management strategy
   - Define token storage approach
   - Document authentication flow

2. **Implement OAuth2 provider integration** (3 days)
   ```python
   # unified_connector/web/auth.py
   from aiohttp_security import setup as setup_security
   from aiohttp_session import setup as setup_session
   from aiohttp_session.cookie_storage import EncryptedCookieStorage
   from authlib.integrations.aiohttp_client import OAuth

   class AuthenticationManager:
       def __init__(self, config: Dict[str, Any]):
           self.oauth_enabled = config.get('oauth', {}).get('enabled', False)
           self.saml_enabled = config.get('saml', {}).get('enabled', False)

       async def setup_oauth(self, app):
           # Configure OAuth2 (Azure AD, Okta, etc.)
           oauth = OAuth()
           oauth.register(
               name='azure',
               client_id=os.getenv('OAUTH_CLIENT_ID'),
               client_secret=os.getenv('OAUTH_CLIENT_SECRET'),
               server_metadata_url='https://login.microsoftonline.com/.../v2.0/.well-known/openid-configuration',
               client_kwargs={'scope': 'openid email profile'}
           )
           app['oauth'] = oauth
   ```

3. **Add login/logout endpoints** (2 days)
   ```python
   # New routes
   web.get('/login', self.handle_login),
   web.get('/login/callback', self.handle_oauth_callback),
   web.post('/logout', self.handle_logout),
   web.get('/api/auth/status', self.get_auth_status),
   ```

4. **Implement authentication middleware** (2 days)
   ```python
   @web.middleware
   async def auth_middleware(request, handler):
       # Allow public endpoints
       if request.path in ['/login', '/login/callback', '/health']:
           return await handler(request)

       # Check session/token
       user = await authorized_userid(request)
       if not user:
           raise web.HTTPUnauthorized()

       request['user'] = user
       return await handler(request)
   ```

5. **Update Web UI for authentication** (2 days)
   - Add login page
   - Implement session management in JavaScript
   - Add logout button
   - Show current user in UI

6. **Testing and documentation** (1 day)

**Deliverables**:
- [ ] OAuth2 authentication working
- [ ] SAML support (optional, can be Phase 2)
- [ ] Login/logout flows tested
- [ ] Authentication documentation

**Dependencies**: None
**Risk**: Integration with corporate IdP may require IT coordination

---

#### Epic 1.1.2: Multi-Factor Authentication (MFA)
**Owner**: Senior Backend Engineer
**Effort**: 1 week
**Priority**: HIGH

**Tasks**:
1. **Choose MFA approach** (1 day)
   - Option A: Delegated MFA (IdP handles MFA) - **RECOMMENDED**
   - Option B: Built-in TOTP (authenticator apps)
   - Option C: Hardware tokens (Yubikey)

2. **Implement MFA enforcement** (2 days)
   ```python
   # config.yaml
   web_ui:
     authentication:
       enabled: true
       method: oauth2
       require_mfa: true  # Enforce MFA at IdP level
       mfa_exceptions: []  # No exceptions by default
   ```

3. **Add MFA status checking** (1 day)
   ```python
   async def check_mfa_status(user_token):
       # Verify token contains MFA claim
       claims = decode_jwt(user_token)
       if not claims.get('amr') or 'mfa' not in claims.get('amr'):
           raise web.HTTPForbidden(reason="MFA required")
   ```

4. **Testing and documentation** (1 day)

**Deliverables**:
- [ ] MFA enforced for all users
- [ ] MFA status visible in UI
- [ ] Fallback for emergency access documented

---

#### Epic 1.1.3: Role-Based Access Control (RBAC)
**Owner**: Backend Engineer
**Effort**: 1 week
**Priority**: HIGH

**Tasks**:
1. **Define roles and permissions** (1 day)
   ```yaml
   # config.yaml
   web_ui:
     rbac:
       enabled: true
       roles:
         admin:
           permissions: [read, write, configure, manage_users]
         operator:
           permissions: [read, write, start_stop_sources]
         viewer:
           permissions: [read]

       # Map IdP groups to roles
       role_mappings:
         "CN=OT-Admins,OU=Groups": admin
         "CN=OT-Operators,OU=Groups": operator
         "CN=OT-Viewers,OU=Groups": viewer
   ```

2. **Implement permission checking** (2 days)
   ```python
   from functools import wraps

   def require_permission(permission: str):
       def decorator(handler):
           @wraps(handler)
           async def wrapper(self, request):
               user = request['user']
               if not user.has_permission(permission):
                   raise web.HTTPForbidden(reason=f"Permission '{permission}' required")
               return await handler(self, request)
           return wrapper
       return decorator

   # Usage
   @require_permission('configure')
   async def update_zerobus_config(self, request):
       # Only admin/operator can configure
       ...
   ```

3. **Update all API endpoints with permissions** (2 days)
   - `/api/sources/*` → `write` permission
   - `/api/zerobus/config` → `configure` permission
   - `/api/discovery/scan` → `write` permission
   - `/api/metrics` → `read` permission

4. **Update UI to show/hide based on permissions** (1 day)
   ```javascript
   // app.js
   const userPermissions = await apiFetch('/api/auth/permissions');

   if (!userPermissions.includes('configure')) {
     // Hide "Save" buttons
     document.getElementById('btnSaveZerobus').style.display = 'none';
   }
   ```

5. **Testing and documentation** (1 day)

**Deliverables**:
- [ ] 3 roles defined (admin, operator, viewer)
- [ ] All API endpoints protected
- [ ] UI adapts to user role
- [ ] Audit log for privileged operations

---

### Sprint 1.2: Security Testing Framework (Weeks 4-5)

#### Epic 1.2.1: Automated Vulnerability Scanning
**Owner**: DevSecOps Engineer
**Effort**: 1 week
**Priority**: CRITICAL

**Tasks**:
1. **Set up dependency vulnerability scanning** (1 day)
   ```bash
   # .github/workflows/security-scan.yml
   name: Security Scanning

   on:
     push:
       branches: [main, develop]
     pull_request:
     schedule:
       - cron: '0 0 * * 1'  # Weekly on Monday

   jobs:
     dependency-scan:
       runs-on: ubuntu-latest
       steps:
         - uses: actions/checkout@v3
         - name: Set up Python
           uses: actions/setup-python@v4
           with:
             python-version: '3.12'

         - name: Install dependencies
           run: pip install pip-audit safety

         - name: Run pip-audit
           run: pip-audit --requirement requirements.txt --format json --output pip-audit-report.json

         - name: Run Safety check
           run: safety check --json --output safety-report.json

         - name: Upload reports
           uses: actions/upload-artifact@v3
           with:
             name: vulnerability-reports
             path: |
               pip-audit-report.json
               safety-report.json
   ```

2. **Add SAST (Static Application Security Testing)** (2 days)
   ```bash
   # Install Bandit for Python security linting
   pip install bandit semgrep

   # .github/workflows/security-scan.yml (continued)
   sast-scan:
     runs-on: ubuntu-latest
     steps:
       - name: Run Bandit
         run: bandit -r unified_connector/ -f json -o bandit-report.json

       - name: Run Semgrep
         run: |
           semgrep --config auto unified_connector/ \
             --json --output semgrep-report.json
   ```

3. **Configure security gates** (1 day)
   ```yaml
   # .bandit
   [bandit]
   exclude: /test,/venv
   tests: B201,B301,B302,B303,B304,B305,B306,B307,B308,B309,B310,B311

   # Fail build on HIGH severity
   severity_threshold: HIGH
   confidence_threshold: MEDIUM
   ```

4. **Add container scanning (if using Docker)** (1 day)
   ```bash
   # .github/workflows/security-scan.yml (continued)
   container-scan:
     runs-on: ubuntu-latest
     steps:
       - name: Build image
         run: docker build -t connector:latest .

       - name: Run Trivy scan
         uses: aquasecurity/trivy-action@master
         with:
           image-ref: 'connector:latest'
           format: 'sarif'
           output: 'trivy-results.sarif'

       - name: Upload to GitHub Security
         uses: github/codeql-action/upload-sarif@v2
         with:
           sarif_file: 'trivy-results.sarif'
   ```

5. **Documentation and runbooks** (1 day)

**Deliverables**:
- [ ] CI/CD pipeline with security scanning
- [ ] Automated weekly scans
- [ ] Security reports in GitHub Security tab
- [ ] Runbook for vulnerability remediation

---

#### Epic 1.2.2: Security Unit Tests
**Owner**: Backend Engineer
**Effort**: 3 days
**Priority**: MEDIUM

**Tasks**:
1. **Create security test suite** (2 days)
   ```python
   # tests/security/test_authentication.py
   import pytest
   from aiohttp.test_utils import TestClient

   @pytest.mark.asyncio
   async def test_unauthenticated_access_denied(app_client: TestClient):
       """Test that unauthenticated users cannot access API"""
       resp = await app_client.get('/api/sources')
       assert resp.status == 401

   @pytest.mark.asyncio
   async def test_unauthorized_role_denied(app_client_operator: TestClient):
       """Test that operators cannot access admin endpoints"""
       resp = await app_client_operator.post('/api/auth/manage-users')
       assert resp.status == 403

   @pytest.mark.asyncio
   async def test_credential_not_in_logs(app, caplog):
       """Test that secrets never appear in logs"""
       config_loader = ConfigLoader()
       config = config_loader.load()

       # Trigger some operations
       await app.startup()

       # Check logs don't contain secrets
       for record in caplog.records:
           assert 'client_secret' not in record.message
           assert 'password' not in record.message.lower()

   # tests/security/test_injection.py
   @pytest.mark.asyncio
   async def test_sql_injection_protection(app_client_admin: TestClient):
       """Test protection against SQL injection (if using SQL)"""
       malicious_input = "'; DROP TABLE sources; --"
       resp = await app_client_admin.post('/api/sources', json={
           'name': malicious_input,
           'protocol': 'opcua',
           'endpoint': 'opc.tcp://test:4840'
       })
       # Should sanitize input, not crash
       assert resp.status in [200, 400]  # Not 500

   @pytest.mark.asyncio
   async def test_command_injection_protection(app_client_admin: TestClient):
       """Test protection against command injection"""
       malicious_endpoint = "opc.tcp://test:4840; rm -rf /"
       resp = await app_client_admin.post('/api/discovery/test', json={
           'protocol': 'opcua',
           'endpoint': malicious_endpoint
       })
       # Should reject invalid endpoint format
       assert resp.status == 400

   # tests/security/test_encryption.py
   @pytest.mark.asyncio
   async def test_credentials_encrypted_at_rest():
       """Test that credentials are encrypted on disk"""
       from unified_connector.core.credential_manager import CredentialManager

       cred_manager = CredentialManager()
       cred_manager.update_credential('test.secret', 'supersecret123')

       # Read raw file
       cred_file = Path('~/.unified_connector/credentials.enc').expanduser()
       raw_content = cred_file.read_bytes()

       # Should NOT contain plaintext
       assert b'supersecret123' not in raw_content
   ```

2. **Add tests to CI/CD** (1 day)
   ```yaml
   # .github/workflows/test.yml
   test:
     runs-on: ubuntu-latest
     steps:
       - name: Run security tests
         run: |
           pytest tests/security/ -v --cov=unified_connector \
             --cov-report=html --cov-report=json

       - name: Check security test coverage
         run: |
           # Require 80%+ coverage for security tests
           python -c "
           import json
           with open('coverage.json') as f:
               cov = json.load(f)
               if cov['totals']['percent_covered'] < 80:
                   raise Exception('Security test coverage below 80%')
           "
   ```

**Deliverables**:
- [ ] 20+ security unit tests
- [ ] Tests run in CI/CD
- [ ] 80%+ coverage for security-critical code

---

### Sprint 1.3: Incident Response System (Week 6)

#### Epic 1.3.1: SIEM Integration
**Owner**: Security Engineer
**Effort**: 1 week
**Priority**: CRITICAL

**Tasks**:
1. **Design SIEM integration architecture** (1 day)
   - Choose SIEM solution (Splunk, ELK, Azure Sentinel, etc.)
   - Define event taxonomy (security events, operational events, audit events)
   - Design alerting rules

2. **Implement SIEM logging handler** (2 days)
   ```python
   # unified_connector/monitoring/siem_handler.py
   import logging
   import json
   from datetime import datetime
   from typing import Dict, Any

   class SIEMHandler(logging.Handler):
       """Send security events to SIEM via syslog/HTTP"""

       def __init__(self, siem_config: Dict[str, Any]):
           super().__init__()
           self.siem_type = siem_config.get('type', 'syslog')
           self.host = siem_config['host']
           self.port = siem_config['port']
           self.protocol = siem_config.get('protocol', 'tcp')

           if self.siem_type == 'syslog':
               self._setup_syslog()
           elif self.siem_type == 'http':
               self._setup_http()

       def emit(self, record: logging.LogRecord):
           """Send log record to SIEM"""
           # Only send security-relevant events
           if record.levelno < logging.WARNING:
               return

           event = self._format_event(record)
           self._send_to_siem(event)

       def _format_event(self, record: logging.LogRecord) -> Dict[str, Any]:
           """Format event in CEF (Common Event Format) or JSON"""
           return {
               'timestamp': datetime.utcnow().isoformat(),
               'severity': record.levelname,
               'source': 'unified-ot-connector',
               'event_type': self._classify_event(record),
               'message': record.getMessage(),
               'user': getattr(record, 'user', 'system'),
               'action': getattr(record, 'action', 'unknown'),
               'result': getattr(record, 'result', 'unknown'),
               'source_ip': getattr(record, 'source_ip', None),
               'target': getattr(record, 'target', None),
           }

       def _classify_event(self, record: logging.LogRecord) -> str:
           """Classify event type for SIEM"""
           msg = record.getMessage().lower()

           if 'authentication' in msg or 'login' in msg:
               return 'authentication'
           elif 'authorization' in msg or 'permission' in msg:
               return 'authorization'
           elif 'circuit breaker' in msg or 'failure' in msg:
               return 'availability'
           elif 'connection' in msg and 'failed' in msg:
               return 'network'
           elif 'credential' in msg or 'secret' in msg:
               return 'credential_access'
           else:
               return 'operational'
   ```

3. **Add security event logging** (2 days)
   ```python
   # Add to authentication handler
   logger.warning(
       "Failed login attempt",
       extra={
           'user': username,
           'action': 'login',
           'result': 'failure',
           'source_ip': request.remote,
           'event_type': 'authentication'
       }
   )

   # Add to authorization handler
   logger.warning(
       f"Unauthorized access attempt to {endpoint}",
       extra={
           'user': user.username,
           'action': 'access',
           'result': 'denied',
           'target': endpoint,
           'event_type': 'authorization'
       }
   )

   # Add to circuit breaker
   logger.error(
       "Circuit breaker opened - potential service disruption",
       extra={
           'action': 'circuit_breaker_open',
           'result': 'degraded_service',
           'failure_count': self.failure_count,
           'event_type': 'availability'
       }
   )
   ```

4. **Configure alerting rules** (1 day)
   ```yaml
   # config.yaml
   monitoring:
     siem:
       enabled: true
       type: syslog  # or 'http' for webhook
       host: siem.company.com
       port: 514
       protocol: tls

       # Alert on these events
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
   ```

5. **Testing and documentation** (1 day)

**Deliverables**:
- [ ] SIEM integration working
- [ ] Security events flowing to SIEM
- [ ] Alerting rules configured
- [ ] Incident response runbook

---

## Phase 2: Encryption & Secure Defaults (Weeks 7-10)

**Goal**: Implement encryption by default and secure configuration
**Effort**: 8-10 person-weeks
**Team**: 2 engineers + 1 security specialist

### Sprint 2.1: Default Encryption Configuration (Weeks 7-8)

#### Epic 2.1.1: OPC-UA Encryption by Default
**Owner**: OT Protocol Engineer
**Effort**: 1.5 weeks
**Priority**: HIGH

**Tasks**:
1. **Change default security mode** (1 day)
   ```yaml
   # config.yaml - Update defaults
   sources:
   - name: example-opcua
     protocol: opcua
     endpoint: opc.tcp://192.168.20.100:4840
     security_mode: SignAndEncrypt  # Changed from None
     security_policy: Basic256Sha256  # Recommended policy
     certificate_path: ${env:OPCUA_CERT_PATH}
     private_key_path: ${env:OPCUA_KEY_PATH}
     enabled: true
   ```

2. **Add certificate generation utility** (3 days)
   ```python
   # unified_connector/tools/generate_certificates.py
   from cryptography import x509
   from cryptography.x509.oid import NameOID, ExtensionOID
   from cryptography.hazmat.primitives import hashes, serialization
   from cryptography.hazmat.primitives.asymmetric import rsa
   from datetime import datetime, timedelta

   def generate_opcua_certificate(
       output_dir: Path,
       common_name: str = "Unified OT Connector",
       organization: str = "Your Company",
       validity_days: int = 365
   ):
       """Generate self-signed certificate for OPC-UA client"""

       # Generate private key
       private_key = rsa.generate_private_key(
           public_exponent=65537,
           key_size=2048
       )

       # Generate certificate
       subject = issuer = x509.Name([
           x509.NameAttribute(NameOID.COUNTRY_NAME, "US"),
           x509.NameAttribute(NameOID.ORGANIZATION_NAME, organization),
           x509.NameAttribute(NameOID.COMMON_NAME, common_name),
       ])

       cert = x509.CertificateBuilder().subject_name(
           subject
       ).issuer_name(
           issuer
       ).public_key(
           private_key.public_key()
       ).serial_number(
           x509.random_serial_number()
       ).not_valid_before(
           datetime.utcnow()
       ).not_valid_after(
           datetime.utcnow() + timedelta(days=validity_days)
       ).add_extension(
           x509.SubjectAlternativeName([
               x509.DNSName(common_name),
               x509.UniformResourceIdentifier(f"urn:{organization}:UnifiedConnector")
           ]),
           critical=False,
       ).add_extension(
           x509.BasicConstraints(ca=False, path_length=None),
           critical=True,
       ).add_extension(
           x509.KeyUsage(
               digital_signature=True,
               key_encipherment=True,
               content_commitment=False,
               data_encipherment=True,
               key_agreement=False,
               key_cert_sign=False,
               crl_sign=False,
               encipher_only=False,
               decipher_only=False
           ),
           critical=True,
       ).sign(private_key, hashes.SHA256())

       # Save certificate
       cert_path = output_dir / "opcua_client_cert.pem"
       with open(cert_path, "wb") as f:
           f.write(cert.public_bytes(serialization.Encoding.PEM))

       # Save private key
       key_path = output_dir / "opcua_client_key.pem"
       with open(key_path, "wb") as f:
           f.write(private_key.private_bytes(
               encoding=serialization.Encoding.PEM,
               format=serialization.PrivateFormat.PKCS8,
               encryption_algorithm=serialization.NoEncryption()
           ))

       logger.info(f"Generated OPC-UA certificate: {cert_path}")
       logger.info(f"Private key: {key_path}")
       logger.info(f"Valid until: {cert.not_valid_after}")

       return cert_path, key_path
   ```

3. **Add CLI command for certificate generation** (1 day)
   ```python
   # unified_connector/__main__.py
   @click.group()
   def cli():
       pass

   @cli.command()
   @click.option('--output-dir', default='~/.unified_connector/certs', help='Certificate output directory')
   @click.option('--common-name', default='Unified OT Connector', help='Certificate common name')
   @click.option('--validity-days', default=365, help='Certificate validity in days')
   def generate_certs(output_dir, common_name, validity_days):
       """Generate OPC-UA client certificates"""
       from unified_connector.tools.generate_certificates import generate_opcua_certificate

       output_path = Path(output_dir).expanduser()
       output_path.mkdir(parents=True, exist_ok=True)

       cert_path, key_path = generate_opcua_certificate(
           output_path, common_name, validity_days
       )

       click.echo(f"✓ Certificate generated: {cert_path}")
       click.echo(f"✓ Private key: {key_path}")
       click.echo(f"\nUpdate your config.yaml:")
       click.echo(f"  certificate_path: {cert_path}")
       click.echo(f"  private_key_path: {key_path}")
   ```

4. **Add certificate monitoring** (2 days)
   ```python
   # unified_connector/monitoring/certificate_monitor.py
   from cryptography import x509
   from cryptography.hazmat.backends import default_backend
   from datetime import datetime, timedelta

   class CertificateMonitor:
       """Monitor certificate expiration and validity"""

       def __init__(self, warning_days: int = 30):
           self.warning_days = warning_days

       def check_certificate(self, cert_path: Path) -> Dict[str, Any]:
           """Check certificate validity and expiration"""
           with open(cert_path, 'rb') as f:
               cert_data = f.read()

           cert = x509.load_pem_x509_certificate(cert_data, default_backend())

           now = datetime.utcnow()
           days_until_expiry = (cert.not_valid_after - now).days

           status = {
               'valid': now >= cert.not_valid_before and now <= cert.not_valid_after,
               'expires': cert.not_valid_after.isoformat(),
               'days_remaining': days_until_expiry,
               'subject': cert.subject.rfc4514_string(),
               'issuer': cert.issuer.rfc4514_string(),
           }

           if days_until_expiry < 0:
               logger.error(f"Certificate expired: {cert_path}")
               status['warning'] = 'expired'
           elif days_until_expiry < self.warning_days:
               logger.warning(f"Certificate expiring soon ({days_until_expiry} days): {cert_path}")
               status['warning'] = 'expiring_soon'

           return status
   ```

5. **Update documentation** (1 day)

**Deliverables**:
- [ ] OPC-UA defaults to SignAndEncrypt
- [ ] Certificate generation utility
- [ ] Certificate monitoring
- [ ] Migration guide for existing deployments

---

#### Epic 2.1.2: MQTT TLS Enforcement
**Owner**: Protocol Engineer
**Effort**: 3 days
**Priority**: MEDIUM

**Tasks**:
1. **Add TLS validation** (1 day)
   ```python
   # unified_connector/protocols/mqtt_client.py
   def validate_mqtt_endpoint(endpoint: str) -> None:
       """Validate MQTT endpoint and warn if not using TLS"""
       parsed = urlparse(endpoint)

       if parsed.scheme == 'mqtt' and parsed.port != 1883:
           logger.warning(
               f"MQTT endpoint using unencrypted connection: {endpoint}. "
               f"Consider using mqtts:// (TLS) for production."
           )
       elif parsed.scheme == 'mqtt' and parsed.port == 1883:
           logger.warning(
               f"⚠️  MQTT endpoint using unencrypted connection on default port. "
               f"Change to mqtts://{parsed.hostname}:8883 for encryption."
           )
   ```

2. **Add TLS configuration options** (1 day)
   ```yaml
   # config.yaml
   sources:
   - name: mqtt-broker-secure
     protocol: mqtt
     endpoint: mqtts://192.168.20.200:8883  # TLS enabled
     tls:
       enabled: true
       ca_cert: /etc/connector/certs/mqtt-ca.pem
       client_cert: /etc/connector/certs/mqtt-client.pem  # Optional
       client_key: /etc/connector/certs/mqtt-client.key   # Optional
       verify_hostname: true
       tls_version: TLSv1.2  # Minimum version
     enabled: true
   ```

3. **Documentation and testing** (1 day)

**Deliverables**:
- [ ] MQTT TLS support
- [ ] Warnings for unencrypted MQTT
- [ ] TLS configuration examples

---

### Sprint 2.2: Certificate Management Automation (Weeks 9-10)

#### Epic 2.2.1: Certificate Lifecycle Management
**Owner**: Infrastructure Engineer
**Effort**: 2 weeks
**Priority**: MEDIUM

**Tasks**:
1. **Design certificate renewal architecture** (2 days)
   - Automatic renewal strategy
   - Certificate rollover plan (gradual, not immediate)
   - Notification strategy

2. **Implement certificate renewal** (3 days)
   ```python
   # unified_connector/tools/certificate_renewal.py
   import asyncio
   from pathlib import Path
   from datetime import datetime, timedelta

   class CertificateRenewer:
       """Automatic certificate renewal"""

       def __init__(self, config: Dict[str, Any]):
           self.renewal_days = config.get('renewal_days', 30)
           self.check_interval_hours = config.get('check_interval_hours', 24)

       async def start(self):
           """Start certificate renewal monitoring"""
           while True:
               await self._check_and_renew()
               await asyncio.sleep(self.check_interval_hours * 3600)

       async def _check_and_renew(self):
           """Check certificates and renew if needed"""
           from unified_connector.monitoring.certificate_monitor import CertificateMonitor

           monitor = CertificateMonitor(warning_days=self.renewal_days)

           # Check all configured certificates
           sources = self.config.get('sources', [])
           for source in sources:
               if source.get('protocol') == 'opcua':
                   cert_path = source.get('certificate_path')
                   if cert_path:
                       status = monitor.check_certificate(Path(cert_path))

                       if status['days_remaining'] < self.renewal_days:
                           logger.info(f"Renewing certificate for {source['name']}")
                           await self._renew_certificate(source)

       async def _renew_certificate(self, source: Dict[str, Any]):
           """Renew a certificate"""
           # Generate new certificate
           output_dir = Path(source['certificate_path']).parent
           cert_path, key_path = generate_opcua_certificate(
               output_dir,
               common_name=source.get('name', 'Unified OT Connector'),
               validity_days=365
           )

           # Update configuration (requires restart)
           logger.info(f"New certificate generated: {cert_path}")
           logger.info("Connector restart required to use new certificate")

           # TODO: Implement hot-reload of certificates (advanced)
   ```

3. **Add Web UI certificate status** (2 days)
   - Show certificate expiry dates
   - Certificate health indicators
   - Renewal status

4. **Integrate with monitoring** (2 days)
   ```python
   # Add certificate metrics to Prometheus
   from prometheus_client import Gauge

   certificate_expiry_days = Gauge(
       'connector_certificate_expiry_days',
       'Days until certificate expiry',
       ['source_name', 'cert_type']
   )

   # Update in monitoring loop
   for source in sources:
       if source.get('protocol') == 'opcua':
           status = monitor.check_certificate(source['certificate_path'])
           certificate_expiry_days.labels(
               source_name=source['name'],
               cert_type='opcua'
           ).set(status['days_remaining'])
   ```

5. **Documentation and testing** (1 day)

**Deliverables**:
- [ ] Automatic certificate renewal
- [ ] Certificate status in Web UI
- [ ] Certificate expiry metrics
- [ ] Renewal runbook

---

## Phase 3: Supply Chain & Documentation (Weeks 11-16)

**Goal**: SBOM generation, security documentation, training materials
**Effort**: 10-12 person-weeks
**Team**: 2 engineers + 1 technical writer

### Sprint 3.1: Software Bill of Materials (SBOM) (Weeks 11-12)

#### Epic 3.1.1: SBOM Generation & Management
**Owner**: DevSecOps Engineer
**Effort**: 1 week
**Priority**: MEDIUM

**Tasks**:
1. **Choose SBOM format** (1 day)
   - SPDX (recommended by NTIA)
   - CycloneDX (widely adopted)
   - **Decision: Use CycloneDX for Python ecosystem support**

2. **Implement SBOM generation** (2 days)
   ```bash
   # Install CycloneDX tool
   pip install cyclonedx-bom

   # Generate SBOM
   cyclonedx-py \
     --format json \
     --output sbom.json \
     --requirements requirements.txt

   # Validate SBOM
   cyclonedx validate --input-file sbom.json
   ```

3. **Automate SBOM in CI/CD** (1 day)
   ```yaml
   # .github/workflows/sbom.yml
   name: Generate SBOM

   on:
     release:
       types: [published]
     push:
       branches: [main]

   jobs:
     sbom:
       runs-on: ubuntu-latest
       steps:
         - uses: actions/checkout@v3

         - name: Set up Python
           uses: actions/setup-python@v4
           with:
             python-version: '3.12'

         - name: Install dependencies
           run: pip install cyclonedx-bom

         - name: Generate SBOM
           run: |
             cyclonedx-py \
               --format json \
               --output sbom.json \
               --requirements requirements.txt

         - name: Sign SBOM (optional)
           run: |
             # Use cosign or GPG to sign SBOM
             gpg --armor --detach-sign sbom.json

         - name: Upload SBOM to release
           if: github.event_name == 'release'
           uses: actions/upload-release-asset@v1
           env:
             GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
           with:
             upload_url: ${{ github.event.release.upload_url }}
             asset_path: ./sbom.json
             asset_name: sbom.json
             asset_content_type: application/json

         - name: Publish SBOM to artifact
           uses: actions/upload-artifact@v3
           with:
             name: sbom
             path: sbom.json
   ```

4. **Add SBOM to documentation** (1 day)
   ```markdown
   # docs/SUPPLY_CHAIN_SECURITY.md

   ## Software Bill of Materials (SBOM)

   We provide a complete SBOM for supply chain transparency.

   ### Download SBOM
   - Latest SBOM: [sbom.json](https://github.com/yourorg/connector/releases/latest/download/sbom.json)
   - Format: CycloneDX 1.5
   - Updated: With every release

   ### Verify SBOM
   ```bash
   # Download and verify signature
   wget https://github.com/yourorg/connector/releases/latest/download/sbom.json
   wget https://github.com/yourorg/connector/releases/latest/download/sbom.json.asc
   gpg --verify sbom.json.asc sbom.json
   ```

   ### Vulnerability Scanning
   You can scan our SBOM for known vulnerabilities:
   ```bash
   # Using Grype
   grype sbom:sbom.json

   # Using Dependency-Track
   # Upload sbom.json to your Dependency-Track instance
   ```
   ```

5. **Document dependency update policy** (1 day)

**Deliverables**:
- [ ] SBOM generated for every release
- [ ] SBOM published in GitHub releases
- [ ] Supply chain security documentation
- [ ] Dependency update policy

---

#### Epic 3.1.2: Dependency Monitoring
**Owner**: DevSecOps Engineer
**Effort**: 1 week
**Priority**: MEDIUM

**Tasks**:
1. **Set up Dependabot** (1 day)
   ```yaml
   # .github/dependabot.yml
   version: 2
   updates:
     - package-ecosystem: "pip"
       directory: "/"
       schedule:
         interval: "weekly"
         day: "monday"
         time: "09:00"
       open-pull-requests-limit: 10

       # Group updates by type
       groups:
         security-updates:
           patterns:
             - "*"
           update-types:
             - "security"

         minor-updates:
           patterns:
             - "*"
           update-types:
             - "minor"
             - "patch"

       # Auto-approve security updates
       reviewers:
         - "security-team"
       assignees:
         - "devops-team"

       # Labels
       labels:
         - "dependencies"
         - "security"
   ```

2. **Configure automated dependency updates** (2 days)
   - Test dependency updates in staging
   - Auto-merge minor/patch updates (with tests passing)
   - Manual review for major updates

3. **Add dependency dashboard** (2 days)
   - Web UI showing dependency status
   - Outdated dependencies highlighted
   - Known vulnerabilities displayed

**Deliverables**:
- [ ] Dependabot configured
- [ ] Weekly dependency updates
- [ ] Dependency dashboard in Web UI

---

### Sprint 3.2: Security Documentation (Weeks 13-14)

#### Epic 3.2.1: Comprehensive Security Documentation
**Owner**: Technical Writer + Security Engineer
**Effort**: 2 weeks
**Priority**: HIGH

**Documents to Create**:

1. **SECURITY.md** (2 days)
   ```markdown
   # Security Policy

   ## Supported Versions
   | Version | Supported          |
   | ------- | ------------------ |
   | 1.x.x   | :white_check_mark: |
   | < 1.0   | :x:                |

   ## Reporting a Vulnerability
   **DO NOT** create public GitHub issues for security vulnerabilities.

   Email: security@yourcompany.com
   PGP Key: [Download](security-pgp-key.asc)

   We will respond within 48 hours.

   ## Security Measures
   - All credentials encrypted at rest (AES-256)
   - TLS 1.2+ for all cloud connections
   - OAuth2 authentication with MFA support
   - RBAC with 3 roles (admin, operator, viewer)
   - Comprehensive audit logging
   - Automated vulnerability scanning
   - Regular penetration testing

   ## Compliance
   - NIS2 Directive (EU) 2022/2555
   - ISA-95 / Purdue Model
   - ISO 27001 compatible
   - SOC 2 Type II (in progress)
   ```

2. **DEPLOYMENT_SECURITY.md** (3 days)
   - Secure deployment guide
   - Firewall rules
   - Network segmentation diagrams
   - Hardening checklist
   - Certificate management
   - Secrets management

3. **INCIDENT_RESPONSE.md** (2 days)
   - Incident classification
   - Response procedures
   - Escalation matrix
   - Forensics procedures
   - NIS2 notification procedures (24/72/30 day timeline)

4. **SECURITY_ARCHITECTURE.md** (2 days)
   - Threat model
   - Security controls matrix
   - Data flow diagrams
   - Trust boundaries
   - Attack surface analysis

5. **Update existing docs** (1 day)
   - README.md with security badges
   - NIS2_COMPLIANCE.md (update with new features)
   - PROXY_CONFIGURATION.md (security considerations)

**Deliverables**:
- [ ] 4 new security documents
- [ ] Updated existing documentation
- [ ] Security badges in README
- [ ] Threat model documented

---

### Sprint 3.3: Training Materials (Weeks 15-16)

#### Epic 3.3.1: Security Training Program
**Owner**: Technical Writer + Security Specialist
**Effort**: 2 weeks
**Priority**: MEDIUM

**Tasks**:
1. **Create operator training materials** (1 week)
   - Web UI walkthrough (video + written)
   - Common operations guide
   - Troubleshooting guide
   - Security best practices

2. **Create administrator training** (1 week)
   - Installation guide
   - Configuration guide
   - Certificate management
   - Incident response
   - RBAC administration
   - Security hardening

3. **Create security awareness materials** (3 days)
   - NIS2 compliance overview
   - OT security fundamentals
   - Purdue model explanation
   - Phishing awareness (for operators)

4. **Publish training portal** (2 days)
   - Create docs website (GitHub Pages or ReadTheDocs)
   - Organize by role (operator, admin, security)
   - Add search functionality
   - Track training completion (optional)

**Deliverables**:
- [ ] Operator training (30-min)
- [ ] Administrator training (2-hour)
- [ ] Security awareness (15-min)
- [ ] Training portal online

---

## Phase 4: Testing, Audit & Certification (Weeks 17-24)

**Goal**: External security assessment and NIS2 certification
**Effort**: 8-10 person-weeks internal + external consultants
**Team**: Full team + external auditors

### Sprint 4.1: Security Assessment (Weeks 17-20)

#### Epic 4.1.1: Penetration Testing
**Owner**: External Security Firm
**Effort**: 2 weeks
**Priority**: CRITICAL

**Scope**:
1. **External penetration testing** (1 week)
   - Web UI vulnerabilities
   - API security
   - Authentication bypass attempts
   - Session management
   - Input validation

2. **Internal/OT-focused testing** (1 week)
   - OPC-UA client security
   - MQTT client security
   - Certificate validation
   - Encryption verification
   - Man-in-the-middle resistance

**Deliverables**:
- [ ] Penetration test report
- [ ] Vulnerability findings (with CVSS scores)
- [ ] Remediation recommendations
- [ ] Re-test after fixes

---

#### Epic 4.1.2: Code Security Review
**Owner**: External Security Firm or Internal Security Team
**Effort**: 1 week
**Priority**: HIGH

**Scope**:
- SAST/DAST results review
- Manual code review of critical paths
- Dependency vulnerability assessment
- Secrets management review
- Logging and monitoring review

**Deliverables**:
- [ ] Code security review report
- [ ] Prioritized fix list
- [ ] Best practices recommendations

---

### Sprint 4.2: Gap Remediation (Weeks 21-22)

#### Epic 4.2.1: Fix Penetration Test Findings
**Owner**: Full Engineering Team
**Effort**: 2 weeks
**Priority**: CRITICAL

**Tasks**:
1. Triage findings by severity
2. Fix critical/high vulnerabilities (Week 21)
3. Fix medium vulnerabilities (Week 22)
4. Re-test with security firm
5. Document remediation

**Deliverables**:
- [ ] All critical/high findings fixed
- [ ] 80%+ medium findings fixed
- [ ] Re-test passed
- [ ] Remediation report

---

### Sprint 4.3: NIS2 Audit & Certification (Weeks 23-24)

#### Epic 4.3.1: Internal Audit
**Owner**: Internal Audit Team
**Effort**: 1 week
**Priority**: HIGH

**Checklist**:
```markdown
# NIS2 Compliance Audit Checklist

## Article 21.2(a) - Risk Analysis & Security Policies
- [ ] Purdue Layer 3.5 architecture documented
- [ ] Read-only OT access verified
- [ ] Security policies documented
- [ ] Encrypted credential storage verified
- [ ] Network discovery security reviewed

## Article 21.2(b) - Incident Handling
- [ ] SIEM integration tested
- [ ] Security events flowing to SIEM
- [ ] Alerting rules configured
- [ ] Incident response procedures documented
- [ ] 24-hour notification process defined

## Article 21.2(c) - Business Continuity
- [ ] Disk spooling tested (simulate outage)
- [ ] Circuit breaker tested
- [ ] Retry logic verified
- [ ] Backpressure management tested
- [ ] Recovery time measured

## Article 21.2(d) - Supply Chain Security
- [ ] SBOM generated and published
- [ ] Dependency update process verified
- [ ] Official SDKs used
- [ ] No third-party data storage confirmed
- [ ] Supplier attestations collected

## Article 21.2(e) - Network Security & Segmentation
- [ ] Proxy configuration tested
- [ ] NO_PROXY validation verified
- [ ] Network segmentation documented
- [ ] Firewall rules defined
- [ ] Unidirectional data flow verified

## Article 21.2(f) - Encryption & Cryptography
- [ ] TLS 1.2+ for cloud connections
- [ ] OAuth2 authentication tested
- [ ] OPC-UA SignAndEncrypt default verified
- [ ] MQTT TLS configuration tested
- [ ] Certificate management documented

## Article 21.2(g) - Access Control & MFA
- [ ] Web UI authentication enabled
- [ ] MFA enforced
- [ ] RBAC roles tested (admin, operator, viewer)
- [ ] Permission checks verified
- [ ] Audit logging tested

## Article 21.2(h) - Security Monitoring
- [ ] Comprehensive logging verified
- [ ] Metrics collection tested
- [ ] Health monitoring operational
- [ ] Prometheus integration tested
- [ ] SIEM events verified

## Article 21.2(i) - Testing & Vulnerability Management
- [ ] Automated security scanning enabled
- [ ] Security unit tests passing (80%+ coverage)
- [ ] Penetration test completed
- [ ] Vulnerability remediation documented
- [ ] Testing schedule defined

## Article 21.2(j) - Training & Awareness
- [ ] Security documentation complete
- [ ] Operator training available
- [ ] Administrator training available
- [ ] Security awareness materials published
- [ ] Training completion tracked
```

**Deliverables**:
- [ ] Internal audit report
- [ ] Compliance evidence package
- [ ] Gap analysis (should be 0 gaps)

---

#### Epic 4.3.2: External Certification (Optional but Recommended)
**Owner**: External Auditor (ISO 27001 or equivalent)
**Effort**: 1 week
**Priority**: MEDIUM

**Certifications to Pursue**:
1. **ISO 27001** (Information Security Management)
   - Most recognized globally
   - Demonstrates systematic approach to security
   - Covers most NIS2 requirements

2. **SOC 2 Type II** (Service Organization Control)
   - Focus on security, availability, confidentiality
   - Required by many enterprise customers
   - Annual audit required

3. **IEC 62443** (Industrial Automation Security)
   - Specific to OT/ICS environments
   - Demonstrates OT security expertise
   - Highly relevant for manufacturing sector

**Process**:
1. Choose certification(s)
2. Gap assessment with auditor
3. Remediate any gaps
4. On-site audit
5. Certification awarded
6. Maintain certification (annual audits)

**Deliverables**:
- [ ] Certification gap assessment
- [ ] Certification audit completed
- [ ] Certificate awarded
- [ ] Annual audit scheduled

---

## Project Timeline Summary

```
Month 1-2: Phase 1 - Critical Security Controls
├─ Week 1-3: Web UI Auth + MFA + RBAC
├─ Week 4-5: Security Testing Framework
└─ Week 6: SIEM Integration

Month 3: Phase 2 - Encryption & Secure Defaults
├─ Week 7-8: OPC-UA Encryption by Default
└─ Week 9-10: Certificate Management

Month 4-5: Phase 3 - Supply Chain & Documentation
├─ Week 11-12: SBOM Generation
├─ Week 13-14: Security Documentation
└─ Week 15-16: Training Materials

Month 6: Phase 4 - Testing, Audit & Certification
├─ Week 17-20: Penetration Testing + Code Review
├─ Week 21-22: Gap Remediation
└─ Week 23-24: NIS2 Audit + Certification
```

---

## Resource Requirements

### Team Composition

| Role | FTE | Duration | Estimated Cost |
|------|-----|----------|----------------|
| Senior Backend Engineer | 1.0 | 6 months | $90,000 |
| Backend Engineer | 1.0 | 6 months | $75,000 |
| DevSecOps Engineer | 0.75 | 6 months | $70,000 |
| OT/Protocol Engineer | 0.5 | 2 months | $25,000 |
| Security Specialist | 0.5 | 6 months | $50,000 |
| Technical Writer | 0.5 | 2 months | $15,000 |
| Project Manager | 0.25 | 6 months | $30,000 |

**Internal Labor**: ~$355,000

### External Costs

| Item | Cost | Notes |
|------|------|-------|
| Penetration Testing | $25,000-40,000 | 2 weeks, comprehensive |
| Code Security Review | $15,000-25,000 | 1 week |
| ISO 27001 Certification | $30,000-50,000 | Initial + annual |
| SOC 2 Type II Audit | $25,000-40,000 | Annual audit |
| IEC 62443 Certification | $20,000-35,000 | Optional |
| SIEM Software License | $10,000-20,000 | Annual, if not existing |
| Security Tools (Bandit, etc.) | $0 | Open source |

**External Costs**: ~$125,000-210,000 (conservative: $150,000)

**Total Project Cost**: **$505,000** (labor + external)

---

## Risk Management

### High-Risk Items

1. **Authentication Implementation Complexity**
   - **Risk**: IdP integration may require extensive IT coordination
   - **Mitigation**: Start IdP discussions early (Week 0), have fallback to basic auth
   - **Impact**: 2-4 week delay
   - **Probability**: Medium (40%)

2. **Penetration Test Findings**
   - **Risk**: Critical vulnerabilities discovered late in project
   - **Mitigation**: Continuous security scanning throughout project
   - **Impact**: 2-4 week delay for remediation
   - **Probability**: Medium (30%)

3. **SIEM Integration**
   - **Risk**: Corporate SIEM may not support required integrations
   - **Mitigation**: Assess SIEM capabilities in Week 1, consider alternatives
   - **Impact**: 1-2 week delay
   - **Probability**: Low (20%)

4. **Certificate Management Complexity**
   - **Risk**: OPC-UA certificate requirements vary by vendor
   - **Mitigation**: Document vendor-specific requirements, provide flexible config
   - **Impact**: Additional support burden
   - **Probability**: High (60%)

### Medium-Risk Items

1. **Training Material Quality**
   - **Risk**: Training materials may require multiple revisions
   - **Mitigation**: User testing with operators/admins
   - **Impact**: 1-2 week delay
   - **Probability**: Medium (30%)

2. **Performance Impact**
   - **Risk**: Authentication/encryption may impact performance
   - **Mitigation**: Load testing throughout implementation
   - **Impact**: Architecture changes required
   - **Probability**: Low (15%)

---

## Success Criteria

### Phase 1 Success Criteria
- [ ] Web UI requires authentication (no anonymous access)
- [ ] MFA enforced for all users
- [ ] 3 roles implemented with proper permission checks
- [ ] Security scanning runs in CI/CD
- [ ] 80%+ security test coverage
- [ ] SIEM receiving security events

### Phase 2 Success Criteria
- [ ] OPC-UA defaults to SignAndEncrypt
- [ ] Certificate generation utility available
- [ ] Certificate expiry monitoring active
- [ ] MQTT TLS support documented
- [ ] All encryption warnings implemented

### Phase 3 Success Criteria
- [ ] SBOM generated for every release
- [ ] Dependabot configured and running
- [ ] 4 security documents published
- [ ] Training materials available (operator, admin, security)
- [ ] Training portal online

### Phase 4 Success Criteria
- [ ] Penetration test completed with no critical findings
- [ ] Code security review completed
- [ ] All high/critical vulnerabilities fixed
- [ ] Internal audit passed (10/10 NIS2 requirements)
- [ ] At least one external certification achieved (ISO 27001 or SOC 2)

### Overall Success Criteria
- [ ] **100% NIS2 compliant** (10/10 Article 21.2 requirements)
- [ ] Zero critical or high vulnerabilities
- [ ] <5 medium vulnerabilities (with remediation plan)
- [ ] External certification achieved
- [ ] Management sign-off obtained
- [ ] Deployment guide for customers published

---

## Maintenance & Continuous Compliance

### Ongoing Activities (Post-Implementation)

#### Weekly
- [ ] Dependency vulnerability scanning (automated)
- [ ] Security test suite execution (CI/CD)
- [ ] SIEM alert review

#### Monthly
- [ ] Certificate expiry review
- [ ] Security metrics review
- [ ] Incident response drill

#### Quarterly
- [ ] Vulnerability assessment
- [ ] Security documentation review
- [ ] Training material updates
- [ ] Management security report

#### Annually
- [ ] Penetration testing
- [ ] External audit (ISO 27001, SOC 2)
- [ ] NIS2 compliance review
- [ ] Certification renewal
- [ ] Security architecture review

---

## Appendix: Implementation Checklist

### Pre-Implementation (Week 0)
- [ ] Secure budget approval ($505k)
- [ ] Assemble team (7 resources)
- [ ] Set up project tracking (Jira, GitHub Projects)
- [ ] Schedule kickoff meeting
- [ ] Assess corporate IdP capabilities
- [ ] Assess corporate SIEM capabilities
- [ ] Review existing security policies
- [ ] Identify external vendors (pentesting, audit)

### Phase 1 Checklist (Weeks 1-6)
- [ ] Authentication PoC working (Week 1)
- [ ] MFA tested with test IdP (Week 3)
- [ ] RBAC roles defined and approved (Week 3)
- [ ] Security scanning pipeline live (Week 5)
- [ ] SIEM integration tested (Week 6)
- [ ] Phase 1 demo to stakeholders (Week 6)

### Phase 2 Checklist (Weeks 7-10)
- [ ] Certificate generation tested (Week 8)
- [ ] OPC-UA encryption tested with real server (Week 8)
- [ ] Certificate monitoring dashboard (Week 10)
- [ ] MQTT TLS tested (Week 9)
- [ ] Phase 2 demo to stakeholders (Week 10)

### Phase 3 Checklist (Weeks 11-16)
- [ ] SBOM generated for main branch (Week 12)
- [ ] All 4 security docs reviewed (Week 14)
- [ ] Training materials tested with users (Week 16)
- [ ] Training portal live (Week 16)
- [ ] Phase 3 demo to stakeholders (Week 16)

### Phase 4 Checklist (Weeks 17-24)
- [ ] Pentest kickoff meeting (Week 17)
- [ ] Pentest report received (Week 20)
- [ ] All critical findings fixed (Week 21)
- [ ] Re-test passed (Week 22)
- [ ] Internal audit passed (Week 23)
- [ ] External certification started (Week 23)
- [ ] Management final approval (Week 24)
- [ ] NIS2 compliance achieved 🎉 (Week 24)

---

## Conclusion

This implementation plan provides a clear, actionable roadmap to achieve **full NIS2 Directive compliance** for the Unified OT Zerobus Connector. The plan is ambitious but achievable within 6 months with proper resourcing and executive support.

**Key Success Factors**:
1. ✅ Strong executive sponsorship (€10M penalty is strong motivation)
2. ✅ Dedicated team (not part-time)
3. ✅ Early engagement with corporate IT (IdP, SIEM)
4. ✅ Continuous security testing (not just end-of-project)
5. ✅ External expertise (pentesting, audit) engaged early

**Next Steps**:
1. **Week 0**: Present this plan to management, secure approval
2. **Week 0**: Assemble team, assign roles
3. **Week 1**: Kickoff Phase 1, start authentication implementation
4. **Week 6**: Phase 1 checkpoint - reassess timeline if needed

**Questions/Approvals Needed**:
- [ ] Budget approval ($505k)
- [ ] Team allocation (4-5 engineers for 6 months)
- [ ] IdP selection (Azure AD, Okta, or other?)
- [ ] SIEM integration approach (Splunk, ELK, Sentinel?)
- [ ] Certification preferences (ISO 27001, SOC 2, IEC 62443?)
- [ ] Go/no-go decision on Phase 4 (certification)

---

**Document Owner**: Engineering Leadership
**Review Cycle**: Monthly
**Last Updated**: 2025-01-31
**Next Review**: 2025-02-28
