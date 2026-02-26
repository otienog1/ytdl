"""
Global pytest configuration and fixtures
"""
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock
from motor.motor_asyncio import AsyncIOMotorClient

@pytest.fixture
def mock_db():
    """Mock MongoDB database"""
    mock_client = MagicMock()
    mock_db = MagicMock()
    mock_client.get_database.return_value = mock_db
    return mock_db

@pytest.fixture
def mock_redis():
    """Mock Redis client"""
    mock_redis = AsyncMock()
    return mock_redis

@pytest.fixture
def event_loop():
    """Create event loop for async tests"""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()
