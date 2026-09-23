"""
backend/routers/chat.py — Chat and CV upload endpoints.

POST /api/v1/chat       — Run ReAct agent turn, return response + traces.
POST /api/v1/upload-cv  — Parse uploaded PDF, return text preview.
"""
from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException, Request, UploadFile, File

from api.middleware.rate_limiter import limiter
from api.schemas import (
    ChatRequest,
    ChatResponse,
    ChatData,
    ExecutionMetadata,
    CVUploadResponse,
)
from api.services.agent_engine import run_agent_turn
from api.services.pdf_service import parse_uploaded_pdf
from career_agent.state_adapter import NeutralHistory

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["Chat"])

# In-memory session store: session_id -> NeutralHistory
# For production scale, replace with Redis.
_sessions: dict[str, NeutralHistory] = {}


def _get_or_create_history(session_id: str) -> NeutralHistory:
    """Return existing conversation history for a session, or create a fresh one."""
    if session_id not in _sessions:
        _sessions[session_id] = []
    return _sessions[session_id]


# ── POST /api/v1/chat ────────────────────────────────────────────────────────

@router.post(
    "/chat",
    response_model=ChatResponse,
    summary="Send a message to the career advisor",
    description=(
        "Runs the ReAct loop against the multi-tier model cascade. "
        "Returns the agent response plus execution metadata including "
        "provider used, failover status, and Thought/Action/Observation traces."
    ),
    responses={
        200: {"description": "Agent response with execution metadata."},
        400: {"description": "Invalid request payload."},
        429: {"description": "Rate limit exceeded (5 req/min per IP)."},
        500: {"description": "All model tiers exhausted or unexpected server error."},
    },
)
@limiter.limit("5/minute")
async def chat(request: Request, body: ChatRequest) -> ChatResponse:
    """
    Run a single agent turn for the given session.

    Args:
        request: FastAPI Request (required by slowapi for IP extraction).
        body: Validated ChatRequest with session_id and message.

    Returns:
        ChatResponse with the agent reply and execution metadata.
    """
    logger.info(f"[/chat] session={body.session_id[:8]}... msg_len={len(body.message)}")

    history = _get_or_create_history(body.session_id)

    try:
        result = run_agent_turn(history, body.message)
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception(f"[/chat] Unexpected error: {exc}")
        raise HTTPException(status_code=500, detail=f"Unexpected server error: {exc}")

    return ChatResponse(
        status="success",
        data=ChatData(
            response=result.response,
            execution_metadata=ExecutionMetadata(
                active_provider=result.active_provider,
                failover_occurred=result.failover_occurred,
                turns_taken=result.turns_taken,
                agent_traces=result.agent_traces,
            ),
        ),
    )


# ── POST /api/v1/upload-cv ───────────────────────────────────────────────────

@router.post(
    "/upload-cv",
    response_model=CVUploadResponse,
    summary="Upload and parse a CV/Resume PDF",
    description=(
        "Accepts a multipart PDF upload (max 5 MB). "
        "Extracts text and returns a 300-char preview plus total character count. "
        "Returns HTTP 400 if the PDF is image-based or scanned."
    ),
    responses={
        200: {"description": "PDF parsed successfully."},
        400: {"description": "Wrong type, oversized, or scanned/image-based PDF."},
        429: {"description": "Rate limit exceeded."},
        500: {"description": "PDF parsing failure."},
    },
)
@limiter.limit("5/minute")
async def upload_cv(
    request: Request,
    file: UploadFile = File(..., description="PDF resume/CV file (max 5 MB)."),
) -> CVUploadResponse:
    """
    Parse an uploaded PDF resume and return a text preview.

    Args:
        request: FastAPI Request (required by slowapi).
        file: Multipart-uploaded PDF file.

    Returns:
        CVUploadResponse with char_count, preview, and filename.
    """
    logger.info(f"[/upload-cv] filename={file.filename}")

    extracted_text, char_count, preview = await parse_uploaded_pdf(file)

    logger.info(f"[/upload-cv] Extracted {char_count:,} chars from {file.filename}")

    return CVUploadResponse(
        status="success",
        char_count=char_count,
        preview=preview,
        filename=file.filename or "resume.pdf",
    )
