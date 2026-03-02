# NEO-TX — Claude Session Guide

## What This Is
Shadow Desktop system — AI operates a hidden virtual desktop (WSL2 + Xvfb) while the user keeps their screen. Connects to Alchemy backend (port 8000) for LLM routing, vision analysis, and voice pipeline.

## Key Paths
- Config: `config/settings.py` (Pydantic Settings, port 8100)
- Server: `neotx/server.py` (FastAPI orchestrator)
- Shadow Desktop: `neotx/shadow/` (WSL2 bridge, controller, health)
- Agent Loop: `neotx/agent/` (screenshot → reason → act → observe)
- Constitution: `neotx/constitution/` (AUTO / NOTIFY / APPROVE gates)
- Tray: `neotx/tray/` (PyQt6 system tray + noVNC viewport)
- Planner: `neotx/planner/` (intent + task decomposition via Alchemy)
- Bridge: `neotx/bridge/` (HTTP + WS client to Alchemy)
- WSL2 Scripts: `wsl/` (setup, start, stop, health)
- Full Plan: `docs/PLAN.md`

## Alchemy Integration
NEO-TX is a **client** of Alchemy (port 8000). It does NOT run models directly.
- LLM routing: `POST http://localhost:8000/chat`
- Vision analysis: `POST http://localhost:8000/vision/analyze`
- Auth token: Bearer token from `.env`

## What NEO-TX Does NOT Own
- **Voice** — Alchemy handles STT/TTS/wake word. NEO-TX receives pre-parsed intent.
- **Models** — Alchemy manages Ollama. NEO-TX requests inference via API.
- **Routing** — Alchemy decides which model. NEO-TX only handles shadow-desktop tasks.

## Commands
```bash
make shadow-setup    # Install Xvfb/Fluxbox/x11vnc/noVNC in WSL2
make shadow-start    # Start shadow desktop
make shadow-stop     # Stop shadow desktop
make shadow-health   # Check all services
make test            # Run pytest
make demo            # Run Phase 1 demo
make server          # Start NEO-TX FastAPI on :8100
```

## Architecture
- Shadow desktop runs inside WSL2 Ubuntu (Xvfb :99 + Fluxbox + x11vnc + noVNC)
- Windows host runs: NEO-TX Python orchestrator + PyQt6 tray widget
- Communication: `wsl -d Ubuntu -- bash -c "DISPLAY=:99 xdotool ..."` for actions
- Screenshots: `scrot` inside WSL2 → PNG bytes piped to Windows
- Viewport: noVNC at `http://localhost:6080/vnc.html`

## Defense Constitution Tiers
- **AUTO**: click, type, scroll, screenshot — execute silently
- **NOTIFY**: open app, download, create file — execute + notify
- **APPROVE**: send email, delete file, submit form, purchase — pause + ask user
