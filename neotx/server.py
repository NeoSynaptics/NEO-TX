"""NEO-TX FastAPI server — smart AI interface on port 8100.

The user's single contact point. Delegates GUI work to Alchemy silently.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config.settings import settings
from neotx.api import callbacks, chat
from neotx.models.conversation import ConversationManager
from neotx.models.provider import AlchemyProvider, OllamaProvider
from neotx.models.registry import build_default_registry
from neotx.models.schemas import ModelLocation
from neotx.router.cascade import ConversationToVisionCascade
from neotx.router.router import SmartRouter


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize model registry, providers, and router on startup."""
    registry = build_default_registry()

    ollama = OllamaProvider(
        host=settings.ollama_host,
        timeout=120.0,
        keep_alive=settings.gpu_model_keep_alive,
    )
    await ollama.start()

    alchemy = AlchemyProvider(
        base_url=settings.alchemy_host,
        timeout=30.0,
    )
    await alchemy.start()

    providers = {
        ModelLocation.GPU_LOCAL: ollama,
        ModelLocation.CPU_REMOTE: alchemy,
    }

    conversation_mgr = ConversationManager()

    app.state.router = SmartRouter(
        registry=registry,
        providers=providers,
        conversation_manager=conversation_mgr,
        cascades=[ConversationToVisionCascade()],
    )
    app.state.registry = registry
    app.state.providers = providers

    yield

    await ollama.close()
    await alchemy.close()


app = FastAPI(
    title="NEO-TX",
    description="Smart AI interface — voice, conversation, approval gates, tray widget",
    version="0.2.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(callbacks.router)
app.include_router(chat.router)


@app.get("/health")
async def health():
    return {"status": "ok", "version": "0.2.0"}
