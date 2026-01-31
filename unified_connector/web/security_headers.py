"""
Security Headers Middleware for Web UI.

Implements security headers for NIS2 compliance:
- Content Security Policy (CSP)
- HTTP Strict Transport Security (HSTS)
- X-Frame-Options (clickjacking protection)
- X-Content-Type-Options (MIME sniffing protection)
- X-XSS-Protection (XSS filter)
- Referrer-Policy
- Permissions-Policy

NIS2 Compliance: Article 21.2(a) - Risk Analysis and Security Policies
"""

import logging
from aiohttp import web
from typing import Callable, Awaitable

logger = logging.getLogger(__name__)


@web.middleware
async def security_headers_middleware(
    request: web.Request,
    handler: Callable[[web.Request], Awaitable[web.Response]]
) -> web.Response:
    """
    Add security headers to all responses.

    This middleware adds multiple security headers to protect against
    common web vulnerabilities:
    - XSS attacks
    - Clickjacking
    - MIME sniffing
    - Information leakage
    - Protocol downgrade attacks (when HTTPS is enabled)
    """
    response = await handler(request)

    # Content Security Policy - Restrict resource loading
    # This prevents XSS attacks by controlling what resources can be loaded
    csp_directives = [
        "default-src 'self'",
        "script-src 'self' 'unsafe-inline'",  # 'unsafe-inline' needed for embedded scripts
        "style-src 'self' 'unsafe-inline'",   # 'unsafe-inline' needed for embedded styles
        "img-src 'self' data:",               # Allow data URIs for inline images
        "font-src 'self'",
        "connect-src 'self'",                 # API calls to same origin
        "frame-ancestors 'none'",             # Prevent framing (also set X-Frame-Options)
        "base-uri 'self'",
        "form-action 'self'",
    ]
    response.headers['Content-Security-Policy'] = '; '.join(csp_directives)

    # X-Frame-Options - Prevent clickjacking
    response.headers['X-Frame-Options'] = 'DENY'

    # X-Content-Type-Options - Prevent MIME sniffing
    response.headers['X-Content-Type-Options'] = 'nosniff'

    # X-XSS-Protection - Enable browser XSS filter (legacy, but doesn't hurt)
    response.headers['X-XSS-Protection'] = '1; mode=block'

    # Referrer-Policy - Control referrer information
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'

    # Permissions-Policy - Disable unnecessary browser features
    permissions_directives = [
        "geolocation=()",
        "microphone=()",
        "camera=()",
        "payment=()",
        "usb=()",
        "magnetometer=()",
        "gyroscope=()",
        "accelerometer=()",
    ]
    response.headers['Permissions-Policy'] = ', '.join(permissions_directives)

    # Strict-Transport-Security (HSTS) - Only enable in production with HTTPS
    # This header forces browsers to use HTTPS for all future requests
    # Uncomment in production when HTTPS is configured:
    # response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains; preload'

    # Cache-Control - Prevent caching of sensitive data
    if request.path.startswith('/api/'):
        response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, private'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'

    # Remove server header to avoid information disclosure
    if 'Server' in response.headers:
        del response.headers['Server']

    return response


def get_security_config(config: dict) -> dict:
    """
    Get security configuration from config file.

    Args:
        config: Application configuration

    Returns:
        Security configuration dictionary
    """
    return config.get('web_ui', {}).get('security', {
        'hsts_enabled': False,
        'hsts_max_age': 31536000,
        'hsts_include_subdomains': True,
        'hsts_preload': False,
        'csp_report_only': False,
        'csp_report_uri': None,
    })


def log_security_headers_status():
    """Log security headers configuration on startup."""
    logger.info("✓ Security headers middleware enabled")
    logger.info("  - Content-Security-Policy: Enabled")
    logger.info("  - X-Frame-Options: DENY")
    logger.info("  - X-Content-Type-Options: nosniff")
    logger.info("  - X-XSS-Protection: 1; mode=block")
    logger.info("  - Referrer-Policy: strict-origin-when-cross-origin")
    logger.info("  - Permissions-Policy: Enabled")
    logger.info("  - Cache-Control: Enabled for API routes")
    logger.warning("  - Strict-Transport-Security: DISABLED (enable with HTTPS in production)")
