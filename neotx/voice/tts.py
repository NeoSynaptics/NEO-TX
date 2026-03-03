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
        from piper import PiperVoice

        self._audio_stream = audio_stream

        loop = asyncio.get_event_loop()
        self._voice = await loop.run_in_executor(
            None,
            lambda: PiperVoice.load(self._model_name, use_cuda=False),
        )
        logger.info("Piper TTS loaded: %s", self._model_name)

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
    ) -> None:
        """Buffer streaming text into sentences, synthesize and play each.

        Buffers text until a sentence boundary (. ! ? newline), then
        synthesizes and plays that sentence while continuing to buffer.
        """
        if not self._voice:
            await self.load()

        stream = audio_stream or self._audio_stream
        buffer = ""

        async for chunk_text in chunks:
            buffer += chunk_text

            # Check for sentence boundaries
            while True:
                match = _SENTENCE_END.search(buffer)
                if not match:
                    break

                # Split at sentence boundary
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

    async def _synthesize(self, text: str) -> np.ndarray | None:
        """Convert text to audio array via Piper."""
        if not self._voice or not text.strip():
            return None

        loop = asyncio.get_event_loop()

        def _do_synth():
            wav_buffer = io.BytesIO()
            with wave.open(wav_buffer, "wb") as wav:
                self._voice.synthesize(text, wav)
            wav_buffer.seek(0)
            with wave.open(wav_buffer, "rb") as wav:
                frames = wav.readframes(wav.getnframes())
                return np.frombuffer(frames, dtype=np.int16).astype(np.float32) / 32768.0

        return await loop.run_in_executor(None, _do_synth)

    @property
    def is_loaded(self) -> bool:
        return self._voice is not None
