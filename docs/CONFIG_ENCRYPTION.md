# Configuration File Encryption Guide

**NIS2 Compliance**: Article 21.2(h) - Encryption (data at rest)
**Version**: 1.0
**Last Updated**: 2025-01-31

This guide explains how to encrypt sensitive data in configuration files for NIS2 compliance.

---

## Table of Contents

1. [Overview](#overview)
2. [Quick Start](#quick-start)
3. [How It Works](#how-it-works)
4. [Encrypting Configuration](#encrypting-configuration)
5. [Decrypting Configuration](#decrypting-configuration)
6. [Environment Variables](#environment-variables)
7. [Master Password Setup](#master-password-setup)
8. [Troubleshooting](#troubleshooting)
9. [Security Best Practices](#security-best-practices)

---

## Overview

### Why Encrypt Configuration Files?

Configuration files often contain sensitive data:
- API keys and secrets
- OAuth client secrets
- Session encryption keys
- Database passwords
- Private keys

**NIS2 Requirement**: Article 21.2(h) mandates encryption of sensitive data at rest.

### Features

- ✅ **Selective Encryption**: Only sensitive fields are encrypted
- ✅ **Auto-Detection**: Automatically identifies sensitive fields
- ✅ **Environment Variables**: Supports `${env:VAR}` substitution (not encrypted)
- ✅ **Credential References**: Supports `${credential:key}` references (not encrypted)
- ✅ **Backward Compatible**: Works with existing plaintext configs
- ✅ **Master Password**: Uses CONNECTOR_MASTER_PASSWORD for encryption
- ✅ **Clear Markers**: Encrypted values marked with `ENC[...]` prefix

---

## Quick Start

### 1. Set Master Password

```bash
export CONNECTOR_MASTER_PASSWORD="your-strong-password-here"
```

**Important**: Use a strong password (16+ characters, mixed case, numbers, symbols)

### 2. Identify Sensitive Fields

```bash
python scripts/encrypt_config.py --identify unified_connector/config/config.yaml
```

**Output**:
```
Found 3 sensitive field(s):

  • web_ui.authentication.session.secret_key
  • web_ui.authentication.oauth.client_secret
  • zerobus.auth.client_secret
```

### 3. Encrypt Configuration

```bash
python scripts/encrypt_config.py --encrypt unified_connector/config/config.yaml
```

**Output**:
```
✅ Configuration Encrypted Successfully!
Encrypted file: unified_connector/config/config.encrypted.yaml
```

### 4. Test Encrypted Configuration

```bash
# Verify it loads correctly
python -c 'from unified_connector.core.config_loader import ConfigLoader; \
  c = ConfigLoader("unified_connector/config/config.encrypted.yaml"); \
  print("✅ Configuration loads successfully")'
```

### 5. Replace Original (Optional)

```bash
# Backup original
mv unified_connector/config/config.yaml unified_connector/config/config.yaml.backup

# Use encrypted version
mv unified_connector/config/config.encrypted.yaml unified_connector/config/config.yaml
```

---

## How It Works

### Encryption Process

1. **Identification**: Scans configuration for sensitive field names
2. **Selection**: Identifies fields containing:
   - `password`, `secret`, `token`, `api_key`
   - `client_secret`, `session_secret_key`
   - `private_key`, `encryption_key`
   - `access_token`, `refresh_token`
3. **Encryption**: Encrypts values using AES-256 (Fernet)
4. **Marking**: Adds `ENC[...]` wrapper for identification
5. **Preservation**: Keeps non-sensitive data in plaintext

### Example

**Before**:
```yaml
web_ui:
  authentication:
    session:
      secret_key: my-secret-key-12345
```

**After**:
```yaml
web_ui:
  authentication:
    session:
      secret_key: ENC[gAAAAABl2x3y4z5w6...]
```

### What Gets Encrypted

**Encrypted**:
- Plaintext sensitive values

**NOT Encrypted**:
- Environment variable references: `${env:VAR_NAME}`
- Credential references: `${credential:key}`
- Already encrypted values: `ENC[...]`
- Non-sensitive fields

---

## Encrypting Configuration

### Method 1: Auto-Generated Output

```bash
python scripts/encrypt_config.py --encrypt config.yaml
```

Creates: `config.encrypted.yaml`

### Method 2: Custom Output Path

```bash
python scripts/encrypt_config.py --encrypt config.yaml --output secure_config.yaml
```

### Method 3: In-Place Encryption

```bash
# Backup first
cp config.yaml config.yaml.backup

# Encrypt to same path
python scripts/encrypt_config.py --encrypt config.yaml --output config.yaml --no-backup
```

### Verify Encryption

```bash
# Check for ENC[...] markers
grep "ENC\[" config.encrypted.yaml

# Count encrypted fields
grep -c "ENC\[" config.encrypted.yaml
```

---

## Decrypting Configuration

### Temporary Decryption (for editing)

```bash
python scripts/encrypt_config.py --decrypt config.encrypted.yaml
```

Creates: `config.decrypted.yaml`

**Edit the decrypted file**, then re-encrypt:

```bash
python scripts/encrypt_config.py --encrypt config.decrypted.yaml --output config.yaml
```

### Programmatic Decryption

```python
from unified_connector.core.config_loader import ConfigLoader

# Loads and auto-decrypts
config_loader = ConfigLoader("config.encrypted.yaml")
config = config_loader.load()

# Access decrypted values
secret = config['web_ui']['authentication']['session']['secret_key']
```

---

## Environment Variables

### Why Use Environment Variables?

Environment variables provide:
- ✅ Separation of config from secrets
- ✅ Different values per environment (dev/staging/prod)
- ✅ No encryption needed (resolved at runtime)
- ✅ 12-Factor App compliance

### Syntax

```yaml
# Basic: ${env:VAR_NAME}
oauth:
  client_id: ${env:OAUTH_CLIENT_ID}
  client_secret: ${env:OAUTH_CLIENT_SECRET}

# With default value: ${env:VAR_NAME:default}
session:
  secret_key: ${env:SESSION_SECRET_KEY:generate-a-random-key}
```

### Setting Environment Variables

**Linux/macOS**:
```bash
export OAUTH_CLIENT_ID=abc123
export OAUTH_CLIENT_SECRET=secret456
export SESSION_SECRET_KEY=$(openssl rand -base64 32)
```

**Windows PowerShell**:
```powershell
$env:OAUTH_CLIENT_ID = "abc123"
$env:OAUTH_CLIENT_SECRET = "secret456"
$env:SESSION_SECRET_KEY = (openssl rand -base64 32)
```

**Docker Compose**:
```yaml
services:
  unified-connector:
    environment:
      - OAUTH_CLIENT_ID=abc123
      - OAUTH_CLIENT_SECRET=secret456
      - SESSION_SECRET_KEY=generate-a-random-key
```

**.env File** (development only):
```bash
OAUTH_CLIENT_ID=abc123
OAUTH_CLIENT_SECRET=secret456
SESSION_SECRET_KEY=generate-a-random-key
```

Load with:
```bash
set -a; source .env; set +a
python -m unified_connector.main
```

---

## Master Password Setup

### Choosing a Master Password

**Requirements**:
- ✅ 16+ characters minimum
- ✅ Mixed case (uppercase + lowercase)
- ✅ Numbers and symbols
- ✅ Not dictionary word
- ✅ Unique to this installation

**Good Examples**:
```
Tr@nsf0rm-Un1f1ed!C0nn3ct0r
SecureOT#2025$Databricks!
```

**Bad Examples**:
```
password123       (too simple)
unified          (dictionary word)
12345678         (no letters)
```

### Generating Strong Password

```bash
# Linux/macOS
openssl rand -base64 24

# Output: +3Qx7zW8nP9mK2vL5tR6yU1wN4eA=
```

### Setting Master Password

**Option 1: Environment Variable** (recommended)
```bash
export CONNECTOR_MASTER_PASSWORD="your-strong-password"
```

**Option 2: .bashrc / .zshrc** (persistent)
```bash
echo 'export CONNECTOR_MASTER_PASSWORD="your-strong-password"' >> ~/.bashrc
source ~/.bashrc
```

**Option 3: Systemd Service** (production)
```ini
# /etc/systemd/system/unified-connector.service
[Service]
Environment="CONNECTOR_MASTER_PASSWORD=your-strong-password"
```

**Option 4: Docker Secret** (Docker Swarm)
```bash
echo "your-strong-password" | docker secret create connector_master_password -
```

### Verifying Master Password

```bash
# Should load without errors
python -c 'from unified_connector.core.config_loader import ConfigLoader; \
  ConfigLoader().load(); \
  print("✅ Master password correct")'
```

---

## Troubleshooting

### Error: "No master password provided"

**Symptom**:
```
WARNING: No master password provided. Credential encryption disabled.
```

**Solution**:
```bash
export CONNECTOR_MASTER_PASSWORD="your-password"
```

### Error: "Decryption failed: Invalid key"

**Cause**: Wrong master password or corrupted encrypted data

**Solution**:
1. Verify master password is correct
2. Check if you have a backup: `config.yaml.backup`
3. Restore from backup and re-encrypt

### Error: "Failed to decrypt field"

**Cause**: Salt file or encrypted data corrupted

**Solution**:
```bash
# Check salt file exists
ls ~/.unified_connector/salt.txt

# If missing, restore from backup or re-encrypt
python scripts/encrypt_config.py --encrypt config.yaml.backup
```

### Configuration Not Loading

**Check 1**: Master password set?
```bash
echo $CONNECTOR_MASTER_PASSWORD
```

**Check 2**: Encrypted file exists?
```bash
ls -l unified_connector/config/config.yaml
```

**Check 3**: File contains encrypted values?
```bash
grep "ENC\[" unified_connector/config/config.yaml
```

**Check 4**: Test decryption manually:
```python
from unified_connector.core.config_encryption import ConfigEncryption
ce = ConfigEncryption()
config = ce.load_config("config.yaml", decrypt=True)
print("✅ Decryption successful")
```

### Mixed Encrypted and Plaintext Fields

**Scenario**: Some fields encrypted, others plaintext

**This is normal**! Encryption is selective:
- Sensitive fields (password, secret, token) → Encrypted
- Non-sensitive fields (host, port, enabled) → Plaintext

---

## Security Best Practices

### Configuration Files

1. ✅ **Always encrypt production configs** with sensitive data
2. ✅ **Use environment variables** for environment-specific secrets
3. ✅ **Never commit plaintext secrets** to Git
4. ✅ **Set file permissions**: `chmod 600 config.yaml`
5. ✅ **Backup encrypted configs** before editing
6. ✅ **Rotate secrets regularly** (quarterly minimum)
7. ✅ **Audit access** to configuration files

### Master Password

1. ✅ **Use strong passwords** (16+ characters)
2. ✅ **Don't hardcode** in scripts or code
3. ✅ **Store securely** (password manager, secrets vault)
4. ✅ **Rotate annually** (change password + re-encrypt)
5. ✅ **Limit access** (only authorized personnel)
6. ✅ **Document location** (team knowledge base)
7. ✅ **Test recovery** procedure regularly

### Development vs Production

**Development**:
- Self-signed certs OK
- Environment variables for secrets
- Plaintext config acceptable (non-production secrets)

**Production**:
- ✅ Always encrypt sensitive config fields
- ✅ Use secrets management (HashiCorp Vault, AWS Secrets Manager)
- ✅ Implement key rotation
- ✅ Enable audit logging
- ✅ Restrict file system access
- ✅ Use CA-signed certificates

### Key Management

**Storage Locations** (in order of security):

1. **Hardware Security Module (HSM)** - Best for high-security
2. **Secrets Management System** (Vault, AWS Secrets Manager)
3. **Environment Variables** (systemd, Docker secrets)
4. **Encrypted Config Files** (this solution)
5. ~~Plaintext config files~~ ❌ Never in production

**Key Rotation Procedure**:

```bash
# 1. Generate new master password
NEW_PASSWORD=$(openssl rand -base64 24)

# 2. Decrypt with old password
export CONNECTOR_MASTER_PASSWORD="old-password"
python scripts/encrypt_config.py --decrypt config.yaml

# 3. Re-encrypt with new password
export CONNECTOR_MASTER_PASSWORD="$NEW_PASSWORD"
python scripts/encrypt_config.py --encrypt config.decrypted.yaml

# 4. Test loading
python -c 'from unified_connector.core.config_loader import ConfigLoader; \
  ConfigLoader().load(); \
  print("✅ Re-encryption successful")'

# 5. Update password in production environment
# 6. Restart application
```

---

## Advanced Topics

### Custom Sensitive Fields

Add custom field patterns to encryption:

```python
from unified_connector.core.config_encryption import ConfigEncryption

config_encryption = ConfigEncryption()
config = config_encryption.encrypt_config(
    config_dict,
    sensitive_fields={'my_custom_secret', 'internal_token'}
)
```

### Integration with Secrets Management

**HashiCorp Vault**:
```yaml
oauth:
  client_secret: ${credential:vault/oauth/client_secret}
```

**AWS Secrets Manager**:
```yaml
oauth:
  client_secret: ${credential:aws/unified-connector/oauth-secret}
```

### Programmatic Encryption

```python
from unified_connector.core.config_encryption import ConfigEncryption

# Initialize
ce = ConfigEncryption()

# Encrypt specific value
encrypted = ce.encrypt_value("my-secret-value")
print(encrypted)  # ENC[gAAAAABl2x3y...]

# Decrypt
decrypted = ce.decrypt_value(encrypted)
print(decrypted)  # my-secret-value
```

---

## Migration Guide

### From Plaintext to Encrypted

**Scenario**: Existing plaintext configuration in production

**Steps**:

1. **Identify current secrets**:
```bash
python scripts/encrypt_config.py --identify config.yaml
```

2. **Create encrypted version**:
```bash
python scripts/encrypt_config.py --encrypt config.yaml --output config.encrypted.yaml
```

3. **Test in development**:
```bash
export CONNECTOR_MASTER_PASSWORD="your-password"
python -m unified_connector.main --config config.encrypted.yaml
```

4. **Deploy to production**:
```bash
# Backup
cp /etc/unified-connector/config.yaml /etc/unified-connector/config.yaml.backup

# Deploy encrypted version
cp config.encrypted.yaml /etc/unified-connector/config.yaml

# Set master password in production
systemctl edit unified-connector
# Add: Environment="CONNECTOR_MASTER_PASSWORD=your-password"

# Restart
systemctl restart unified-connector
```

5. **Verify**:
```bash
systemctl status unified-connector
journalctl -u unified-connector -n 50
```

### From Environment Variables to Encrypted Config

**Scenario**: Moving secrets from env vars to encrypted config

**Before** (config.yaml):
```yaml
oauth:
  client_secret: ${env:OAUTH_CLIENT_SECRET}
```

**After** (config.yaml):
```yaml
oauth:
  client_secret: actual-secret-value  # Will be encrypted as ENC[...]
```

**Migration**:
```bash
# 1. Export env vars to file
echo "oauth:
  client_secret: $OAUTH_CLIENT_SECRET" > secrets.yaml

# 2. Merge with main config
# 3. Encrypt merged config
python scripts/encrypt_config.py --encrypt merged-config.yaml
```

---

## References

- **NIS2 Directive**: [EUR-Lex](https://eur-lex.europa.eu/eli/dir/2022/2555)
- **OWASP Secrets Management**: [cheatsheetseries.owasp.org](https://cheatsheetseries.owasp.org/cheatsheets/Secrets_Management_Cheat_Sheet.html)
- **12-Factor App**: [12factor.net/config](https://12factor.net/config)
- **Cryptography Library**: [cryptography.io](https://cryptography.io/)

---

**Last Updated**: 2025-01-31
**NIS2 Compliance**: Phase 2, Sprint 2.1 - Data Protection & Encryption
**Status**: Production Ready
