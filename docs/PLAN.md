# NEO-TX: Shadow Desktop Implementation Plan

## Context

Every existing computer-use agent (Claude Computer Use, OpenAI Operator) hijacks the user's screen. NEO-TX doesn't. The AI gets its own hidden virtual desktop — a "shadow" of the real desktop — where it operates GUI apps autonomously. The user keeps their screen. They only intersect at approval gates and an optional viewport.

This is a new standalone repo (NeoSynaptics/NEO-TX) that connects to the existing AlchemyGoldOS backend (port 8000) for LLM routing, auth, project registry, and WebSocket relay — no infrastructure duplication.

**Platform:** Windows 11 Pro → Shadow desktop runs inside **WSL2 + Xvfb** (direct port of Linux spec, zero security flags, proven stack).

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
│   └── settings.py                    # Pydantic Settings (port 8100, WSL2 config, API keys)
│
├── neotx/
│   ├── __init__.py
│   ├── server.py                      # NEO-TX FastAPI server (port 8100, thin orchestrator)
│   │
│   ├── shadow/                        # Phase 1: Shadow Desktop
│   │   ├── controller.py             # Start/stop/health Xvfb+Fluxbox+x11vnc+noVNC
│   │   ├── display.py                # Xvfb display manager
│   │   ├── vnc.py                    # x11vnc + noVNC bridge
│   │   ├── wsl.py                    # WSL2 command runner (Windows→WSL2 bridge)
│   │   └── health.py                 # Service health checks
│   │
│   ├── agent/                         # Phase 2: Model B (visuomotor agent)
│   │   ├── loop.py                   # screenshot → reason → act → observe cycle
│   │   ├── claude_backend.py         # Claude Computer Use API wrapper
│   │   ├── local_backend.py          # Local vision model (Phase 6)
│   │   ├── actions.py                # click/type/scroll/drag via xdotool in WSL2
│   │   ├── screenshot.py             # Capture from Xvfb
│   │   └── prompts.py                # System prompts for Model B
│   │
│   ├── constitution/                  # Defense Constitution (approval gates)
│   │   ├── gates.py                  # 3-tier: AUTO / NOTIFY / APPROVE
│   │   ├── rules.py                  # Action classification
│   │   └── audit.py                  # JSONL audit log
│   │
│   ├── tray/                          # Phase 3: System Tray Widget
│   │   ├── widget.py                 # PyQt6 system tray icon + menu
│   │   ├── viewport.py              # noVNC viewport (QWebEngineView)
│   │   ├── notifications.py         # Toast notifications
│   │   └── approval_dialog.py       # Modal approve/deny dialog
│   │
│   ├── voice/                         # Phase 4: Voice Interface
│   │   ├── wake_word.py             # "Hey Neo" detection (openWakeWord)
│   │   ├── listener.py              # Whisper STT
│   │   ├── speaker.py               # Piper TTS (CPU, lightweight)
│   │   └── pipeline.py              # VAD → STT → Planner → TTS
│   │
│   ├── planner/                       # Phase 5: Model A (LLM Planner)
│   │   ├── intent.py                # Intent parser via AlchemyGoldOS gateway
│   │   ├── decomposer.py            # Task → sub-steps
│   │   └── memory.py                # ChromaDB session memory
│   │
│   ├── router/                        # Phase 5: Task Router
│   │   └── task_router.py           # API-direct vs shadow-desktop decision
│   │
│   └── bridge/                        # AlchemyGoldOS integration
│       ├── client.py                # HTTP client to port 8000
│       ├── ws_client.py             # WebSocket (project subscribe, approval relay)
│       └── auth.py                  # Bearer token management
│
├── wsl/                               # WSL2 setup scripts
│   ├── setup.sh                      # Install Xvfb, Fluxbox, x11vnc, noVNC
│   ├── start_shadow.sh              # Start shadow desktop services
│   ├── stop_shadow.sh               # Stop services
│   └── health_check.sh              # Verify all running
│
├── tests/
│   ├── conftest.py
│   ├── test_shadow/
│   ├── test_agent/
│   ├── test_constitution/
│   ├── test_tray/
│   ├── test_voice/
│   ├── test_planner/
│   └── test_bridge/
│
├── scripts/
│   ├── install_wsl.ps1              # Ensure WSL2 + Ubuntu
│   ├── install_deps.sh
│   └── demo.py                      # Phase 1 PoC demo
│
└── docs/
    ├── ARCHITECTURE.md
    ├── WSL2_SETUP.md
    └── APPROVAL_GATES.md
```

---

## Architecture: WSL2 Shadow Desktop

```
Windows 11 Host                              WSL2 Ubuntu
┌──────────────────────────┐    localhost    ┌──────────────────────────┐
│                          │    :6080        │                          │
│  NEO-TX Python           │◄──────────────►│  noVNC (websockify)      │
│  (tray + orchestrator    │                 │    ↓                     │
│   on port :8100)         │    localhost    │  x11vnc (:5900)          │
│                          │    :5900       │    ↓                     │
│  AlchemyGoldOS           │◄──────────────►│  Xvfb (:99)              │
│  (FastAPI on :8000)      │                 │    + Fluxbox (WM)        │
│                          │                 │    + Firefox, LibreOffice│
└──────────────────────────┘                 └──────────────────────────┘
```

**WslRunner** (Windows→WSL2 bridge): all shadow desktop commands go through `wsl -d Ubuntu -- bash -c "DISPLAY=:99 xdotool ..."`. Screenshots captured via `scrot` inside WSL2, piped back as PNG bytes.

---

## Phase Plan

### Phase 1 (Week 1-2): Shadow Desktop PoC
**Goal:** Xvfb running in WSL2, controllable from Windows, viewable via noVNC.

**Build:**
- `neotx/shadow/wsl.py` — WslRunner class (`run()`, `run_bg()`, `is_available()`)
- `neotx/shadow/controller.py` — ShadowDesktopController (`start()`, `stop()`, `health()`, `screenshot()`)
- `wsl/setup.sh` + `wsl/start_shadow.sh` + `wsl/stop_shadow.sh`
- `scripts/demo.py` — starts shadow, opens Firefox, user views at localhost:6080

**Milestone:** `python scripts/demo.py` starts hidden desktop → opens Firefox → viewable at `http://localhost:6080/vnc.html`

**Tests:** ~20 (WslRunner, controller lifecycle, health checks)

---

### Phase 2 (Week 3-4): Model B — Claude Computer Use
**Goal:** Agent loop: screenshot → Claude API → parse action → xdotool → repeat.

**Build:**
- `neotx/agent/loop.py` — perceive-plan-act cycle (max 50 steps)
- `neotx/agent/claude_backend.py` — Anthropic Computer Use API (`computer_20241022` tool)
- `neotx/agent/actions.py` — xdotool primitives (click, type, key, scroll, drag)
- `neotx/agent/screenshot.py` — capture + base64 encode
- `neotx/constitution/gates.py` — 3-tier classification (AUTO/NOTIFY/APPROVE)
- `neotx/constitution/audit.py` — JSONL action log

**Constitution tiers (from spec):**
- **AUTO:** click, type, scroll, screenshot, navigate — execute silently
- **NOTIFY:** open app, download file, create file — execute + notify user
- **APPROVE:** send email, delete file, submit form, purchase, post publicly — pause + ask

**Pattern to reuse:** `gold/gate/ollama_gate.py` from AlchemyGoldOS

**Milestone:** "Open Firefox and search for weather in Stockholm" works end-to-end.

**Tests:** ~30 (loop, action parsing, constitution gates, audit trail)

---

### Phase 3 (Week 5-6): Tray Widget & Viewport
**Goal:** PyQt6 system tray with noVNC viewport and approval dialogs.

**Build:**
- `neotx/tray/widget.py` — QSystemTrayIcon (Show Viewport / Pause / Resume / Quit)
- `neotx/tray/viewport.py` — QWebEngineView → `localhost:6080/vnc.html?autoconnect=true`
- `neotx/tray/approval_dialog.py` — screenshot preview + approve/deny (60s timeout)
- `neotx/bridge/ws_client.py` — connect to `ws://localhost:8000/ws/chat`, relay approval_request/response to phone via AlchemyGoldOS

**AlchemyGoldOS integration:** Approval requests relay through existing WS protocol → phone can approve from AlchemyCode app.

**Milestone:** Tray icon in system tray. Click → viewport shows shadow desktop. APPROVE actions show dialog with screenshot.

**Tests:** ~15 (QTest smoke tests)

---

### Phase 4 (Week 7-8): Voice Interface
**Goal:** "Hey Neo, send an email to work" triggers the full pipeline.

**Build:**
- `neotx/voice/wake_word.py` — openWakeWord (CPU, "hey_neo")
- `neotx/voice/listener.py` — faster-whisper (large-v3, CUDA)
- `neotx/voice/speaker.py` — Piper TTS (CPU, en_US-lessac-medium)
- `neotx/voice/pipeline.py` — VAD → STT → planner → TTS

**Pattern to reuse:** `gold/voice/pipeline.py` from AlchemyGoldOS

**Milestone:** Voice command → STT → Ollama via AlchemyGoldOS → TTS response.

**Tests:** ~20

---

### Phase 5 (Week 9-10): Model A & Task Router
**Goal:** Intelligent task decomposition + API-direct vs shadow-desktop routing.

**Build:**
- `neotx/planner/intent.py` — send to AlchemyGoldOS `POST /chat/completions` (NOT direct Ollama)
- `neotx/planner/decomposer.py` — complex task → ordered sub-steps
- `neotx/router/task_router.py` — `requires_gui?` → shadow : api_direct
- `neotx/planner/memory.py` — ChromaDB for task patterns

**Key:** NEO-TX does NOT create its own Ollama connection. It uses AlchemyGoldOS as the LLM gateway (shared routing, model cache, triviality detection).

**Milestone:** "Send my hours to work" decomposes into: gather hours (api) → compose email (shadow) → fill form (shadow) → APPROVE gate → send (shadow).

**Tests:** ~25

---

### Phase 6 (Week 11-14): Local Model B
**Goal:** Replace Claude Computer Use with local vision model.

**Build:**
- `neotx/agent/local_backend.py` — Qwen2.5-VL-7B via Ollama (fits in 12GB VRAM)

**Approach:** Backend-agnostic agent loop — swap `ClaudeComputerBackend` for `LocalVisionBackend` via config.

**Milestone:** Common GUI tasks run locally. Claude API only for complex multi-step tasks.

**Tests:** ~15

---

## AlchemyGoldOS Integration (What Exists — Don't Reinvent)

| NEO-TX Need | AlchemyGoldOS Endpoint | Module |
|---|---|---|
| LLM routing | `POST /chat/completions` or WS `/ws/chat` | `gold/router/gateway.py` |
| Action safety | `POST /gate/review` | `gold/gate/ollama_gate.py` |
| Project registry | `POST /director/projects/register` | `gold/tasks/projects.py` |
| Context buffer | `POST /director/context-append` | `gold/tasks/projects.py` |
| Phone approval relay | WS `approval_request` type | `gold/server.py` |
| Auth | Bearer token | `gold/security/auth.py` |
| Triviality detection | Hybrid router | `gold/hybrid/triviality.py` |

---

## Dependencies

**WSL2 Ubuntu:** `xvfb fluxbox x11vnc xdotool scrot xclip firefox-esr`

**Python (Windows host):**
- Core: `pydantic pydantic-settings fastapi uvicorn httpx websockets`
- Agent: `anthropic Pillow`
- Tray: `PyQt6 PyQt6-WebEngine`
- Voice: `faster-whisper piper-tts openwakeword sounddevice webrtcvad`
- Planner: `chromadb`
- Local vision (Phase 6): `transformers torch accelerate`

**Ollama (via AlchemyGoldOS):** qwen3:8b (planner), qwen2.5-coder:14b (safety review), qwen2.5-vl:7b (Phase 6 local vision)

---

## Hardware Budget (RTX 4070 12GB)

- Ollama 14B (resident): ~9.4GB VRAM
- Whisper large-v3 (on-demand): ~3GB
- Qwen2.5-VL-7B (Phase 6, on-demand): ~4GB
- Scheduling: Ollama unloads idle models after 5min. Whisper loads only during speech. Vision model loads only during agent loop.

---

## Verification

1. **Phase 1:** Run `demo.py` → view shadow desktop at localhost:6080 from Windows browser
2. **Phase 2:** Give agent "open Firefox, search for X" → watch it execute via viewport
3. **Phase 3:** Right-click tray → Open Viewport. Trigger APPROVE action → dialog appears
4. **Phase 4:** Say "Hey Neo, what time is it?" → TTS speaks answer
5. **Phase 5:** Complex task routes correctly (file ops → API, browser → shadow)
6. **Phase 6:** Same tasks work with local vision model, no Claude API calls

---

## First Commit

Push to NeoSynaptics/NEO-TX:
- This plan as `docs/PLAN.md`
- `README.md` with project overview + quickstart
- `CLAUDE.md` with session nav
- `.gitignore` + `pyproject.toml` + `.env.example`
- Empty package scaffold (`neotx/__init__.py`, `config/settings.py`)
- WSL2 setup scripts (`wsl/setup.sh`, `wsl/start_shadow.sh`, `wsl/stop_shadow.sh`)
