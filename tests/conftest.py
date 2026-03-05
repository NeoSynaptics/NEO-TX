"""AlchemyVoice test configuration."""

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from alchemyvoice.server import app


@pytest.fixture
def alchemy_url():
    """Default Alchemy API URL."""
    return "http://localhost:8000"


@pytest.fixture
def alchemyvoice_port():
    """Default AlchemyVoice server port."""
    return 8100


@pytest_asyncio.fixture
async def async_client():
    """Async HTTP client for testing AlchemyVoice endpoints."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c
