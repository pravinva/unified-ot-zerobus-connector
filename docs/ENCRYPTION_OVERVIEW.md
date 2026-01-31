# Encryption and Security Overview

**NIS2 Compliance**: Article 21.2(h) - Encryption
**Version**: 1.0
**Last Updated**: 2025-01-31

This document provides a comprehensive overview of all encryption and security features in the Unified OT Zerobus Connector.

---

## Table of Contents

1. [Overview](#overview)
2. [NIS2 Compliance](#nis2-compliance)
3. [Encryption Features](#encryption-features)
4. [Quick Start](#quick-start)
5. [Component Overview](#component-overview)
6. [Security Architecture](#security-architecture)
7. [Best Practices](#best-practices)
8. [Documentation Index](#documentation-index)

---

## Overview

The Unified OT Zerobus Connector implements comprehensive encryption for **data at rest** and **data in transit** to meet NIS2 cybersecurity requirements.

### Encryption Coverage

| Component | Type | Status | Documentation |
|-----------|------|--------|---------------|
| **Credentials** | Data at rest | ✅ Implemented | Built-in |
| **Configuration Files** | Data at rest | ✅ Implemented | [CONFIG_ENCRYPTION.md](CONFIG_ENCRYPTION.md) |
| **Web UI (HTTPS)** | Data in transit | ✅ Implemented | [TLS_SETUP.md](TLS_SETUP.md) |
| **OPC-UA** | Data in transit | ✅ Implemented | [OPCUA_SECURITY.md](OPCUA_SECURITY.md) |
| **MQTT** | Data in transit | ✅ Implemented | [MQTT_SECURITY.md](MQTT_SECURITY.md) |
| **ZeroBus** | Data in transit | ✅ Native TLS | Databricks managed |

### Security Standards

- **Encryption Algorithm**: AES-256 (Fernet) for data at rest
- **Key Derivation**: PBKDF2 with SHA-256, 480,000 iterations
- **TLS/SSL**: TLS 1.2 minimum, TLS 1.3 preferred
- **Cipher Suites**: ECDHE, AESGCM, ChaCha20 (Mozilla Intermediate)
- **Certificate Standards**: X.509v3, 2048+ bit RSA keys

---

## NIS2 Compliance

### Article 21.2(h) - Encryption Requirements

> **Encryption**: Essential services operators must implement policies and procedures for the use of cryptography, where appropriate, including encryption, to protect data.

### Compliance Matrix

| Requirement | Implementation | Status |
|-------------|----------------|--------|
| **Encryption at rest** | Credentials, config files | ✅ Complete |
| **Encryption in transit** | HTTPS, OPC-UA, MQTT, ZeroBus | ✅ Complete |
| **Key management** | Master password, PBKDF2 | ✅ Complete |
| **Strong algorithms** | AES-256, TLS 1.2+, SHA-256 | ✅ Complete |
| **Certificate management** | Auto-generation, validation | ✅ Complete |
| **Access control** | File permissions (0600/0644) | ✅ Complete |

**Compliance Status**: ✅ **FULLY COMPLIANT** with NIS2 Article 21.2(h)

---

## Encryption Features

### 1. Data at Rest

#### Credential Storage
- **Technology**: Fernet (AES-256-CBC)
- **Key Derivation**: PBKDF2, 480,000 iterations
- **Salt**: 16-byte per-installation salt
- **Location**: `~/.unified_connector/credentials.enc`
- **Master Password**: `CONNECTOR_MASTER_PASSWORD` env var

**Usage**:
```bash
export CONNECTOR_MASTER_PASSWORD="your-strong-password"
python -m unified_connector.main
```

#### Configuration File Encryption
- **Technology**: Fernet (AES-256-CBC)
- **Selective Encryption**: Only sensitive fields encrypted
- **Markers**: `ENC[...]` prefix for encrypted values
- **Backward Compatible**: Works with plaintext configs

**Usage**:
```bash
python scripts/encrypt_config.py --encrypt config.yaml
```

**See**: [CONFIG_ENCRYPTION.md](CONFIG_ENCRYPTION.md)

### 2. Data in Transit

#### Web UI (HTTPS)
- **Protocol**: HTTPS (TLS/SSL)
- **Versions**: TLS 1.2, TLS 1.3
- **Certificates**: Self-signed or CA-signed
- **HSTS**: HTTP Strict Transport Security enabled

**Usage**:
```bash
python scripts/generate_tls_cert.py --generate
```

**Configuration**:
```yaml
web_ui:
  tls:
    enabled: true
    common_name: localhost
```

**See**: [TLS_SETUP.md](TLS_SETUP.md)

#### OPC-UA Security
- **Protocol**: OPC UA with Basic256Sha256
- **Modes**: Sign, SignAndEncrypt
- **Authentication**: Certificate-based, username/password
- **Standard**: IEC 62541 compliant

**Usage**:
```bash
python scripts/generate_opcua_cert.py --generate
```

**Configuration**:
```yaml
security:
  enabled: true
  security_policy: Basic256Sha256
  security_mode: SignAndEncrypt
```

**See**: [OPCUA_SECURITY.md](OPCUA_SECURITY.md)

#### MQTT TLS
- **Protocol**: MQTT v3.1.1 with TLS
- **Versions**: TLS 1.2, TLS 1.3
- **Authentication**: Mutual TLS, username/password
- **Cloud Support**: AWS IoT, Azure IoT Hub, HiveMQ

**Configuration**:
```yaml
endpoint: mqtts://broker:8883
security:
  ca_cert_path: /path/to/ca.crt
  client_cert_path: /path/to/client.crt
  client_key_path: /path/to/client.key
```

**See**: [MQTT_SECURITY.md](MQTT_SECURITY.md)

#### ZeroBus (Databricks)
- **Protocol**: HTTPS with OAuth 2.0
- **Managed by**: Databricks platform
- **Encryption**: TLS 1.2+ (automatic)
- **Authentication**: OAuth client credentials

**Configuration**:
```yaml
zerobus:
  workspace_host: https://your-workspace.cloud.databricks.com
  auth:
    client_id: ${credential:zerobus.client_id}
    client_secret: ${credential:zerobus.client_secret}
```

---

## Quick Start

### Step 1: Set Master Password

```bash
export CONNECTOR_MASTER_PASSWORD="$(openssl rand -base64 24)"
echo "CONNECTOR_MASTER_PASSWORD=$CONNECTOR_MASTER_PASSWORD" >> ~/.bashrc
```

### Step 2: Encrypt Configuration (Optional)

```bash
python scripts/encrypt_config.py --identify config.yaml
python scripts/encrypt_config.py --encrypt config.yaml
```

### Step 3: Enable HTTPS for Web UI

```bash
python scripts/generate_tls_cert.py --generate
```

Edit `config.yaml`:
```yaml
web_ui:
  tls:
    enabled: true
```

### Step 4: Configure Protocol Security

**OPC-UA**:
```bash
python scripts/generate_opcua_cert.py --generate
```

**MQTT**: Use `mqtts://` scheme in endpoint:
```yaml
endpoint: mqtts://broker.example.com:8883
```

### Step 5: Start Connector

```bash
python -m unified_connector.main
```

**Verify**:
- ✅ HTTPS: `https://localhost:8082`
- ✅ OPC-UA: Check logs for "Configured certificate-based security"
- ✅ MQTT: Check logs for "TLS/SSL enabled for MQTT connection"

---

## Component Overview

### Encryption Modules

```
unified_connector/
├── core/
│   ├── encryption.py          # Base encryption (AES-256)
│   ├── credential_manager.py  # Credential storage
│   ├── config_encryption.py   # Config file encryption
│   └── tls_manager.py          # TLS certificate management
├── protocols/
│   ├── opcua_security.py       # OPC-UA security
│   └── mqtt_security.py        # MQTT TLS security
└── web/
    ├── security_headers.py     # HSTS, CSP headers
    └── web_server.py           # HTTPS support
```

### Utilities

```
scripts/
├── generate_tls_cert.py        # HTTPS certificates
├── generate_opcua_cert.py      # OPC-UA certificates
└── encrypt_config.py           # Config encryption
```

### Documentation

```
docs/
├── ENCRYPTION_OVERVIEW.md      # This file
├── CONFIG_ENCRYPTION.md        # Config file encryption
├── TLS_SETUP.md                # HTTPS setup
├── OPCUA_SECURITY.md           # OPC-UA security
└── MQTT_SECURITY.md            # MQTT TLS
```

---

## Security Architecture

### Defense in Depth

```
┌─────────────────────────────────────────────────────────┐
│  Layer 7: Application                                   │
│  - Input validation                                     │
│  - Authentication (OAuth2, certificates)                │
│  - Authorization (RBAC)                                 │
├─────────────────────────────────────────────────────────┤
│  Layer 6: Encryption                                    │
│  - Config encryption (AES-256)                          │
│  - Credential encryption (Fernet)                       │
│  - File permissions (0600/0644)                         │
├─────────────────────────────────────────────────────────┤
│  Layer 5: Transport Security                            │
│  - HTTPS (TLS 1.2/1.3)                                  │
│  - OPC-UA SignAndEncrypt                                │
│  - MQTT TLS/mTLS                                        │
│  - ZeroBus HTTPS                                        │
├─────────────────────────────────────────────────────────┤
│  Layer 4: Network                                       │
│  - Firewall rules                                       │
│  - Network segmentation (OT/IT separation)              │
│  - VPN/private networks                                 │
└─────────────────────────────────────────────────────────┘
```

### Encryption Flow

```
┌─────────────────┐
│  Plaintext Data │
└────────┬────────┘
         │
         ▼
┌─────────────────────┐
│  Master Password    │ ──► PBKDF2 (480k iterations)
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│  Encryption Key     │ ──► AES-256 via Fernet
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│  Encrypted Data     │ ──► ENC[...] or binary
└─────────────────────┘
          │
          ▼
┌─────────────────────┐
│  TLS Transport      │ ──► TLS 1.2/1.3
└─────────────────────┘
          │
          ▼
┌─────────────────────┐
│  Databricks/Server  │
└─────────────────────┘
```

---

## Best Practices

### Master Password

✅ **DO**:
- Use 16+ characters
- Include uppercase, lowercase, numbers, symbols
- Store in password manager
- Use environment variable (`CONNECTOR_MASTER_PASSWORD`)
- Rotate annually

❌ **DON'T**:
- Use dictionary words
- Hardcode in scripts
- Commit to Git
- Share via email/chat
- Reuse across systems

### Certificate Management

✅ **DO**:
- Use 2048+ bit RSA keys
- Set appropriate validity periods (1-2 years)
- Monitor expiration (30-day warning)
- Rotate before expiration
- Use CA-signed certs in production
- Set secure file permissions (0600 for keys)

❌ **DON'T**:
- Use self-signed certs in production
- Share private keys
- Use weak key sizes (<2048 bits)
- Let certificates expire
- Disable certificate validation

### Configuration Files

✅ **DO**:
- Encrypt sensitive fields
- Use environment variables for secrets
- Set file permissions to 0600
- Backup before encryption
- Test encrypted configs in dev first

❌ **DON'T**:
- Commit secrets to Git
- Store plaintext passwords
- Use same secrets across environments
- Skip encryption in production

### Protocol Security

✅ **DO**:
- Use TLS 1.2 minimum
- Enable certificate validation
- Use mutual TLS for high security
- Implement defense in depth
- Monitor security logs

❌ **DON'T**:
- Use unencrypted protocols in production
- Disable certificate validation
- Use weak cipher suites
- Ignore security warnings
- Skip security testing

---

## Documentation Index

### Getting Started
1. **This Document** - Overall encryption overview
2. [TLS_SETUP.md](TLS_SETUP.md) - HTTPS for web UI (start here)
3. [CONFIG_ENCRYPTION.md](CONFIG_ENCRYPTION.md) - Encrypt config files

### Protocol-Specific
4. [OPCUA_SECURITY.md](OPCUA_SECURITY.md) - OPC-UA Sign & Encrypt
5. [MQTT_SECURITY.md](MQTT_SECURITY.md) - MQTT TLS/mTLS

### Additional Resources
6. [SIEM_INTEGRATION.md](SIEM_INTEGRATION.md) - Security monitoring
7. [SECURITY_TESTING.md](SECURITY_TESTING.md) - Security testing guide

### Implementation Details
- Source code: `unified_connector/core/encryption.py`
- Scripts: `scripts/generate_*.py`
- Configuration: `unified_connector/config/config.yaml`

---

## Encryption Checklist

Use this checklist to verify encryption is properly configured:

### Data at Rest
- [ ] Master password set (`CONNECTOR_MASTER_PASSWORD`)
- [ ] Credentials encrypted (`~/.unified_connector/credentials.enc`)
- [ ] Config files encrypted (optional but recommended)
- [ ] File permissions set correctly (0600 for private keys)

### Data in Transit
- [ ] Web UI using HTTPS (`https://localhost:8082`)
- [ ] HSTS header enabled
- [ ] OPC-UA security mode: SignAndEncrypt (if used)
- [ ] MQTT using mqtts:// (if used)
- [ ] ZeroBus using HTTPS (automatic)

### Certificates
- [ ] TLS certificates generated for HTTPS
- [ ] OPC-UA certificates generated (if used)
- [ ] CA certificates obtained for MQTT (if used)
- [ ] Certificate expiration monitoring enabled
- [ ] Private keys have 0600 permissions

### Configuration
- [ ] `web_ui.tls.enabled = true`
- [ ] OPC-UA `security.enabled = true` (if used)
- [ ] MQTT using `mqtts://` scheme (if used)
- [ ] Credentials stored in credential manager, not config
- [ ] Environment variables used for secrets

### Validation
- [ ] Test HTTPS connection
- [ ] Test OPC-UA secure connection
- [ ] Test MQTT TLS connection
- [ ] No plaintext secrets in config files
- [ ] No certificate validation warnings in logs

---

## Troubleshooting

### Issue: Decryption Failed

**Symptom**: "Decryption failed: Invalid key or corrupted data"

**Solution**:
```bash
# Check master password is set
echo $CONNECTOR_MASTER_PASSWORD

# If wrong password, restore from backup
cp credentials.enc.backup credentials.enc

# Or re-encrypt with correct password
export CONNECTOR_MASTER_PASSWORD="correct-password"
```

### Issue: TLS Certificate Error

**Symptom**: "Certificate verification failed"

**Solution**:
```bash
# Regenerate certificate
python scripts/generate_tls_cert.py --generate

# Or trust self-signed certificate
# See TLS_SETUP.md for instructions
```

### Issue: Connection Refused

**Symptom**: Can't connect to HTTPS/mqtts://

**Check**:
```bash
# Web UI
curl -k https://localhost:8082/api/health

# MQTT
telnet broker.example.com 8883
```

---

## Support and Resources

### Documentation
- **NIS2 Directive**: [EUR-Lex](https://eur-lex.europa.eu/eli/dir/2022/2555)
- **OWASP Cheat Sheets**: [cheatsheetseries.owasp.org](https://cheatsheetseries.owasp.org/)
- **Mozilla SSL Config**: [ssl-config.mozilla.org](https://ssl-config.mozilla.org/)

### Related Modules
- **Authentication**: See Sprint 1.1 documentation
- **Security Testing**: See `SECURITY_TESTING.md`
- **SIEM Integration**: See `SIEM_INTEGRATION.md`

### Getting Help
- Check specific documentation for each component
- Review logs for error details
- Test in development environment first
- Contact support with correlation IDs from logs

---

## Security Contacts

For security issues or questions:
- **Documentation**: This repository (`docs/` directory)
- **Configuration**: `unified_connector/config/config.yaml`
- **Scripts**: `scripts/generate_*.py`

---

**Last Updated**: 2025-01-31
**NIS2 Compliance**: Phase 2, Sprint 2.1 - Data Protection & Encryption
**Status**: ✅ PRODUCTION READY - FULLY NIS2 COMPLIANT

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2025-01-31 | Initial release with complete encryption suite |

---

**Encryption Coverage**: ✅ 100% Complete
**NIS2 Article 21.2(h)**: ✅ Fully Compliant
**Production Ready**: ✅ Yes
