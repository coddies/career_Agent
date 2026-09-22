"""
backend/schemas.py — Pydantic v2 request and response schemas.

All input schemas enforce strict validation so invalid payloads
are rejected with HTTP 422 before reaching the agent.
"""
from __future__ import annotations

from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


# ---------------------------------------------------------------------------
# REQUEST SCHEMAS
# ---------------------------------------------------------------------------

class ChatRequest(BaseModel):
    """Payload for POST /api/v1/chat."""

    session_id: str = Field(
        ...,
        description="Ephemeral session ID obtained from GET /api/v1/session.",
        min_length=1,
    )
    message: str = Field(
        ...,
        description="User message (max 1000 characters).",
        min_length=1,
        max_length=1000,
    )

    @field_validator("message")
    @classmethod
    def strip_whitespace(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError("Message cannot be empty or whitespace only.")
        return stripped


# ---------------------------------------------------------------------------
# RESPONSE SCHEMAS
# ---------------------------------------------------------------------------

class ExecutionMetadata(BaseModel):
    """Metadata about the ReAct execution for this turn."""

    active_provider: str = Field(description="Model tier that produced the final answer.")
    failover_occurred: bool = Field(description="True if any tier was skipped due to error.")
    turns_taken: int = Field(description="Number of ReAct loop iterations executed.")
    agent_traces: list[str] = Field(
        default_factory=list,
        description="Ordered list of Thought / Action / Observation trace strings.",
    )


class ChatData(BaseModel):
    """Inner data payload for a successful chat response."""

    response: str = Field(description="Final assistant response text.")
    execution_metadata: ExecutionMetadata


class ChatResponse(BaseModel):
    """Response for POST /api/v1/chat."""

    status: str = Field(default="success")
    data: ChatData


class SessionResponse(BaseModel):
    """Response for GET /api/v1/session."""

    session_id: str = Field(description="UUID4 ephemeral guest session token.")
    rate_limit_remaining: int = Field(description="Requests remaining in current window.")
    primary_model: str = Field(description="Active primary model display name.")
    status: str = Field(default="operational")


class CVUploadResponse(BaseModel):
    """Response for POST /api/v1/upload-cv."""

    status: str = Field(default="success")
    char_count: int = Field(description="Number of characters extracted from the PDF.")
    preview: str = Field(description="First 300 characters of extracted text.")
    filename: str = Field(description="Original uploaded filename.")


# ---------------------------------------------------------------------------
# ERROR SCHEMAS
# ---------------------------------------------------------------------------

class ErrorDetail(BaseModel):
    """Standard error response body."""

    status: str = Field(default="error")
    code: int = Field(description="HTTP status code.")
    message: str = Field(description="Human-readable error description.")
