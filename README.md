# NEO-TX

**Smart AI interface — voice, fast GPU models, tray widget, approval gates.**

NEO-TX is the user-facing layer. It talks to you (voice), understands you (14B conversational model on GPU), and delegates heavy GUI work to [Alchemy](https://github.com/NeoSynaptics/Alchemy) (CPU-side shadow desktop). You never interact with Alchemy directly — NEO-TX is your interface.

## How It Works

```
You: "Hey Neo, send an email to my work with my hours this week."

NEO-TX (GPU, fast):
1. Wake word detected → Whisper STT → text
2. 14B model interprets: "needs GUI work (email client)"
3. Sends task to Alchemy → shadow desktop starts working
4. Alchemy's agent loop fills in the email form...
5. Before clicking "Send" → approval request comes back to NEO-TX
6. Tray popup: "Send email to work@company.com?" → you approve
7. Alchemy clicks Send. Done. You never left your CAD/IDE/browser.
```

## What NEO-TX Owns

| Responsibility | Detail |
|----------------|--------|
| **Voice** | Whisper STT + Piper TTS + wake word ("Hey Neo") |
| **14B Conversational Model** | Fast semantic understanding on GPU (~9GB VRAM) |
| **Small Specialized Models** | Fast GPU models for specific tasks (~2B, hot-swap) |
| **Tray Widget** | PyQt6 system tray + noVNC viewport into shadow desktop |
| **Approval Gates** | AUTO / NOTIFY / APPROVE — non-bypassable constitution |
| **User Conversation** | Chat, intent parsing, task routing |

## What NEO-TX Does NOT Own

| Responsibility | Owner |
|----------------|-------|
| Shadow desktop (WSL2 + Xvfb) | **Alchemy** (CPU side) |
| Vision agent (UI-TARS-72B) | **Alchemy** (CPU side) |
| Agent loop (screenshot → click) | **Alchemy** (CPU side) |

## Architecture

```
┌───────────────────────────────────────────────┐
│                  NEO-TX                       │
│                  port 8100                    │
│                                               │
│  ┌──────────┐  ┌──────────┐  ┌────────────┐  │
│  │  Voice   │  │   14B    │  │   Tray     │  │
│  │          │  │  Convo   │  │   Widget   │  │
│  │ wake     │  │  Model   │  │            │  │
│  │ STT      │  │          │  │ viewport   │  │
│  │ TTS      │  │ semantic │  │ approvals  │  │
│  │          │  │ intent   │  │ notify     │  │
│  └────┬─────┘  └────┬─────┘  └─────┬──────┘  │
│       │             │              │          │
│  ┌────▼─────────────▼──────────────▼──────┐   │
│  │     Ollama GPU (localhost:11434)       │   │
│  │     14B conversational (~9GB VRAM)    │   │
│  │     + Whisper / small models (swap)    │   │
│  └────────────────────────────────────────┘   │
│       │                                       │
│       │ HTTP (GUI tasks)                      │
│       ▼                                       │
│  Alchemy (:8000) — CPU-side shadow desktop    │
└───────────────────────────────────────────────┘
```

## Defense Constitution

Every action from the shadow desktop goes through a 3-tier gate:

- **AUTO**: click, type, scroll, screenshot — execute silently
- **NOTIFY**: open app, download, create file — execute + notify user via tray
- **APPROVE**: send email, delete file, submit form, purchase — pause + ask user

Non-bypassable. Every action logged to JSONL audit trail.

## Quick Start

```bash
# 1. Clone
git clone https://github.com/NeoSynaptics/NEO-TX.git
cd NEO-TX

# 2. Install
pip install -e ".[all,dev]"

# 3. Make sure Alchemy is running on :8000
# (see https://github.com/NeoSynaptics/Alchemy)

# 4. Run
make server   # → http://localhost:8100
```

## Requirements

- Windows 11 Pro
- Python 3.12+
- RTX 4070 (12GB VRAM) — runs 14B model + Whisper
- [Alchemy](https://github.com/NeoSynaptics/Alchemy) running on port 8000

## Project Structure

```
neotx/
├── voice/          # Whisper STT + Piper TTS + wake word
├── models/         # GPU model management (14B + small specialized)
├── constitution/   # Defense Constitution (approval gates)
├── tray/           # PyQt6 system tray + viewport
├── planner/        # Task decomposition (via Alchemy API)
├── router/         # Task routing (direct answer vs shadow desktop)
├── bridge/         # Alchemy HTTP + WS client
└── server.py       # FastAPI orchestrator (port 8100)
```

## License

MIT — NeoSynaptics
