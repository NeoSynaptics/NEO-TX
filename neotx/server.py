"""NEO-TX FastAPI server — smart AI interface on port 8100.

The user's single contact point. Delegates GUI work to Alchemy silently.
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config.settings import settings
from neotx.api import callbacks, chat, voice
from neotx.models.conversation import ConversationManager
from neotx.models.provider import AlchemyProvider, OllamaProvider
from neotx.models.registry import build_default_registry
from neotx.models.schemas import ModelLocation
from neotx.router.cascade import ConversationToVisionCascade
from neotx.router.router import SmartRouter

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize model registry, providers, router, and voice pipeline on startup."""
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

    # --- System tray (optional) ---
    app.state.tray_event_bus = None
    app.state.tray_manager = None
    app.state.alchemy_client = None

    if settings.tray_enabled:
        try:
            import asyncio

            from neotx.tray.events import TrayEventBus
            from neotx.tray.app import TrayManager

            event_bus = TrayEventBus()
            event_bus.bind_loop(asyncio.get_event_loop())
            app.state.tray_event_bus = event_bus

            tray_mgr = TrayManager(event_bus=event_bus, settings=settings)
            tray_mgr.start()
            app.state.tray_manager = tray_mgr
            logger.info("System tray started")
        except ImportError:
            logger.warning("PyQt6 not installed — tray disabled. Run: pip install -e '.[tray]'")
        except Exception:
            logger.exception("Failed to start system tray")

    # Store AlchemyClient on app.state for callback handlers
    app.state.alchemy_client = getattr(alchemy, '_alchemy_client', None)

    # --- Constitution (approval defense) ---
    from neotx.constitution.engine import ConstitutionEngine

    app.state.constitution = ConstitutionEngine()
    logger.info("Constitution engine loaded (%d rules)", len(app.state.constitution.rules))

    # --- Task planner ---
    from neotx.planner.planner import TaskPlanner

    app.state.planner = TaskPlanner()
    logger.info("Task planner initialized")

    # --- Voice pipeline (optional) ---
    app.state.voice_pipeline = None
    if settings.voice_enabled:
        try:
            from neotx.voice.audio import AudioStream
            from neotx.voice.listener import SpeechListener
            from neotx.voice.pipeline import VoicePipeline
            from neotx.voice.stt import WhisperSTT
            from neotx.voice.tts import PiperTTS
            from neotx.voice.wake_word import WakeWordDetector

            audio_stream = AudioStream()
            app.state.voice_pipeline = VoicePipeline(
                router=app.state.router,
                wake_word=WakeWordDetector(
                    model_name=settings.wake_word,
                    threshold=settings.voice_wake_threshold,
                ),
                listener=SpeechListener(
                    vad_aggressiveness=settings.voice_vad_aggressiveness,
                    silence_ms=settings.voice_silence_ms,
                ),
                stt=WhisperSTT(
                    model_size=settings.whisper_model,
                    device=settings.whisper_device,
                ),
                tts=PiperTTS(model=settings.piper_model),
                audio_stream=audio_stream,
            )
            logger.info("Voice pipeline initialized (start via POST /voice/start)")
        except ImportError:
            logger.warning("Voice dependencies not installed — run: pip install -e '.[voice]'")
        except Exception:
            logger.exception("Failed to initialize voice pipeline")

    yield

    # Cleanup
    if app.state.voice_pipeline and app.state.voice_pipeline.is_running:
        await app.state.voice_pipeline.stop()

    if app.state.tray_manager and app.state.tray_manager.is_running:
        app.state.tray_manager.stop()

    await ollama.close()
    await alchemy.close()


app = FastAPI(
    title="NEO-TX",
    description="Smart AI interface — voice, conversation, approval gates, tray widget",
    version="0.4.0",
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
app.include_router(voice.router)


@app.get("/health")
async def health():
    return {"status": "ok", "version": "0.4.0"}
