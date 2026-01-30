# NIS2 Implementation - Phases 2-4: Encryption, SBOM, Documentation, and Audit

## Phase 2: Encryption & Secure Defaults (Weeks 7-10)

### Task 1: Default OPC-UA Encryption and Certificate Generation

#### Prompt for AI Assistant

```
Change OPC-UA default security mode to SignAndEncrypt and add certificate generation utilities.

CURRENT STATE:
OPC-UA defaults to security_mode: None (unencrypted)

TARGET STATE:
- Default to SignAndEncrypt
- Automatic certificate generation
- Certificate expiry monitoring
- Easy certificate management via CLI

CREATE unified_connector/tools/generate_certificates.py:
```python
from cryptography import x509
from cryptography.x509.oid import NameOID, ExtensionOID
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from datetime import datetime, timedelta
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

def generate_opcua_certificate(
    output_dir: Path,
    common_name: str = "Unified OT Connector",
    organization: str = "Your Company",
    validity_days: int = 365,
    key_size: int = 2048
) -> tuple[Path, Path]:
    """
    Generate self-signed certificate for OPC-UA client
    
    Returns:
        tuple: (cert_path, key_path)
    """
    
    logger.info(f"Generating OPC-UA certificate: CN={common_name}, validity={validity_days} days")
    
    # Generate private key
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=key_size
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
    ).add_extension(
        x509.ExtendedKeyUsage([
            x509.oid.ExtendedKeyUsageOID.CLIENT_AUTH,
        ]),
        critical=True,
    ).sign(private_key, hashes.SHA256())
    
    # Save certificate
    output_dir.mkdir(parents=True, exist_ok=True)
    cert_path = output_dir / "opcua_client_cert.pem"
    with open(cert_path, "wb") as f:
        f.write(cert.public_bytes(serialization.Encoding.PEM))
    
    # Save private key (unencrypted for now - could add password protection)
    key_path = output_dir / "opcua_client_key.pem"
    with open(key_path, "wb") as f:
        f.write(private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        ))
    
    # Set restrictive permissions
    key_path.chmod(0o600)
    cert_path.chmod(0o644)
    
    logger.info(f"✓ Certificate generated: {cert_path}")
    logger.info(f"✓ Private key: {key_path}")
    logger.info(f"✓ Valid until: {cert.not_valid_after}")
    
    return cert_path, key_path
```

ADD CLI command (unified_connector/__main__.py):
```python
import click
from pathlib import Path
from unified_connector.tools.generate_certificates import generate_opcua_certificate

@click.group()
def cli():
    """Unified OT Connector CLI"""
    pass

@cli.command()
@click.option('--output-dir', default='~/.unified_connector/certs', help='Certificate output directory')
@click.option('--common-name', default='Unified OT Connector', help='Certificate common name')
@click.option('--organization', default='Your Company', help='Organization name')
@click.option('--validity-days', default=365, type=int, help='Certificate validity in days')
def generate_certs(output_dir, common_name, organization, validity_days):
    """Generate OPC-UA client certificates"""
    
    output_path = Path(output_dir).expanduser()
    
    try:
        cert_path, key_path = generate_opcua_certificate(
            output_path,
            common_name,
            organization,
            validity_days
        )
        
        click.echo(f"✓ Certificate generated: {cert_path}")
        click.echo(f"✓ Private key: {key_path}")
        click.echo(f"\nUpdate your config.yaml:")
        click.echo(f"  certificate_path: {cert_path}")
        click.echo(f"  private_key_path: {key_path}")
        
    except Exception as e:
        click.echo(f"❌ Error generating certificate: {e}", err=True)
        raise click.Abort()

if __name__ == '__main__':
    cli()
```

CREATE unified_connector/monitoring/certificate_monitor.py:
```python
from cryptography import x509
from cryptography.hazmat.backends import default_backend
from datetime import datetime, timedelta
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

class CertificateMonitor:
    """Monitor certificate expiration and validity"""
    
    def __init__(self, warning_days: int = 30):
        self.warning_days = warning_days
    
    def check_certificate(self, cert_path: Path) -> dict:
        """Check certificate validity and expiration"""
        
        if not cert_path.exists():
            return {
                'valid': False,
                'error': 'Certificate file not found'
            }
        
        try:
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
                'serial_number': cert.serial_number,
            }
            
            # Warnings
            if days_until_expiry < 0:
                logger.error(f"❌ Certificate expired: {cert_path}")
                status['warning'] = 'expired'
                status['valid'] = False
            elif days_until_expiry < self.warning_days:
                logger.warning(
                    f"⚠️  Certificate expiring soon ({days_until_expiry} days): {cert_path}"
                )
                status['warning'] = 'expiring_soon'
            
            return status
        
        except Exception as e:
            logger.error(f"Error checking certificate {cert_path}: {e}")
            return {
                'valid': False,
                'error': str(e)
            }
    
    def check_all_sources(self, config: dict) -> dict:
        """Check certificates for all OPC-UA sources"""
        results = {}
        
        for source in config.get('sources', []):
            if source.get('protocol') == 'opcua':
                cert_path = source.get('certificate_path')
                if cert_path:
                    source_name = source['name']
                    results[source_name] = self.check_certificate(Path(cert_path))
        
        return results
```

UPDATE config.yaml (change defaults):
```yaml
sources:
  # Example OPC-UA source with SECURE defaults
  - name: production-opcua
    protocol: opcua
    endpoint: opc.tcp://192.168.20.100:4840
    
    # ✅ SECURE DEFAULT: SignAndEncrypt (changed from None)
    security_mode: SignAndEncrypt
    security_policy: Basic256Sha256
    
    # Certificate paths (generate with: python -m unified_connector generate-certs)
    certificate_path: ~/.unified_connector/certs/opcua_client_cert.pem
    private_key_path: ~/.unified_connector/certs/opcua_client_key.pem
    
    enabled: true
```

ADD to web UI - show certificate status:
```javascript
// app.js - Add certificate status section
async function loadCertificateStatus() {
    const response = await apiFetch('/api/certificates/status');
    const data = await response.json();
    
    const container = document.getElementById('certificate-status');
    
    for (const [source, status] of Object.entries(data)) {
        const statusHtml = `
            <div class="certificate-status ${status.warning ? 'warning' : ''}">
                <h4>${source}</h4>
                <p>Valid: ${status.valid ? '✓' : '❌'}</p>
                <p>Expires: ${new Date(status.expires).toLocaleDateString()}</p>
                <p>Days remaining: ${status.days_remaining}</p>
                ${status.warning ? `<p class="warning">⚠️ ${status.warning}</p>` : ''}
            </div>
        `;
        container.innerHTML += statusHtml;
    }
}
```

ADD certificate status API endpoint:
```python
async def get_certificate_status(self, request):
    """Get certificate status for all sources"""
    from unified_connector.monitoring.certificate_monitor import CertificateMonitor
    
    monitor = CertificateMonitor()
    results = monitor.check_all_sources(self.config)
    
    return web.json_response(results)
```

USAGE:
```bash
# Generate certificates
python -m unified_connector generate-certs \
    --output-dir ~/.unified_connector/certs \
    --common-name "Manufacturing Plant A Connector" \
    --organization "ACME Manufacturing" \
    --validity-days 365

# Check certificate status
curl http://localhost:8082/api/certificates/status | jq

# Connector automatically checks certificates on startup
docker-compose up
```

TESTING:
1. Generate certificate
2. Configure source with SignAndEncrypt
3. Verify encrypted connection to OPC-UA server
4. Check certificate status in Web UI
5. Test with expired certificate (set validity to -1 days)

Implement OPC-UA encryption by default with certificate management.
```

---

## Phase 3: Supply Chain & Documentation (Weeks 11-16)

### Task 1: Generate Software Bill of Materials (SBOM)

#### Prompt for AI Assistant

```
Implement SBOM generation for supply chain transparency (NIS2 Article 21.2d).

REQUIREMENTS:
1. Generate SBOM in CycloneDX format
2. Automate SBOM generation in CI/CD
3. Publish SBOM with releases
4. Sign SBOM for integrity

CREATE .github/workflows/sbom.yml:
```yaml
name: Generate SBOM

on:
  release:
    types: [published]
  push:
    branches: [main, develop]
  workflow_dispatch:  # Manual trigger

jobs:
  generate-sbom:
    name: Generate Software Bill of Materials
    runs-on: ubuntu-latest
    
    steps:
      - name: Checkout code
        uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      
      - name: Install CycloneDX tool
        run: |
          pip install cyclonedx-bom
      
      - name: Generate SBOM
        run: |
          cyclonedx-py \
            --format json \
            --output sbom.json \
            --requirements requirements.txt
      
      - name: Validate SBOM
        run: |
          # Install CycloneDX CLI for validation
          wget https://github.com/CycloneDX/cyclonedx-cli/releases/latest/download/cyclonedx-linux-x64
          chmod +x cyclonedx-linux-x64
          ./cyclonedx-linux-x64 validate --input-file sbom.json
      
      - name: Sign SBOM (GPG)
        if: github.event_name == 'release'
        run: |
          # Import GPG key from secrets
          echo "${{ secrets.GPG_PRIVATE_KEY }}" | gpg --import --batch --yes
          
          # Sign SBOM
          gpg --armor --detach-sign sbom.json
      
      - name: Upload SBOM to release
        if: github.event_name == 'release'
        uses: softprops/action-gh-release@v1
        with:
          files: |
            sbom.json
            sbom.json.asc
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
      
      - name: Upload SBOM as artifact
        uses: actions/upload-artifact@v4
        with:
          name: sbom-${{ github.sha }}
          path: |
            sbom.json
            sbom.json.asc
      
      - name: Generate SBOM summary
        run: |
          echo "## Software Bill of Materials (SBOM)" >> $GITHUB_STEP_SUMMARY
          echo "" >> $GITHUB_STEP_SUMMARY
          echo "✓ SBOM generated successfully" >> $GITHUB_STEP_SUMMARY
          echo "" >> $GITHUB_STEP_SUMMARY
          
          # Count components
          component_count=$(jq '.components | length' sbom.json)
          echo "- **Components**: $component_count" >> $GITHUB_STEP_SUMMARY
          
          # List top-level dependencies
          echo "" >> $GITHUB_STEP_SUMMARY
          echo "### Top Dependencies" >> $GITHUB_STEP_SUMMARY
          jq -r '.components[] | select(.type == "library") | "- \(.name)@\(.version)"' sbom.json | head -10 >> $GITHUB_STEP_SUMMARY
```

CREATE docs/SUPPLY_CHAIN_SECURITY.md:
```markdown
# Supply Chain Security

## Software Bill of Materials (SBOM)

We provide a comprehensive SBOM for supply chain transparency and security.

### Download SBOM

- **Latest SBOM**: [sbom.json](https://github.com/yourorg/unified-connector/releases/latest/download/sbom.json)
- **SBOM Signature**: [sbom.json.asc](https://github.com/yourorg/unified-connector/releases/latest/download/sbom.json.asc)
- **Format**: CycloneDX 1.5 (JSON)
- **Updated**: With every release

### Verify SBOM

```bash
# Download SBOM and signature
wget https://github.com/yourorg/unified-connector/releases/latest/download/sbom.json
wget https://github.com/yourorg/unified-connector/releases/latest/download/sbom.json.asc

# Import our GPG public key
gpg --keyserver keyserver.ubuntu.com --recv-keys YOUR_KEY_ID

# Verify signature
gpg --verify sbom.json.asc sbom.json
```

### Scan for Vulnerabilities

You can scan our SBOM for known vulnerabilities:

```bash
# Using Grype
grype sbom:sbom.json

# Using Trivy
trivy sbom sbom.json

# Using Dependency-Track
# Upload sbom.json to your Dependency-Track instance
```

## Dependency Management

### Update Policy

- **Security updates**: Applied within 7 days
- **Minor updates**: Applied within 30 days
- **Major updates**: Evaluated quarterly
- **Automated scanning**: Weekly via Dependabot

### Official Dependencies

We use only official, trusted packages:

| Package | Source | Purpose |
|---------|--------|---------|
| databricks-zerobus-ingest-sdk | PyPI (Databricks) | ZeroBus ingestion |
| asyncua | PyPI (FreeOpcUa) | OPC-UA client |
| asyncio-mqtt | PyPI | MQTT client |
| pymodbus | PyPI | Modbus TCP client |
| aiohttp | PyPI | Web server |
| cryptography | PyPI | Encryption |

### Vulnerability Disclosure

If you discover a vulnerability in our dependencies:
1. Email security@yourcompany.com
2. Include SBOM component name and version
3. Include CVE ID if known
4. We will respond within 48 hours
```

TESTING:
```bash
# Generate SBOM locally
pip install cyclonedx-bom
cyclonedx-py --format json --output sbom.json --requirements requirements.txt

# Validate
cyclonedx validate --input-file sbom.json

# Scan for vulnerabilities
grype sbom:sbom.json
```

Implement SBOM generation and supply chain security documentation.
```

---

### Task 2: Create Comprehensive Security Documentation

#### Prompt for AI Assistant

```
Create comprehensive security documentation for NIS2 compliance.

CREATE docs/SECURITY.md:
```markdown
# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 1.x.x   | :white_check_mark: |
| < 1.0   | :x:                |

## Reporting a Vulnerability

**DO NOT** create public GitHub issues for security vulnerabilities.

### Contact
- **Email**: security@yourcompany.com
- **PGP Key**: [Download](docs/security-pgp-key.asc)
- **Response Time**: 48 hours

### What to Include
- Description of vulnerability
- Steps to reproduce
- Affected versions
- Potential impact

### Our Process
1. **Acknowledge** - Within 48 hours
2. **Assess** - Severity rating (using CVSS)
3. **Fix** - Patch development and testing
4. **Disclose** - Coordinated disclosure after patch

## Security Measures

### Authentication & Authorization
- OAuth2 with MFA support
- Role-Based Access Control (3 roles)
- Session management with encrypted cookies
- Audit logging for privileged operations

### Encryption
- TLS 1.2+ for all cloud connections
- OPC-UA SignAndEncrypt by default
- Encrypted credential storage (AES-256)
- Certificate management and monitoring

### Network Security
- Purdue Layer 3.5 (DMZ) deployment
- Network segmentation (OT/IT isolation)
- Proxy support for cloud connections
- Read-only OT access

### Monitoring
- Comprehensive security logging
- SIEM integration
- Real-time alerting
- Circuit breaker for availability

### Testing
- Automated vulnerability scanning
- SAST/DAST in CI/CD
- Security unit tests (80%+ coverage)
- Annual penetration testing

### Supply Chain
- SBOM generated for each release
- Dependency vulnerability monitoring
- Official packages only
- Automated security updates

## Compliance

- **NIS2 Directive** (EU) 2022/2555
- **ISA-95** / Purdue Model
- **ISO 27001** compatible
- **SOC 2 Type II** (in progress)

## Security Updates

Subscribe to security advisories:
- **GitHub**: Watch repository for security advisories
- **RSS**: https://github.com/yourorg/unified-connector/security/advisories
- **Email**: security-announce@yourcompany.com
```

CREATE docs/DEPLOYMENT_SECURITY.md:
```markdown
# Secure Deployment Guide

## Network Architecture

### Recommended Deployment (Purdue Model)

```
┌──────────────────────────────────────┐
│ Layer 4/5: Cloud / Enterprise       │
│ Databricks (SOC 2, ISO 27001)       │
└─────────────▲────────────────────────┘
              │ TLS 1.3 + OAuth2
              │ Via corporate proxy
┌─────────────┼────────────────────────┐
│ Layer 3.5: DMZ                       │
│ Unified Connector (this application) │
│ - Authentication enabled             │
│ - SIEM integrated                    │
│ - Encrypted credentials              │
└─────────────▲────────────────────────┘
              │ OPC-UA SignAndEncrypt
              │ Direct connection
┌─────────────┼────────────────────────┐
│ Layer 2/3: OT Network                │
│ - OPC-UA Servers                     │
│ - MQTT Brokers                       │
│ - Modbus Devices                     │
└──────────────────────────────────────┘
```

## Firewall Rules

### Inbound (to Connector)
```
# Web UI (restrict to admin network)
ALLOW tcp/8082 from 10.100.0.0/24 to connector  # Admin subnet only
DENY tcp/8082 from any to connector

# Health check (internal monitoring)
ALLOW tcp/8081 from monitoring_server to connector

# Prometheus metrics (internal monitoring)
ALLOW tcp/9090 from prometheus_server to connector
```

### Outbound (from Connector)
```
# OT device access (Layer 2/3)
ALLOW tcp/4840 from connector to 192.168.20.0/24  # OPC-UA
ALLOW tcp/1883 from connector to 192.168.20.0/24  # MQTT
ALLOW tcp/502 from connector to 192.168.20.0/24   # Modbus

# Cloud access via proxy
ALLOW tcp/8080 from connector to proxy_server      # Proxy
DENY tcp/443 from connector to any                 # Block direct internet

# DNS (for proxy resolution)
ALLOW udp/53 from connector to dns_server
```

### Proxy Rules (from Proxy to Internet)
```
# Databricks workspace
ALLOW tcp/443 to *.cloud.databricks.com

# SIEM
ALLOW tcp/514 to siem.company.com

# Block everything else
DENY tcp/443 to any
```

## Hardening Checklist

### Pre-Deployment
- [ ] Generate OPC-UA certificates
- [ ] Configure OAuth2 credentials
- [ ] Set strong master password
- [ ] Review firewall rules
- [ ] Configure SIEM integration
- [ ] Test proxy connectivity

### Connector Configuration
- [ ] Enable authentication
- [ ] Enforce MFA
- [ ] Configure RBAC roles
- [ ] Set OPC-UA to SignAndEncrypt
- [ ] Enable SIEM logging
- [ ] Configure certificate monitoring

### Operating System
- [ ] Apply latest security patches
- [ ] Disable unnecessary services
- [ ] Configure host firewall
- [ ] Enable SELinux/AppArmor
- [ ] Configure NTP
- [ ] Enable audit logging

### Docker (if using)
- [ ] Use official base images
- [ ] Scan images for vulnerabilities
- [ ] Run as non-root user
- [ ] Limit container resources
- [ ] Use Docker secrets
- [ ] Enable Docker Content Trust

## Certificate Management

### Generate Certificates
```bash
python -m unified_connector generate-certs \
    --output-dir /etc/connector/certs \
    --common-name "Plant A Connector" \
    --organization "ACME Manufacturing" \
    --validity-days 365
```

### Certificate Rotation
1. Generate new certificates 30 days before expiry
2. Update configuration with new cert paths
3. Restart connector
4. Verify encrypted connections work
5. Remove old certificates

### Trust OPC-UA Server Certificates
```bash
# Export server certificate
# Add to connector's trust store
cp server_cert.pem /etc/connector/certs/trusted/

# Update config
certificate_trust_list: /etc/connector/certs/trusted/
```

## Secrets Management

### Environment Variables (Recommended)
```bash
# .env file (never commit!)
OAUTH_CLIENT_ID=...
OAUTH_CLIENT_SECRET=...
SESSION_SECRET_KEY=...
CONNECTOR_MASTER_PASSWORD=...
```

### HashiCorp Vault (Enterprise)
```bash
# Store secrets in Vault
vault kv put secret/connector \
    oauth_client_id=$CLIENT_ID \
    oauth_client_secret=$CLIENT_SECRET

# Connector reads from Vault
export VAULT_ADDR=https://vault.company.com
export VAULT_TOKEN=...
```

### AWS Secrets Manager (Cloud)
```bash
# Store secrets in AWS
aws secretsmanager create-secret \
    --name connector/credentials \
    --secret-string file://secrets.json

# Connector reads from AWS
export AWS_REGION=us-west-2
```

## Monitoring

### Security Metrics
- Failed authentication attempts
- Permission denials
- Certificate expiry warnings
- Circuit breaker trips
- SIEM connection status

### Alerts
Configure alerts for:
- 5+ failed logins in 5 minutes
- Any privilege escalation attempt
- Certificate expiring in 30 days
- SIEM connection lost
- Repeated network failures

## Incident Response

### Detection
1. SIEM alerts trigger
2. Security team notified
3. Connector logs reviewed

### Containment
1. Disable compromised user accounts
2. Block suspicious IP addresses
3. Rotate credentials if needed
4. Isolate connector if necessary

### Recovery
1. Patch vulnerabilities
2. Restore from backup if needed
3. Review and update security controls
4. Document lessons learned

### NIS2 Notification
- **24 hours**: Early warning to authorities
- **72 hours**: Detailed incident report
- **1 month**: Final report with remediation

## Compliance Verification

### Weekly
- [ ] Review security logs
- [ ] Check certificate status
- [ ] Verify backup success

### Monthly
- [ ] Security metrics review
- [ ] Access control audit
- [ ] Vulnerability scan

### Quarterly
- [ ] Penetration testing
- [ ] Firewall rule review
- [ ] Disaster recovery test

### Annually
- [ ] External security audit
- [ ] NIS2 compliance review
- [ ] Certification renewal
```

CREATE these documents and ensure they're comprehensive and actionable.
```

---

## Phase 4: Testing, Audit & Certification (Weeks 17-24)

### Task: Final Security Assessment and NIS2 Audit

#### Prompt for AI Assistant

```
Prepare for external security assessment and NIS2 compliance audit.

CREATE docs/NIS2_AUDIT_CHECKLIST.md:
```markdown
# NIS2 Compliance Audit Checklist

## Article 21.2(a) - Risk Analysis & Security Policies

- [ ] **Purdue Layer 3.5 architecture documented**
  - Network diagrams showing OT/DMZ/IT separation
  - Data flow documentation
  - Firewall rules documented

- [ ] **Read-only OT access verified**
  - No write operations to OT devices
  - Unidirectional data flow tested
  - Evidence of read-only behavior

- [ ] **Security policies documented**
  - Access control policy
  - Encryption policy
  - Incident response policy
  - Acceptable use policy

- [ ] **Encrypted credential storage verified**
  - Credentials encrypted at rest (AES-256)
  - Master password protection
  - No plaintext secrets in configuration

- [ ] **Network discovery security reviewed**
  - Discovery scans logged
  - Rate limiting implemented
  - NO_PROXY configuration validated

---

## Article 21.2(b) - Incident Handling

- [ ] **SIEM integration tested**
  - Security events flowing to SIEM
  - CEF/JSON formatting validated
  - Buffering works during SIEM outage

- [ ] **Security events logged**
  - Authentication events
  - Authorization failures
  - Configuration changes
  - Network connectivity issues

- [ ] **Alerting rules configured**
  - Multiple failed logins alert
  - Circuit breaker alert
  - Unauthorized access alert
  - Certificate expiry alert

- [ ] **Incident response procedures documented**
  - Detection procedures
  - Containment procedures
  - Recovery procedures
  - 24/72 hour notification process

---

## Article 21.2(c) - Business Continuity

- [ ] **Disk spooling tested**
  - Simulate network outage
  - Verify data buffered to disk
  - Verify replay after recovery
  - Measure recovery time

- [ ] **Circuit breaker tested**
  - Trigger circuit breaker
  - Verify automatic recovery
  - Verify backoff logic
  - Measure failure detection time

- [ ] **Retry logic verified**
  - Test retry on transient failures
  - Verify exponential backoff
  - Verify max retry limit

- [ ] **Backup/restore tested**
  - Configuration backup
  - Credential backup
  - Restore from backup
  - Disaster recovery time measured

---

## Article 21.2(d) - Supply Chain Security

- [ ] **SBOM generated and published**
  - CycloneDX format
  - Signed with GPG
  - Published with each release
  - Verification instructions provided

- [ ] **Dependency update process verified**
  - Dependabot configured
  - Weekly vulnerability scans
  - Security updates applied within 7 days
  - Update policy documented

- [ ] **Official SDKs used**
  - databricks-zerobus-ingest-sdk verified
  - asyncua verified
  - No untrusted packages

- [ ] **No third-party data storage confirmed**
  - Data flows directly OT → Databricks
  - No intermediate storage
  - No third-party services

---

## Article 21.2(e) - Network Security & Segmentation

- [ ] **Proxy configuration tested**
  - Cloud traffic routes through proxy
  - OT traffic bypasses proxy
  - Proxy authentication works

- [ ] **NO_PROXY validation verified**
  - OT device ranges in NO_PROXY
  - Validation warnings logged
  - Misrouting prevented

- [ ] **Network segmentation documented**
  - Purdue model layers defined
  - Firewall rules documented
  - Network diagrams updated

- [ ] **Unidirectional data flow verified**
  - Data flows UP only (OT → Cloud)
  - No commands from IT to OT
  - Read-only operations confirmed

---

## Article 21.2(f) - Encryption & Cryptography

- [ ] **TLS 1.2+ for cloud connections**
  - ZeroBus uses TLS
  - OAuth uses TLS
  - Certificate validation enabled

- [ ] **OAuth2 authentication tested**
  - Token acquisition works
  - Token refresh works
  - Expired tokens rejected

- [ ] **OPC-UA SignAndEncrypt default verified**
  - Default security_mode is SignAndEncrypt
  - Certificates generated
  - Encrypted connections tested

- [ ] **MQTT TLS configuration tested**
  - mqtts:// connections work
  - Certificate validation works
  - Fallback to unencrypted logged

- [ ] **Certificate management documented**
  - Generation procedure
  - Rotation procedure
  - Expiry monitoring
  - Trust list management

---

## Article 21.2(g) - Access Control & MFA

- [ ] **Web UI authentication enabled**
  - OAuth2 working
  - Login/logout tested
  - Session persistence verified

- [ ] **MFA enforced**
  - MFA claim checked
  - Non-MFA users blocked
  - MFA status logged

- [ ] **RBAC roles tested**
  - Admin has full access
  - Operator has limited access
  - Viewer has read-only access
  - Role mapping from IdP groups works

- [ ] **Permission checks verified**
  - All API endpoints protected
  - Proper 401/403 responses
  - UI adapts to user role

- [ ] **Audit logging tested**
  - Privileged operations logged
  - User attribution correct
  - Logs sent to SIEM

---

## Article 21.2(h) - Security Monitoring & Logging

- [ ] **Comprehensive logging verified**
  - All operations logged
  - Timestamps accurate
  - Log levels appropriate

- [ ] **Metrics collection tested**
  - Prometheus metrics exported
  - Health check endpoint works
  - Status API returns correct data

- [ ] **Health monitoring operational**
  - /health endpoint responds
  - Circuit breaker state visible
  - Connection status accurate

- [ ] **SIEM events verified**
  - Security events reach SIEM
  - Event format correct (CEF/JSON)
  - Event classification accurate

---

## Article 21.2(i) - Testing & Vulnerability Management

- [ ] **Automated security scanning enabled**
  - GitHub Actions workflows running
  - Dependency scans weekly
  - SAST scans on every PR
  - Container scans on releases

- [ ] **Security unit tests passing**
  - Authentication tests pass
  - Authorization tests pass
  - Input validation tests pass
  - 80%+ coverage achieved

- [ ] **Penetration test completed**
  - External pentest performed
  - Findings documented
  - Critical/high issues fixed
  - Re-test passed

- [ ] **Vulnerability remediation documented**
  - Remediation procedures
  - SLA for fixes (7 days for critical)
  - Patch testing process

- [ ] **Testing schedule defined**
  - Weekly: Automated scans
  - Monthly: Vulnerability assessment
  - Quarterly: Internal audit
  - Annually: Penetration test

---

## Article 21.2(j) - Training & Awareness

- [ ] **Security documentation complete**
  - SECURITY.md
  - DEPLOYMENT_SECURITY.md
  - INCIDENT_RESPONSE.md
  - SUPPLY_CHAIN_SECURITY.md

- [ ] **Operator training available**
  - Web UI walkthrough
  - Common operations guide
  - Troubleshooting guide

- [ ] **Administrator training available**
  - Installation guide
  - Configuration guide
  - Certificate management
  - Incident response

- [ ] **Security awareness materials published**
  - NIS2 compliance overview
  - OT security fundamentals
  - Purdue model explanation

- [ ] **Training completion tracked**
  - Training attendance log
  - Competency assessment
  - Refresher training schedule

---

## Management Accountability (Article 20)

- [ ] **Top management approval documented**
  - Security policy approved
  - Risk assessment approved
  - Compliance sign-off

- [ ] **Regular reporting to board**
  - Quarterly security reports
  - Incident reports
  - Compliance status

- [ ] **Configuration audit trail**
  - All changes logged
  - Change approval process
  - Rollback capability

---

## External Certifications (Optional but Recommended)

- [ ] **ISO 27001 assessment**
  - Gap analysis completed
  - Gaps remediated
  - Audit scheduled

- [ ] **SOC 2 Type II assessment**
  - Control design documented
  - Operating effectiveness tested
  - Audit report received

- [ ] **IEC 62443 assessment**
  - OT security controls validated
  - Industrial automation security
  - Certification awarded

---

## Final Verification

- [ ] **All 10 NIS2 requirements met**
  - 10/10 fully compliant
  - Evidence documented
  - Management sign-off

- [ ] **Zero critical vulnerabilities**
  - Penetration test findings addressed
  - SAST/DAST scans clean
  - Dependency scans clean

- [ ] **Documentation complete**
  - All required documents created
  - Reviewed by legal/compliance
  - Published and accessible

- [ ] **Training delivered**
  - Operators trained
  - Administrators trained
  - Management briefed

- [ ] **Deployment guide published**
  - Step-by-step instructions
  - Hardening checklist
  - Troubleshooting guide

---

## Audit Evidence Package

Prepare the following for auditors:

1. **Architecture Documentation**
   - Network diagrams
   - Data flow diagrams
   - Deployment topology

2. **Security Policies**
   - Access control policy
   - Encryption policy
   - Incident response policy

3. **Technical Evidence**
   - Configuration files (redacted)
   - Log samples
   - SIEM integration test results
   - Certificate management procedures

4. **Test Results**
   - Penetration test report
   - Vulnerability scan results
   - Security unit test results
   - Code security review

5. **Training Materials**
   - Training slides
   - Attendance logs
   - Competency assessments

6. **Incident Response**
   - Incident response plan
   - Test incident walkthrough
   - 24/72 hour notification process

7. **Compliance Documentation**
   - This checklist (completed)
   - Gap analysis (before/after)
   - Management sign-offs
   - External audit reports

---

## Sign-Off

**Prepared by**: _________________________ Date: _________

**Reviewed by (Legal)**: _________________________ Date: _________

**Reviewed by (Security)**: _________________________ Date: _________

**Approved by (Management)**: _________________________ Date: _________

**External Auditor**: _________________________ Date: _________

---

## Next Steps

After audit completion:
1. Address any findings
2. Publish compliance statement
3. Schedule annual re-audit
4. Maintain continuous compliance
5. Update documentation as changes occur
```

CREATE this comprehensive audit checklist and evidence package template.
```

---

## Summary of All Phases

### Phase 1 Deliverables ✅
- Web UI authentication (OAuth2 + MFA)
- RBAC (admin/operator/viewer)
- Automated security scanning (CI/CD)
- Security unit tests (80%+ coverage)
- SIEM integration with alerting

### Phase 2 Deliverables ✅
- OPC-UA defaults to SignAndEncrypt
- Certificate generation utility
- Certificate monitoring
- MQTT TLS support

### Phase 3 Deliverables ✅
- SBOM generation (CycloneDX)
- Dependabot configured
- Security documentation:
  - SECURITY.md
  - DEPLOYMENT_SECURITY.md
  - SUPPLY_CHAIN_SECURITY.md
  - INCIDENT_RESPONSE.md
- Training materials

### Phase 4 Deliverables ✅
- Penetration testing
- Code security review
- NIS2 audit checklist
- Evidence package
- Management sign-off
- External certification

---

## Final Verification Command

```bash
#!/bin/bash
# verify-nis2-compliance.sh

echo "=== NIS2 Compliance Verification ==="

# 1. Authentication
echo "✓ Checking authentication..."
grep "authentication.enabled: true" config.yaml || echo "❌ Auth not enabled"

# 2. Security scanning
echo "✓ Checking security scans..."
ls -la .github/workflows/security-scan.yml || echo "❌ Security scan missing"

# 3. SBOM
echo "✓ Checking SBOM..."
ls -la sbom.json || echo "❌ SBOM not generated"

# 4. Documentation
echo "✓ Checking documentation..."
for doc in SECURITY.md DEPLOYMENT_SECURITY.md SUPPLY_CHAIN_SECURITY.md; do
    ls -la docs/$doc || echo "❌ $doc missing"
done

# 5. Certificates
echo "✓ Checking certificates..."
ls -la ~/.unified_connector/certs/ || echo "❌ Certificates not generated"

# 6. Tests
echo "✓ Running security tests..."
pytest tests/security/ -v --tb=short

echo ""
echo "=== Compliance Status ==="
echo "Review checklist: docs/NIS2_AUDIT_CHECKLIST.md"
```

Run this script to verify all NIS2 components are in place.
```

---

This completes Phases 2-4 of the NIS2 implementation!