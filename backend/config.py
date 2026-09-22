"""
backend/config.py — Environment configuration for the career_agent API.
"""
from __future__ import annotations

import os
from functools import lru_cache

from dotenv import load_dotenv

# Load .env from project root (parent of backend/)
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "..", ".env"))


class Settings:
    """Centralised settings loaded from environment variables."""

    # API metadata
    API_TITLE: str = "career_agent API"
    API_VERSION: str = "2.0.0"
    API_DESCRIPTION: str = (
        "Production-grade Multi-Provider ReAct Career Advisor Agent. "
        "4-tier failover: Gemini -> Groq (3 models) -> NVIDIA NIM -> Ollama."
    )

    # LLM API keys
    GEMINI_API_KEY: str = os.environ.get("GEMINI_API_KEY", "")
    GROQ_API_KEY: str = os.environ.get("GROQ_API_KEY", "")
    NVIDIA_API_KEY: str = os.environ.get("NVIDIA_API_KEY", "")
    OLLAMA_BASE_URL: str = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")

    # CORS — set to your Vercel domain in production
    ALLOWED_ORIGINS: list[str] = os.environ.get(
        "ALLOWED_ORIGINS", "*"
    ).split(",")

    # Rate limiting
    RATE_LIMIT: str = "5/minute"

    # File upload limits
    MAX_PDF_SIZE_MB: int = 5
    MAX_PDF_SIZE_BYTES: int = MAX_PDF_SIZE_MB * 1024 * 1024

    # Chat input limits
    MAX_MESSAGE_LENGTH: int = 1000


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return a cached singleton Settings instance."""
    return Settings()
