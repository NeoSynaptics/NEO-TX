# AlchemyVoice — Claude Session Guide

## What This Is
Smart AI interface — the user-facing layer. Voice, fast GPU models, tray widget, approval gates. Delegates heavy GUI work to Alchemy (CPU-side shadow desktop) via API.

## Key Paths
- Config: `config/settings.py` (port 8100, GPU models, voice)
- Server: `alchemyvoice/server.py` (FastAPI orchestrator)
- Voice: `alchemyvoice/voice/` (wake word, Whisper STT, Piper TTS)
- Models: `alchemyvoice/models/` (14B conversational + small specialized, GPU)
- Constitution: `alchemyvoice/constitution/` (AUTO / NOTIFY / APPROVE gates)
- Tray: `alchemyvoice/tray/` (PyQt6 system tray + noVNC viewport)
- Planner: `alchemyvoice/planner/` (task decomposition via Alchemy)
- Router: `alchemyvoice/router/` (direct answer vs shadow desktop)
- Bridge: `alchemyvoice/bridge/` (HTTP + WS client to Alchemy)

## GPU Models (owned by AlchemyVoice)
- **14B conversational** → GPU (12GB VRAM) → semantic understanding, user interaction
- **Whisper large-v3** → GPU (on-demand, ~3GB) → speech-to-text
- **Small specialized** → GPU (on-demand, ~2B) → specific fast tasks
- **Piper TTS** → CPU (~50MB) → text-to-speech

## What AlchemyVoice Does NOT Own
- Shadow desktop (WSL2 + Xvfb) → Alchemy
- Vision agent (UI-TARS-72B) → Alchemy
- Agent loop (screenshot → click) → Alchemy

## Alchemy Integration
AlchemyVoice sends GUI tasks to Alchemy (port 8000). Alchemy runs the shadow desktop and vision agent. For APPROVE-tier actions, Alchemy pauses and asks AlchemyVoice for approval.

## Commands
```bash
make dev      # Install all deps
make test     # Run pytest
make server   # Start AlchemyVoice on :8100
```
