"""pytest configuration and shared fixtures"""

import pytest
import asyncio
import os
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(autouse=True)
def reset_env():
    """Reset environment between tests"""
    original_env = os.environ.copy()
    yield
    os.environ.clear()
    os.environ.update(original_env)


@pytest.fixture
def async_client():
    """Async HTTP client for testing"""
    try:
        from httpx import AsyncClient
        return AsyncClient()
    except ImportError:
        pytest.skip("httpx not installed")
