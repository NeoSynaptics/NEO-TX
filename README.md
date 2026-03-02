# NEO-TX — Shadow Desktop

**AI operates a hidden virtual desktop while you keep yours.**

Every existing computer-use agent hijacks the user's screen. NEO-TX doesn't. The AI gets its own hidden virtual desktop — a "shadow" of the real desktop — where it opens apps, fills forms, navigates browsers, and completes tasks. The user never sees any of this unless they choose to.

## How It Works

```
You: "Hey Neo, send an email to my work with my hours this week."

Alchemy (voice):
1. Whisper STT captures your speech
2. 14B interprets intent → "needs GUI" → routes to NEO-TX

NEO-TX (shadow desktop):
3. Opens a browser in the hidden shadow desktop
4. UI-TARS-72B analyzes screenshots, clicks and types
5. Pauses before clicking "Send" → asks for your approval
6. You approve (tray widget or voice "yes")
7. Email sent. You never left your CAD/IDE/browser.
```

A small tray icon sits in your system tray. You can:
- **Ignore it** — keep working, the AI finishes in the background
- **Glance** — a notification popup shows when a task is ready
- **Click** — opens a viewport showing the shadow desktop live
- **Talk** — voice commands handled by Alchemy, routed here

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

### What Lives Where

| Concern | Where | Why |
|---------|-------|-----|
| Voice (STT/TTS) | **Alchemy** | General I/O, uses fast 14B GPU |
| Model routing | **Alchemy** | Shared across all tools |
| Shadow desktop | **NEO-TX** | WSL2 + Xvfb, desktop-specific |
| Agent loop | **NEO-TX** | Screenshot → reason → act cycle |
| Approval gates | **NEO-TX** | Action safety, tray integration |
| Tray widget | **NEO-TX** | Desktop UI element |

### Model Split

| Model | Hardware | Role | Called By |
|-------|----------|------|-----------|
| **UI-TARS-72B** | CPU (128GB RAM) | GUI agent — screenshot → action JSON | NEO-TX via Alchemy API |
| **Qwen2.5-Coder-14B** | GPU (12GB VRAM) | Planner, reasoning, voice interpretation | Alchemy directly |
| **Qwen3-8B** | GPU (swapped) | Fast trivial responses | Alchemy directly |

## Quick Start

```bash
# 1. Clone
git clone https://github.com/NeoSynaptics/NEO-TX.git
cd NEO-TX

# 2. Install
pip install -e ".[all,dev]"

# 3. Setup WSL2 shadow desktop
make shadow-setup

# 4. Start shadow desktop
make shadow-start

# 5. View in browser
# Open http://localhost:6080/vnc.html?autoconnect=true

# 6. Run demo
make demo
```

## Requirements

- Windows 11 Pro with WSL2 + Ubuntu
- Python 3.12+
- [Alchemy](https://github.com/NeoSynaptics/Alchemy) running on port 8000
- RTX 4070 (12GB VRAM) or equivalent
- 128GB RAM recommended (for UI-TARS-72B on CPU)

## Project Structure

```
neotx/
├── shadow/         # Shadow Desktop (WSL2 + Xvfb)
├── agent/          # Model B (visuomotor agent loop)
├── constitution/   # Defense Constitution (approval gates)
├── tray/           # PyQt6 system tray + viewport
├── planner/        # Intent + task decomposition (via Alchemy API)
├── router/         # Task routing (API vs shadow)
├── bridge/         # Alchemy integration (HTTP + WS)
└── server.py       # FastAPI orchestrator (port 8100)
```

## Implementation Phases

| Phase | What | When |
|-------|------|------|
| 1 | Shadow Desktop PoC (Xvfb + noVNC in WSL2) | Week 1-2 |
| 2 | Agent Loop + UI-TARS (local vision, screenshot → act) | Week 3-4 |
| 3 | Defense Constitution (AUTO / NOTIFY / APPROVE gates) | Week 5-6 |
| 4 | Tray Widget & Viewport (PyQt6 + noVNC) | Week 7-8 |
| 5 | Task Planner & Router (via Alchemy API) | Week 9-10 |

## Defense Constitution

Every agent action goes through a 3-tier gate:

- **AUTO**: click, type, scroll, screenshot — execute silently
- **NOTIFY**: open app, download, create file — execute + notify user
- **APPROVE**: send email, delete file, submit form, purchase — pause + ask user

Non-bypassable. Every action logged to JSONL audit trail.

## License

MIT — NeoSynaptics
