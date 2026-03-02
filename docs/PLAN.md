# NEO-TX: Implementation Plan

## Context

NEO-TX is the smart user-facing AI interface. It handles voice, conversation (14B GPU model), tray widget, and approval gates. For heavy GUI work, it delegates to [Alchemy](https://github.com/NeoSynaptics/Alchemy) (CPU-side shadow desktop + UI-TARS-72B).

**Local-first.** No cloud APIs. GPU models for fast interaction, CPU models for heavy lifting.

---

## Architecture

```
NEO-TX (GPU side, port 8100)          Alchemy (CPU side, port 8000)
┌────────────────────────────┐        ┌────────────────────────────┐
│  Voice pipeline            │        │  Shadow desktop (WSL2)     │
│  14B conversational model  │  HTTP  │  UI-TARS-72B agent loop    │
│  Tray widget + viewport    │◄──────►│  Screenshot → click/type   │
│  Approval gates            │        │  xdotool actions           │
│  Small specialized models  │        │                            │
└────────────────────────────┘        └────────────────────────────┘
```

### Resource Split

| Resource | Owner | What |
|----------|-------|------|
| GPU (12GB VRAM) | **NEO-TX** | 14B conversational + Whisper + small models |
| CPU (128GB RAM) | **Alchemy** | UI-TARS-72B (~42GB) + shadow desktop |

GPU and CPU work in parallel — never block each other.

---

## Phase Plan

### Phase 1 (Week 1-2): Voice Pipeline
**Goal:** "Hey Neo" → Whisper STT → text response → Piper TTS.

**Build:**
- `neotx/voice/wake_word.py` — openWakeWord ("hey_neo", CPU, ~10MB)
- `neotx/voice/listener.py` — faster-whisper (large-v3, CUDA, on-demand)
- `neotx/voice/speaker.py` — Piper TTS (CPU, en_US-lessac-medium)
- `neotx/voice/pipeline.py` — VAD → STT → 14B model → TTS

**Milestone:** Say "Hey Neo, what time is it?" → NEO-TX speaks the answer.

**Tests:** ~20

---

### Phase 2 (Week 3-4): 14B Conversational Model
**Goal:** Fast, semantic conversation via GPU model. NOT a coding model.

**Build:**
- `neotx/models/manager.py` — GPU model lifecycle (load, unload, health, VRAM tracking)
- `neotx/models/conversation.py` — 14B chat interface (context window, history)
- `neotx/router/task_router.py` — direct answer vs delegate to Alchemy

**Key:** 14B understands intent semantically. "Send my hours to work" → knows this needs GUI → routes to Alchemy. "What's 2+2?" → answers directly.

**Milestone:** Voice + 14B conversation works end-to-end.

**Tests:** ~25

---

### Phase 3 (Week 5-6): Alchemy Bridge + Approval Gates
**Goal:** NEO-TX sends GUI tasks to Alchemy. Alchemy sends approval requests back.

**Build:**
- `neotx/bridge/client.py` — HTTP client to Alchemy (port 8000)
- `neotx/bridge/ws_client.py` — WebSocket for real-time task updates + approval requests
- `neotx/constitution/gates.py` — 3-tier classification (AUTO/NOTIFY/APPROVE)
- `neotx/constitution/rules.py` — action → tier mapping
- `neotx/constitution/audit.py` — JSONL audit log

**Tiers:**
- **AUTO:** click, type, scroll — Alchemy executes silently
- **NOTIFY:** open app, download — Alchemy executes, NEO-TX shows notification
- **APPROVE:** send email, delete, purchase — Alchemy pauses, NEO-TX asks user

**Milestone:** Send a GUI task → Alchemy runs it → approval dialog appears before dangerous action.

**Tests:** ~25

---

### Phase 4 (Week 7-8): Tray Widget & Viewport
**Goal:** PyQt6 system tray with noVNC viewport and approval dialogs.

**Build:**
- `neotx/tray/widget.py` — QSystemTrayIcon (Show Viewport / Pause / Resume / Quit)
- `neotx/tray/viewport.py` — QWebEngineView → `localhost:6080/vnc.html?autoconnect=true`
- `neotx/tray/approval_dialog.py` — screenshot preview + approve/deny (60s timeout)
- `neotx/tray/notifications.py` — toast notifications for NOTIFY-tier actions

**Milestone:** Tray icon in system tray. Click → viewport shows shadow desktop. APPROVE actions show dialog with screenshot.

**Tests:** ~15

---

### Phase 5 (Week 9-10): Task Planner & Small Models
**Goal:** Intelligent task decomposition + small specialized GPU models for specific fast tasks.

**Build:**
- `neotx/planner/intent.py` — intent parsing via 14B model
- `neotx/planner/decomposer.py` — complex task → ordered sub-steps
- `neotx/models/specialized.py` — small model hot-swap framework (~2B models)
- `neotx/planner/memory.py` — ChromaDB for task patterns

**Future:** LoRA adapter hot-swap via llama.cpp (when Ollama supports it, or switch to llama.cpp server).

**Milestone:** "Send my hours to work" decomposes into steps, routes correctly between direct answers and Alchemy GUI tasks.

**Tests:** ~25

---

## Alchemy Integration (API Boundary)

| NEO-TX Need | Alchemy Endpoint |
|---|---|
| Submit GUI task | `POST /vision/task` |
| Single screenshot analysis | `POST /vision/analyze` |
| Task status | `GET /vision/task/{id}/status` |
| Shadow desktop control | `POST /shadow/start\|stop` |
| Shadow desktop health | `GET /shadow/health` |
| Screenshot capture | `GET /shadow/screenshot` |
| Model status | `GET /models` |

---

## Hardware Budget

```
GPU (RTX 4070, 12GB VRAM) — owned by NEO-TX:
  14B conversational (resident)   = ~9GB
  Whisper large-v3 (on-demand)    = ~3GB  (swaps with 14B)
  Small models (on-demand)        = ~2GB  (swaps)

CPU (i9-13900K, 128GB RAM) — owned by Alchemy:
  UI-TARS-72B Q4_K_M (resident)   = ~42GB
  Piper TTS (tiny)                 = ~50MB
  Shadow desktop                   = minimal
  Remaining                        = ~86GB free
```

---

## Verification

1. **Phase 1:** Say "Hey Neo, what time is it?" → TTS speaks answer
2. **Phase 2:** Natural conversation, intent detection, routing decisions
3. **Phase 3:** GUI task delegated → Alchemy runs it → approval dialog works
4. **Phase 4:** Tray icon → viewport shows shadow desktop live
5. **Phase 5:** Complex task decomposes and routes correctly
