"""Voice pipeline — state machine orchestrator.

IDLE → LISTENING → RECORDING → PROCESSING → SPEAKING → IDLE (loop)

Runs as a background asyncio task. Feeds transcribed speech into
SmartRouter, streams response to Piper TTS.
"""

from __future__ import annotations

import asyncio
import logging
from enum import Enum
from uuid import UUID, uuid4

from neotx.models.schemas import ChatRequest
from neotx.router.router import SmartRouter
from neotx.voice.audio import AudioStream
from neotx.voice.listener import SpeechListener
from neotx.voice.stt import WhisperSTT
from neotx.voice.tts import PiperTTS
from neotx.voice.wake_word import WakeWordDetector

logger = logging.getLogger(__name__)


class PipelineState(str, Enum):
    IDLE = "idle"
    LISTENING = "listening"
    RECORDING = "recording"
    PROCESSING = "processing"
    SPEAKING = "speaking"


class VoicePipeline:
    """Orchestrates the full voice loop: wake → record → transcribe → route → speak."""

    def __init__(
        self,
        router: SmartRouter,
        wake_word: WakeWordDetector,
        listener: SpeechListener,
        stt: WhisperSTT,
        tts: PiperTTS,
        audio_stream: AudioStream,
    ) -> None:
        self._router = router
        self._wake_word = wake_word
        self._listener = listener
        self._stt = stt
        self._tts = tts
        self._audio = audio_stream

        self._state = PipelineState.IDLE
        self._task: asyncio.Task | None = None
        self._conversation_id: UUID = uuid4()

    @property
    def state(self) -> PipelineState:
        return self._state

    @property
    def is_running(self) -> bool:
        return self._task is not None and not self._task.done()

    @property
    def conversation_id(self) -> UUID:
        return self._conversation_id

    async def start(self) -> None:
        """Start the voice pipeline as a background task."""
        if self.is_running:
            logger.warning("Voice pipeline already running")
            return

        self._conversation_id = uuid4()
        await self._audio.start()
        self._task = asyncio.create_task(self._loop(), name="voice-pipeline")
        logger.info("Voice pipeline started (conversation=%s)", self._conversation_id)

    async def stop(self) -> None:
        """Gracefully stop the voice pipeline."""
        if self._task and not self._task.done():
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        await self._audio.stop()
        self._state = PipelineState.IDLE
        self._task = None
        logger.info("Voice pipeline stopped")

    async def _loop(self) -> None:
        """Main pipeline loop. Runs until cancelled."""
        try:
            while True:
                await self._cycle()
        except asyncio.CancelledError:
            logger.info("Voice pipeline cancelled")
            raise
        except Exception:
            logger.exception("Voice pipeline error")
            self._state = PipelineState.IDLE

    async def _cycle(self) -> None:
        """One full cycle: listen → record → transcribe → route → speak."""
        # 1. Wait for wake word
        self._state = PipelineState.LISTENING
        await self._wake_word.listen(self._audio)

        # 2. Record speech
        self._state = PipelineState.RECORDING
        audio_bytes = await self._listener.record(self._audio)

        if len(audio_bytes) < 1600:  # Less than 0.1s of audio — ignore
            logger.debug("Recording too short, ignoring")
            return

        # 3. Transcribe
        self._state = PipelineState.PROCESSING
        text = await self._stt.transcribe(audio_bytes)

        if not text.strip():
            logger.debug("Empty transcription, ignoring")
            return

        logger.info("User said: %s", text)

        # 4. Route through SmartRouter
        request = ChatRequest(
            message=text,
            conversation_id=self._conversation_id,
            source="voice",
        )

        # 5. Stream response to TTS
        self._state = PipelineState.SPEAKING

        async def _response_chunks():
            async for chunk in self._router.route_stream(request):
                if chunk.content and not chunk.done:
                    yield chunk.content
                elif chunk.content and chunk.done:
                    yield chunk.content

        await self._tts.speak_streamed(_response_chunks(), self._audio)

        self._wake_word.reset()
