# AlchemyVoice Roadmap

## Done

### Phase 0 — API Contract
Schemas (synced with Alchemy), callback endpoints, Alchemy client.

### Phase 1 — Voice Pipeline
Wake word ("Hey Neo"), VAD recording, Whisper STT, Piper TTS.

### Phase 2 — Smart Model Routing
14B classifier + provider abstraction + streaming.

### Phase 3 — System Tray
PyQt6 tray icon, approval dialogs, noVNC viewport into shadow desktop.

### Phase 4 — Constitution + Planner
Safety rules (AUTO/NOTIFY/APPROVE), task decomposition via Alchemy.

### Schema Sync
VisionAction aligned with Alchemy (drag, scroll, hotkey fields).

**Current: 237 tests, 7 commits**

---

## Next

### Phase 5 — Pull Qwen3 14B + Wire Real Inference
**Goal:** Get the conversational model actually responding.

- [ ] Pull `qwen3:14b` via Ollama
- [ ] Wire the model provider to use real Ollama inference
- [ ] Test: user says "open spotify and play music" → AlchemyVoice responds "On it!" → delegates to Alchemy
- [ ] Test: user says "what's the weather?" → AlchemyVoice answers directly (no Alchemy needed)
- [ ] Verify the router correctly classifies direct-answer vs shadow-desktop tasks

### Phase 6 — Live End-to-End
**Goal:** Full loop from voice to visible action.

- [ ] Start both servers (Alchemy :8000, AlchemyVoice :8100)
- [ ] Say "Hey Neo, open Firefox and go to google.com"
- [ ] Watch: voice → STT → classify → delegate to Alchemy → shadow desktop executes → noVNC shows it → tray reports "Done!"
- [ ] Test approval flow: "Hey Neo, send an email" → Alchemy pauses → tray shows approval dialog → user approves/denies
- [ ] Fix any bridge issues between the two services

---

## Blocked / Waiting

- **Qwen3 14B not yet pulled** — needs `ollama pull qwen3:14b` (~9GB)
- **GPU memory budget** — 14B (~9GB) + Whisper (~3GB) = 12GB. Fits RTX 4070 but tight. May need model swapping via `keep_alive`.

---

## Not AlchemyVoice's Job

These belong to Alchemy:
- Shadow desktop (WSL2, Xvfb, Fluxbox)
- Vision agent loop (screenshot → UI-TARS → xdotool)
- Context routing (task categories, recovery, completion)
- Model inference for GUI actions (72B + 1.5-7B)
