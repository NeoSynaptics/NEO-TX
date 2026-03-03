"""AlchemyClient unit tests — mock httpx, verify typed returns."""

import pytest
from uuid import uuid4
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

from neotx.bridge.alchemy_client import AlchemyClient


def _mock_response(json_data=None, content=b"", status_code=200, content_type="application/json"):
    """Create a mock httpx response."""
    resp = MagicMock()
    resp.status_code = status_code
    resp.json.return_value = json_data or {}
    resp.content = content
    resp.headers = {"content-type": content_type}
    resp.raise_for_status = MagicMock()
    return resp


@pytest.mark.asyncio
async def test_submit_task():
    client = AlchemyClient(base_url="http://localhost:8000")
    task_id = str(uuid4())
    now = datetime.now(timezone.utc).isoformat()

    mock_resp = _mock_response(json_data={
        "task_id": task_id, "status": "pending", "created_at": now,
    })
    client._client.post = AsyncMock(return_value=mock_resp)

    result = await client.submit_task("send email")
    assert str(result.task_id) == task_id
    assert result.status.value == "pending"


@pytest.mark.asyncio
async def test_task_status():
    client = AlchemyClient()
    task_id = uuid4()
    now = datetime.now(timezone.utc).isoformat()

    mock_resp = _mock_response(json_data={
        "task_id": str(task_id), "status": "running",
        "current_step": 3, "created_at": now, "updated_at": now,
    })
    client._client.get = AsyncMock(return_value=mock_resp)

    result = await client.task_status(task_id)
    assert result.task_id == task_id
    assert result.current_step == 3


@pytest.mark.asyncio
async def test_screenshot():
    client = AlchemyClient()
    png_bytes = b"\x89PNG\r\n\x1a\n" + b"\x00" * 100

    mock_resp = _mock_response(content=png_bytes, content_type="image/png")
    client._client.get = AsyncMock(return_value=mock_resp)

    result = await client.screenshot()
    assert result[:4] == b"\x89PNG"


@pytest.mark.asyncio
async def test_models():
    client = AlchemyClient()

    mock_resp = _mock_response(json_data={
        "models": [{"name": "ui-tars:72b", "loaded": False, "size_gb": 42.0}],
        "total_ram_gb": 128.0, "available_ram_gb": 86.0,
    })
    client._client.get = AsyncMock(return_value=mock_resp)

    result = await client.models()
    assert len(result.models) == 1
    assert result.models[0].name == "ui-tars:72b"


@pytest.mark.asyncio
async def test_close():
    client = AlchemyClient()
    client._client.aclose = AsyncMock()
    await client.close()
    client._client.aclose.assert_awaited_once()
