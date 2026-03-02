"""NEO-TX FastAPI server — thin orchestration layer on port 8100."""

from fastapi import FastAPI

app = FastAPI(
    title="NEO-TX",
    description="Smart AI interface — voice, conversation, approval gates, tray widget",
    version="0.1.0",
)


@app.get("/health")
async def health():
    return {"status": "ok", "version": "0.1.0"}
