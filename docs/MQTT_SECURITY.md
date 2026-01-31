# MQTT TLS/SSL Security Configuration Guide

**NIS2 Compliance**: Article 21.2(h) - Encryption (data in transit)
**Protocol**: MQTT v3.1.1 with TLS/SSL
**Version**: 1.0
**Last Updated**: 2025-01-31

This guide explains how to configure secure MQTT connections using TLS/SSL encryption.

---

## Table of Contents

1. [Overview](#overview)
2. [Quick Start](#quick-start)
3. [Security Modes](#security-modes)
4. [Certificate Setup](#certificate-setup)
5. [Configuration](#configuration)
6. [Authentication Methods](#authentication-methods)
7. [Troubleshooting](#troubleshooting)
8. [Security Best Practices](#security-best-practices)

---

## Overview

### Why MQTT TLS?

MQTT is a lightweight publish/subscribe messaging protocol widely used in IoT and industrial automation. By default, MQTT connections are unencrypted.

**NIS2 Requirement**: Article 21.2(h) mandates encryption for data in transit.

**Threats Mitigated**:
- ✅ **Eavesdropping** on sensor data
- ✅ **Man-in-the-Middle (MITM)** attacks
- ✅ **Unauthorized access** to MQTT broker
- ✅ **Message tampering**

### MQTT vs MQTTS

| Scheme | Port | Encryption | Use Case |
|--------|------|------------|----------|
| `mqtt://` | 1883 | ❌ None | Development only |
| `mqtts://` | 8883 | ✅ TLS/SSL | Production |

**Recommendation**: Always use `mqtts://` for production deployments.

### TLS Versions

| Version | Status | Use |
|---------|--------|-----|
| TLS 1.0 | ❌ Deprecated | Never use |
| TLS 1.1 | ❌ Deprecated | Never use |
| TLS 1.2 | ✅ Recommended | Default |
| TLS 1.3 | ✅ Best | If broker supports |

---

## Quick Start

### 1. Basic TLS Connection (Server Authentication Only)

**Configuration**:
```yaml
sources:
  - name: mqtt-secure
    protocol: mqtt
    endpoint: mqtts://broker.example.com:8883
    security:
      ca_cert_path: /path/to/ca.crt
      username: ${credential:mqtt.username}
      password: ${credential:mqtt.password}
```

**This enables**:
- ✅ Encrypted connection
- ✅ Server certificate validation
- ✅ Username/password authentication

### 2. Mutual TLS (Client + Server Authentication)

**Configuration**:
```yaml
sources:
  - name: mqtt-mutual-tls
    protocol: mqtt
    endpoint: mqtts://broker.example.com:8883
    security:
      ca_cert_path: /path/to/ca.crt
      client_cert_path: /path/to/client.crt
      client_key_path: /path/to/client.key
```

**This enables**:
- ✅ Encrypted connection
- ✅ Server certificate validation
- ✅ Client certificate authentication (mutual TLS)

### 3. Start Connector

```bash
python -m unified_connector.main
```

**Verify**:
```
✓ MQTT TLS configuration is valid
✓ Loaded CA certificate: /path/to/ca.crt
✓ TLS/SSL enabled for MQTT connection
```

---

## Security Modes

### 1. No Security (Development Only)

**Configuration**:
```yaml
endpoint: mqtt://localhost:1883
```

**Features**:
- ❌ No encryption
- ❌ No authentication

**Use Case**: Local development only
**NIS2 Compliant**: ❌ No

### 2. TLS with Username/Password

**Configuration**:
```yaml
endpoint: mqtts://broker.example.com:8883
security:
  ca_cert_path: /path/to/ca.crt
  username: ${credential:mqtt.username}
  password: ${credential:mqtt.password}
```

**Features**:
- ✅ Encrypted connection
- ✅ Server authentication
- ✅ Password authentication

**Use Case**: Standard secure deployment
**NIS2 Compliant**: ✅ Yes

### 3. Mutual TLS (mTLS)

**Configuration**:
```yaml
endpoint: mqtts://broker.example.com:8883
security:
  ca_cert_path: /path/to/ca.crt
  client_cert_path: /path/to/client.crt
  client_key_path: /path/to/client.key
```

**Features**:
- ✅ Encrypted connection
- ✅ Server authentication
- ✅ Client certificate authentication

**Use Case**: High-security industrial environments
**NIS2 Compliant**: ✅✅ Yes (strongest)

### 4. Mutual TLS + Username/Password

**Configuration**:
```yaml
endpoint: mqtts://broker.example.com:8883
security:
  ca_cert_path: /path/to/ca.crt
  client_cert_path: /path/to/client.crt
  client_key_path: /path/to/client.key
  username: ${credential:mqtt.username}
  password: ${credential:mqtt.password}
```

**Features**:
- ✅ Encrypted connection
- ✅ Server authentication
- ✅ Client certificate authentication
- ✅ Password authentication (2-factor)

**Use Case**: Maximum security for critical infrastructure
**NIS2 Compliant**: ✅✅✅ Yes (2-factor)

---

## Certificate Setup

### CA Certificate (Required for TLS)

The CA certificate validates the MQTT broker's identity.

**Obtain CA Certificate**:

**Method 1: From Broker Provider** (AWS IoT, Azure IoT Hub, HiveMQ Cloud):
```bash
# AWS IoT Core
curl https://www.amazontrust.com/repository/AmazonRootCA1.pem -o ca.crt

# Azure IoT Hub
curl https://cacerts.digicert.com/DigiCertGlobalRootG2.crt.pem -o ca.crt
```

**Method 2: Self-Signed (Development)**:
```bash
# Generate CA certificate
openssl req -new -x509 -days 3650 \
  -keyout ca.key -out ca.crt \
  -subj "/CN=MQTT CA"
```

**Method 3: Let's Encrypt** (Public brokers):
```bash
# Download Let's Encrypt CA bundle
curl https://letsencrypt.org/certs/isrgrootx1.pem -o ca.crt
```

### Client Certificate (Optional, for Mutual TLS)

**Generate Client Certificate**:

```bash
# 1. Generate client private key
openssl genrsa -out client.key 2048

# 2. Generate certificate signing request (CSR)
openssl req -new -key client.key -out client.csr \
  -subj "/CN=unified-connector-client"

# 3. Sign with CA (or submit to broker provider)
openssl x509 -req -in client.csr \
  -CA ca.crt -CAkey ca.key -CAcreateserial \
  -out client.crt -days 365 -sha256
```

**Or use broker-provided client certificates** (AWS IoT, Azure IoT):
- Follow broker's instructions to generate device certificates
- Download client certificate and private key

### File Locations

Recommended structure:
```
~/.unified_connector/mqtt_certs/
├── ca.crt              # CA certificate
├── client.crt          # Client certificate (optional)
└── client.key          # Client private key (optional, chmod 600)
```

**Set Permissions**:
```bash
chmod 644 ~/.unified_connector/mqtt_certs/ca.crt
chmod 644 ~/.unified_connector/mqtt_certs/client.crt
chmod 600 ~/.unified_connector/mqtt_certs/client.key  # Private key!
```

---

## Configuration

### Basic TLS Configuration

```yaml
sources:
  - name: mqtt-broker
    protocol: mqtt
    endpoint: mqtts://broker.example.com:8883
    security:
      tls_version: TLSv1_2
      ca_cert_path: ~/.unified_connector/mqtt_certs/ca.crt
      cert_required: true
      check_hostname: true
```

### Mutual TLS Configuration

```yaml
sources:
  - name: mqtt-broker
    protocol: mqtt
    endpoint: mqtts://broker.example.com:8883
    security:
      tls_version: TLSv1_2
      ca_cert_path: ~/.unified_connector/mqtt_certs/ca.crt
      client_cert_path: ~/.unified_connector/mqtt_certs/client.crt
      client_key_path: ~/.unified_connector/mqtt_certs/client.key
      cert_required: true
      check_hostname: true
```

### With Username/Password

```yaml
sources:
  - name: mqtt-broker
    protocol: mqtt
    endpoint: mqtts://broker.example.com:8883
    security:
      ca_cert_path: ~/.unified_connector/mqtt_certs/ca.crt
      username: ${credential:mqtt.username}
      password: ${credential:mqtt.password}
```

### Development Mode (Skip Validation)

```yaml
security:
  ca_cert_path: ~/.unified_connector/mqtt_certs/ca.crt
  cert_required: false
  check_hostname: false
  insecure: true  # ⚠️  DEVELOPMENT ONLY
```

**Warning**: `insecure: true` disables all certificate validation. **NEVER** use in production!

### Advanced Configuration

```yaml
sources:
  - name: mqtt-broker
    protocol: mqtt
    endpoint: mqtts://broker.example.com:8883
    security:
      # TLS configuration
      tls_version: TLSv1_3  # Use TLS 1.3 if broker supports
      ca_cert_path: ~/.unified_connector/mqtt_certs/ca.crt
      client_cert_path: ~/.unified_connector/mqtt_certs/client.crt
      client_key_path: ~/.unified_connector/mqtt_certs/client.key
      cert_required: true
      check_hostname: true
      # Custom cipher suite (optional)
      ciphers: "ECDHE+AESGCM:ECDHE+CHACHA20:!aNULL:!MD5"
      # Authentication
      username: ${credential:mqtt.username}
      password: ${credential:mqtt.password}
    # MQTT settings
    topics: ["sensor/#", "telemetry/#"]
    qos: 1
    client_id: unified-connector
    clean_session: true
    keepalive: 60
```

---

## Authentication Methods

### 1. No Authentication (Insecure)

```yaml
endpoint: mqtt://localhost:1883
```

**Security Level**: ❌ None

### 2. Username/Password Only (Insecure without TLS)

```yaml
endpoint: mqtt://broker.example.com:1883
security:
  username: myuser
  password: mypassword
```

**Security Level**: ❌ Low (credentials sent in plaintext!)

### 3. TLS + Username/Password (Recommended)

```yaml
endpoint: mqtts://broker.example.com:8883
security:
  ca_cert_path: ~/.unified_connector/mqtt_certs/ca.crt
  username: ${credential:mqtt.username}
  password: ${credential:mqtt.password}
```

**Security Level**: ✅ Good

### 4. Mutual TLS (Certificate-Based)

```yaml
endpoint: mqtts://broker.example.com:8883
security:
  ca_cert_path: ~/.unified_connector/mqtt_certs/ca.crt
  client_cert_path: ~/.unified_connector/mqtt_certs/client.crt
  client_key_path: ~/.unified_connector/mqtt_certs/client.key
```

**Security Level**: ✅✅ Strong

### 5. Mutual TLS + Username/Password (Most Secure)

```yaml
endpoint: mqtts://broker.example.com:8883
security:
  ca_cert_path: ~/.unified_connector/mqtt_certs/ca.crt
  client_cert_path: ~/.unified_connector/mqtt_certs/client.crt
  client_key_path: ~/.unified_connector/mqtt_certs/client.key
  username: ${credential:mqtt.username}
  password: ${credential:mqtt.password}
```

**Security Level**: ✅✅✅ Very Strong (2-factor)

---

## Troubleshooting

### Error: "Certificate verification failed"

**Symptom**:
```
ssl.SSLError: [SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed
```

**Cause**: CA certificate not trusted or incorrect

**Solution 1**: Check CA certificate path
```bash
cat ~/.unified_connector/mqtt_certs/ca.crt
# Should show PEM-encoded certificate
```

**Solution 2**: Use system CA certificates
```yaml
security:
  # Omit ca_cert_path to use system default CAs
  cert_required: true
```

**Solution 3**: Skip validation (development only)
```yaml
security:
  insecure: true  # ⚠️  Development only!
```

### Error: "Hostname mismatch"

**Symptom**:
```
ssl.CertificateError: hostname 'broker.example.com' doesn't match certificate
```

**Cause**: Server certificate Common Name (CN) doesn't match endpoint hostname

**Solution 1**: Use correct hostname in endpoint
```yaml
endpoint: mqtts://correct-hostname:8883
```

**Solution 2**: Disable hostname checking (not recommended)
```yaml
security:
  check_hostname: false
```

### Error: "Connection refused"

**Symptom**:
```
ConnectionRefusedError: [Errno 111] Connection refused
```

**Check 1**: Broker is running
```bash
telnet broker.example.com 8883
```

**Check 2**: Correct port (mqtts:// uses 8883, not 1883)
```yaml
endpoint: mqtts://broker.example.com:8883  # Not 1883!
```

**Check 3**: Firewall allows port 8883
```bash
nc -zv broker.example.com 8883
```

### Error: "Client certificate required"

**Symptom**:
```
ssl.SSLError: [SSL: TLSV1_ALERT_CERTIFICATE_REQUIRED]
```

**Cause**: Broker requires client certificate (mutual TLS)

**Solution**: Provide client certificate
```yaml
security:
  client_cert_path: ~/.unified_connector/mqtt_certs/client.crt
  client_key_path: ~/.unified_connector/mqtt_certs/client.key
```

### Error: "Authentication failed"

**Symptom**:
```
CONNACK: Connection refused, not authorized
```

**Cause**: Invalid username/password

**Solution**: Check credentials
```bash
# Store credentials securely
python -m unified_connector.core.credential_manager set mqtt.username "myuser"
python -m unified_connector.core.credential_manager set mqtt.password "mypass"
```

---

## Security Best Practices

### Development

1. ✅ Use `mqtt://localhost` for local testing
2. ✅ Username/password authentication OK
3. ✅ Self-signed certificates acceptable
4. ✅ `insecure: true` OK for troubleshooting

### Production

1. ✅ **Always use mqtts://** (port 8883)
2. ✅ **Validate server certificates** (cert_required: true)
3. ✅ **Never use** `insecure: true`
4. ✅ **Use mutual TLS** for high-security environments
5. ✅ **Strong usernames/passwords** (16+ characters)
6. ✅ **Store credentials** in credential manager, not config
7. ✅ **Rotate credentials** quarterly
8. ✅ **Monitor certificate expiration**
9. ✅ **Use TLS 1.2 minimum**, TLS 1.3 preferred
10. ✅ **Restrict MQTT topics** (don't use `#` wildcard)

### Certificate Management

**Validity Periods**:
- Development: 365 days OK
- Production: 730 days recommended
- Max: 825 days (browser CA limits)

**Key Sizes**:
- Minimum: 2048 bits RSA
- Recommended: 2048 bits (good balance)
- High security: 4096 bits (slower)

**File Permissions**:
```bash
chmod 644 ca.crt        # CA certificate (public)
chmod 644 client.crt    # Client certificate (public)
chmod 600 client.key    # Private key (SECRET!)
```

**Rotation**:
```bash
# Check expiration
openssl x509 -in client.crt -noout -enddate

# Renew 30 days before expiration
# 1. Generate new certificate
# 2. Test with new certificate
# 3. Update production config
# 4. Revoke old certificate
```

### Defense in Depth

1. **Network Level**: Firewall, VPN, network segmentation
2. **Transport Level**: TLS 1.2+ encryption
3. **Authentication Level**: Mutual TLS + username/password
4. **Authorization Level**: MQTT ACLs (topic permissions)
5. **Application Level**: Input validation, rate limiting
6. **Monitoring Level**: SIEM integration, anomaly detection

---

## Cloud Provider Examples

### AWS IoT Core

```yaml
sources:
  - name: aws-iot
    protocol: mqtt
    endpoint: mqtts://xxxxx.iot.us-east-1.amazonaws.com:8883
    security:
      ca_cert_path: ~/.unified_connector/mqtt_certs/AmazonRootCA1.pem
      client_cert_path: ~/.unified_connector/mqtt_certs/device.crt
      client_key_path: ~/.unified_connector/mqtt_certs/device.key
    topics: ["$aws/things/my-device/shadow/update"]
    client_id: my-device
```

### Azure IoT Hub

```yaml
sources:
  - name: azure-iot
    protocol: mqtt
    endpoint: mqtts://my-hub.azure-devices.net:8883
    security:
      ca_cert_path: ~/.unified_connector/mqtt_certs/DigiCertGlobalRootG2.crt
      username: my-hub.azure-devices.net/my-device/?api-version=2021-04-12
      password: ${credential:azure.iot.sas_token}
    topics: ["devices/my-device/messages/devicebound/#"]
    client_id: my-device
```

### HiveMQ Cloud

```yaml
sources:
  - name: hivemq-cloud
    protocol: mqtt
    endpoint: mqtts://xxxxx.s2.eu.hivemq.cloud:8883
    security:
      # HiveMQ Cloud uses Let's Encrypt, system CAs work
      username: ${credential:hivemq.username}
      password: ${credential:hivemq.password}
    topics: ["sensor/#"]
    client_id: unified-connector
```

---

## References

- **MQTT v3.1.1 Specification**: [docs.oasis-open.org](http://docs.oasis-open.org/mqtt/mqtt/v3.1.1/mqtt-v3.1.1.html)
- **NIS2 Directive**: [EUR-Lex](https://eur-lex.europa.eu/eli/dir/2022/2555)
- **OWASP IoT Security**: [owasp.org/iot](https://owasp.org/www-project-internet-of-things/)
- **aiomqtt Documentation**: [sbtinstruments.github.io/aiomqtt](https://sbtinstruments.github.io/aiomqtt/)
- **Mozilla SSL Configuration**: [ssl-config.mozilla.org](https://ssl-config.mozilla.org/)

---

**Last Updated**: 2025-01-31
**NIS2 Compliance**: Phase 2, Sprint 2.1 - Protocol-Level Encryption
**Status**: Production Ready
