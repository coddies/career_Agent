"""
backend/middleware/security.py — CORS configuration and security headers.

Security headers added to every response:
  X-Content-Type-Options : nosniff
  X-Frame-Options        : DENY
  Referrer-Policy        : strict-origin-when-cross-origin
  X-XSS-Protection       : 1; mode=block
"""
from __future__ import annotations

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Injects security headers into every HTTP response.
    Applied at the Starlette middleware layer so it covers
    all routes including error responses.
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        response: Response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["X-Powered-By"] = "career_agent v2.0"
        return response
