# FRONTEND DESIGN SPECIFICATION: CAREER_AGENT TERMINAL

## 1. DESIGN SYSTEM & VISUAL IDENTITY

- **Theme**: Dark-mode first, Industrial / Cyber-Minimalist (Linear.app / Vercel Dashboard style)
- **Color Palette**:
  - Background: Slate 950 (`#020617`) & Zinc 900 (`#18181b`)
  - Accent / Primary: Emerald 500 (`#10b981`) for active execution
  - Buttons: Indigo 500 (`#6366f1`)
  - Borders: Subtly glowing Zinc 800 (`#27272a`)
- **Typography**: Geist Sans / Inter for body, JetBrains Mono / Fira Code for agent traces

---

## 2. LAYOUT STRUCTURE (NEXT.JS 15 + TAILWIND + SHADCN UI)

### HEADER / STATUS BAR

```
career_agent // AI Career Strategist v2.0
[ Green Pulse ] System Operational [Gemini 3.6 Flash / Groq Cascade]
                                       [ Developer Mode Toggle ]
```

### MAIN INTERFACE (2-COLUMN GRID — DESKTOP)

#### LEFT PANEL — Agent Control & CV Upload
1. **CV Dropzone Card** — drag & drop PDF; shows parsing indicator + extracted char pill
2. **Quick Action Pills**:
   - "Analyze my CV for Remote Jobs"
   - "Top 3 Micro-SaaS ideas for my stack"
   - "Find my highest-paying skill gaps"
3. **Active Failover Health Card** — real-time API latency + failover history

#### RIGHT PANEL — Interactive Chat & Thought Drawer
1. **Terminal Trace Drawer** (collapsible code box at top):
   - Streams ReAct loops: `[THOUGHT]` -> `[ACTION]` -> `[OBSERVATION]`
2. **Main Chat Feed**:
   - User messages: dark card, right-aligned
   - Assistant messages: rich Markdown with syntax highlighting and pill links
3. **Input Area**:
   - Auto-resize textarea
   - PDF attach icon button + Send button with loading spinner
   - Footer: *"Powered by ReAct Control Loops with Auto-Provider Failover."*

---

## 3. API INTEGRATION (BACKEND)

```
API Base URL: https://huggingface.co/spaces/YOUR_USER/career-agent
Endpoints used:
  GET  /api/v1/session      — fetch session_id on page load
  POST /api/v1/chat         — send message, get response + traces
  POST /api/v1/upload-cv    — upload PDF, get parsed text
```

---

## 4. UI COMPONENTS

| Component | Library |
|-----------|---------|
| Icons | Lucide React (`Terminal`, `Cpu`, `ShieldCheck`, `UploadCloud`, `Sparkles`, `Zap`) |
| Animations | Framer Motion (drawer collapse, message slide-in) |
| UI Primitives | shadcn/ui (Card, Badge, Button, Textarea, Switch) |
| Code Highlighting | react-syntax-highlighter or shiki |

---

## 5. NEXT.JS IMPLEMENTATION NOTES

```
Framework   : Next.js 15 (App Router)
Styling     : Tailwind CSS v4
Components  : shadcn/ui
State       : React useState / useRef (no Redux needed)
Streaming   : fetch() with ReadableStream for trace logs
Deploy      : Vercel (npx vercel deploy)
```

### v0.dev Prompt (paste this)
```
Build a dark-mode Next.js 15 AI chat interface called "career_agent".
Layout: 2-column grid. Left: PDF drag-drop upload card + quick action pills.
Right: collapsible terminal trace drawer (JetBrains Mono font) + chat feed
with rich Markdown rendering + auto-resize textarea input.
Colors: Slate 950 background, Emerald 500 accent, Indigo 500 buttons.
Add Framer Motion slide-in animations for messages.
Use shadcn Card, Badge, Button, Textarea, Switch components.
Lucide icons: Terminal, Cpu, UploadCloud, Sparkles, Zap.
```
