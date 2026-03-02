"""NEO-TX FastAPI server — smart AI interface on port 8100.

The user's single contact point. Delegates GUI work to Alchemy silently.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from neotx.api import callbacks

app = FastAPI(
    title="NEO-TX",
    description="Smart AI interface — voice, conversation, approval gates, tray widget",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(callbacks.router)


@app.get("/health")
async def health():
    return {"status": "ok", "version": "0.1.0"}
