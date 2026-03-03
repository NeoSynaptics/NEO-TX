"""Tests for VoicePipeline — mocked components, verify state machine."""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import numpy as np
import pytest

from neotx.models.schemas import StreamChunk
from neotx.voice.pipeline import PipelineState, VoicePipeline


def _make_pipeline(
    router_response: str = "Hello from Neo!",
    transcription: str = "what time is it",
    wake_after: int = 1,
):
    """Create a VoicePipeline with fully mocked components."""
    mock_router = AsyncMock()

    async def mock_route_stream(request):
        yield StreamChunk(content=router_response)
        yield StreamChunk(content="", done=True, model_used="qwen3:14b")

    mock_router.route_stream = mock_route_stream

    mock_wake = AsyncMock()
    call_count = 0

    async def mock_listen(audio):
        nonlocal call_count
        call_count += 1
        if call_count > wake_after:
            # After first cycle, block forever (pipeline will be cancelled)
            await asyncio.sleep(999)
        return "hey_neo"

    mock_wake.listen = mock_listen
    mock_wake.reset = MagicMock()

    mock_listener = AsyncMock()
    # 1 second of audio at 16kHz
    mock_listener.record = AsyncMock(
        return_value=np.zeros(16000, dtype=np.int16).tobytes()
    )

    mock_stt = AsyncMock()
    mock_stt.transcribe = AsyncMock(return_value=transcription)

    mock_tts = AsyncMock()
    mock_tts.speak_streamed = AsyncMock()

    mock_audio = AsyncMock()
    mock_audio.start = AsyncMock()
    mock_audio.stop = AsyncMock()

    pipeline = VoicePipeline(
        router=mock_router,
        wake_word=mock_wake,
        listener=mock_listener,
        stt=mock_stt,
        tts=mock_tts,
        audio_stream=mock_audio,
    )

    return pipeline, {
        "router": mock_router,
        "wake_word": mock_wake,
        "listener": mock_listener,
        "stt": mock_stt,
        "tts": mock_tts,
        "audio": mock_audio,
    }


class TestPipelineState:
    def test_initial_state(self):
        pipeline, _ = _make_pipeline()
        assert pipeline.state == PipelineState.IDLE
        assert pipeline.is_running is False

    async def test_start_sets_running(self):
        pipeline, mocks = _make_pipeline()
        await pipeline.start()
        assert pipeline.is_running is True
        mocks["audio"].start.assert_called_once()
        # Let the loop run one cycle
        await asyncio.sleep(0.1)
        await pipeline.stop()

    async def test_stop_resets_state(self):
        pipeline, _ = _make_pipeline()
        await pipeline.start()
        await asyncio.sleep(0.05)
        await pipeline.stop()
        assert pipeline.state == PipelineState.IDLE
        assert pipeline.is_running is False

    async def test_double_start_ignored(self):
        pipeline, mocks = _make_pipeline()
        await pipeline.start()
        await pipeline.start()  # Should log warning but not crash
        await asyncio.sleep(0.05)
        await pipeline.stop()
        # Audio start should only be called once
        assert mocks["audio"].start.call_count == 1

    async def test_conversation_id_created(self):
        pipeline, _ = _make_pipeline()
        cid1 = pipeline.conversation_id
        await pipeline.start()
        cid2 = pipeline.conversation_id
        assert cid1 != cid2  # New conversation on start
        await asyncio.sleep(0.05)
        await pipeline.stop()


class TestPipelineCycle:
    async def test_full_cycle(self):
        """Verify: wake → record → transcribe → route → speak."""
        pipeline, mocks = _make_pipeline(
            transcription="what time is it",
            router_response="It's 3 PM.",
        )

        await pipeline.start()
        # Let one cycle complete
        await asyncio.sleep(0.2)
        await pipeline.stop()

        # Verify each component was called (listen is a plain async function,
        # but record being called proves listen ran first in the cycle)
        mocks["listener"].record.assert_called_once()
        mocks["stt"].transcribe.assert_called_once()
        mocks["tts"].speak_streamed.assert_called_once()

    async def test_empty_transcription_skipped(self):
        """Empty transcription should not route or speak."""
        pipeline, mocks = _make_pipeline(transcription="")

        await pipeline.start()
        await asyncio.sleep(0.2)
        await pipeline.stop()

        mocks["tts"].speak_streamed.assert_not_called()

    async def test_short_audio_skipped(self):
        """Very short recording (<0.1s) should be ignored."""
        pipeline, mocks = _make_pipeline()
        # Override with very short audio (less than 1600 bytes)
        mocks["listener"].record = AsyncMock(return_value=b"\x00" * 100)

        await pipeline.start()
        await asyncio.sleep(0.2)
        await pipeline.stop()

        mocks["stt"].transcribe.assert_not_called()
