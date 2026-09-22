# career_agent — AI Career & Skills Advisor

> Multi-Provider ReAct Agent | 4-Tier Failover: Gemini → Groq → NVIDIA → Ollama

[![HF Space](https://img.shields.io/badge/HuggingFace-Space-orange)](https://huggingface.co/spaces/MuhammadBurhan/career-agent-backend)
[![Python](https://img.shields.io/badge/Python-3.11%2B-blue)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)

## What It Does

career_agent analyzes your skills (CV upload or text input) and delivers a
**360-degree career strategy** across 4 pillars:

| Pillar | Output |
|--------|--------|
| 🎯 Job Roles | Exact high-paying titles matching your stack |
| 💼 Freelancing | Upwork/Fiverr gig titles + B2B outreach services |
| 🚀 SaaS Ideas | Micro-SaaS and automation business concepts |
| 📈 Skill Gaps | Top 2 missing skills to 2x your income |

## Project Structure

```
career_agent/          Core ReAct agent (LLM cascade, tools, PDF parser)
backend/               FastAPI REST API (rate limiting, CORS, auth)
hf_space/              Hugging Face Spaces deployment (Gradio, free tier)
BACKEND_SPEC.md        API specification
DESIGN.md              Frontend design spec (Next.js / v0.dev)
```

## Quick Start (Local)

```bash
# 1. Clone
git clone https://github.com/YOUR_USERNAME/career-agent
cd career-agent

# 2. Create venv with uv
uv venv .venv
.venv\Scripts\activate   # Windows

# 3. Install dependencies
uv pip install -r requirements.txt

# 4. Configure keys
cp .env.example .env
# Edit .env and fill in GEMINI_API_KEY, GROQ_API_KEY

# 5a. Run CLI agent
cd career_agent && python main.py

# 5b. Run FastAPI backend
uvicorn backend.main:app --reload --port 8000
# Swagger: http://localhost:8000/docs

# 5c. Run Gradio (HF Space locally)
cd hf_space && python app.py
```

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `GEMINI_API_KEY` | ✅ | Google Gemini (Tier 1) |
| `GROQ_API_KEY` | ✅ | Groq — GPT-OSS 120B / Qwen 27B / GPT-OSS 20B |
| `NVIDIA_API_KEY` | ⚠️ Optional | NVIDIA NIM (Tier 3) |
| `OLLAMA_BASE_URL` | ⚠️ Optional | Local Ollama (Tier 4 emergency) |
| `ALLOWED_ORIGINS` | ⚠️ Optional | CORS origin (default: `*`) |

## Model Cascade

| Tier | Model | Provider | Tools |
|------|-------|----------|-------|
| 1 | Gemini 3.6 Flash | Google | ✅ |
| 2A | GPT-OSS 120B | Groq | ✅ |
| 2B | Qwen 3.8 27B | Groq | ✅ |
| 2C | GPT-OSS 20B | Groq | ✅ |
| 3 | Llama 3.3 70B | NVIDIA NIM | ✅ |
| 4 | Gemma 4B | Ollama (local) | ❌ |

## Deploy

### Hugging Face Spaces (Free)
```bash
git clone https://huggingface.co/spaces/MuhammadBurhan/career-agent-backend
cp -r hf_space/* career-agent-backend/
cd career-agent-backend
git add . && git commit -m "deploy" && git push
```
Add secrets in Space Settings → Variables and Secrets.

### Frontend (Vercel + Next.js)
See [DESIGN.md](DESIGN.md) — paste the v0.dev prompt to generate the UI,
then `vercel deploy`.

## License

MIT © MuhammadBurhan
