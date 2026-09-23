"""
backend/middleware/rate_limiter.py — slowapi IP-based rate limiter.

Default: 5 requests per minute per client IP.
On limit breach, returns HTTP 429 with a Retry-After header.
"""
from __future__ import annotations

from slowapi import Limiter
from slowapi.util import get_remote_address

# Singleton Limiter instance — imported by routers and main.py
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["5/minute"],
)
