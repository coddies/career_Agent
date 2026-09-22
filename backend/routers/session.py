"""
backend/routers/session.py — Ephemeral guest session endpoint.

GET /api/v1/session
  Returns a UUID4 session token that the client uses to identify
  itself in subsequent chat requests. No login or signup required.
"""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Request
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from backend.middleware.rate_limiter import limiter
from backend.schemas import SessionResponse

# Import cascade to read the primary model name
from career_agent.config import FALLBACK_CASCADE

router = APIRouter(prefix="/api/v1", tags=["Session"])


@router.get(
    "/session",
    response_model=SessionResponse,
    summary="Create ephemeral guest session",
    description=(
        "Generates an anonymous UUID4 session token. "
        "No account or authentication required. "
        "Pass the returned `session_id` in all subsequent chat requests."
    ),
    responses={
        200: {"description": "Session created successfully."},
        429: {"description": "Rate limit exceeded (5 req/min per IP)."},
    },
)
@limiter.limit("5/minute")
async def create_session(request: Request) -> SessionResponse:
    """
    Issue an ephemeral guest session token.

    Returns:
        SessionResponse with a fresh UUID4 session_id,
        the primary model name, and system operational status.
    """
    primary_model = FALLBACK_CASCADE[0].name if FALLBACK_CASCADE else "Unknown"

    return SessionResponse(
        session_id=str(uuid.uuid4()),
        rate_limit_remaining=4,   # 1 consumed by this request; 4 remain
        primary_model=primary_model,
        status="operational",
    )
