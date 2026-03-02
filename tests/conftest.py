"""NEO-TX test configuration."""

import pytest


@pytest.fixture
def alchemy_url():
    """Default Alchemy API URL."""
    return "http://localhost:8000"


@pytest.fixture
def neotx_port():
    """Default NEO-TX server port."""
    return 8100
