---
title: career_agent
emoji: 🤖
colorFrom: indigo
colorTo: emerald
sdk: gradio
sdk_version: 5.9.1
app_file: app.py
pinned: false
license: mit
short_description: Multi-Provider ReAct AI Career & Skills Advisor
---

# career_agent — AI Career & Skills Advisor

> Multi-Provider ReAct Agent | 4-Tier Failover: Gemini → Groq → NVIDIA → Ollama

## Features
- 🎯 360-degree career strategy (Job Roles, Freelancing, SaaS Ideas, Skill Gaps)
- 📄 CV/PDF upload with scanned-PDF detection
- 🔄 Auto-failover across 4 model tiers
- 🌐 Multilingual (English / Roman Urdu / Urdu script)

## Environment Variables (HF Space Secrets)
Set these in your Space **Settings → Variables and Secrets**:

| Variable | Required | Description |
|----------|----------|-------------|
| `GEMINI_API_KEY` | ✅ | Google Gemini API key |
| `GROQ_API_KEY` | ✅ | Groq API key |
| `NVIDIA_API_KEY` | ⚠️ Optional | NVIDIA NIM key (Tier 3) |
| `OLLAMA_BASE_URL` | ⚠️ Optional | Local Ollama URL (Tier 4) |

## API Usage
Gradio auto-exposes REST endpoints. Use `@gradio/client` in your frontend:

```javascript
import { Client } from "@gradio/client";
const client = await Client.connect("MuhammadBurhan/career-agent-backend");
const result = await client.predict("/chat", { message: "My skills: Python, FastAPI" });
```

## Local Development
```bash
git clone https://huggingface.co/spaces/MuhammadBurhan/career-agent-backend
cd career-agent-backend
pip install -r requirements.txt
# Add your keys to .env
python app.py
```
