"""
backend/main.py — FastAPI application factory for career_agent API.

Mounts:
  - SecurityHeadersMiddleware  (X-Content-Type-Options, X-Frame-Options)
  - CORSMiddleware             (restricted to ALLOWED_ORIGINS)
  - slowapi RateLimitExceeded  (returns HTTP 429 on breach)
  - /api/v1/session  router
  - /api/v1/chat     router
  - /api/v1/upload-cv router

Start dev server:
    uvicorn backend.main:app --reload --port 8000

Swagger docs available at:
    http://localhost:8000/docs
"""
from __future__ import annotations

import logging
import sys
import os

from dotenv import load_dotenv

# Load .env from project root
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "..", ".env"))

# Ensure project root is on path so career_agent imports resolve
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from api.config import get_settings
from api.middleware.rate_limiter import limiter
from api.middleware.security import SecurityHeadersMiddleware
from api.routers import session as session_router
from api.routers import chat as chat_router

# ── Logging ───────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
for _noisy in ("httpx", "httpcore", "groq", "openai", "google"):
    logging.getLogger(_noisy).setLevel(logging.WARNING)

logger = logging.getLogger(__name__)
settings = get_settings()

# ── App Factory ───────────────────────────────────────────────────────────────
app = FastAPI(
    title=settings.API_TITLE,
    version=settings.API_VERSION,
    description=settings.API_DESCRIPTION,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_tags=[
        {
            "name": "Session",
            "description": "Ephemeral guest session management. No signup required.",
        },
        {
            "name": "Chat",
            "description": "ReAct career advisor chat and CV upload endpoints.",
        },
    ],
)

# ── Rate limiter state ─────────────────────────────────────────────────────────
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# ── Middleware stack (applied bottom-up) ──────────────────────────────────────
app.add_middleware(SecurityHeadersMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "Authorization"],
)

# ── Routers ───────────────────────────────────────────────────────────────────
app.include_router(session_router.router)
app.include_router(chat_router.router)


# ── Root health check ─────────────────────────────────────────────────────────
@app.get("/", tags=["Health"], summary="API health check")
async def root() -> dict:
    """
    Simple liveness probe. Returns API name, version, and status.
    Used by HF Spaces and load balancers to confirm the service is alive.
    """
    return {
        "api": settings.API_TITLE,
        "version": settings.API_VERSION,
        "status": "operational",
        "docs": "/docs",
    }


@app.get("/health", tags=["Health"], summary="Detailed health check")
async def health() -> dict:
    """Returns model cascade info alongside status."""
    from career_agent.config import FALLBACK_CASCADE
    return {
        "status": "operational",
        "primary_model": FALLBACK_CASCADE[0].name if FALLBACK_CASCADE else "Unknown",
        "cascade_tiers": len(FALLBACK_CASCADE),
    }


# ── Startup log ───────────────────────────────────────────────────────────────
@app.on_event("startup")
async def on_startup() -> None:
    logger.info(f"career_agent API v{settings.API_VERSION} starting up...")
    logger.info(f"CORS origins  : {settings.ALLOWED_ORIGINS}")
    logger.info(f"Rate limit    : {settings.RATE_LIMIT}")
    logger.info(f"Docs          : http://localhost:8000/docs")
