# NIS2 Implementation - Phase 1, Sprint 1.2: Security Testing Framework

## Context
NIS2 Article 21.2(i) requires "regular testing, reviewing, and evaluating the effectiveness of security measures." Currently, there's no automated security testing.

## Target State
- Automated vulnerability scanning in CI/CD
- Security unit tests (80%+ coverage)
- SAST (Static Application Security Testing)
- Container scanning
- Dependency vulnerability monitoring

---

## Task 1: Set Up Automated Vulnerability Scanning

### Prompt for AI Assistant

```
Set up automated security scanning pipeline for the Unified OT Connector using GitHub Actions.

REQUIREMENTS:
1. Dependency vulnerability scanning (pip-audit, Safety)
2. SAST with Bandit and Semgrep
3. Container scanning with Trivy
4. Run on every PR and weekly schedule
5. Fail build on HIGH+ vulnerabilities
6. Generate security reports

CREATE .github/workflows/security-scan.yml:
```yaml
name: Security Scanning

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main, develop]
  schedule:
    - cron: '0 0 * * 1'  # Weekly on Monday at midnight UTC

permissions:
  contents: read
  security-events: write  # For uploading SARIF to GitHub Security tab

jobs:
  dependency-scan:
    name: Dependency Vulnerability Scan
    runs-on: ubuntu-latest
    steps:
      - name: Checkout code
        uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      
      - name: Install scanning tools
        run: |
          python -m pip install --upgrade pip
          pip install pip-audit safety
      
      - name: Run pip-audit
        run: |
          pip-audit --requirement requirements.txt \
            --format json \
            --output pip-audit-report.json || true
      
      - name: Run Safety check
        run: |
          safety check --json --output safety-report.json || true
      
      - name: Upload reports
        uses: actions/upload-artifact@v4
        with:
          name: dependency-scan-reports
          path: |
            pip-audit-report.json
            safety-report.json
      
      - name: Check for HIGH+ vulnerabilities
        run: |
          # Fail if HIGH or CRITICAL vulnerabilities found
          pip-audit --requirement requirements.txt --vulnerability-service osv --strict
  
  sast-scan:
    name: Static Application Security Testing
    runs-on: ubuntu-latest
    steps:
      - name: Checkout code
        uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      
      - name: Install dependencies for code analysis
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt
      
      - name: Install SAST tools
        run: |
          pip install bandit[toml] semgrep
      
      - name: Run Bandit
        run: |
          bandit -r unified_connector/ \
            -f json \
            -o bandit-report.json \
            --severity-level high \
            --confidence-level medium || true
      
      - name: Run Semgrep
        run: |
          semgrep --config auto unified_connector/ \
            --json \
            --output semgrep-report.json \
            --severity ERROR \
            --severity WARNING || true
      
      - name: Upload Bandit results to GitHub Security
        uses: github/codeql-action/upload-sarif@v3
        if: always()
        with:
          sarif_file: bandit-report.json
          category: bandit
      
      - name: Upload SAST reports
        uses: actions/upload-artifact@v4
        if: always()
        with:
          name: sast-reports
          path: |
            bandit-report.json
            semgrep-report.json
      
      - name: Check for critical issues
        run: |
          # Parse reports and fail if critical issues found
          python .github/scripts/check_sast_results.py
  
  container-scan:
    name: Container Security Scan
    runs-on: ubuntu-latest
    if: github.event_name == 'push' || github.event_name == 'schedule'
    steps:
      - name: Checkout code
        uses: actions/checkout@v4
      
      - name: Build Docker image
        run: |
          docker build -t unified-ot-connector:${{ github.sha }} .
      
      - name: Run Trivy scan
        uses: aquasecurity/trivy-action@master
        with:
          image-ref: 'unified-ot-connector:${{ github.sha }}'
          format: 'sarif'
          output: 'trivy-results.sarif'
          severity: 'HIGH,CRITICAL'
          exit-code: '1'  # Fail on HIGH+ vulnerabilities
      
      - name: Upload Trivy results to GitHub Security
        uses: github/codeql-action/upload-sarif@v3
        if: always()
        with:
          sarif_file: 'trivy-results.sarif'
          category: trivy
      
      - name: Generate container SBOM
        uses: aquasecurity/trivy-action@master
        with:
          image-ref: 'unified-ot-connector:${{ github.sha }}'
          format: 'cyclonedx'
          output: 'container-sbom.json'
      
      - name: Upload container SBOM
        uses: actions/upload-artifact@v4
        with:
          name: container-sbom
          path: container-sbom.json
  
  security-summary:
    name: Security Scan Summary
    runs-on: ubuntu-latest
    needs: [dependency-scan, sast-scan]
    if: always()
    steps:
      - name: Download all reports
        uses: actions/download-artifact@v4
      
      - name: Generate summary
        run: |
          echo "## Security Scan Summary" >> $GITHUB_STEP_SUMMARY
          echo "" >> $GITHUB_STEP_SUMMARY
          
          # Parse and summarize results
          python .github/scripts/security_summary.py >> $GITHUB_STEP_SUMMARY
```

CREATE .github/scripts/check_sast_results.py:
```python
#!/usr/bin/env python3
import json
import sys

def check_bandit_results():
    """Check Bandit results for critical issues"""
    try:
        with open('bandit-report.json', 'r') as f:
            data = json.load(f)
        
        high_issues = [r for r in data.get('results', []) if r['issue_severity'] == 'HIGH']
        critical_issues = [r for r in data.get('results', []) if r['issue_severity'] == 'CRITICAL']
        
        if critical_issues:
            print(f"❌ CRITICAL: Found {len(critical_issues)} critical security issues")
            for issue in critical_issues:
                print(f"  - {issue['test_id']}: {issue['issue_text']} ({issue['filename']}:{issue['line_number']})")
            return False
        
        if high_issues:
            print(f"⚠️  WARNING: Found {len(high_issues)} high severity issues")
            for issue in high_issues:
                print(f"  - {issue['test_id']}: {issue['issue_text']} ({issue['filename']}:{issue['line_number']})")
        
        print(f"✅ Bandit scan passed: {len(high_issues)} high, {len(critical_issues)} critical issues")
        return True
    
    except FileNotFoundError:
        print("❌ Bandit report not found")
        return False
    except Exception as e:
        print(f"❌ Error checking Bandit results: {e}")
        return False

def check_semgrep_results():
    """Check Semgrep results for errors"""
    try:
        with open('semgrep-report.json', 'r') as f:
            data = json.load(f)
        
        errors = [r for r in data.get('results', []) if r.get('extra', {}).get('severity') == 'ERROR']
        
        if errors:
            print(f"❌ CRITICAL: Found {len(errors)} Semgrep errors")
            for error in errors:
                print(f"  - {error['check_id']}: {error['extra']['message']} ({error['path']}:{error['start']['line']})")
            return False
        
        warnings = [r for r in data.get('results', []) if r.get('extra', {}).get('severity') == 'WARNING']
        if warnings:
            print(f"⚠️  WARNING: Found {len(warnings)} Semgrep warnings")
        
        print(f"✅ Semgrep scan passed: {len(warnings)} warnings, {len(errors)} errors")
        return True
    
    except FileNotFoundError:
        print("❌ Semgrep report not found")
        return False
    except Exception as e:
        print(f"❌ Error checking Semgrep results: {e}")
        return False

if __name__ == '__main__':
    bandit_ok = check_bandit_results()
    semgrep_ok = check_semgrep_results()
    
    if not (bandit_ok and semgrep_ok):
        sys.exit(1)
```

CREATE .bandit configuration:
```toml
# .bandit
[bandit]
exclude_dirs = ["/test", "/venv", "/.venv"]
tests = [
    "B201",  # flask_debug_true
    "B301",  # pickle
    "B302",  # marshal
    "B303",  # md5
    "B304",  # ciphers
    "B305",  # cipher_modes
    "B306",  # mktemp_q
    "B307",  # eval
    "B308",  # mark_safe
    "B309",  # httpsconnection
    "B310",  # urllib_urlopen
    "B311",  # random
    "B312",  # telnetlib
    "B313",  # xml_bad_cElementTree
    "B314",  # xml_bad_ElementTree
    "B315",  # xml_bad_expatreader
    "B316",  # xml_bad_expatbuilder
    "B317",  # xml_bad_sax
    "B318",  # xml_bad_minidom
    "B319",  # xml_bad_pulldom
    "B320",  # xml_bad_etree
    "B321",  # ftplib
    "B323",  # unverified_context
    "B324",  # hashlib
    "B325",  # tempnam
    "B401",  # import_telnetlib
    "B402",  # import_ftplib
    "B403",  # import_pickle
    "B404",  # import_subprocess
    "B405",  # import_xml_etree
    "B406",  # import_xml_sax
    "B407",  # import_xml_expat
    "B408",  # import_xml_minidom
    "B409",  # import_xml_pulldom
    "B410",  # import_lxml
    "B411",  # import_xmlrpclib
    "B412",  # import_httpoxy
    "B501",  # request_with_no_cert_validation
    "B502",  # ssl_with_bad_version
    "B503",  # ssl_with_bad_defaults
    "B504",  # ssl_with_no_version
    "B505",  # weak_cryptographic_key
    "B506",  # yaml_load
    "B507",  # ssh_no_host_key_verification
    "B601",  # paramiko_calls
    "B602",  # shell_equals_true
    "B603",  # subprocess_without_shell_equals_true
    "B604",  # any_other_function_with_shell_equals_true
    "B605",  # start_process_with_a_shell
    "B606",  # start_process_with_no_shell
    "B607",  # start_process_with_partial_path
    "B608",  # hardcoded_sql_expressions
    "B609",  # linux_commands_wildcard_injection
    "B610",  # django_extra_used
    "B611",  # django_rawsql_used
    "B701",  # jinja2_autoescape_false
    "B702",  # use_of_mako_templates
    "B703",  # django_mark_safe
]

# Set severity threshold
severity = "HIGH"
confidence = "MEDIUM"
```

CREATE .semgrep.yml:
```yaml
rules:
  - id: hardcoded-credentials
    pattern: |
      $VAR = "$...PASSWORD..."
    message: "Hardcoded credentials detected"
    severity: ERROR
    languages: [python]
  
  - id: sql-injection
    pattern: |
      execute($...{$USER_INPUT}...)
    message: "Potential SQL injection"
    severity: ERROR
    languages: [python]
  
  - id: command-injection
    pattern: |
      os.system($USER_INPUT)
    message: "Command injection vulnerability"
    severity: ERROR
    languages: [python]
  
  - id: insecure-random
    pattern: |
      random.$METHOD(...)
    message: "Use secrets module for security-sensitive randomness"
    severity: WARNING
    languages: [python]
```

TESTING:
1. Push to branch and verify workflow runs
2. Check GitHub Security tab for findings
3. Test that HIGH vulnerabilities fail the build
4. Download and review security reports

Implement complete automated security scanning pipeline.
```

---

## Task 2: Create Security Unit Tests

### Prompt for AI Assistant

```
Create comprehensive security unit tests for the Unified OT Connector.

REQUIREMENTS:
1. Test authentication/authorization
2. Test input validation
3. Test credential encryption
4. Test no secrets in logs
5. 80%+ coverage for security-critical code

CREATE tests/security/ directory structure:
```
tests/
├── security/
│   ├── __init__.py
│   ├── test_authentication.py
│   ├── test_authorization.py
│   ├── test_credential_security.py
│   ├── test_input_validation.py
│   └── conftest.py  # Shared fixtures
```

CREATE tests/security/conftest.py:
```python
import pytest
from aiohttp.test_utils import TestClient, TestServer
from unittest.mock import Mock, AsyncMock, patch
from unified_connector.web.web_server import WebServer
from unified_connector.web.rbac import User, Role

@pytest.fixture
async def app():
    """Create test application"""
    web_server = WebServer(config={
        'web_ui': {
            'host': '0.0.0.0',
            'port': 8082,
            'authentication': {
                'enabled': True,
                'require_mfa': False,
                'rbac': {'enabled': True}
            }
        }
    })
    return web_server.app

@pytest.fixture
async def app_client(app, aiohttp_client):
    """Create test client (unauthenticated)"""
    return await aiohttp_client(app)

@pytest.fixture
async def mock_admin_user():
    """Mock admin user"""
    return User(
        email='admin@example.com',
        groups=['OT-Admins'],
        role_mappings={'OT-Admins': 'admin'},
        default_role='viewer'
    )

@pytest.fixture
async def mock_operator_user():
    """Mock operator user"""
    return User(
        email='operator@example.com',
        groups=['OT-Operators'],
        role_mappings={'OT-Operators': 'operator'},
        default_role='viewer'
    )

@pytest.fixture
async def mock_viewer_user():
    """Mock viewer user"""
    return User(
        email='viewer@example.com',
        groups=['OT-Viewers'],
        role_mappings={'OT-Viewers': 'viewer'},
        default_role='viewer'
    )

@pytest.fixture
async def app_client_admin(app, aiohttp_client, mock_admin_user):
    """Create authenticated test client (admin)"""
    async def create_client():
        client = await aiohttp_client(app)
        # Mock session with admin user
        with patch('aiohttp_security.authorized_userid', return_value=mock_admin_user):
            yield client
    return create_client()

@pytest.fixture
async def app_client_operator(app, aiohttp_client, mock_operator_user):
    """Create authenticated test client (operator)"""
    async def create_client():
        client = await aiohttp_client(app)
        with patch('aiohttp_security.authorized_userid', return_value=mock_operator_user):
            yield client
    return create_client()

@pytest.fixture
async def app_client_viewer(app, aiohttp_client, mock_viewer_user):
    """Create authenticated test client (viewer)"""
    async def create_client():
        client = await aiohttp_client(app)
        with patch('aiohttp_security.authorized_userid', return_value=mock_viewer_user):
            yield client
    return create_client()
```

CREATE tests/security/test_authentication.py:
```python
import pytest
from aiohttp import web

@pytest.mark.asyncio
async def test_unauthenticated_access_denied(app_client):
    """Test that unauthenticated users cannot access API"""
    resp = await app_client.get('/api/sources')
    assert resp.status == 401, "Unauthenticated access should be denied"

@pytest.mark.asyncio
async def test_health_endpoint_no_auth(app_client):
    """Test that health endpoint doesn't require auth"""
    resp = await app_client.get('/health')
    assert resp.status == 200, "Health endpoint should be public"

@pytest.mark.asyncio
async def test_login_page_accessible(app_client):
    """Test that login page is accessible"""
    resp = await app_client.get('/login')
    assert resp.status in [200, 302], "Login page should be accessible"

@pytest.mark.asyncio
async def test_session_persistence(app_client_admin):
    """Test that session persists across requests"""
    # First request
    resp1 = await app_client_admin.get('/api/auth/status')
    assert resp1.status == 200
    
    # Second request should use same session
    resp2 = await app_client_admin.get('/api/sources')
    assert resp2.status == 200

@pytest.mark.asyncio
async def test_logout_clears_session(app_client_admin):
    """Test that logout clears session"""
    # Login successful
    resp1 = await app_client_admin.get('/api/auth/status')
    assert resp1.status == 200
    
    # Logout
    resp2 = await app_client_admin.post('/logout')
    assert resp2.status in [200, 302]
    
    # Subsequent request should fail
    resp3 = await app_client_admin.get('/api/sources')
    assert resp3.status == 401

@pytest.mark.asyncio
async def test_mfa_enforcement(app, aiohttp_client):
    """Test MFA enforcement when enabled"""
    # Enable MFA in config
    app['config']['web_ui']['authentication']['require_mfa'] = True
    
    client = await aiohttp_client(app)
    
    # Attempt login without MFA claim
    with patch('unified_connector.web.auth.AuthenticationManager.check_mfa_status', return_value=False):
        resp = await client.get('/login/callback', params={'code': 'test_code'})
        assert resp.status == 403, "Should deny access without MFA"
```

CREATE tests/security/test_authorization.py:
```python
import pytest
from aiohttp import web

@pytest.mark.asyncio
async def test_admin_full_access(app_client_admin):
    """Test admin has full access"""
    # Can read
    resp = await app_client_admin.get('/api/sources')
    assert resp.status == 200
    
    # Can write
    resp = await app_client_admin.post('/api/sources', json={'name': 'test'})
    assert resp.status in [200, 201, 400]  # Not 403
    
    # Can configure
    resp = await app_client_admin.post('/api/zerobus/config', json={})
    assert resp.status in [200, 400]  # Not 403
    
    # Can delete
    resp = await app_client_admin.delete('/api/sources/test')
    assert resp.status in [200, 404]  # Not 403

@pytest.mark.asyncio
async def test_operator_limited_access(app_client_operator):
    """Test operator has limited access"""
    # Can read
    resp = await app_client_operator.get('/api/sources')
    assert resp.status == 200
    
    # Can write
    resp = await app_client_operator.post('/api/sources', json={'name': 'test'})
    assert resp.status in [200, 201, 400]  # Not 403
    
    # Cannot configure
    resp = await app_client_operator.post('/api/zerobus/config', json={})
    assert resp.status == 403, "Operator should not configure"
    
    # Cannot delete
    resp = await app_client_operator.delete('/api/sources/test')
    assert resp.status == 403, "Operator should not delete"

@pytest.mark.asyncio
async def test_viewer_read_only(app_client_viewer):
    """Test viewer has read-only access"""
    # Can read
    resp = await app_client_viewer.get('/api/sources')
    assert resp.status == 200
    
    # Cannot write
    resp = await app_client_viewer.post('/api/sources', json={'name': 'test'})
    assert resp.status == 403, "Viewer should not write"
    
    # Cannot configure
    resp = await app_client_viewer.post('/api/zerobus/config', json={})
    assert resp.status == 403, "Viewer should not configure"
    
    # Cannot delete
    resp = await app_client_viewer.delete('/api/sources/test')
    assert resp.status == 403, "Viewer should not delete"

@pytest.mark.asyncio
async def test_permission_audit_logging(app_client_operator, caplog):
    """Test that permission denials are logged"""
    # Attempt unauthorized action
    resp = await app_client_operator.post('/api/zerobus/config', json={})
    assert resp.status == 403
    
    # Check audit log
    assert any('Permission denied' in record.message for record in caplog.records)
    assert any('configure' in record.message for record in caplog.records)
```

CREATE tests/security/test_credential_security.py:
```python
import pytest
from pathlib import Path
import json
from unified_connector.core.credential_manager import CredentialManager

@pytest.mark.asyncio
async def test_credentials_encrypted_at_rest():
    """Test that credentials are encrypted on disk"""
    cred_manager = CredentialManager()
    
    # Store a secret
    cred_manager.update_credential('test.secret', 'supersecret123')
    
    # Read raw file
    cred_file = Path('~/.unified_connector/credentials.enc').expanduser()
    raw_content = cred_file.read_bytes()
    
    # Should NOT contain plaintext
    assert b'supersecret123' not in raw_content, "Credentials leaked in plaintext!"

@pytest.mark.asyncio
async def test_credentials_not_in_logs(app, caplog):
    """Test that secrets never appear in logs"""
    # Trigger some operations
    await app.startup()
    
    # Check logs don't contain secrets
    sensitive_patterns = ['password', 'secret', 'token', 'client_secret', 'api_key']
    for record in caplog.records:
        msg = record.message.lower()
        for pattern in sensitive_patterns:
            if pattern in msg:
                # Should only be in context, not actual values
                assert not any(char.isalnum() for char in msg.split(pattern)[1][:20])

@pytest.mark.asyncio
async def test_credentials_not_in_api_responses(app_client_admin):
    """Test that API responses don't leak credentials"""
    # Get configuration
    resp = await app_client_admin.get('/api/config')
    data = await resp.json()
    
    # Convert to string and check
    config_str = json.dumps(data).lower()
    assert 'client_secret' not in config_str
    assert 'password' not in config_str or '${credential:' in config_str

@pytest.mark.asyncio
async def test_master_password_required():
    """Test that master password is required for credential access"""
    # Without master password
    with pytest.raises(Exception):
        cred_manager = CredentialManager(master_password=None)
        cred_manager.get_credential('test.secret')
```

CREATE tests/security/test_input_validation.py:
```python
import pytest
from aiohttp import web

@pytest.mark.asyncio
async def test_sql_injection_protection(app_client_admin):
    """Test protection against SQL injection"""
    malicious_input = "'; DROP TABLE sources; --"
    
    resp = await app_client_admin.post('/api/sources', json={
        'name': malicious_input,
        'protocol': 'opcua',
        'endpoint': 'opc.tcp://test:4840'
    })
    
    # Should sanitize input, not crash
    assert resp.status in [200, 400], "Should handle malicious input gracefully"

@pytest.mark.asyncio
async def test_command_injection_protection(app_client_admin):
    """Test protection against command injection"""
    malicious_endpoint = "opc.tcp://test:4840; rm -rf /"
    
    resp = await app_client_admin.post('/api/discovery/test', json={
        'protocol': 'opcua',
        'endpoint': malicious_endpoint
    })
    
    # Should reject invalid endpoint format
    assert resp.status == 400, "Should reject malicious endpoint"

@pytest.mark.asyncio
async def test_path_traversal_protection(app_client_admin):
    """Test protection against path traversal"""
    malicious_path = "../../etc/passwd"
    
    resp = await app_client_admin.get(f'/api/files/{malicious_path}')
    
    # Should not access parent directories
    assert resp.status in [400, 404], "Should prevent path traversal"

@pytest.mark.asyncio
async def test_xxe_protection(app_client_admin):
    """Test protection against XXE (XML External Entity) attacks"""
    malicious_xml = """<?xml version="1.0"?>
    <!DOCTYPE foo [<!ENTITY xxe SYSTEM "file:///etc/passwd">]>
    <foo>&xxe;</foo>"""
    
    resp = await app_client_admin.post('/api/import', data=malicious_xml, headers={'Content-Type': 'application/xml'})
    
    # Should reject or sanitize XML
    assert resp.status in [400, 415], "Should prevent XXE attacks"

@pytest.mark.asyncio
async def test_excessive_input_size(app_client_admin):
    """Test protection against excessive input"""
    huge_input = "A" * 10_000_000  # 10MB
    
    resp = await app_client_admin.post('/api/sources', json={
        'name': huge_input,
        'protocol': 'opcua',
        'endpoint': 'opc.tcp://test:4840'
    })
    
    # Should reject or truncate
    assert resp.status in [400, 413], "Should limit input size"
```

UPDATE pytest configuration (pytest.ini):
```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
asyncio_mode = auto

# Coverage settings
addopts =
    --cov=unified_connector
    --cov-report=html
    --cov-report=term-missing
    --cov-report=json
    --cov-fail-under=80

# Markers
markers =
    security: Security-related tests
    slow: Slow-running tests
    integration: Integration tests
```

UPDATE requirements.txt (add test dependencies):
```
pytest>=7.4.0
pytest-asyncio>=0.21.0
pytest-aiohttp>=1.0.5
pytest-cov>=4.1.0
pytest-mock>=3.11.1
```

RUN TESTS:
```bash
# Run all security tests
pytest tests/security/ -v

# Run with coverage
pytest tests/security/ --cov=unified_connector --cov-report=html

# Run specific test
pytest tests/security/test_authentication.py::test_unauthenticated_access_denied -v
```

CI/CD INTEGRATION (.github/workflows/test.yml):
```yaml
name: Unit Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pytest pytest-asyncio pytest-aiohttp pytest-cov
      
      - name: Run security tests
        run: |
          pytest tests/security/ -v \
            --cov=unified_connector \
            --cov-report=html \
            --cov-report=json \
            --cov-report=term
      
      - name: Check security test coverage
        run: |
          python -c "
          import json
          with open('coverage.json') as f:
              cov = json.load(f)
              if cov['totals']['percent_covered'] < 80:
                  raise Exception(f\"Security test coverage below 80%: {cov['totals']['percent_covered']}%\")
          "
      
      - name: Upload coverage report
        uses: actions/upload-artifact@v4
        with:
          name: coverage-report
          path: htmlcov/
```

Implement complete security test suite with 80%+ coverage.
```

---

## Verification Checklist

After completing Sprint 1.2:

- [ ] GitHub Actions workflow for security scanning
- [ ] Dependency scanning (pip-audit, Safety)
- [ ] SAST scanning (Bandit, Semgrep)
- [ ] Container scanning (Trivy)
- [ ] Security unit tests (20+ tests)
- [ ] 80%+ coverage for security code
- [ ] Tests run in CI/CD
- [ ] Build fails on HIGH+ vulnerabilities
- [ ] Security reports uploaded to GitHub Security tab

---

## Success Criteria

✅ Sprint 1.2 Complete When:
1. Automated security scans run weekly
2. All HIGH+ vulnerabilities identified
3. 20+ security unit tests passing
4. 80%+ coverage for authentication/authorization code
5. CI/CD fails on critical security issues
6. Security reports available in GitHub Security tab
