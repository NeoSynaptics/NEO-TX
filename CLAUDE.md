# NEO-TX — Claude Session Guide

## What This Is
Smart AI interface — the user-facing layer. Voice, fast GPU models, tray widget, approval gates. Delegates heavy GUI work to Alchemy (CPU-side shadow desktop) via API.

## Key Paths
- Config: `config/settings.py` (port 8100, GPU models, voice)
- Server: `neotx/server.py` (FastAPI orchestrator)
- Voice: `neotx/voice/` (wake word, Whisper STT, Piper TTS)
- Models: `neotx/models/` (14B conversational + small specialized, GPU)
- Constitution: `neotx/constitution/` (AUTO / NOTIFY / APPROVE gates)
- Tray: `neotx/tray/` (PyQt6 system tray + noVNC viewport)
- Planner: `neotx/planner/` (task decomposition via Alchemy)
- Router: `neotx/router/` (direct answer vs shadow desktop)
- Bridge: `neotx/bridge/` (HTTP + WS client to Alchemy)

## GPU Models (owned by NEO-TX)
- **14B conversational** → GPU (12GB VRAM) → semantic understanding, user interaction
- **Whisper large-v3** → GPU (on-demand, ~3GB) → speech-to-text
- **Small specialized** → GPU (on-demand, ~2B) → specific fast tasks
- **Piper TTS** → CPU (~50MB) → text-to-speech

## What NEO-TX Does NOT Own
- Shadow desktop (WSL2 + Xvfb) → Alchemy
- Vision agent (UI-TARS-72B) → Alchemy
- Agent loop (screenshot → click) → Alchemy

## Alchemy Integration
NEO-TX sends GUI tasks to Alchemy (port 8000). Alchemy runs the shadow desktop and vision agent. For APPROVE-tier actions, Alchemy pauses and asks NEO-TX for approval.

## Commands
```bash
make dev      # Install all deps
make test     # Run pytest
make server   # Start NEO-TX on :8100
```
