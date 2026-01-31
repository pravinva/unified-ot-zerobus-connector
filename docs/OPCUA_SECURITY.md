# OPC-UA Security Configuration Guide

**NIS2 Compliance**: Article 21.2(h) - Encryption (data in transit)
**OPC UA Specification**: IEC 62541 Security
**Version**: 1.0
**Last Updated**: 2025-01-31

This guide explains how to configure secure OPC-UA connections using Sign and SignAndEncrypt modes.

---

## Table of Contents

1. [Overview](#overview)
2. [Quick Start](#quick-start)
3. [Security Modes](#security-modes)
4. [Certificate Generation](#certificate-generation)
5. [Server Configuration](#server-configuration)
6. [Client Configuration](#client-configuration)
7. [Authentication Methods](#authentication-methods)
8. [Troubleshooting](#troubleshooting)
9. [Security Best Practices](#security-best-practices)

---

## Overview

### Why OPC-UA Security?

OPC-UA (OPC Unified Architecture) supports multiple security modes to protect industrial data:

**NIS2 Requirement**: Article 21.2(h) mandates encryption for data in transit, especially for critical infrastructure.

**Threats Mitigated**:
- ✅ **Man-in-the-Middle (MITM)** attacks
- ✅ **Eavesdropping** on industrial data
- ✅ **Replay attacks**
- ✅ **Unauthorized access** to OT systems
- ✅ **Data tampering**

### Security Modes

| Mode | Description | Use Case | NIS2 Compliant |
|------|-------------|----------|----------------|
| **None** | No security | Development only | ❌ No |
| **Sign** | Message signing (integrity) | Legacy systems | ⚠️  Partial |
| **SignAndEncrypt** | Signing + encryption | Production | ✅ Yes |

**Recommendation**: Always use **SignAndEncrypt** for production deployments.

### Security Policies

| Policy | Algorithm | Key Size | Strength |
|--------|-----------|----------|----------|
| **NoSecurity** | None | N/A | None |
| **Basic256Sha256** | AES-256-CBC + SHA-256 | 2048-bit RSA | Strong |

**Recommendation**: Use **Basic256Sha256** (current OPC-UA standard).

---

## Quick Start

### 1. Generate Client Certificate

```bash
python scripts/generate_opcua_cert.py --generate
```

**Output**:
```
✅ Certificate: ~/.unified_connector/opcua_certs/client_cert.der
✅ Private Key: ~/.unified_connector/opcua_certs/client_key.pem
```

### 2. Export Server Certificate

From your OPC-UA server (e.g., using UAExpert or server admin panel):

1. Connect to server
2. Export server certificate
3. Save as `server_cert.der`

### 3. Trust Server Certificate

```bash
python scripts/generate_opcua_cert.py --trust-server server_cert.der
```

### 4. Configure Source

Edit `unified_connector/config/config.yaml`:

```yaml
sources:
  - name: secure-opcua-server
    protocol: opcua
    endpoint: opc.tcp://server:4840
    security:
      enabled: true
      security_policy: Basic256Sha256
      security_mode: SignAndEncrypt
      client_cert_path: ~/.unified_connector/opcua_certs/client_cert.der
      client_key_path: ~/.unified_connector/opcua_certs/client_key.pem
      server_cert_path: ~/.unified_connector/opcua_certs/trusted/server_cert.der
      trust_all_certificates: false
```

### 5. Start Connector

```bash
python -m unified_connector.main
```

**Verify**:
```
✓ Configured certificate-based security
✓ Trusting server certificate: server_cert.der
```

---

## Security Modes

### NoSecurity (Development Only)

**Configuration**:
```yaml
security:
  enabled: false  # Or omit security section entirely
```

**Use Case**: Development, testing, local networks
**NIS2 Compliant**: ❌ No

### Sign Mode

**Configuration**:
```yaml
security:
  enabled: true
  security_policy: Basic256Sha256
  security_mode: Sign
  client_cert_path: ~/.unified_connector/opcua_certs/client_cert.der
  client_key_path: ~/.unified_connector/opcua_certs/client_key.pem
```

**Features**:
- ✅ Message authentication (integrity)
- ✅ Prevents tampering
- ❌ No encryption (data visible)

**Use Case**: Legacy systems that don't support encryption
**NIS2 Compliant**: ⚠️  Partial (integrity only, no confidentiality)

### SignAndEncrypt Mode (Recommended)

**Configuration**:
```yaml
security:
  enabled: true
  security_policy: Basic256Sha256
  security_mode: SignAndEncrypt
  client_cert_path: ~/.unified_connector/opcua_certs/client_cert.der
  client_key_path: ~/.unified_connector/opcua_certs/client_key.pem
  server_cert_path: ~/.unified_connector/opcua_certs/trusted/server_cert.der
```

**Features**:
- ✅ Message authentication (integrity)
- ✅ Message encryption (confidentiality)
- ✅ Prevents tampering
- ✅ Prevents eavesdropping

**Use Case**: All production deployments
**NIS2 Compliant**: ✅ Yes (full compliance)

---

## Certificate Generation

### Client Certificate Generation

**Command**:
```bash
python scripts/generate_opcua_cert.py --generate \
  --app-uri "urn:company:unified-connector:client" \
  --common-name "Company OT Connector" \
  --organization "Company Name" \
  --days 730 \
  --key-size 2048
```

**Parameters**:
- `--app-uri`: Unique Application URI (must match server whitelist)
- `--common-name`: Certificate CN (e.g., "Unified OT Connector Client")
- `--organization`: Your organization name
- `--days`: Validity period (default: 365, max: 3650)
- `--key-size`: RSA key size (2048 or 4096)

**Output Files**:
- `client_cert.der`: Client certificate (DER format, required by OPC-UA)
- `client_key.pem`: Private key (PEM format)

### Certificate Requirements

**OPC-UA certificates must include**:
- ✅ X.509v3 format
- ✅ Subject Alternative Name (SAN) with Application URI
- ✅ Key Usage extensions
- ✅ DER encoding (for compatibility)

**Application URI**:
- Must be unique for each client
- Format: `urn:organization:application:instance`
- Example: `urn:company:unified-connector:client`
- Server may whitelist specific Application URIs

### View Certificate Information

```bash
python scripts/generate_opcua_cert.py --info
```

**Output**:
```
🔒 OPC-UA Certificate Information
============================================================
Common Name: Unified OT Connector Client
Organization: Unified OT Connector
Application URI: urn:unified-ot-connector:client
Valid From: 2025-01-31
Valid Until: 2026-01-31
Days Until Expiry: 365
✅ Status: VALID
```

---

## Server Configuration

### Server Certificate Export

**Method 1: Using UAExpert**:
1. Connect to OPC-UA server
2. Right-click connection → "Show Server Certificate"
3. "Export Certificate" → Save as `server_cert.der`

**Method 2: Using OpenSSL** (if server provides HTTPS endpoint):
```bash
openssl s_client -connect server:4840 -showcerts < /dev/null 2>/dev/null | \
  openssl x509 -outform DER -out server_cert.der
```

**Method 3: Server Admin Panel**:
- Access server web interface
- Navigate to Security / Certificates
- Download server certificate

### Trust Server Certificate

```bash
python scripts/generate_opcua_cert.py --trust-server server_cert.der
```

This copies the certificate to `~/.unified_connector/opcua_certs/trusted/` directory.

### List Trusted Certificates

```bash
python scripts/generate_opcua_cert.py --list-trusted
```

**Output**:
```
📋 Trusted Server Certificates (2)
============================================================
✅ OPC-UA Server
   File: OPC-UA_Server.der
   Expires: 2026-12-31 (365 days)

⚠️  Legacy Server
   File: Legacy_Server.der
   Expires: 2025-02-15 (15 days)
```

### Server-Side Client Trust

**On OPC-UA server**, you must also trust the client certificate:

1. Export client certificate: `~/.unified_connector/opcua_certs/client_cert.der`
2. Copy to server's trusted certificates directory
3. Restart server or reload certificates

**Common server locations**:
- Prosys: `C:\ProgramData\Prosys\trusted\certs\`
- UA Server: `/opt/opcua/trusted/`
- KEPServerEX: `C:\ProgramData\Kepware\KEPServerEX 6\trusted\`

---

## Client Configuration

### Basic Configuration

```yaml
sources:
  - name: my-opcua-server
    protocol: opcua
    endpoint: opc.tcp://192.168.1.100:4840
    security:
      enabled: true
      security_policy: Basic256Sha256
      security_mode: SignAndEncrypt
      client_cert_path: ~/.unified_connector/opcua_certs/client_cert.der
      client_key_path: ~/.unified_connector/opcua_certs/client_key.pem
      server_cert_path: ~/.unified_connector/opcua_certs/trusted/server_cert.der
```

### With Username/Password

```yaml
sources:
  - name: my-opcua-server
    protocol: opcua
    endpoint: opc.tcp://192.168.1.100:4840
    security:
      enabled: true
      security_policy: Basic256Sha256
      security_mode: SignAndEncrypt
      client_cert_path: ~/.unified_connector/opcua_certs/client_cert.der
      client_key_path: ~/.unified_connector/opcua_certs/client_key.pem
      server_cert_path: ~/.unified_connector/opcua_certs/trusted/server_cert.der
      # Username/password for additional authentication
      username: ${credential:opcua.username}
      password: ${credential:opcua.password}
```

### Development Mode (Trust All)

```yaml
security:
  enabled: true
  security_policy: Basic256Sha256
  security_mode: SignAndEncrypt
  client_cert_path: ~/.unified_connector/opcua_certs/client_cert.der
  client_key_path: ~/.unified_connector/opcua_certs/client_key.pem
  trust_all_certificates: true  # ⚠️  DEVELOPMENT ONLY
```

**Warning**: `trust_all_certificates: true` disables server certificate validation. **NEVER** use in production!

### Advanced Configuration

```yaml
security:
  enabled: true
  security_policy: Basic256Sha256
  security_mode: SignAndEncrypt
  client_cert_path: ~/.unified_connector/opcua_certs/client_cert.der
  client_key_path: ~/.unified_connector/opcua_certs/client_key.pem
  server_cert_path: ~/.unified_connector/opcua_certs/trusted/server_cert.der
  trust_all_certificates: false
  username: ${credential:opcua.username}
  password: ${credential:opcua.password}
  # Connection timeouts
  timeout: 10.0           # Connection timeout (seconds)
  session_timeout_ms: 120000  # Session timeout (milliseconds)
```

---

## Authentication Methods

OPC-UA supports multiple authentication methods that can be combined:

### 1. Anonymous (No Authentication)

**Configuration**:
```yaml
security:
  enabled: false
```

**Use Case**: Development only
**Security Level**: ❌ None

### 2. Certificate-Based (Recommended)

**Configuration**:
```yaml
security:
  enabled: true
  security_policy: Basic256Sha256
  security_mode: SignAndEncrypt
  client_cert_path: ~/.unified_connector/opcua_certs/client_cert.der
  client_key_path: ~/.unified_connector/opcua_certs/client_key.pem
```

**Use Case**: Production
**Security Level**: ✅ Strong

### 3. Username/Password

**Configuration**:
```yaml
security:
  enabled: true
  username: ${credential:opcua.username}
  password: ${credential:opcua.password}
```

**Use Case**: Additional authentication layer
**Security Level**: ⚠️  Medium (passwords can be brute-forced)

**Best Practice**: Store credentials in credential manager:

```bash
# Using credential manager CLI
python -m unified_connector.core.credential_manager set opcua.username "admin"
python -m unified_connector.core.credential_manager set opcua.password "secure-password"
```

### 4. Certificate + Username/Password (Most Secure)

**Configuration**:
```yaml
security:
  enabled: true
  security_policy: Basic256Sha256
  security_mode: SignAndEncrypt
  client_cert_path: ~/.unified_connector/opcua_certs/client_cert.der
  client_key_path: ~/.unified_connector/opcua_certs/client_key.pem
  server_cert_path: ~/.unified_connector/opcua_certs/trusted/server_cert.der
  username: ${credential:opcua.username}
  password: ${credential:opcua.password}
```

**Use Case**: High-security production environments
**Security Level**: ✅✅ Very Strong (2-factor authentication)

---

## Troubleshooting

### Error: "Certificate not trusted"

**Symptom**:
```
BadCertificateUntrusted: The certificate is not trusted
```

**Cause**: Server doesn't trust client certificate

**Solution**:
1. Export client certificate: `~/.unified_connector/opcua_certs/client_cert.der`
2. Import into server's trusted certificates
3. Restart server

### Error: "Application URI mismatch"

**Symptom**:
```
BadCertificateUriInvalid: The URI specified in the ApplicationDescription does not match the URI in the certificate
```

**Cause**: Application URI in certificate doesn't match configuration

**Solution**:
```bash
# Check current Application URI
python scripts/generate_opcua_cert.py --info

# Regenerate with correct URI
python scripts/generate_opcua_cert.py --generate \
  --app-uri "urn:correct:application:uri"
```

### Error: "Certificate expired"

**Symptom**:
```
BadCertificateTimeInvalid: Certificate has expired
```

**Solution**:
```bash
# Check expiration
python scripts/generate_opcua_cert.py --info

# Regenerate certificate
python scripts/generate_opcua_cert.py --generate --days 730
```

### Error: "Failed to load certificate"

**Symptom**:
```
Client certificate not found: /path/to/cert.der
```

**Check 1**: Certificate exists?
```bash
ls -l ~/.unified_connector/opcua_certs/
```

**Check 2**: Correct path in config?
```bash
grep -A10 "security:" config.yaml
```

**Check 3**: File permissions?
```bash
chmod 644 ~/.unified_connector/opcua_certs/client_cert.der
chmod 600 ~/.unified_connector/opcua_certs/client_key.pem
```

### Connection Timeout

**Symptom**:
```
TimeoutError: Connection timeout after 5.0 seconds
```

**Solution 1**: Increase timeout
```yaml
security:
  timeout: 15.0  # Increase from default 5.0
```

**Solution 2**: Check network connectivity
```bash
telnet server 4840
# Or
nc -zv server 4840
```

**Solution 3**: Check firewall rules
```bash
# On server, allow port 4840
sudo ufw allow 4840/tcp
```

### "Security policy not supported"

**Symptom**:
```
BadSecurityPolicyRejected: The security policy is not supported
```

**Cause**: Server doesn't support Basic256Sha256

**Solution**: Check server's supported security policies and update config:

```yaml
security:
  security_policy: Basic256  # Or whatever server supports
```

---

## Security Best Practices

### Development

1. ✅ Use self-signed certificates (acceptable)
2. ✅ `trust_all_certificates: true` OK for local testing
3. ✅ Use username/password for basic access control
4. ✅ Restrict network access (localhost or internal network)

### Production

1. ✅ **Always use SignAndEncrypt** mode
2. ✅ **Never use** `trust_all_certificates: true`
3. ✅ **Validate server certificates** explicitly
4. ✅ **Use strong Application URIs** (unique per client)
5. ✅ **Certificate rotation**: Renew before expiration
6. ✅ **Monitor certificate expiration** (30-day warning)
7. ✅ **Secure key storage**: Private keys with 0600 permissions
8. ✅ **Username/password**: Use credential manager, not plaintext
9. ✅ **Network segmentation**: OT network separate from IT
10. ✅ **Audit logging**: Enable security event logging

### Certificate Management

**Validity Period**:
- Development: 365 days OK
- Production: 730-1095 days (2-3 years)
- Max recommended: 3 years

**Key Size**:
- Minimum: 2048 bits
- Recommended: 2048 bits (good balance)
- High security: 4096 bits (slower performance)

**Rotation Schedule**:
```bash
# Check expiration monthly
0 0 1 * * python scripts/generate_opcua_cert.py --info

# Renew 30 days before expiration
# 1. Generate new certificate
python scripts/generate_opcua_cert.py --generate

# 2. Export to server
# 3. Update server trust
# 4. Test connection
# 5. Update production config
```

### Defense in Depth

Implement multiple security layers:

1. **Network Level**: Firewall, VLANs, network segmentation
2. **Transport Level**: OPC-UA SignAndEncrypt
3. **Authentication Level**: Certificates + username/password
4. **Authorization Level**: OPC-UA node-level permissions
5. **Application Level**: Input validation, rate limiting
6. **Monitoring Level**: SIEM integration, anomaly detection

---

## Advanced Topics

### Multiple Servers with Different Certificates

```yaml
sources:
  - name: server-a
    protocol: opcua
    endpoint: opc.tcp://server-a:4840
    security:
      client_cert_path: ~/.unified_connector/opcua_certs/client_cert.der
      client_key_path: ~/.unified_connector/opcua_certs/client_key.pem
      server_cert_path: ~/.unified_connector/opcua_certs/trusted/server_a.der

  - name: server-b
    protocol: opcua
    endpoint: opc.tcp://server-b:4840
    security:
      client_cert_path: ~/.unified_connector/opcua_certs/client_cert.der
      client_key_path: ~/.unified_connector/opcua_certs/client_key.pem
      server_cert_path: ~/.unified_connector/opcua_certs/trusted/server_b.der
```

### Certificate Pinning

For high-security environments, pin specific server certificates:

```python
# In unified_connector/protocols/opcua_client.py
# Validate server certificate fingerprint
expected_fingerprint = "AA:BB:CC:DD:EE:FF:..."
# Reject connection if fingerprint doesn't match
```

### Mutual TLS with Certificate Revocation

Implement CRL (Certificate Revocation List) checking:

1. Configure server to publish CRL
2. Download CRL periodically
3. Check certificates against CRL before connection

---

## References

- **IEC 62541**: OPC Unified Architecture Specification
- **OPC UA Security**: [opcfoundation.org/security](https://opcfoundation.org/security)
- **NIS2 Directive**: [EUR-Lex](https://eur-lex.europa.eu/eli/dir/2022/2555)
- **NIST SP 800-82**: Guide to Industrial Control Systems Security
- **asyncua Documentation**: [python-opcua.readthedocs.io](https://python-opcua.readthedocs.io/)

---

**Last Updated**: 2025-01-31
**NIS2 Compliance**: Phase 2, Sprint 2.1 - Protocol-Level Encryption
**Status**: Production Ready
