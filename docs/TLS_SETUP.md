# TLS/SSL Setup Guide

**NIS2 Compliance**: Article 21.2(h) - Encryption (data in transit)
**Version**: 1.0
**Last Updated**: 2025-01-31

This guide explains how to enable HTTPS for the Unified OT Zerobus Connector web UI using TLS/SSL certificates.

---

## Table of Contents

1. [Overview](#overview)
2. [Quick Start](#quick-start)
3. [Certificate Options](#certificate-options)
4. [Self-Signed Certificates (Development)](#self-signed-certificates-development)
5. [CA-Signed Certificates (Production)](#ca-signed-certificates-production)
6. [Configuration](#configuration)
7. [Verification](#verification)
8. [Troubleshooting](#troubleshooting)
9. [Security Best Practices](#security-best-practices)

---

## Overview

### Why HTTPS?

HTTPS (HTTP over TLS/SSL) is **mandatory** for NIS2 compliance Article 21.2(h):

> **Encryption**: Essential services operators must implement encryption to protect data in transit.

**Benefits**:
- ✅ Encrypted communication between browser and server
- ✅ Protection against man-in-the-middle (MITM) attacks
- ✅ Data integrity verification
- ✅ Authentication of server identity
- ✅ HTTP Strict Transport Security (HSTS) enforcement

### TLS Configuration Features

The Unified OT Connector supports:
- **Auto-generated self-signed certificates** (development)
- **Custom certificates from Certificate Authority** (production)
- **TLS 1.2 and TLS 1.3** (modern, secure protocols)
- **Strong cipher suites** (ECDHE, AES-GCM, ChaCha20)
- **HTTP Strict Transport Security (HSTS)**
- **Subject Alternative Names (SAN)** for multiple hostnames/IPs

---

## Quick Start

### 1. Generate Self-Signed Certificate

For development and testing:

```bash
# Generate certificate for localhost
python scripts/generate_tls_cert.py --generate

# Or with custom hostname
python scripts/generate_tls_cert.py --generate \
  --common-name unified-connector.example.com \
  --san localhost 127.0.0.1 192.168.1.100 unified-connector.example.com \
  --days 365
```

**Output**:
```
Certificate: /Users/username/.unified_connector/certs/server.crt
Private Key: /Users/username/.unified_connector/certs/server.key
Valid for: 365 days
```

### 2. Enable TLS in Configuration

Edit `unified_connector/config/config.yaml`:

```yaml
web_ui:
  tls:
    enabled: true  # Change from false to true
```

### 3. Update OAuth Redirect URI (if using authentication)

If authentication is enabled, update the redirect URI to use HTTPS:

```yaml
web_ui:
  authentication:
    oauth:
      redirect_uri: https://localhost:8082/login/callback  # Change http:// to https://
```

Or set environment variable:
```bash
export OAUTH_REDIRECT_URI=https://localhost:8082/login/callback
```

### 4. Restart the Connector

```bash
# Stop existing instance
# Ctrl+C or kill process

# Start with HTTPS enabled
python -m unified_connector.main
```

### 5. Access Web UI

Open browser to:
```
https://localhost:8082
```

**Expected**: Browser will show a security warning for self-signed certificate. This is normal for development.

**To proceed**:
- Chrome/Edge: Click "Advanced" → "Proceed to localhost (unsafe)"
- Firefox: Click "Advanced" → "Accept the Risk and Continue"
- Safari: Click "Show Details" → "visit this website"

---

## Certificate Options

### Option 1: Auto-Generated Self-Signed Certificate

**Best for**: Development, testing, internal networks

**Pros**:
- ✅ Quick setup (1 command)
- ✅ Free
- ✅ No external dependencies

**Cons**:
- ❌ Browser warnings
- ❌ Not trusted by default
- ❌ Manual trust required on each device

**How to use**:
```bash
python scripts/generate_tls_cert.py --generate
```

### Option 2: Custom Self-Signed Certificate

**Best for**: Development with specific requirements

**How to generate**:
```bash
python scripts/generate_tls_cert.py --generate \
  --common-name unified-connector.local \
  --san unified-connector.local 192.168.1.100 10.0.0.50 \
  --days 730 \
  --key-size 4096
```

### Option 3: CA-Signed Certificate

**Best for**: Production deployments

**Pros**:
- ✅ Trusted by browsers
- ✅ No security warnings
- ✅ Enterprise-ready

**Cons**:
- ⏱️  Requires Certificate Authority
- 💰 May have cost (Let's Encrypt is free)
- 🔄 Requires renewal

**Options**:
1. **Let's Encrypt** (free, automated)
2. **Enterprise CA** (internal certificate authority)
3. **Commercial CA** (DigiCert, Sectigo, etc.)

---

## Self-Signed Certificates (Development)

### Generate Certificate

```bash
python scripts/generate_tls_cert.py --generate \
  --common-name localhost \
  --san localhost 127.0.0.1 ::1 \
  --days 365
```

**Parameters**:
- `--common-name`: Main hostname (CN) - default: localhost
- `--san`: Subject Alternative Names (DNS names and IP addresses)
- `--days`: Validity period in days - default: 365
- `--organization`: Organization name - default: "Unified OT Connector"
- `--key-size`: RSA key size (2048, 3072, 4096) - default: 2048

### View Certificate Info

```bash
python scripts/generate_tls_cert.py --info
```

**Output**:
```
🔒 Certificate Information
============================================================
Common Name: localhost
Serial Number: 123456789
Valid From: 2025-01-31T00:00:00Z
Valid Until: 2026-01-31T00:00:00Z
Days Until Expiry: 365
✅ Status: VALID
Subject Alternative Names:
  - localhost
  - 127.0.0.1
  - ::1
============================================================
```

### Validate Certificate

```bash
python scripts/generate_tls_cert.py --validate
```

### Trust Self-Signed Certificate (Optional)

To avoid browser warnings, add certificate to system trust store:

**macOS**:
```bash
sudo security add-trusted-cert -d -r trustRoot -k /Library/Keychains/System.keychain \
  ~/.unified_connector/certs/server.crt
```

**Windows** (PowerShell as Administrator):
```powershell
Import-Certificate -FilePath "$env:USERPROFILE\.unified_connector\certs\server.crt" `
  -CertStoreLocation Cert:\LocalMachine\Root
```

**Linux** (Ubuntu/Debian):
```bash
sudo cp ~/.unified_connector/certs/server.crt /usr/local/share/ca-certificates/unified-connector.crt
sudo update-ca-certificates
```

---

## CA-Signed Certificates (Production)

### Option 1: Let's Encrypt (Free, Automated)

**Requirements**:
- Public domain name (e.g., unified-connector.example.com)
- Port 80 or 443 accessible from internet (for validation)

**Using Certbot**:

```bash
# Install Certbot
sudo apt install certbot  # Ubuntu/Debian
brew install certbot      # macOS

# Generate certificate
sudo certbot certonly --standalone -d unified-connector.example.com

# Certificates will be in: /etc/letsencrypt/live/unified-connector.example.com/
```

**Configure**:
```yaml
web_ui:
  tls:
    enabled: true
    cert_file: /etc/letsencrypt/live/unified-connector.example.com/fullchain.pem
    key_file: /etc/letsencrypt/live/unified-connector.example.com/privkey.pem
```

**Auto-renewal**:
```bash
# Test renewal
sudo certbot renew --dry-run

# Add to crontab for automatic renewal
sudo crontab -e
# Add line:
0 3 * * * certbot renew --quiet && systemctl restart unified-connector
```

### Option 2: Enterprise CA

**Request certificate from internal CA**:

1. Generate CSR (Certificate Signing Request):
```bash
openssl req -new -newkey rsa:2048 -nodes \
  -keyout server.key \
  -out server.csr \
  -subj "/C=AU/ST=NSW/L=Sydney/O=YourCompany/CN=unified-connector.local"
```

2. Submit CSR to your enterprise CA

3. Receive signed certificate (`server.crt`)

4. Configure:
```yaml
web_ui:
  tls:
    enabled: true
    cert_file: /path/to/server.crt
    key_file: /path/to/server.key
```

### Option 3: Commercial CA

**Purchase certificate from**:
- DigiCert
- Sectigo
- GlobalSign
- etc.

**Follow provider's instructions** to:
1. Generate CSR
2. Submit to CA
3. Complete domain validation
4. Download certificate
5. Install certificate

---

## Configuration

### Basic TLS Configuration

**config.yaml**:
```yaml
web_ui:
  enabled: true
  host: 0.0.0.0
  port: 8082

  # TLS/SSL Configuration (NIS2 Article 21.2(h))
  tls:
    enabled: true  # Enable HTTPS

    # Auto-generated certificate (leave empty for auto-generation)
    common_name: localhost
    san_list:
      - localhost
      - 127.0.0.1
      - ::1

    # Custom certificate paths (optional)
    cert_file: ""  # Leave empty for auto-generated
    key_file: ""   # Leave empty for auto-generated

    # HSTS (HTTP Strict Transport Security)
    hsts:
      max_age: 31536000       # 1 year in seconds
      include_subdomains: true
      preload: false          # Set true for HSTS preload list

    # Mutual TLS (client certificate authentication)
    require_client_cert: false
```

### Production Configuration

**For production with Let's Encrypt**:

```yaml
web_ui:
  tls:
    enabled: true
    cert_file: /etc/letsencrypt/live/unified-connector.example.com/fullchain.pem
    key_file: /etc/letsencrypt/live/unified-connector.example.com/privkey.pem
    hsts:
      max_age: 31536000
      include_subdomains: true
      preload: true  # Submit to HSTS preload list
```

### Development Configuration

**For development with auto-generated certificate**:

```yaml
web_ui:
  tls:
    enabled: true  # Will auto-generate certificate
    common_name: localhost
    san_list:
      - localhost
      - 127.0.0.1
      - ::1
      - 192.168.1.100  # Add your LAN IP if needed
```

---

## Verification

### 1. Check Certificate Generation

```bash
python scripts/generate_tls_cert.py --info
```

Expected output:
```
✅ Status: VALID
Days Until Expiry: 365
```

### 2. Test HTTPS Connection

**Using curl**:
```bash
# Self-signed (ignore certificate verification)
curl -k https://localhost:8082/api/health

# CA-signed (verify certificate)
curl https://unified-connector.example.com:8082/api/health
```

**Expected**:
```json
{"status": "healthy"}
```

### 3. Verify TLS Version and Ciphers

```bash
openssl s_client -connect localhost:8082 -tls1_2
openssl s_client -connect localhost:8082 -tls1_3
```

**Check for**:
- Protocol: `TLSv1.2` or `TLSv1.3`
- Cipher: `ECDHE-RSA-AES256-GCM-SHA384` or similar strong cipher

### 4. Test HSTS Header

```bash
curl -k -I https://localhost:8082 | grep -i strict-transport-security
```

**Expected**:
```
strict-transport-security: max-age=31536000; includeSubDomains
```

### 5. Browser Verification

1. Open developer tools (F12)
2. Go to "Security" tab (Chrome) or "Security" in Inspector (Firefox)
3. Click on "View certificate"

**Check**:
- Valid dates
- Subject Alternative Names include your hostname
- Key size is 2048+ bits

---

## Troubleshooting

### Certificate Not Found

**Error**:
```
TLSError: Certificate file not found: /path/to/server.crt
```

**Solution**:
```bash
# Generate certificate
python scripts/generate_tls_cert.py --generate

# Or verify path in config.yaml
```

### Invalid Certificate

**Error**:
```
TLSError: Failed to load certificate
```

**Solution**:
```bash
# Validate certificate
python scripts/generate_tls_cert.py --validate

# Check file permissions
ls -l ~/.unified_connector/certs/
# Should see: -rw------- (600) for key, -rw-r--r-- (644) for cert
```

### Certificate Expired

**Error**:
```
Certificate has expired
```

**Solution**:
```bash
# Check expiration
python scripts/generate_tls_cert.py --info

# Generate new certificate
python scripts/generate_tls_cert.py --generate --days 365
```

### Browser Shows Certificate Error

**Error**: "Your connection is not private" or "NET::ERR_CERT_AUTHORITY_INVALID"

**Cause**: Self-signed certificate not trusted

**Solutions**:

**Option 1**: Accept risk and proceed (development only)

**Option 2**: Trust certificate in system store (see [Trust Self-Signed Certificate](#trust-self-signed-certificate-optional))

**Option 3**: Use CA-signed certificate (production)

### HTTPS Not Working

**Check 1**: TLS enabled in config?
```bash
grep -A5 "tls:" unified_connector/config/config.yaml
```

**Check 2**: Certificate files exist?
```bash
ls -l ~/.unified_connector/certs/
```

**Check 3**: Port not blocked by firewall?
```bash
telnet localhost 8082
```

**Check 4**: Check logs for errors:
```bash
tail -f /var/log/unified-connector/unified_connector.log | grep -i tls
```

### HSTS Not Working

**Check**: HTTPS must be enabled for HSTS to activate

```bash
# Should return HSTS header
curl -k -I https://localhost:8082 | grep -i strict-transport-security
```

If empty, check:
1. TLS is enabled in config
2. SSL context is created (check logs)
3. Security headers middleware is active

---

## Security Best Practices

### Development

1. ✅ Use self-signed certificates (acceptable for development)
2. ✅ Restrict access to localhost or internal network
3. ✅ Use strong key sizes (2048+ bits)
4. ✅ Set short validity periods (90-365 days)

### Production

1. ✅ **Always use CA-signed certificates** (no self-signed)
2. ✅ Enable HSTS with long max-age (1 year minimum)
3. ✅ Use 2048-bit or 4096-bit RSA keys
4. ✅ Include all hostnames/IPs in Subject Alternative Names
5. ✅ Monitor certificate expiration (renew before 30 days)
6. ✅ Enable certificate transparency logging
7. ✅ Consider HSTS preload submission (for public services)
8. ✅ Implement certificate pinning (for high-security environments)
9. ✅ Rotate certificates annually (even if not expired)
10. ✅ Store private keys with 0600 permissions

### Certificate Management

**Automated Monitoring**:
```bash
# Add to cron for weekly certificate checks
0 2 * * 1 python /path/to/scripts/generate_tls_cert.py --validate || mail -s "Certificate Expiring" admin@example.com
```

**Key Security**:
```bash
# Verify private key permissions
ls -l ~/.unified_connector/certs/server.key
# Should be: -rw------- (600)

# If wrong, fix:
chmod 600 ~/.unified_connector/certs/server.key
```

---

## Advanced Topics

### Mutual TLS (mTLS)

Require client certificates for authentication:

**config.yaml**:
```yaml
web_ui:
  tls:
    enabled: true
    require_client_cert: true
```

**Generate client certificate**:
```bash
# Create CA
openssl req -new -x509 -days 3650 -keyout ca.key -out ca.crt

# Create client key
openssl genrsa -out client.key 2048

# Create client CSR
openssl req -new -key client.key -out client.csr

# Sign client certificate with CA
openssl x509 -req -in client.csr -CA ca.crt -CAkey ca.key -CAcreateserial -out client.crt -days 365
```

### Certificate Pinning

For high-security environments, pin server certificate:

```javascript
// In app.js
const expectedFingerprint = "AA:BB:CC:DD...";
// Verify certificate fingerprint on connection
```

### HSTS Preload

Submit domain to [HSTS Preload List](https://hstspreload.org/):

**Requirements**:
1. Valid HTTPS certificate
2. HTTPS on port 443
3. All subdomains use HTTPS
4. HSTS header with:
   - `max-age` >= 31536000 (1 year)
   - `includeSubDomains`
   - `preload`

**Configuration**:
```yaml
web_ui:
  port: 443  # Must use standard HTTPS port
  tls:
    enabled: true
    hsts:
      max_age: 63072000  # 2 years
      include_subdomains: true
      preload: true
```

---

## References

- **NIS2 Directive**: [EUR-Lex](https://eur-lex.europa.eu/eli/dir/2022/2555)
- **Mozilla SSL Configuration Generator**: [ssl-config.mozilla.org](https://ssl-config.mozilla.org/)
- **Let's Encrypt**: [letsencrypt.org](https://letsencrypt.org/)
- **HSTS Preload**: [hstspreload.org](https://hstspreload.org/)
- **OWASP TLS Cheat Sheet**: [cheatsheetseries.owasp.org](https://cheatsheetseries.owasp.org/cheatsheets/Transport_Layer_Security_Cheat_Sheet.html)

---

**Last Updated**: 2025-01-31
**NIS2 Compliance**: Phase 2, Sprint 2.1 - Data Encryption
**Status**: Production Ready
