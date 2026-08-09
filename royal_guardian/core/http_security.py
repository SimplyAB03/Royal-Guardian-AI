from __future__ import annotations
from urllib.parse import urlparse
from fastapi import Request
from royal_guardian.core.config import settings

SAFE_METHODS={"GET","HEAD","OPTIONS"}

def origin_allowed(request: Request) -> bool:
    if request.method in SAFE_METHODS: return True
    path=request.url.path
    if path.startswith('/api/device/') or path.startswith('/api/billing/webhook') or path.startswith('/api/oauth/'):
        return True
    origin=request.headers.get('origin')
    if not origin: return True  # non-browser/API clients; auth still required
    expected=urlparse(settings.public_base_url)
    actual=urlparse(origin)
    return actual.scheme==expected.scheme and actual.netloc==expected.netloc

SECURITY_HEADERS={
    "X-Content-Type-Options":"nosniff",
    "X-Frame-Options":"DENY",
    "Referrer-Policy":"strict-origin-when-cross-origin",
    "Permissions-Policy":"camera=(), geolocation=(), payment=(self)",
    "Content-Security-Policy":"default-src 'self'; img-src 'self' data:; style-src 'self' 'unsafe-inline'; script-src 'self' 'unsafe-inline'; connect-src 'self'; frame-ancestors 'none'; base-uri 'self'; form-action 'self'",
}
