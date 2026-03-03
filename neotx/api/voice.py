"""Voice control endpoints — start/stop/status for the voice pipeline."""

from __future__ import annotations

from fastapi import APIRouter, Request
from pydantic import BaseModel

router = APIRouter(prefix="/voice", tags=["voice"])


class VoiceStatus(BaseModel):
    state: str
    is_running: bool
    conversation_id: str | None = None
    voice_enabled: bool = True


@router.get("/status", response_model=VoiceStatus)
async def voice_status(req: Request) -> VoiceStatus:
    """Get current voice pipeline state."""
    pipeline = getattr(req.app.state, "voice_pipeline", None)
    if not pipeline:
        return VoiceStatus(state="idle", is_running=False, voice_enabled=False)

    return VoiceStatus(
        state=pipeline.state.value,
        is_running=pipeline.is_running,
        conversation_id=str(pipeline.conversation_id) if pipeline.is_running else None,
    )


@router.post("/start")
async def voice_start(req: Request):
    """Start the voice pipeline."""
    pipeline = getattr(req.app.state, "voice_pipeline", None)
    if not pipeline:
        return {"error": "Voice not available (voice_enabled=false or no audio device)"}

    if pipeline.is_running:
        return {"status": "already_running", "state": pipeline.state.value}

    await pipeline.start()
    return {"status": "started", "conversation_id": str(pipeline.conversation_id)}


@router.post("/stop")
async def voice_stop(req: Request):
    """Stop the voice pipeline."""
    pipeline = getattr(req.app.state, "voice_pipeline", None)
    if not pipeline:
        return {"error": "Voice not available"}

    if not pipeline.is_running:
        return {"status": "already_stopped"}

    await pipeline.stop()
    return {"status": "stopped"}
