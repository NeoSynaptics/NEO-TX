# NEO-TX — Claude Session Guide

## What This Is
Shadow Desktop system — AI operates a hidden virtual desktop (WSL2 + Xvfb) while the user keeps their screen. Connects to AlchemyGoldOS backend (port 8000) for LLM routing, auth, and WebSocket relay.

## Key Paths
- Config: `config/settings.py` (Pydantic Settings, port 8100)
- Server: `neotx/server.py` (FastAPI orchestrator)
- Shadow Desktop: `neotx/shadow/` (WSL2 bridge, controller, health)
- Agent Loop: `neotx/agent/loop.py` (screenshot → reason → act → observe)
- Constitution: `neotx/constitution/gates.py` (AUTO / NOTIFY / APPROVE)
- WSL2 Scripts: `wsl/` (setup, start, stop, health)
- Full Plan: `docs/PLAN.md`

## AlchemyGoldOS Integration
NEO-TX is a **client** of AlchemyGoldOS (port 8000). It does NOT create its own Ollama connection.
- LLM routing: `POST http://localhost:8000/chat/completions`
- Project registry: `POST http://localhost:8000/director/projects/register`
- WebSocket: `ws://localhost:8000/ws/chat?token=...`
- Auth token: Bearer token from `.env`

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
