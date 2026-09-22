# ARCHITECTURE & SPECIFICATION: GEMINI AGENT WITH FAILOVER

## 1. ENVIRONMENT & PACKAGE MANAGEMENT

- **Tooling**: Use `uv` strictly instead of standard `pip`.

### Setup Commands

```bash
# Create virtual environment
uv venv .venv

# Activate (Linux/Mac)
source .venv/bin/activate

# Activate (Windows)
.venv\Scripts\activate

# Install all dependencies
uv pip install google-genai groq pydantic pypdf python-dotenv
```

---

## 2. MULTI-LLM FAILOVER ARCHITECTURE

| Role | Model | Provider SDK |
|------|-------|--------------|
| **Primary** | `gemini-2.5-flash` | `google-genai` |
| **Secondary (Failover)** | `llama-3.3-70b-versatile` | `groq` |

### Fallback Trigger Conditions

- `HTTP 429` — Rate Limit Exceeded
- `HTTP 503` — Server Overload
- **Timeout** — Response exceeds 15 seconds per turn

### State Synchronization Rule

Maintain conversation history in a **provider-agnostic format**:

```python
List[Dict[str, str]]

# Example structure:
[
    {"role": "user",      "content": "Analyze my CV..."},
    {"role": "assistant", "content": "Based on your skills..."},
]
```

> Upon failover, convert the agnostic history to the secondary provider's
> native format **before** retrying the call.

---

## 3. REACT LOOP & CONTROL BOUNDARIES

### Hard Limits

| Parameter | Value | Reason |
|-----------|-------|--------|
| `max_turns` | `5` | Prevent infinite execution loops |

### Temperature Strategy

| Scenario | Temperature |
|----------|-------------|
| Default (tool calling + grounded advice) | `0.3` |
| Fallback (creative business brainstorming) | `0.4` |

### Error Handling

- Wrap **every** tool execution in `try-except` blocks.
- On tool error, pass the observation back to the model instead of crashing:

```python
try:
    result = tool.execute(params)
except Exception as e:
    observation = f"Observation: Error — {str(e)}"
    # Pass observation back into the ReAct loop
```

> Never crash the script on tool failure. Always surface the error as an
> `Observation` so the model can recover gracefully.
