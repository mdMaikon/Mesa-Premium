"""
Pytest configuration and shared fixtures
"""

import asyncio
import os
import sys
from collections.abc import AsyncGenerator, Generator
from unittest.mock import Mock, patch

import pytest

from fastapi.testclient import TestClient

# Add project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import app
from utils.state_manager import get_state_manager


@pytest.fixture
def client() -> TestClient:
    """FastAPI test client fixture"""
    return TestClient(app)


@pytest.fixture
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def async_client() -> AsyncGenerator:
    """Async test client for async endpoints"""
    from httpx import AsyncClient

    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


@pytest.fixture
def mock_db_connection():
    """Mock database connection"""
    with patch("database.connection.get_connection_pool") as mock_pool:
        mock_conn = Mock()
        mock_cursor = Mock()

        # Configure cursor mock with proper context manager support
        mock_cursor.fetchall.return_value = []
        mock_cursor.fetchone.return_value = None
        mock_cursor.rowcount = 0
        mock_cursor.lastrowid = 1
        mock_cursor.__enter__ = Mock(return_value=mock_cursor)
        mock_cursor.__exit__ = Mock(return_value=None)

        # Configure connection mock
        mock_conn.cursor.return_value = mock_cursor
        mock_conn.is_connected.return_value = True
        mock_conn.__enter__ = Mock(return_value=mock_conn)
        mock_conn.__exit__ = Mock(return_value=None)

        # Configure pool mock
        mock_pool.return_value = mock_conn

        yield mock_cursor


@pytest.fixture
def reset_state_manager():
    """Reset state manager before each test"""
    state_manager = get_state_manager()
    state_manager.reset_state()
    yield state_manager
    state_manager.reset_state()


@pytest.fixture
def mock_selenium_driver():
    """Mock Selenium WebDriver"""
    with patch("selenium.webdriver.Chrome") as mock_chrome:
        mock_driver = Mock()

        # Configure driver methods
        mock_driver.get.return_value = None
        mock_driver.quit.return_value = None
        mock_driver.find_element.return_value = Mock()
        mock_driver.execute_script.return_value = "mock_token_12345"
        mock_driver.current_url = "https://hub.xpi.com.br/dashboard"

        mock_chrome.return_value = mock_driver
        yield mock_driver


@pytest.fixture
def sample_hub_credentials():
    """Sample valid Hub XP credentials for testing"""
    return {
        "user_login": "SILVA.A12345",
        "password": "senhavalida123",
        "mfa_code": "123456",
    }


@pytest.fixture
def sample_token_data():
    """Sample token data for testing"""
    from datetime import datetime, timedelta

    return {
        "id": 1,
        "user_login": "SILVA.A12345",
        "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.test",
        "expires_at": datetime.now() + timedelta(hours=1),
        "extracted_at": datetime.now(),
        "created_at": datetime.now(),
    }


@pytest.fixture
def sample_fixed_income_data():
    """Sample fixed income data for testing"""
    return [
        {
            "ativo": "NTN-F 2025",
            "instrumento": "Tesouro Nacional",
            "duration": 1.5,
            "indexador": "IPCA",
            "juros": "Semestral",
            "rating": "AAA",
            "vencimento": "2025-12-31",
            "tax_min": "12,50%",
            "emissor": "Tesouro Nacional",
            "publico": "Geral",
        }
    ]


@pytest.fixture(autouse=True)
def setup_test_environment():
    """Setup test environment variables"""
    test_env = {
        "DB_HOST": "test_host",
        "DB_NAME": "test_db",
        "DB_USER": "test_user",
        "DB_PASSWORD": "test_pass",
        "HUB_XP_API_KEY": "test_api_key",
        "DISABLE_RATE_LIMITING": "true",  # Disable rate limiting for tests
    }

    with patch.dict(os.environ, test_env):
        yield


@pytest.fixture
def disable_rate_limiting():
    """Disable rate limiting for specific tests"""
    with patch(
        "middleware.rate_limiting.rate_limit_middleware"
    ) as mock_middleware:
        # Mock the middleware to always allow requests
        mock_middleware.return_value = None
        yield
