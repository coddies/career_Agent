"""
backend/services/pdf_service.py — PDF extraction service for the API layer.

Wraps career_agent.pdf_parser with:
  - File size guard  (< 5 MB)
  - Extension guard  (.pdf only)
  - Scanned-PDF guard (< 50 chars extracted)
All failures raise FastAPI HTTPException with appropriate status codes.
"""
from __future__ import annotations

import os
import tempfile

from fastapi import HTTPException, UploadFile

# Import the core parser from the sibling career_agent package
from career_agent.pdf_parser import extract_pdf_text, SCANNED_PDF_MSG
from backend.config import get_settings

_settings = get_settings()


async def parse_uploaded_pdf(file: UploadFile) -> tuple[str, int, str]:
    """
    Read, validate, and extract text from a multipart-uploaded PDF.

    Args:
        file: FastAPI UploadFile object from the multipart form.

    Returns:
        Tuple of (full_text, char_count, preview_300_chars).

    Raises:
        HTTPException 400: Wrong file type, oversized file, or scanned PDF.
        HTTPException 500: Unexpected parsing error.
    """
    # ── Extension check ────────────────────────────────────────────────────
    filename = file.filename or "upload.pdf"
    if not filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type '{os.path.splitext(filename)[1]}'. Only .pdf files are accepted.",
        )

    # ── Read bytes ─────────────────────────────────────────────────────────
    try:
        content = await file.read()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to read uploaded file: {exc}")

    # ── Size check ─────────────────────────────────────────────────────────
    size_mb = len(content) / (1024 * 1024)
    if len(content) > _settings.MAX_PDF_SIZE_BYTES:
        raise HTTPException(
            status_code=400,
            detail=f"File too large ({size_mb:.1f} MB). Maximum allowed size is {_settings.MAX_PDF_SIZE_MB} MB.",
        )

    # ── Write to temp file and extract ─────────────────────────────────────
    try:
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            tmp.write(content)
            tmp_path = tmp.name

        extracted = extract_pdf_text(tmp_path)

    except (FileNotFoundError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"PDF parsing error: {exc}")
    finally:
        try:
            os.unlink(tmp_path)
        except Exception:
            pass

    # ── Scanned PDF check ──────────────────────────────────────────────────
    if extracted == SCANNED_PDF_MSG:
        raise HTTPException(status_code=400, detail=SCANNED_PDF_MSG)

    char_count = len(extracted)
    preview = extracted[:300].strip()

    return extracted, char_count, preview
