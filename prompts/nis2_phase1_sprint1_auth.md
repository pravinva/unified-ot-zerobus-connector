# NIS2 Implementation - Phase 1, Sprint 1.1: Web UI Authentication & Authorization

## Context
The Unified OT Zerobus Connector currently has no authentication on its Web UI (port 8082). This is a CRITICAL NIS2 compliance gap (Article 21.2g - Access Control).

## Current State
- Web UI accessible at http://localhost:8082 without authentication
- No session management
- No user roles or permissions
- Anyone on the network can view/modify configuration

## Target State
- OAuth2/SAML authentication enforced
- MFA required for all users
- 3 RBAC roles: admin, operator, viewer
- All API endpoints protected
- Audit logging for privileged operations

## Deployment Environment
- **Connector**: Always runs in Docker container
- **OT Simulators**: Can run locally or in Docker/Colima
- **Networking**: Connector must reach local and Docker-based simulators
- **Databricks**: Use default profile from `~/.databrickscfg` (field engineering workspace)

---

## Task 1: Implement OAuth2 Authentication

### Prompt for AI Assistant

```
I need to add OAuth2 authentication to the aiohttp web server in the Unified OT Zerobus Connector.

CURRENT CODE:
- Web server in unified_connector/web/web_server.py (aiohttp)
- Routes defined in setup_routes()
- No authentication currently

REQUIREMENTS:
1. Add OAuth2 authentication using aiohttp_security + authlib
2. Support Azure AD as primary IdP (configurable for others)
3. Session management with encrypted cookies
4. Login/logout flows with callback handling
5. Protect all /api/* endpoints (except /health)
6. Allow unauthenticated access to login pages

CONFIGURATION (config.yaml):
```yaml
web_ui:
  authentication:
    enabled: true
    method: oauth2
    oauth:
      provider: azure  # or okta, google
      client_id: ${env:OAUTH_CLIENT_ID}
      client_secret: ${env:OAUTH_CLIENT_SECRET}
      tenant_id: ${env:OAUTH_TENANT_ID}  # For Azure AD
      redirect_uri: http://localhost:8082/login/callback
      scopes: [openid, email, profile]
    session:
      secret_key: ${env:SESSION_SECRET_KEY}
      max_age_seconds: 28800  # 8 hours
```

IMPLEMENTATION:
1. Create unified_connector/web/auth.py with:
   - AuthenticationManager class
   - OAuth2 setup (using authlib)
   - Session setup (aiohttp_session with EncryptedCookieStorage)
   - Login/logout handlers
   - Callback handler

2. Add authentication middleware to web_server.py:
   - Check session for all protected routes
   - Allow public endpoints: /login, /login/callback, /health, /static/*
   - Return 401 Unauthorized if not authenticated
   - Redirect to /login for browser requests

3. Add routes:
   - GET /login - Redirect to OAuth provider
   - GET /login/callback - Handle OAuth callback
   - POST /logout - Clear session and redirect
   - GET /api/auth/status - Return current user info

4. Update Web UI (unified_connector/web/static/):
   - Add login.html page
   - Add logout button to index.html
   - Show current user in header
   - Handle 401 responses (redirect to login)

5. Update requirements.txt:
   - authlib>=1.3.0
   - aiohttp-security>=0.4.0
   - aiohttp-session>=2.12.0
   - cryptography>=41.0.0

TESTING:
- Test unauthenticated access is blocked
- Test OAuth login flow
- Test session persistence
- Test logout
- Test token refresh

DOCKER CONSIDERATION:
- OAuth redirect URI must work from Docker container
- Use http://localhost:8082 (not container hostname)
- Allow configuration via environment variables

Implement this complete authentication system. Use proper error handling and logging.
```

---

## Task 2: Add Multi-Factor Authentication (MFA) Support

### Prompt for AI Assistant

```
Add MFA enforcement to the OAuth2 authentication system.

CONTEXT:
OAuth2 authentication is now implemented. Need to verify that users have completed MFA at the IdP level before granting access.

APPROACH:
Use delegated MFA (IdP handles MFA, we verify the claim in the token)

REQUIREMENTS:
1. Check for MFA claim in OAuth2 token
2. Reject authentication if MFA not completed
3. Make MFA enforcement configurable
4. Log MFA status for audit

CONFIGURATION (config.yaml):
```yaml
web_ui:
  authentication:
    require_mfa: true
    mfa:
      claim_name: amr  # Authentication Methods Reference
      required_methods: [mfa, otp, duo]  # At least one required
```

IMPLEMENTATION:
1. Update unified_connector/web/auth.py:
   - Add check_mfa_status() method to AuthenticationManager
   - Verify token contains MFA claim after OAuth callback
   - Raise HTTPForbidden if MFA not satisfied

2. Add to callback handler:
   ```python
   async def handle_oauth_callback(self, request):
       # ... existing token exchange ...
       
       # Check MFA
       if self.require_mfa:
           mfa_satisfied = self.check_mfa_status(token)
           if not mfa_satisfied:
               logger.warning(f"MFA not satisfied for user {user_email}")
               raise web.HTTPForbidden(reason="Multi-factor authentication required")
       
       # ... create session ...
   ```

3. Log MFA events:
   ```python
   logger.info(f"User {user_email} authenticated with MFA: {mfa_methods}")
   logger.warning(f"User {user_email} attempted login without MFA")
   ```

4. Show MFA status in Web UI:
   - Update /api/auth/status to include mfa_completed boolean
   - Display in UI header (e.g., "🔒 MFA Enabled")

TESTING:
- Test with MFA-enabled user (should succeed)
- Test with non-MFA user (should fail)
- Test with MFA disabled in config (should allow)
- Verify audit logs contain MFA status

Implement MFA verification with proper error handling and user feedback.
```

---

## Task 3: Implement Role-Based Access Control (RBAC)

### Prompt for AI Assistant

```
Add RBAC system with 3 roles: admin, operator, viewer

CURRENT STATE:
Authentication is implemented, but all authenticated users have same permissions.

TARGET STATE:
- 3 roles with different permissions
- Map IdP groups to roles
- Permission checks on all API endpoints
- UI adapts to user's role

ROLES & PERMISSIONS:
```yaml
web_ui:
  rbac:
    enabled: true
    roles:
      admin:
        permissions: [read, write, configure, manage_users, start_stop, delete]
        description: "Full system access"
      operator:
        permissions: [read, write, start_stop]
        description: "Can view and control sources"
      viewer:
        permissions: [read]
        description: "Read-only access"
    
    # Map OAuth groups to roles
    role_mappings:
      "OT-Admins": admin
      "OT-Operators": operator
      "OT-Viewers": viewer
    
    # Default role for authenticated users not in any group
    default_role: viewer
```

IMPLEMENTATION:

1. Create unified_connector/web/rbac.py:
```python
from enum import Enum
from functools import wraps
from aiohttp import web

class Permission(Enum):
    READ = "read"
    WRITE = "write"
    CONFIGURE = "configure"
    MANAGE_USERS = "manage_users"
    START_STOP = "start_stop"
    DELETE = "delete"

class Role(Enum):
    ADMIN = "admin"
    OPERATOR = "operator"
    VIEWER = "viewer"

ROLE_PERMISSIONS = {
    Role.ADMIN: [Permission.READ, Permission.WRITE, Permission.CONFIGURE, 
                 Permission.MANAGE_USERS, Permission.START_STOP, Permission.DELETE],
    Role.OPERATOR: [Permission.READ, Permission.WRITE, Permission.START_STOP],
    Role.VIEWER: [Permission.READ],
}

class User:
    def __init__(self, email, groups, role_mappings, default_role):
        self.email = email
        self.groups = groups
        self.role = self._determine_role(groups, role_mappings, default_role)
    
    def _determine_role(self, groups, role_mappings, default_role):
        # Check groups against role_mappings
        for group in groups:
            if group in role_mappings:
                return Role[role_mappings[group].upper()]
        return Role[default_role.upper()]
    
    def has_permission(self, permission: Permission) -> bool:
        return permission in ROLE_PERMISSIONS[self.role]

def require_permission(permission: Permission):
    """Decorator to enforce permission on route handlers"""
    def decorator(handler):
        @wraps(handler)
        async def wrapper(self, request):
            user = request.get('user')
            if not user:
                raise web.HTTPUnauthorized()
            
            if not user.has_permission(permission):
                logger.warning(f"Permission denied: {user.email} lacks {permission.value}")
                raise web.HTTPForbidden(reason=f"Permission '{permission.value}' required")
            
            return await handler(self, request)
        return wrapper
    return decorator
```

2. Update unified_connector/web/auth.py:
   - Extract groups from OAuth token (e.g., token['groups'])
   - Create User object with role mapping
   - Store User in session

3. Update unified_connector/web/web_server.py:
   - Add @require_permission decorators to all API handlers:
   
```python
from unified_connector.web.rbac import require_permission, Permission

@require_permission(Permission.READ)
async def get_sources(self, request):
    # Anyone can read sources
    ...

@require_permission(Permission.WRITE)
async def update_source(self, request):
    # Only admin/operator can modify
    ...

@require_permission(Permission.CONFIGURE)
async def update_zerobus_config(self, request):
    # Only admin can configure
    ...

@require_permission(Permission.START_STOP)
async def start_source(self, request):
    # Admin/operator can start/stop
    ...

@require_permission(Permission.DELETE)
async def delete_source(self, request):
    # Only admin can delete
    ...
```

4. Add GET /api/auth/permissions endpoint:
```python
async def get_user_permissions(self, request):
    user = request['user']
    return web.json_response({
        'email': user.email,
        'role': user.role.value,
        'permissions': [p.value for p in ROLE_PERMISSIONS[user.role]]
    })
```

5. Update Web UI JavaScript (unified_connector/web/static/app.js):
```javascript
// Load user permissions on page load
let userPermissions = [];

async function loadUserPermissions() {
    const response = await apiFetch('/api/auth/permissions');
    const data = await response.json();
    userPermissions = data.permissions;
    updateUIForPermissions();
}

function updateUIForPermissions() {
    // Hide/disable elements based on permissions
    if (!userPermissions.includes('write')) {
        document.querySelectorAll('.btn-edit').forEach(btn => {
            btn.disabled = true;
            btn.title = "You don't have permission to edit";
        });
    }
    
    if (!userPermissions.includes('configure')) {
        document.getElementById('btnSaveZerobus').style.display = 'none';
    }
    
    if (!userPermissions.includes('start_stop')) {
        document.querySelectorAll('.btn-start, .btn-stop').forEach(btn => {
            btn.disabled = true;
        });
    }
    
    if (!userPermissions.includes('delete')) {
        document.querySelectorAll('.btn-delete').forEach(btn => {
            btn.style.display = 'none';
        });
    }
}

// Call on page load
document.addEventListener('DOMContentLoaded', () => {
    loadUserPermissions();
});
```

6. Add audit logging for privileged operations:
```python
@require_permission(Permission.CONFIGURE)
async def update_zerobus_config(self, request):
    user = request['user']
    logger.info(f"AUDIT: User {user.email} (role={user.role.value}) modified ZeroBus configuration")
    # ... existing code ...
```

TESTING:
- Test admin user can do everything
- Test operator can start/stop but not configure
- Test viewer can only read
- Test permission denial returns 403
- Test UI hides/disables elements correctly
- Verify audit logs capture privileged operations

Implement complete RBAC system with role mapping, permission checks, and UI adaptation.
```

---

## Task 4: Update Docker Configuration for Authentication

### Prompt for AI Assistant

```
Update Docker setup to support OAuth2 authentication with environment variables.

CONTEXT:
Connector always runs in Docker container. OAuth2 requires client credentials and session secrets.

REQUIREMENTS:
1. Pass OAuth credentials via environment variables
2. Support both local and Docker-based OT simulators
3. Handle OAuth redirect URI correctly from Docker
4. Secure credential storage

DOCKER COMPOSE UPDATE:

Update docker-compose.yml:
```yaml
version: '3.8'

services:
  unified-connector:
    build: .
    container_name: unified-ot-connector
    ports:
      - "8082:8082"  # Web UI
      - "8081:8081"  # Health check
      - "9090:9090"  # Prometheus metrics
    
    environment:
      # OAuth2 credentials
      - OAUTH_CLIENT_ID=${OAUTH_CLIENT_ID}
      - OAUTH_CLIENT_SECRET=${OAUTH_CLIENT_SECRET}
      - OAUTH_TENANT_ID=${OAUTH_TENANT_ID}  # For Azure AD
      
      # Session security
      - SESSION_SECRET_KEY=${SESSION_SECRET_KEY}
      
      # Connector credentials
      - CONNECTOR_MASTER_PASSWORD=${CONNECTOR_MASTER_PASSWORD}
      - CONNECTOR_ZEROBUS_CLIENT_ID=${CONNECTOR_ZEROBUS_CLIENT_ID}
      - CONNECTOR_ZEROBUS_CLIENT_SECRET=${CONNECTOR_ZEROBUS_CLIENT_SECRET}
      
      # Databricks config (use default profile)
      - DATABRICKS_CONFIG_FILE=/root/.databrickscfg
    
    volumes:
      - ./config:/app/config  # Configuration files
      - ./data:/app/data      # Persistent data (spool, credentials)
      - ~/.databrickscfg:/root/.databrickscfg:ro  # Read-only Databricks config
    
    networks:
      - ot-network  # Access to OT simulators
      - default     # Access to internet/proxy
    
    restart: unless-stopped

  # OT Simulator (optional - can also run locally)
  ot-simulator:
    image: pravinva/ot-simulator:latest  # Your OT simulator image
    container_name: ot-simulator
    ports:
      - "4840:4840"  # OPC-UA
      - "1883:1883"  # MQTT
      - "502:502"    # Modbus
    networks:
      - ot-network
    restart: unless-stopped

networks:
  ot-network:
    driver: bridge
    ipam:
      config:
        - subnet: 172.20.0.0/16  # Custom subnet for OT devices
```

CREATE .env FILE:
```bash
# .env (add to .gitignore!)

# OAuth2 Credentials (Azure AD example)
OAUTH_CLIENT_ID=your-azure-app-client-id
OAUTH_CLIENT_SECRET=your-azure-app-client-secret
OAUTH_TENANT_ID=your-azure-tenant-id

# Session Security (generate with: python -c "import secrets; print(secrets.token_urlsafe(32))")
SESSION_SECRET_KEY=generate-a-secure-random-key-here

# Connector Master Password
CONNECTOR_MASTER_PASSWORD=your-secure-master-password

# ZeroBus OAuth Credentials (from Databricks)
CONNECTOR_ZEROBUS_CLIENT_ID=your-databricks-oauth-client-id
CONNECTOR_ZEROBUS_CLIENT_SECRET=your-databricks-oauth-client-secret
```

UPDATE config.yaml:
```yaml
web_ui:
  enabled: true
  host: 0.0.0.0  # Listen on all interfaces in container
  port: 8082
  authentication:
    enabled: true
    method: oauth2
    oauth:
      provider: azure
      client_id: ${env:OAUTH_CLIENT_ID}
      client_secret: ${env:OAUTH_CLIENT_SECRET}
      tenant_id: ${env:OAUTH_TENANT_ID}
      # IMPORTANT: Use localhost for redirect (Docker port mapping)
      redirect_uri: http://localhost:8082/login/callback
      scopes: [openid, email, profile]
    session:
      secret_key: ${env:SESSION_SECRET_KEY}
      max_age_seconds: 28800

# Sources can be Docker-based or local
sources:
  # Docker-based OT simulator
  - name: docker-opcua-simulator
    protocol: opcua
    endpoint: opc.tcp://ot-simulator:4840  # Docker service name
    enabled: true
  
  # Local OT simulator (use host.docker.internal on Mac/Windows, or host network on Linux)
  - name: local-opcua-simulator
    protocol: opcua
    endpoint: opc.tcp://host.docker.internal:4841  # Access local host
    enabled: false
```

UPDATE Dockerfile:
```dockerfile
FROM python:3.12-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY unified_connector/ ./unified_connector/

# Create directories
RUN mkdir -p /app/data /app/config

# Expose ports
EXPOSE 8082 8081 9090

# Run application
CMD ["python", "-m", "unified_connector"]
```

CREATE .dockerignore:
```
__pycache__/
*.pyc
*.pyo
*.pyd
.Python
env/
venv/
.env
.env.local
*.log
.git/
.gitignore
README.md
docs/
tests/
.pytest_cache/
.coverage
htmlcov/
```

CREATE setup script (setup-auth.sh):
```bash
#!/bin/bash

# Generate session secret if not exists
if [ -z "$SESSION_SECRET_KEY" ]; then
    echo "Generating session secret key..."
    export SESSION_SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")
    echo "SESSION_SECRET_KEY=$SESSION_SECRET_KEY" >> .env
fi

# Check required environment variables
required_vars=("OAUTH_CLIENT_ID" "OAUTH_CLIENT_SECRET" "CONNECTOR_MASTER_PASSWORD")
for var in "${required_vars[@]}"; do
    if [ -z "${!var}" ]; then
        echo "ERROR: $var not set. Please set in .env file"
        exit 1
    fi
done

echo "✓ Environment variables configured"
echo "Starting connector with authentication..."
docker-compose up -d
```

TESTING INSTRUCTIONS:

1. Local OT Simulator + Docker Connector:
```bash
# Start local OT simulator
python ot_simulator.py --port 4841

# Update config.yaml to use host.docker.internal:4841
# Start connector
docker-compose up
```

2. Docker OT Simulator + Docker Connector:
```bash
# Both in same Docker network
docker-compose up
```

3. Test authentication:
```bash
# Should redirect to OAuth login
curl -I http://localhost:8082/api/sources

# After login, should work
curl -H "Cookie: session=..." http://localhost:8082/api/sources
```

NETWORKING NOTES:
- Docker containers use service names for DNS (e.g., ot-simulator)
- To access local host from Docker:
  - Mac/Windows: host.docker.internal
  - Linux: Add --network=host or use 172.17.0.1 (Docker bridge gateway)
- OAuth redirect URI must be localhost:8082 (Docker port mapping)

Implement Docker configuration with proper networking for both local and Docker-based OT simulators.
```

---

## Verification Checklist

After completing all tasks:

- [ ] Web UI requires authentication (no anonymous access)
- [ ] OAuth2 login flow works from Docker container
- [ ] MFA is enforced (if configured)
- [ ] 3 roles work correctly (admin, operator, viewer)
- [ ] Permission checks on all API endpoints
- [ ] UI adapts to user's role (hides/disables elements)
- [ ] Audit logging for privileged operations
- [ ] Docker-based OT simulators reachable from connector
- [ ] Local OT simulators reachable from connector (host.docker.internal)
- [ ] Credentials stored in .env (not committed to git)
- [ ] Session management works (login persists across requests)
- [ ] Logout clears session

---

## Files to Create/Modify

### New Files:
- unified_connector/web/auth.py (OAuth2 + session management)
- unified_connector/web/rbac.py (Roles + permissions)
- unified_connector/web/static/login.html (Login page)
- .env (OAuth credentials - add to .gitignore!)
- setup-auth.sh (Setup script)

### Modified Files:
- unified_connector/web/web_server.py (Add auth middleware, permission decorators)
- unified_connector/web/static/index.html (Add logout button, user info)
- unified_connector/web/static/app.js (Handle auth, adapt UI to permissions)
- unified_connector/config/config.yaml (Add auth configuration)
- docker-compose.yml (Add environment variables)
- Dockerfile (Ensure proper setup)
- requirements.txt (Add auth libraries)
- .gitignore (Add .env, credentials.enc)

---

## Success Criteria

**Sprint 1.1 Complete When:**
1. ✅ No unauthenticated access to Web UI
2. ✅ OAuth2 login flow working
3. ✅ MFA enforced (if configured)
4. ✅ 3 roles with correct permissions
5. ✅ UI adapts to user role
6. ✅ Audit logs capture privileged operations
7. ✅ Works from Docker container
8. ✅ Can connect to both local and Docker OT simulators
