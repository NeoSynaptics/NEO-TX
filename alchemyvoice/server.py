"""AlchemyVoice FastAPI server — smart AI interface on port 8100.

The user's single contact point. Delegates GUI work to Alchemy silently.
"""

import logging
from contextlib import asynccontextmanager

from config.logging import setup_logging
from fastapi import FastAPI

setup_logging()
from fastapi.middleware.cors import CORSMiddleware

from config.settings import settings
from alchemyvoice import __version__
from alchemyvoice.api import callbacks, chat, voice
from alchemyvoice.models.conversation import ConversationManager
from alchemyvoice.models.provider import AlchemyProvider, OllamaProvider
from alchemyvoice.models.registry import build_default_registry
from alchemyvoice.models.schemas import ModelLocation
from alchemyvoice.router.cascade import ConversationToVisionCascade
from alchemyvoice.router.router import SmartRouter

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

    # --- Knowledge retriever + event reporter (NEO-RX, optional) ---
    knowledge_retriever = None
    event_reporter = None
    if settings.knowledge_enabled:
        from alchemyvoice.knowledge.retriever import KnowledgeRetriever
        from alchemyvoice.knowledge.reporter import EventReporter

        knowledge_retriever = KnowledgeRetriever(
            neorx_host=settings.neorx_host,
            max_docs=settings.knowledge_max_docs,
        )
        event_reporter = EventReporter(neorx_host=settings.neorx_host)
        logger.info("Knowledge retrieval enabled (NEO-RX: %s)", settings.neorx_host)

    app.state.knowledge_retriever = knowledge_retriever
    app.state.event_reporter = event_reporter

    app.state.router = SmartRouter(
        registry=registry,
        providers=providers,
        conversation_manager=conversation_mgr,
        cascades=[ConversationToVisionCascade()],
        knowledge_retriever=knowledge_retriever,
        event_reporter=event_reporter,
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

            from alchemyvoice.tray.events import TrayEventBus
            from alchemyvoice.tray.app import TrayManager

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
    from alchemyvoice.constitution.engine import ConstitutionEngine

    app.state.constitution = ConstitutionEngine()
    logger.info("Constitution engine loaded (%d rules)", len(app.state.constitution.rules))

    # --- Task planner ---
    from alchemyvoice.planner.planner import TaskPlanner

    app.state.planner = TaskPlanner()
    logger.info("Task planner initialized")

    # --- Voice pipeline (optional) ---
    app.state.voice_pipeline = None
    app.state.vram_manager = None
    if settings.voice_enabled:
        try:
            from alchemyvoice.voice.audio import AudioStream
            from alchemyvoice.voice.listener import SpeechListener
            from alchemyvoice.voice.pipeline import VoicePipeline
            from alchemyvoice.voice.stt import WhisperSTT
            from alchemyvoice.voice.wake_word import WakeWordDetector

            audio_stream = AudioStream()
            stt = WhisperSTT(
                model_size=settings.whisper_model,
                device=settings.whisper_device,
            )

            # TTS engine selection
            fish_process = None
            if settings.tts_engine == "fish":
                from alchemyvoice.voice.fish_speech import FishSpeechProcess
                from alchemyvoice.voice.tts import FishSpeechTTS

                fish_process = FishSpeechProcess(
                    port=settings.fish_speech_port,
                    checkpoint_path=settings.fish_speech_checkpoint,
                    decoder_path=settings.fish_speech_decoder_path or None,
                    decoder_config=settings.fish_speech_decoder_config,
                    listen_host=settings.fish_speech_host,
                    startup_timeout=settings.fish_speech_startup_timeout,
                    compile=settings.fish_speech_compile,
                    python_exe=settings.fish_speech_python_exe or None,
                    working_dir=settings.fish_speech_dir or None,
                )
                tts = FishSpeechTTS(
                    fish_process=fish_process,
                    sample_rate=settings.fish_speech_sample_rate,
                    temperature=settings.fish_speech_temperature,
                    top_p=settings.fish_speech_top_p,
                    repetition_penalty=settings.fish_speech_repetition_penalty,
                    max_new_tokens=settings.fish_speech_max_new_tokens,
                    reference_id=settings.fish_speech_reference_id or None,
                    chunk_length=settings.fish_speech_chunk_length,
                )
            elif settings.tts_engine == "kokoro":
                from alchemyvoice.voice.tts import KokoroTTS

                tts = KokoroTTS(
                    base_url=f"http://{settings.kokoro_host}:{settings.kokoro_port}",
                    voice=settings.kokoro_voice,
                )
            else:
                from alchemyvoice.voice.tts import PiperTTS

                tts = PiperTTS(model=settings.piper_model)

            # VRAM Manager (single-GPU mode only)
            vram_mgr = None
            from alchemyvoice.voice.vram_manager import GPUMode, VRAMManager

            gpu_mode = GPUMode(settings.gpu_mode)
            if gpu_mode == GPUMode.SINGLE:
                vram_mgr = VRAMManager(
                    mode=gpu_mode,
                    ollama_host=settings.ollama_host,
                    gpu_model=settings.gpu_model,
                    keep_alive=settings.gpu_model_keep_alive,
                )
                await vram_mgr.start()
                app.state.vram_manager = vram_mgr
            else:
                # Dual-GPU: pre-start Fish Speech and pre-load Whisper
                # so they're warm and ready when voice pipeline starts.
                if fish_process:
                    logger.info("Dual-GPU: pre-starting Fish Speech...")
                    await fish_process.start()
                logger.info("Dual-GPU: pre-loading Whisper...")
                await stt.load()

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
                stt=stt,
                tts=tts,
                audio_stream=audio_stream,
                vram=vram_mgr,
                fish_process=fish_process,
            )
            logger.info(
                "Voice pipeline initialized (tts=%s, gpu_mode=%s)",
                settings.tts_engine,
                settings.gpu_mode,
            )

            # Auto-start voice pipeline so wake word listens immediately
            await app.state.voice_pipeline.start()
            logger.info("Voice pipeline auto-started")
        except ImportError:
            logger.warning("Voice dependencies not installed — run: pip install -e '.[voice]'")
        except Exception:
            logger.exception("Failed to initialize voice pipeline")

    yield

    # Cleanup
    if app.state.voice_pipeline and app.state.voice_pipeline.is_running:
        await app.state.voice_pipeline.stop()

    if app.state.vram_manager:
        await app.state.vram_manager.close()

    if app.state.tray_manager and app.state.tray_manager.is_running:
        app.state.tray_manager.stop()

    if app.state.knowledge_retriever:
        await app.state.knowledge_retriever.close()
    if app.state.event_reporter:
        await app.state.event_reporter.close()

    await ollama.close()
    await alchemy.close()


app = FastAPI(
    title="AlchemyVoice",
    description="Smart AI interface — voice, conversation, approval gates, tray widget",
    version=__version__,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(callbacks.router, prefix="/v1")
app.include_router(chat.router, prefix="/v1")
app.include_router(voice.router, prefix="/v1")


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "version": __version__,
        "knowledge_enabled": getattr(app.state, "knowledge_retriever", None) is not None,
    }
