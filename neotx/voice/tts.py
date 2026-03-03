"""Text-to-speech — Piper TTS wrapper.

CPU-only (~50MB). Supports sentence-buffered streaming for natural playback
while the 14B model is still generating text.
"""

from __future__ import annotations

import asyncio
import io
import logging
import re
import wave
from typing import AsyncIterator

import numpy as np

from neotx.voice.audio import AudioStream

logger = logging.getLogger(__name__)

_SENTENCE_END = re.compile(r"[.!?\n]")


class PiperTTS:
    """Synthesizes text to speech using Piper (CPU, local)."""

    def __init__(self, model: str = "en_US-lessac-medium") -> None:
        self._model_name = model
        self._voice = None
        self._audio_stream: AudioStream | None = None

    async def load(self, audio_stream: AudioStream | None = None) -> None:
        """Load the Piper voice model."""
        from pathlib import Path

        from piper import PiperVoice

        self._audio_stream = audio_stream

        # Resolve model path — accept bare name or full path
        model_path = self._model_name
        if not Path(model_path).exists():
            # Look in project models directory
            project_models = Path(__file__).resolve().parents[2] / "models" / "piper"
            candidate = project_models / f"{self._model_name}.onnx"
            if candidate.exists():
                model_path = str(candidate)
            else:
                raise FileNotFoundError(
                    f"Piper model not found: {self._model_name}. "
                    f"Expected at {candidate}. Download with: "
                    f"python -c \"from piper.download_voices import download_voice; "
                    f"from pathlib import Path; download_voice('{self._model_name}', Path('{project_models}'))\""
                )

        loop = asyncio.get_event_loop()
        self._voice = await loop.run_in_executor(
            None,
            lambda: PiperVoice.load(model_path, use_cuda=False),
        )
        logger.info("Piper TTS loaded: %s (rate=%d)", model_path, self._voice.config.sample_rate)

    async def speak(self, text: str, audio_stream: AudioStream | None = None) -> None:
        """Synthesize full text and play it."""
        if not self._voice:
            await self.load()

        stream = audio_stream or self._audio_stream
        audio = await self._synthesize(text)
        if audio is not None and stream:
            stream.play_audio(audio, sample_rate=self._voice.config.sample_rate)

    async def speak_streamed(
        self,
        chunks: AsyncIterator[str],
        audio_stream: AudioStream | None = None,
        flush_timeout: float = 0.5,
    ) -> None:
        """Buffer streaming text into sentences, synthesize and play each.

        Buffers text until a sentence boundary (. ! ? newline), then
        synthesizes and plays that sentence while continuing to buffer.
        If no new chunk arrives within flush_timeout seconds, any buffered
        text is spoken immediately to avoid perceived latency.

        Uses an asyncio.Queue so the generator runs independently and
        timeouts don't cancel the underlying streaming HTTP request.
        """
        if not self._voice:
            await self.load()

        stream = audio_stream or self._audio_stream
        buffer = ""

        # Decouple the generator from timeout-based reads via a queue.
        _DONE = object()
        queue: asyncio.Queue = asyncio.Queue()

        async def _fill_queue():
            try:
                async for text in chunks:
                    await queue.put(text)
            except Exception:
                logger.exception("Error reading response chunks")
            finally:
                await queue.put(_DONE)

        fill_task = asyncio.create_task(_fill_queue())

        try:
            while True:
                try:
                    item = await asyncio.wait_for(queue.get(), timeout=flush_timeout)
                except asyncio.TimeoutError:
                    if buffer.strip():
                        audio = await self._synthesize(buffer.strip())
                        if audio is not None and stream:
                            stream.play_audio(audio, sample_rate=self._voice.config.sample_rate)
                        buffer = ""
                    continue

                if item is _DONE:
                    break

                buffer += item

                # Check for sentence boundaries
                while True:
                    match = _SENTENCE_END.search(buffer)
                    if not match:
                        break

                    end_idx = match.end()
                    sentence = buffer[:end_idx].strip()
                    buffer = buffer[end_idx:]

                    if sentence:
                        audio = await self._synthesize(sentence)
                        if audio is not None and stream:
                            stream.play_audio(audio, sample_rate=self._voice.config.sample_rate)

            # Flush remaining buffer
            remaining = buffer.strip()
            if remaining:
                audio = await self._synthesize(remaining)
                if audio is not None and stream:
                    stream.play_audio(audio, sample_rate=self._voice.config.sample_rate)
        finally:
            if not fill_task.done():
                fill_task.cancel()
                try:
                    await fill_task
                except asyncio.CancelledError:
                    pass

    async def _synthesize(self, text: str) -> np.ndarray | None:
        """Convert text to audio array via Piper."""
        if not self._voice or not text.strip():
            return None

        loop = asyncio.get_event_loop()

        def _do_synth():
            wav_buffer = io.BytesIO()
            with wave.open(wav_buffer, "wb") as wav_out:
                self._voice.synthesize_wav(text, wav_out)
            wav_buffer.seek(0)
            with wave.open(wav_buffer, "rb") as wav_in:
                frames = wav_in.readframes(wav_in.getnframes())
                return np.frombuffer(frames, dtype=np.int16).astype(np.float32) / 32768.0

        return await loop.run_in_executor(None, _do_synth)

    @property
    def is_loaded(self) -> bool:
        return self._voice is not None
