# BACKEND SPECIFICATION: CAREER_AGENT FASTAPI API

## 1. ARCHITECTURE & SECURITY REQUIREMENTS

Build a production-grade FastAPI backend for the Multi-Provider ReAct Career Agent.

### Security & Validation Rules

| Rule | Implementation |
|------|---------------|
| Rate Limiting | `slowapi` — 5 requests/min per IP |
| Ephemeral Guest Auth | UUID4 session token via `GET /api/v1/session` (no signup needed) |
| Input Validation | Pydantic v2 strict schemas; message max 1000 chars |
| CORS | Restricted to frontend Vercel origin |
| Security Headers | `X-Content-Type-Options`, `X-Frame-Options` |
| Swagger Docs | OpenAPI tags, response models, status codes at `/docs` |

---

## 2. FILE STRUCTURE

```
backend/
├── main.py                  # FastAPI App & Middleware configuration
├── config.py                # Environment variables & Model Cascade
├── schemas.py               # Pydantic Request/Response models
├── middleware/
│   ├── rate_limiter.py      # Slowapi IP Rate Limiter setup
│   └── security.py         # CORS & Security headers
├── services/
│   ├── agent_engine.py     # ReAct Loop with Event Logging
│   └── pdf_service.py      # PDF Text Extractor (<50 char error)
└── routers/
    ├── chat.py             # POST /api/v1/chat, POST /api/v1/upload-cv
    └── session.py          # GET /api/v1/session (Guest token)
```

---

## 3. ENDPOINT SPECIFICATION

### GET `/api/v1/session`
Returns ephemeral session token, rate limit info, and system status.

```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "rate_limit_remaining": 5,
  "primary_model": "Gemini 3.6 Flash",
  "status": "operational"
}
```

### POST `/api/v1/chat`
Request:
```json
{ "session_id": "string", "message": "string (max 1000 chars)" }
```
Response:
```json
{
  "status": "success",
  "data": {
    "response": "Detailed career advice...",
    "execution_metadata": {
      "active_provider": "Gemini 3.6 Flash",
      "failover_occurred": false,
      "turns_taken": 3,
      "agent_traces": [
        "Thought: User provided Python/FastAPI skills.",
        "Action: Executing skill gap analyzer.",
        "Observation: Missing Docker/Kubernetes."
      ]
    }
  }
}
```

### POST `/api/v1/upload-cv`
- Accepts `.pdf` multipart file
- Validates: size < 5MB, parseable text
- Response: `{ "status": "success", "char_count": 3420, "preview": "..." }`

---

## 4. ERROR CODES

| Code | Scenario |
|------|----------|
| 400 | Invalid PDF (scanned/image-based, oversized, wrong format) |
| 422 | Pydantic validation failure (message too long, missing field) |
| 429 | Rate limit exceeded (5 req/min per IP) |
| 500 | All model tiers exhausted / unexpected server error |
