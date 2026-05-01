import os
import uuid

import pytest
import pytest_asyncio
from asgi_lifespan import LifespanManager
from httpx import ASGITransport, AsyncClient

from app.config import get_settings
from app.main import create_app

_TEST_DB_URL = os.environ.get(
    "DB_URL",
    "postgresql+asyncpg://postgres:postgres@localhost:5437/app_test",
)


def pytest_collection_modifyitems(items):
    for item in items:
        item.add_marker(pytest.mark.integration)


@pytest.fixture(scope="session")
def integration_settings():
    os.environ["DB_URL"] = _TEST_DB_URL
    os.environ["ENV"] = "test"
    get_settings.cache_clear()
    return get_settings()


@pytest.fixture
def integration_app(integration_settings):
    return create_app(integration_settings)


@pytest_asyncio.fixture
async def client(integration_app):
    async with LifespanManager(integration_app):
        async with AsyncClient(
            transport=ASGITransport(app=integration_app),
            base_url="http://testserver",
        ) as ac:
            yield ac


@pytest_asyncio.fixture
async def admin_token(client):
    response = await client.post(
        "/api/v1/auth/token",
        data={"username": "admin@example.com", "password": "admin123"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert response.status_code == 200, response.text
    return response.json()["access_token"]


@pytest.fixture
def admin_headers(admin_token):
    return {"Authorization": f"Bearer {admin_token}"}


@pytest.fixture
def unique_email():
    return f"test-{uuid.uuid4().hex[:8]}@example.com"
