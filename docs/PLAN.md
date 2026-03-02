# NEO-TX: Shadow Desktop Implementation Plan

## Context

Every existing computer-use agent (Claude Computer Use, OpenAI Operator) hijacks the user's screen. NEO-TX doesn't. The AI gets its own hidden virtual desktop — a "shadow" of the real desktop — where it operates GUI apps autonomously. The user keeps their screen. They only intersect at approval gates and an optional viewport.

**Local-first.** No cloud APIs. UI-TARS-72B (ByteDance, open-weight) runs on CPU for GUI agent work. Qwen2.5-Coder-14B on GPU for planning. Voice handled by Alchemy (separate repo).

**Platform:** Windows 11 Pro → Shadow desktop runs inside **WSL2 + Xvfb** (direct port of Linux spec, zero security flags, proven stack).

---

## Architecture

```
Windows 11 Host                              WSL2 Ubuntu
┌──────────────────────────┐    localhost    ┌──────────────────────────┐
│                          │    :6080        │                          │
│  Alchemy (:8000)         │                 │  Xvfb (:99)             │
│   ├─ voice pipeline      │                 │   + Fluxbox (WM)        │
│   ├─ model routing       │                 │   + Firefox, apps       │
│   └─ Ollama (models)     │                 │                          │
│                          │◄──────────────►│  x11vnc (:5900)          │
│  NEO-TX (:8100)          │◄──────────────►│  noVNC (:6080)           │
│   ├─ agent loop          │                 │                          │
│   ├─ tray widget         │    WSL bridge  │  xdotool (actions)       │
│   ├─ constitution        │───────────────►│  scrot (screenshots)     │
│   └─ task planner        │                 │                          │
└──────────────────────────┘                 └──────────────────────────┘
```

### Separation of Concerns

| Concern | Owner | Why |
|---------|-------|-----|
| Voice (STT/TTS) | **Alchemy** | General I/O, fast 14B GPU |
| Model routing | **Alchemy** | Shared, triviality detection |
| Ollama models | **Alchemy** | Centralized model lifecycle |
| Shadow desktop | **NEO-TX** | WSL2 + Xvfb |
| Agent loop | **NEO-TX** | Screenshot → reason → act |
| Constitution | **NEO-TX** | Approval gates |
| Tray widget | **NEO-TX** | Desktop UI |
| Task planner | **NEO-TX** | Decomposition via Alchemy API |

---

## Repo Structure

```
NEO-TX/
├── README.md
├── CLAUDE.md
├── pyproject.toml
├── .env.example
├── .gitignore
├── Makefile
│
├── config/
│   └── settings.py                    # Pydantic Settings (port 8100, WSL2 config)
│
├── neotx/
│   ├── __init__.py
│   ├── server.py                      # FastAPI server (port 8100, thin orchestrator)
│   │
│   ├── shadow/                        # Phase 1: Shadow Desktop
│   │   ├── controller.py             # Start/stop/health Xvfb+Fluxbox+x11vnc+noVNC
│   │   ├── display.py                # Xvfb display manager
│   │   ├── vnc.py                    # x11vnc + noVNC bridge
│   │   ├── wsl.py                    # WSL2 command runner (Windows→WSL2 bridge)
│   │   └── health.py                 # Service health checks
│   │
│   ├── agent/                         # Phase 2: Visuomotor Agent (local-first)
│   │   ├── loop.py                   # screenshot → reason → act → observe cycle
│   │   ├── vision_backend.py         # UI-TARS via Alchemy /vision/analyze endpoint
│   │   ├── actions.py                # click/type/scroll/drag via xdotool in WSL2
│   │   ├── screenshot.py             # Capture from Xvfb
│   │   └── prompts.py                # System prompts for vision model
│   │
│   ├── constitution/                  # Phase 3: Defense Constitution
│   │   ├── gates.py                  # 3-tier: AUTO / NOTIFY / APPROVE
│   │   ├── rules.py                  # Action classification
│   │   └── audit.py                  # JSONL audit log
│   │
│   ├── tray/                          # Phase 4: System Tray Widget
│   │   ├── widget.py                 # PyQt6 system tray icon + menu
│   │   ├── viewport.py              # noVNC viewport (QWebEngineView)
│   │   ├── notifications.py         # Toast notifications
│   │   └── approval_dialog.py       # Modal approve/deny dialog
│   │
│   ├── planner/                       # Phase 5: Task Planner
│   │   ├── intent.py                # Intent parser via Alchemy gateway
│   │   ├── decomposer.py            # Task → sub-steps
│   │   └── memory.py                # ChromaDB session memory
│   │
│   ├── router/                        # Phase 5: Task Router
│   │   └── task_router.py           # API-direct vs shadow-desktop decision
│   │
│   └── bridge/                        # Alchemy integration
│       ├── client.py                # HTTP client to port 8000
│       ├── ws_client.py             # WebSocket client
│       └── auth.py                  # Bearer token management
│
├── wsl/
│   ├── setup.sh
│   ├── start_shadow.sh
│   ├── stop_shadow.sh
│   └── health_check.sh
│
├── tests/
│   ├── conftest.py
│   ├── test_shadow/
│   ├── test_agent/
│   ├── test_constitution/
│   ├── test_tray/
│   ├── test_planner/
│   └── test_bridge/
│
├── scripts/
│   ├── install_wsl.ps1
│   └── demo.py
│
└── docs/
    ├── PLAN.md (this file)
    ├── ARCHITECTURE.md
    └── APPROVAL_GATES.md
```

---

## Phase Plan

### Phase 1 (Week 1-2): Shadow Desktop PoC
**Goal:** Xvfb running in WSL2, controllable from Windows, viewable via noVNC.

**Build:**
- `neotx/shadow/wsl.py` — WslRunner class (`run()`, `run_bg()`, `is_available()`)
- `neotx/shadow/controller.py` — ShadowDesktopController (`start()`, `stop()`, `health()`, `screenshot()`)
- WSL2 scripts (already scaffolded)
- `scripts/demo.py` — starts shadow, opens Firefox, user views at localhost:6080

**Milestone:** `python scripts/demo.py` starts hidden desktop → opens Firefox → viewable at `http://localhost:6080/vnc.html`

**Tests:** ~20 (WslRunner, controller lifecycle, health checks)

---

### Phase 2 (Week 3-4): Agent Loop + UI-TARS (Local-First)
**Goal:** Agent loop: screenshot → Alchemy /vision/analyze (UI-TARS-72B) → parse action → xdotool → repeat.

**Build:**
- `neotx/agent/loop.py` — perceive-plan-act cycle (max 50 steps)
- `neotx/agent/vision_backend.py` — calls `POST http://localhost:8000/vision/analyze` (Alchemy routes to UI-TARS-72B on CPU)
- `neotx/agent/actions.py` — xdotool primitives (click, type, key, scroll, drag)
- `neotx/agent/screenshot.py` — capture + base64 encode from Xvfb

**Key:** Agent loop runs locally. Vision model (UI-TARS-72B) runs on CPU via Alchemy. No cloud API calls.

**Milestone:** "Open Firefox and search for weather in Stockholm" works end-to-end.

**Tests:** ~25 (loop, action parsing, screenshot capture, mock vision responses)

---

### Phase 3 (Week 5-6): Defense Constitution
**Goal:** 3-tier approval gates for every agent action.

**Build:**
- `neotx/constitution/gates.py` — 3-tier classification (AUTO/NOTIFY/APPROVE)
- `neotx/constitution/rules.py` — action → tier mapping
- `neotx/constitution/audit.py` — JSONL action log (every action, every screenshot)

**Tiers:**
- **AUTO:** click, type, scroll, screenshot, navigate — execute silently
- **NOTIFY:** open app, download file, create file — execute + notify user
- **APPROVE:** send email, delete file, submit form, purchase, post publicly — pause + ask

**Milestone:** Agent stops and waits for approval before sending email.

**Tests:** ~20 (gate classification, audit trail integrity, timeout behavior)

---

### Phase 4 (Week 7-8): Tray Widget & Viewport
**Goal:** PyQt6 system tray with noVNC viewport and approval dialogs.

**Build:**
- `neotx/tray/widget.py` — QSystemTrayIcon (Show Viewport / Pause / Resume / Quit)
- `neotx/tray/viewport.py` — QWebEngineView → `localhost:6080/vnc.html?autoconnect=true`
- `neotx/tray/approval_dialog.py` — screenshot preview + approve/deny (60s timeout)
- `neotx/tray/notifications.py` — toast notifications for NOTIFY-tier actions

**Milestone:** Tray icon in system tray. Click → viewport shows shadow desktop. APPROVE actions show dialog with screenshot.

**Tests:** ~15 (QTest smoke tests)

---

### Phase 5 (Week 9-10): Task Planner & Router
**Goal:** Intelligent task decomposition + API-direct vs shadow-desktop routing.

**Build:**
- `neotx/planner/intent.py` — send to Alchemy `POST /chat` for intent parsing
- `neotx/planner/decomposer.py` — complex task → ordered sub-steps
- `neotx/router/task_router.py` — `requires_gui?` → shadow : api_direct
- `neotx/planner/memory.py` — ChromaDB for task patterns

**Key:** NEO-TX does NOT create its own Ollama connection. It uses Alchemy as the LLM gateway.

**Milestone:** "Send my hours to work" decomposes into: gather hours → compose email (shadow) → fill form (shadow) → APPROVE gate → send (shadow).

**Tests:** ~25

---

## Alchemy Integration (API Boundary)

| NEO-TX Need | Alchemy Endpoint |
|---|---|
| Text generation | `POST /chat` |
| Vision analysis | `POST /vision/analyze` |
| Model status | `GET /models` |
| Voice transcription | `POST /voice/transcribe` |
| Voice synthesis | `POST /voice/speak` |
| Health check | `GET /health` |

---

## Dependencies

**WSL2 Ubuntu:** `xvfb fluxbox x11vnc xdotool scrot xclip firefox-esr`

**Python (Windows host):**
- Core: `pydantic pydantic-settings fastapi uvicorn httpx websockets Pillow`
- Tray: `PyQt6 PyQt6-WebEngine`
- Planner: `chromadb`

**Ollama (via Alchemy):** UI-TARS-72B (CPU), Qwen2.5-Coder-14B (GPU), Qwen3-8B (GPU swapped)

---

## Hardware Budget

```
GPU (RTX 4070, 12GB VRAM):
  Qwen2.5-Coder-14B (resident)  = 9.4GB
  Qwen3-8B (on-demand, swapped) = 5.2GB
  Whisper large-v3 (on-demand)   = 3GB  (managed by Alchemy)

CPU (i9-13900K, 128GB RAM):
  UI-TARS-72B Q4_K_M (resident)  = ~42GB
  Piper TTS (tiny)               = ~50MB
  Remaining                       = ~86GB free
```

---

## Future: Adapter Architecture

Apple-inspired pattern — one base model resident, tiny LoRA adapters hot-swap per request:

```
Qwen2.5-Coder-14B (base, resident ~9GB VRAM)
  ├─ Adapter: Routing classifier (~200MB, 1-5ms swap)
  ├─ Adapter: Code understanding (~200MB)
  ├─ Adapter: Doc classification (~200MB)
  └─ Adapter: Intent parser (~200MB)
```

Requires llama.cpp server (Ollama doesn't support LoRA hot-swap yet). Train with Unsloth. This replaces regex-based triviality detection with learned routing.

---

## Verification

1. **Phase 1:** Run `demo.py` → view shadow desktop at localhost:6080
2. **Phase 2:** Give agent "open Firefox, search for X" → watch it execute
3. **Phase 3:** Agent pauses before sending email → approval dialog
4. **Phase 4:** Right-click tray → viewport shows shadow desktop live
5. **Phase 5:** "Send my hours to work" decomposes and routes correctly
