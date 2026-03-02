# NEO-TX — Shadow Desktop

**AI operates a hidden virtual desktop while you keep yours.**

Every existing computer-use agent hijacks the user's screen. NEO-TX doesn't. The AI gets its own hidden virtual desktop — a "shadow" of the real desktop — where it opens apps, fills forms, navigates browsers, and completes tasks. The user never sees any of this unless they choose to.

## How It Works

```
You: "Hey Neo, send an email to my work with my hours this week."

NEO-TX:
1. Opens a browser in the hidden shadow desktop
2. Navigates to webmail, composes the email
3. Pauses before clicking "Send" → asks for your approval
4. You approve (click, voice "yes", or inspect via viewport)
5. Email sent. You never left your CAD/IDE/browser.
```

A small tray icon sits in your system tray. You can:
- **Ignore it** — keep working, the AI finishes in the background
- **Glance** — a notification popup shows when a task is ready
- **Click** — opens a viewport showing the shadow desktop live
- **Talk** — voice commands for hands-free operation

## Architecture

```
Windows 11 Host                              WSL2 Ubuntu
┌──────────────────────────┐    localhost    ┌──────────────────────────┐
│  NEO-TX (tray + server)  │◄──────────────►│  Xvfb (virtual desktop)  │
│  AlchemyGoldOS (:8000)   │◄──────────────►│  Fluxbox + x11vnc        │
│  Ollama (local LLM)      │                 │  noVNC + Firefox/apps    │
└──────────────────────────┘                 └──────────────────────────┘
```

- **Shadow Desktop**: Xvfb + Fluxbox + x11vnc + noVNC in WSL2
- **Model A** (LLM Planner): Ollama via AlchemyGoldOS — understands intent, decomposes tasks
- **Model B** (Visuomotor Agent): Claude Computer Use API → migrates to local vision model
- **Defense Constitution**: 3-tier approval gates (AUTO / NOTIFY / APPROVE)

## Quick Start

```bash
# 1. Clone
git clone https://github.com/NeoSynaptics/NEO-TX.git
cd NEO-TX

# 2. Install Python deps
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
- AlchemyGoldOS running on port 8000
- RTX 4070 (12GB VRAM) or equivalent

## Project Structure

```
neotx/
├── shadow/         # Phase 1: Shadow Desktop (WSL2 + Xvfb)
├── agent/          # Phase 2: Model B (visuomotor agent loop)
├── constitution/   # Defense Constitution (approval gates)
├── tray/           # Phase 3: PyQt6 system tray + viewport
├── voice/          # Phase 4: Whisper STT + Piper TTS
├── planner/        # Phase 5: Model A (intent + decomposition)
├── router/         # Phase 5: Task routing (API vs shadow)
├── bridge/         # AlchemyGoldOS integration (HTTP + WS)
└── server.py       # FastAPI orchestrator (port 8100)
```

## Implementation Phases

| Phase | What | When |
|-------|------|------|
| 1 | Shadow Desktop PoC (Xvfb + noVNC in WSL2) | Week 1-2 |
| 2 | Model B (Claude Computer Use agent loop) | Week 3-4 |
| 3 | Tray Widget & Viewport (PyQt6 + noVNC) | Week 5-6 |
| 4 | Voice Interface (Whisper + Piper + wake word) | Week 7-8 |
| 5 | Model A & Task Router (Ollama planner) | Week 9-10 |
| 6 | Local Model B (Qwen2.5-VL, no cloud) | Week 11-14 |

## License

MIT — NeoSynaptics
