"""Chat endpoints — /chat (non-streaming) and /chat/stream (SSE)."""

from __future__ import annotations

from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse

from neotx.models.schemas import ChatRequest, ChatResponse
from neotx.router.router import SmartRouter

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("/", response_model=ChatResponse)
async def chat(request: ChatRequest, req: Request) -> ChatResponse:
    """Non-streaming chat. Returns full response after inference completes."""
    smart_router: SmartRouter = req.app.state.router
    return await smart_router.route(request)


@router.post("/stream")
async def chat_stream(request: ChatRequest, req: Request) -> StreamingResponse:
    """Streaming chat via Server-Sent Events. Primary endpoint for real-time UX."""
    smart_router: SmartRouter = req.app.state.router

    async def event_generator():
        async for chunk in smart_router.route_stream(request):
            data = chunk.model_dump_json()
            yield f"data: {data}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
