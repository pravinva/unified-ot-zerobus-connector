# Proxy Configuration for Purdue Layer 3.5 Deployment

## Overview

The Unified OT Zerobus Connector is designed for deployment in **Purdue/ISA-95 Layer 3.5 (DMZ)**, where it:
- **Listens** to OT devices on Layer 2/2.5/3 (local network, no proxy)
- **Transmits** to Databricks cloud on Layer 4+ via HTTPS/443 (through corporate proxy)

## Network Architecture

```
┌──────────────────────────────────────────────────────────┐
│ Layer 4+: Enterprise / Cloud                             │
│                                                          │
│ Databricks Workspace (Unity Catalog)                     │
│ - workspace.cloud.databricks.com (HTTPS/443)            │
│ - *.zerobus.*.cloud.databricks.com (gRPC over HTTPS)    │
└────────────────────▲─────────────────────────────────────┘
                     │
                     │ THROUGH PROXY
                     │ Port 443 (HTTPS)
                     │
┌────────────────────┼─────────────────────────────────────┐
│ Layer 3.5: DMZ / Edge Gateway                           │
│                    │                                     │
│ Unified Connector  │                                     │
│ (This Application) │                                     │
│                    │                                     │
│ ┌──────────────────┴──────────────────┐                 │
│ │ Proxy Configuration:                │                 │
│ │ - HTTP_PROXY for workspace API      │                 │
│ │ - HTTPS_PROXY for ZeroBus ingest    │                 │
│ │ - NO_PROXY for local OT devices     │                 │
│ └─────────────────────────────────────┘                 │
└────────────────────▲─────────────────────────────────────┘
                     │
                     │ NO PROXY
                     │ Direct connection to OT network
                     │
┌────────────────────┼─────────────────────────────────────┐
│ Layer 2/3: OT Network                                    │
│                    │                                     │
│ - OPC-UA Servers (4840, 4841, etc.)                     │
│ - MQTT Brokers (1883, 8883)                             │
│ - Modbus TCP Devices (502, 5020)                        │
└──────────────────────────────────────────────────────────┘
```

## Real-World Example: Manufacturing Plant Deployment

### Scenario
A manufacturing plant with multiple production lines:
- **OT Network**: 192.168.20.0/24 (PLCs, OPC-UA servers on Layer 2/3)
- **DMZ Network**: 10.100.50.0/24 (Edge gateway/connector on Layer 3.5)
- **Corporate Proxy**: proxy.company.com:8080 (routes to internet/cloud)

### Physical Layout
```
Production Floor (192.168.20.0/24):
├─ PLC #1: 192.168.20.10 (Modbus TCP port 502)
├─ OPC-UA Server #1: 192.168.20.100:4840 (Production Line A)
├─ OPC-UA Server #2: 192.168.20.105:4841 (Production Line B)
└─ MQTT Broker: 192.168.20.200:1883 (Sensor aggregation)

DMZ/Edge Network (10.100.50.0/24):
└─ Unified Connector: 10.100.50.25:8082
   ├─ Connects to OT devices (192.168.20.x) → NO PROXY
   └─ Connects to Databricks cloud → THROUGH PROXY

Corporate Network:
└─ Proxy Server: proxy.company.com:8080 → Internet
```

### Configuration for This Scenario
```yaml
zerobus:
  enabled: true
  proxy:
    enabled: true
    use_env_vars: false
    http_proxy: "http://proxy.company.com:8080"
    https_proxy: "http://proxy.company.com:8080"
    # CRITICAL: Include 192.168.20.0/24 so OT devices bypass proxy
    no_proxy: "localhost,127.0.0.1,192.168.20.0/24,10.100.50.0/24"

# Sources (OT devices - all remote, none are localhost)
sources:
- name: production-line-a-opcua
  protocol: opcua
  endpoint: opc.tcp://192.168.20.100:4840  # ← Direct, no proxy
  enabled: true

- name: production-line-b-opcua
  protocol: opcua
  endpoint: opc.tcp://192.168.20.105:4841  # ← Direct, no proxy
  enabled: true

- name: sensor-mqtt-broker
  protocol: mqtt
  endpoint: mqtt://192.168.20.200:1883     # ← Direct, no proxy
  enabled: true

- name: plc-modbus
  protocol: modbus
  endpoint: modbus://192.168.20.10:502     # ← Direct, no proxy
  enabled: true
```

### Connection Flow
1. **Connector starts** on 10.100.50.25 (DMZ)
2. **Discovery scans** 192.168.20.0/24:
   - Finds 4 devices
   - All connections **direct** (matches `192.168.20.0/24` in `no_proxy`)
3. **Data collection**:
   - OPC-UA clients connect to 192.168.20.100:4840 and 192.168.20.105:4841
   - MQTT client subscribes to 192.168.20.200:1883
   - Modbus polls 192.168.20.10:502
   - All without proxy
4. **Data transmission**:
   - ZeroBus client connects to `workspace.cloud.databricks.com:443`
   - Routes **through** proxy.company.com:8080 (not in `no_proxy`)

## Configuration Methods

### Method 1: Web UI (Recommended)

1. Access the Web UI at `http://localhost:8082`
2. Navigate to the **ZeroBus** section
3. Expand **Proxy Settings (for Purdue Layer 3.5)**
4. Configure:
   - ✅ **Enable Proxy**: Check to activate proxy support
   - ✅ **Use Environment Variables**: Check to use existing env vars (or uncheck to use explicit config)
   - **HTTP Proxy**: `http://proxy.company.com:8080`
   - **HTTPS Proxy**: `http://proxy.company.com:8080`
   - **No Proxy**: `localhost,127.0.0.1,192.168.0.0/16,10.0.0.0/8,.internal`
5. Click **Save**
6. Click **Start** to apply changes

### Method 2: config.yaml

Edit `unified_connector/config/config.yaml`:

```yaml
zerobus:
  enabled: true
  workspace_host: https://your-workspace.cloud.databricks.com
  zerobus_endpoint: 1234567890.zerobus.us-west-2.cloud.databricks.com

  auth:
    client_id: ${credential:zerobus.client_id}
    client_secret: ${credential:zerobus.client_secret}

  # Proxy configuration for Layer 3.5 deployment
  proxy:
    enabled: true
    use_env_vars: false  # Set to true to use environment variables instead
    http_proxy: "http://proxy.company.com:8080"
    https_proxy: "http://proxy.company.com:8080"
    no_proxy: "localhost,127.0.0.1,192.168.0.0/16,10.0.0.0/8,.internal"
```

### Method 3: Environment Variables

Set environment variables before starting the connector:

```bash
export HTTP_PROXY=http://proxy.company.com:8080
export HTTPS_PROXY=http://proxy.company.com:8080
export NO_PROXY=localhost,127.0.0.1,192.168.0.0/16,10.0.0.0/8,.internal

# Start connector
python -m unified_connector
```

Or in `config.yaml`:
```yaml
zerobus:
  proxy:
    enabled: true
    use_env_vars: true  # Will read from HTTP_PROXY/HTTPS_PROXY env vars
```

### Method 4: Docker Compose

Add to `docker-compose.yml`:

```yaml
services:
  unified-connector:
    image: unified-ot-zerobus-connector:latest
    environment:
      # Proxy configuration
      - HTTP_PROXY=http://proxy.company.com:8080
      - HTTPS_PROXY=http://proxy.company.com:8080
      - NO_PROXY=localhost,127.0.0.1,192.168.0.0/16,10.0.0.0/8,.internal

      # Credentials
      - CONNECTOR_MASTER_PASSWORD=your-secure-password
      - CONNECTOR_ZEROBUS_CLIENT_ID=your-client-id
      - CONNECTOR_ZEROBUS_CLIENT_SECRET=your-client-secret

    ports:
      - "8082:8082"

    networks:
      - ot-network  # Access to OT devices
      - dmz-network # Access to proxy
```

### Method 5: Kubernetes Deployment

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: unified-ot-connector
  namespace: ot-dmz
spec:
  replicas: 1
  template:
    spec:
      containers:
      - name: connector
        image: unified-ot-zerobus-connector:latest
        env:
        # Proxy configuration
        - name: HTTP_PROXY
          value: "http://proxy.company.com:8080"
        - name: HTTPS_PROXY
          value: "http://proxy.company.com:8080"
        - name: NO_PROXY
          value: "localhost,127.0.0.1,192.168.0.0/16,10.0.0.0/8,.cluster.local,.internal"

        # Credentials from secrets
        - name: CONNECTOR_MASTER_PASSWORD
          valueFrom:
            secretKeyRef:
              name: connector-secrets
              key: master-password
        - name: CONNECTOR_ZEROBUS_CLIENT_ID
          valueFrom:
            secretKeyRef:
              name: databricks-oauth
              key: client-id
        - name: CONNECTOR_ZEROBUS_CLIENT_SECRET
          valueFrom:
            secretKeyRef:
              name: databricks-oauth
              key: client-secret
```

## Proxy Patterns by Deployment

### Pattern 1: Explicit Proxy (Most Common)

Use when you have a specific proxy server:

```yaml
proxy:
  enabled: true
  use_env_vars: false
  http_proxy: "http://proxy.company.com:8080"
  https_proxy: "http://proxy.company.com:8080"
  no_proxy: "localhost,127.0.0.1,192.168.0.0/16"
```

### Pattern 2: Authenticated Proxy

For proxies requiring username/password:

```yaml
proxy:
  enabled: true
  use_env_vars: false
  http_proxy: "http://username:password@proxy.company.com:8080"
  https_proxy: "http://username:password@proxy.company.com:8080"
  no_proxy: "localhost,127.0.0.1"
```

Or via environment:
```bash
export HTTP_PROXY=http://username:password@proxy.company.com:8080
export HTTPS_PROXY=http://username:password@proxy.company.com:8080
```

### Pattern 3: Environment Variable Inheritance

For containerized environments where proxy is set at the host/orchestrator level:

```yaml
proxy:
  enabled: true
  use_env_vars: true  # Inherit HTTP_PROXY/HTTPS_PROXY from environment
```

### Pattern 4: No Proxy (Direct Connection)

For cloud-hosted or directly-connected deployments:

```yaml
proxy:
  enabled: false
```

## NO_PROXY Configuration

The `no_proxy` setting defines hosts that should bypass the proxy. This is critical for:

1. **Local OT devices** - Direct connection to PLCs, OPC-UA servers, etc.
2. **Local services** - Health checks, monitoring
3. **Internal domains** - Company-internal services

### Common NO_PROXY Patterns

```bash
# Minimal (loopback only)
NO_PROXY=localhost,127.0.0.1

# Include private networks
NO_PROXY=localhost,127.0.0.1,192.168.0.0/16,10.0.0.0/8,172.16.0.0/12

# Include internal domain
NO_PROXY=localhost,127.0.0.1,192.168.0.0/16,.internal,.company.local

# Kubernetes specific
NO_PROXY=localhost,127.0.0.1,192.168.0.0/16,.cluster.local,.svc
```

## Testing Proxy Configuration

### Test 1: Verify Proxy Settings

```bash
# Check environment variables
env | grep -i proxy

# Check connector logs
tail -f unified_connector.log | grep -i proxy
```

Expected output:
```
2025-01-31 10:00:00 INFO - HTTPS proxy configured: http://proxy.company.com:8080
2025-01-31 10:00:00 INFO - No proxy for: localhost,127.0.0.1,192.168.0.0/16
```

### Test 2: Test OT Device Connectivity (No Proxy)

```bash
# From connector host, test direct connection to OT device
curl -v opc.tcp://192.168.1.100:4840 2>&1 | grep -i proxy
# Should show: "No proxy configured" or direct connection
```

### Test 3: Test Databricks Connectivity (Through Proxy)

```bash
# Set proxy environment
export HTTPS_PROXY=http://proxy.company.com:8080

# Test workspace connection
curl -v https://your-workspace.cloud.databricks.com/api/2.0/clusters/list \
  -H "Authorization: Bearer $DATABRICKS_TOKEN" 2>&1 | grep -i proxy

# Expected: "Connected to proxy.company.com"
```

### Test 4: ZeroBus Diagnostics

Use the Web UI:
1. Navigate to **ZeroBus** section
2. Click **Diagnostics**
3. Check for:
   - ✅ Proxy configuration detected
   - ✅ Connection to workspace successful
   - ✅ Connection to ZeroBus endpoint successful

## Troubleshooting

### Issue: "Connection refused" to Databricks

**Cause**: Proxy not configured or incorrect proxy URL

**Solution**:
```yaml
proxy:
  enabled: true
  https_proxy: "http://proxy.company.com:8080"  # Verify URL and port
```

### Issue: "Connection timeout" to OT devices

**Cause**: OT device traffic incorrectly routed through proxy

**Solution**:
```yaml
proxy:
  no_proxy: "localhost,127.0.0.1,192.168.0.0/16,10.0.0.0/8"  # Add OT network ranges
```

### Issue: "407 Proxy Authentication Required"

**Cause**: Proxy requires credentials

**Solution**:
```yaml
proxy:
  https_proxy: "http://username:password@proxy.company.com:8080"
```

Or use environment variables to avoid storing credentials in config:
```bash
export HTTPS_PROXY=http://username:password@proxy.company.com:8080
```

### Issue: SSL certificate verification errors

**Cause**: Corporate proxy performs SSL inspection

**Solution**: Contact your IT team for the proxy CA certificate, then:

1. Add CA cert to system trust store, or
2. Configure the connector to trust the corporate CA (implementation dependent)

### Issue: Proxy works for workspace but not ZeroBus

**Cause**: ZeroBus uses gRPC over HTTPS, may need additional proxy config

**Solution**: Ensure proxy supports HTTP/2 and gRPC:
```yaml
proxy:
  https_proxy: "http://proxy.company.com:8080"
  # Some proxies require HTTP_PROXY for gRPC
  http_proxy: "http://proxy.company.com:8080"
```

## Security Considerations

### 1. Credential Storage

Never commit proxy credentials to version control:

```bash
# BAD
proxy:
  https_proxy: "http://admin:password123@proxy.company.com:8080"

# GOOD - Use environment variables
export HTTPS_PROXY=http://admin:password123@proxy.company.com:8080
```

### 2. Network Segmentation

Ensure the connector has minimal necessary access:
- **OT Network**: Read-only access to specific devices
- **DMZ Network**: Access to proxy only
- **No direct access**: Should not directly reach internet

### 3. Firewall Rules

```bash
# Connector → OT devices (direct, no proxy)
ALLOW tcp/4840 from connector to 192.168.0.0/16  # OPC-UA
ALLOW tcp/1883 from connector to 192.168.0.0/16  # MQTT
ALLOW tcp/502 from connector to 192.168.0.0/16   # Modbus

# Connector → Proxy (outbound to cloud)
ALLOW tcp/8080 from connector to proxy.company.com  # Proxy
DENY all from connector to 0.0.0.0/0  # Block direct internet

# Proxy → Databricks (outbound)
ALLOW tcp/443 from proxy to *.cloud.databricks.com  # HTTPS/gRPC
```

## References

- [Purdue Model for ICS/OT Security](https://en.wikipedia.org/wiki/Purdue_Enterprise_Reference_Architecture)
- [ISA-95 Standard](https://www.isa.org/standards-and-publications/isa-standards/isa-standards-committees/isa95)
- [Databricks ZeroBus Documentation](https://docs.databricks.com/ingestion/zerobus/)
- [Python Requests Proxy Documentation](https://requests.readthedocs.io/en/latest/user/advanced/#proxies)
