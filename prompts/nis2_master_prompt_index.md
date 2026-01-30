# NIS2 Compliance Implementation - Master Prompt Index

## Overview

This document provides the complete set of implementation prompts for making the Unified OT Zerobus Connector NIS2 compliant. Use these prompts with AI coding assistants (Claude, GitHub Copilot, etc.) to implement each phase systematically.

**Total Timeline**: 24 weeks (6 months)
**Total Effort**: 38-50 person-weeks
**Team Size**: 4-5 engineers + 1 security specialist

---

## Quick Start

### Prerequisites
1. **Docker installed** (connector always runs in Docker)
2. **Databricks default profile** configured in `~/.databrickscfg`
3. **OT simulators** ready (can run locally or in Docker/Colima)
4. **GitHub repository** with Actions enabled
5. **Corporate proxy** details (if applicable)
6. **OAuth2 provider** access (Azure AD, Okta, etc.)

### Environment Setup
```bash
# Clone repository
git clone https://github.com/pravinva/unified-ot-zerobus-connector
cd unified-ot-zerobus-connector

# Create .env file (never commit!)
cat > .env << EOF
OAUTH_CLIENT_ID=your-client-id
OAUTH_CLIENT_SECRET=your-client-secret
OAUTH_TENANT_ID=your-tenant-id
SESSION_SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")
CONNECTOR_MASTER_PASSWORD=your-secure-password
EOF

# Start development environment
docker-compose up -d
```

---

## Phase 1: Critical Security Controls (Weeks 1-6)

### Sprint 1.1: Web UI Authentication & Authorization (Weeks 1-3)

**Prompt Set**: See "Phase 1 Sprint 1.1 - Web UI Authentication" artifact

**Tasks**:
1. ✅ Implement OAuth2 authentication (2 weeks)
2. ✅ Add MFA support (1 week)
3. ✅ Implement RBAC (1 week)
4. ✅ Update Docker configuration (3 days)

**Key Deliverables**:
- OAuth2 login flow working
- 3 roles: admin, operator, viewer
- Permission checks on all API endpoints
- UI adapts to user role
- Works from Docker container

**Testing**:
```bash
# Test authentication
curl -I http://localhost:8082/api/sources  # Should redirect to login

# Test with valid token
curl -H "Cookie: session=..." http://localhost:8082/api/sources

# Test RBAC
curl -H "Cookie: viewer_session=..." -X DELETE http://localhost:8082/api/sources/test
# Should return 403 Forbidden
```

---

### Sprint 1.2: Security Testing Framework (Weeks 4-5)

**Prompt Set**: See "Phase 1 Sprint 1.2 - Security Testing Framework" artifact

**Tasks**:
1. ✅ Set up automated vulnerability scanning (1 week)
2. ✅ Create security unit tests (3 days)
3. ✅ Configure CI/CD security gates (2 days)

**Key Deliverables**:
- GitHub Actions security scanning workflow
- Dependency scanning (pip-audit, Safety)
- SAST (Bandit, Semgrep)
- Container scanning (Trivy)
- 20+ security unit tests
- 80%+ test coverage

**Testing**:
```bash
# Run security scans locally
pip install pip-audit bandit safety
pip-audit --requirement requirements.txt
bandit -r unified_connector/

# Run security tests
pytest tests/security/ -v --cov=unified_connector

# Check coverage
pytest --cov=unified_connector --cov-report=html
open htmlcov/index.html
```

---

### Sprint 1.3: Incident Response System (Week 6)

**Prompt Set**: See "Phase 1 Sprint 1.3 - SIEM Integration" artifact

**Tasks**:
1. ✅ Implement SIEM logging handler (4 days)
2. ✅ Add security event logging (2 days)
3. ✅ Configure alerting rules (1 day)

**Key Deliverables**:
- SIEM integration (syslog, HTTP, Splunk HEC)
- Security events in CEF/JSON format
- Alerting for critical events
- Event buffering for SIEM outages

**Testing**:
```bash
# Test SIEM connection
# Update config.yaml with SIEM details
docker-compose up

# Trigger security event
curl -X POST http://localhost:8082/api/auth/login \
  -d '{"username":"test","password":"wrong"}'

# Check SIEM received event
# Or check unified_connector.log
tail -f unified_connector.log | grep "event_type"
```

---

## Phase 2: Encryption & Secure Defaults (Weeks 7-10)

### Sprint 2.1: Default Encryption Configuration (Weeks 7-8)

**Prompt Set**: See "Phases 2-4" artifact, Task 1

**Tasks**:
1. ✅ Change OPC-UA defaults to SignAndEncrypt (1 week)
2. ✅ Add certificate generation utility (1.5 weeks)
3. ✅ Add certificate monitoring (3 days)
4. ✅ Add MQTT TLS support (3 days)

**Key Deliverables**:
- OPC-UA defaults to encrypted
- Certificate generation CLI
- Certificate expiry monitoring
- Web UI shows certificate status

**Usage**:
```bash
# Generate certificates
python -m unified_connector generate-certs \
    --output-dir ~/.unified_connector/certs \
    --common-name "Plant A Connector" \
    --validity-days 365

# Check certificate status
curl http://localhost:8082/api/certificates/status | jq
```

---

### Sprint 2.2: Certificate Management Automation (Weeks 9-10)

**Prompt Set**: See "Phases 2-4" artifact, includes automatic renewal

**Tasks**:
1. ✅ Implement certificate renewal logic (3 days)
2. ✅ Add certificate status to Web UI (2 days)
3. ✅ Integrate with Prometheus metrics (2 days)

**Key Deliverables**:
- Automatic certificate renewal
- Certificate expiry alerts
- Prometheus metrics for certificate health

---

## Phase 3: Supply Chain & Documentation (Weeks 11-16)

### Sprint 3.1: SBOM Generation (Weeks 11-12)

**Prompt Set**: See "Phases 2-4" artifact, SBOM section

**Tasks**:
1. ✅ Implement SBOM generation (1 week)
2. ✅ Automate in CI/CD (2 days)
3. ✅ Configure Dependabot (1 day)

**Key Deliverables**:
- SBOM in CycloneDX format
- SBOM signed with GPG
- Published with each release
- Dependabot configured

**Usage**:
```bash
# Generate SBOM locally
pip install cyclonedx-bom
cyclonedx-py --format json --output sbom.json --requirements requirements.txt

# Scan for vulnerabilities
grype sbom:sbom.json
```

---

### Sprint 3.2: Security Documentation (Weeks 13-14)

**Prompt Set**: See "Phases 2-4" artifact, Documentation section

**Tasks**:
1. ✅ Create SECURITY.md (2 days)
2. ✅ Create DEPLOYMENT_SECURITY.md (3 days)
3. ✅ Create SUPPLY_CHAIN_SECURITY.md (2 days)
4. ✅ Create INCIDENT_RESPONSE.md (2 days)
5. ✅ Update existing documentation (1 day)

**Key Deliverables**:
- 4 new security documents
- Deployment hardening guide
- Incident response procedures
- Supply chain security documentation

---

### Sprint 3.3: Training Materials (Weeks 15-16)

**Tasks**:
1. ✅ Create operator training (1 week)
2. ✅ Create administrator training (1 week)
3. ✅ Create security awareness materials (3 days)

**Key Deliverables**:
- Operator training guide
- Administrator training guide
- Security awareness materials
- Training completion tracking

---

## Phase 4: Testing, Audit & Certification (Weeks 17-24)

### Sprint 4.1: Security Assessment (Weeks 17-20)

**Prompt Set**: See "Phases 2-4" artifact, Audit section

**Tasks**:
1. ✅ External penetration testing (2 weeks)
2. ✅ Code security review (1 week)
3. ✅ Vulnerability assessment (1 week)

**Key Deliverables**:
- Penetration test report
- Code security review report
- Vulnerability assessment report

---

### Sprint 4.2: Gap Remediation (Weeks 21-22)

**Tasks**:
1. ✅ Fix critical/high findings (1 week)
2. ✅ Fix medium findings (1 week)
3. ✅ Re-test (3 days)

**Key Deliverables**:
- All critical/high vulnerabilities fixed
- 80%+ medium vulnerabilities fixed
- Re-test passed

---

### Sprint 4.3: NIS2 Audit & Certification (Weeks 23-24)

**Prompt Set**: See "Phases 2-4" artifact, Audit Checklist

**Tasks**:
1. ✅ Internal audit (1 week)
2. ✅ External certification (1 week)
3. ✅ Management sign-off (2 days)

**Key Deliverables**:
- NIS2 audit checklist completed (10/10)
- External certification (ISO 27001 or SOC 2)
- Management approval
- Compliance statement published

---

## Implementation Strategy

### Week-by-Week Plan

**Weeks 1-6**: Phase 1 - Critical Security
- Focus: Authentication, testing, SIEM
- Team: 3 engineers + 1 security specialist
- Checkpoint: Week 6 demo to stakeholders

**Weeks 7-10**: Phase 2 - Encryption
- Focus: OPC-UA encryption, certificates
- Team: 2 engineers
- Checkpoint: Week 10 encrypted connections verified

**Weeks 11-16**: Phase 3 - Documentation
- Focus: SBOM, security docs, training
- Team: 2 engineers + 1 technical writer
- Checkpoint: Week 16 all docs published

**Weeks 17-24**: Phase 4 - Audit
- Focus: Penetration testing, remediation, certification
- Team: Full team + external auditors
- Checkpoint: Week 24 NIS2 compliance achieved

---

## Docker & Networking Configuration

### Connector Always in Docker
```yaml
# docker-compose.yml
services:
  unified-connector:
    build: .
    container_name: unified-ot-connector
    ports:
      - "8082:8082"  # Web UI
      - "8081:8081"  # Health
      - "9090:9090"  # Metrics
    volumes:
      - ./config:/app/config
      - ./data:/app/data
      - ~/.databrickscfg:/root/.databrickscfg:ro
    environment:
      - OAUTH_CLIENT_ID=${OAUTH_CLIENT_ID}
      - OAUTH_CLIENT_SECRET=${OAUTH_CLIENT_SECRET}
      - SESSION_SECRET_KEY=${SESSION_SECRET_KEY}
      - CONNECTOR_MASTER_PASSWORD=${CONNECTOR_MASTER_PASSWORD}
    networks:
      - ot-network
    restart: unless-stopped
```

### OT Simulators - Two Options

**Option 1: Local Simulators**
```yaml
# config.yaml - Use host.docker.internal
sources:
  - name: local-opcua
    protocol: opcua
    endpoint: opc.tcp://host.docker.internal:4841
    enabled: true
```

**Option 2: Docker Simulators**
```yaml
# docker-compose.yml
services:
  ot-simulator:
    image: pravinva/ot-simulator:latest
    ports:
      - "4840:4840"
    networks:
      - ot-network

# config.yaml - Use service name
sources:
  - name: docker-opcua
    protocol: opcua
    endpoint: opc.tcp://ot-simulator:4840
    enabled: true
```

### Databricks Configuration

```yaml
# Uses default profile from ~/.databrickscfg
# Volume mount: ~/.databrickscfg:/root/.databrickscfg:ro

# config.yaml
zerobus:
  workspace_host: ${env:DATABRICKS_HOST}  # From databrickscfg
  auth:
    client_id: ${env:DATABRICKS_CLIENT_ID}
    client_secret: ${env:DATABRICKS_CLIENT_SECRET}
```

---

## Verification Commands

### Quick Health Check
```bash
#!/bin/bash
# nis2-health-check.sh

echo "=== NIS2 Compliance Health Check ==="

# 1. Authentication
curl -I http://localhost:8082/api/sources | grep "401\|302"
echo "✓ Authentication enforced"

# 2. RBAC
curl http://localhost:8082/api/auth/permissions | jq .permissions
echo "✓ RBAC configured"

# 3. Certificates
python -m unified_connector check-certs
echo "✓ Certificates valid"

# 4. SIEM
grep "SIEM integration enabled" unified_connector.log
echo "✓ SIEM connected"

# 5. Security tests
pytest tests/security/ -q
echo "✓ Security tests passing"

# 6. SBOM
ls -l sbom.json
echo "✓ SBOM generated"

# 7. Documentation
for doc in SECURITY DEPLOYMENT_SECURITY SUPPLY_CHAIN_SECURITY; do
    ls docs/${doc}.md || echo "❌ Missing ${doc}.md"
done
echo "✓ Documentation complete"

echo ""
echo "=== Overall Status ==="
echo "Review NIS2_AUDIT_CHECKLIST.md for detailed compliance status"
```

### Full Compliance Verification
```bash
# Run all checks
./nis2-health-check.sh

# Run security scans
.github/workflows/security-scan.yml  # Via GitHub Actions

# Check audit checklist
cat docs/NIS2_AUDIT_CHECKLIST.md | grep "\[ \]" | wc -l
# Should be 0 (all checkboxes checked)
```

---

## Troubleshooting

### Common Issues

**Issue**: OAuth redirect not working from Docker
```bash
# Solution: Use localhost in redirect_uri, not container hostname
redirect_uri: http://localhost:8082/login/callback
```

**Issue**: Connector can't reach local OT simulator
```bash
# Solution: Use host.docker.internal (Mac/Windows) or --network=host (Linux)
endpoint: opc.tcp://host.docker.internal:4841
```

**Issue**: Certificate generation fails
```bash
# Solution: Install cryptography package
pip install cryptography>=41.0.0
python -m unified_connector generate-certs
```

**Issue**: SIEM not receiving events
```bash
# Solution: Check SIEM configuration and network connectivity
docker-compose logs unified-connector | grep SIEM
telnet siem.company.com 514
```

---

## Success Criteria

### Phase 1 Complete When:
- [ ] No unauthenticated access to Web UI
- [ ] 3 RBAC roles working correctly
- [ ] Security scanning in CI/CD
- [ ] 20+ security tests passing (80%+ coverage)
- [ ] SIEM receiving security events

### Phase 2 Complete When:
- [ ] OPC-UA defaults to SignAndEncrypt
- [ ] Certificates auto-generated
- [ ] Certificate monitoring active
- [ ] MQTT TLS supported

### Phase 3 Complete When:
- [ ] SBOM generated for each release
- [ ] 4 security documents published
- [ ] Training materials available
- [ ] Dependabot configured

### Phase 4 Complete When:
- [ ] Penetration test passed
- [ ] All critical/high vulnerabilities fixed
- [ ] NIS2 audit checklist 10/10
- [ ] External certification achieved
- [ ] Management sign-off obtained

### Overall NIS2 Compliance When:
- [ ] All 10 Article 21.2 requirements met
- [ ] Zero critical vulnerabilities
- [ ] Documentation complete
- [ ] Training delivered
- [ ] External audit passed
- [ ] **🎉 NIS2 COMPLIANT 🎉**

---

## Next Steps

1. **Download all prompt artifacts** from this conversation
2. **Set up development environment** (Docker, .env, etc.)
3. **Start with Phase 1, Sprint 1.1** (Authentication)
4. **Use prompts with AI coding assistant** (Claude, Copilot)
5. **Test each component** before moving to next
6. **Schedule weekly checkpoints** with team
7. **Engage external security firm** for Phase 4

---

## Support & Resources

- **NIS2 Directive**: https://eur-lex.europa.eu/eli/dir/2022/2555
- **Purdue Model**: https://www.isa.org/standards-and-publications/isa-standards/isa-standards-committees/isa95
- **IEC 62443**: https://www.isa.org/standards-and-publications/isa-standards/isa-standards-committees/isa99
- **CycloneDX SBOM**: https://cyclonedx.org/

---

## Document Structure

All prompts are organized in downloadable artifacts:

1. **Phase 1 Sprint 1.1**: Authentication & Authorization
2. **Phase 1 Sprint 1.2**: Security Testing Framework
3. **Phase 1 Sprint 1.3**: SIEM Integration
4. **Phases 2-4**: Encryption, SBOM, Documentation, Audit
5. **This Document**: Master Index & Quick Start

Copy each artifact to a text file and use as implementation guide.

---

**Total Implementation Time**: 24 weeks
**Budget**: ~$500,000 (labor + external costs)
**ROI**: Avoid â‚¬10M+ NIS2 penalties + customer trust

**Let's make your connector NIS2 compliant! 🚀**
