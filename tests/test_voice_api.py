"""Tests for /voice API endpoints."""

import sys
from unittest.mock import AsyncMock, MagicMock, PropertyMock
from uuid import uuid4

# Mock webrtcvad before voice imports (broken on Python 3.12+)
if "webrtcvad" not in sys.modules:
    _mock = MagicMock()
    _mock.Vad = MagicMock(return_value=MagicMock())
    sys.modules["webrtcvad"] = _mock

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from neotx.voice.pipeline import PipelineState
from neotx.server import app


@pytest_asyncio.fixture
async def client_with_voice():
    """Client with a mocked voice pipeline."""
    mock_pipeline = MagicMock()
    mock_pipeline.state = PipelineState.IDLE
    mock_pipeline.is_running = False
    mock_pipeline.conversation_id = uuid4()
    mock_pipeline.start = AsyncMock()
    mock_pipeline.stop = AsyncMock()

    app.state.voice_pipeline = mock_pipeline

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c, mock_pipeline


@pytest_asyncio.fixture
async def client_no_voice():
    """Client with no voice pipeline (voice disabled)."""
    app.state.voice_pipeline = None

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


class TestVoiceStatus:
    async def test_status_idle(self, client_with_voice):
        client, pipeline = client_with_voice
        resp = await client.get("/voice/status")
        assert resp.status_code == 200
        data = resp.json()
        assert data["state"] == "idle"
        assert data["is_running"] is False
        assert data["voice_enabled"] is True

    async def test_status_no_voice(self, client_no_voice):
        resp = await client_no_voice.get("/voice/status")
        assert resp.status_code == 200
        data = resp.json()
        assert data["voice_enabled"] is False


class TestVoiceStart:
    async def test_start_pipeline(self, client_with_voice):
        client, pipeline = client_with_voice
        resp = await client.post("/voice/start")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "started"
        pipeline.start.assert_called_once()

    async def test_start_already_running(self, client_with_voice):
        client, pipeline = client_with_voice
        pipeline.is_running = True
        pipeline.state = PipelineState.LISTENING
        resp = await client.post("/voice/start")
        data = resp.json()
        assert data["status"] == "already_running"

    async def test_start_no_voice(self, client_no_voice):
        resp = await client_no_voice.post("/voice/start")
        data = resp.json()
        assert "error" in data


class TestVoiceStop:
    async def test_stop_pipeline(self, client_with_voice):
        client, pipeline = client_with_voice
        pipeline.is_running = True
        resp = await client.post("/voice/stop")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "stopped"
        pipeline.stop.assert_called_once()

    async def test_stop_already_stopped(self, client_with_voice):
        client, pipeline = client_with_voice
        pipeline.is_running = False
        resp = await client.post("/voice/stop")
        data = resp.json()
        assert data["status"] == "already_stopped"

    async def test_stop_no_voice(self, client_no_voice):
        resp = await client_no_voice.post("/voice/stop")
        data = resp.json()
        assert "error" in data
