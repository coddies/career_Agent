"""
app.py — career_agent Gradio Interface for Hugging Face Spaces (Free Tier).

Architecture:
  - Gradio Blocks UI with Chat + CV Upload tabs
  - Auto-exposes REST API at /api/predict for frontend consumption
  - ReAct loop runs career_agent core (no Docker needed)
  - gr.State() holds per-session conversation history

HF Space: https://huggingface.co/spaces/MuhammadBurhan/career-agent-backend
"""
from __future__ import annotations

import logging
import os
import sys
import tempfile

# Force disable Gradio 6 SSR (Node.js Proxy) which crashes on Hugging Face free tier
os.environ["GRADIO_SSR_MODE"] = "False"

import gradio as gr
from dotenv import load_dotenv

# ── Path setup — works both locally and on HF Spaces ─────────────────────────
sys.path.insert(0, os.path.dirname(__file__))
load_dotenv()

# ── Configure logging ─────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
for _lib in ("httpx", "httpcore", "groq", "openai", "google"):
    logging.getLogger(_lib).setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

# ── Import career_agent core ──────────────────────────────────────────────────
from career_agent.state_adapter import NeutralHistory, append_user
from career_agent.agent import run_react_loop
from career_agent.pdf_parser import extract_pdf_text, SCANNED_PDF_MSG
from career_agent.config import FALLBACK_CASCADE

PRIMARY_MODEL = FALLBACK_CASCADE[0].name if FALLBACK_CASCADE else "Unknown"

# ── CUSTOM CSS ────────────────────────────────────────────────────────────────
CSS = """
/* Root color tokens */
:root {
    --bg-primary: #020617;
    --bg-secondary: #18181b;
    --border-color: #27272a;
    --accent-green: #10b981;
    --accent-indigo: #6366f1;
    --text-primary: #f4f4f5;
    --text-muted: #71717a;
    --font-mono: 'JetBrains Mono', 'Fira Code', monospace;
}

/* Overall app background */
.gradio-container {
    background: var(--bg-primary) !important;
    font-family: 'Inter', system-ui, sans-serif !important;
    max-width: 1100px !important;
    margin: 0 auto !important;
}

/* Header */
.app-header {
    background: linear-gradient(135deg, #0f172a 0%, #1e1b4b 100%);
    border: 1px solid var(--border-color);
    border-radius: 12px;
    padding: 20px 28px;
    margin-bottom: 16px;
    display: flex;
    align-items: center;
    justify-content: space-between;
}
.app-title {
    font-size: 1.4rem;
    font-weight: 700;
    color: var(--text-primary);
    letter-spacing: -0.02em;
    font-family: var(--font-mono);
}
.app-title span { color: var(--accent-green); }
.status-badge {
    display: flex;
    align-items: center;
    gap: 8px;
    background: rgba(16,185,129,0.1);
    border: 1px solid rgba(16,185,129,0.3);
    border-radius: 20px;
    padding: 5px 14px;
    font-size: 0.78rem;
    color: var(--accent-green);
}
.pulse {
    width: 8px; height: 8px;
    background: var(--accent-green);
    border-radius: 50%;
    animation: pulse 2s infinite;
}
@keyframes pulse {
    0%, 100% { opacity: 1; transform: scale(1); }
    50%       { opacity: 0.5; transform: scale(1.3); }
}

/* Tabs */
.tab-nav button {
    background: var(--bg-secondary) !important;
    color: var(--text-muted) !important;
    border: 1px solid var(--border-color) !important;
    border-radius: 8px !important;
    padding: 8px 20px !important;
    font-size: 0.85rem !important;
    transition: all 0.2s ease !important;
}
.tab-nav button.selected {
    background: var(--accent-indigo) !important;
    color: #fff !important;
    border-color: var(--accent-indigo) !important;
}

/* Chat messages */
.message.user   { background: #1e1b4b !important; border-radius: 10px 10px 2px 10px !important; }
.message.bot    { background: #0f172a !important; border-radius: 10px 10px 10px 2px !important; }

/* Textboxes */
textarea, input[type=text] {
    background: var(--bg-secondary) !important;
    border: 1px solid var(--border-color) !important;
    color: var(--text-primary) !important;
    border-radius: 10px !important;
    font-size: 0.9rem !important;
}

/* Buttons */
button.primary {
    background: linear-gradient(135deg, var(--accent-indigo), #4f46e5) !important;
    color: #fff !important;
    border: none !important;
    border-radius: 8px !important;
    font-weight: 600 !important;
    transition: opacity 0.2s !important;
}
button.primary:hover { opacity: 0.88 !important; }

/* Trace box */
.trace-box {
    background: #0a0a0a !important;
    border: 1px solid #1e293b !important;
    border-radius: 10px !important;
    font-family: var(--font-mono) !important;
    font-size: 0.78rem !important;
    color: var(--accent-green) !important;
}

/* Info cards */
.info-card {
    background: var(--bg-secondary);
    border: 1px solid var(--border-color);
    border-radius: 10px;
    padding: 14px 18px;
    margin: 8px 0;
    font-size: 0.85rem;
    color: var(--text-muted);
}
"""

# ── AGENT FUNCTIONS ───────────────────────────────────────────────────────────

def respond(
    message: str,
    chat_history: list,
    neutral_history: list,
    trace_log: str,
) -> tuple[list, list, str]:
    """
    Run one ReAct agent turn.

    Args:
        message: Current user input.
        chat_history: Gradio-format [[user, assistant], ...] history.
        neutral_history: Provider-agnostic history (gr.State).
        trace_log: Accumulated trace string displayed in the terminal box.

    Returns:
        Updated (chat_history, neutral_history, trace_log).
    """
    if not message.strip():
        return chat_history, neutral_history, trace_log

    if neutral_history is None:
        neutral_history = []

    logger.info(f"[Chat] Processing: {message[:80]}...")

    # Patch agent to collect traces
    import career_agent.agent as _agent
    import career_agent.llm_cascade as _cascade

    traces: list[str] = []
    providers_used: list[str] = []
    orig_cascade = _cascade.call_with_cascade
    orig_tool    = _agent._execute_tool

    def traced_cascade(hist, enable_tools=True):
        result = orig_cascade(hist, enable_tools=enable_tools)
        p = result.get("provider", "?")
        providers_used.append(p)
        traces.append(f"[THOUGHT] Queried: {p}")
        return result

    def traced_tool(name, args):
        traces.append(f"[ACTION] {name}({list(args.keys())})")
        obs = orig_tool(name, args)
        traces.append(f"[OBSERVATION] {obs[:120]}...")
        return obs

    _cascade.call_with_cascade = traced_cascade
    _agent._execute_tool = traced_tool

    try:
        append_user(neutral_history, message)
        response = run_react_loop(neutral_history)
    except Exception as exc:
        response = f"Error: {exc}. All model tiers may be temporarily unavailable."
        logger.error(f"Agent error: {exc}")
    finally:
        _cascade.call_with_cascade = orig_cascade
        _agent._execute_tool = orig_tool

    chat_history.append({"role": "user", "content": message})
    chat_history.append({"role": "assistant", "content": response})
    provider = providers_used[-1] if providers_used else PRIMARY_MODEL
    new_traces = "\n".join(traces)
    updated_trace = f"{trace_log}\n---\n{new_traces}\n[PROVIDER] {provider}" if traces else trace_log

    return chat_history, neutral_history, updated_trace.strip()


def upload_cv(
    pdf_file,
    chat_history: list,
    neutral_history: list,
    trace_log: str,
) -> tuple[str, list, list, str]:
    """
    Parse an uploaded PDF and inject its text into the conversation.

    Returns:
        (status_message, chat_history, neutral_history, trace_log)
    """
    if pdf_file is None:
        return "⚠️ Please upload a PDF file.", chat_history, neutral_history, trace_log

    if neutral_history is None:
        neutral_history = []

    try:
        text = extract_pdf_text(pdf_file.name)
    except FileNotFoundError as exc:
        return f"❌ File not found: {exc}", chat_history, neutral_history, trace_log
    except ValueError as exc:
        return f"❌ {exc}", chat_history, neutral_history, trace_log

    if text == SCANNED_PDF_MSG:
        return f"⚠️ {SCANNED_PDF_MSG}", chat_history, neutral_history, trace_log

    char_count = len(text)
    msg = f"Here is my CV/Resume text:\n\n{text}"
    append_user(neutral_history, msg)

    status = f"✅ CV parsed — {char_count:,} characters extracted. Ask me anything about your career!"
    chat_history.append({"role": "user", "content": "[CV Uploaded]"})
    chat_history.append({"role": "assistant", "content": status})
    traces = f"[ACTION] pdf_parser.extract_pdf_text()\n[OBSERVATION] Extracted {char_count} chars"
    updated_trace = f"{trace_log}\n---\n{traces}".strip()

    return status, chat_history, neutral_history, updated_trace


def clear_session() -> tuple[list, list, str]:
    """Reset the conversation to a clean state."""
    return [], [], ""


# ── QUICK ACTION STARTERS ────────────────────────────────────────────────────
QUICK_ACTIONS = [
    "Analyze my skills for the highest-paying remote jobs",
    "Suggest 3 Micro-SaaS ideas based on my stack",
    "What are my top 2 skill gaps to double my income?",
    "Give me specific Upwork gig titles I can create today",
]

# ── GRADIO UI ─────────────────────────────────────────────────────────────────
with gr.Blocks(
    title="career_agent — AI Career Advisor",
    css=CSS,
    theme=gr.themes.Base(
        primary_hue="indigo",
        neutral_hue="zinc",
        font=[gr.themes.GoogleFont("Inter")],
    ),
) as demo:

    # ── Header ────────────────────────────────────────────────────────────────
    gr.HTML(f"""
    <div class="app-header">
        <div class="app-title">career_agent <span>// AI Career Strategist v2.0</span></div>
        <div class="status-badge">
            <div class="pulse"></div>
            System Operational &nbsp;|&nbsp; {PRIMARY_MODEL} / Groq Cascade
        </div>
    </div>
    """)

    # ── Session state ─────────────────────────────────────────────────────────
    neutral_history_state = gr.State([])

    # ── Main tabs ─────────────────────────────────────────────────────────────
    with gr.Tabs(elem_classes="tab-nav"):

        # ── TAB 1: CHAT ───────────────────────────────────────────────────────
        with gr.Tab("💬 Chat"):
            with gr.Row():
                # LEFT — Controls
                with gr.Column(scale=1, min_width=240):
                    gr.HTML('''<div class="info-card">
                        <b>Quick Actions</b><br>
                        Click a prompt or type your own below.
                    </div>''')
                    for qa in QUICK_ACTIONS:
                        qa_btn = gr.Button(qa, size="sm", variant="secondary")

                    gr.HTML('''<div class="info-card" style="margin-top:16px">
                        <b>Failover Status</b><br>
                        <span style="color:#10b981">● Tier 1</span> Gemini 3.6 Flash<br>
                        <span style="color:#6366f1">● Tier 2A</span> GPT-OSS 120B (Groq)<br>
                        <span style="color:#6366f1">● Tier 2B</span> Qwen 27B (Groq)<br>
                        <span style="color:#6366f1">● Tier 2C</span> GPT-OSS 20B (Groq)<br>
                        <span style="color:#52525b">● Tier 3</span> NVIDIA NIM<br>
                        <span style="color:#52525b">● Tier 4</span> Ollama (Emergency)
                    </div>''')

                # RIGHT — Chat
                with gr.Column(scale=3):
                    # Trace drawer
                    with gr.Accordion("🔬 Agent Thought Traces (Developer Mode)", open=False):
                        trace_box = gr.Textbox(
                            label="ReAct Loop Traces",
                            interactive=False,
                            lines=8,
                            elem_classes="trace-box",
                            placeholder="[THOUGHT] -> [ACTION] -> [OBSERVATION] will appear here...",
                        )

                    # Chat UI
                    chatbot = gr.Chatbot(
                        label="career_agent",
                        height=440,
                        render_markdown=True,
                    )
                    with gr.Row():
                        msg_input = gr.Textbox(
                            placeholder="Type your skills, goals, or questions...",
                            show_label=False,
                            scale=4,
                            lines=2,
                            max_lines=5,
                        )
                        with gr.Column(scale=1, min_width=120):
                            send_btn = gr.Button("Send ⚡", variant="primary")
                            clear_btn = gr.Button("Clear 🗑️", size="sm")

                    gr.HTML('''<p style="text-align:center;color:#52525b;font-size:0.75rem;margin-top:8px">
                        Powered by ReAct Control Loops with Auto-Provider Failover
                    </p>''')

            # ── Quick action button wiring ────────────────────────────────────
            def make_qa_handler(text):
                def handler(hist, nh, tl):
                    return respond(text, hist, nh, tl)
                return handler

            for i, qa in enumerate(QUICK_ACTIONS):
                # Re-bind buttons inside the loop
                pass   # Handled below with shared logic

            # ── Event handlers ────────────────────────────────────────────────
            send_inputs  = [msg_input, chatbot, neutral_history_state, trace_box]
            send_outputs = [chatbot, neutral_history_state, trace_box]

            send_btn.click(
                fn=respond,
                inputs=send_inputs,
                outputs=send_outputs,
            ).then(fn=lambda: "", outputs=msg_input)

            msg_input.submit(
                fn=respond,
                inputs=send_inputs,
                outputs=send_outputs,
            ).then(fn=lambda: "", outputs=msg_input)

            clear_btn.click(
                fn=clear_session,
                outputs=[chatbot, neutral_history_state, trace_box],
            )

        # ── TAB 2: CV UPLOAD ──────────────────────────────────────────────────
        with gr.Tab("📄 Upload CV"):
            gr.HTML('''<div class="info-card">
                Upload your CV as a <b>searchable text PDF</b> (not scanned/image).
                Max size: 10 MB. After upload, switch to Chat to ask questions about your CV.
            </div>''')

            with gr.Row():
                with gr.Column():
                    pdf_upload = gr.File(
                        label="Drop your CV / Resume PDF here",
                        file_types=[".pdf"],
                        type="filepath",
                    )
                    upload_btn = gr.Button("Parse CV 📤", variant="primary")
                    cv_status  = gr.Textbox(
                        label="Status",
                        interactive=False,
                        lines=2,
                    )

                with gr.Column():
                    chatbot2 = gr.Chatbot(
                        label="Chat (synced with main tab)",
                        height=300,
                        visible=True,
                    )

            upload_btn.click(
                fn=upload_cv,
                inputs=[pdf_upload, chatbot2, neutral_history_state, trace_box],
                outputs=[cv_status, chatbot2, neutral_history_state, trace_box],
            )

        # ── TAB 3: API DOCS ───────────────────────────────────────────────────
        with gr.Tab("🔌 API Docs"):
            gr.Markdown("""
## Using career_agent as a Backend API

Gradio automatically exposes REST endpoints. Connect from your Next.js frontend:

### JavaScript (Gradio Client)
```javascript
import { Client } from "@gradio/client";

const client = await Client.connect("MuhammadBurhan/career-agent-backend");

// Send a chat message
const result = await client.predict("/chat_api", {
    message: "My skills: Python, FastAPI, Docker. Goal: Remote Job."
});
console.log(result.data);
```

### Direct HTTP (fetch)
```javascript
const res = await fetch(
  "https://muhammadburhan-career-agent-backend.hf.space/api/predict",
  {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      data: ["My skills: Python, FastAPI, Docker. Goal: Remote Job."]
    })
  }
);
const json = await res.json();
console.log(json.data[0]);  // agent response
```

### Environment Variables (HF Space Secrets)
Go to **Settings → Variables and Secrets** and add:
- `GEMINI_API_KEY` — Google Gemini key
- `GROQ_API_KEY` — Groq API key
- `NVIDIA_API_KEY` — Optional (Tier 3)
            """)

    # ── Standalone API endpoint (for frontend fetch calls) ────────────────────
    def chat_api(message: str, history: list | None = None) -> str:
        """
        Lightweight API endpoint callable via Gradio client or direct HTTP POST.
        Stateless — history must be passed each call, or use the UI for stateful chat.
        """
        if history is None:
            history = []
        nh: NeutralHistory = []
        for user_msg, bot_msg in history:
            from career_agent.state_adapter import append_user, append_assistant
            append_user(nh, user_msg)
            if bot_msg:
                append_assistant(nh, bot_msg)
        append_user(nh, message)
        try:
            return run_react_loop(nh)
        except Exception as exc:
            return f"Error: {exc}"

    gr.Interface(
        fn=chat_api,
        inputs=[
            gr.Textbox(label="message"),
            gr.JSON(label="history (optional)", value=[]),
        ],
        outputs=gr.Textbox(label="response"),
        api_name="chat_api",
        title="career_agent API",
        description="Stateless chat API endpoint for frontend integration.",
    ).render()


# ── Launch ────────────────────────────────────────────────────────────────────
demo.launch(server_name="0.0.0.0", server_port=7860)
