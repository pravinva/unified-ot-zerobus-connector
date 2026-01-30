"""
Authentication module for Web UI using OAuth2/SAML.

Supports:
- OAuth2 authentication (Azure AD, Okta, Google)
- MFA verification from OAuth tokens
- Session management with encrypted cookies
- Login/logout flows

NIS2 Compliance: Article 21.2(g) - Access Control & MFA
"""

import logging
import os
from typing import Dict, Any, Optional
from urllib.parse import urlencode

from aiohttp import web
from aiohttp_session import setup as setup_session, get_session, new_session
from aiohttp_session.cookie_storage import EncryptedCookieStorage
from authlib.integrations.aiohttp_client import OAuth
from cryptography import fernet

logger = logging.getLogger(__name__)


class AuthenticationManager:
    """Manages OAuth2 authentication and session handling."""

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize authentication manager.

        Args:
            config: Authentication configuration from config.yaml
        """
        self.config = config
        self.enabled = config.get('enabled', False)

        if not self.enabled:
            logger.info("Authentication disabled")
            return

        self.method = config.get('method', 'oauth2')
        self.oauth_config = config.get('oauth', {})
        self.session_config = config.get('session', {})
        self.rbac_config = config.get('rbac', {})

        # OAuth2 settings
        self.provider = self.oauth_config.get('provider', 'azure')
        self.client_id = self._get_env_or_config('client_id')
        self.client_secret = self._get_env_or_config('client_secret')
        self.tenant_id = self._get_env_or_config('tenant_id', '')
        self.redirect_uri = self.oauth_config.get('redirect_uri', 'http://localhost:8082/login/callback')
        self.scopes = self.oauth_config.get('scopes', ['openid', 'email', 'profile'])

        # MFA settings
        self.require_mfa = config.get('require_mfa', False)
        mfa_config = config.get('mfa', {})
        self.mfa_claim_name = mfa_config.get('claim_name', 'amr')
        self.mfa_required_methods = mfa_config.get('required_methods', ['mfa', 'otp', 'duo'])

        # Session settings
        self.session_secret = self._get_env_or_config('secret_key', key_path='session')
        self.session_max_age = self.session_config.get('max_age_seconds', 28800)  # 8 hours

        # OAuth client (initialized in setup())
        self.oauth = None
        self.oauth_client = None

        logger.info(f"Authentication manager initialized: provider={self.provider}, mfa_required={self.require_mfa}")

    def _get_env_or_config(self, key: str, default: str = '', key_path: Optional[str] = None) -> str:
        """
        Get value from environment variable or config, with fallback.

        Args:
            key: Configuration key
            default: Default value if not found
            key_path: Path in config dict (e.g., 'session' for session.secret_key)

        Returns:
            Configuration value
        """
        # Try environment variable first (uppercase with OAUTH_ prefix)
        env_key = f"OAUTH_{key.upper()}"
        env_value = os.getenv(env_key)
        if env_value:
            return env_value

        # Try SESSION_ prefix for session keys
        if key_path == 'session':
            env_key = f"SESSION_{key.upper()}"
            env_value = os.getenv(env_key)
            if env_value:
                return env_value

        # Try config dict
        config_dict = self.session_config if key_path == 'session' else self.oauth_config
        config_value = config_dict.get(key, '')

        # Check if config value is ${env:VAR_NAME} format
        if isinstance(config_value, str) and config_value.startswith('${env:'):
            env_var = config_value[6:-1]  # Extract VAR_NAME from ${env:VAR_NAME}
            return os.getenv(env_var, default)

        return config_value or default

    async def setup(self, app: web.Application):
        """
        Set up authentication for the application.

        Args:
            app: aiohttp Application instance
        """
        if not self.enabled:
            logger.info("Authentication disabled, skipping setup")
            return

        # Set up session management with encrypted cookies
        secret_key = self.session_secret
        if not secret_key:
            logger.error("Session secret key not configured! Set SESSION_SECRET_KEY environment variable.")
            raise ValueError("Session secret key required for authentication")

        # Convert secret key to Fernet key format
        fernet_key = fernet.Fernet.generate_key()  # In production, derive from secret_key
        storage = EncryptedCookieStorage(fernet_key, max_age=self.session_max_age)
        setup_session(app, storage)

        # Set up OAuth2
        self.oauth = OAuth()

        if self.provider == 'azure':
            # Azure AD configuration
            authority = f"https://login.microsoftonline.com/{self.tenant_id}" if self.tenant_id else "https://login.microsoftonline.com/common"
            self.oauth.register(
                name='azure',
                client_id=self.client_id,
                client_secret=self.client_secret,
                server_metadata_url=f"{authority}/v2.0/.well-known/openid-configuration",
                client_kwargs={
                    'scope': ' '.join(self.scopes),
                    'prompt': 'select_account'
                }
            )
            self.oauth_client = self.oauth.azure
            logger.info(f"OAuth2 configured for Azure AD: tenant={self.tenant_id}")

        elif self.provider == 'okta':
            # Okta configuration
            okta_domain = self.oauth_config.get('okta_domain', '')
            self.oauth.register(
                name='okta',
                client_id=self.client_id,
                client_secret=self.client_secret,
                server_metadata_url=f"https://{okta_domain}/.well-known/openid-configuration",
                client_kwargs={'scope': ' '.join(self.scopes)}
            )
            self.oauth_client = self.oauth.okta
            logger.info(f"OAuth2 configured for Okta: domain={okta_domain}")

        elif self.provider == 'google':
            # Google configuration
            self.oauth.register(
                name='google',
                client_id=self.client_id,
                client_secret=self.client_secret,
                server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
                client_kwargs={'scope': ' '.join(self.scopes)}
            )
            self.oauth_client = self.oauth.google
            logger.info("OAuth2 configured for Google")

        else:
            raise ValueError(f"Unsupported OAuth provider: {self.provider}")

        # Store auth manager in app
        app['auth_manager'] = self

        logger.info("✓ Authentication setup complete")

    async def handle_login(self, request: web.Request) -> web.Response:
        """
        Handle login initiation - redirect to OAuth provider.

        Args:
            request: aiohttp Request

        Returns:
            Redirect response to OAuth provider
        """
        redirect_uri = self.redirect_uri
        return await self.oauth_client.authorize_redirect(request, redirect_uri)

    async def handle_oauth_callback(self, request: web.Request) -> web.Response:
        """
        Handle OAuth callback after user authentication.

        Args:
            request: aiohttp Request with authorization code

        Returns:
            Redirect to home page or error page
        """
        try:
            # Exchange authorization code for token
            token = await self.oauth_client.authorize_access_token(request)

            # Parse user info from token
            userinfo = token.get('userinfo')
            if not userinfo:
                # Fetch userinfo if not in token
                userinfo = await self.oauth_client.userinfo(token=token)

            user_email = userinfo.get('email') or userinfo.get('preferred_username') or userinfo.get('upn')
            user_name = userinfo.get('name', user_email)
            user_groups = userinfo.get('groups', [])

            if not user_email:
                logger.error("No email in OAuth token")
                return web.Response(text="Authentication failed: No email in token", status=403)

            # Check MFA if required
            if self.require_mfa:
                mfa_satisfied = self.check_mfa_status(token)
                if not mfa_satisfied:
                    logger.warning(f"MFA not satisfied for user {user_email}")
                    return web.Response(
                        text="Multi-factor authentication required. Please enable MFA and try again.",
                        status=403
                    )
                logger.info(f"User {user_email} authenticated with MFA")

            # Create user object with role (RBAC will be implemented separately)
            from unified_connector.web.rbac import User
            user = User(
                email=user_email,
                name=user_name,
                groups=user_groups,
                role_mappings=self.rbac_config.get('role_mappings', {}),
                default_role=self.rbac_config.get('default_role', 'viewer')
            )

            # Create session
            session = await new_session(request)
            session['user'] = {
                'email': user.email,
                'name': user.name,
                'groups': user.groups,
                'role': user.role.value,
                'mfa_completed': self.require_mfa
            }

            logger.info(f"User {user_email} logged in successfully (role={user.role.value})")

            # Redirect to home page
            return web.HTTPFound('/')

        except Exception as e:
            logger.error(f"OAuth callback failed: {e}", exc_info=True)
            return web.Response(text=f"Authentication failed: {str(e)}", status=500)

    async def handle_logout(self, request: web.Request) -> web.Response:
        """
        Handle logout - clear session and redirect to login.

        Args:
            request: aiohttp Request

        Returns:
            Redirect response to login page
        """
        session = await get_session(request)
        user_email = session.get('user', {}).get('email', 'unknown')

        # Clear session
        session.invalidate()

        logger.info(f"User {user_email} logged out")

        return web.HTTPFound('/login')

    async def get_auth_status(self, request: web.Request) -> web.Response:
        """
        Get current authentication status.

        Args:
            request: aiohttp Request

        Returns:
            JSON response with user info or 401 if not authenticated
        """
        session = await get_session(request)
        user_data = session.get('user')

        if not user_data:
            raise web.HTTPUnauthorized()

        return web.json_response({
            'authenticated': True,
            'user': user_data
        })

    def check_mfa_status(self, token: Dict[str, Any]) -> bool:
        """
        Check if user completed MFA based on OAuth token claims.

        Args:
            token: OAuth token with claims

        Returns:
            True if MFA satisfied, False otherwise
        """
        # Check for MFA claim in token
        # Azure AD uses 'amr' (Authentication Methods Reference)
        amr = token.get(self.mfa_claim_name, [])

        if not isinstance(amr, list):
            amr = [amr]

        # Check if any required MFA method is present
        for method in self.mfa_required_methods:
            if method in amr:
                logger.debug(f"MFA satisfied with method: {method}")
                return True

        logger.debug(f"MFA not satisfied. Available methods: {amr}, required: {self.mfa_required_methods}")
        return False


@web.middleware
async def auth_middleware(request: web.Request, handler):
    """
    Authentication middleware - check session for protected routes.

    Args:
        request: aiohttp Request
        handler: Route handler

    Returns:
        Handler response or 401/302 if not authenticated
    """
    auth_manager = request.app.get('auth_manager')

    # Skip authentication if disabled
    if not auth_manager or not auth_manager.enabled:
        return await handler(request)

    # Public endpoints (no authentication required)
    public_paths = ['/login', '/login/callback', '/health', '/static']
    if any(request.path.startswith(path) for path in public_paths):
        return await handler(request)

    # Check session
    session = await get_session(request)
    user_data = session.get('user')

    if not user_data:
        # Not authenticated
        logger.debug(f"Unauthenticated access attempt to {request.path}")

        # For API requests, return 401
        if request.path.startswith('/api/'):
            raise web.HTTPUnauthorized(reason="Authentication required")

        # For browser requests, redirect to login
        return web.HTTPFound('/login')

    # Recreate User object and attach to request
    from unified_connector.web.rbac import User, Role
    request['user'] = User(
        email=user_data['email'],
        name=user_data.get('name', user_data['email']),
        groups=user_data.get('groups', []),
        role_mappings={},  # Not needed, role already determined
        default_role='viewer'
    )
    request['user'].role = Role[user_data['role'].upper()]

    return await handler(request)
